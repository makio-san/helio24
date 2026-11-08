"""Evaluate the frozen precision context protocol (config/precision-context-v1.json)."""
import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from scipy.special import logit
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from helio24.calibration import recall_threshold
from helio24.modeling import metrics
from helio24.v2_training import load_development
from helio24.walk_forward import annual_fold
from scripts.audit_alarm_persistence import acceptance, evaluate, paired_bootstrap, sha
from scripts.audit_threshold_selection_baseline import ensemble_probability, identity_check

KEY = ['harp', 'forecast_time']
CONTEXT = ['logit_p', 'age_log_hours', 'past24_max_logit', 'past24_mean_logit', 'past72_max_logit',
           'past72_mean_logit', 'past72_hours_above_control', 'slope6', 'coverage24', 'coverage72',
           'missing_fraction']
RECAL = ['logit_p', 'missing_fraction']
FEATURES = {'recal': RECAL, 'context': CONTEXT}
FOLDS = 5
TARGET_PRECISION = 0.30


def context_features(frame, probability, control_threshold):
    """Causal per-HARP context: only windows of the same HARP strictly before the current one."""
    data = frame[['harp', 'forecast_time', 'missing_fraction']].copy()
    data['forecast_time'] = pd.to_datetime(data.forecast_time, utc=True)
    data['logit_p'] = logit(np.clip(np.asarray(probability, dtype=float), 1e-9, 1-1e-9))
    data['above'] = (np.asarray(probability, dtype=float) >= control_threshold).astype(float)
    data = data.sort_values(['harp', 'forecast_time'])
    if data.duplicated(['harp', 'forecast_time']).any():
        raise ValueError('Duplicate forecast key')
    parts = []
    for _, group in data.groupby('harp', sort=False):
        series = group.set_index('forecast_time')
        logits, above = series.logit_p, series.above
        out = pd.DataFrame(index=group.index)
        out['logit_p'] = logits.to_numpy()
        hours = (series.index-series.index.min()).total_seconds()/3600
        out['age_log_hours'] = np.log1p(hours)
        for window in ['24h', '72h']:
            past = logits.rolling(window, closed='left')
            name = f'past{window[:-1]}'
            out[f'{name}_max_logit'] = past.max().fillna(logits).to_numpy()
            out[f'{name}_mean_logit'] = past.mean().fillna(logits).to_numpy()
            out[f'coverage{window[:-1]}'] = past.count().fillna(0).to_numpy()
        out['past72_hours_above_control'] = above.rolling('72h', closed='left').sum().fillna(0).to_numpy()
        out['slope6'] = (logits-logits.rolling('6h', closed='left').mean()).fillna(0).to_numpy()
        out['missing_fraction'] = series.missing_fraction.to_numpy()
        parts.append(out)
    features = pd.concat(parts).loc[frame.index, CONTEXT]
    if features.isna().any().any():
        raise ValueError('Context features must be complete')
    return features


def stage_two_model():
    return make_pipeline(StandardScaler(), LogisticRegression(C=1.0, solver='lbfgs', max_iter=2000,
                                                              class_weight=None, random_state=24))


def harp_folds(harps, folds=FOLDS):
    """Deterministic HARP-group fold: rank of the HARP id among sorted unique HARPs modulo folds."""
    order = {harp: rank for rank, harp in enumerate(sorted(set(harps)))}
    return np.array([order[h] % folds for h in harps])


def cross_fit(features, target, harps):
    """Cross-fitted probability for every row plus the model fitted on all rows."""
    fold = harp_folds(harps)
    out = np.empty(len(features))
    for k in range(FOLDS):
        held = fold == k
        model = stage_two_model().fit(features[~held], target[~held])
        out[held] = model.predict_proba(features[held])[:, 1]
    full = stage_two_model().fit(features, target)
    return out, full


def fp_allowed(tp, target=TARGET_PRECISION):
    """Largest false-alarm count with precision >= target at the given true positives."""
    return int(np.floor(tp*(1-target)/target+1e-9))


def run(source, expected, config_path, output):
    if output.exists():
        raise FileExistsError(output)
    config = json.loads(config_path.read_text())
    evidence = config['evidence']
    if sha(source/'report.json') != expected or expected != evidence['predictions_report_sha256']:
        raise ValueError('Final experiment manifest changed')
    report = json.loads((source/'report.json').read_text())
    walk_dir = Path(evidence['baseline_artifact'])
    if sha(walk_dir/'report.json') != evidence['baseline_report_sha256']:
        raise ValueError('Baseline walk-forward report changed')
    walk_report = json.loads((walk_dir/'report.json').read_text())
    original, _ = load_development(Path(evidence['frozen_shards_report']).parent,
                                   evidence['frozen_shards_report_sha256'])
    table = pd.concat(original.values(), ignore_index=True)
    del original
    output.mkdir(parents=True)
    # Phase 1: stage-one inference, context features, stage-two fits and thresholds from the calibration year.
    gate, thresholds, coefficients, prepared = [], {}, {}, {}
    for year in config['years']:
        rel = f'{year}/thresholds.json'
        if sha(source/rel) != report['artifact_hashes'][rel]:
            raise ValueError(f'Changed annual evidence: {rel}')
        control_threshold = json.loads((source/rel).read_text())['baseline']
        models_path = walk_dir/str(year)/'models.joblib'
        if sha(models_path) != walk_report['artifact_hashes'][f'{year}/models.joblib']:
            raise ValueError(f'Changed stage-one model: {year}')
        stored = joblib.load(models_path)  # trusted local frozen experiment artifact
        groups, _ = annual_fold(table, year)
        calibration = groups['calibration'].reset_index(drop=True)
        evaluation = groups['evaluation'].drop(columns=['target', 'label_status']).reset_index(drop=True)
        p_cal = ensemble_probability(stored, calibration)
        p_eval = ensemble_probability(stored, evaluation)
        y_cal = calibration.target.to_numpy()
        reproduced = recall_threshold(y_cal, p_cal, 0.95)
        identity = identity_check(evaluation.assign(probability=p_eval),
                                  pd.read_parquet(source/str(year)/'predictions.parquet', columns=[*KEY, 'baseline']))
        gate.append({'year': year, 'control_threshold_reproduced': bool(np.isclose(reproduced, control_threshold, rtol=1e-12, atol=0)),
                     'identity': identity, 'calibration_positives': int(y_cal.sum()),
                     'calibration_harps': int(calibration.harp.nunique())})
        if not (gate[-1]['control_threshold_reproduced'] and identity['passed']):
            raise ValueError(f'Baseline gate failed in {year}')
        x_cal = context_features(calibration, p_cal, control_threshold)
        x_eval = context_features(evaluation, p_eval, control_threshold)
        chosen = {'control': float(control_threshold)}
        probabilities = {'control': p_eval}
        for candidate, columns in FEATURES.items():
            cross, full = cross_fit(x_cal[columns].to_numpy(), y_cal, calibration.harp.to_numpy())
            chosen[candidate] = recall_threshold(y_cal, cross, 0.95)
            probabilities[candidate] = full.predict_proba(x_eval[columns].to_numpy())[:, 1]
            coefficients[f'{year}/{candidate}'] = dict(zip(columns, map(float, full[-1].coef_[0])),
                                                       intercept=float(full[-1].intercept_[0]))
        thresholds[str(year)] = chosen
        prepared[year] = evaluation[KEY].assign(**probabilities)
        print(f'{year}: thresholds {chosen}', flush=True)
    (output/'gate.json').write_text(json.dumps(gate, indent=2)+'\n')
    (output/'thresholds.json').write_text(json.dumps(thresholds, indent=2)+'\n')
    (output/'coefficients.json').write_text(json.dumps(coefficients, indent=2)+'\n')
    thresholds_sha = sha(output/'thresholds.json')
    # Phase 2: evaluation labels are read only now.
    tolerance = config['acceptance']['per_year_primary']['window_recall_drop_at_most']
    candidates = [c['id'] for c in config['candidates']]
    rows, intervals = [], []
    for year in config['years']:
        for name in ['predictions.parquet', 'finished.json']:
            rel = f'{year}/{name}'
            if sha(source/rel) != report['artifact_hashes'][rel]:
                raise ValueError(f'Changed annual evidence: {rel}')
        labels = pd.read_parquet(source/str(year)/'predictions.parquet',
                                 columns=[*KEY, 'target', 'missing_fraction', 'baseline'])
        frame = labels.merge(prepared[year], on=KEY, how='inner')
        if len(frame) != len(labels) or len(frame) != len(prepared[year]):
            raise ValueError(f'Evaluation keys do not match: {year}')
        if not np.allclose(frame.control, frame.baseline, atol=1e-6):
            raise ValueError(f'Stage-one probabilities differ from the frozen predictions: {year}')
        y = frame.target.to_numpy()
        results = {c: evaluate(frame, c, thresholds[str(year)][c], 1) for c in candidates}
        control, control_harp = results['control']
        for candidate in candidates:
            values, per_harp = results[candidate]
            scores = metrics(y, frame[candidate].to_numpy(), thresholds[str(year)][candidate])
            row = dict(year=year, candidate=candidate, **values,
                       average_precision=scores['average_precision'], brier=scores['brier'],
                       log_loss=scores['log_loss'], tss=scores['tss'],
                       fp_allowed_for_target_precision=fp_allowed(values['tp']),
                       fp_excess_over_target=values['fp']-fp_allowed(values['tp']))
            if candidate != 'control':
                flags = acceptance(values, control, tolerance)
                row.update(flags)
                row['primary_met'] = bool(all(flags.values()) and year in config['positive_years'])
                for metric, interval in paired_bootstrap(control_harp, per_harp).items():
                    intervals.append(dict(year=year, candidate=candidate, metric=metric, **interval))
            rows.append(row)
    table = pd.DataFrame(rows)
    summary = []
    for candidate in candidates[1:]:
        gated = table[(table.candidate == candidate) & table.year.isin(config['positive_years'])]
        summary.append(dict(candidate=candidate, years_met=int(gated.primary_met.sum()),
                            required_years=len(config['positive_years']),
                            all_year_primary=bool(gated.primary_met.all() and len(gated) == len(config['positive_years'])),
                            met_years=[int(y) for y in gated.loc[gated.primary_met, 'year']]))
    table.to_csv(output/'results.csv', index=False)
    pd.DataFrame(intervals).to_csv(output/'intervals.csv', index=False)
    pd.DataFrame(summary).to_csv(output/'acceptance.csv', index=False)
    result = {'config_sha256': sha(config_path), 'source_report_sha256': expected,
              'thresholds_sha256': thresholds_sha, 'baseline_gate_passed': True, 'years': config['years'],
              'acceptance': summary, 'stage_two_fits': len(config['years'])*len(FEATURES)*(FOLDS+1),
              'bootstrap': {'draws': 1000, 'seed': 24, 'unit': 'full HARP, paired with control'},
              'reserved_test_accessed': False, 'model_promoted': False,
              'artifact_hashes': {p.name: sha(p) for p in sorted(output.iterdir())}}
    (output/'report.json').write_text(json.dumps(result, indent=2)+'\n')
    return result, table


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--source-sha256', required=True)
    parser.add_argument('--config', type=Path, default=Path('config/precision-context-v1.json'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result, table = run(args.source, args.source_sha256, args.config, args.output)
    print(pd.DataFrame(result['acceptance']).to_string(index=False))
    print(table[['year', 'candidate', 'threshold', 'tp', 'fp', 'recall', 'precision', 'episode_precision',
                 'positive_runs_alarmed', 'fp_excess_over_target']].to_string(index=False))
