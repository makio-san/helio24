"""Causal features that place a window inside the stored life of its HARP (config/life-phase-v1.json).

Every value of a window is computed from measurements of the same HARP at strictly earlier forecast times.
Labels and label status are refused. Nothing here counts windows: the table stores only labelled windows,
so a count or an exact-lag missing flag would carry the label-status exclusions of the neighbours.
"""
import numpy as np
import pandas as pd

KEY = ['harp', 'forecast_time']
MEASUREMENTS = ['USFLUX', 'TOTUSJH', 'TOTPOT', 'SAVNCPP', 'R_VALUE', 'MEANSHR']
LAGS_HOURS = [24, 48, 72]
AGE = 'life__log1p_hours_since_first_window'
PHASE_STATISTICS = ['ratio_to_running_max', 'running_z', 'hours_since_running_max', *[f'change_{lag}h' for lag in LAGS_HOURS]]
PHASE_COLUMNS = [f'life__{name}__{statistic}' for name in MEASUREMENTS for statistic in PHASE_STATISTICS]
SOURCE_COLUMNS = [f'{name}__mean' for name in MEASUREMENTS]
GAP = 'recent_gap_72h'
GAP_SPACING_HOURS, GAP_SPAN_HOURS = 1.5, 72
RATIO_CLIP, Z_CLIP = 100.0, 100.0
FORBIDDEN = {'target', 'label_status', 'label_status_v2', 'role'}
HOUR = pd.Timedelta(hours=1).value


def _harp_features(time, values):
    """Age and phase features of one HARP; `time` ascending in nanoseconds, `values` one column per measurement."""
    rows = len(time)
    out = np.full((rows, 1+len(PHASE_COLUMNS)), np.nan)
    out[:, 0] = np.log1p((time-time[0])/HOUR)
    positions = np.arange(rows)
    references = [np.searchsorted(time, time-lag*HOUR, side='right')-1 for lag in LAGS_HOURS]
    for j in range(values.shape[1]):
        value = values[:, j]
        finite = np.isfinite(value)
        column = 1+j*len(PHASE_STATISTICS)
        if not finite.any():
            continue
        # Running maximum over earlier windows and the first window that attained it.
        reached = np.maximum.accumulate(np.where(finite, value, -np.inf))
        earlier_max = np.r_[-np.inf, reached[:-1]]
        attained = np.maximum.accumulate(np.where(np.where(finite, value, -np.inf) > earlier_max, positions, -1))
        earlier_at = np.r_[-1, attained[:-1]]
        seen = earlier_at >= 0
        usable = seen & finite & (earlier_max > 0)
        with np.errstate(over='ignore'):
            out[usable, column] = np.clip(value[usable]/earlier_max[usable], -RATIO_CLIP, RATIO_CLIP)
        out[seen, column+2] = (time[seen]-time[earlier_at[seen]])/HOUR
        # Running mean and population standard deviation over earlier windows, centred on the first finite value.
        centred = np.where(finite, value-value[finite][0], 0.0)
        count = np.r_[0, np.cumsum(finite)[:-1]]
        with np.errstate(divide='ignore', invalid='ignore'):
            mean = np.r_[0.0, np.cumsum(centred)[:-1]]/count
            spread = np.sqrt(np.maximum(np.r_[0.0, np.cumsum(centred**2)[:-1]]/count-mean**2, 0.0))
            scored = finite & (count >= 2) & (spread > 0)
            out[scored, column+1] = np.clip((centred[scored]-mean[scored])/spread[scored], -Z_CLIP, Z_CLIP)
        # Change against the latest earlier window at or before the lag; missing only when the record is younger.
        for k, reference in enumerate(references):
            known = reference >= 0
            out[known, column+3+k] = value[known]-value[reference[known]]
    spacing = np.r_[False, np.diff(time) > GAP_SPACING_HOURS*HOUR]
    wide = np.cumsum(spacing)
    first = np.searchsorted(time, time-GAP_SPAN_HOURS*HOUR, side='right')
    gap = wide-np.where(first > 0, wide[np.maximum(first-1, 0)], 0) > 0
    return out, gap


def life_phase_features(windows):
    """AGE, PHASE_COLUMNS and the reporting flag GAP for every window, aligned to the index of `windows`.

    `windows` holds the forecast key and the six `__mean` summaries only. GAP marks a spacing above 1.5 hours
    between consecutive stored windows of the HARP in the last 72 hours; it is never a model input.
    """
    refused = FORBIDDEN & set(windows.columns)
    if refused:
        raise ValueError(f'Life features never see labels, label status or roles: {sorted(refused)}')
    missing = {*KEY, *SOURCE_COLUMNS}-set(windows.columns)
    if missing:
        raise ValueError(f'Missing columns: {sorted(missing)}')
    if windows.duplicated(KEY).any():
        raise ValueError('Duplicate forecast key')
    time = pd.to_datetime(windows.forecast_time, utc=True).astype('datetime64[ns, UTC]').astype('int64').to_numpy()
    harp = windows.harp.to_numpy()
    values = windows[SOURCE_COLUMNS].to_numpy(dtype=float)
    order = np.lexsort((time, harp))
    features = np.full((len(windows), 1+len(PHASE_COLUMNS)), np.nan)
    gap = np.zeros(len(windows), dtype=bool)
    harp_sorted = harp[order]
    starts = np.flatnonzero(np.r_[True, harp_sorted[1:] != harp_sorted[:-1]]) if len(order) else np.array([], dtype=int)
    for start, stop in zip(starts, np.r_[starts[1:], len(order)]):
        rows = order[start:stop]
        features[rows], gap[rows] = _harp_features(time[rows], values[rows])
    if np.isinf(features).any():
        raise ValueError('Infinite life feature')
    frame = pd.DataFrame(features, index=windows.index, columns=[AGE, *PHASE_COLUMNS])
    frame[GAP] = gap
    return frame
