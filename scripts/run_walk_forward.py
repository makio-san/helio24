"""Audit fixed model recipes on successive years without evaluation threshold tuning."""
import argparse
import gc
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import joblib
import numpy as np
import pandas as pd
from helio24.data import ROOT, FEATURE_COLUMNS
from helio24.full_data import sha256
from helio24.calibration import SigmoidCalibration, recall_threshold, cluster_intervals
from helio24.modeling import metrics
from helio24.metric_summary import enrich
from helio24.v2_training import load_development, candidate_models, METADATA
from helio24.walk_forward import annual_fold, evaluable_metrics


def run(protocol_path, output):
    if output.exists():
        raise ValueError('Preserve existing experiment')
    protocol = json.loads(protocol_path.read_text())
    if any(year >= 2024 for year in protocol['evaluation_years']):
        raise ValueError('Reserved test forbidden')
    original, _ = load_development(ROOT/protocol['source'], protocol['source_sha256'])
    table = pd.concat(original.values(), ignore_index=True)
    del original
    output.mkdir(parents=True)
    rows, folds, uncertainties = [], [], []
    for year in protocol['evaluation_years']:
        groups, audit = annual_fold(table, year)
        directory = output/str(year); directory.mkdir()
        fold = {'year': year, 'audit': audit, 'status': 'complete'}
        invalid = [role for role in ['train', 'calibration'] if groups[role].target.nunique() != 2]
        if invalid or groups['evaluation'].empty:
            fold.update(status='skipped', reason=f'Training/calibration lacks both classes: {invalid}' if invalid else 'Empty evaluation')
            folds.append(fold)
            (directory/'split.json').write_text(json.dumps(fold, indent=2)+'\n')
            print(f'{year}: {fold["reason"]}', flush=True)
            continue
        (directory/'split.json').write_text(json.dumps(fold, indent=2)+'\n')
        X = {role: g[FEATURE_COLUMNS].to_numpy(dtype=np.float32) for role, g in groups.items()}
        y = {role: g.target.to_numpy(dtype=np.int8) for role, g in groups.items()}
        models = candidate_models(protocol)
        calibrated, calibrators = {}, {}
        for name, model in models.items():
            model.fit(X['train'], y['train'])
            raw = model.predict_proba(X['calibration'])[:, 1]
            calibrators[name] = SigmoidCalibration().fit(raw, y['calibration'])
            calibrated[name] = calibrators[name].transform(raw)
        weight = protocol['ensemble']['logistic_weight']
        calibrated['ensemble'] = weight*calibrated['logistic']+(1-weight)*calibrated['xgboost']
        calibrated['baseline'] = np.full(len(y['calibration']), y['train'].mean())
        thresholds = {name: recall_threshold(y['calibration'], p, protocol['required_recall'])
                      for name, p in calibrated.items()}
        (directory/'thresholds.json').write_text(json.dumps(thresholds, indent=2)+'\n')
        joblib.dump({'models': models, 'calibrators': calibrators, 'thresholds': thresholds,
                     'features': FEATURE_COLUMNS, 'ensemble': protocol['ensemble']}, directory/'models.joblib')
        evaluation = {name: calibrators[name].transform(model.predict_proba(X['evaluation'])[:, 1])
                      for name, model in models.items()}
        evaluation['ensemble'] = weight*evaluation['logistic']+(1-weight)*evaluation['xgboost']
        evaluation['baseline'] = np.full(len(y['evaluation']), y['train'].mean())
        predictions = groups['evaluation'][METADATA].copy()
        for name, probability in evaluation.items():
            m = evaluable_metrics(enrich(metrics(y['evaluation'], probability, thresholds[name])))
            rows.append({'year': year, 'model': name, **m})
            intervals = cluster_intervals(y['evaluation'], probability, groups['evaluation'].harp,
                                          thresholds[name], **protocol['bootstrap'])
            uncertainties.append({'year': year, 'model': name, 'intervals': intervals})
            predictions[name] = probability
            predictions[f'{name}_alarm'] = probability >= thresholds[name]
        predictions.to_parquet(directory/'predictions.parquet', index=False)
        errors = predictions.assign(fp=predictions.ensemble_alarm & predictions.target.eq(0),
                                    fn=~predictions.ensemble_alarm & predictions.target.eq(1))
        regions = errors.groupby('harp').agg(rows=('target','size'), positives=('target','sum'),
                    fp=('fp','sum'), fn=('fn','sum'), mean_missing=('missing_fraction','mean')).reset_index()
        regions.sort_values('fp', ascending=False).to_csv(directory/'region_errors.csv', index=False)
        fold['error_summary'] = {'fp': int(regions.fp.sum()), 'fn': int(regions.fn.sum()),
            'top10_region_fp': int(regions.nlargest(10, 'fp').fp.sum()),
            'zero_positive_region_fp': int(regions.loc[regions.positives.eq(0), 'fp'].sum())}
        folds.append(fold)
        print(f'{year}: ensemble precision={rows[-2]["precision"]}, recall={rows[-2]["recall"]}', flush=True)
        del X, y, models, calibrators, groups, predictions, errors, regions, evaluation, calibrated
        gc.collect()
    pd.DataFrame(rows).to_csv(output/'metrics.csv', index=False)
    result = {'protocol': protocol, 'protocol_sha256': sha256(protocol_path), 'folds': folds,
              'metrics': rows, 'conditional_cluster_intervals': uncertainties,
              'reserved_test_accessed': False,
              'code_hashes': {name: sha256(ROOT/name) for name in [
                  'scripts/run_walk_forward.py', 'helio24/walk_forward.py', 'helio24/v2_training.py',
                  'helio24/modeling.py', 'helio24/calibration.py']},
              'artifact_hashes': {str(p.relative_to(output)): sha256(p) for p in sorted(output.rglob('*')) if p.is_file()}}
    (output/'report.json').write_text(json.dumps(result, indent=2)+'\n')
    print(output/'report.json', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--protocol', type=Path, default=ROOT/'config/walk-forward-v1.json')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    run(args.protocol.resolve(), args.output.resolve())
