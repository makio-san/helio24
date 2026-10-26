import json
from pathlib import Path

import numpy as np
import pandas as pd

from helio24.data import FEATURE_COLUMNS
from helio24.v2_training import fit_development


def protocol():
    root = Path(__file__).resolve().parents[1]
    value = json.loads((root / 'config/experiment5-v5.json').read_text())
    value['status'] = 'execution_contract_frozen'
    value['gates'] = {key: 'verified' for key in value['gates']}
    value['candidates']['xgboost']['n_estimators'] = 2
    return value


def group(role, offset):
    rng = np.random.default_rng(24+offset)
    target = np.tile([0, 0, 0, 1], 20)
    values = rng.normal(size=(len(target), len(FEATURE_COLUMNS)))
    values[:, 0] += target*3
    start = pd.Timestamp('2020-01-01T00:00Z')+pd.Timedelta(days=offset*100)
    frame = pd.DataFrame(values, columns=FEATURE_COLUMNS)
    frame['harp'] = np.arange(len(frame))+1+offset*100
    frame['role'] = role
    frame['observation_start'] = [start+pd.Timedelta(hours=i) for i in range(len(frame))]
    frame['forecast_time'] = frame.observation_start+pd.Timedelta(hours=12)
    frame['prediction_end'] = frame.forecast_time+pd.Timedelta(hours=24)
    frame['missing_fraction'] = 0.0
    frame['target'] = target
    frame['label_status'] = np.where(target, 'positive', 'negative')
    return frame


def test_fixed_development_runner_preserves_test_boundary(tmp_path):
    groups = {name: group(name, offset) for offset, name in
              enumerate(['train', 'calibration', 'validation'])}
    report = fit_development(groups, protocol(), tmp_path / 'experiment')
    assert report['reserved_test_accessed'] is False
    assert report['selection']['model'] in {'logistic', 'xgboost'}
    assert all(row['recall'] >= .95 for row in report['metrics'])
    assert {row['model'] for row in report['metrics']} == {
        'baseline', 'logistic', 'xgboost'}
    assert (tmp_path / 'experiment' / 'selection.json').exists()


def test_frozen_ensemble_is_reported_as_a_candidate(tmp_path):
    groups = {name: group(name, offset) for offset, name in
              enumerate(['train', 'calibration', 'validation'])}
    spec = protocol()
    spec['ensemble'] = {'logistic_weight': 0.45, 'xgboost_weight': 0.55,
                        'weight_selection': 'frozen'}
    report = fit_development(groups, spec, tmp_path / 'ensemble')
    assert {row['model'] for row in report['metrics']} == {
        'baseline', 'logistic', 'xgboost', 'ensemble'}
    assert (tmp_path / 'ensemble' / 'ensemble.joblib').exists()
