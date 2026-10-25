"""Vectorized development-window extraction for SWAN-SF-V2."""
from collections import Counter

import numpy as np
import pandas as pd

from helio24.data import FEATURE_COLUMNS
from helio24.v2_contract import V2_MEASUREMENTS, tai_to_utc, tai_utc_offset


def extract_harp_windows(observations, roles, *, stride=5):
    """Return quality-retained windows owned by one chronological role."""
    values = observations.sort_values('obs_start').reset_index(drop=True)
    if values.empty or values.harp_number.nunique() != 1:
        raise ValueError('Feature extraction requires one non-empty HARP')
    clocks = pd.to_datetime(values.obs_start, errors='raise')
    if clocks.dt.tz is not None or clocks.duplicated().any():
        raise ValueError('Observation clocks must be unique timezone-naive TAI values')
    if stride <= 0:
        raise ValueError('Stride must be positive')

    numeric = values[list(V2_MEASUREMENTS.values())].apply(pd.to_numeric, errors='coerce')
    array = numeric.to_numpy(dtype=float, na_value=np.nan, copy=True)
    array[~np.isfinite(array)] = np.nan
    finite = np.isfinite(array)
    filled = np.where(finite, array, 0.0)
    cumulative_count = np.vstack([np.zeros((1, array.shape[1]), dtype=np.int64),
                                  finite.cumsum(axis=0)])
    cumulative_sum = np.vstack([np.zeros((1, array.shape[1])), filled.cumsum(axis=0)])
    cumulative_square = np.vstack([np.zeros((1, array.shape[1])),
                                   np.square(filled).cumsum(axis=0)])
    bad_cadence = clocks.diff().iloc[1:].ne(pd.Timedelta(minutes=12)).astype(int)
    bad_prefix = np.r_[0, bad_cadence.cumsum().to_numpy()]
    audit = Counter()
    records = []
    for start in range(0, max(0, len(values)-59), stride):
        end = start+59
        if bad_prefix[end]-bad_prefix[start]:
            audit['cadence_rejected'] += 1
            continue
        start_tai = clocks.iloc[start]
        forecast_tai = start_tai+pd.Timedelta(hours=12)
        if tai_utc_offset(start_tai) != tai_utc_offset(forecast_tai):
            audit['leap_rejected'] += 1
            continue
        observation_start = tai_to_utc(start_tai)
        forecast_time = tai_to_utc(forecast_tai)
        prediction_end = forecast_time+pd.Timedelta(hours=24)
        role = next((name for name, (left, right) in roles.items()
                     if left <= forecast_time < right), None)
        if (role is None or observation_start < roles[role][0]
                or prediction_end > roles[role][1]):
            audit['boundary_rejected'] += 1
            continue
        audit[f'{role}_candidate'] += 1
        counts = cumulative_count[end+1]-cumulative_count[start]
        if (counts < 48).any():
            audit[f'{role}_quality_rejected'] += 1
            continue
        sums = cumulative_sum[end+1]-cumulative_sum[start]
        squares = cumulative_square[end+1]-cumulative_square[start]
        means = sums/counts
        variance = np.maximum(squares/counts-np.square(means), 0.0)
        summaries = np.column_stack([means, np.sqrt(variance), array[end],
                                     array[end]-array[start]])
        records.append({
            'harp': int(values.harp_number.iloc[0]),
            'role': role,
            'observation_start': observation_start,
            'forecast_time': forecast_time,
            'prediction_end': prediction_end,
            'missing_fraction': float(1-counts.sum()/(60*array.shape[1])),
        } | dict(zip(FEATURE_COLUMNS, summaries.ravel())))
        audit[f'{role}_quality_retained'] += 1

    columns = ['harp', 'role', 'observation_start', 'forecast_time',
               'prediction_end', 'missing_fraction', *FEATURE_COLUMNS]
    frame = pd.DataFrame(records, columns=columns)
    active_roles = [name for name in roles if audit[f'{name}_candidate']]
    if not active_roles:
        return frame, dict(audit)
    owner = active_roles[0]
    removed = len(frame)-int(frame.role.eq(owner).sum())
    audit['shared_role_quality_rows_removed'] = removed
    return frame[frame.role.eq(owner)].reset_index(drop=True), dict(audit)
