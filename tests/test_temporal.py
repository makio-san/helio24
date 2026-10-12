import numpy as np
import pandas as pd

from helio24.data import MAGNETIC_COLUMNS
from helio24.temporal import TEMPORAL_FEATURE_COLUMNS, extract_temporal_features


def observation():
    values = np.arange(60, dtype=float)
    return pd.DataFrame({
        **{column: values.copy() for column in MAGNETIC_COLUMNS},
        'Timestamp': pd.date_range('2011-01-01', periods=60, freq='12min'),
        'QUALITY': 0,
        'IS_TMFI': True,
    })


def test_temporal_features_use_fixed_recent_intervals():
    frame = observation()
    features = extract_temporal_features(frame)
    assert list(features) == TEMPORAL_FEATURE_COLUMNS
    assert len(features) == 216
    for hours, expected_change in [(1, 4), (3, 14), (6, 29)]:
        prefix = f'TOTUSJH__recent_{hours}h_'
        assert np.isclose(features[prefix+'slope'], 5.0)
        assert features[prefix+'change'] == expected_change
        assert features[prefix+'diff_std'] == 0


def test_temporal_features_mask_untrusted_values_and_ignore_old_history():
    frame = observation()
    frame.loc[:29, 'TOTUSJH'] = 10000
    baseline = extract_temporal_features(frame)
    frame.loc[57, 'QUALITY'] = 1
    masked = extract_temporal_features(frame)
    assert baseline['TOTUSJH__recent_1h_change'] == 4
    assert baseline['TOTUSJH__recent_6h_change'] == 29
    assert masked['TOTUSJH__recent_1h_change'] == 4
    assert np.isclose(masked['TOTUSJH__recent_1h_slope'], 5.0)
    assert masked['TOTUSJH__recent_1h_diff_std'] == 0
