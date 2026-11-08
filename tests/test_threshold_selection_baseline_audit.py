import numpy as np
import pandas as pd

from scripts.audit_threshold_selection_baseline import ensemble_probability, identity_check
from helio24.data import FEATURE_COLUMNS


class Stub:
    def __init__(self, value):
        self.value = value

    def predict_proba(self, x):
        p = np.full(len(x), self.value)
        return np.column_stack([1-p, p])

    def transform(self, raw):
        return raw


def test_ensemble_probability_weights_calibrated_logistic_and_xgboost():
    stored = {'models': {'logistic': Stub(0.2), 'xgboost': Stub(0.6)},
              'calibrators': {'logistic': Stub(0), 'xgboost': Stub(0)},
              'ensemble': {'logistic_weight': 0.25}}
    features = pd.DataFrame(np.zeros((3, len(FEATURE_COLUMNS))), columns=FEATURE_COLUMNS)
    assert np.allclose(ensemble_probability(stored, features), 0.25*0.2+0.75*0.6)


def frames(shift=0.0, drop=0):
    time = pd.date_range('2020-01-01', periods=4, freq='h', tz='UTC')
    evaluation = pd.DataFrame({'harp': 1, 'forecast_time': time, 'probability': [.1, .2, .3, .4]})
    predictions = pd.DataFrame({'harp': 1, 'forecast_time': time, 'baseline': np.array([.1, .2, .3, .4])+shift})
    return evaluation, predictions.iloc[drop:]


def test_identity_check_passes_on_equal_probabilities_and_keys():
    assert identity_check(*frames())['passed']


def test_identity_check_fails_on_difference_or_key_mismatch():
    assert not identity_check(*frames(shift=1e-3))['passed']
    result = identity_check(*frames(drop=1))
    assert not result['passed'] and not result['same_keys']
