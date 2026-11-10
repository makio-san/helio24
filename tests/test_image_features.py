import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pandas as pd
import pytest

from scripts.audit_image_features import CANDIDATES, CONTEXT, attach_maps, map_labels

ROOT = Path(__file__).resolve().parents[1]


def _maps():
    return pd.DataFrame({'harp': [1, 1, 2], 't_rec': pd.to_datetime(['2014-03-01', '2014-03-02', '2014-03-02'], utc=True)})


def test_attach_uses_only_maps_at_or_before_each_rule_cutoff():
    frame = pd.DataFrame({'harp': [1, 1, 1, 2, 3], 'forecast_time': pd.to_datetime(
        ['2014-03-01 12:00', '2014-03-02 06:00', '2014-03-04 00:00', '2014-03-01 23:00', '2014-03-02 06:00'], utc=True)})
    out = attach_maps(frame, _maps(), np.array([1.0, 2.0, 3.0]))
    assert list(out.columns) == CONTEXT
    # same rule: latest map not after t and at most 24 h old
    assert out.map_available_same.tolist() == [1.0, 1.0, 0.0, 0.0, 0.0]
    assert out.cnn_logit_same[:2].tolist() == [1.0, 2.0] and out.map_age_hours_same[:2].tolist() == [12.0, 6.0]
    # lag24 rule: the map must be at least 24 h old and at most 48 h old
    assert out.map_available_lag24.tolist() == [0.0, 1.0, 1.0, 0.0, 0.0]
    assert out.cnn_logit_lag24[1:3].tolist() == [1.0, 2.0] and out.map_age_hours_lag24[1:3].tolist() == [30.0, 48.0]
    assert np.isnan(out.cnn_logit_lag24[0]) and np.isnan(out.map_age_hours_same[3])


def test_map_labels_cover_the_following_48_hours_of_training_windows_only():
    windows = pd.DataFrame({'harp': [1, 1, 2], 'target': [0, 1, 0], 'forecast_time': pd.to_datetime(
        ['2014-03-01 05:00', '2014-03-03 10:00', '2014-03-05 00:00'], utc=True)})
    labels = map_labels(_maps(), windows)
    assert labels[0] == 0 and labels[1] == 1 and np.isnan(labels[2])


def test_cnn_trains_and_scores_in_a_fresh_process():
    if importlib.util.find_spec('torch') is None:
        pytest.skip('Optional neural dependency not installed')
    code = """
import numpy as np
from helio24.map_model import score_cnn, train_cnn
rng = np.random.default_rng(0)
images = (rng.normal(size=(16, 128, 256))*100).astype(np.float16)
extra = np.zeros((16, 3), dtype=np.float32)
settings = {'epochs': 1, 'batch': 8, 'learning_rate': 0.001, 'weight_decay': 0.0001, 'dropout': 0.3}
model, loss = train_cnn(images, extra, np.array([0, 1]*8, dtype=float), settings, 24, 'cpu')
scores = score_cnn(model, images, extra, np.arange(16), 'cpu')
assert np.isfinite(loss) and scores.shape == (16,) and np.isfinite(scores).all()
"""
    result = subprocess.run([sys.executable, '-c', code], capture_output=True, text=True, timeout=120, cwd=ROOT)
    assert result.returncode == 0, result.stderr


def test_protocol_is_frozen_with_the_lagged_rule_as_primary():
    config = json.loads((ROOT/'config/image-features-v1.json').read_text())
    assert config['recall_target'] == 0.9 and config['reserved_test_accessed'] is False
    assert config['budget'] == {'cnn_fits': 18, 'candidate_recipes': 4, 'years': 6, 'constituent_fits': 48,
                                'hyperparameter_search': 0, 'architectures_after_results': 0}
    assert [c['id'] for c in config['candidates']][1:] == list(CANDIDATES)
    assert 'image_lag24' in config['acceptance']['all_year_primary'] and 2018 not in config['years']
    assert config['availability_rules']['same'].startswith('Sensitivity only')
