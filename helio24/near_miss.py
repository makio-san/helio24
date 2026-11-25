"""Training-only weights for near-miss negatives of flaring HARPs (config/near-miss-weighting-v1.json)."""
import numpy as np
import pandas as pd


def near_miss_mask(train, span_hours):
    """Negative windows with a positive window of the same HARP within `span_hours` before or after.

    Only the rows of `train` are looked at, so membership never depends on a label outside the frame.
    """
    if span_hours <= 0:
        raise ValueError('Positive span required')
    if 'role' in train.columns and not train.role.eq('train').all():
        raise ValueError('Near-miss membership is computed inside the training role only')
    if not train.target.isin([0, 1]).all():
        raise ValueError('Binary training labels required')
    if train.duplicated(['harp', 'forecast_time']).any():
        raise ValueError('Duplicate forecast key')
    span = pd.Timedelta(hours=span_hours).value
    time = pd.to_datetime(train.forecast_time, utc=True).astype('datetime64[ns, UTC]').astype('int64').to_numpy()
    harp = train.harp.to_numpy()
    positive = train.target.eq(1).to_numpy()
    mask = np.zeros(len(train), dtype=bool)
    order = np.lexsort((time, harp))
    harp_sorted, time_sorted, positive_sorted = harp[order], time[order], positive[order]
    starts = np.flatnonzero(np.r_[True, harp_sorted[1:] != harp_sorted[:-1]])
    for start, stop in zip(starts, np.r_[starts[1:], len(order)]):
        flagged = positive_sorted[start:stop]
        if not flagged.any():
            continue
        times = time_sorted[start:stop]
        events = times[flagged]
        after = np.searchsorted(events, times)
        distance = np.minimum(np.abs(events[np.minimum(after, len(events)-1)]-times),
                              np.abs(times-events[np.maximum(after-1, 0)]))
        mask[order[start:stop]] = ~flagged & (distance <= span)
    return mask


def near_miss_weights(train, factor, span_hours):
    """(targeted, uniform, mask): near-miss negatives at `factor`, and the same total negative weight spread evenly.

    Positives keep weight 1 in both; the two weightings differ only in which negatives carry the extra weight.
    """
    if factor <= 1:
        raise ValueError('Weight factor above 1 required')
    mask = near_miss_mask(train, span_hours)
    negative = train.target.eq(0).to_numpy()
    if not mask.any():
        raise ValueError('No near-miss negative in training: the two weightings would be identical')
    targeted = np.where(mask, float(factor), 1.0)
    uniform = np.ones(len(train))
    uniform[negative] = 1+(factor-1)*mask.sum()/negative.sum()
    if not np.isclose(targeted[negative].sum(), uniform[negative].sum()) or not (targeted[~negative] == 1).all():
        raise ValueError('Negative weight totals differ')
    return targeted, uniform, mask
