"""Measure the two-tier operating point on the frozen baseline (config/two-tier-v1.json)."""
import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from helio24.calibration import cluster_intervals, recall_threshold
from helio24.two_tier import precision_threshold
from helio24.v2_training import load_development
from helio24.walk_forward import annual_fold
from scripts.audit_alarm_persistence import evaluate, sha
from scripts.audit_operating_point import recall_for_precision
from scripts.audit_threshold_selection_baseline import ensemble_probability, identity_check

KEY = ['harp', 'forecast_time']


def tier_thresholds(config, calibration, p_cal):
    """Both tiers' thresholds from the calibration year only."""
    y = calibration.target.to_numpy()
    alert = config['tiers']['alert']
    out = {'watch': {'threshold': recall_threshold(y, p_cal, config['tiers']['watch']['recall_target'])}}
    for target in alert['precision_targets']:
        threshold, recall, precision, fallback = precision_threshold(y, p_cal, target, alert['recall_floor'])
        out[f'alert_{target}'] = dict(threshold=threshold, calibration_recall=recall, calibration_precision=precision,
                                      fallback=fallback)
    return out


def point(frame, tier, chosen, year):
    values, _ = evaluate(frame, 'probability', chosen['threshold'], 1)
    n = values['tp']+values['fp']+values['fn']+values['tn']
    interval = cluster_intervals(frame.target.to_numpy(), frame.probability.to_numpy(), frame.harp.to_numpy(),
                                 chosen['threshold'])
    row = dict(year=year, tier=tier, threshold=chosen['threshold'],
               calibration_recall=chosen.get('calibration_recall'), calibration_precision=chosen.get('calibration_precision'),
               fallback=chosen.get('fallback', False))
    for key in ['tp', 'fp', 'fn', 'tn', 'recall', 'precision', 'alarm_windows', 'episodes', 'episode_precision',
                'positive_runs', 'positive_runs_alarmed']:
        row[key] = values[key]
    row.update(missed_positive_runs=values['positive_runs']-values['positive_runs_alarmed'],
               accuracy=(values['tp']+values['tn'])/n, always_negative_accuracy=(values['fp']+values['tn'])/n,
               precision_lower=interval['precision']['lower'], precision_upper=interval['precision']['upper'],
               recall_lower=interval['recall']['lower'], recall_upper=interval['recall']['upper'])
    return row


def run(config_path, output):
    if output.exists():
        raise FileExistsError(output)
    config = json.loads(config_path.read_text())
    evidence = config['evidence']
    source = Path(evidence['predictions'])
    if sha(source/'report.json') != evidence['predictions_report_sha256']:
        raise ValueError('Final experiment manifest changed')
    walk_dir = Path(evidence['baseline_artifact'])
    if sha(walk_dir/'report.json') != evidence['baseline_report_sha256']:
        raise ValueError('Baseline walk-forward report changed')
    if sha(Path(evidence['watch_tier_thresholds'])) != evidence['watch_tier_thresholds_sha256']:
        raise ValueError('Watch tier thresholds changed')
    watch_stored = json.loads(Path(evidence['watch_tier_thresholds']).read_text())
    walk_report = json.loads((walk_dir/'report.json').read_text())
    original, _ = load_development(Path(evidence['frozen_shards_report']).parent, evidence['frozen_shards_report_sha256'])
    table = pd.concat(original.values(), ignore_index=True)
    del original
    output.mkdir(parents=True)
    # Phase 1: thresholds from calibration years only.
    thresholds, prepared = {}, {}
    for year in config['years']:
        models_path = walk_dir/str(year)/'models.joblib'
        if sha(models_path) != walk_report['artifact_hashes'][f'{year}/models.joblib']:
            raise ValueError(f'Changed stage-one model: {year}')
        stored = joblib.load(models_path)  # trusted local frozen experiment artifact
        groups, _ = annual_fold(table, year)
        calibration = groups['calibration']
        evaluation = groups['evaluation'].drop(columns=['target', 'label_status'])
        p_cal = ensemble_probability(stored, calibration)
        p_eval = ensemble_probability(stored, evaluation)
        chosen = tier_thresholds(config, calibration, p_cal)
        if chosen['watch']['threshold'] != watch_stored[str(year)][str(config['tiers']['watch']['recall_target'])]:
            raise ValueError(f'Watch tier threshold not reproduced: {year}')
        identity = identity_check(evaluation.assign(probability=p_eval),
                                  pd.read_parquet(source/str(year)/'predictions.parquet', columns=[*KEY, 'baseline']))
        if not identity['passed']:
            raise ValueError(f'Identity check failed: {year}')
        thresholds[str(year)] = chosen
        prepared[year] = evaluation[KEY].reset_index(drop=True).assign(probability=p_eval)
    (output/'thresholds.json').write_text(json.dumps(thresholds, indent=2)+'\n')
    thresholds_sha = sha(output/'thresholds.json')
    # Phase 2: evaluation labels.
    rows, oracle = [], []
    for year in config['years']:
        labels = pd.read_parquet(source/str(year)/'predictions.parquet', columns=[*KEY, 'target', 'missing_fraction'])
        frame = labels.merge(prepared[year], on=KEY, how='inner')
        if len(frame) != len(labels):
            raise ValueError(f'Evaluation keys do not match: {year}')
        for tier, chosen in thresholds[str(year)].items():
            rows.append(point(frame, tier, chosen, year))
        for target in config['tiers']['alert']['precision_targets']:
            oracle.append(dict(year=year, precision_target=target, oracle_max_recall=recall_for_precision(
                frame.target.to_numpy(), frame.probability.to_numpy(), target)))
    results = pd.DataFrame(rows)
    results.to_csv(output/'results.csv', index=False)
    pd.DataFrame(oracle).to_csv(output/'oracle.csv', index=False)
    primary = results[results.tier == f"alert_{config['tiers']['alert']['primary_precision_target']}"]
    met = primary[(primary.precision >= config['tiers']['alert']['primary_precision_target']) & ~primary.fallback]
    watch = results[results.tier == 'watch']
    result = {'config_sha256': sha(config_path), 'source_report_sha256': evidence['predictions_report_sha256'],
              'thresholds_sha256': thresholds_sha, 'years': config['years'],
              'years_meeting_primary': [int(y) for y in met.year], 'fallback_years_primary': [int(y) for y in primary[primary.fallback].year],
              'watch_tier_identical_to_v2': bool((watch.precision.round(4).to_numpy() == np.array([0.2082, 0.1721, 0.1106, 0.1850, 0.0442, 0.1186])).all()),
              'redefinition_supported': len(met) >= 4,
              'reserved_test_accessed': False, 'model_promoted': False,
              'artifact_hashes': {p.name: sha(p) for p in sorted(output.iterdir())}}
    (output/'report.json').write_text(json.dumps(result, indent=2)+'\n')
    return result, results, pd.DataFrame(oracle)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=Path('config/two-tier-v1.json'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result, results, oracle = run(args.config, args.output)
    pd.set_option('display.width', 250)
    print(results[['year', 'tier', 'fallback', 'calibration_precision', 'calibration_recall', 'tp', 'fp', 'recall', 'precision',
                   'precision_lower', 'precision_upper', 'accuracy', 'always_negative_accuracy', 'episode_precision',
                   'positive_runs', 'missed_positive_runs']].round(4).to_string(index=False))
    print(oracle.round(4).to_string(index=False))
    print(json.dumps({k: v for k, v in result.items() if k != 'artifact_hashes'}, indent=1))
