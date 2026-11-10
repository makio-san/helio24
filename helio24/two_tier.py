"""Precision-targeted threshold selection for the alert tier (config/two-tier-v1.json)."""
import numpy as np

from helio24.modeling import threshold_curve


def precision_threshold(target, probability, precision_target, recall_floor):
    """Highest-recall calibration threshold at or above the precision target; best precision as fallback.

    Returns (threshold, calibration_recall, calibration_precision, fallback).
    """
    if not 0 < precision_target <= 1 or not 0 < recall_floor <= 1:
        raise ValueError('Targets must be in (0, 1]')
    if set(np.unique(target)) != {0, 1}:
        raise ValueError('Threshold selection needs both classes')
    curve = threshold_curve(target, probability)
    curve = curve[curve.recall >= recall_floor-1e-12]
    if curve.empty:
        raise ValueError('No threshold reaches the recall floor')
    reaching = curve[curve.precision >= precision_target-1e-12]
    if len(reaching):
        chosen = reaching.sort_values(['recall', 'threshold'], ascending=[False, True]).iloc[0]
        fallback = False
    else:
        chosen = curve.sort_values(['precision', 'recall', 'threshold'], ascending=[False, False, True]).iloc[0]
        fallback = True
    return float(chosen.threshold), float(chosen.recall), float(chosen.precision), fallback
