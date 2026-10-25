import numpy as np
import pandas as pd

from helio24.data import FEATURE_COLUMNS
from helio24.v2_contract import V2_MEASUREMENTS
from helio24.v2_features import extract_harp_windows


def observations(rows=65, start='2022-06-01 00:00:37'):
    frame = pd.DataFrame({
        'harp_number': 7,
        'obs_start': pd.date_range(start, periods=rows, freq='12min'),
    })
    for index, column in enumerate(V2_MEASUREMENTS.values()):
        frame[column] = np.arange(rows, dtype=float)+index
    return frame


def roles():
    return {
        'train': (pd.Timestamp('2022-01-01T00:00Z'), pd.Timestamp('2023-01-01T00:00Z')),
        'calibration': (pd.Timestamp('2023-01-01T00:00Z'), pd.Timestamp('2024-01-01T00:00Z')),
        'validation': (pd.Timestamp('2024-01-01T00:00Z'), pd.Timestamp('2025-01-01T00:00Z')),
    }


def test_extracts_vectorized_summaries_at_the_frozen_stride():
    frame, audit = extract_harp_windows(observations(), roles())
    assert len(frame) == 2
    assert frame.role.tolist() == ['train', 'train']
    assert frame.forecast_time.tolist() == [
        pd.Timestamp('2022-06-01T12:00Z'), pd.Timestamp('2022-06-01T13:00Z')]
    first = next(iter(V2_MEASUREMENTS)).upper()
    assert frame.loc[0, f'{first}__mean'] == 29.5
    assert frame.loc[0, f'{first}__last'] == 59
    assert frame.loc[0, f'{first}__delta'] == 59
    assert frame.loc[0, f'{first}__std'] == np.std(np.arange(60))
    assert list(frame.columns[-len(FEATURE_COLUMNS):]) == FEATURE_COLUMNS
    assert audit['train_quality_retained'] == 2


def test_rejects_bad_quality_and_cadence_without_filling_values():
    frame = observations(rows=60)
    first = next(iter(V2_MEASUREMENTS.values()))
    frame.loc[:12, first] = np.nan
    result, audit = extract_harp_windows(frame, roles())
    assert result.empty
    assert audit['train_quality_rejected'] == 1
    frame = observations(rows=60)
    frame.loc[30, 'obs_start'] += pd.Timedelta(minutes=1)
    result, audit = extract_harp_windows(frame, roles())
    assert result.empty
    assert audit['cadence_rejected'] == 1


def test_earliest_role_owns_a_harp_across_boundaries():
    frame = observations(rows=245, start='2022-12-30 12:00:37')
    result, audit = extract_harp_windows(frame, roles())
    assert set(result.role) == {'train'}
    assert audit['shared_role_quality_rows_removed'] > 0
