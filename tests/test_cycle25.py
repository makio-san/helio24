import json
from pathlib import Path

import numpy as np
import pandas as pd

from scripts.audit_cycle25 import decomposition

ROOT = Path(__file__).resolve().parents[1]


def test_decomposition_separates_which_region_from_when():
    frame = pd.DataFrame({'harp': [1, 1, 1, 2, 2, 3, 3], 'target': [0, 1, 0, 0, 0, 1, 0],
                          'probability': [.2, .9, .3, .8, .7, .6, .1]})
    out = decomposition(frame, 0.5)
    # region: harp1 max .9 (pos), harp2 .8 (neg), harp3 .6 (pos) -> ranking .9+, .8-, .6+ : AP = (1 + 2/3)/2
    assert np.isclose(out['region_ap'], (1+2/3)/2)
    # within flaring HARPs 1 and 3: .9+, .6+, .3-, .2-, .1- -> AP 1
    assert out['within_flaring_ap'] == 1.0
    # FP at 0.5: .8 and .7 of harp 2 (never flaring), .6 is a hit -> 2 FP, all from never-flaring HARPs
    assert out['fp_windows'] == 2 and out['fp_share_never_flaring_harps'] == 1.0


def test_protocol_is_frozen_as_a_description_with_readings():
    config = json.loads((ROOT/'config/cycle25-diagnostic-v1.json').read_text())
    assert config['status'] == 'frozen_before_any_result' and config['reserved_test_accessed'] is False
    assert config['budget'] == {'fits': 20, 'hyperparameter_search': 0, 'feature_changes': 0}
    assert config['eras'] == {'cycle24': [2014, 2015, 2016, 2017], 'cycle25': [2022, 2023]}
    assert 'never a deployable model' in config['measures']['D4_within_era_fit']
    assert set(config['reading']) == {'R1_information_fell', 'R2_drift', 'R3_timing_dominates', 'mixed'}
