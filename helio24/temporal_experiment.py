"""Walk-forward comparison and retrospective error-audit helpers."""
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from xgboost import XGBClassifier

from helio24.calibration import recall_threshold
from helio24.data import FEATURE_COLUMNS
from helio24.modeling import metrics
from helio24.temporal import TEMPORAL_FEATURE_COLUMNS


def merge_feature_tables(base, temporal):
    """Require an exact one-to-one match before adding temporal columns."""
    keys = ['archive_member', 'partition', 'harp', 'forecast_time', 'target']
    if base.duplicated('archive_member').any() or temporal.duplicated('archive_member').any():
        raise ValueError('Feature tables contain duplicate archive members')
    if len(base) != len(temporal):
        raise ValueError('Base and temporal feature counts differ')
    merged = base.merge(temporal[keys+TEMPORAL_FEATURE_COLUMNS], on=keys, how='outer',
                        validate='one_to_one', indicator=True)
    if not merged['_merge'].eq('both').all():
        raise ValueError('Base and temporal feature identities differ')
    return merged.drop(columns='_merge').sort_values(['forecast_time', 'harp']).reset_index(drop=True)


def chronological_fold(table, training_partitions, evaluation_partition):
    """Purge prediction overlap and prevent a HARP from crossing a fold boundary."""
    train = table[table.partition.isin(training_partitions)].copy()
    evaluation = table[table.partition.eq(evaluation_partition)].copy()
    if train.empty or evaluation.empty:
        raise ValueError('A walk-forward fold cannot be empty')
    boundary = evaluation.observation_start.min()
    before_train = len(train)
    train = train[train.prediction_end <= boundary].copy()
    shared = set(train.harp) & set(evaluation.harp)
    before_evaluation = len(evaluation)
    evaluation = evaluation[~evaluation.harp.isin(shared)].copy()
    for name, frame in [('training', train), ('evaluation', evaluation)]:
        if frame.empty or frame.target.nunique() != 2:
            raise ValueError(f'{name} fold needs both target classes')
        if frame.duplicated(['harp', 'forecast_time']).any():
            raise ValueError(f'{name} fold contains duplicate observations')
    if train.prediction_end.max() > evaluation.observation_start.min():
        raise ValueError('Temporal overlap remains in walk-forward fold')
    audit = dict(
        training_partitions=list(training_partitions),
        evaluation_partition=int(evaluation_partition),
        boundary=str(boundary),
        boundary_removed=before_train-len(train),
        shared_harps=sorted(map(int, shared)),
        shared_harp_rows_removed=before_evaluation-len(evaluation),
    )
    return train, evaluation, audit


def xgboost_pipeline():
    return make_pipeline(
        SimpleImputer(strategy='median', add_indicator=True),
        XGBClassifier(
            n_estimators=200,
            max_depth=3,
            learning_rate=0.04,
            min_child_weight=5,
            subsample=1,
            colsample_bytree=1,
            reg_lambda=5,
            tree_method='hist',
            eval_metric='logloss',
            n_jobs=2,
            random_state=24,
        ),
    )


def predict(model, frame, columns):
    return np.clip(model.predict_proba(frame[columns])[:, 1], 1e-9, 1-1e-9)


def score_at_recall_targets(target, probability, model_name, fold):
    rows = []
    for required in (.8, .9, .95):
        threshold = recall_threshold(target, probability, required)
        rows.append(dict(model=model_name, fold=fold, recall_target=required,
                         **metrics(target, probability, threshold)))
    return rows


def promotion_decision(results):
    """Apply the fixed fold-majority and pooled-false-alarm rule."""
    frame = pd.DataFrame(results)
    at_90 = frame[np.isclose(frame.recall_target, .9)]
    pivot_fp = at_90.pivot(index='fold', columns='model', values='fp')
    pivot_ap = at_90.pivot(index='fold', columns='model', values='average_precision')
    expected = {'control', 'temporal'}
    if set(pivot_fp.columns) != expected or len(pivot_fp) != 3:
        raise ValueError('Promotion needs both models in three development folds')
    fewer_fp_folds = int((pivot_fp.temporal < pivot_fp.control).sum())
    nonlower_ap_folds = int((pivot_ap.temporal >= pivot_ap.control).sum())
    control_fp = int(pivot_fp.control.sum())
    temporal_fp = int(pivot_fp.temporal.sum())
    promising = fewer_fp_folds >= 2 and temporal_fp < control_fp and nonlower_ap_folds >= 2
    return dict(
        promising=bool(promising),
        fewer_false_alarm_folds=fewer_fp_folds,
        nonlower_average_precision_folds=nonlower_ap_folds,
        pooled_control_false_alarms=control_fp,
        pooled_temporal_false_alarms=temporal_fp,
    )


def classify_outcomes(target, probability, threshold):
    target = np.asarray(target, dtype=int)
    alarm = np.asarray(probability) >= threshold
    return np.select(
        [alarm & (target == 1), ~alarm & (target == 1), alarm & (target == 0)],
        ['hit', 'miss', 'false_alarm'],
        default='correct_quiet',
    )


def grouped_error_rates(frame, group):
    counts = pd.crosstab(frame[group], frame.outcome).reindex(
        columns=['hit', 'miss', 'false_alarm', 'correct_quiet'], fill_value=0
    )
    counts['windows'] = counts.sum(axis=1)
    counts['positives'] = counts.hit + counts.miss
    counts['negatives'] = counts.false_alarm + counts.correct_quiet
    counts['miss_rate'] = np.divide(
        counts.miss, counts.positives,
        out=np.full(len(counts), np.nan), where=counts.positives.to_numpy() > 0,
    )
    counts['false_alarm_rate'] = np.divide(
        counts.false_alarm, counts.negatives,
        out=np.full(len(counts), np.nan), where=counts.negatives.to_numpy() > 0,
    )
    return counts.reset_index()


def error_audit(frame, probability, threshold):
    audited = frame[['harp', 'forecast_time', 'target', 'missing_fraction']].copy()
    audited['probability'] = probability
    audited['outcome'] = classify_outcomes(audited.target, probability, threshold)
    audited['quarter'] = audited.forecast_time.dt.to_period('Q').astype(str)
    audited['missingness'] = pd.cut(
        audited.missing_fraction,
        bins=[-np.inf, 0, .01, .05, np.inf],
        labels=['none', '(0, 1%]', '(1%, 5%]', '>5%'],
    ).astype(str)
    by_quarter = grouped_error_rates(audited, 'quarter')
    by_missingness = grouped_error_rates(audited, 'missingness')
    by_harp = grouped_error_rates(audited, 'harp')
    by_harp['errors'] = by_harp['miss'] + by_harp['false_alarm']
    by_harp = by_harp.sort_values(['errors', 'windows', 'harp'], ascending=[False, False, True])
    total_errors = int((audited.outcome.isin(['miss', 'false_alarm'])).sum())
    concentration = float(by_harp.head(10).errors.sum()/total_errors) if total_errors else 0.0
    summary = dict(
        threshold=float(threshold),
        windows=len(audited),
        outcome_counts={name: int(count) for name, count in audited.outcome.value_counts().items()},
        regions=int(audited.harp.nunique()),
        top_10_region_error_share=concentration,
    )
    return audited, by_quarter, by_missingness, by_harp, summary


BASE_COLUMNS = FEATURE_COLUMNS
AUGMENTED_COLUMNS = FEATURE_COLUMNS + TEMPORAL_FEATURE_COLUMNS
