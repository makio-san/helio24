"""Run the preregistered full-data experiment without replacing experiment 1."""
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
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from xgboost import XGBClassifier

from helio24.calibration import SigmoidCalibration, split_roles, recall_threshold, cluster_intervals, paired_brier_interval
from helio24.data import ROOT, FEATURE_COLUMNS
from helio24.full_data import sha256
from helio24.modeling import predict, metrics, reliability_table


def run():
    output = ROOT / 'artifacts/experiment2'
    output.mkdir(parents=True, exist_ok=True)
    if (output / 'report.json').exists():
        raise RuntimeError('Experiment 2 already exists. Preserve it before starting another experiment.')
    snapshot = ROOT / 'artifacts/experiment1'
    snapshot_hashes = json.loads((snapshot / 'snapshot.json').read_text())
    for name, digest in snapshot_hashes.items():
        if sha256(snapshot / name) != digest:
            raise ValueError(f'Experiment 1 snapshot changed: {name}')
    sources = [ROOT / f'data/full/partition{p}.parquet' for p in range(1, 6)]
    source_audits = []
    for p, source in enumerate(sources, 1):
        audit = json.loads((source.with_suffix('.json')).read_text())
        if sha256(source) != audit['features_sha256']:
            raise ValueError(f'Feature checksum mismatch: partition {p}')
        source_audits.append(audit)
    table = pd.concat([pd.read_parquet(path) for path in sources], ignore_index=True)
    groups, exclusions = split_roles(table)
    summary = {name: dict(n=len(frame), positives=int(frame.target.sum()), harps=int(frame.harp.nunique()),
                          observation_start=str(frame.observation_start.min()), prediction_end=str(frame.prediction_end.max()))
               for name, frame in groups.items()}
    (output / 'splits.json').write_text(json.dumps(dict(roles=summary, exclusions=exclusions), indent=2))
    print(json.dumps(summary, indent=2), flush=True)
    train, calibration, validation, retrospective = (groups[name] for name in ['train', 'calibration', 'validation', 'audit'])
    model = make_pipeline(SimpleImputer(strategy='median', add_indicator=True),
                          XGBClassifier(n_estimators=200, max_depth=3, learning_rate=0.04,
                                        min_child_weight=5, subsample=1, colsample_bytree=1,
                                        reg_lambda=5, tree_method='hist', eval_metric='logloss',
                                        n_jobs=2, random_state=24))
    model.fit(train[FEATURE_COLUMNS], train.target)
    calibrator = SigmoidCalibration().fit(predict(model, calibration), calibration.target)
    original = joblib.load(snapshot / 'model.joblib')['model']
    prevalence = float(train.target.mean())

    def probabilities(frame):
        raw = predict(model, frame)
        return dict(original_sample=predict(original, frame), full_raw=raw,
                    full_calibrated=calibrator.transform(raw), baseline=np.full(len(frame), prevalence))

    validation_probabilities = probabilities(validation)
    thresholds = {name: {str(target): recall_threshold(validation.target, p, target) for target in [.8, .9, .95]}
                  for name, p in validation_probabilities.items()}
    for target in ['0.8', '0.9', '0.95']:
        if not np.array_equal(validation_probabilities['full_raw'] >= thresholds['full_raw'][target],
                              validation_probabilities['full_calibrated'] >= thresholds['full_calibrated'][target]):
            raise ValueError('Calibration unexpectedly changed the validation alarm sets')
    scores = {name: metrics(validation.target, p, thresholds[name]['0.9']) for name, p in validation_probabilities.items()}
    selected = 'full_calibrated' if scores['full_calibrated']['brier'] < scores['full_raw']['brier'] else 'full_raw'
    frozen = dict(selected_probability=selected, thresholds=thresholds,
                  calibrator=dict(slope=calibrator.slope, intercept=calibrator.intercept),
                  protocol_sha256=sha256(ROOT / 'docs/second-experiment-protocol.md'))
    (output / 'frozen_decisions.json').write_text(json.dumps(frozen, indent=2))
    joblib.dump(dict(model=model, calibrator=calibrator, selection=frozen), output / 'model.joblib')
    print('Validation decisions frozen. Evaluating the previously inspected audit period.', flush=True)
    audit_probabilities = probabilities(retrospective)
    results, intervals, reliability, frames = [], [], [], []
    for split, group, probability_set in [('validation', validation, validation_probabilities), ('audit', retrospective, audit_probabilities)]:
        for name, probability in probability_set.items():
            reliability.append(reliability_table(group.target, probability).assign(model=name, split=split))
            for target, threshold in thresholds[name].items():
                results.append(dict(model=name, split=split, recall_target=float(target), **metrics(group.target, probability, threshold)))
                if split == 'audit':
                    ci = cluster_intervals(group.target, probability, group.harp, threshold)
                    for metric, values in ci.items():
                        intervals.append(dict(model=name, recall_target=float(target), metric=metric, **values))
            frame = group[['harp', 'forecast_time', 'prediction_end', 'label', 'target']].copy()
            frame['probability'], frame['model'], frame['split'] = probability, name, split
            frames.append(frame)
    paired = paired_brier_interval(retrospective.target, audit_probabilities['full_raw'],
                                   audit_probabilities['full_calibrated'], retrospective.harp)
    pd.DataFrame(results).to_csv(output / 'metrics.csv', index=False)
    pd.DataFrame(intervals).to_csv(output / 'cluster_intervals.csv', index=False)
    pd.concat(reliability, ignore_index=True).to_csv(output / 'calibration.csv', index=False)
    pd.concat(frames, ignore_index=True).to_parquet(output / 'predictions.parquet', index=False)
    report = dict(protocol=frozen, roles=summary, purge_audit=exclusions, metrics=results,
                  archive_sources=source_audits, reference_model_sha256=snapshot_hashes['model.joblib'],
                  paired_brier_difference=paired, bootstrap=dict(draws=1000, seed=24, unit='HARP', confidence=.95),
                  source_features={path.name: sha256(path) for path in sources},
                  source_code={name: sha256(ROOT / name) for name in ['helio24/data.py', 'helio24/calibration.py', 'helio24/modeling.py', 'scripts/run_calibration.py']},
                  versions=dict(python=platform.python_version(), numpy=np.__version__, pandas=pd.__version__,
                                sklearn=sklearn.__version__, xgboost=xgboost.__version__,
                                scipy=version('scipy'), pyarrow=version('pyarrow'), joblib=version('joblib')),
                  scope='Full-data retrospective audit; partition 5 was inspected in experiment 1; not an untouched test')
    (output / 'report.json').write_text(json.dumps(report, indent=2, allow_nan=False))
    (output / 'protocol.md').write_text((ROOT / 'docs/second-experiment-protocol.md').read_text())
    print(pd.DataFrame(results).query('split == "audit"')[['model', 'recall_target', 'recall', 'precision', 'fp', 'fn', 'brier']].to_string(index=False), flush=True)
    print('Paired calibrated-minus-raw Brier:', paired, flush=True)
    return report


if __name__ == '__main__':
    run()
