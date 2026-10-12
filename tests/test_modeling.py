import numpy as np

from helio24.modeling import metrics, select_threshold, reliability_table


def test_false_alarm_denominators_are_distinct():
    result = metrics([1, 1, 0, 0, 0], [0.9, 0.1, 0.8, 0.2, 0.1], 0.5)
    assert (result['tp'], result['fp'], result['fn'], result['tn']) == (1, 1, 1, 2)
    assert result['recall'] == 0.5
    assert result['precision'] == 0.5
    assert result['false_positive_rate'] == 1/3
    assert result['false_alarm_ratio'] == 0.5


def test_constant_baseline_has_zero_skill():
    threshold, _ = select_threshold([0, 0, 1, 0], np.full(4, 0.25))
    result = metrics([0, 0, 1, 0], np.full(4, 0.25), threshold)
    assert result['tss'] == 0
    assert result['fp'] == 0


def test_threshold_finds_validation_operating_point():
    threshold, _ = select_threshold([0, 1, 0, 1], np.array([0.1, 0.7, 0.2, 0.8]))
    assert threshold == 0.7


def test_calibration_retains_counts_and_boundary_probabilities():
    result = reliability_table([0, 1, 0, 1], [0.0, 0.3, 0.3, 1.0])
    assert result['count'].sum() == 4
    assert result.loc[result['count'].eq(2), 'observed_rate'].iloc[0] == 0.5
