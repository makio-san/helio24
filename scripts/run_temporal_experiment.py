"""Run the fixed walk-forward temporal-feature experiment."""
import json
from importlib.metadata import version
from pathlib import Path
import platform
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import joblib
import numpy as np
import pandas as pd
import sklearn
import xgboost

from helio24.data import ROOT
from helio24.full_data import sha256
from helio24.modeling import metrics
from helio24.temporal_experiment import (
    AUGMENTED_COLUMNS,
    BASE_COLUMNS,
    chronological_fold,
    error_audit,
    merge_feature_tables,
    predict,
    promotion_decision,
    score_at_recall_targets,
    xgboost_pipeline,
)


def verified_partition(partition):
    base_path = ROOT / f'data/full/partition{partition}.parquet'
    temporal_path = ROOT / f'data/temporal/partition{partition}.parquet'
    base_audit = json.loads(base_path.with_suffix('.json').read_text())
    temporal_audit = json.loads(temporal_path.with_suffix('.json').read_text())
    if sha256(base_path) != base_audit['features_sha256']:
        raise ValueError(f'Base feature checksum mismatch: partition {partition}')
    if sha256(temporal_path) != temporal_audit['features_sha256']:
        raise ValueError(f'Temporal feature checksum mismatch: partition {partition}')
    if base_audit['archive_md5'] != temporal_audit['archive_md5']:
        raise ValueError(f'Archive identity mismatch: partition {partition}')
    merged = merge_feature_tables(pd.read_parquet(base_path), pd.read_parquet(temporal_path))
    return merged, dict(base=base_audit, temporal=temporal_audit)


def run():
    output = ROOT / 'artifacts/experiment3'
    output.mkdir(parents=True, exist_ok=True)
    if (output / 'report.json').exists():
        raise RuntimeError('Experiment 3 already exists. Preserve it before another run.')

    protocol = ROOT / 'docs/third-experiment-protocol.md'
    exp2 = ROOT / 'artifacts/experiment2'
    exp2_frozen = json.loads((exp2 / 'frozen_decisions.json').read_text())
    exp2_predictions = pd.read_parquet(exp2 / 'predictions.parquet')
    source_audits, partitions = {}, {}
    for partition in range(1, 5):
        partitions[partition], source_audits[str(partition)] = verified_partition(partition)
    development = pd.concat(partitions.values(), ignore_index=True)

    validation_predictions = exp2_predictions[
        (exp2_predictions.split == 'validation') &
        (exp2_predictions.model == 'full_calibrated')
    ][['harp', 'forecast_time', 'probability']]
    validation = partitions[4].merge(
        validation_predictions, on=['harp', 'forecast_time'], how='inner', validate='one_to_one'
    )
    expected_validation = int((exp2_predictions.split.eq('validation') &
                               exp2_predictions.model.eq('full_calibrated')).sum())
    if len(validation) != expected_validation:
        raise ValueError('Experiment-2 validation predictions do not match partition 4')
    audit_outputs = error_audit(
        validation,
        validation.probability.to_numpy(),
        exp2_frozen['thresholds']['full_calibrated']['0.9'],
    )
    audited, by_quarter, by_missingness, by_harp, error_summary = audit_outputs
    audited.to_parquet(output / 'error_windows.parquet', index=False)
    by_quarter.to_csv(output / 'error_by_quarter.csv', index=False)
    by_missingness.to_csv(output / 'error_by_missingness.csv', index=False)
    by_harp.to_csv(output / 'error_by_harp.csv', index=False)
    (output / 'error_summary.json').write_text(json.dumps(error_summary, indent=2))
    print('Experiment-2 validation error audit saved.', flush=True)

    fold_specs = [('A', (1,), 2), ('B', (1, 2), 3), ('C', (1, 2, 3), 4)]
    results, split_audits, prediction_frames, fold_c_thresholds = [], [], [], {}
    for fold, training_partitions, evaluation_partition in fold_specs:
        train, evaluation, split_audit = chronological_fold(
            development, training_partitions, evaluation_partition
        )
        split_audit.update(fold=fold, training_windows=len(train), evaluation_windows=len(evaluation),
                           training_positives=int(train.target.sum()),
                           evaluation_positives=int(evaluation.target.sum()))
        split_audits.append(split_audit)
        for model_name, columns in [('control', BASE_COLUMNS), ('temporal', AUGMENTED_COLUMNS)]:
            model = xgboost_pipeline()
            model.fit(train[columns], train.target)
            probability = predict(model, evaluation, columns)
            rows = score_at_recall_targets(evaluation.target, probability, model_name, fold)
            results.extend(rows)
            if fold == 'C':
                fold_c_thresholds[model_name] = next(
                    row['threshold'] for row in rows if np.isclose(row['recall_target'], .9)
                )
            prediction_frames.append(pd.DataFrame({
                'fold': fold,
                'model': model_name,
                'harp': evaluation.harp.to_numpy(),
                'forecast_time': evaluation.forecast_time.to_numpy(),
                'target': evaluation.target.to_numpy(),
                'probability': probability,
            }))
            print(f'Fold {fold}: {model_name} complete', flush=True)

    decision = promotion_decision(results)
    decision.update(
        fold_c_thresholds=fold_c_thresholds,
        protocol_sha256=sha256(protocol),
        partition5_role='Previously inspected descriptive stability check only',
    )
    pd.DataFrame(results).to_csv(output / 'development_metrics.csv', index=False)
    pd.concat(prediction_frames, ignore_index=True).to_parquet(
        output / 'development_predictions.parquet', index=False
    )
    (output / 'splits.json').write_text(json.dumps(split_audits, indent=2))
    (output / 'frozen_decision.json').write_text(json.dumps(decision, indent=2))
    print('Development decision frozen before loading partition 5.', flush=True)

    partitions[5], source_audits['5'] = verified_partition(5)
    all_records = pd.concat(partitions.values(), ignore_index=True)
    train, retrospective, retrospective_split = chronological_fold(all_records, (1, 2, 3, 4), 5)
    retrospective_results, retrospective_predictions, final_models = [], [], {}
    for model_name, columns in [('control', BASE_COLUMNS), ('temporal', AUGMENTED_COLUMNS)]:
        model = xgboost_pipeline()
        model.fit(train[columns], train.target)
        probability = predict(model, retrospective, columns)
        threshold = fold_c_thresholds[model_name]
        retrospective_results.append(dict(
            model=model_name,
            recall_target=.9,
            **metrics(retrospective.target, probability, threshold),
        ))
        retrospective_predictions.append(pd.DataFrame({
            'model': model_name,
            'harp': retrospective.harp.to_numpy(),
            'forecast_time': retrospective.forecast_time.to_numpy(),
            'target': retrospective.target.to_numpy(),
            'probability': probability,
        }))
        final_models[model_name] = model
        print(f'Retrospective stability check: {model_name} complete', flush=True)

    pd.DataFrame(retrospective_results).to_csv(output / 'retrospective_metrics.csv', index=False)
    pd.concat(retrospective_predictions, ignore_index=True).to_parquet(
        output / 'retrospective_predictions.parquet', index=False
    )
    joblib.dump(dict(models=final_models, decision=decision), output / 'models.joblib')
    report = dict(
        decision=decision,
        development_metrics=results,
        retrospective_metrics=retrospective_results,
        development_splits=split_audits,
        retrospective_split=retrospective_split,
        error_audit=error_summary,
        source_audits=source_audits,
        source_code={name: sha256(ROOT / name) for name in [
            'helio24/data.py', 'helio24/temporal.py', 'helio24/temporal_experiment.py',
            'scripts/run_temporal_experiment.py',
        ]},
        versions=dict(
            python=platform.python_version(), numpy=np.__version__, pandas=pd.__version__,
            sklearn=sklearn.__version__, xgboost=xgboost.__version__,
            pyarrow=version('pyarrow'), joblib=version('joblib'),
        ),
        scope='Walk-forward development comparison plus previously inspected retrospective stability check',
    )
    (output / 'protocol.md').write_text(protocol.read_text())
    (output / 'report.json').write_text(json.dumps(report, indent=2, allow_nan=False))
    print(pd.DataFrame(results).query('recall_target == 0.9')[
        ['fold', 'model', 'recall', 'precision', 'fp', 'fn', 'average_precision', 'brier']
    ].to_string(index=False), flush=True)
    print('Decision:', json.dumps(decision, indent=2), flush=True)
    print('Retrospective:', pd.DataFrame(retrospective_results)[
        ['model', 'recall', 'precision', 'fp', 'fn', 'average_precision', 'brier']
    ].to_string(index=False), flush=True)
    return report


if __name__ == '__main__':
    run()
