import json
from pathlib import Path

import numpy as np
import pandas as pd

from helio24.walk_forward import annual_fold
from scripts.audit_horizon_72h import extend_labels, read

ROOT = Path(__file__).resolve().parents[1]
START = pd.Timestamp('2020-03-01 00:59:26', tz='UTC')


def windows(hours, event_hours=(), harp=1, jitter=False):
    """Hourly windows at the given hour offsets; a window is positive when an event lies in [t, t+24h)."""
    frame = pd.DataFrame({'harp': harp, 'forecast_time': [START+pd.Timedelta(hours=int(h)) for h in hours]})
    if jitter:
        frame.loc[frame.index[len(frame)//2:], 'forecast_time'] += pd.Timedelta(seconds=1)
    frame['target'] = [int(any(h <= e < h+24 for e in event_hours)) for h in hours]
    frame['observation_start'] = frame.forecast_time-pd.Timedelta(hours=12)
    frame['label_status'] = np.where(frame.target.eq(1), 'positive', 'negative')
    return frame


def label_at(result, hour):
    row = result[result.forecast_time.eq(START+pd.Timedelta(hours=hour))]
    return None if row.empty else int(row.target.iloc[0])


def test_label_is_or_of_the_next_three_days_of_windows():
    result = extend_labels(windows(range(0, 200), event_hours=[100.5]))
    # An event at hour 100.5 lies in [t, t+72h) for t in (28.5, 100.5].
    assert label_at(result, 28) == 0 and label_at(result, 29) == 1 and label_at(result, 100) == 1 and label_at(result, 101) == 0
    assert result.prediction_end.sub(result.forecast_time).eq(pd.Timedelta(hours=72)).all()
    assert (result.target24 == windows(range(0, 200), event_hours=[100.5]).set_index(['forecast_time']).loc[result.forecast_time, 'target'].to_numpy()).all()
    assert set(result.label_status) == {'positive', 'negative'}


def test_windows_without_covered_horizon_are_removed_whatever_their_label():
    result = extend_labels(windows(range(0, 100), event_hours=[95.5]))
    # Windows after hour 51 have no window at t+48h; they are removed, positive or not.
    assert result.forecast_time.max() == START+pd.Timedelta(hours=51)
    assert label_at(result, 52) is None and label_at(result, 51) == 1


def test_small_gaps_are_bridged_and_large_gaps_remove_the_window():
    small = windows([h for h in range(0, 120) if not 20 <= h <= 30], event_hours=[60.5])
    assert label_at(extend_labels(small), 0) == 1
    large = windows([h for h in range(0, 120) if not 10 <= h <= 40], event_hours=[60.5])
    result = extend_labels(large)
    assert label_at(result, 0) is None and label_at(result, 41) == 1


def test_leap_second_jitter_keeps_the_hour_grid():
    result = extend_labels(windows(range(0, 100), event_hours=[60.5], jitter=True))
    assert label_at(result, 0) is None or label_at(result, 0) == 1
    assert len(result) == 52 and result.target.sum() > 0


def test_two_windows_in_one_hour_stop_the_build():
    frame = windows(range(0, 80))
    frame.loc[len(frame)] = frame.iloc[5]
    frame.loc[len(frame)-1, 'forecast_time'] += pd.Timedelta(minutes=10)
    try:
        extend_labels(frame)
    except ValueError:
        return
    raise AssertionError('Expected ValueError')


def test_annual_fold_purges_windows_whose_72_hour_horizon_reaches_the_next_role():
    start = pd.Timestamp('2021-12-20 00:00', tz='UTC')
    frame = pd.DataFrame({'harp': 1, 'forecast_time': [start+pd.Timedelta(hours=h) for h in range(0, 24*20)]})
    frame['target'] = 0
    frame['observation_start'] = frame.forecast_time-pd.Timedelta(hours=12)
    frame['label_status'] = 'negative'
    result = extend_labels(frame)
    split, _ = annual_fold(result, 2022)
    assert split['calibration'].prediction_end.max() <= pd.Timestamp('2022-01-01', tz='UTC')
    assert split['calibration'].forecast_time.max() <= pd.Timestamp('2021-12-29 00:00', tz='UTC')


def test_reading_and_frozen_protocol():
    goal = dict(all_years_goal=True, **{'years_precision_at_least_0.50': list(range(6))})
    assert read(goal) == 'W1_goal_met_on_72h'
    assert read(dict(all_years_goal=False, **{'years_precision_at_least_0.50': [1, 2, 3, 4]})) == 'W2_partial'
    assert read(dict(all_years_goal=False, **{'years_precision_at_least_0.50': [1, 2, 3]})) == 'W3_no_gain'
    config = json.loads((ROOT/'config/horizon-72h-v1.json').read_text())
    v2 = json.loads((ROOT/'config/activity-history-v2.json').read_text())
    assert config['status'] == 'frozen_before_any_candidate_result' and config['reserved_test_accessed'] is False
    assert config['years'] == v2['years'] and [c['id'] for c in config['candidates']] == ['m24', 'm72']
    assert config['evidence']['table_report_sha256'] == v2['evidence']['table_report_sha256']
    assert set(config['reading']) == {'W1_goal_met_on_72h', 'W2_partial', 'W3_no_gain'}
