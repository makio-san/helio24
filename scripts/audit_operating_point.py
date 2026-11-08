"""Describe the frozen baseline at recall targets below 0.95 (config/operating-point-review-v1.json)."""
import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from helio24.calibration import recall_threshold
from helio24.v2_training import load_development
from helio24.walk_forward import annual_fold
from scripts.audit_alarm_persistence import evaluate, sha
from scripts.audit_threshold_selection_baseline import ensemble_probability, identity_check

KEY = ['harp', 'forecast_time']


def recall_for_precision(target, probability, precision_target):
    """Smallest recall loss: highest recall whose best threshold reaches the precision target (oracle)."""
    order = np.argsort(-probability, kind='stable')
    y = np.asarray(target)[order]
    tp = np.cumsum(y)
    fp = np.cumsum(1-y)
    precision = tp/np.maximum(tp+fp, 1)
    recall = tp/max(y.sum(), 1)
    ok = precision >= precision_target-1e-12
    return float(recall[ok].max()) if ok.any() else 0.0


def point(frame, column, threshold, year, kind, target):
    values, _ = evaluate(frame, column, threshold, 1)
    return dict(year=year, kind=kind, recall_target=target, threshold=threshold, tp=values['tp'], fp=values['fp'],
                fn=values['fn'], recall=values['recall'], precision=values['precision'],
                alarm_windows=values['alarm_windows'], episodes=values['episodes'],
                episode_precision=values['episode_precision'], positive_runs=values['positive_runs'],
                positive_runs_alarmed=values['positive_runs_alarmed'], positive_run_recall=values['positive_run_recall'],
                missed_positive_runs=values['positive_runs']-values['positive_runs_alarmed'])


def run(config_path, output):
    if output.exists():
        raise FileExistsError(output)
    config = json.loads(config_path.read_text())
    evidence = config['evidence']
    source = Path(evidence['predictions'])
    if sha(source/'report.json') != evidence['predictions_report_sha256']:
        raise ValueError('Final experiment manifest changed')
    report = json.loads((source/'report.json').read_text())
    walk_dir = Path(evidence['baseline_artifact'])
    if sha(walk_dir/'report.json') != evidence['baseline_report_sha256']:
        raise ValueError('Baseline walk-forward report changed')
    walk_report = json.loads((walk_dir/'report.json').read_text())
    original, _ = load_development(Path(evidence['frozen_shards_report']).parent, evidence['frozen_shards_report_sha256'])
    table = pd.concat(original.values(), ignore_index=True)
    del original
    output.mkdir(parents=True)
    targets = config['deployable_curve']['recall_targets']
    # Phase 1: deployable thresholds from calibration years only.
    deployable, prepared = {}, {}
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
        stored_threshold = json.loads((source/str(year)/'thresholds.json').read_text())['baseline']
        chosen = {str(t): recall_threshold(calibration.target.to_numpy(), p_cal, t) for t in targets}
        if not np.isclose(chosen['0.95'], stored_threshold, rtol=1e-12, atol=0):
            raise ValueError(f'Control threshold not reproduced: {year}')
        identity = identity_check(evaluation.assign(probability=p_eval),
                                  pd.read_parquet(source/str(year)/'predictions.parquet', columns=[*KEY, 'baseline']))
        if not identity['passed']:
            raise ValueError(f'Identity check failed: {year}')
        deployable[str(year)] = chosen
        prepared[year] = evaluation[KEY].reset_index(drop=True).assign(probability=p_eval)
    (output/'deployable_thresholds.json').write_text(json.dumps(deployable, indent=2)+'\n')
    thresholds_sha = sha(output/'deployable_thresholds.json')
    # Phase 2: evaluation labels.
    rows, required = [], []
    for year in config['years']:
        labels = pd.read_parquet(source/str(year)/'predictions.parquet', columns=[*KEY, 'target', 'missing_fraction'])
        frame = labels.merge(prepared[year], on=KEY, how='inner')
        if len(frame) != len(labels):
            raise ValueError(f'Evaluation keys do not match: {year}')
        y = frame.target.to_numpy()
        for t in targets:
            rows.append(point(frame, 'probability', deployable[str(year)][str(t)], year, 'deployable', t))
        for t in config['oracle_curve']['recall_targets']:
            rows.append(point(frame, 'probability', recall_threshold(y, frame.probability.to_numpy(), t), year, 'oracle', t))
        for precision_target in config['oracle_curve']['precision_targets_for_required_recall']:
            required.append(dict(year=year, precision_target=precision_target,
                                 oracle_max_recall=recall_for_precision(y, frame.probability.to_numpy(), precision_target)))
    curve = pd.DataFrame(rows)
    curve.to_csv(output/'curve.csv', index=False)
    pd.DataFrame(required).to_csv(output/'required_recall.csv', index=False)
    result = {'config_sha256': sha(config_path), 'source_report_sha256': evidence['predictions_report_sha256'],
              'deployable_thresholds_sha256': thresholds_sha, 'years': config['years'],
              'reserved_test_accessed': False, 'model_promoted': False,
              'artifact_hashes': {p.name: sha(p) for p in sorted(output.iterdir())}}
    (output/'report.json').write_text(json.dumps(result, indent=2)+'\n')
    return result, curve, pd.DataFrame(required)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=Path('config/operating-point-review-v1.json'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result, curve, required = run(args.config, args.output)
    pd.set_option('display.width', 220)
    print(curve[['year', 'kind', 'recall_target', 'recall', 'precision', 'fp', 'episode_precision',
                 'positive_runs', 'missed_positive_runs']].round(4).to_string(index=False))
    print(required.round(4).to_string(index=False))
