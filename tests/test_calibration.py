import numpy as np
import pandas as pd
import pytest

from helio24.calibration import SigmoidCalibration, recall_threshold, split_roles, cluster_intervals, paired_brier_interval


def test_sigmoid_is_monotonic_and_improves_miscalibrated_probabilities():
    p = np.repeat([.01, .1, .4], 100)
    y = np.concatenate([np.r_[np.ones(n), np.zeros(100-n)] for n in [10, 40, 80]])
    model = SigmoidCalibration().fit(p, y)
    calibrated = model.transform(p)
    assert model.slope > 0
    assert np.all(np.diff(calibrated) >= 0)
    assert np.mean((calibrated-y)**2) < np.mean((p-y)**2)
    with pytest.raises(ValueError):
        model.fit([.1, .2], [0, 0])


def test_recall_target_selects_fewest_false_alarms():
    y = np.array([1, 0, 1, 0, 1])
    p = np.array([.9, .8, .7, .6, .5])
    assert recall_threshold(y, p, .6) == .7
    assert recall_threshold(y, p, .95) == .5


def test_monotonic_calibration_preserves_alarm_sets():
    y = np.array([1, 0, 1, 0, 1])
    p = np.array([.9, .8, .7, .6, .5])
    c = SigmoidCalibration(slope=.7, intercept=-1).transform(p)
    np.testing.assert_array_equal(p >= recall_threshold(y, p, .8), c >= recall_threshold(y, c, .8))


def test_cluster_bootstrap_keeps_windows_within_regions_together():
    # One region has 100 hits; the other has 100 misses. Region resampling gives
    # [0, 1], whereas independently resampling 200 rows yields a narrow interval.
    y = np.ones(200)
    p = np.repeat([.9, .1], 100)
    harp = np.repeat([1, 2], 100)
    ci = cluster_intervals(y, p, harp, .5, draws=100)
    assert ci['recall']['lower'] == 0
    assert ci['recall']['upper'] == 1
    assert ci['precision']['undefined_draws'] > 0
    assert ci['false_positive_rate']['undefined_draws'] == 100
    delta = paired_brier_interval(y, p, p, harp, draws=100)
    assert delta['estimate'] == delta['lower'] == delta['upper'] == 0


def test_four_roles_purge_boundaries_and_shared_harps():
    rows = []
    for partition in range(1, 6):
        for y in [0, 1]:
            start = pd.Timestamp(f'201{partition}-01-01')
            rows.append(dict(partition=partition, harp=partition*10+y, target=y,
                             observation_start=start, forecast_time=start+pd.Timedelta(hours=12),
                             prediction_end=start+pd.Timedelta(hours=36)))
    rows.append(dict(rows[4], harp=10))
    rows.append(dict(rows[2], harp=999, observation_start=pd.Timestamp('2012-12-31 12:00'),
                     forecast_time=pd.Timestamp('2013-01-01'), prediction_end=pd.Timestamp('2013-01-02')))
    groups, audit = split_roles(pd.DataFrame(rows))
    assert [len(group) for group in groups.values()] == [4, 2, 2, 2]
    assert len(set().union(*(set(group.harp) for group in groups.values()))) == 10
    assert sum(item.get('shared_harp_rows_removed', 0) for item in audit) == 1
    assert sum(item.get('boundary_removed', 0) for item in audit) == 1
