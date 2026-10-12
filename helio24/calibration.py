"""Chronological calibration, fixed-recall thresholds, and cluster uncertainty."""
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.special import expit, logit

from helio24.modeling import threshold_curve


@dataclass
class SigmoidCalibration:
    slope: float = 1.0
    intercept: float = 0.0

    def fit(self, probability, target):
        x = logit(np.clip(np.asarray(probability, dtype=float), 1e-9, 1-1e-9))
        y = np.asarray(target, dtype=float)
        if set(np.unique(y)) != {0, 1} or len(x) != len(y) or not np.isfinite(x).all():
            raise ValueError('Calibration requires finite predictions and both target classes')

        def objective(parameters):
            z = parameters[0]*x + parameters[1]
            residual = expit(z)-y
            return np.mean(np.logaddexp(0, z)-y*z), np.array([np.mean(residual*x), np.mean(residual)])

        result = minimize(objective, [1.0, 0.0], jac=True, method='L-BFGS-B',
                          bounds=[(1e-6, None), (None, None)],
                          options={'maxiter': 1000, 'ftol': 1e-12, 'gtol': 1e-9})
        if not result.success:
            raise ValueError(f'Calibration failed: {result.message}')
        self.slope, self.intercept = map(float, result.x)
        return self

    def transform(self, probability):
        scores = logit(np.clip(np.asarray(probability, dtype=float), 1e-9, 1-1e-9))
        return np.clip(expit(self.slope*scores+self.intercept), 1e-12, 1-1e-12)


def recall_threshold(target, probability, required_recall):
    if not 0 < required_recall <= 1:
        raise ValueError('Recall target must be in (0, 1]')
    if set(np.unique(target)) != {0, 1}:
        raise ValueError('Threshold selection needs both classes')
    candidates = threshold_curve(target, probability)
    candidates = candidates[candidates.recall >= required_recall]
    chosen = candidates.sort_values(['false_alarms', 'threshold'], ascending=[True, False]).iloc[0]
    return float(chosen.threshold)


def split_roles(table):
    assignments = {'train': [1, 2], 'calibration': [3], 'validation': [4], 'audit': [5]}
    groups = {name: table[table.partition.isin(parts)].sort_values(['forecast_time', 'harp']).copy()
              for name, parts in assignments.items()}
    if any(frame.empty for frame in groups.values()):
        raise ValueError('Every chronological role needs data')
    audit = []
    names = list(groups)
    for left, right in zip(names, names[1:]):
        boundary = groups[right].observation_start.min()
        before = len(groups[left])
        groups[left] = groups[left][groups[left].prediction_end <= boundary].copy()
        audit.append(dict(role=left, boundary=str(boundary), boundary_removed=before-len(groups[left])))
    seen = set()
    for name, frame in groups.items():
        before = len(frame)
        shared = set(frame.harp) & seen
        frame = frame[~frame.harp.isin(shared)].copy()
        shared_removed = before-len(frame)
        # Different labels for one observation cannot be resolved by silently choosing one.
        if (frame.groupby(['harp', 'forecast_time']).target.nunique() > 1).any():
            raise ValueError('Conflicting labels for an observation')
        unique = frame.drop_duplicates(['harp', 'forecast_time']).copy()
        audit.append(dict(role=name, shared_harps=sorted(map(int, shared)),
                          shared_harp_rows_removed=shared_removed, duplicates_removed=len(frame)-len(unique)))
        if unique.target.nunique() != 2:
            raise ValueError(f'{name} does not contain both classes after purging')
        groups[name] = unique
        seen.update(unique.harp)
    for left, right in zip(names, names[1:]):
        if groups[left].prediction_end.max() > groups[right].observation_start.min():
            raise ValueError('Temporal overlap remains between roles')
    return groups, audit


def _interval(values):
    valid = np.asarray(values)[np.isfinite(values)]
    return dict(lower=float(np.quantile(valid, .025)) if len(valid) else None,
                upper=float(np.quantile(valid, .975)) if len(valid) else None,
                valid_draws=len(valid), undefined_draws=len(values)-len(valid))


def cluster_intervals(target, probability, harp, threshold, draws=1000, seed=24):
    """Resample entire HARP clusters; no independence assumption for their windows."""
    y = np.asarray(target, dtype=int)
    p = np.asarray(probability, dtype=float)
    a = p >= threshold
    frame = pd.DataFrame(dict(harp=np.asarray(harp), n=np.ones(len(y)),
                              tp=a*y, fp=a*(1-y), fn=(~a)*y, tn=(~a)*(1-y),
                              squared_error=(p-y)**2))
    totals = frame.groupby('harp', sort=True).sum().to_numpy(dtype=float)
    if len(totals) < 2 or draws < 2:
        raise ValueError('Bootstrap needs at least two regions and draws')
    rng = np.random.default_rng(seed)
    # Each row represents one entire region's contribution; duplicated draws retain multiplicity.
    samples = np.array([totals[rng.integers(0, len(totals), len(totals))].sum(axis=0) for _ in range(draws)])
    n, tp, fp, fn, tn, squared = samples.T

    def divide(numerator, denominator):
        return np.divide(numerator, denominator, out=np.full(draws, np.nan), where=denominator > 0)

    return {name: _interval(values) for name, values in {
        'recall': divide(tp, tp+fn), 'precision': divide(tp, tp+fp),
        'false_positive_rate': divide(fp, fp+tn), 'false_alarm_ratio': divide(fp, tp+fp),
        'brier': divide(squared, n),
    }.items()}


def paired_brier_interval(target, raw, calibrated, harp, draws=1000, seed=24):
    y = np.asarray(target)
    delta = (np.asarray(calibrated)-y)**2 - (np.asarray(raw)-y)**2
    totals = pd.DataFrame(dict(harp=np.asarray(harp), delta=delta, n=np.ones(len(y)))).groupby('harp', sort=True).sum().to_numpy()
    if len(totals) < 2 or draws < 2:
        raise ValueError('Bootstrap needs at least two regions and draws')
    rng = np.random.default_rng(seed)
    samples = np.array([totals[rng.integers(0, len(totals), len(totals))].sum(axis=0) for _ in range(draws)])
    return dict(estimate=float(delta.mean()), **_interval(samples[:, 0]/samples[:, 1]))
