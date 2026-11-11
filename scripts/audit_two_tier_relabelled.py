"""Measure the frozen two-tier operating point on the relabelled table (config/two-tier-v2.json)."""
import argparse
import json
from pathlib import Path

import joblib
import pandas as pd

from helio24.v2_training import load_development
from helio24.walk_forward import annual_fold
from scripts.audit_alarm_persistence import sha
from scripts.audit_operating_point import recall_for_precision
from scripts.audit_threshold_selection_baseline import ensemble_probability, identity_check
from scripts.audit_two_tier import KEY, point, tier_thresholds


def run(config_path, output):
    if output.exists():
        raise FileExistsError(output)
    config = json.loads(config_path.read_text())
    evidence = config['evidence']
    table_dir = Path(evidence['relabelled_table'])
    walk_dir = Path(evidence['relabelled_walk_forward'])
    frozen_dir = Path(evidence['frozen_two_tier'])
    for path, expected in [(table_dir/'report.json', evidence['relabelled_table_report_sha256']),
                           (walk_dir/'report.json', evidence['relabelled_walk_forward_report_sha256']),
                           (frozen_dir/'report.json', evidence['frozen_two_tier_report_sha256'])]:
        if sha(path) != expected:
            raise ValueError(f'Frozen input changed: {path}')
    walk_report = json.loads((walk_dir/'report.json').read_text())
    original, _ = load_development(table_dir, evidence['relabelled_table_report_sha256'])
    table = pd.concat(original.values(), ignore_index=True)
    del original
    output.mkdir(parents=True)
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
        stored_watch = json.loads((walk_dir/str(year)/'thresholds.json').read_text())['relabelled_models']['recall_0.90']
        if chosen['watch']['threshold'] != stored_watch:
            raise ValueError(f'Watch tier threshold not reproduced: {year}')
        frozen_predictions = pd.read_parquet(walk_dir/str(year)/'predictions.parquet', columns=[*KEY, 'relabelled_models'])
        identity = identity_check(evaluation.assign(probability=p_eval), frozen_predictions.rename(columns={'relabelled_models': 'baseline'}))
        if not identity['passed']:
            raise ValueError(f'Identity check failed: {year}')
        thresholds[str(year)] = chosen
        prepared[year] = evaluation[KEY].reset_index(drop=True).assign(probability=p_eval)
    (output/'thresholds.json').write_text(json.dumps(thresholds, indent=2)+'\n')
    thresholds_sha = sha(output/'thresholds.json')
    rows, oracle = [], []
    for year in config['years']:
        labels = pd.read_parquet(walk_dir/str(year)/'predictions.parquet', columns=[*KEY, 'target', 'missing_fraction'])
        frame = labels.merge(prepared[year], on=KEY, how='inner')
        if len(frame) != len(labels):
            raise ValueError(f'Evaluation keys do not match: {year}')
        for tier, chosen in thresholds[str(year)].items():
            rows.append(point(frame, tier, chosen, year))
        for target in config['tiers']['alert']['precision_targets']:
            oracle.append(dict(year=year, precision_target=target, oracle_max_recall=recall_for_precision(
                frame.target.to_numpy(), frame.probability.to_numpy(), target)))
    results = pd.DataFrame(rows).assign(labels='relabelled')
    frozen = pd.read_csv(frozen_dir/'results.csv').assign(labels='frozen')
    combined = pd.concat([frozen, results], ignore_index=True).sort_values(['year', 'tier', 'labels'])
    results.to_csv(output/'results.csv', index=False)
    combined.to_csv(output/'comparison.csv', index=False)
    pd.DataFrame(oracle).to_csv(output/'oracle.csv', index=False)
    target = config['tiers']['alert']['primary_precision_target']
    primary = results[results.tier == f'alert_{target}']
    met = primary[(primary.precision >= target) & ~primary.fallback]
    result = {'config_sha256': sha(config_path), 'thresholds_sha256': thresholds_sha, 'years': config['years'],
              'years_meeting_primary': [int(y) for y in met.year], 'fallback_years_primary': [int(y) for y in primary[primary.fallback].year],
              'cycle25_now_met': bool({2022, 2023} <= set(int(y) for y in met.year)),
              'watch_tier_reproduced': True, 'redefinition_supported': len(met) >= 4,
              'reserved_test_accessed': False, 'model_promoted': False,
              'artifact_hashes': {p.name: sha(p) for p in sorted(output.iterdir())}}
    (output/'report.json').write_text(json.dumps(result, indent=2)+'\n')
    return result, results, pd.DataFrame(oracle)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=Path('config/two-tier-v2.json'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result, results, oracle = run(args.config, args.output)
    pd.set_option('display.width', 250)
    print(results[['year', 'tier', 'fallback', 'calibration_precision', 'calibration_recall', 'tp', 'fp', 'recall', 'precision',
                   'precision_lower', 'precision_upper', 'accuracy', 'always_negative_accuracy', 'episode_precision',
                   'positive_runs', 'missed_positive_runs']].round(4).to_string(index=False))
    print(oracle.round(4).to_string(index=False))
    print(json.dumps({k: v for k, v in result.items() if k != 'artifact_hashes'}, indent=1))
