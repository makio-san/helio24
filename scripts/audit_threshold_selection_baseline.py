"""Evaluate the frozen baseline selection protocol (config/threshold-selection-v2.json)."""
import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from helio24.calibration import recall_threshold
from helio24.data import FEATURE_COLUMNS
from helio24.v2_training import load_development
from helio24.walk_forward import annual_fold
from scripts.audit_alarm_persistence import acceptance, evaluate, paired_bootstrap, sha
from scripts.audit_threshold_selection import positive_run_maxima, select_thresholds

KEY = ['harp', 'forecast_time']


def ensemble_probability(stored, features):
    """Calibrated ensemble probability of the stored frozen models (inference only)."""
    x = features[FEATURE_COLUMNS].to_numpy(dtype=np.float32)
    parts = {name: stored['calibrators'][name].transform(stored['models'][name].predict_proba(x)[:, 1])
             for name in ['logistic', 'xgboost']}
    weight = stored['ensemble']['logistic_weight']
    return weight*parts['logistic']+(1-weight)*parts['xgboost']


def identity_check(evaluation, predictions, tolerance=1e-6):
    """Label-free check that recomputed probabilities equal the frozen predictions column."""
    left = evaluation[[*KEY, 'probability']].assign(forecast_time=lambda d: pd.to_datetime(d.forecast_time, utc=True))
    right = predictions[[*KEY, 'baseline']].assign(forecast_time=lambda d: pd.to_datetime(d.forecast_time, utc=True))
    if left.duplicated(KEY).any() or right.duplicated(KEY).any():
        return {'passed': False, 'reason': 'Duplicate key', 'rows_recomputed': len(left), 'rows_frozen': len(right)}
    merged = left.merge(right, on=KEY, how='outer', indicator=True)
    both = merged[merged._merge.eq('both')]
    same_keys = bool(merged._merge.eq('both').all())
    difference = float((both.probability-both.baseline).abs().max()) if len(both) else float('inf')
    return {'passed': bool(same_keys and difference <= tolerance), 'same_keys': same_keys,
            'rows_recomputed': len(left), 'rows_frozen': len(right), 'rows_matched': len(both),
            'max_abs_difference': difference, 'tolerance': tolerance}


def year_gate(config, year, groups, source, walk_dir, walk_report, stored_thresholds):
    """G2 to G4 for one year. Evaluation labels are not used."""
    result = {'year': year, 'G2': {'passed': False}, 'G3': {'passed': False}, 'G4': {'passed': False}}
    inputs = None
    try:
        models_path = walk_dir/str(year)/'models.joblib'
        expected = walk_report['artifact_hashes'][f'{year}/models.joblib']
        actual = sha(models_path)
        result['G2'] = {'passed': actual == expected, 'expected': expected, 'actual': actual}
        if not result['G2']['passed']:
            return result, inputs
        stored = joblib.load(models_path)  # trusted local frozen experiment artifact
        calibration = groups['calibration']
        probability = ensemble_probability(stored, calibration)
        threshold = recall_threshold(calibration.target.to_numpy(), probability, config['control']['target'])
        reference = stored_thresholds['baseline']
        result['G3'] = {'passed': bool(np.isclose(threshold, reference, rtol=1e-12, atol=0)),
                        'recomputed': float(threshold), 'stored': float(reference),
                        'walk_forward_stored_ensemble': float(stored['thresholds']['ensemble'])}
        evaluation = groups['evaluation'].assign(probability=ensemble_probability(stored, groups['evaluation']))
        predictions = pd.read_parquet(source/str(year)/'predictions.parquet', columns=[*KEY, 'baseline'])
        result['G4'] = identity_check(evaluation, predictions)
        if result['G3']['passed'] and result['G4']['passed']:
            inputs = {'probability': probability}
    except Exception as error:  # a failed gate must be reported, never skipped
        failed = next(name for name in ['G2', 'G3', 'G4'] if not result[name]['passed'])
        result[failed] = {'passed': False, 'error': f'{type(error).__name__}: {error}'}
    return result, inputs


def run(source, expected, config_path, output):
    if output.exists():
        raise FileExistsError(output)
    config = json.loads(config_path.read_text())
    evidence = config['evidence']
    if sha(source/'report.json') != expected or expected != evidence['predictions_report_sha256']:
        raise ValueError('Final experiment manifest changed')
    report = json.loads((source/'report.json').read_text())
    walk_dir = Path(evidence['baseline_artifact'])
    output.mkdir(parents=True)
    gate = {'G1': {'passed': False}, 'walk_forward_report': {'passed': False}, 'years': []}
    groups_by_year, stored_by_year = {}, {}
    try:
        gate['walk_forward_report'] = {'passed': sha(walk_dir/'report.json') == evidence['baseline_report_sha256']}
        walk_report = json.loads((walk_dir/'report.json').read_text())
        original, shard_report = load_development(Path(evidence['frozen_shards_report']).parent,
                                                  evidence['frozen_shards_report_sha256'])
        table = pd.concat(original.values(), ignore_index=True)
        gate['G1'] = {'passed': len(shard_report['shards']) == evidence['shard_count'],
                      'shards': len(shard_report['shards'])}
    except Exception as error:
        gate['G1'] = {'passed': False, 'error': f'{type(error).__name__}: {error}'}
    prerequisites = gate['G1']['passed'] and gate['walk_forward_report']['passed']
    inputs = {}
    for year in config['years']:
        if not prerequisites:
            break
        rel = f'{year}/thresholds.json'
        if sha(source/rel) != report['artifact_hashes'][rel]:
            raise ValueError(f'Changed annual evidence: {rel}')
        stored_thresholds = json.loads((source/rel).read_text())
        groups, _ = annual_fold(table, year)
        year_result, year_inputs = year_gate(config, year, groups, source, walk_dir, walk_report, stored_thresholds)
        gate['years'].append(year_result)
        if year_inputs is not None:
            inputs[year] = {**year_inputs, 'calibration': groups['calibration'][[*KEY, 'target']]}
    gate['evaluable'] = bool(prerequisites and len(gate['years']) == len(config['years'])
                             and all(all(y[s]['passed'] for s in ['G2', 'G3', 'G4']) for y in gate['years']))
    (output/'gate.json').write_text(json.dumps(gate, indent=2)+'\n')
    result = {'config_sha256': sha(config_path), 'source_report_sha256': expected, 'baseline_gate': gate,
              'years': config['years'], 'reserved_test_accessed': False, 'model_promoted': False}
    if not gate['evaluable']:
        result['acceptance'] = []
        result['artifact_hashes'] = {p.name: sha(p) for p in sorted(output.iterdir())}
        (output/'report.json').write_text(json.dumps(result, indent=2)+'\n')
        return result, None
    # Phase 1: thresholds from calibration windows only, written to disk before any evaluation label is read.
    rules = [config['control']]+config['candidates']
    chosen, stability = {}, []
    for year in config['years']:
        calibration, probability = inputs[year]['calibration'], inputs[year]['probability']
        selected = select_thresholds(calibration, probability, rules)
        chosen[str(year)] = selected
        maxima = positive_run_maxima(calibration, probability)
        target = calibration.target.to_numpy()
        for rule_id, threshold in selected.items():
            stability.append(dict(year=year, rule=rule_id, threshold=threshold,
                ratio_to_control=threshold/selected['control_w95'],
                calibration_positive_windows=int(target.sum()), calibration_positive_runs=len(maxima),
                calibration_recall=float((probability[target == 1] >= threshold).mean()),
                calibration_run_recall=float((maxima >= threshold).mean())))
    (output/'selected_thresholds.json').write_text(json.dumps(chosen, indent=2)+'\n')
    thresholds_sha = sha(output/'selected_thresholds.json')
    # Phase 2: evaluation windows and labels are read only now.
    stability = pd.DataFrame(stability)
    tolerance = config['acceptance']['per_year_primary']['window_recall_drop_at_most']
    rows, intervals = [], []
    for year in config['years']:
        for name in ['predictions.parquet', 'finished.json']:
            rel = f'{year}/{name}'
            if sha(source/rel) != report['artifact_hashes'][rel]:
                raise ValueError(f'Changed annual evidence: {rel}')
        frame = pd.read_parquet(source/str(year)/'predictions.parquet')
        selected = chosen[str(year)]
        results = {rule['id']: evaluate(frame, 'baseline', selected[rule['id']], 1) for rule in rules}
        control, control_harp = results['control_w95']
        for rule in rules:
            values, per_harp = results[rule['id']]
            row = dict(year=year, arm='baseline', rule=rule['id'], **values)
            if rule['id'] != 'control_w95':
                flags = acceptance(values, control, tolerance)
                row.update(flags)
                row['primary_met'] = bool(all(flags.values()) and year in config['positive_years'])
                for metric, interval in paired_bootstrap(control_harp, per_harp).items():
                    intervals.append(dict(year=year, arm='baseline', rule=rule['id'], metric=metric, **interval))
            rows.append(row)
    table = pd.DataFrame(rows).merge(
        stability[['year', 'rule', 'ratio_to_control', 'calibration_positive_windows',
                   'calibration_positive_runs', 'calibration_recall', 'calibration_run_recall']],
        on=['year', 'rule'])
    table['evaluation_recall_minus_calibration_recall'] = table.recall-table.calibration_recall
    summary = []
    for rule, group in table[table.rule != 'control_w95'].groupby('rule', sort=False):
        gated = group[group.year.isin(config['positive_years'])]
        summary.append(dict(arm='baseline', rule=rule, years_met=int(gated.primary_met.sum()),
            required_years=len(config['positive_years']),
            all_year_primary=bool(gated.primary_met.all() and len(gated) == len(config['positive_years']))))
    table.to_csv(output/'selection.csv', index=False)
    pd.DataFrame(intervals).to_csv(output/'intervals.csv', index=False)
    pd.DataFrame(summary).to_csv(output/'acceptance.csv', index=False)
    result.update({'selected_thresholds_sha256': thresholds_sha, 'acceptance': summary,
        'bootstrap': {'draws': 1000, 'seed': 24, 'unit': 'full HARP, paired with control'},
        'artifact_hashes': {p.name: sha(p) for p in sorted(output.iterdir())}})
    (output/'report.json').write_text(json.dumps(result, indent=2)+'\n')
    return result, table


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--source-sha256', required=True)
    parser.add_argument('--config', type=Path, default=Path('config/threshold-selection-v2.json'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result, _ = run(args.source, args.source_sha256, args.config, args.output)
    print(json.dumps(result['baseline_gate'], indent=1, default=str))
    print(pd.DataFrame(result['acceptance']).to_string(index=False))
