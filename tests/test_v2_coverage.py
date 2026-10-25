import numpy as np
import pandas as pd

from helio24.v2_contract import V2_MEASUREMENTS
from helio24.v2_coverage import audit_harp


def observations(rows=60):
    frame = pd.DataFrame({
        'harp_number': 7,
        'obs_start': pd.date_range('2022-06-01', periods=rows, freq='12min'),
    })
    for column in V2_MEASUREMENTS.values():
        frame[column] = 1.0
    return frame


def roles():
    empty = (pd.Timestamp('2021-01-01T00:00Z'), pd.Timestamp('2022-01-01T00:00Z'))
    return {
        'train': (pd.Timestamp('2022-01-01T00:00Z'), pd.Timestamp('2023-01-01T00:00Z')),
        'calibration': empty,
        'validation': empty,
    }


def test_harp_coverage_counts_known_positive_window():
    events = pd.DataFrame([{
        'goes_class': 'M1.2', 'has_goes': True, 'confidence': 'high',
        'peak_time_utc': pd.Timestamp('2022-06-01T13:00Z'),
    }])
    result = audit_harp(observations(), events, roles())
    assert result['roles']['train'] == {
        'candidate_windows': 1,
        'quality_retained': 1,
        'missing_positions_retained': 0,
        'known_positive_windows': 1,
    }


def test_harp_coverage_rejects_parameter_over_twenty_percent_missing():
    frame = observations()
    frame.loc[:12, next(iter(V2_MEASUREMENTS.values()))] = np.nan
    result = audit_harp(frame, pd.DataFrame(), roles())
    assert result['roles']['train']['candidate_windows'] == 1
    assert result['roles']['train']['quality_rejected'] == 1
    assert result['roles']['train'].get('quality_retained', 0) == 0
