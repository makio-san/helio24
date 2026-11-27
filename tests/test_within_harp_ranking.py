"""Synthetic tests of config/within-harp-ranking-v1.json and its runner; no project data or evidence is read."""
import copy
import itertools
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import scripts.audit_within_harp_ranking as runner
from helio24.data import FEATURE_COLUMNS
from helio24.full_data import sha256
from helio24.v2_training import METADATA
from helio24.walk_forward import annual_fold
from helio24.within_harp import control_logit, fit_stack, margin, ranker_model, ranker_objective, ranking_rows
from scripts.rebuild_walk_forward_v2 import select_thresholds

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT/'config/within-harp-ranking-v1.json'
YEARS = [2022, 2023]
HOUR = pd.Timedelta(hours=1)


def harp_windows(harp, start, hours, positive_hours=()):
    frame = pd.DataFrame({'harp': harp, 'forecast_time': [pd.Timestamp(start, tz='UTC')+int(h)*HOUR for h in hours]})
    frame['target'] = [int(h in set(positive_hours)) for h in hours]
    frame['observation_start'] = frame.forecast_time-12*HOUR
    frame['prediction_end'] = frame.forecast_time+24*HOUR
    frame['label_status'] = np.where(frame.target.eq(1), 'positive', 'negative')
    frame['missing_fraction'] = 0.0
    return frame


def synthetic_development(seed=24):
    """Eight HARPs a year from 2018 to 2023, 240 hourly windows each; every second HARP has one positive day."""
    rng = np.random.default_rng(seed)
    parts, harp = [], 0
    for year in range(2018, 2024):
        for k in range(8):
            harp += 1
            start = pd.Timestamp(f'{year}-02-01')+pd.Timedelta(days=30*k)
            part = harp_windows(harp, start, range(240), range(100, 124) if k % 2 == 0 else ())
            part['flaring'] = int(k % 2 == 0)
            parts.append(part)
    table = pd.concat(parts, ignore_index=True)
    values = rng.normal(size=(len(table), len(FEATURE_COLUMNS))).astype(np.float32)
    values[:, 0] += 2*table.target.to_numpy()+table.flaring.to_numpy()
    values[:, 1] += 0.02*((table.forecast_time-table.groupby('harp').forecast_time.transform('min'))/HOUR).to_numpy()
    table = pd.concat([table.drop(columns='flaring'), pd.DataFrame(values, columns=FEATURE_COLUMNS)], axis=1)
    year = table.forecast_time.dt.year
    table['role'] = np.where(year <= 2021, 'train', np.where(year == 2022, 'calibration', 'validation'))
    return table


def small_base():
    base = json.loads((ROOT/'config/walk-forward-v1.json').read_text())
    base['candidates']['xgboost']['n_estimators'] = 8
    return base


def population(meta, years):
    out = {}
    for year in years:
        split, _ = annual_fold(runner.blind(meta, year), year)
        train = split['train']
        ranked, harps = ranking_rows(train)
        timed, y, _ = runner.timing_rows(train, pd.Timestamp(f'{year-1}-01-01', tz='UTC'))
        out[str(year)] = dict(train_rows=len(train), train_positives=int(train.target.sum()), flaring_training_harps=len(np.unique(harps)),
                              ranker_rows=len(ranked), timing_rows=len(timed), timing_positives=int(y.sum()))
    return out


def stored_control(development, year, base):
    """What the stored pipeline would hold: the refit's evaluation ensemble and its prior-year thresholds."""
    meta = development[runner.META]
    split, _ = annual_fold(meta, year)
    features = development[FEATURE_COLUMNS].to_numpy(dtype=np.float32)
    x = {role: features[group.index.to_numpy()] for role, group in split.items()}
    p_cal, p_eval, _ = runner.fit_control(base, x, split['train'].target.to_numpy(dtype=np.int8),
                                          split['calibration'].target.to_numpy(dtype=np.int8))
    pipeline = json.loads((ROOT/'config/walk-forward-v2.json').read_text())
    thresholds = select_thresholds(pipeline, split['calibration'].target.to_numpy(dtype=np.int8), p_cal)
    predictions = split['evaluation'][['harp', 'forecast_time', 'target']].assign(ensemble=p_eval)
    return predictions, json.loads(json.dumps(thresholds))


@pytest.fixture(scope='module')
def development():
    return synthetic_development()


# Query groups and the timing subset

def test_query_groups_hold_only_flaring_training_harps_in_harp_and_time_order():
    first = harp_windows(1, '2015-03-01', range(200), range(100, 124)).assign(role='train')
    second = harp_windows(2, '2015-03-01', range(200)).assign(role='train')
    third = harp_windows(3, '2015-04-01', range(50), range(10, 12)).assign(role='train')
    train = pd.concat([second, third, first], ignore_index=True).sample(frac=1, random_state=3).reset_index(drop=True)
    order, qid = ranking_rows(train)
    assert set(qid) == {1, 3} and len(order) == 250 and list(qid) == sorted(qid)
    picked = train.iloc[order]
    assert all(part.forecast_time.is_monotonic_increasing for _, part in picked.groupby('harp'))
    assert int(picked.target.sum()) == int(train.target.sum())


def test_query_groups_never_use_a_label_outside_the_training_role():
    table = harp_windows(7, '2020-12-20', range(24*20), range(24*14, 24*15))
    split, _ = annual_fold(table, 2022)
    train = split['train']
    assert len(train) and not train.target.any()
    # The HARP flares in January 2021, the calibration year: it gives no query group.
    with pytest.raises(ValueError, match='No flaring training HARP'):
        ranking_rows(train)
    with pytest.raises(ValueError, match='training role only'):
        ranking_rows(pd.concat([train, table.tail(5).assign(role='calibration')]))


def test_timing_subset_is_the_known_72_hour_positive_training_windows():
    train = harp_windows(1, '2015-03-01', range(300), range(100, 124)).assign(role='train')
    positions, y, removed = runner.timing_rows(train, pd.Timestamp('2020-01-01', tz='UTC'))
    hours = set((train.forecast_time.iloc[positions]-pd.Timestamp('2015-03-01', tz='UTC'))//HOUR)
    # Window t is 72-hour positive when a 24-hour positive window starts in [t, t+48h]: hours 52 to 123.
    assert hours == set(range(52, 124)) and int(y.sum()) == 24 and int((y == 0).sum()) == 48
    # The last 48 hours have no window 48 hours later and an unknown 72-hour label.
    assert removed == {'label_unknown': 48, 'horizon_purged': 0}


def test_timing_subset_never_uses_a_label_outside_the_training_role():
    table = harp_windows(5, '2020-12-25', range(24*12), range(24*8, 24*9))
    split, _ = annual_fold(table, 2022)
    train = split['train']
    # The positive day lies in the calibration year: no training window may become 72-hour positive.
    extended = runner.extend_labels(train[['harp', 'forecast_time', 'target']])
    assert len(extended) and not extended.target.any()
    with pytest.raises(ValueError, match='both 24-hour classes'):
        runner.timing_rows(train, pd.Timestamp('2021-01-01', tz='UTC'))
    with pytest.raises(ValueError, match='training role only'):
        runner.timing_rows(pd.concat([train, table.tail(3).assign(role='calibration')]), pd.Timestamp('2021-01-01', tz='UTC'))


def test_timing_subset_purges_windows_whose_72_hour_horizon_reaches_calibration():
    boundary = pd.Timestamp('2021-01-01', tz='UTC')
    positives = [*range(200, 206), *range(250, 256)]
    train = harp_windows(4, '2020-12-20', range(265), positives).assign(role='train')
    # Sub-minute jitter as in the table: the window at hour 216 starts 40 seconds late, so its 72-hour horizon
    # ends 40 seconds after the calibration start although the window 48 hours later is a training window.
    early = ((train.forecast_time-pd.Timestamp('2020-12-20', tz='UTC'))//HOUR).lt(240)
    train.loc[early, 'forecast_time'] += pd.Timedelta(seconds=40)
    train['prediction_end'] = train.forecast_time+24*HOUR
    assert train.prediction_end.le(boundary).all()
    positions, y, removed = runner.timing_rows(train, boundary)
    ends = train.forecast_time.iloc[positions]+72*HOUR
    assert removed['horizon_purged'] == 1 and ends.le(boundary).all() and set(np.unique(y)) == {0, 1}


# Stack, margins and the ranker

def test_stack_is_fitted_on_calibration_rows_only():
    rng = np.random.default_rng(1)
    z_cal = rng.normal(size=(400, 2))
    y_cal = (z_cal[:, 0]+rng.normal(size=400) > 0).astype(int)
    params = json.loads(CONFIG.read_text())['stack']['logistic']
    p_cal, p_eval, first = fit_stack(params, z_cal, y_cal, rng.normal(size=(50, 2)))
    other_cal, other_eval, second = fit_stack(params, z_cal, y_cal, 100*rng.normal(size=(70, 2)))
    assert np.array_equal(p_cal, other_cal) and first == second and len(p_eval) == 50 and len(other_eval) == 70
    assert ((p_cal > 0) & (p_cal < 1)).all() and first['coefficients'][0] > 0
    with pytest.raises(ValueError):
        fit_stack(params, z_cal, np.zeros(400, dtype=int), z_cal)
    with pytest.raises(ValueError):
        fit_stack(params, z_cal[:, 0], y_cal, z_cal[:, 0])
    with pytest.raises(ValueError):
        fit_stack(params, np.c_[z_cal[:, 0], np.full(400, np.inf)], y_cal, z_cal)


def test_ranker_uses_the_frozen_pairwise_objective_and_query_groups(development):
    config = json.loads(CONFIG.read_text())
    train = annual_fold(development[development.forecast_time.dt.year < 2021], 2022)[0]['train']
    order, qid = ranking_rows(train)
    x = development.loc[train.index, FEATURE_COLUMNS].to_numpy(dtype=np.float32)
    model = runner.fit_ranker(small_base(), x[order], qid, train.target.to_numpy()[order], config['harp_ranker']['objective'])
    assert ranker_objective(model) == config['harp_ranker']['objective']
    params = model.steps[-1][1].get_params()
    assert params['objective'] == 'rank:pairwise' and params['max_depth'] == 3 and params['learning_rate'] == 0.04
    assert params.get('scale_pos_weight') is None and np.isfinite(margin(model, x)).all()
    changed = dict(config['harp_ranker']['objective'], lambdarank_pair_method='mean')
    with pytest.raises(ValueError, match='ranking objective'):
        runner.fit_ranker(small_base(), x[order], qid, train.target.to_numpy()[order], changed)
    assert isinstance(ranker_model(small_base()).steps[-1][1].get_params()['n_estimators'], int)


def test_control_logit_is_the_clipped_logit():
    assert np.allclose(control_logit([0.5, 1.0, 0.0]), [0.0, np.log((1-1e-9)/1e-9), -np.log((1-1e-9)/1e-9)])


# Phase 1

@pytest.fixture(scope='module')
def phase_inputs(development, tmp_path_factory):
    base = small_base()
    meta = development[runner.META].copy()
    features = development[FEATURE_COLUMNS].to_numpy(dtype=np.float32)
    control_dir = tmp_path_factory.mktemp('control')
    thresholds = {}
    for year in YEARS:
        (control_dir/str(year)).mkdir()
        predictions, thresholds[year] = stored_control(development, year, base)
        predictions.to_parquet(control_dir/str(year)/'predictions.parquet', index=False)
    config = json.loads(CONFIG.read_text())
    config.update(years=YEARS, population=population(meta, YEARS))
    config['budget'].update(constituent_fits=8, stack_fits=6)
    pipeline = json.loads((ROOT/'config/walk-forward-v2.json').read_text())
    folds = {year: annual_fold(meta, year)[1] for year in YEARS}
    return config, base, pipeline, meta, features, control_dir, folds, thresholds


def phase(inputs, meta=None, config=None, control_dir=None):
    config_, base, pipeline, base_meta, features, control_dir_, folds, thresholds = inputs
    return runner.fit_phase(config or config_, base, pipeline, base_meta if meta is None else meta, features,
                            control_dir or control_dir_, folds, thresholds)


def single(config, year=2023):
    return dict(config, years=[year], budget=dict(config['budget'], constituent_fits=4, stack_fits=3))


def test_blind_hides_every_label_from_the_evaluation_year_on(development):
    meta = development[runner.META]
    hidden = runner.blind(meta, 2022)
    late = meta.forecast_time.ge(pd.Timestamp('2022-01-01', tz='UTC'))
    assert meta.target[late].sum() > 0 and hidden.target[late].sum() == 0 and set(hidden.label_status[late]) == {'hidden'}
    assert hidden.target[~late].equals(meta.target[~late])


def test_phase_one_is_identical_whatever_the_evaluation_labels_are(phase_inputs):
    config, _, _, meta, _, _, _, _ = phase_inputs
    flipped = meta.assign(target=meta.target.where(meta.forecast_time.dt.year < 2023, 1-meta.target))
    first, second = phase(phase_inputs, config=single(config)), phase(phase_inputs, meta=flipped, config=single(config))
    assert json.dumps(first[0], sort_keys=True) == json.dumps(second[0], sort_keys=True)
    assert first[1][2023].equals(second[1][2023]) and first[2] == second[2] and first[3] == second[3]
    assert list(first[1][2023].columns) == ['harp', 'forecast_time', 'control_logit', 'ranker_margin', 'timing_margin', *runner.CANDIDATES]
    assert first[4:] == (4, 3)


def test_specialists_see_only_training_rows_and_stacks_only_calibration_rows(phase_inputs, monkeypatch):
    config, *_ = phase_inputs
    seen = {}
    ranker, timing, stack = runner.fit_ranker, runner.fit_timing, runner.fit_stack

    def spy_ranker(base, x, harps, y, objective):
        seen['ranker'] = (len(x), list(harps))
        return ranker(base, x, harps, y, objective)

    def spy_timing(base, x, y):
        seen['timing'] = (len(x), int(y.sum()))
        return timing(base, x, y)

    def spy_stack(params, z_cal, y_cal, z_eval):
        seen.setdefault('stack', []).append((z_cal.shape, len(y_cal), z_eval.shape))
        return stack(params, z_cal, y_cal, z_eval)

    monkeypatch.setattr(runner, 'fit_ranker', spy_ranker)
    monkeypatch.setattr(runner, 'fit_timing', spy_timing)
    monkeypatch.setattr(runner, 'fit_stack', spy_stack)
    _, probabilities, stacks, population_rows, _, _ = phase(phase_inputs, config=single(config))
    row = population_rows[0]
    assert seen['ranker'][0] == row['ranker_rows'] and seen['ranker'][1] == sorted(seen['ranker'][1])
    assert seen['timing'] == (row['timing_rows'], row['timing_positives'])
    assert [s[0][1] for s in seen['stack']] == [1, 2, 2]
    assert all(s[0][0] == s[1] == row['calibration_rows'] and s[2][0] == row['evaluation_rows'] for s in seen['stack'])
    assert [stacks['2023'][c]['inputs'] for c in runner.CANDIDATES] == [['control_logit'], ['control_logit', 'ranker_margin'],
                                                                        ['control_logit', 'timing_margin']]
    frame = probabilities[2023]
    assert all(frame[c].between(0, 1).all() for c in runner.CANDIDATES)


def test_phase_one_stops_on_budget_population_or_fold_changes(phase_inputs):
    config, base, pipeline, meta, features, control_dir, folds, thresholds = phase_inputs
    with pytest.raises(RuntimeError):
        phase(phase_inputs, config=dict(config, budget=dict(config['budget'], constituent_fits=6)))
    with pytest.raises(RuntimeError):
        phase(phase_inputs, config=dict(config, budget=dict(config['budget'], stack_fits=5)))
    with pytest.raises(RuntimeError):
        # One year run against a two-year budget: fewer fits than frozen also stops the run.
        phase(phase_inputs, config=dict(config, years=[2023]))
    for key in ['ranker_rows', 'timing_rows', 'timing_positives', 'train_positives']:
        changed = copy.deepcopy(config)
        changed['population']['2022'][key] += 1
        with pytest.raises(ValueError, match='differ from the protocol'):
            phase(phase_inputs, config=changed)
    other = copy.deepcopy(folds)
    other[2022][0]['rows'] += 1
    with pytest.raises(ValueError, match='Annual populations'):
        runner.fit_phase(config, base, pipeline, meta, features, control_dir, other, thresholds)


def test_phase_one_stops_when_the_control_refit_does_not_reproduce_the_stored_control(phase_inputs, tmp_path):
    config, base, pipeline, meta, features, control_dir, folds, thresholds = phase_inputs
    (tmp_path/'2023').mkdir()
    stored = pd.read_parquet(control_dir/'2023/predictions.parquet')
    stored.assign(ensemble=stored.ensemble+1e-6).to_parquet(tmp_path/'2023/predictions.parquet', index=False)
    with pytest.raises(ValueError, match='stored control probabilities'):
        phase(phase_inputs, config=single(config), control_dir=tmp_path)
    moved = copy.deepcopy(thresholds)
    moved[2023]['alert']['threshold'] += 1e-6
    with pytest.raises(ValueError, match='stored thresholds'):
        runner.fit_phase(single(config), base, pipeline, meta, features, control_dir, folds, moved)
    flipped = copy.deepcopy(thresholds)
    flipped[2023]['alert']['fallback'] = not flipped[2023]['alert']['fallback']
    with pytest.raises(ValueError, match='stored thresholds'):
        runner.fit_phase(single(config), base, pipeline, meta, features, control_dir, folds, flipped)


# Reading

def test_every_result_falls_into_exactly_one_reading():
    keys = ['all_year_primary', 'cycle25_primary', 'cycle25_bootstrap_lower_above_zero']
    seen = set()
    for values in itertools.product([False, True], repeat=13):
        restack = dict(zip(keys, values[:3]))
        ranker = dict(zip(keys, values[3:6]), beats_restack_all_years=values[6], beats_restack_cycle25=values[7])
        timing = dict(zip(keys, values[8:11]), beats_restack_all_years=values[11], beats_restack_cycle25=values[12])
        entries = [restack, ranker, timing]
        if any(e['all_year_primary'] and not e['cycle25_primary'] for e in entries) \
                or any(e['beats_restack_all_years'] and not e['beats_restack_cycle25'] for e in [ranker, timing]):
            continue
        decision = runner.read({'restack_control': restack, 'harp_ranker': ranker, 'timing_specialist': timing})
        specific = [name for name, e in [('harp_ranker', ranker), ('timing_specialist', timing)]
                    if (e['all_year_primary'] and e['beats_restack_all_years'])
                    or (e['cycle25_primary'] and e['cycle25_bootstrap_lower_above_zero'] and e['beats_restack_cycle25'])]
        goal = [runner.meets_goal(e) for e in entries]
        expected = 'S1_within_harp_helps' if specific else 'S2_restack_or_unattributed' if any(goal) else 'S3_no_gain'
        assert decision['reading'] == expected and decision['specific_candidates'] == specific
        assert decision['specific_candidates_meeting_goal'] == len(specific)
        assert (decision['specific_candidates_meeting_goal'] >= 1) == (decision['reading'] == 'S1_within_harp_helps')
        assert decision['candidates_meeting_goal_against_control'] == [c for c, g in zip(runner.CANDIDATES, goal) if g]
        assert decision['outcome_label'] == runner.OUTCOME[expected]
        seen.add(decision['reading'])
    assert seen == set(runner.READINGS)


def test_a_specialist_that_does_not_beat_the_restack_is_not_attributed():
    passing = dict(all_year_primary=False, cycle25_primary=True, cycle25_bootstrap_lower_above_zero=True)
    failing = dict(passing, cycle25_bootstrap_lower_above_zero=False)
    loses = dict(beats_restack_all_years=False, beats_restack_cycle25=False)
    beats = dict(beats_restack_all_years=False, beats_restack_cycle25=True)
    assert runner.read({'restack_control': passing, 'harp_ranker': {**passing, **loses}, 'timing_specialist': {**failing, **beats}})[
        'outcome_label'] == 'result:partial'
    assert runner.read({'restack_control': failing, 'harp_ranker': {**failing, **beats}, 'timing_specialist': {**passing, **beats}})[
        'specific_candidates'] == ['timing_specialist']
    assert runner.read({'restack_control': failing, 'harp_ranker': {**failing, **beats}, 'timing_specialist': {**failing, **beats}})[
        'outcome_label'] == 'result:no-gain'


# The frozen protocol

def test_frozen_protocol_matches_the_idea_and_the_adopted_basis():
    text = CONFIG.read_text()
    config = json.loads(text)
    v2 = json.loads((ROOT/'config/activity-history-v2.json').read_text())
    near = json.loads((ROOT/'config/near-miss-weighting-v1.json').read_text())
    runner.check_protocol(config)
    assert config['id'] == 'within-harp-ranking-v1' and config['status'] == 'frozen_before_any_candidate_result'
    assert config['reserved_test_accessed'] is False and not {chr(0x2013), chr(0x2014)} & set(text)
    assert config['years'] == v2['years'] == [2014, 2015, 2016, 2017, 2022, 2023] and config['alert_fallback_years'] == [2022]
    assert [c['id'] for c in config['candidates']] == ['restack_control', 'harp_ranker', 'timing_specialist']
    assert config['budget']['constituent_fits'] == 24 and config['budget']['stack_fits'] == 18
    assert config['budget']['hyperparameter_search'] == 0 and config['budget']['downloads'] == 0
    evidence = config['evidence']
    assert evidence['table'] == 'artifacts/relabelled_development_20261111_r1' and evidence['control'] == 'artifacts/walk_forward_v2_20261112_r1'
    assert evidence['table_report_sha256'] == v2['evidence']['table_report_sha256']
    assert evidence['control_report_sha256'] == v2['evidence']['control_report_sha256']
    for name in ['pipeline_protocol', 'base_protocol', 'operating_point', 'label_construction_source', 'acceptance_source']:
        assert sha256(ROOT/evidence[name]) == evidence[f'{name}_sha256']
    assert config['acceptance']['per_year_primary'] == v2['acceptance']['per_year_primary']
    assert set(config['reading']) == {*runner.READINGS, 'exclusive'}
    assert config['acceptance_rule'] == {**config['acceptance_rule'], 'metric_path': 'decision.specific_candidates_meeting_goal',
                                         'op': '>=', 'value': 1}
    assert set(config['population'])-{'source'} == {str(year) for year in config['years']}
    for year in config['years']:
        counts, other = config['population'][str(year)], near['population'][str(year)]
        assert all(counts[k] == other[k] for k in ['train_rows', 'train_positives', 'flaring_training_harps', 'calibration_rows',
                                                   'calibration_positives', 'evaluation_rows'])
        assert counts['ranker_positives'] == counts['train_positives'] and counts['ranker_rows'] < counts['train_rows']
        assert counts['timing_rows'] == counts['timing_positives']+counts['timing_negatives']
        assert 0 < counts['timing_positives'] <= counts['train_positives']
    assert 'models.joblib is never opened' in evidence['stored_files']


@pytest.mark.parametrize('change', [
    lambda c: c['candidates'].append({'id': 'ndcg_ranker'}),
    lambda c: c['candidates'].reverse(),
    lambda c: c['control'].update(id='refit'),
    lambda c: c['stack']['inputs'].update(harp_ranker=['ranker_margin']),
    lambda c: c['stack']['logistic'].update(C=0.1),
    lambda c: c['harp_ranker']['objective'].update(name='rank:ndcg'),
    lambda c: c['timing_subset'].update(horizon_hours=48),
    lambda c: c['years'].append(2024),
    lambda c: c['years'].remove(2022),
    lambda c: c['budget'].update(constituent_fits=36),
    lambda c: c['budget'].update(stack_fits=24),
    lambda c: c['budget'].update(hyperparameter_search=1),
    lambda c: c['budget'].update(downloads=1),
    lambda c: c.update(reserved_test_accessed=True),
    lambda c: c.update(status='design_proposed'),
    lambda c: c.update(alert_fallback_years=[2021]),
])
def test_runner_refuses_a_changed_protocol(change):
    config = json.loads(CONFIG.read_text())
    change(config)
    with pytest.raises(ValueError):
        runner.check_protocol(config)


# End to end on synthetic inputs

def write_inputs(directory, development):
    """A materialized table, a stored control and a protocol copy that point at synthetic files only."""
    table_dir, control_dir = directory/'table', directory/'control'
    (table_dir/'shards').mkdir(parents=True)
    shard = table_dir/'shards/part-0.parquet'
    development[[*METADATA, *FEATURE_COLUMNS]].to_parquet(shard, index=False)
    roles = development.groupby('role').target
    (table_dir/'report.json').write_text(json.dumps({
        'shards': [{'file': shard.name, 'bytes': shard.stat().st_size, 'sha256': sha256(shard)}],
        'rows': {k: int(v) for k, v in roles.size().items()}, 'positives': {k: int(v) for k, v in roles.sum().items()}}))
    meta = development[runner.META]
    base = small_base()
    folds, hashes, fallback = [], {}, []
    for year in YEARS:
        _, audit = annual_fold(meta, year)
        (control_dir/str(year)).mkdir(parents=True)
        predictions, thresholds = stored_control(development, year, base)
        predictions.to_parquet(control_dir/str(year)/'predictions.parquet', index=False)
        (control_dir/str(year)/'thresholds.json').write_text(json.dumps(thresholds))
        # Not a model file: the run fails if anything tries to load it.
        (control_dir/str(year)/'models.joblib').write_bytes(b'not a pickle')
        if thresholds['alert']['fallback']:
            fallback.append(year)
        folds.append({'year': year, 'audit': audit, 'status': 'complete'})
        hashes.update({f'{year}/{name}': sha256(control_dir/str(year)/name) for name in ['predictions.parquet', 'thresholds.json']})
    (control_dir/'report.json').write_text(json.dumps({'folds': folds, 'artifact_hashes': hashes}))
    (directory/'base.json').write_text(json.dumps(base))
    config = json.loads(CONFIG.read_text())
    config.update(years=YEARS, population=population(meta, YEARS), alert_fallback_years=fallback)
    config['budget'].update(constituent_fits=8, stack_fits=6)
    config['evidence'].update(table=str(table_dir), table_report_sha256=sha256(table_dir/'report.json'), control=str(control_dir),
                              control_report_sha256=sha256(control_dir/'report.json'), base_protocol=str(directory/'base.json'),
                              base_protocol_sha256=sha256(directory/'base.json'),
                              pipeline_protocol=str(ROOT/'config/walk-forward-v2.json'))
    (directory/'config.json').write_text(json.dumps(config))
    return directory/'config.json'


@pytest.fixture(scope='module')
def executed(tmp_path_factory, development):
    directory = tmp_path_factory.mktemp('within_harp')
    config_path = write_inputs(directory, development)
    result, table = runner.run(config_path, directory/'output')
    return directory, config_path, result, table


def test_run_on_synthetic_inputs_freezes_phase_one_before_labels(executed):
    directory, config_path, result, table = executed
    output = directory/'output'
    phase1 = json.loads((output/'phase1.json').read_text())
    assert set(phase1) == {'thresholds.json', 'stacks.json', 'population.csv', 'probabilities_2022.parquet', 'probabilities_2023.parquet'}
    assert all(sha256(output/name) == value for name, value in phase1.items())
    assert result['phase1_sha256'] == sha256(output/'phase1.json') and result['thresholds_sha256'] == phase1['thresholds.json']
    assert result['config_sha256'] == sha256(config_path) and result['constituent_fits'] == 8 and result['stack_fits'] == 6
    for year in YEARS:
        columns = list(pd.read_parquet(output/f'probabilities_{year}.parquet').columns)
        assert 'target' not in columns and columns[-3:] == runner.CANDIDATES
    thresholds = json.loads((output/'thresholds.json').read_text())
    stored = {year: json.loads((directory/f'control/{year}/thresholds.json').read_text()) for year in YEARS}
    assert all(set(thresholds[str(year)]) == {'control', *runner.CANDIDATES} for year in YEARS)
    assert all(thresholds[str(year)]['control'] == stored[year] for year in YEARS)
    assert result['reserved_test_accessed'] is False and result['model_promoted'] is False and result['threshold_adopted'] is False
    assert result['artifact_hashes'].keys() >= {'results.csv', 'intervals.csv', 'phase1.json', 'predictions_2022.parquet'}


def test_run_reports_every_candidate_and_one_reading(executed):
    _, _, result, table = executed
    names = ['control', *runner.CANDIDATES]
    assert set(zip(table.year, table.candidate, table.tier)) == set(itertools.product(YEARS, names, ['watch', 'alert']))
    alert = table[table.tier.eq('alert')]
    assert alert.missed_positive_runs.notna().all() and alert.within_flaring_ap.notna().all()
    assert {'alert_fp_share_lingering', 'alert_fp_share_early', 'alert_fp_share_between', 'median_alarm_delay_hours',
            'hit_episodes', 'episodes', 'margin_within_flaring_ap', 'alert_windows_differing_from_control'} <= set(table.columns)
    specialists = alert[alert.candidate.isin(runner.SPECIALISTS)]
    assert specialists.margin_within_flaring_ap.notna().all() and specialists.beats_restack.notna().all()
    decision = result['decision']
    assert result['reading'] == decision['reading'] and decision['reading'] in runner.READINGS
    assert decision['specific_candidates_meeting_goal'] == len(decision['specific_candidates'])
    assert set(result['acceptance']) == {*names, 'descriptive'}
    assert 'goal_met' not in result['acceptance']['control']
    assert {'beats_restack_all_years', 'beats_restack_cycle25'} <= set(result['acceptance']['harp_ranker'])
    assert isinstance(result['acceptance']['descriptive']['within_harp_route_closed_for_96_summaries'], bool)
    assert [row['year'] for row in result['population']] == YEARS


def test_run_refuses_an_existing_output_and_changed_inputs(executed, tmp_path):
    directory, config_path, _, _ = executed
    before = {p.name: sha256(p) for p in (directory/'output').iterdir()}
    with pytest.raises(FileExistsError):
        runner.run(config_path, directory/'output')
    assert before == {p.name: sha256(p) for p in (directory/'output').iterdir()}
    config = json.loads(config_path.read_text())

    def refused(change, name):
        changed = copy.deepcopy(config)
        change(changed)
        path = tmp_path/f'{name}.json'
        path.write_text(json.dumps(changed))
        with pytest.raises(ValueError):
            runner.run(path, tmp_path/f'{name}_output')

    refused(lambda c: c['evidence'].update(control_report_sha256='0'*64), 'control_hash')
    refused(lambda c: c['evidence'].update(table_report_sha256='0'*64), 'table_hash')
    refused(lambda c: c['evidence'].update(base_protocol_sha256='0'*64), 'recipes_hash')
    refused(lambda c: c['evidence'].update(pipeline_protocol_sha256='0'*64), 'pipeline_hash')
    refused(lambda c: c.update(alert_fallback_years=[] if c['alert_fallback_years'] else [2023]), 'fallback')
    refused(lambda c: c['years'].append(2024), 'reserved')
    assert not (tmp_path/'control_hash_output').exists() and not (tmp_path/'reserved_output').exists()


def test_run_refuses_changed_control_files_and_labels(tmp_path, development):
    config_path = write_inputs(tmp_path, development)
    thresholds = tmp_path/'control/2023/thresholds.json'
    original = thresholds.read_text()
    thresholds.write_text(original.replace('"fallback": false', '"fallback": true').replace('"fallback": true', '"fallback": false')+' ')
    with pytest.raises(ValueError, match='Stored control file changed'):
        runner.run(config_path, tmp_path/'changed_thresholds')
    thresholds.write_text(original)
    # A control whose stored labels differ from the table is refused, even with consistent hashes.
    predictions = tmp_path/'control/2023/predictions.parquet'
    frame = pd.read_parquet(predictions)
    frame['target'] = 1-frame.target
    frame.to_parquet(predictions, index=False)
    report_path = tmp_path/'control/report.json'
    report = json.loads(report_path.read_text())
    report['artifact_hashes']['2023/predictions.parquet'] = sha256(predictions)
    report_path.write_text(json.dumps(report))
    config = json.loads(config_path.read_text())
    config['evidence']['control_report_sha256'] = sha256(report_path)
    config_path.write_text(json.dumps(config))
    with pytest.raises(ValueError, match='Stored control labels differ'):
        runner.run(config_path, tmp_path/'changed_labels')
