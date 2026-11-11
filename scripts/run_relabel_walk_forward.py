"""Rerun the frozen walk-forward recipes on the relabelled table (config/relabel-v1.json)."""
import argparse
import gc
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score

from helio24.calibration import SigmoidCalibration, cluster_intervals, recall_threshold
from helio24.data import FEATURE_COLUMNS, ROOT
from helio24.full_data import sha256
from helio24.v2_training import METADATA, candidate_models, load_development
from helio24.walk_forward import annual_fold

POINTS = {'recall_0.95': 0.95, 'recall_0.90': 0.90}


def score(year, arm, point, threshold, frame, probability, bootstrap):
    y = frame.target.to_numpy(dtype=int)
    p = np.asarray(probability, dtype=float)
    alarm = p >= threshold
    tp, fp = int((alarm & (y == 1)).sum()), int((alarm & (y == 0)).sum())
    fn, tn = int((~alarm & (y == 1)).sum()), int((~alarm & (y == 0)).sum())
    row = dict(year=year, arm=arm, operating_point=point, threshold=float(threshold), windows=len(y),
               harps=int(frame.harp.nunique()), positives=int(y.sum()), tp=tp, fp=fp, fn=fn, tn=tn,
               precision=tp/(tp+fp) if tp+fp else None, recall=tp/(tp+fn) if tp+fn else None,
               accuracy=(tp+tn)/len(y), always_negative_accuracy=float((y == 0).mean()),
               average_precision=float(average_precision_score(y, p)) if y.sum() else None)
    intervals = cluster_intervals(y, p, frame.harp, threshold, **bootstrap)
    for name in ['precision', 'recall']:
        row[f'{name}_lower'], row[f'{name}_upper'] = intervals[name]['lower'], intervals[name]['upper']
    return row


def ensemble(models, calibrators, weights, X):
    parts = {name: calibrators[name].transform(model.predict_proba(X)[:, 1]) for name, model in models.items()}
    return weights['logistic_weight']*parts['logistic']+weights['xgboost_weight']*parts['xgboost']


def run(config_path, output):
    if output.exists():
        raise ValueError('Preserve existing experiment')
    config = json.loads(config_path.read_text())
    evidence = config['evidence']
    source = ROOT/config['materialisation']['output']
    source_report = json.loads((source/'report.json').read_text())
    if source_report['protocol_sha256'] != sha256(config_path):
        raise ValueError('Relabelled table was built under another protocol')
    if not source_report['frozen_consistency']['features_identical']:
        raise ValueError('Relabelled table failed the frozen consistency check')
    for path, expected in [(ROOT/evidence['frozen_walk_forward']/'report.json', evidence['frozen_walk_forward_report_sha256']),
                           (ROOT/evidence['frozen_predictions']/'report.json', evidence['frozen_predictions_report_sha256']),
                           (ROOT/evidence['watch_tier_thresholds'], evidence['watch_tier_thresholds_sha256'])]:
        if sha256(path) != expected:
            raise ValueError(f'Frozen input changed: {path}')
    recipes = json.loads((ROOT/evidence['recipes']).read_text())
    if any(year >= 2024 for year in recipes['evaluation_years']):
        raise ValueError('Reserved test forbidden')
    watch = json.loads((ROOT/evidence['watch_tier_thresholds']).read_text())
    groups, _ = load_development(source, sha256(source/'report.json'))
    table = pd.concat(groups.values(), ignore_index=True)
    del groups
    output.mkdir(parents=True)
    rows, folds = [], []
    for year in recipes['evaluation_years']:
        split, audit = annual_fold(table, year)
        fold = {'year': year, 'audit': audit, 'status': 'complete'}
        invalid = [role for role in ['train', 'calibration'] if split[role].target.nunique() != 2]
        if invalid or split['evaluation'].empty or split['evaluation'].target.sum() == 0:
            fold.update(status='skipped', reason=f'Training/calibration lacks both classes: {invalid}' if invalid else 'No evaluable positives')
            folds.append(fold)
            print(f'{year}: {fold["reason"]}', flush=True)
            continue
        directory = output/str(year)
        directory.mkdir()
        X = {role: g[FEATURE_COLUMNS].to_numpy(dtype=np.float32) for role, g in split.items()}
        y = {role: g.target.to_numpy(dtype=np.int8) for role, g in split.items()}
        evaluation = split['evaluation']
        predictions = evaluation[METADATA].copy()
        thresholds = {}
        # Reference: frozen models on frozen labels, copied from the frozen annual predictions.
        frozen_predictions = pd.read_parquet(ROOT/evidence['frozen_predictions']/str(year)/'predictions.parquet',
                                             columns=['harp', 'forecast_time', 'target', 'baseline'])
        frozen_bundle = joblib.load(ROOT/evidence['frozen_walk_forward']/str(year)/'models.joblib')
        thresholds['frozen_models'] = {'recall_0.95': frozen_bundle['thresholds']['ensemble'],
                                       'recall_0.90': watch[str(year)]['0.9']}
        for point, threshold in thresholds['frozen_models'].items():
            rows.append(score(year, 'frozen_models_old_labels', point, threshold, frozen_predictions,
                              frozen_predictions.baseline, recipes['bootstrap']))
        # Label effect alone: frozen models and thresholds on the relabelled evaluation windows.
        predictions['frozen_models'] = ensemble(frozen_bundle['models'], frozen_bundle['calibrators'],
                                                frozen_bundle['ensemble'], X['evaluation'])
        for point, threshold in thresholds['frozen_models'].items():
            rows.append(score(year, 'frozen_models_new_labels', point, threshold, evaluation,
                              predictions.frozen_models, recipes['bootstrap']))
        # Label and model effect: frozen recipes refitted on the relabelled roles.
        models = candidate_models(recipes)
        calibrators, calibrated = {}, {}
        for name, model in models.items():
            model.fit(X['train'], y['train'])
            raw = model.predict_proba(X['calibration'])[:, 1]
            calibrators[name] = SigmoidCalibration().fit(raw, y['calibration'])
            calibrated[name] = calibrators[name].transform(raw)
        weights = recipes['ensemble']
        calibration_probability = weights['logistic_weight']*calibrated['logistic']+weights['xgboost_weight']*calibrated['xgboost']
        thresholds['relabelled_models'] = {point: recall_threshold(y['calibration'], calibration_probability, r)
                                           for point, r in POINTS.items()}
        joblib.dump({'models': models, 'calibrators': calibrators, 'thresholds': thresholds['relabelled_models'],
                     'features': FEATURE_COLUMNS, 'ensemble': weights}, directory/'models.joblib')
        predictions['relabelled_models'] = ensemble(models, calibrators, weights, X['evaluation'])
        for point, threshold in thresholds['relabelled_models'].items():
            rows.append(score(year, 'relabelled_models', point, threshold, evaluation,
                              predictions.relabelled_models, recipes['bootstrap']))
        (directory/'thresholds.json').write_text(json.dumps(thresholds, indent=2)+'\n')
        predictions.to_parquet(directory/'predictions.parquet', index=False)
        folds.append(fold)
        last = [r for r in rows if r['year'] == year and r['operating_point'] == 'recall_0.90']
        print(f'{year}: ' + ', '.join(f'{r["arm"]} precision={r["precision"]:.4f}' for r in last), flush=True)
        del X, y, models, calibrators, split, predictions, frozen_bundle
        gc.collect()
    metrics = pd.DataFrame(rows)
    metrics.to_csv(output/'metrics.csv', index=False)
    at = metrics[metrics.operating_point.eq('recall_0.90')].set_index(['year', 'arm'])

    def value(year, arm, column):
        if (year, arm) not in at.index or pd.isna(at.loc[(year, arm), column]):
            return None
        return float(at.loc[(year, arm), column])

    r1 = all(value(y, 'relabelled_models', 'precision') is not None and value(y, 'frozen_models_old_labels', 'precision') is not None
             and value(y, 'relabelled_models', 'precision') > value(y, 'frozen_models_old_labels', 'precision')
             and value(y, 'relabelled_models', 'precision_lower') > value(y, 'frozen_models_old_labels', 'precision')
             for y in [2022, 2023])
    with_positives = sorted(set(metrics[metrics.positives.gt(0)].year))
    accuracy_years = {arm: [int(y) for y in with_positives if value(y, arm, 'precision') is not None
                            and value(y, arm, 'accuracy') >= value(y, arm, 'always_negative_accuracy')]
                      for arm in ['frozen_models_old_labels', 'frozen_models_new_labels', 'relabelled_models']}
    r3 = {str(y): ('relabelled_models' if (value(y, 'relabelled_models', 'precision') or 0) >= (value(y, 'frozen_models_new_labels', 'precision') or 0)
                   else 'frozen_models_new_labels') for y in [2022, 2023] if value(y, 'relabelled_models', 'precision') is not None}
    reading = {'R1_labels_explain_cycle25': bool(r1), 'R2_accuracy_goal': accuracy_years, 'R3_label_versus_model': r3,
               'R4_no_gain': not bool(r1)}
    result = {'protocol_sha256': sha256(config_path), 'source_report_sha256': sha256(source/'report.json'),
              'folds': folds, 'metrics': rows, 'reading': reading, 'reserved_test_accessed': False,
              'model_promoted': False, 'dashboard_threshold_changed': False,
              'code_hashes': {name: sha256(ROOT/name) for name in [
                  'scripts/run_relabel_walk_forward.py', 'helio24/relabel.py', 'helio24/walk_forward.py',
                  'helio24/v2_training.py', 'helio24/calibration.py']},
              'artifact_hashes': {str(p.relative_to(output)): sha256(p) for p in sorted(output.rglob('*')) if p.is_file()}}
    (output/'report.json').write_text(json.dumps(result, indent=2)+'\n')
    pd.set_option('display.width', 250)
    print(metrics[['year', 'arm', 'operating_point', 'windows', 'positives', 'precision', 'recall', 'accuracy',
                   'always_negative_accuracy', 'average_precision']].round(4).to_string(index=False))
    print(json.dumps(reading))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=ROOT/'config/relabel-v1.json')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    run(args.config.resolve(), args.output.resolve())
