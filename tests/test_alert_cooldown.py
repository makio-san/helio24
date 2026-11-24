import hashlib
import itertools
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from scripts.audit_alert_cooldown import (CANDIDATES, CLASSES, COOLDOWN_HOURS, OUTCOME, alarm_states, assert_development_period,
                                          cooldown_alarm, decision, direction_classes, read, run)

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT/'config/alert-cooldown-v1.json'
START = pd.Timestamp('2022-03-01 00:11:23', tz='UTC')


def series(hours, above=(), harp=1, start=START, positive=()):
    """Hourly windows of one HARP at the given hour offsets; probability 0.9 inside `above`, 0.1 outside."""
    return pd.DataFrame({'harp': harp, 'forecast_time': [start+pd.Timedelta(hours=int(h)) for h in hours],
                         'probability': [.9 if h in above else .1 for h in hours],
                         'target': [int(h in positive) for h in hours]})


def on_hours(frame, alarm):
    return [int(round((t-START).total_seconds()/3600)) for t in frame.forecast_time[np.asarray(alarm, dtype=bool)]]


def test_cooldown_keeps_the_first_hours_of_a_run_and_restarts_after_a_drop_below_threshold():
    frame = series(range(0, 120), above=set(range(10, 50)) | set(range(51, 60)))
    assert on_hours(frame, cooldown_alarm(frame, .5, 24)) == [*range(10, 34), *range(51, 60)]
    assert on_hours(frame, cooldown_alarm(frame, .5, 48)) == [*range(10, 50), *range(51, 60)]
    states = alarm_states(frame, .5)
    assert list(states.columns) == CANDIDATES and on_hours(frame, states.control) == [*range(10, 50), *range(51, 60)]
    # A cooldown only removes alert windows of the control.
    assert not (states.cooldown_24h & ~states.control).any() and not (states.cooldown_48h & ~states.cooldown_24h & ~states.control).any()


def test_a_gap_in_the_hourly_windows_starts_a_new_episode():
    frame = series([h for h in range(0, 80) if h != 30], above=set(range(0, 80)))
    assert on_hours(frame, cooldown_alarm(frame, .5, 24)) == [*range(0, 24), *range(31, 55)]


def test_runs_of_two_harps_never_join():
    frame = pd.concat([series(range(0, 20), above=set(range(0, 20)), harp=1),
                       series(range(20, 40), above=set(range(20, 40)), harp=2)], ignore_index=True)
    assert cooldown_alarm(frame, .5, 24).all()


def test_cooldown_is_causal_and_never_reads_a_label():
    frame = series(range(0, 100), above=set(range(5, 70)), positive=set(range(5, 29)))
    full = cooldown_alarm(frame, .5, 24)
    for cut in [10, 29, 30, 60]:
        past = frame.iloc[:cut]
        assert cooldown_alarm(past, .5, 24).tolist() == full.iloc[:cut].tolist()
    # No label column is needed, and changing the labels changes nothing.
    assert cooldown_alarm(frame.drop(columns='target'), .5, 24).tolist() == full.tolist()
    assert alarm_states(frame.assign(target=1-frame.target), .5).equals(alarm_states(frame, .5))
    shuffled = frame.sample(frac=1, random_state=3)
    assert cooldown_alarm(shuffled, .5, 24).sort_index().tolist() == full.tolist()


def test_duplicate_keys_stop_the_rule():
    frame = pd.concat([series(range(0, 5)), series([2])], ignore_index=True)
    with pytest.raises(ValueError):
        cooldown_alarm(frame, .5, 24)


def test_every_false_positive_window_gets_exactly_one_direction_class():
    flaring = series(range(0, 400), positive={100, 101, 300})
    # 60: early (40 h before 100), 150: lingering (49 h after 101), 0: other (100 h before), 173: lingering edge (exactly
    # 72 h after 101), 174: other, 227: other (73 h before 300), 240: early (60 h before 300, 139 h after 101).
    flaring['probability'] = [.9 if h in {0, 60, 150, 173, 174, 227, 240, 100} else .1 for h in range(0, 400)]
    quiet = series(range(0, 50), above={7}, harp=2)
    frame = pd.concat([flaring, quiet], ignore_index=True)
    fp = direction_classes(frame, frame.probability.ge(.5))
    got = {(int(h), int(round((t-START).total_seconds()/3600))): d for h, t, d in zip(fp.harp, fp.forecast_time, fp.direction)}
    assert got == {(1, 0): 'flaring_harp_other', (1, 60): 'early', (1, 150): 'lingering', (1, 173): 'lingering',
                   (1, 174): 'flaring_harp_other', (1, 227): 'flaring_harp_other', (1, 240): 'early', (2, 7): 'never_flaring_harp'}
    assert set(fp.direction) <= set(CLASSES)
    row = fp[fp.forecast_time.eq(START+pd.Timedelta(hours=150))].iloc[0]
    assert row.hours_since_last_positive == 49 and row.hours_to_next_positive == 150 and row.hours_to_nearest_positive == 49
    assert fp[fp.harp.eq(2)].hours_to_nearest_positive.isna().all()
    between = series(range(0, 200), above={50}, positive={20, 90})
    assert direction_classes(between, between.probability.ge(.5)).direction.tolist() == ['between']


def entry(all_year, cycle25, lower):
    return dict(all_year_primary=all_year, cycle25_primary=cycle25, cycle25_bootstrap_lower_above_zero=lower,
                goal_met=all_year or (cycle25 and lower))


def test_any_result_falls_in_exactly_one_reading_and_the_acceptance_rule_agrees():
    config = json.loads(CONFIG.read_text())
    rule = config['acceptance_rule']
    assert set(rule) == {'description', 'metric_path', 'op', 'value'} and rule['op'] == '>=' and rule['value'] == 1
    assert rule['metric_path'] == 'decision.candidates_meeting_goal'
    readings = set(config['reading'])-{'exclusive'}
    assert readings == set(OUTCOME) == {'C1_goal_met', 'C2_partial', 'C3_no_gain'}
    seen = set()
    states = [entry(a, c, b) for a, c, b in itertools.product([False, True], repeat=3) if c or not a]
    for first, second in itertools.product(states, repeat=2):
        summary = {'control': {}, 'cooldown_24h': first, 'cooldown_48h': second}
        reading = read(summary)
        assert reading in readings
        seen.add(reading)
        assert (decision(summary)['candidates_meeting_goal'] >= rule['value']) == (reading == 'C1_goal_met')
    assert seen == readings
    assert read({'cooldown_24h': entry(False, True, False), 'cooldown_48h': entry(False, False, False)}) == 'C2_partial'
    assert read({'cooldown_24h': entry(False, False, True), 'cooldown_48h': entry(False, False, False)}) == 'C3_no_gain'
    assert read({'cooldown_24h': entry(False, False, False), 'cooldown_48h': entry(False, True, True)}) == 'C1_goal_met'


def test_frozen_protocol():
    config = json.loads(CONFIG.read_text())
    v2 = json.loads((ROOT/'config/activity-history-v2.json').read_text())
    assert config['id'] == 'alert-cooldown-v1' and config['status'] == 'frozen_before_any_candidate_result'
    assert config['reserved_test_accessed'] is False
    assert config['years'] == v2['years'] == [2014, 2015, 2016, 2017, 2022, 2023] and config['alert_fallback_years'] == [2022]
    assert config['acceptance']['per_year_primary'] == v2['acceptance']['per_year_primary']
    assert config['evidence']['control'] == v2['evidence']['control'] == 'artifacts/walk_forward_v2_20261112_r1'
    assert config['evidence']['control_report_sha256'] == v2['evidence']['control_report_sha256']
    assert config['evidence']['table'] == v2['evidence']['table'] == 'artifacts/relabelled_development_20261111_r1'
    assert config['evidence']['table_report_sha256'] == v2['evidence']['table_report_sha256']
    assert {c['id']: c.get('cooldown_hours') for c in config['candidates']} == {'control': None, **COOLDOWN_HOURS}
    assert COOLDOWN_HOURS == {'cooldown_24h': 24, 'cooldown_48h': 48}
    assert set(config['descriptive']['classes']) == set(CLASSES) and config['descriptive']['near_hours'] == 72
    assert config['budget']['model_fits'] == config['budget']['downloads'] == config['budget']['new_thresholds'] == 0
    assert set(config['population']['windows']) == set(config['population']['positive_windows']) == {str(y) for y in config['years']}
    for path in [CONFIG, ROOT/'scripts/audit_alert_cooldown.py', Path(__file__)]:
        assert not set(path.read_text()) & {chr(0x2013), chr(0x2014)}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def synthetic_year(year):
    """Three HARPs: a lingering alarm after a positive run, a short alarm on a quiet HARP, an early alarm before a missed run."""
    start = pd.Timestamp(f'{year}-03-01 00:11:23', tz='UTC')
    parts = [series(range(0, 100), above=set(range(10, 70)), harp=1, start=start, positive=set(range(10, 34))),
             series(range(0, 60), above=set(range(20, 25)), harp=2, start=start),
             series(range(0, 80), above=set(range(0, 10)), harp=3, start=start, positive=set(range(20, 44)))]
    frame = pd.concat(parts, ignore_index=True).rename(columns={'probability': 'ensemble'})
    frame['prediction_end'] = frame.forecast_time+pd.Timedelta(hours=24)
    frame['missing_fraction'] = 0.0
    frame['alert_alarm'] = frame.ensemble.ge(.5)
    return frame


def build(tmp_path, years=(2022, 2023), fallback=(2022,)):
    control, table = tmp_path/'control', tmp_path/'table'
    (table/'shards').mkdir(parents=True)
    hashes, frames = {}, {}
    for year in years:
        (control/str(year)).mkdir(parents=True)
        frames[year] = synthetic_year(year)
        frames[year].to_parquet(control/str(year)/'predictions.parquet', index=False)
        thresholds = {'watch': {'threshold': .05}, 'alert': {'threshold': .5, 'calibration_recall': .2, 'calibration_precision': .5,
                                                              'fallback': year in fallback}}
        (control/str(year)/'thresholds.json').write_text(json.dumps(thresholds))
        for name in ['predictions.parquet', 'thresholds.json']:
            hashes[f'{year}/{name}'] = digest(control/str(year)/name)
    (control/'report.json').write_text(json.dumps({'artifact_hashes': hashes}))
    pd.concat(frames.values(), ignore_index=True)[['harp', 'forecast_time', 'target']].to_parquet(table/'shards/a.parquet', index=False)
    shard = table/'shards/a.parquet'
    (table/'report.json').write_text(json.dumps({'shards': [{'file': 'a.parquet', 'bytes': shard.stat().st_size, 'sha256': digest(shard)}]}))
    config = json.loads(CONFIG.read_text())
    config['evidence'].update(control=str(control), control_report_sha256=digest(control/'report.json'),
                              table=str(table), table_report_sha256=digest(table/'report.json'))
    config.update(years=list(years), alert_fallback_years=list(fallback))
    config['population'].update(windows={str(y): len(f) for y, f in frames.items()},
                                positive_windows={str(y): int(f.target.sum()) for y, f in frames.items()})
    path = tmp_path/'config.json'
    path.write_text(json.dumps(config))
    return path, config, control, table


def rewrite(path, config):
    path.write_text(json.dumps(config))
    return path


def test_synthetic_run_scores_the_cooldowns_without_models_and_writes_the_decision(tmp_path):
    path, config, control, _ = build(tmp_path)
    assert not list(control.rglob('models.joblib'))
    result, table = run(path, tmp_path/'out')
    alert = table[table.tier.eq('alert')].set_index(['year', 'candidate'])
    # Control: 24 TP and 36 lingering FP on HARP 1, 5 FP on the quiet HARP 2, 10 early FP on HARP 3 whose run is missed.
    assert alert.loc[(2022, 'control'), ['tp', 'fp', 'positive_runs', 'missed_positive_runs']].tolist() == [24, 51, 2, 1]
    assert alert.loc[(2022, 'cooldown_24h'), ['tp', 'fp', 'missed_positive_runs']].tolist() == [24, 15, 1]
    assert alert.loc[(2022, 'cooldown_48h'), ['tp', 'fp', 'fp_windows_removed', 'tp_windows_removed']].tolist() == [24, 39, 12, 0]
    assert bool(alert.loc[(2022, 'cooldown_24h'), 'primary_met']) and bool(alert.loc[(2022, 'control'), 'fallback'])
    assert not bool(alert.loc[(2023, 'control'), 'fallback'])
    assert len(table[table.tier.eq('watch')]) == 2 and set(table[table.tier.eq('watch')].candidate) == {'control'}
    directions = pd.read_csv(tmp_path/'out/directions.csv').set_index(['year', 'candidate', 'direction'])
    assert directions.loc[(2022, 'control'), 'fp_windows'].to_dict() == {'early': 10, 'lingering': 36, 'between': 0,
                                                                         'flaring_harp_other': 0, 'never_flaring_harp': 5}
    assert directions.loc[(2022, 'cooldown_24h', 'lingering'), 'control_fp_windows_removed'] == 36
    assert directions.groupby(['year', 'candidate']).fp_windows.sum().eq(alert.fp).all()
    assert result['reading'] == 'C1_goal_met' and result['outcome_label'] == 'result:goal-met'
    assert result['decision']['candidates_meeting_goal'] == 2 and result['alert_fallback_years'] == [2022]
    assert result['model_fits'] == 0 and result['downloads'] == 0 and result['reserved_test_accessed'] is False
    assert result['protocol_sha256'] == digest(path) and result['selections_sha256'] == digest(tmp_path/'out/selections.json')
    stored = json.loads((tmp_path/'out/report.json').read_text())
    node = stored
    for part in config['acceptance_rule']['metric_path'].split('.'):
        node = node[part]
    assert isinstance(node, int) and not isinstance(node, bool)
    assert stored['artifact_hashes']['selections.json'] == stored['selections_sha256']
    with pytest.raises(FileExistsError):
        run(path, tmp_path/'out')


def test_alert_states_are_fixed_before_labels_and_do_not_depend_on_them(tmp_path):
    path, _, control, table = build(tmp_path)
    run(path, tmp_path/'first')
    other = tmp_path/'relabelled'
    other.mkdir()
    path2, config2, control2, table2 = build(other)
    for year in [2022, 2023]:
        file = control2/str(year)/'predictions.parquet'
        frame = pd.read_parquet(file)
        frame['target'] = 0
        frame.to_parquet(file, index=False)
    hashes = {f'{y}/{n}': digest(control2/str(y)/n) for y in [2022, 2023] for n in ['predictions.parquet', 'thresholds.json']}
    (control2/'report.json').write_text(json.dumps({'artifact_hashes': hashes}))
    config2['evidence']['control_report_sha256'] = digest(control2/'report.json')
    with pytest.raises(ValueError, match='do not match the relabelled table'):
        run(rewrite(path2, config2), other/'out')
    # The alert states were written before the label check and are the same whatever the labels say.
    for year in [2022, 2023]:
        assert pd.read_parquet(other/f'out/alarms_{year}.parquet').equals(pd.read_parquet(tmp_path/f'first/alarms_{year}.parquet'))
        assert 'target' not in pd.read_parquet(other/f'out/alarms_{year}.parquet').columns


def test_changed_inputs_and_changed_candidates_are_refused(tmp_path):
    path, config, control, table = build(tmp_path)
    (control/'2023/thresholds.json').write_text(json.dumps({'watch': {'threshold': .05}, 'alert': {'threshold': .4, 'fallback': False}}))
    with pytest.raises(ValueError, match='Input changed'):
        run(path, tmp_path/'retuned')
    assert not (tmp_path/'retuned').exists()
    path, config, control, table = build(tmp_path/'b')
    for change in [lambda c: c['candidates'].append({'id': 'cooldown_12h', 'cooldown_hours': 12}),
                   lambda c: c['candidates'][1].update(cooldown_hours=36),
                   lambda c: c['budget'].update(model_fits=2),
                   lambda c: c['descriptive'].update(near_hours=48),
                   lambda c: c.update(reserved_test_accessed=True)]:
        changed = json.loads(path.read_text())
        change(changed)
        with pytest.raises(ValueError):
            run(rewrite(tmp_path/'changed.json', changed), tmp_path/'never')
        assert not (tmp_path/'never').exists()
    wrong = json.loads(path.read_text())
    wrong['alert_fallback_years'] = []
    with pytest.raises(ValueError, match='fallback'):
        run(rewrite(tmp_path/'fallback.json', wrong), tmp_path/'fallback')
    assert not (tmp_path/'fallback/report.json').exists()
    (table/'shards/a.parquet').write_bytes((table/'shards/a.parquet').read_bytes()+b'x')
    with pytest.raises(ValueError, match='shard changed'):
        run(path, tmp_path/'shard')


def test_reserved_period_is_refused(tmp_path):
    with pytest.raises(ValueError, match='reserved'):
        assert_development_period([pd.Timestamp('2024-01-01 00:00', tz='UTC')])
    assert_development_period([pd.Timestamp('2023-12-31 23:59', tz='UTC')])
    path, config, _, _ = build(tmp_path)
    for years in [[2022, 2023, 2024], [2025]]:
        config['years'] = years
        with pytest.raises(ValueError, match='reserved'):
            run(rewrite(tmp_path/'reserved.json', config), tmp_path/'reserved')
        assert not (tmp_path/'reserved').exists()
