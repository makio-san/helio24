import json
from pathlib import Path

import numpy as np
import pytest

from helio24.two_tier import precision_threshold

ROOT = Path(__file__).resolve().parents[1]
Y = np.array([1, 1, 0, 1, 0, 0, 0, 1])
P = np.array([.9, .8, .7, .6, .5, .4, .3, .2])
# cumulative precision: 1, 1, .667, .75, .6, .5, .43, .5 ; recall: .25, .5, .5, .75, .75, .75, .75, 1


def test_alert_threshold_takes_the_highest_recall_that_keeps_the_precision_target():
    threshold, recall, precision, fallback = precision_threshold(Y, P, 0.75, 0.1)
    assert (threshold, recall, precision, fallback) == (.6, .75, .75, False)
    threshold, recall, precision, fallback = precision_threshold(Y, P, 1.0, 0.1)
    assert (threshold, recall, precision, fallback) == (.8, .5, 1.0, False)


def test_alert_threshold_falls_back_to_the_best_precision_above_the_recall_floor():
    threshold, recall, precision, fallback = precision_threshold(Y, P, 1.0, 0.6)
    assert fallback and (threshold, recall, precision) == (.6, .75, .75)
    with pytest.raises(ValueError):
        precision_threshold(Y, P, 0.5, 1.0+1e-9)
    with pytest.raises(ValueError):
        precision_threshold(np.zeros(8, dtype=int), P, 0.5, 0.1)


def test_protocol_is_frozen_with_the_watch_tier_unchanged():
    config = json.loads((ROOT/'config/two-tier-v1.json').read_text())
    assert config['status'] == 'frozen_before_any_result' and config['reserved_test_accessed'] is False
    assert config['tiers']['watch']['recall_target'] == 0.9
    assert config['tiers']['alert'] ['primary_precision_target'] == 0.5 and config['tiers']['alert']['recall_floor'] == 0.1
    assert config['evidence']['watch_tier_thresholds_sha256'] == 'bd4594e2ab0e5ebcdc58cc438b59f7a213828fa3dfdd5b5dfb9c7fcb0df3d6c0'
    assert 'never changes alerts' in config['reading']['meaning']
    assert any('oracle' in item for item in config['prohibitions'])
