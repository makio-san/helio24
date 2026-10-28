import numpy as np

from scripts.run_precision_log import operating_metrics


def test_transferred_threshold_is_not_retuned_to_validation_labels():
    probability = np.array([0.1, 0.3, 0.7, 0.9])
    first = operating_metrics(np.array([0, 0, 1, 1]), probability, 0.8)
    changed = operating_metrics(np.array([1, 1, 0, 0]), probability, 0.8)
    assert first['threshold'] == changed['threshold'] == 0.8
    assert first['alarms'] == changed['alarms'] == 1
    assert first['tp'] == 1 and changed['tp'] == 0
    assert first['recall'] == 0.5
