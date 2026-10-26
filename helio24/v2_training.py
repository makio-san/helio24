"""Reviewed development-only model fitting for Experiment 5."""
import hashlib
import json
import platform
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from helio24.calibration import SigmoidCalibration, recall_threshold
from helio24.data import FEATURE_COLUMNS
from helio24.evaluation_protocol import require_training_ready
from helio24.full_data import sha256
from helio24.metric_summary import enrich
from helio24.modeling import metrics, reliability_table


METADATA = ['harp', 'role', 'observation_start', 'forecast_time',
            'prediction_end', 'missing_fraction', 'target', 'label_status']


def load_development(materialized, expected_report_sha256):
    """Verify every frozen shard before loading development roles."""
    report_path = materialized / 'report.json'
    if sha256(report_path) != expected_report_sha256:
        raise ValueError('Materialization report hash changed')
    report = json.loads(report_path.read_text())
    frames = []
    for item in report['shards']:
        path = materialized / 'shards' / item['file']
        if path.stat().st_size != item['bytes'] or sha256(path) != item['sha256']:
            raise ValueError(f'Materialized shard changed: {item["file"]}')
        frames.append(pd.read_parquet(path, columns=[*METADATA, *FEATURE_COLUMNS]))
    table = pd.concat(frames, ignore_index=True)
    expected_columns = {*METADATA, *FEATURE_COLUMNS}
    if set(table.columns) != expected_columns:
        raise ValueError('Unexpected development table schema')
    if set(table.role) != {'train', 'calibration', 'validation'}:
        raise ValueError('Reserved or unknown role in development table')
    if table.duplicated(['harp', 'forecast_time']).any():
        raise ValueError('Duplicate development HARP/forecast key')
    if not table.label_status.isin(['positive', 'negative']).all():
        raise ValueError('Excluded labels remain in development table')
    groups = {name: table[table.role.eq(name)].sort_values(['forecast_time', 'harp']).copy()
              for name in ['train', 'calibration', 'validation']}
    for name, group in groups.items():
        if len(group) != report['rows'][name] or int(group.target.sum()) != report['positives'][name]:
            raise ValueError(f'Materialized {name} counts changed')
        if set(group.target.unique()) != {0, 1}:
            raise ValueError(f'{name} requires both classes')
    return groups, report


def candidate_models(protocol):
    from xgboost import XGBClassifier

    logistic = protocol['candidates']['logistic']
    tree = protocol['candidates']['xgboost']
    return {
        'logistic': make_pipeline(
            SimpleImputer(strategy='median', add_indicator=True),
            StandardScaler(),
            LogisticRegression(**logistic)),
        'xgboost': make_pipeline(
            SimpleImputer(strategy='median', add_indicator=True),
            XGBClassifier(**tree)),
    }


def fit_development(groups, protocol, output):
    """Fit fixed candidates and select only on the validation role."""
    if output.exists():
        raise RuntimeError('Preserve the existing development experiment')
    require_training_ready(protocol)
    output.mkdir(parents=True)
    train, calibration, validation = (groups[name] for name in
                                      ['train', 'calibration', 'validation'])
    arrays = {name: group[FEATURE_COLUMNS].to_numpy(dtype=np.float32, copy=True)
              for name, group in groups.items()}
    targets = {name: group.target.to_numpy(dtype=np.int8)
               for name, group in groups.items()}
    prevalence = float(targets['train'].mean())
    probabilities = {
        'baseline': {
            'calibration': np.full(len(calibration), prevalence),
            'validation': np.full(len(validation), prevalence),
        }
    }
    fitted, calibrators = {}, {}
    for name, model in candidate_models(protocol).items():
        model.fit(arrays['train'], targets['train'])
        raw_calibration = np.clip(model.predict_proba(arrays['calibration'])[:, 1],
                                  1e-9, 1-1e-9)
        calibrator = SigmoidCalibration().fit(raw_calibration, targets['calibration'])
        raw_validation = np.clip(model.predict_proba(arrays['validation'])[:, 1],
                                 1e-9, 1-1e-9)
        probabilities[name] = {
            'calibration': calibrator.transform(raw_calibration),
            'validation': calibrator.transform(raw_validation),
            'raw_validation': raw_validation,
        }
        fitted[name], calibrators[name] = model, calibrator
        print(f'{name}: fitted and calibrated', flush=True)

    results, thresholds, reliability, prediction_frames = [], {}, [], []
    required_recall = protocol['primary_recall']
    for name, split_probabilities in probabilities.items():
        probability = split_probabilities['validation']
        threshold = recall_threshold(targets['validation'], probability, required_recall)
        thresholds[name] = threshold
        result = enrich({'model': name, 'split': 'validation',
                         **metrics(targets['validation'], probability, threshold)})
        results.append(result)
        reliability.append(reliability_table(targets['validation'], probability)
                           .assign(model=name, split='validation'))
        prediction = validation[METADATA].copy()
        prediction['probability'] = probability
        prediction['alarm'] = probability >= threshold
        prediction['model'] = name
        prediction_frames.append(prediction)
        print(f'{name}: recall={result["recall"]:.6f}, precision={result["precision"]:.6f}, '
              f'FP={result["fp"]}', flush=True)

    learned = [row for row in results if row['model'] != 'baseline']
    winner = sorted(learned, key=lambda row: (-row['precision'], row['fp'],
                                              -row['average_precision'], row['model']))[0]
    selection = {
        'model': winner['model'], 'threshold': thresholds[winner['model']],
        'required_recall': required_recall,
        'rule': 'Maximum validation precision, then minimum false positives, among fixed learned candidates satisfying recall >= 0.95',
        'reserved_test_accessed': False,
    }
    decision = {
        'selection': selection,
        'protocol_sha256': hashlib.sha256(
            json.dumps(protocol, sort_keys=True, separators=(',', ':')).encode()).hexdigest(),
        'feature_columns': FEATURE_COLUMNS,
        'training_prevalence': prevalence,
    }
    (output / 'selection.json').write_text(json.dumps(decision, indent=2)+'\n')
    pd.DataFrame(results).to_csv(output / 'metrics.csv', index=False)
    pd.concat(reliability, ignore_index=True).to_csv(output / 'reliability.csv', index=False)
    pd.concat(prediction_frames, ignore_index=True).to_parquet(
        output / 'validation_predictions.parquet', index=False, compression='zstd')
    for name, model in fitted.items():
        joblib.dump({'model': model, 'calibrator': calibrators[name],
                     'features': FEATURE_COLUMNS, 'threshold': thresholds[name]},
                    output / f'{name}.joblib')
    return {
        'selection': selection,
        'training_prevalence': prevalence,
        'metrics': results,
        'roles': {name: {'rows': len(group), 'positives': int(group.target.sum()),
                         'harps': int(group.harp.nunique()),
                         'first_forecast': group.forecast_time.min().isoformat(),
                         'last_forecast': group.forecast_time.max().isoformat()}
                  for name, group in groups.items()},
        'versions': {'python': platform.python_version(), 'numpy': np.__version__,
                     'pandas': pd.__version__, 'sklearn': sklearn.__version__},
        'artifact_hashes': {name: sha256(output / name) for name in
                            ['selection.json', 'metrics.csv', 'reliability.csv',
                             'validation_predictions.parquet', 'logistic.joblib',
                             'xgboost.joblib']},
        'reserved_test_accessed': False,
    }
