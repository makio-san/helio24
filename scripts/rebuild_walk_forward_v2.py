"""Rebuild the development pipeline from the relabelled table (config/walk-forward-v2.json)."""
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

from helio24.calibration import SigmoidCalibration, recall_threshold
from helio24.data import FEATURE_COLUMNS, ROOT
from helio24.full_data import sha256
from helio24.two_tier import precision_threshold
from helio24.v2_training import METADATA, candidate_models, load_development
from helio24.walk_forward import annual_fold
from scripts.audit_two_tier import point

TIERS = ['watch', 'alert', 'comparison_recall_0.95']
REFERENCE_TIER = {'watch': 'watch', 'alert': 'alert_0.5'}
COUNTS = ['tp', 'fp', 'fn', 'tn', 'positive_runs', 'missed_positive_runs']


def verify_inputs(protocol):
    pairs = [(ROOT/protocol['source']/'report.json', protocol['source_sha256']),
             (ROOT/protocol['must_reproduce']['relabelled_walk_forward']/'report.json',
              protocol['must_reproduce']['relabelled_walk_forward_report_sha256']),
             (ROOT/protocol['must_reproduce']['two_tier_relabelled']/'report.json',
              protocol['must_reproduce']['two_tier_relabelled_report_sha256']),
             (ROOT/protocol['frozen_label_reference']['walk_forward']/'report.json',
              protocol['frozen_label_reference']['walk_forward_report_sha256']),
             (ROOT/protocol['frozen_label_reference']['two_tier']/'report.json',
              protocol['frozen_label_reference']['two_tier_report_sha256'])]
    for path, expected in pairs:
        if sha256(path) != expected:
            raise ValueError(f'Frozen input changed: {path}')
    recipes = json.loads((ROOT/protocol['recipes']).read_text())
    operating_point = json.loads((ROOT/protocol['operating_point']).read_text())
    if not operating_point['status'].startswith('adopted'):
        raise ValueError('The operating point must be adopted before the pipeline is rebuilt')
    if any(year >= 2024 for year in protocol['evaluation_years']):
        raise ValueError('Reserved test forbidden')
    return recipes


def select_thresholds(protocol, y_cal, p_cal):
    tiers = protocol['tiers']
    out = {'watch': {'threshold': recall_threshold(y_cal, p_cal, tiers['watch']['recall_target'])},
           'comparison_recall_0.95': {'threshold': recall_threshold(y_cal, p_cal, tiers['comparison_recall_0.95']['recall_target'])}}
    threshold, recall, precision, fallback = precision_threshold(
        y_cal, p_cal, tiers['alert']['precision_target'], tiers['alert']['recall_floor'])
    out['alert'] = dict(threshold=threshold, calibration_recall=recall, calibration_precision=precision, fallback=fallback)
    return out


def reproduction_checks(year, protocol, thresholds, probability, evaluation, rows):
    """Compare the rebuilt year with the stored relabelled walk-forward and two-tier artifacts."""
    must = protocol['must_reproduce']
    stored = pd.read_parquet(ROOT/must['relabelled_walk_forward']/str(year)/'predictions.parquet',
                             columns=['harp', 'forecast_time', must['arm']])
    merged = evaluation[['harp', 'forecast_time']].assign(rebuilt=probability).merge(stored, on=['harp', 'forecast_time'], how='outer')
    stored_thresholds = json.loads((ROOT/must['relabelled_walk_forward']/str(year)/'thresholds.json').read_text())[must['arm']]
    two_tier = json.loads((ROOT/must['two_tier_relabelled']/'thresholds.json').read_text())[str(year)]['alert_0.5']
    results = pd.read_csv(ROOT/must['two_tier_relabelled']/'results.csv').set_index(['year', 'tier'])
    checks = {
        'windows_identical': len(merged) == len(evaluation) == len(stored) and not merged.isna().any().any(),
        'probability_identical': bool(len(merged) == len(stored) and np.array_equal(merged.rebuilt.to_numpy(), merged[must['arm']].to_numpy())),
        'probability_max_abs_difference': float(np.nanmax(np.abs(merged.rebuilt.to_numpy()-merged[must['arm']].to_numpy()))),
        'threshold_0.95_identical': thresholds['comparison_recall_0.95']['threshold'] == stored_thresholds['recall_0.95'],
        'threshold_0.90_identical': thresholds['watch']['threshold'] == stored_thresholds['recall_0.90'],
        'alert_threshold_identical': all(thresholds['alert'][k] == two_tier[k] for k in ['threshold', 'calibration_recall', 'calibration_precision', 'fallback']),
    }
    for tier, reference in REFERENCE_TIER.items():
        row = next(r for r in rows if r['tier'] == tier)
        checks[f'{tier}_counts_identical'] = all(int(row[c]) == int(results.loc[(year, reference), c]) for c in COUNTS)
    checks['reproduced'] = all(v for k, v in checks.items() if k.endswith('identical'))
    return checks


def reference_rows(protocol, year):
    """Frozen-label reference rows for the same year and tiers."""
    ref = protocol['frozen_label_reference']
    out = []
    two_tier = pd.read_csv(ROOT/ref['two_tier']/'results.csv')
    for tier, reference in REFERENCE_TIER.items():
        hit = two_tier[two_tier.year.eq(year) & two_tier.tier.eq(reference)]
        if len(hit):
            r = hit.iloc[0]
            out.append(dict(year=year, tier=tier, labels='frozen', threshold=r.threshold, fallback=bool(r.fallback),
                            tp=int(r.tp), fp=int(r.fp), fn=int(r.fn), tn=int(r.tn), recall=r.recall, precision=r.precision,
                            precision_lower=r.precision_lower, precision_upper=r.precision_upper, accuracy=r.accuracy,
                            always_negative_accuracy=r.always_negative_accuracy, positive_runs=int(r.positive_runs),
                            missed_positive_runs=int(r.missed_positive_runs)))
    walk = pd.read_csv(ROOT/ref['walk_forward']/'metrics.csv')
    hit = walk[walk.year.eq(year) & walk.model.eq('ensemble')]
    if len(hit):
        r = hit.iloc[0]
        out.append(dict(year=year, tier='comparison_recall_0.95', labels='frozen', threshold=r.threshold, fallback=False,
                        tp=int(r.tp), fp=int(r.fp), fn=int(r.fn), tn=int(r.tn), recall=r.recall, precision=r.precision,
                        accuracy=r.accuracy, always_negative_accuracy=r.always_quiet_accuracy,
                        average_precision=r.average_precision))
    return out


def run(protocol_path, output):
    if output.exists():
        raise ValueError('Preserve existing experiment')
    protocol = json.loads(protocol_path.read_text())
    recipes = verify_inputs(protocol)
    groups, _ = load_development(ROOT/protocol['source'], protocol['source_sha256'])
    table = pd.concat(groups.values(), ignore_index=True)
    del groups
    output.mkdir(parents=True)
    rows, folds, reproduction = [], [], []
    for year in protocol['evaluation_years']:
        split, audit = annual_fold(table, year)
        directory = output/str(year)
        directory.mkdir()
        fold = {'year': year, 'audit': audit, 'status': 'complete'}
        invalid = [role for role in ['train', 'calibration'] if split[role].target.nunique() != 2]
        if invalid or split['evaluation'].empty or split['evaluation'].target.sum() == 0:
            fold.update(status='skipped', reason=f'Training/calibration lacks both classes: {invalid}' if invalid else 'No evaluable positives')
            folds.append(fold)
            (directory/'split.json').write_text(json.dumps(fold, indent=2)+'\n')
            print(f'{year}: {fold["reason"]}', flush=True)
            continue
        (directory/'split.json').write_text(json.dumps(fold, indent=2)+'\n')
        X = {role: g[FEATURE_COLUMNS].to_numpy(dtype=np.float32) for role, g in split.items()}
        y = {role: g.target.to_numpy(dtype=np.int8) for role, g in split.items()}
        models = candidate_models(recipes)
        calibrators, calibrated = {}, {}
        for name, model in models.items():
            model.fit(X['train'], y['train'])
            raw = model.predict_proba(X['calibration'])[:, 1]
            calibrators[name] = SigmoidCalibration().fit(raw, y['calibration'])
            calibrated[name] = calibrators[name].transform(raw)
        weights = recipes['ensemble']
        p_cal = weights['logistic_weight']*calibrated['logistic']+weights['xgboost_weight']*calibrated['xgboost']
        thresholds = select_thresholds(protocol, y['calibration'], p_cal)
        # Thresholds are fixed and written before any evaluation label is read.
        (directory/'thresholds.json').write_text(json.dumps(thresholds, indent=2)+'\n')
        joblib.dump({'models': models, 'calibrators': calibrators, 'thresholds': thresholds, 'features': FEATURE_COLUMNS,
                     'ensemble': weights, 'protocol': protocol['id'], 'source': protocol['source']}, directory/'models.joblib')
        evaluation = split['evaluation']
        parts = {name: calibrators[name].transform(model.predict_proba(X['evaluation'])[:, 1]) for name, model in models.items()}
        probability = weights['logistic_weight']*parts['logistic']+weights['xgboost_weight']*parts['xgboost']
        predictions = evaluation[METADATA].copy()
        predictions['logistic'], predictions['xgboost'], predictions['ensemble'] = parts['logistic'], parts['xgboost'], probability
        predictions['baseline'] = float(y['train'].mean())
        frame = evaluation[['harp', 'forecast_time', 'target', 'missing_fraction']].assign(probability=probability)
        year_rows = []
        for tier in TIERS:
            row = point(frame, tier, thresholds[tier], year)
            row.update(labels='relabelled', average_precision=float(average_precision_score(y['evaluation'], probability)))
            year_rows.append(row)
            predictions[f'{tier}_alarm'] = probability >= thresholds[tier]['threshold']
        predictions.to_parquet(directory/'predictions.parquet', index=False)
        checks = reproduction_checks(year, protocol, thresholds, probability, evaluation, year_rows)
        reproduction.append({'year': year, **checks})
        rows.extend(year_rows)
        rows.extend(reference_rows(protocol, year))
        folds.append(fold)
        print(f'{year}: ' + ', '.join(f'{r["tier"]} precision={r["precision"]:.4f} recall={r["recall"]:.4f}' for r in year_rows)
              + f', reproduced={checks["reproduced"]}', flush=True)
        del X, y, models, calibrators, split, predictions, parts
        gc.collect()
    metrics = pd.DataFrame(rows)
    metrics.to_csv(output/'metrics.csv', index=False)
    repro = pd.DataFrame(reproduction)
    repro.to_csv(output/'reproduction.csv', index=False)
    new = metrics[metrics.labels.eq('relabelled') & metrics.tier.eq('alert')]
    meeting = [int(r.year) for r in new.itertuples() if r.precision is not None and r.precision >= 0.5 and not r.fallback]
    reading = {'pipeline_reproduced': bool(len(repro) and repro.reproduced.all()),
               'years_evaluated': [int(y) for y in repro.year],
               'years_meeting_alert_target': meeting,
               'alert_fallback_years': [int(r.year) for r in new.itertuples() if r.fallback]}
    reading['adoption_effective'] = reading['pipeline_reproduced']
    result = {'protocol_sha256': sha256(protocol_path), 'source_report_sha256': sha256(ROOT/protocol['source']/'report.json'),
              'folds': folds, 'reproduction': reproduction, 'reading': reading, 'reserved_test_accessed': False,
              'dashboard_threshold_changed': False,
              'code_hashes': {name: sha256(ROOT/name) for name in [
                  'scripts/rebuild_walk_forward_v2.py', 'scripts/audit_two_tier.py', 'helio24/two_tier.py',
                  'helio24/walk_forward.py', 'helio24/v2_training.py', 'helio24/calibration.py']},
              'artifact_hashes': {str(p.relative_to(output)): sha256(p) for p in sorted(output.rglob('*')) if p.is_file()}}
    (output/'report.json').write_text(json.dumps(result, indent=2)+'\n')
    if not reading['pipeline_reproduced']:
        raise SystemExit('Rebuild did not reproduce the relabelled walk-forward; see reproduction.csv')
    pd.set_option('display.width', 250)
    print(metrics[['year', 'tier', 'labels', 'fallback', 'tp', 'fp', 'recall', 'precision', 'accuracy', 'always_negative_accuracy',
                   'positive_runs', 'missed_positive_runs']].round(4).to_string(index=False))
    print(repro.to_string(index=False))
    print(json.dumps(reading))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--protocol', type=Path, default=ROOT/'config/walk-forward-v2.json')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    run(args.protocol.resolve(), args.output.resolve())
