"""Within-HARP ranking score and prior-year stacking step (config/within-harp-ranking-v1.json).

Everything here sees only the rows it is given: query groups come from training-role rows and labels,
and the stack is fitted on calibration-year rows and labels. No evaluation label enters any function.
"""
import json

import numpy as np
from scipy.special import logit
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

RANKER_DROPPED = ('scale_pos_weight', 'eval_metric')
RANKER_OBJECTIVE = {'objective': 'rank:pairwise', 'lambdarank_pair_method': 'topk'}


def control_logit(probability):
    """Logit of the calibrated control ensemble probability, clipped as helio24.calibration does."""
    return logit(np.clip(np.asarray(probability, dtype=float), 1e-9, 1-1e-9))


def ranking_rows(train):
    """Positions into `train` of the windows of flaring training HARPs, ordered by HARP and time, and their query ids.

    A HARP is flaring when it has at least one positive window in `train`; other HARPs would give no pair.
    """
    if 'role' in train.columns and not train.role.eq('train').all():
        raise ValueError('Query groups are built inside the training role only')
    if not train.target.isin([0, 1]).all():
        raise ValueError('Binary training labels required')
    if train.duplicated(['harp', 'forecast_time']).any():
        raise ValueError('Duplicate forecast key')
    flaring = set(train.harp[train.target.eq(1)])
    if not flaring:
        raise ValueError('No flaring training HARP: the ranker has no pair')
    harp = train.harp.to_numpy()
    time = train.forecast_time.to_numpy()
    keep = np.flatnonzero(np.isin(harp, list(flaring)))
    order = keep[np.lexsort((time[keep], harp[keep]))]
    return order, harp[order]


def ranker_model(base):
    """The walk-forward-v1 XGBoost settings with the pairwise ranking objective, behind the same median imputer."""
    from xgboost import XGBRanker

    params = {k: v for k, v in base['candidates']['xgboost'].items() if k not in RANKER_DROPPED}
    return make_pipeline(SimpleImputer(strategy='median', add_indicator=True), XGBRanker(**params, **RANKER_OBJECTIVE))


def ranker_objective(model):
    """The objective block XGBoost actually used, to compare with the frozen one."""
    config = json.loads(model.steps[-1][1].get_booster().save_config())['learner']['objective']
    return {'name': config['name'], **config['lambdarank_param']}


def margin(model, x):
    """Raw margin of a fitted imputer plus XGBoost pipeline; it has no calibrated scale and only enters through the stack."""
    return np.asarray(model.steps[-1][1].predict(model[:-1].transform(x), output_margin=True), dtype=float)


def stack_model(params):
    return make_pipeline(StandardScaler(), LogisticRegression(**params))


def fit_stack(params, z_calibration, y_calibration, z_evaluation):
    """Logistic stack fitted on the calibration year only; returns calibration and evaluation probabilities and its coefficients."""
    z_calibration, z_evaluation = np.asarray(z_calibration, dtype=float), np.asarray(z_evaluation, dtype=float)
    if z_calibration.ndim != 2 or z_evaluation.ndim != 2 or z_calibration.shape[1] != z_evaluation.shape[1]:
        raise ValueError('Stack inputs are one column per input')
    if not np.isfinite(z_calibration).all() or not np.isfinite(z_evaluation).all():
        raise ValueError('Stack inputs must be finite')
    if set(np.unique(y_calibration)) != {0, 1}:
        raise ValueError('The stack needs both calibration classes')
    model = stack_model(params).fit(z_calibration, y_calibration)
    scaler, logistic = model.steps[0][1], model.steps[-1][1]
    coefficients = dict(coefficients=[float(v) for v in logistic.coef_[0]], intercept=float(logistic.intercept_[0]),
                        input_mean=[float(v) for v in scaler.mean_], input_scale=[float(v) for v in scaler.scale_])
    return model.predict_proba(z_calibration)[:, 1], model.predict_proba(z_evaluation)[:, 1], coefficients
