"""Fixed baseline models, validation-only selection, and held-out evaluation."""
import hashlib
import json
import platform
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.dummy import DummyClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, confusion_matrix, log_loss, roc_curve
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from helio24.data import FEATURE_COLUMNS, ROOT, chronological_split


def metrics(y, probability, threshold):
    prediction = np.asarray(probability) >= threshold
    tn, fp, fn, tp = confusion_matrix(y, prediction, labels=[0, 1]).ravel()
    recall = tp / (tp + fn) if tp + fn else 0.0
    precision = tp / (tp + fp) if tp + fp else 0.0
    fpr = fp / (fp + tn) if fp + tn else 0.0
    return dict(n=len(y), positives=int(tp+fn), threshold=float(threshold),
                tp=int(tp), fp=int(fp), fn=int(fn), tn=int(tn),
                recall=float(recall), precision=float(precision), false_positive_rate=float(fpr),
                false_alarm_ratio=float(fp/(tp+fp)) if tp+fp else 0.0,
                alarms=int(tp+fp), tss=float(recall-fpr),
                average_precision=float(average_precision_score(y, probability)),
                brier=float(brier_score_loss(y, probability)),
                log_loss=float(log_loss(y, probability, labels=[0, 1])))


def threshold_curve(y, probability):
    """Candidate operating points. Prefer fewer false alarms when TSS ties."""
    fpr, recall, thresholds = roc_curve(y, probability, drop_intermediate=False)
    thresholds[0] = 1.0  # Probabilities are clipped below 1, so this means no alarms.
    positives, negatives = int(np.sum(y)), len(y)-int(np.sum(y))
    tp, fp = np.rint(recall*positives).astype(int), np.rint(fpr*negatives).astype(int)
    precision = np.divide(tp, tp+fp, out=np.zeros(len(tp), dtype=float), where=(tp+fp)>0)
    return pd.DataFrame(dict(threshold=thresholds, recall=recall, precision=precision,
                             false_positive_rate=fpr, false_alarms=fp, tss=recall-fpr))


def select_threshold(y, probability):
    curve = threshold_curve(y, probability)
    best = curve.sort_values(['tss', 'false_alarms', 'threshold'], ascending=[False, True, False]).iloc[0]
    return float(best.threshold), curve


def reliability_table(y, probability):
    frame = pd.DataFrame(dict(observed=np.asarray(y), probability=probability))
    frame['bin'] = pd.cut(frame.probability, np.linspace(0, 1, 11), include_lowest=True)
    result = frame.groupby('bin', observed=True).agg(
        count=('observed', 'size'), mean_probability=('probability', 'mean'),
        observed_rate=('observed', 'mean')).reset_index()
    result['bin'] = result['bin'].astype(str)
    return result


def predict(model, frame):
    return np.clip(model.predict_proba(frame[FEATURE_COLUMNS])[:, 1], 1e-9, 1-1e-9)


def run_experiment(table, output=ROOT / 'artifacts'):
    from xgboost import XGBClassifier
    import xgboost

    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    splits, split_audit = chronological_split(table)
    train, validation, test = (splits[name] for name in ['train', 'validation', 'test'])
    models = {
        'baseline': DummyClassifier(strategy='prior'),
        'logistic': make_pipeline(SimpleImputer(strategy='median', add_indicator=True),
                                  StandardScaler(), LogisticRegression(C=1.0, max_iter=3000, random_state=24)),
        'xgboost': make_pipeline(SimpleImputer(strategy='median', add_indicator=True),
                                 XGBClassifier(n_estimators=200, max_depth=3, learning_rate=0.04,
                                               min_child_weight=5, subsample=1, colsample_bytree=1,
                                               reg_lambda=5, tree_method='hist', eval_metric='logloss',
                                               n_jobs=2, random_state=24))
    }
    results, probabilities, thresholds, curves, calibration = [], {}, {}, [], []
    for name, model in models.items():
        model.fit(train[FEATURE_COLUMNS], train.target)
        probabilities[name] = predict(model, validation)
        threshold, curve = select_threshold(validation.target, probabilities[name])
        thresholds[name] = threshold
        curves.append(curve.assign(model=name))
        results.append(dict(model=name, split='validation', **metrics(validation.target, probabilities[name], threshold)))
        print(f'{name}: validation AP={results[-1]["average_precision"]:.4f}, threshold={threshold:.4f}', flush=True)
    # Freeze the model and thresholds before reading any test predictions/metrics.
    chosen = max(results, key=lambda result: result['average_precision'])['model']
    selection = dict(model=chosen, threshold=thresholds[chosen],
                     model_rule='Highest validation average precision; fixed model settings',
                     threshold_rule='Highest validation TSS; fewer false alarms break ties',
                     calibration='Raw model probabilities; calibration is measured, not fitted')
    (output / 'selection.json').write_text(json.dumps(selection, indent=2))
    pd.concat(curves, ignore_index=True).to_csv(output / 'validation_thresholds.csv', index=False)
    metadata_columns = ['file', 'partition', 'harp', 'observation_start', 'observation_last',
                        'forecast_time', 'prediction_end', 'label', 'flare_class', 'flare_id',
                        'peak_time', 'target', 'missing_fraction']
    all_predictions = []
    for split, group in [('validation', validation), ('test', test)]:
        for name, model in models.items():
            probability = probabilities[name] if split == 'validation' else predict(model, group)
            if split == 'test':
                results.append(dict(model=name, split=split, **metrics(group.target, probability, thresholds[name])))
            calibration.append(reliability_table(group.target, probability).assign(model=name, split=split))
            prediction = group[metadata_columns].copy()
            prediction['probability'] = probability
            prediction['alarm'] = probability >= thresholds[name]
            prediction['model'], prediction['split'] = name, split
            all_predictions.append(prediction)
    predictions = pd.concat(all_predictions, ignore_index=True)
    predictions.to_parquet(output / 'predictions.parquet', index=False)
    pd.concat(calibration, ignore_index=True).to_csv(output / 'calibration.csv', index=False)
    pd.DataFrame(results).to_csv(output / 'metrics.csv', index=False)
    errors = predictions[(predictions.model == chosen) & (predictions.split == 'test')].copy()
    errors['outcome'] = np.select(
        [errors.alarm & errors.target.eq(0), ~errors.alarm & errors.target.eq(1), errors.alarm & errors.target.eq(1)],
        ['false_alarm', 'miss', 'hit'], default='correct_quiet')
    errors.to_csv(output / 'test_outcomes.csv', index=False)
    joblib.dump(dict(model=models[chosen], features=FEATURE_COLUMNS, selection=selection), output / 'model.joblib')
    split_summary = {name: dict(n=len(group), positives=int(group.target.sum()),
                               harps=int(group.harp.nunique()),
                               start=str(group.observation_start.min()), end=str(group.prediction_end.max()))
                     for name, group in splits.items()}
    # Input digest includes selected records and features, not merely file names.
    digest = hashlib.sha256(pd.util.hash_pandas_object(table, index=True).values.tobytes()).hexdigest()
    report = dict(selection=selection, splits=split_summary, split_audit=split_audit,
                  training_prevalence=float(train.target.mean()), metrics=results, input_sha256=digest,
                  versions=dict(python=platform.python_version(), sklearn=sklearn.__version__,
                                xgboost=xgboost.__version__, pandas=pd.__version__, numpy=np.__version__),
                  sample_fractions=table.attrs.get('sample_fractions', {}),
                  scope='Class-blind development sample of partitions 1, 3, 5; not a full benchmark',
                  unit='forecast windows, not unique flares; overlapping windows are dependent')
    (output / 'report.json').write_text(json.dumps(report, indent=2))
    return report
