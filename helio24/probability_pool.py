"""Generalized means for calibrated forecast probabilities."""
import numpy as np


def probability_pool(left, right, weight, power):
    if not 0 <= weight <= 1:
        raise ValueError('Weight must be in [0, 1]')
    left, right = np.asarray(left, dtype=float), np.asarray(right, dtype=float)
    if left.shape != right.shape or not np.isfinite(left).all() or not np.isfinite(right).all():
        raise ValueError('Matching finite probability arrays required')
    if (left < 0).any() or (left > 1).any() or (right < 0).any() or (right > 1).any():
        raise ValueError('Probabilities must be in [0, 1]')
    if power == 1:
        return weight*left+(1-weight)*right
    left, right = np.clip(left, 1e-12, 1), np.clip(right, 1e-12, 1)
    if power == 0:
        return np.exp(weight*np.log(left)+(1-weight)*np.log(right))
    return (weight*left**power+(1-weight)*right**power)**(1/power)
