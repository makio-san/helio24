"""Bounded calibration-selected signed-log experiment; reserved test stays closed."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from helio24.calibration import SigmoidCalibration, recall_threshold, cluster_intervals
from helio24.data import FEATURE_COLUMNS, ROOT
from helio24.full_data import sha256
from helio24.metric_summary import enrich
from helio24.modeling import metrics
from helio24.signed_log import SignedLogScaler
from helio24.magnetic_interactions import MagneticInteractions, RelativeEvolution
from helio24.v2_training import load_development, METADATA


def run(args):
    protocol = json.loads(args.protocol.read_text())
    if args.output.exists():
        raise ValueError('Preserve existing output')
    if sha256(args.incumbent / 'report.json') != protocol['incumbent_report_sha256']:
        raise ValueError('Incumbent report changed')
    original = json.loads((args.incumbent / 'report.json').read_text())
    for name in ['logistic.joblib', 'xgboost.joblib']:
        if sha256(args.incumbent / name) != original['artifact_hashes'][name]:
            raise ValueError('Incumbent model changed')
    groups, _ = load_development(args.materialized, protocol['materialization_report_sha256'])
    args.output.mkdir(parents=True)
    X = {k: v[FEATURE_COLUMNS].to_numpy(dtype=np.float32) for k, v in groups.items()}
    y = {k: v.target.to_numpy(dtype=np.int8) for k, v in groups.items()}
    incumbent = {}
    for role in ['calibration', 'validation']:
        p = []
        for name in ['logistic', 'xgboost']:
            artifact = joblib.load(args.incumbent / f'{name}.joblib')
            p.append(artifact['calibrator'].transform(artifact['model'].predict_proba(X[role])[:, 1]))
        incumbent[role] = .45*p[0]+.55*p[1]
    def score(role, probability):
        threshold = recall_threshold(y[role], probability, protocol['required_recall'])
        return enrich(metrics(y[role], probability, threshold))
    candidates = [{'candidate': 'incumbent', **score('calibration', incumbent['calibration'])}]
    models, calibrators, probabilities = {}, {}, {}
    specifications = [{'id': f'signed_log_C{C:g}', 'C': C}
                      for C in protocol['regularization_C']] + protocol.get('hist_candidates', []) + protocol.get('feature_candidates', [])
    for specification in specifications:
        key = specification['id']
        if specification.get('kind') == 'weighted_logistic':
            steps = [SimpleImputer(strategy='median', add_indicator=True)]
            if specification.get('signed_log'):
                steps.append(SignedLogScaler())
            weight = specification['positive_weight']
            class_weight = 'balanced' if weight == 'balanced' else {0: 1., 1: float(weight)}
            model = make_pipeline(*steps, StandardScaler(),
                                  LogisticRegression(C=1., class_weight=class_weight,
                                                     max_iter=2000, random_state=24))
        elif specification.get('kind') == 'interactions':
            model = make_pipeline(SimpleImputer(strategy='median', add_indicator=True),
                                  SignedLogScaler(), StandardScaler(), MagneticInteractions(),
                                  StandardScaler(), LogisticRegression(C=specification['C'],
                                                                      max_iter=2000, random_state=24))
        elif specification.get('kind') == 'relative_xgb':
            from xgboost import XGBClassifier
            model = make_pipeline(RelativeEvolution(),
                                  SimpleImputer(strategy='median', add_indicator=True),
                                  XGBClassifier(**specification['parameters']))
        elif 'C' in specification:
            model = make_pipeline(SimpleImputer(strategy='median', add_indicator=True),
                                  SignedLogScaler(), StandardScaler(),
                                  LogisticRegression(C=specification['C'], max_iter=2000, random_state=24))
        else:
            model = HistGradientBoostingClassifier(**specification['parameters'],
                                                   early_stopping=False, random_state=24)
        mask = np.ones(len(y['train']), dtype=bool)
        if 'train_start' in specification:
            mask = (groups['train'].forecast_time >= pd.Timestamp(specification['train_start'])).to_numpy()
        model.fit(X['train'][mask], y['train'][mask])
        raw = model.predict_proba(X['calibration'])[:, 1]
        calibrator = SigmoidCalibration().fit(raw, y['calibration'])
        p = calibrator.transform(raw)
        models[key], calibrators[key] = model, calibrator
        for weight in protocol['new_model_weights']:
            name = f'{key}_w{weight:g}'
            blend = weight*p+(1-weight)*incumbent['calibration']
            candidates.append({'candidate': name, 'model': key, 'weight': weight,
                               **score('calibration', blend)})
        print(f'{key}: trained; calibration search complete', flush=True)
    winner = sorted(candidates, key=lambda r: (-r['precision'], -r['average_precision'], r['candidate']))[0]
    (args.output / 'calibration_selection.json').write_text(json.dumps(winner, indent=2)+'\n')
    pd.DataFrame(candidates).to_csv(args.output / 'calibration_candidates.csv', index=False)
    # Validation predictions for the selected new candidate only, after selection is recorded.
    if winner['candidate'] == 'incumbent':
        selected = incumbent['validation']
    else:
        key, weight = winner['model'], winner['weight']
        selected = weight*calibrators[key].transform(models[key].predict_proba(X['validation'])[:, 1])+(1-weight)*incumbent['validation']
        joblib.dump({'model': models[key], 'calibrator': calibrators[key],
                     'new_model_weight': weight, 'incumbent': str(args.incumbent)},
                    args.output / 'candidate.joblib')
    results, intervals = {}, {}
    for name, p in [('incumbent', incumbent['validation']), ('selected', selected)]:
        results[name] = score('validation', p)
        intervals[name] = cluster_intervals(y['validation'], p, groups['validation'].harp,
                                           results[name]['threshold'], **protocol['bootstrap'])
        probabilities[name] = p
    old, new = results['incumbent'], results['selected']
    promote = (new['recall'] >= protocol['required_recall'] and new['precision'] > old['precision']
               and new['average_precision'] >= old['average_precision']
               and new['brier'] <= old['brier'] and new['log_loss'] <= old['log_loss'])
    prediction = groups['validation'][METADATA].copy()
    for name, p in probabilities.items():
        prediction[name] = p
    prediction.to_parquet(args.output / 'validation_predictions.parquet', index=False)
    report = {'completed_utc': datetime.now(timezone.utc).isoformat(), 'winner': winner,
              'metrics': results, 'conditional_cluster_intervals': intervals,
              'promote': bool(promote), 'reserved_test_accessed': False,
              'protocol': protocol, 'protocol_sha256': sha256(args.protocol),
              'code_hashes': {name: sha256(ROOT / name) for name in
                             ['scripts/run_precision_log.py', 'helio24/signed_log.py',
                              'helio24/v2_training.py', 'helio24/calibration.py',
                              'helio24/magnetic_interactions.py']}}
    (args.output / 'report.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--protocol', type=Path, default=ROOT / 'config/precision-log-v1.json')
    parser.add_argument('--materialized', type=Path, default=ROOT / 'artifacts/v2_development_features_20261025_r2')
    parser.add_argument('--incumbent', type=Path, default=ROOT / 'artifacts/experiment5_v2_development_20261026_r2')
    parser.add_argument('--output', type=Path, required=True)
    run(parser.parse_args())
