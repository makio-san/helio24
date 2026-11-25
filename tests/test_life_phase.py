"""Synthetic tests of config/life-phase-v1.json, helio24.life_phase and the runner; no project data or evidence is read."""
import copy
import itertools
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import scripts.audit_life_phase as runner
from helio24.data import FEATURE_COLUMNS
from helio24.full_data import sha256
from helio24.life_phase import AGE, GAP, KEY, PHASE_COLUMNS, SOURCE_COLUMNS, life_phase_features
from helio24.v2_training import METADATA
from helio24.walk_forward import annual_fold
from scripts.audit_activity_history_relabelled import fit_probabilities

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT/'config/life-phase-v1.json'
YEARS = [2022, 2023]
HOUR = pd.Timedelta(hours=1)
START = pd.Timestamp('2015-03-01', tz='UTC')


def series(harp, hours, values=None, start=START):
    """Windows of one HARP at the given hours; `values` fills USFLUX__mean, the other sources stay at 1."""
    frame = pd.DataFrame({'harp': harp, 'forecast_time': [start+int(h)*HOUR for h in hours]})
    for column in SOURCE_COLUMNS:
        frame[column] = 1.0
    if values is not None:
        frame['USFLUX__mean'] = np.asarray(values, dtype=float)
    return frame


def harp_windows(harp, start, hours, positive_hours=()):
    frame = pd.DataFrame({'harp': harp, 'forecast_time': [pd.Timestamp(start, tz='UTC')+int(h)*HOUR for h in hours]})
    frame['target'] = [int(h in set(positive_hours)) for h in hours]
    frame['observation_start'] = frame.forecast_time-12*HOUR
    frame['prediction_end'] = frame.forecast_time+24*HOUR
    frame['label_status'] = np.where(frame.target.eq(1), 'positive', 'negative')
    frame['missing_fraction'] = 0.0
    return frame


def synthetic_development(seed=24):
    """Eight HARPs a year from 2018 to 2023, up to 240 hourly windows each; every second HARP has one positive day, every third a gap."""
    rng = np.random.default_rng(seed)
    parts, harp = [], 0
    for year in range(2018, 2024):
        for k in range(8):
            harp += 1
            start = pd.Timestamp(f'{year}-02-01')+pd.Timedelta(days=30*k)
            hours = [h for h in range(240) if not (k % 3 == 0 and 150 <= h < 171)]
            part = harp_windows(harp, start, hours, range(100, 124) if k % 2 == 0 else ())
            part['flaring'] = int(k % 2 == 0)
            parts.append(part)
    table = pd.concat(parts, ignore_index=True)
    values = rng.normal(size=(len(table), len(FEATURE_COLUMNS))).astype(np.float32)
    values[:, 0] += 2*table.target.to_numpy()+table.flaring.to_numpy()
    table = pd.concat([table.drop(columns='flaring'), pd.DataFrame(values, columns=FEATURE_COLUMNS)], axis=1)
    table[SOURCE_COLUMNS] = table[SOURCE_COLUMNS]+5
    year = table.forecast_time.dt.year
    table['role'] = np.where(year <= 2021, 'train', np.where(year == 2022, 'calibration', 'validation'))
    return table


def life_of(development):
    return life_phase_features(development[[*KEY, *SOURCE_COLUMNS]])


def population(development, life, years):
    out = {}
    for year in years:
        split, _ = annual_fold(runner.blind(development[runner.META], year), year)
        out[str(year)] = runner.fold_population(split, {role: life.loc[group.index] for role, group in split.items()})
    return out


def stored_thresholds(year):
    return {'watch': {'threshold': 0.2}, 'comparison_recall_0.95': {'threshold': 0.1},
            'alert': {'threshold': 0.6, 'calibration_recall': 0.5, 'calibration_precision': 0.4, 'fallback': year == 2022}}


def stub_fit(calls):
    def fit(base, groups, contexts, columns):
        calls.append(dict(columns=list(columns), rows={role: len(group) for role, group in groups.items()},
                          evaluation_columns=set(groups['evaluation'].columns),
                          aligned=all(contexts[role].index.equals(groups[role].index) for role in groups)))
        scale = 1+len(columns)/100
        score = {role: groups[role][FEATURE_COLUMNS[0]].to_numpy(dtype=float) for role in ['calibration', 'evaluation']}
        return 1/(1+np.exp(-scale*score['calibration'])), 1/(1+np.exp(-scale*score['evaluation']))
    return fit


@pytest.fixture(scope='module')
def development():
    return synthetic_development()


@pytest.fixture(scope='module')
def phase_inputs(development):
    table = development[[*runner.META, *FEATURE_COLUMNS]]
    life = life_of(development)
    config = {'years': YEARS, 'budget': {'constituent_fits': 8}, 'population': population(development, life, YEARS)}
    pipeline = json.loads((ROOT/'config/walk-forward-v2.json').read_text())
    folds = {year: annual_fold(table[runner.META], year)[1] for year in YEARS}
    return config, pipeline, table, life, folds, {year: stored_thresholds(year) for year in YEARS}


def phase(inputs, table=None, config=None, fit=None):
    base_config, pipeline, base_table, life, folds, thresholds = inputs
    return runner.fit_phase(config or base_config, {}, pipeline, base_table if table is None else table, life, folds, thresholds,
                            fit=fit or stub_fit([]))


def test_features_follow_the_frozen_definitions():
    frame = series(1, range(5), [2, 4, 3, 8, 6])
    life = life_phase_features(frame)
    assert list(life.columns) == [AGE, *PHASE_COLUMNS, GAP] and len(PHASE_COLUMNS) == 36
    assert np.allclose(life[AGE], np.log1p(np.arange(5)))
    assert np.allclose(life['life__USFLUX__ratio_to_running_max'], [np.nan, 2, 0.75, 2, 0.75], equal_nan=True)
    assert np.allclose(life['life__USFLUX__hours_since_running_max'], [np.nan, 1, 1, 2, 1], equal_nan=True)
    # Earlier windows of hour 3 are 2, 4, 3 (mean 3, population variance 2/3); of hour 4 they are 2, 4, 3, 8.
    expected = [np.nan, np.nan, 0, 5/np.sqrt(2/3), (6-4.25)/np.sqrt(5.1875)]
    assert np.allclose(life['life__USFLUX__running_z'], expected, equal_nan=True)
    # A constant measurement: ratio 1, no z, and the maximum was first attained at the first window.
    assert np.allclose(life['life__TOTPOT__ratio_to_running_max'], [np.nan, 1, 1, 1, 1], equal_nan=True)
    assert life['life__TOTPOT__running_z'].isna().all()
    assert np.allclose(life['life__TOTPOT__hours_since_running_max'], [np.nan, 1, 2, 3, 4], equal_nan=True)
    assert life[[c for c in PHASE_COLUMNS if 'change' in c]].isna().all().all() and not life[GAP].any()


def test_ratio_and_z_are_clipped_and_a_zero_maximum_gives_no_ratio():
    life = life_phase_features(series(1, range(6), [0, 0, 1e-30, 5, 5, 5+1e9]))
    ratio, z = life['life__USFLUX__ratio_to_running_max'], life['life__USFLUX__running_z']
    assert ratio.iloc[:3].isna().all() and ratio.iloc[3] == 100 and ratio.iloc[4] == 1
    assert z.iloc[5] == 100 and np.isfinite(life[[AGE, *PHASE_COLUMNS]].to_numpy(dtype=np.float32)[~life[[AGE, *PHASE_COLUMNS]].isna().to_numpy()]).all()
    negative = life_phase_features(series(1, range(4), [5, 5.5, 5, -1e9]))
    assert negative['life__USFLUX__running_z'].iloc[3] == -100


def test_lags_use_the_latest_earlier_window_and_never_flag_an_absent_one():
    hours = [h for h in range(120) if not 30 <= h < 41]
    life = life_phase_features(series(1, hours, hours))
    life.index = hours
    change = life['life__USFLUX__change_24h']
    assert change[[h for h in hours if h < 24]].isna().all() and change[[h for h in hours if h >= 24]].notna().all()
    # Hour 60 minus 24 is hour 36, which is not stored: the reference is hour 29, the latest stored window before it.
    assert change[60] == 31 and change[50] == 24 and change[100] == 24
    assert life.loc[75, 'life__USFLUX__change_72h'] == 72 and life.loc[110, 'life__USFLUX__change_72h'] == 81
    for lag in [24, 48, 72]:
        missing = life[f'life__USFLUX__change_{lag}h'].isna()
        assert missing.equals(pd.Series([h < lag for h in hours], index=hours))
    # The reporting flag sees the gap for 72 hours after it; no model column does.
    assert [h for h in hours if life.loc[h, GAP]] == list(range(41, 113))
    assert GAP not in sum(runner.CANDIDATES.values(), []) and not any('count' in c for c in [AGE, *PHASE_COLUMNS])
    # Which model values are missing is the same with and without the gap: no missing-value indicator can state it.
    complete = life_phase_features(series(1, range(120), range(120)))
    assert complete.loc[hours, [AGE, *PHASE_COLUMNS]].isna().equals(life[[AGE, *PHASE_COLUMNS]].isna())


def test_features_use_only_earlier_windows_of_the_same_harp():
    rng = np.random.default_rng(5)
    frames = []
    for harp in [3, 1, 2]:
        frame = series(harp, range(150))
        frame[SOURCE_COLUMNS] = rng.lognormal(size=(150, len(SOURCE_COLUMNS)))
        frames.append(frame)
    table = pd.concat(frames, ignore_index=True)
    full = life_phase_features(table)
    # Row order does not matter.
    shuffled = table.sample(frac=1, random_state=2)
    assert life_phase_features(shuffled).loc[table.index].equals(full)
    # Cutting the later windows away, or changing them, leaves every earlier window as it was.
    cut = table.forecast_time < START+90*HOUR
    assert life_phase_features(table[cut]).equals(full[cut])
    changed = table.copy()
    changed.loc[~cut, SOURCE_COLUMNS] = changed.loc[~cut, SOURCE_COLUMNS]*7+3
    assert life_phase_features(changed)[cut].equals(full[cut])
    assert not life_phase_features(changed)[~cut].equals(full[~cut])
    # Another HARP changes nothing.
    other = table.copy()
    other.loc[other.harp.ne(1), SOURCE_COLUMNS] = 99.0
    assert life_phase_features(other)[other.harp.eq(1)].equals(full[table.harp.eq(1)])
    # The current window's own summary enters only its own row.
    own = table.copy()
    last = own[own.harp.eq(2)].index[-1]
    own.loc[last, SOURCE_COLUMNS] = 1234.0
    assert life_phase_features(own).drop(index=last).equals(full.drop(index=last))


@pytest.mark.parametrize('column', ['target', 'label_status', 'label_status_v2', 'role'])
def test_features_refuse_labels_label_status_and_roles(column):
    frame = series(1, range(5))
    with pytest.raises(ValueError, match='never see labels'):
        life_phase_features(frame.assign(**{column: 0}))
    with pytest.raises(ValueError):
        life_phase_features(frame.drop(columns='MEANSHR__mean'))
    with pytest.raises(ValueError):
        life_phase_features(pd.concat([frame, frame.head(1)]))


def test_phase_one_is_identical_whatever_the_evaluation_labels_are(phase_inputs):
    config, _, table, _, _, _ = phase_inputs
    single = dict(config, years=[2023], budget={'constituent_fits': 4})
    flipped = table.assign(target=table.target.where(table.forecast_time.dt.year < 2023, 1-table.target))
    first, second = phase(phase_inputs, config=single), phase(phase_inputs, table=flipped, config=single)
    assert json.dumps(first[0], sort_keys=True) == json.dumps(second[0], sort_keys=True)
    assert first[1][2023].equals(second[1][2023]) and first[2] == second[2]
    assert list(first[1][2023].columns) == ['harp', 'forecast_time', *runner.CANDIDATES, GAP]


def test_phase_one_gives_each_candidate_its_frozen_columns_and_no_evaluation_label(phase_inputs):
    calls = []
    thresholds, probabilities, coverage, fits = phase(phase_inputs, fit=stub_fit(calls))
    assert fits == 8 and [c['columns'] for c in calls] == [[AGE], [AGE, *PHASE_COLUMNS]]*2
    assert all(c['aligned'] and not {'target', 'label_status'} & c['evaluation_columns'] for c in calls)
    assert len(runner.FEATURE_COLUMNS)+len(calls[0]['columns']) == 97 and len(runner.FEATURE_COLUMNS)+len(calls[1]['columns']) == 133
    assert all(thresholds[str(year)]['control'] == stored_thresholds(year) for year in YEARS)
    assert {(row['year'], row['role']) for row in coverage} == set(itertools.product(YEARS, ['train', 'calibration', 'evaluation']))
    row = next(r for r in coverage if r['year'] == 2023 and r['role'] == 'evaluation')
    assert row['recent_gap_72h'] == int(probabilities[2023][GAP].sum()) > 0 and row[f'missing__{AGE}'] == 0
    assert row['missing__life__USFLUX__change_72h'] == 8*72


def test_phase_one_stops_on_budget_population_or_fold_changes(phase_inputs):
    config, pipeline, table, life, folds, thresholds = phase_inputs
    with pytest.raises(RuntimeError):
        phase(phase_inputs, config=dict(config, budget={'constituent_fits': 6}))
    with pytest.raises(RuntimeError):
        phase(phase_inputs, config=dict(config, budget={'constituent_fits': 10}))
    for key in runner.POPULATION:
        changed = copy.deepcopy(config)
        changed['population']['2022'][key] += 1
        with pytest.raises(ValueError):
            phase(phase_inputs, config=changed)
    other = copy.deepcopy(folds)
    other[2022][0]['rows'] += 1
    with pytest.raises(ValueError):
        runner.fit_phase(config, {}, pipeline, table, life, other, thresholds, fit=stub_fit([]))


def test_default_fit_is_the_unchanged_recipe_function():
    assert runner.fit_probabilities is fit_probabilities
    assert runner.run.__defaults__ == (fit_probabilities,) and runner.fit_phase.__defaults__ == (fit_probabilities,)
    assert runner.CONSTITUENTS == 2


def test_every_result_falls_into_exactly_one_reading():
    keys = ['all_year_primary', 'cycle25_primary', 'cycle25_bootstrap_lower_above_zero']
    seen = set()
    for values in itertools.product([False, True], repeat=8):
        life = dict(zip(keys, values[:3]), beats_age_only_all_years=values[3], beats_age_only_cycle25=values[4])
        age = dict(zip(keys, values[5:]))
        if (life['all_year_primary'] and not life['cycle25_primary']) or (age['all_year_primary'] and not age['cycle25_primary']) \
                or (life['beats_age_only_all_years'] and not life['beats_age_only_cycle25']):
            continue
        decision = runner.read({'life_phase': life, 'age_only': age})
        specific = (life['all_year_primary'] and life['beats_age_only_all_years']) or (
            life['cycle25_primary'] and life['cycle25_bootstrap_lower_above_zero'] and life['beats_age_only_cycle25'])
        goal = {'age_only': runner.meets_goal(age), 'life_phase': runner.meets_goal(life)}
        expected = 'L1_life_phase_helps' if specific else 'L2_refit_or_age_only' if any(goal.values()) else 'L3_no_gain'
        assert decision['reading'] == expected and decision['reading'] in runner.READINGS
        assert decision['life_phase_goal_met_and_beats_age_only'] == int(decision['reading'] == 'L1_life_phase_helps')
        assert decision['candidates_meeting_goal_against_control'] == [c for c in runner.CANDIDATES if goal[c]]
        assert decision['outcome_label'] == runner.LABELS[decision['reading']]
        seen.add(decision['reading'])
    assert seen == set(runner.READINGS)
    passing, failing = dict(zip(keys, [False, True, True])), dict(zip(keys, [False, True, False]))
    beats = dict(beats_age_only_all_years=False, beats_age_only_cycle25=True)
    loses = dict(beats_age_only_all_years=False, beats_age_only_cycle25=False)
    assert runner.read({'life_phase': {**passing, **beats}, 'age_only': passing})['outcome_label'] == 'result:goal-met'
    assert runner.read({'life_phase': {**passing, **loses}, 'age_only': failing})['outcome_label'] == 'result:partial'
    assert runner.read({'life_phase': {**failing, **beats}, 'age_only': passing})['outcome_label'] == 'result:partial'
    assert runner.read({'life_phase': {**failing, **beats}, 'age_only': failing})['outcome_label'] == 'result:no-gain'


def test_complete_history_counts_only_windows_without_a_recent_gap():
    frame = pd.DataFrame({'target': [1, 1, 0, 0, 1, 0], GAP: [False, False, False, False, True, True]})
    row = runner.complete_history(frame, np.array([True, False, True, False, True, True]), 2023, 'life_phase')
    assert (row['windows'], row['positives'], row['tp'], row['fp'], row['fn']) == (4, 2, 1, 1, 1)
    assert row['precision'] == 0.5 and row['recall'] == 0.5 and np.isclose(row['window_share'], 4/6) and np.isclose(row['positive_share'], 2/3)
    assert row['positive_rate_with_gap'] == 0.5 and row['positive_rate_without_gap'] == 0.5
    quiet = runner.complete_history(frame.assign(target=0), np.zeros(6, dtype=bool), 2023, 'control')
    assert quiet['precision'] is None and quiet['recall'] is None and quiet['positive_share'] is None


def test_frozen_protocol_matches_the_idea_and_the_adopted_basis():
    text = CONFIG.read_text()
    config = json.loads(text)
    v2 = json.loads((ROOT/'config/activity-history-v2.json').read_text())
    runner.check_protocol(config)
    assert config['id'] == 'life-phase-v1' and config['status'] == 'frozen_before_any_candidate_result'
    assert config['reserved_test_accessed'] is False and not {chr(0x2013), chr(0x2014)} & set(text)
    assert config['years'] == v2['years'] == [2014, 2015, 2016, 2017, 2022, 2023] and config['alert_fallback_years'] == [2022]
    assert [c['id'] for c in config['candidates']] == ['age_only', 'life_phase'] and config['control']['id'] == 'control'
    features = config['features']
    assert features['measurements'] == ['USFLUX', 'TOTUSJH', 'TOTPOT', 'SAVNCPP', 'R_VALUE', 'MEANSHR'] and features['lags_hours'] == [24, 48, 72]
    assert features['added']['age_only'] == [AGE] and features['added']['life_phase'] == [AGE, *PHASE_COLUMNS]
    assert len(features['added']['life_phase']) == 37 == config['budget']['added_features']['life_phase']
    assert set(features['source_columns']) <= set(FEATURE_COLUMNS) and features['gap_flag']['model_input'] is False
    assert config['budget']['constituent_fits'] == 24 and config['budget']['hyperparameter_search'] == 0 and config['budget']['downloads'] == 0
    evidence = config['evidence']
    assert evidence['table'] == 'artifacts/relabelled_development_20261111_r1' and evidence['control'] == 'artifacts/walk_forward_v2_20261112_r1'
    # The table and the stored control are the only evidence directories the protocol names as inputs.
    assert set(re.findall(r'(?:artifacts|data)/[A-Za-z0-9_]+', json.dumps({k: v for k, v in config.items() if k != 'leak_question'}))) \
        == {evidence['table'], evidence['control']}
    assert evidence['table_report_sha256'] == v2['evidence']['table_report_sha256']
    assert evidence['control_report_sha256'] == v2['evidence']['control_report_sha256']
    assert sha256(ROOT/evidence['pipeline_protocol']) == evidence['pipeline_protocol_sha256']
    assert sha256(ROOT/evidence['base_protocol']) == evidence['base_protocol_sha256']
    assert config['acceptance']['per_year_primary'] == v2['acceptance']['per_year_primary']
    assert set(config['reading']) == {*runner.READINGS, 'exclusive'}
    assert all(runner.LABELS[name] in config['reading'][name] for name in runner.READINGS)
    assert config['acceptance_rule'] == {**config['acceptance_rule'], 'metric_path': 'decision.life_phase_goal_met_and_beats_age_only',
                                         'op': '>=', 'value': 1}
    assert set(config['population'])-{'source', 'coverage_counts'} == {str(year) for year in config['years']}
    for year in config['years']:
        counts = config['population'][str(year)]
        assert set(counts) == set(runner.POPULATION)
        assert 0 < counts['train_positives'] < counts['train_rows'] and 0 < counts['calibration_positives'] < counts['calibration_rows']
        assert 0 < counts['evaluation_recent_gap_72h'] < counts['evaluation_rows'] and 0 < counts['evaluation_younger_than_72h'] < counts['evaluation_rows']
    assert {'question', 'finding', 'mechanism', 'decision', 'residual_risk'} == set(config['leak_question'])


@pytest.mark.parametrize('change', [
    lambda c: c['candidates'].append({'id': 'life_phase_wide'}),
    lambda c: c['candidates'].reverse(),
    lambda c: c['features']['added']['age_only'].append('life__earlier_window_count_72h'),
    lambda c: c['features']['added']['life_phase'].append(GAP),
    lambda c: c['features']['added']['life_phase'].pop(),
    lambda c: c['features']['added'].update(extra=[AGE]),
    lambda c: c['features']['measurements'].append('TOTBSQ'),
    lambda c: c['features']['lags_hours'].append(96),
    lambda c: c['features']['clip'].update(running_z=10.0),
    lambda c: c['features']['gap_flag'].update(model_input=True),
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
    # The runner concatenates the roles in the order train, calibration, validation; the population is counted the same way.
    ordered = pd.concat([development[development.role.eq(role)].sort_values(['forecast_time', 'harp'])
                         for role in ['train', 'calibration', 'validation']], ignore_index=True)
    config = json.loads(CONFIG.read_text())
    config.update(years=YEARS, population=population(ordered, life_of(ordered), YEARS))
    config['budget']['constituent_fits'] = 8
    config['evidence'].update(table=str(table_dir), table_report_sha256=sha256(table_dir/'report.json'), control=str(control_dir),
                              control_report_sha256=sha256(control_dir/'report.json'), base_protocol=str(directory/'base.json'),
                              base_protocol_sha256=sha256(directory/'base.json'),
                              pipeline_protocol=str(ROOT/'config/walk-forward-v2.json'))
    (directory/'config.json').write_text(json.dumps(config))
    return directory/'config.json'


@pytest.fixture(scope='module')
def executed(tmp_path_factory, development):
    directory = tmp_path_factory.mktemp('life_phase')
    config_path = write_inputs(directory, development)
    result, table = runner.run(config_path, directory/'output')
    return directory, config_path, result, table


def test_run_on_synthetic_inputs_freezes_phase_one_before_labels(executed):
    directory, config_path, result, table = executed
    output = directory/'output'
    phase1 = json.loads((output/'phase1.json').read_text())
    assert set(phase1) == {'thresholds.json', 'features.json', 'life_coverage.csv', 'probabilities_2022.parquet', 'probabilities_2023.parquet'}
    assert all(sha256(output/name) == value for name, value in phase1.items())
    assert result['phase1_sha256'] == sha256(output/'phase1.json') and result['thresholds_sha256'] == phase1['thresholds.json']
    assert result['features_sha256'] == phase1['features.json']
    assert result['config_sha256'] == sha256(config_path) and result['constituent_fits'] == 8
    assert result['feature_counts'] == {'age_only': 97, 'life_phase': 133}
    written = json.loads((output/'features.json').read_text())
    assert written == {'age_only': [*FEATURE_COLUMNS, AGE], 'life_phase': [*FEATURE_COLUMNS, AGE, *PHASE_COLUMNS]}
    for year in YEARS:
        assert list(pd.read_parquet(output/f'probabilities_{year}.parquet').columns) == ['harp', 'forecast_time', *runner.CANDIDATES, GAP]
    thresholds = json.loads((output/'thresholds.json').read_text())
    assert all(set(thresholds[str(year)]) == {'control', *runner.CANDIDATES} for year in YEARS)
    assert all(thresholds[str(year)]['control'] == stored_thresholds(year) for year in YEARS)
    assert result['reserved_test_accessed'] is False and result['model_promoted'] is False and result['threshold_adopted'] is False
    assert result['alert_fallback_years_control'] == [2022]
    assert result['artifact_hashes'].keys() >= {'results.csv', 'intervals.csv', 'complete_history.csv', 'phase1.json', 'predictions_2022.parquet'}


def test_run_reports_every_candidate_and_one_reading(executed):
    directory, _, result, table = executed
    assert set(zip(table.year, table.candidate, table.tier)) == set(itertools.product(YEARS, ['control', *runner.CANDIDATES], ['watch', 'alert']))
    alert = table[table.tier.eq('alert')].set_index(['year', 'candidate'])
    assert bool(alert.loc[(2022, 'control'), 'fallback']) and not bool(alert.loc[(2023, 'control'), 'fallback'])
    assert alert.loc[(2022, 'control'), 'threshold'] == 0.6
    assert alert.missed_positive_runs.notna().all() and alert.alert_fp_share_within_72h_of_positive.dropna().between(0, 1).all()
    decision = result['decision']
    assert result['reading'] == decision['reading'] and decision['reading'] in runner.READINGS
    assert decision['life_phase_goal_met_and_beats_age_only'] == int(decision['reading'] == 'L1_life_phase_helps')
    assert set(result['acceptance']) == {'control', *runner.CANDIDATES}
    assert {'beats_age_only_all_years', 'beats_age_only_cycle25', 'all_year_primary', 'cycle25_primary'} <= set(result['acceptance']['life_phase'])
    complete = pd.read_csv(directory/'output/complete_history.csv')
    assert set(zip(complete.year, complete.candidate)) == set(itertools.product(YEARS, ['control', *runner.CANDIDATES]))
    assert complete.window_share.between(0, 1, inclusive='neither').all()
    intervals = pd.read_csv(directory/'output/intervals.csv')
    assert set(zip(intervals.candidate, intervals.reference)) == {('age_only', 'control'), ('life_phase', 'control'), ('life_phase', 'age_only')}


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
    refused(lambda c: c.update(alert_fallback_years=[2023]), 'fallback')
    refused(lambda c: c['years'].append(2024), 'reserved')
    refused(lambda c: c['features']['added']['life_phase'].append(GAP), 'gap_input')
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
