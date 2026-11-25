"""Synthetic tests of config/near-miss-weighting-v1.json and its runner; no project data or evidence is read."""
import copy
import itertools
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import scripts.audit_near_miss_weighting as runner
from helio24.data import FEATURE_COLUMNS
from helio24.full_data import sha256
from helio24.near_miss import near_miss_mask, near_miss_weights
from helio24.v2_training import METADATA
from helio24.walk_forward import annual_fold
from scripts.audit_activity_history_relabelled import fit_probabilities

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT/'config/near-miss-weighting-v1.json'
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
    table = pd.concat([table.drop(columns='flaring'), pd.DataFrame(values, columns=FEATURE_COLUMNS)], axis=1)
    year = table.forecast_time.dt.year
    table['role'] = np.where(year <= 2021, 'train', np.where(year == 2022, 'calibration', 'validation'))
    return table


def population(meta, years):
    out = {}
    for year in years:
        split, _ = annual_fold(runner.blind(meta, year), year)
        train = split['train']
        _, _, mask = near_miss_weights(train, runner.FACTOR, runner.SPAN_HOURS)
        out[str(year)] = dict(train_rows=len(train), train_positives=int(train.target.sum()),
                              train_negatives=int(train.target.eq(0).sum()), near_miss_negatives=int(mask.sum()))
    return out


def stored_thresholds(year):
    return {'watch': {'threshold': 0.2}, 'comparison_recall_0.95': {'threshold': 0.1},
            'alert': {'threshold': 0.6, 'calibration_recall': 0.5, 'calibration_precision': 0.4, 'fallback': year == 2022}}


def stub_fit(calls):
    def fit(base, x, y_train, y_cal, weight):
        calls.append(dict(weight=weight.copy(), rows={role: len(values) for role, values in x.items()}, train=len(y_train)))
        scale = 1+weight.max()/10
        return 1/(1+np.exp(-scale*x['calibration'][:, 0])), 1/(1+np.exp(-scale*x['evaluation'][:, 0])), 2
    return fit


@pytest.fixture(scope='module')
def development():
    return synthetic_development()


@pytest.fixture(scope='module')
def phase_inputs(development):
    meta = development[runner.META].copy()
    features = development[FEATURE_COLUMNS].to_numpy(dtype=np.float32)
    config = {'years': YEARS, 'budget': {'constituent_fits': 8}, 'population': population(meta, YEARS)}
    pipeline = json.loads((ROOT/'config/walk-forward-v2.json').read_text())
    folds = {year: annual_fold(meta, year)[1] for year in YEARS}
    return config, pipeline, meta, features, folds, {year: stored_thresholds(year) for year in YEARS}


def phase(inputs, meta=None, config=None, fit=None):
    base_config, pipeline, base_meta, features, folds, thresholds = inputs
    return runner.fit_phase(config or base_config, {}, pipeline, base_meta if meta is None else meta, features, folds, thresholds,
                            fit=fit or stub_fit([]))


def test_near_miss_is_a_negative_within_72_hours_of_a_positive_of_the_same_harp():
    first = harp_windows(1, '2015-03-01', range(300), range(100, 124)).assign(role='train')
    second = harp_windows(2, '2015-03-01', range(300)).assign(role='train')
    train = pd.concat([second, first], ignore_index=True).sample(frac=1, random_state=3)
    mask = pd.Series(near_miss_mask(train, 72), index=train.index)
    hours = (train.forecast_time-pd.Timestamp('2015-03-01', tz='UTC'))//HOUR
    flagged = set(hours[mask & train.harp.eq(1)])
    # Positives are hours 100 to 123: the boundary hours 28 and 195 are 72 hours away and count, 27 and 196 do not.
    assert flagged == set(range(28, 100)) | set(range(124, 196))
    assert not mask[train.harp.eq(2)].any() and not mask[train.target.eq(1)].any()


def test_membership_never_uses_a_label_outside_the_training_role():
    table = harp_windows(7, '2020-12-20', range(24*20), range(24*14, 24*15))
    split, _ = annual_fold(table, 2022)
    train = split['train']
    assert len(train) and train.forecast_time.max() < pd.Timestamp('2021-01-01', tz='UTC') and not train.target.any()
    # The HARP flares in January 2021, the calibration year: no training window may become a near miss.
    assert not near_miss_mask(train, 72).any()
    with pytest.raises(ValueError):
        near_miss_mask(pd.concat([train, table.tail(5).assign(role='calibration')]), 72)
    with pytest.raises(ValueError):
        near_miss_weights(train, 3, 72)


def test_weights_put_the_same_total_on_negatives_and_leave_positives_at_one():
    train = pd.concat([harp_windows(1, '2015-03-01', range(300), range(100, 124)), harp_windows(2, '2015-03-01', range(300))],
                      ignore_index=True)
    targeted, uniform, mask = near_miss_weights(train, 3, 72)
    negative = train.target.eq(0).to_numpy()
    assert mask.sum() == 144 and set(targeted[mask]) == {3.0} and set(targeted[~mask]) == {1.0}
    assert np.allclose(uniform[negative], 1+2*144/negative.sum()) and (uniform[~negative] == 1).all() and (targeted[~negative] == 1).all()
    assert np.isclose(targeted[negative].sum(), uniform[negative].sum())
    with pytest.raises(ValueError):
        near_miss_weights(train, 1, 72)
    with pytest.raises(ValueError):
        near_miss_mask(train, 0)


def test_blind_hides_every_label_from_the_evaluation_year_on(development):
    meta = development[runner.META]
    hidden = runner.blind(meta, 2022)
    late = meta.forecast_time.ge(pd.Timestamp('2022-01-01', tz='UTC'))
    assert meta.target[late].sum() > 0 and hidden.target[late].sum() == 0 and set(hidden.label_status[late]) == {'hidden'}
    assert hidden.target[~late].equals(meta.target[~late]) and hidden.label_status[~late].equals(meta.label_status[~late])


def test_phase_one_is_identical_whatever_the_evaluation_labels_are(phase_inputs):
    config, _, meta, _, _, _ = phase_inputs
    single = dict(config, years=[2023], budget={'constituent_fits': 4})
    flipped = meta.assign(target=meta.target.where(meta.forecast_time.dt.year < 2023, 1-meta.target))
    first, second = phase(phase_inputs, config=single), phase(phase_inputs, meta=flipped, config=single)
    assert json.dumps(first[0], sort_keys=True) == json.dumps(second[0], sort_keys=True)
    assert first[1][2023].equals(second[1][2023]) and first[2] == second[2]
    assert list(first[1][2023].columns) == ['harp', 'forecast_time', *runner.CANDIDATES]


def test_phase_one_weights_only_training_rows_by_training_labels(phase_inputs):
    config, _, meta, _, _, _ = phase_inputs
    single = dict(config, years=[2023], budget={'constituent_fits': 4})
    calls, flipped_calls = [], []
    _, _, weights, fits = phase(phase_inputs, config=single, fit=stub_fit(calls))
    # Changing the calibration-year labels must not change which training windows are near misses.
    flipped = meta.assign(target=meta.target.where(meta.forecast_time.dt.year < 2022, 1-meta.target))
    _, pipeline, _, features, _, thresholds = phase_inputs
    _, _, flipped_weights, _ = runner.fit_phase(single, {}, pipeline, flipped, features, {2023: annual_fold(flipped, 2023)[1]}, thresholds,
                                                fit=stub_fit(flipped_calls))
    assert weights == flipped_weights and all(np.array_equal(a['weight'], b['weight']) for a, b in zip(calls, flipped_calls))
    row = weights[0]
    assert fits == 4 and len(calls) == 2 and all(len(c['weight']) == c['rows']['train'] == c['train'] == row['train_rows'] for c in calls)
    assert sorted(set(calls[0]['weight'])) == [1.0, 3.0] and int((calls[0]['weight'] == 3).sum()) == row['near_miss_negatives']
    assert len(set(calls[1]['weight'])) == 2 and np.isclose(calls[1]['weight'].max(), row['uniform_negative_weight'])
    assert np.isclose(row['negative_weight_total_near_miss_w3'], row['negative_weight_total_uniform_matched'])
    assert row['calibration_weight'] == row['evaluation_weight'] == 1.0


def test_phase_one_stops_on_budget_population_or_fold_changes(phase_inputs):
    config, pipeline, meta, features, folds, thresholds = phase_inputs
    with pytest.raises(RuntimeError):
        phase(phase_inputs, config=dict(config, budget={'constituent_fits': 6}))
    with pytest.raises(RuntimeError):
        phase(phase_inputs, config=dict(config, budget={'constituent_fits': 10}))
    changed = copy.deepcopy(config)
    changed['population']['2022']['near_miss_negatives'] += 1
    with pytest.raises(ValueError):
        phase(phase_inputs, config=changed)
    other = copy.deepcopy(folds)
    other[2022][0]['rows'] += 1
    with pytest.raises(ValueError):
        runner.fit_phase(config, {}, pipeline, meta, features, other, thresholds, fit=stub_fit([]))


def test_sample_weight_reaches_both_final_estimators_of_the_unchanged_recipes(monkeypatch, development):
    base = json.loads((ROOT/'config/walk-forward-v1.json').read_text())
    base['candidates']['xgboost']['n_estimators'] = 8
    table = development[development.forecast_time.dt.year >= 2021]
    split, _ = annual_fold(table, 2023)
    x = {role: group[FEATURE_COLUMNS].to_numpy(dtype=np.float32) for role, group in split.items()}
    y_train, y_cal = split['train'].target.to_numpy(dtype=np.int8), split['calibration'].target.to_numpy(dtype=np.int8)
    targeted, _, _ = near_miss_weights(split['train'], 3, 72)
    p_cal, p_eval, fits = runner.fit_weighted(base, x, y_train, y_cal, np.ones(len(y_train)))
    empty = {role: pd.DataFrame(index=group.index) for role, group in split.items()}
    reference = fit_probabilities(base, split, empty, [])
    assert fits == 2 and np.allclose(p_cal, reference[0]) and np.allclose(p_eval, reference[1])
    weighted = runner.fit_weighted(base, x, y_train, y_cal, targeted)
    assert not np.allclose(weighted[1], p_eval)
    seen = {}

    class Spy:
        def __init__(self, name):
            self.steps = [('imputer', None), (name, None)]

        def fit(self, x, y, **kwargs):
            seen[self.steps[-1][0]] = kwargs
            return self

        def predict_proba(self, x):
            return np.column_stack([1-1/(1+np.exp(-x[:, 0])), 1/(1+np.exp(-x[:, 0]))])

    monkeypatch.setattr(runner, 'candidate_models', lambda base: {'logistic': Spy('logisticregression'), 'xgboost': Spy('xgbclassifier')})
    runner.fit_weighted(base, x, y_train, y_cal, targeted)
    assert set(seen) == {'logisticregression', 'xgbclassifier'}
    assert all(list(kwargs) == [f'{name}__sample_weight'] and kwargs[f'{name}__sample_weight'] is targeted for name, kwargs in seen.items())


def test_every_result_falls_into_exactly_one_reading():
    keys = ['all_year_primary', 'cycle25_primary', 'cycle25_bootstrap_lower_above_zero']
    seen = set()
    for values in itertools.product([False, True], repeat=8):
        near = dict(zip(keys, values[:3]), beats_uniform_all_years=values[3], beats_uniform_cycle25=values[4])
        uniform = dict(zip(keys, values[5:]))
        if (near['all_year_primary'] and not near['cycle25_primary']) or (uniform['all_year_primary'] and not uniform['cycle25_primary']) \
                or (near['beats_uniform_all_years'] and not near['beats_uniform_cycle25']):
            continue
        decision = runner.read({'near_miss_w3': near, 'uniform_matched': uniform})
        specific = (near['all_year_primary'] and near['beats_uniform_all_years']) or (
            near['cycle25_primary'] and near['cycle25_bootstrap_lower_above_zero'] and near['beats_uniform_cycle25'])
        goal = [runner.meets_goal(near), runner.meets_goal(uniform)]
        expected = 'N1_near_miss_helps' if specific else 'N2_reweighting_only' if any(goal) else 'N3_no_gain'
        assert decision['reading'] == expected and decision['reading'] in runner.READINGS
        assert decision['near_miss_w3_goal_met_and_beats_uniform'] == int(decision['reading'] == 'N1_near_miss_helps')
        assert decision['candidates_meeting_goal_against_control'] == [c for c, g in zip(runner.CANDIDATES, goal) if g]
        seen.add(decision['reading'])
    assert seen == set(runner.READINGS)
    passing = dict(zip(keys, [False, True, True]))
    failing = dict(zip(keys, [False, True, False]))
    beats, loses = dict(beats_uniform_all_years=False, beats_uniform_cycle25=True), dict(beats_uniform_all_years=False, beats_uniform_cycle25=False)
    assert runner.read({'near_miss_w3': {**passing, **beats}, 'uniform_matched': passing})['outcome_label'] == 'result:goal-met'
    assert runner.read({'near_miss_w3': {**passing, **loses}, 'uniform_matched': failing})['outcome_label'] == 'result:partial'
    assert runner.read({'near_miss_w3': {**failing, **beats}, 'uniform_matched': passing})['outcome_label'] == 'result:partial'
    assert runner.read({'near_miss_w3': {**failing, **beats}, 'uniform_matched': failing})['outcome_label'] == 'result:no-gain'


def test_frozen_protocol_matches_the_idea_and_the_adopted_basis():
    text = CONFIG.read_text()
    config = json.loads(text)
    v2 = json.loads((ROOT/'config/activity-history-v2.json').read_text())
    runner.check_protocol(config)
    assert config['id'] == 'near-miss-weighting-v1' and config['status'] == 'frozen_before_any_candidate_result'
    assert config['reserved_test_accessed'] is False and not {chr(0x2013), chr(0x2014)} & set(text)
    assert config['years'] == v2['years'] == [2014, 2015, 2016, 2017, 2022, 2023] and config['alert_fallback_years'] == [2022]
    assert [c['id'] for c in config['candidates']] == ['near_miss_w3', 'uniform_matched'] and config['control']['id'] == 'control'
    assert config['weighting']['factor'] == 3 and config['weighting']['span_hours'] == 72
    assert config['budget']['constituent_fits'] == 24 and config['budget']['hyperparameter_search'] == 0 and config['budget']['downloads'] == 0
    evidence = config['evidence']
    assert evidence['table'] == 'artifacts/relabelled_development_20261111_r1' and evidence['control'] == 'artifacts/walk_forward_v2_20261112_r1'
    assert evidence['table_report_sha256'] == v2['evidence']['table_report_sha256']
    assert evidence['control_report_sha256'] == v2['evidence']['control_report_sha256']
    assert sha256(ROOT/evidence['pipeline_protocol']) == evidence['pipeline_protocol_sha256']
    assert sha256(ROOT/evidence['base_protocol']) == evidence['base_protocol_sha256']
    assert config['acceptance']['per_year_primary'] == v2['acceptance']['per_year_primary']
    assert set(config['reading']) == {*runner.READINGS, 'exclusive'}
    assert config['acceptance_rule'] == {**config['acceptance_rule'], 'metric_path': 'decision.near_miss_w3_goal_met_and_beats_uniform',
                                         'op': '>=', 'value': 1}
    assert set(config['population'])-{'source'} == {str(year) for year in config['years']}
    for year in config['years']:
        counts = config['population'][str(year)]
        assert counts['train_rows'] == counts['train_positives']+counts['train_negatives']
        assert 0 < counts['near_miss_negatives'] < counts['train_negatives']
    assert 'alert-cooldown' not in text


@pytest.mark.parametrize('change', [
    lambda c: c['candidates'].append({'id': 'near_miss_w5'}),
    lambda c: c['candidates'].reverse(),
    lambda c: c['weighting'].update(factor=5),
    lambda c: c['weighting'].update(span_hours=48),
    lambda c: c['years'].append(2024),
    lambda c: c['years'].remove(2022),
    lambda c: c['budget'].update(constituent_fits=48),
    lambda c: c.update(reserved_test_accessed=True),
    lambda c: c.update(status='design_proposed'),
    lambda c: c.update(alert_fallback_years=[2021]),
])
def test_runner_refuses_a_changed_protocol(change):
    config = json.loads(CONFIG.read_text())
    change(config)
    with pytest.raises(ValueError):
        runner.check_protocol(config)


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
    folds, hashes = [], {}
    for year in YEARS:
        split, audit = annual_fold(meta, year)
        (control_dir/str(year)).mkdir(parents=True)
        evaluation = split['evaluation']
        score = development.loc[evaluation.index, FEATURE_COLUMNS[0]].to_numpy(dtype=float)
        evaluation[['harp', 'forecast_time', 'target']].assign(ensemble=1/(1+np.exp(-score))).to_parquet(
            control_dir/str(year)/'predictions.parquet', index=False)
        (control_dir/str(year)/'thresholds.json').write_text(json.dumps(stored_thresholds(year)))
        folds.append({'year': year, 'audit': audit, 'status': 'complete'})
        hashes.update({f'{year}/{name}': sha256(control_dir/str(year)/name) for name in ['predictions.parquet', 'thresholds.json']})
    (control_dir/'report.json').write_text(json.dumps({'folds': folds, 'artifact_hashes': hashes}))
    base = json.loads((ROOT/'config/walk-forward-v1.json').read_text())
    base['candidates']['xgboost']['n_estimators'] = 8
    (directory/'base.json').write_text(json.dumps(base))
    config = json.loads(CONFIG.read_text())
    config.update(years=YEARS, population=population(meta, YEARS))
    config['budget']['constituent_fits'] = 8
    config['evidence'].update(table=str(table_dir), table_report_sha256=sha256(table_dir/'report.json'), control=str(control_dir),
                              control_report_sha256=sha256(control_dir/'report.json'), base_protocol=str(directory/'base.json'),
                              base_protocol_sha256=sha256(directory/'base.json'),
                              pipeline_protocol=str(ROOT/'config/walk-forward-v2.json'))
    (directory/'config.json').write_text(json.dumps(config))
    return directory/'config.json'


@pytest.fixture(scope='module')
def executed(tmp_path_factory, development):
    directory = tmp_path_factory.mktemp('near_miss')
    config_path = write_inputs(directory, development)
    result, table = runner.run(config_path, directory/'output')
    return directory, config_path, result, table


def test_run_on_synthetic_inputs_freezes_phase_one_before_labels(executed):
    directory, config_path, result, table = executed
    output = directory/'output'
    phase1 = json.loads((output/'phase1.json').read_text())
    assert set(phase1) == {'thresholds.json', 'weights.csv', 'probabilities_2022.parquet', 'probabilities_2023.parquet'}
    assert all(sha256(output/name) == value for name, value in phase1.items())
    assert result['phase1_sha256'] == sha256(output/'phase1.json') and result['thresholds_sha256'] == phase1['thresholds.json']
    assert result['config_sha256'] == sha256(config_path) and result['constituent_fits'] == 8
    for year in YEARS:
        assert list(pd.read_parquet(output/f'probabilities_{year}.parquet').columns) == ['harp', 'forecast_time', *runner.CANDIDATES]
    thresholds = json.loads((output/'thresholds.json').read_text())
    assert all(set(thresholds[str(year)]) == {'control', *runner.CANDIDATES} for year in YEARS)
    assert all(thresholds[str(year)]['control'] == stored_thresholds(year) for year in YEARS)
    assert result['reserved_test_accessed'] is False and result['model_promoted'] is False and result['threshold_adopted'] is False
    assert result['alert_fallback_years_control'] == [2022]
    assert result['artifact_hashes'].keys() >= {'results.csv', 'intervals.csv', 'phase1.json', 'predictions_2022.parquet'}


def test_run_reports_every_candidate_and_one_reading(executed):
    _, _, result, table = executed
    assert set(zip(table.year, table.candidate, table.tier)) == set(itertools.product(YEARS, ['control', *runner.CANDIDATES], ['watch', 'alert']))
    alert = table[table.tier.eq('alert')].set_index(['year', 'candidate'])
    assert bool(alert.loc[(2022, 'control'), 'fallback']) and not bool(alert.loc[(2023, 'control'), 'fallback'])
    assert alert.loc[(2022, 'control'), 'threshold'] == 0.6
    assert alert.missed_positive_runs.notna().all() and alert.alert_fp_share_within_72h_of_positive.dropna().between(0, 1).all()
    decision = result['decision']
    assert result['reading'] == decision['reading'] and decision['reading'] in runner.READINGS
    assert decision['near_miss_w3_goal_met_and_beats_uniform'] == int(decision['reading'] == 'N1_near_miss_helps')
    assert set(result['acceptance']) == {'control', *runner.CANDIDATES}
    assert {'beats_uniform_all_years', 'beats_uniform_cycle25', 'all_year_primary', 'cycle25_primary'} <= set(result['acceptance']['near_miss_w3'])
    assert [row['year'] for row in result['weighting']['per_year']] == YEARS


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
    refused(lambda c: c.update(alert_fallback_years=[2023]), 'fallback')
    refused(lambda c: c['years'].append(2024), 'reserved')
    assert not (tmp_path/'control_hash_output').exists() and not (tmp_path/'reserved_output').exists()


def test_run_refuses_changed_control_files_and_labels(tmp_path, development):
    config_path = write_inputs(tmp_path, development)
    thresholds = tmp_path/'control/2023/thresholds.json'
    original = thresholds.read_text()
    thresholds.write_text(original.replace('0.6', '0.7'))
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
        runner.run(config_path, tmp_path/'changed_labels', fit=stub_fit([]))
