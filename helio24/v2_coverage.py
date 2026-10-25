"""Development-only V2 measurement coverage calculations."""
from collections import Counter

import numpy as np
import pandas as pd

from helio24.v2_contract import (
    ACCEPTED_CONFIDENCE, AMBIGUOUS_CONFIDENCE, V2_MEASUREMENTS,
    parse_flare_class, tai_to_utc, tai_utc_offset,
)


ROLE_ORDER = ('train', 'calibration', 'validation')


def audit_harp(observations, events, roles):
    """Count eligible windows without retaining feature vectors."""
    values = observations.sort_values('obs_start').reset_index(drop=True)
    if values.empty or values.harp_number.nunique() != 1:
        raise ValueError('Coverage audit requires one non-empty HARP')
    clocks = pd.to_datetime(values.obs_start, errors='raise')
    if clocks.dt.tz is not None or clocks.duplicated().any():
        raise ValueError('Observation clocks must be unique timezone-naive TAI values')

    numeric = values[list(V2_MEASUREMENTS.values())].apply(pd.to_numeric, errors='coerce')
    array = numeric.to_numpy(dtype=float, na_value=np.nan, copy=True)
    array[~np.isfinite(array)] = np.nan
    missing = np.isnan(array).astype(np.int64)
    cumulative = np.vstack([np.zeros((1, missing.shape[1]), dtype=np.int64),
                            missing.cumsum(axis=0)])
    events = events.copy()
    if events.empty:
        accepted_peaks = ambiguous_peaks = np.array([], dtype=np.int64)
    else:
        letters = np.array([parse_flare_class(value)[0] for value in events.goes_class])
        strong_goes = np.isin(letters, ['M', 'X']) & events.has_goes.to_numpy(dtype=bool)
        peak_ns = np.array([pd.Timestamp(value).value for value in events.peak_time_utc],
                           dtype=np.int64)
        confidence = events.confidence.to_numpy()
        accepted_peaks = np.sort(peak_ns[strong_goes & np.isin(confidence, list(ACCEPTED_CONFIDENCE))])
        ambiguous_peaks = np.sort(peak_ns[strong_goes & np.isin(confidence, list(AMBIGUOUS_CONFIDENCE))])

    stats = {role: Counter() for role in ROLE_ORDER}
    coverage = {role: [None, None] for role in ROLE_ORDER}
    boundary_removed = leap_removed = cadence_removed = 0
    diffs = clocks.diff().iloc[1:]
    bad_prefix = diffs.ne(pd.Timedelta(minutes=12)).astype(int).cumsum()
    for start_index in range(0, max(0, len(clocks)-59), 5):
        end_index = start_index+59
        bad_before = int(bad_prefix.iloc[start_index-1]) if start_index else 0
        if int(bad_prefix.iloc[end_index-1])-bad_before:
            cadence_removed += 1
            continue
        start_tai = clocks.iloc[start_index]
        forecast_tai = start_tai+pd.Timedelta(hours=12)
        if tai_utc_offset(start_tai) != tai_utc_offset(forecast_tai):
            leap_removed += 1
            continue
        observation_start = tai_to_utc(start_tai)
        forecast = tai_to_utc(forecast_tai)
        prediction_end = forecast+pd.Timedelta(hours=24)
        role = next((name for name, (left, right) in roles.items()
                     if left <= forecast < right), None)
        if role is None or observation_start < roles[role][0] or prediction_end > roles[role][1]:
            boundary_removed += 1
            continue
        role_stats = stats[role]
        role_stats['candidate_windows'] += 1
        missing_counts = cumulative[end_index+1]-cumulative[start_index]
        if (missing_counts > 12).any():
            role_stats['quality_rejected'] += 1
            continue
        role_stats['quality_retained'] += 1
        role_stats['missing_positions_retained'] += int(missing_counts.sum())
        forecast_ns, prediction_end_ns = forecast.value, prediction_end.value
        accepted_left = np.searchsorted(accepted_peaks, forecast_ns, side='left')
        accepted_right = np.searchsorted(accepted_peaks, prediction_end_ns, side='left')
        ambiguous_left = np.searchsorted(ambiguous_peaks, forecast_ns, side='left')
        ambiguous_right = np.searchsorted(ambiguous_peaks, prediction_end_ns, side='left')
        if accepted_right > accepted_left:
            role_stats['known_positive_windows'] += 1
        elif ambiguous_right > ambiguous_left:
            role_stats['ambiguous_harp_windows'] += 1
        else:
            role_stats['unresolved_nonpositive_windows'] += 1
        first, last = coverage[role]
        coverage[role] = [forecast if first is None or forecast < first else first,
                          forecast if last is None or forecast > last else last]
    return {
        'harp': int(values.harp_number.iloc[0]),
        'rows': len(values),
        'roles': {role: dict(stats[role]) for role in ROLE_ORDER},
        'forecast_coverage': {
            role: [value.isoformat() if value is not None else None for value in bounds]
            for role, bounds in coverage.items()
        },
        'boundary_removed': boundary_removed,
        'leap_removed': leap_removed,
        'cadence_removed': cadence_removed,
    }
