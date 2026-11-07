import pandas as pd
from scripts.audit_alarm_persistence import acceptance, evaluate, paired_bootstrap, persistent_alarm


def frame(probabilities, targets, harp=1, gap_after=None):
    times = list(pd.date_range('2020-01-01', periods=len(probabilities), freq='h', tz='UTC'))
    if gap_after is not None:
        times = times[:gap_after]+[t+pd.Timedelta(hours=5) for t in times[gap_after:]]
    return pd.DataFrame({'harp': harp, 'forecast_time': times, 'target': targets,
                         'missing_fraction': 0.0, 'arm': probabilities})


def test_alarm_starts_at_kth_consecutive_exceedance_using_only_past_windows():
    data = frame([.9, .9, .9, .9, .1, .9], [0] * 6)
    assert persistent_alarm(data, 'arm', .5, 1).tolist() == [True, True, True, True, False, True]
    assert persistent_alarm(data, 'arm', .5, 3).tolist() == [False, False, True, True, False, False]


def test_time_gap_and_harp_boundary_reset_the_count():
    data = pd.concat([frame([.9, .9, .9], [0] * 3, gap_after=2), frame([.9, .9], [0] * 2, harp=2)], ignore_index=True)
    assert persistent_alarm(data, 'arm', .5, 2).tolist() == [False, True, False, False, True]


def test_persistence_removes_short_false_episode_and_reports_alarm_delay():
    data = frame([.9, .1, .9, .9, .9, .9], [0, 0, 1, 1, 1, 0])
    control, _ = evaluate(data, 'arm', .5, 1)
    persist, per_harp = evaluate(data, 'arm', .5, 3)
    assert (control['episodes'], persist['episodes']) == (2, 1)
    assert (control['fp'], persist['fp']) == (2, 1)
    assert persist['positive_runs'] == 1 and persist['positive_runs_alarmed'] == 1
    assert persist['median_alarm_delay_hours'] == 2.0
    assert per_harp.loc[1, 'hit_episodes'] == 1


def test_acceptance_requires_all_four_conditions():
    control = dict(episode_precision=.1, fp=10, positive_runs_alarmed=5, recall=.9)
    good = dict(episode_precision=.2, fp=5, positive_runs_alarmed=5, recall=.89)
    assert all(acceptance(good, control, .02).values())
    bad = dict(good, recall=.87)
    assert not acceptance(bad, control, .02)['recall_drop_ok']


def test_bootstrap_is_paired_and_reproducible():
    index = pd.Index(range(1, 31), name='harp')
    control = pd.DataFrame({'fp': 10, 'episodes': 4, 'hit_episodes': 1}, index=index)
    candidate = pd.DataFrame({'fp': 6, 'episodes': 2, 'hit_episodes': 1}, index=index)
    first, second = paired_bootstrap(control, candidate), paired_bootstrap(control, candidate)
    assert first == second
    assert first['fp_diff']['upper'] < 0 and first['episode_precision_diff']['lower'] > 0


def test_recall_condition_is_not_applicable_without_positive_windows():
    control = dict(episode_precision=0.0, fp=10, positive_runs_alarmed=0, recall=None)
    row = dict(episode_precision=0.0, fp=5, positive_runs_alarmed=0, recall=None)
    assert acceptance(row, control, .02)['recall_drop_ok']
