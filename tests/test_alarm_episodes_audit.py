import pandas as pd
from scripts.audit_alarm_episodes import summarize


def frame(probabilities, targets, harp=1, start='2020-01-01', gap_after=None):
    times = list(pd.date_range(start, periods=len(probabilities), freq='h', tz='UTC'))
    if gap_after is not None:
        times = times[:gap_after]+[t+pd.Timedelta(hours=5) for t in times[gap_after:]]
    return pd.DataFrame({'harp': harp, 'forecast_time': times, 'target': targets,
                         'missing_fraction': 0.0, 'arm': probabilities})


def test_consecutive_alarm_windows_form_one_episode_and_count_a_hit():
    data = frame([.9, .9, .9, .1], [0, 1, 0, 0])
    out = summarize(data, 'arm', .5)
    assert (out['alarm_windows'], out['episodes'], out['hit_episodes']) == (3, 1, 1)
    assert out['episode_precision'] == 1.0 and out['window_precision'] == 1/3


def test_gap_splits_episodes_and_all_negative_episode_is_false():
    data = frame([.9, .9, .9, .9], [0, 0, 1, 1], gap_after=2)
    out = summarize(data, 'arm', .5)
    assert (out['episodes'], out['hit_episodes'], out['all_negative_episodes']) == (2, 1, 1)
    assert out['episode_false_alarm_ratio'] == .5


def test_no_alarms_leaves_episode_ratios_undefined():
    out = summarize(frame([.1, .2], [0, 0]), 'arm', .5)
    assert out['episodes'] == 0 and out['episode_precision'] is None


def test_positive_runs_are_detected_when_any_window_alarms():
    data = frame([.1, .9, .1, .1, .1, .9], [1, 1, 0, 0, 1, 0])
    out = summarize(data, 'arm', .5)
    assert (out['positive_runs'], out['positive_runs_alarmed'], out['positive_run_recall']) == (2, 1, .5)
