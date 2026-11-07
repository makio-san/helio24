import numpy as np
import pandas as pd
import pytest
from scripts.audit_threshold_selection import positive_run_maxima, run_recall_threshold, select_thresholds


def frame():
    times = pd.date_range('2020-01-01', periods=8, freq='h', tz='UTC')
    # one HARP: positive run of 3 (hours 0-2), negatives, positive run of 2 (hours 5-6), negative
    return pd.DataFrame({'harp': 1, 'forecast_time': times, 'target': [1, 1, 1, 0, 0, 1, 1, 0]})


PROBABILITY = np.array([.2, .9, .3, .5, .1, .4, .35, .05])


def test_positive_run_maxima_group_consecutive_hours_per_harp():
    assert sorted(positive_run_maxima(frame(), PROBABILITY)) == [.4, .9]


def test_run_rule_ignores_missed_windows_inside_an_alarmed_run():
    # full run recall needs t <= .4; window recall would also need the .2 window
    assert run_recall_threshold(frame(), PROBABILITY, 1.0) == .4
    assert run_recall_threshold(frame(), PROBABILITY, .5) == .9


def test_window_and_run_rules_differ_and_use_calibration_labels_only():
    rules = [{'id': 'w', 'basis': 'window_recall', 'target': 1.0}, {'id': 'r', 'basis': 'positive_run_recall', 'target': 1.0}]
    chosen = select_thresholds(frame(), PROBABILITY, rules)
    assert chosen == {'w': .2, 'r': .4}


def test_run_rule_requires_both_classes():
    only_positive = frame().assign(target=1)
    with pytest.raises(ValueError):
        run_recall_threshold(only_positive, PROBABILITY, .9)
