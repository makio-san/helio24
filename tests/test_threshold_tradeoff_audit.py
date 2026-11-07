import pandas as pd
import pytest
from scripts.audit_threshold_tradeoff import largest_threshold, verdict


def frame():
    return pd.DataFrame({'target': [1, 1, 1, 1, 0, 0], 'arm': [.9, .8, .7, .6, .85, .5]})


def test_largest_threshold_keeps_required_share_of_positives():
    assert largest_threshold(frame(), 'arm', 1.0) == .6
    assert largest_threshold(frame(), 'arm', .75) == .7
    assert largest_threshold(frame(), 'arm', .5) == .8
    assert largest_threshold(frame(), 'arm', .01) == .9


def test_unreachable_recall_target_fails():
    with pytest.raises(ValueError):
        largest_threshold(frame(), 'arm', 1.5)


def test_verdict_requires_every_positive_year_and_otherwise_is_mixed():
    assert verdict([True]*6, [False]*6, 6) == 'persistence_adds_value'
    assert verdict([False]*6, [True]*6, 6) == 'threshold_at_least_as_good'
    assert verdict([True]*5+[False], [False]*5+[True], 6) == 'mixed'
    assert verdict([True]*5, [False]*5, 6) == 'mixed'
