"""Numerical diagnostics only; these hypotheses are not a model adapter."""
import numpy as np


def compare_values(reference, candidate, rtol=1e-5, atol=1e-8):
    left, right = np.asarray(reference, dtype=float), np.asarray(candidate, dtype=float)
    if left.shape != right.shape:
        raise ValueError('Aligned arrays must have the same shape')
    finite = np.isfinite(left) & np.isfinite(right)
    nonzero = finite & (left != 0)
    ratio = right[nonzero] / left[nonzero]
    relative = np.abs(right[nonzero] - left[nonzero]) / np.abs(left[nonzero])
    return dict(samples=int(left.size), finite_pairs=int(finite.sum()),
                both_missing=int((np.isnan(left) & np.isnan(right)).sum()),
                finite_mismatch=int((np.isfinite(left) ^ np.isfinite(right)).sum()),
                close_finite=int(np.isclose(left[finite], right[finite], rtol=rtol, atol=atol).sum()),
                ratio_median=float(np.median(ratio)) if ratio.size else None,
                relative_error_max=float(relative.max()) if relative.size else None)


def force_hypotheses(old):
    """Fixed analytical candidates, not coefficients fitted to observations."""
    return {'TOTFX': np.asarray(old['TOTFX']) / (4*np.pi),
            'TOTFY': -np.asarray(old['TOTFY']) / (4*np.pi),
            'TOTFZ': np.asarray(old['TOTFZ']) / (8*np.pi)}


def safe_ratio(numerator, denominator):
    top, bottom = np.broadcast_arrays(np.asarray(numerator, dtype=float), np.asarray(denominator, dtype=float))
    return np.divide(top, bottom, out=np.full(top.shape, np.nan),
                     where=np.isfinite(top) & np.isfinite(bottom) & (bottom != 0))
