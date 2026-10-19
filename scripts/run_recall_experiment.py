"""Run the eight preregistered candidates without opening partition 5."""
import json
import platform
import sys
from importlib.metadata import version
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import joblib
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from xgboost import XGBClassifier
from helio24.calibration import SigmoidCalibration, recall_threshold, cluster_intervals
from helio24.data import ROOT, FEATURE_COLUMNS
from helio24.full_data import sha256
from helio24.metric_summary import enrich
from helio24.modeling import predict, metrics, reliability_table
from helio24.recall_experiment import candidates, region_weights, development_roles, decision


def run():
    output = ROOT / 'artifacts/experiment4'
    output.mkdir(exist_ok=False)
    reference_path = ROOT / 'artifacts/experiment2/report.json'
    frozen = json.loads(reference_path.read_text())
    sources = [ROOT / f'data/full/partition{p}.parquet' for p in range(1, 5)]
    for path in sources:
        if sha256(path) != frozen['source_features'][path.name]:
            raise ValueError(f'Feature checksum mismatch: {path.name}')
    groups, audit = development_roles(pd.concat([pd.read_parquet(p) for p in sources], ignore_index=True), frozen)
    train, calibration, validation = (groups[k] for k in ['train', 'calibration', 'validation'])
    summary = {k: dict(n=len(v), positives=int(v.target.sum()), harps=int(v.harp.nunique())) for k, v in groups.items()}
    (output / 'splits.json').write_text(json.dumps(dict(roles=summary, exclusions=audit), indent=2))
    protocol = ROOT / 'docs/fourth-experiment-protocol.md'
    (output / 'protocol.md').write_text(protocol.read_text())
    results, bins, intervals, saved_probabilities = [], [], [], {}
    for name, parameters in candidates().items():
        print(f'Training {name}: {parameters}', flush=True)
        model = make_pipeline(SimpleImputer(strategy='median', add_indicator=True),
                              XGBClassifier(**parameters, learning_rate=.04, subsample=1,
                                            colsample_bytree=1, tree_method='hist', eval_metric='logloss',
                                            n_jobs=2, random_state=24))
        kwargs = {'xgbclassifier__sample_weight': region_weights(train.harp)} if name == 'region_weight' else {}
        model.fit(train[FEATURE_COLUMNS], train.target, **kwargs)
        raw_cal = predict(model, calibration)
        calibrator = SigmoidCalibration().fit(raw_cal, calibration.target)
        cal = calibrator.transform(raw_cal)
        transfer = {kind: recall_threshold(calibration.target, p, .95) for kind, p in [('raw', raw_cal), ('calibrated', cal)]}
        (output / f'{name}_frozen_thresholds.json').write_text(json.dumps(transfer, indent=2))
        raw_val = predict(model, validation)
        val = calibrator.transform(raw_val)
        saved_probabilities[name] = val
        joblib.dump(dict(model=model, calibrator=calibrator, transfer_thresholds=transfer), output / f'{name}.joblib')
        prediction_frames = []
        for split, group, raw, calibrated in [('calibration', calibration, raw_cal, cal), ('validation', validation, raw_val, val)]:
            frame = group[['harp', 'forecast_time', 'prediction_end', 'target']].copy()
            frame['raw'], frame['calibrated'], frame['split'] = raw, calibrated, split
            prediction_frames.append(frame)
            for kind, p in [('raw', raw), ('calibrated', calibrated)]:
                bins.append(reliability_table(group.target, p).assign(model=name, probability_kind=kind, split=split))
                if split != 'validation':
                    continue
                for target in [.9, .95, .99]:
                    threshold = recall_threshold(group.target, p, target)
                    results.append(dict(model=name, probability_kind=kind, threshold_role='development', recall_target=target,
                                        **enrich(metrics(group.target, p, threshold))))
                results.append(dict(model=name, probability_kind=kind, threshold_role='calibration_transfer', recall_target=.95,
                                    **enrich(metrics(group.target, p, transfer[kind]))))
        pd.concat(prediction_frames).to_parquet(output / f'{name}_predictions.parquet', index=False)
        primary = [r for r in results if r['model'] == name and r['probability_kind'] == 'calibrated'
                   and r['threshold_role'] == 'development' and r['recall_target'] == .95][0]
        if name == 'control' and tuple(primary[k] for k in ['tp', 'fp', 'fn', 'tn']) != (1023, 5183, 53, 44372):
            raise ValueError('Control reproduction failed; stop before candidate comparison')
        pd.DataFrame(results).to_csv(output / 'metrics.csv', index=False)
        print(f"Completed {name}: recall={primary['recall']:.4f}, FP={primary['fp']}, AP={primary['average_precision']:.4f}", flush=True)
    primary = sorted([r for r in results if r['probability_kind'] == 'calibrated' and r['threshold_role'] == 'development'
                      and r['recall_target'] == .95], key=lambda r: (r['fp'], -r['average_precision'], r['brier'], r['model']))
    control = next(r for r in primary if r['model'] == 'control')
    decisions = [decision(r, control) for r in primary]
    promising = [d['model'] for d in decisions if d['promising']]
    selected = promising[0] if promising else primary[0]['model']
    for name in dict.fromkeys(['control', selected]):
        for role in ['development', 'calibration_transfer']:
            row = next(r for r in results if r['model'] == name and r['probability_kind'] == 'calibrated'
                       and r['threshold_role'] == role and r['recall_target'] == .95)
            ci = cluster_intervals(validation.target, saved_probabilities[name], validation.harp, row['threshold'])
            intervals.extend(dict(model=name, threshold_role=role, metric=k, **v) for k, v in ci.items())
    pd.DataFrame(intervals).to_csv(output / 'cluster_intervals.csv', index=False)
    pd.concat(bins).to_csv(output / 'calibration.csv', index=False)
    code = ['scripts/run_recall_experiment.py', 'helio24/recall_experiment.py', 'helio24/calibration.py',
            'helio24/modeling.py', 'helio24/data.py', 'helio24/metric_summary.py']
    report = dict(scope='Previously inspected development partition 4; not an independent test',
                  roles=summary, purge_audit=audit, metrics=results, decisions=decisions,
                  selected_for_analysis=selected, promising_candidates=promising, intervals=intervals,
                  bootstrap=dict(draws=1000, seed=24, unit='HARP', confidence=.95),
                  parameters=candidates(), protocol_sha256=sha256(protocol), reference_report_sha256=sha256(reference_path),
                  source_features={p.name: sha256(p) for p in sources}, source_code={p: sha256(ROOT / p) for p in code},
                  versions=dict(python=platform.python_version(), **{p: version(p) for p in ['numpy', 'pandas', 'scikit-learn', 'xgboost', 'scipy', 'joblib']}))
    (output / 'report.json').write_text(json.dumps(report, indent=2, allow_nan=False))
    print(json.dumps(decisions, indent=2), flush=True)


if __name__ == '__main__':
    run()
