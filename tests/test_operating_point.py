import json
from pathlib import Path

import numpy as np

from scripts.audit_operating_point import recall_for_precision

ROOT = Path(__file__).resolve().parents[1]


def test_recall_for_precision_reads_the_oracle_curve():
    y = np.array([1, 1, 0, 1, 0, 0, 0, 1])  # sorted by descending probability below
    p = np.array([.9, .8, .7, .6, .5, .4, .3, .2])
    # cumulative precision: 1, 1, .667, .75, .6, .5, .43, .5 ; recall: .25,.5,.5,.75,.75,.75,.75,1
    assert recall_for_precision(y, p, 0.75) == 0.75
    assert recall_for_precision(y, p, 1.0) == 0.5
    assert recall_for_precision(y, p, 0.5) == 1.0
    assert recall_for_precision(y, p, 1.1) == 0.0


def test_protocol_is_descriptive_and_separates_oracle():
    config = json.loads((ROOT / 'config/operating-point-review-v1.json').read_text())
    assert config['deployable_curve']['recall_targets'][0] == 0.95
    assert 'Not deployable' in config['oracle_curve']['rule']
    assert any('oracle' in item for item in config['prohibitions'])
    assert any('2024-2025' in item for item in config['prohibitions'])
    assert 'No acceptance rule' in config['purpose']
