"""Evaluate the frozen threshold selection protocol (config/threshold-selection-v1.json)."""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from helio24.calibration import SigmoidCalibration, recall_threshold
from helio24.events import HOUR
from scripts.audit_alarm_persistence import acceptance, evaluate, paired_bootstrap, sha

TCN_ARMS = ['chronological', 'shuffled_interior']


def positive_run_maxima(frame, probability):
    """Highest probability inside each run of consecutive-hour positive-labelled windows of one HARP."""
    data = frame[['harp', 'forecast_time', 'target']].assign(probability=np.asarray(probability))
    data = data.sort_values(['harp', 'forecast_time']).reset_index(drop=True)
    previous = data.groupby('harp').forecast_time.shift()
    continues = data.target.eq(1) & data.groupby('harp').target.shift().eq(1) \
        & data.forecast_time.sub(previous).eq(HOUR)
    run_id = (~continues).cumsum()
    positive = data[data.target.eq(1)]
    return positive.groupby(run_id[positive.index]).probability.max().to_numpy()


def run_recall_threshold(frame, probability, target_recall):
    """Fewest calibration false-alarm windows with positive-run recall >= target; ties take the larger threshold."""
    probability = np.asarray(probability, dtype=float)
    maxima = np.sort(positive_run_maxima(frame, probability))
    negatives = np.sort(probability[frame.target.to_numpy() == 0])
    grid = np.unique(probability)
    if len(maxima) == 0 or negatives.size == 0:
        raise ValueError('Threshold selection needs both classes')
    recall = (len(maxima)-np.searchsorted(maxima, grid, side='left'))/len(maxima)
    false_alarms = len(negatives)-np.searchsorted(negatives, grid, side='left')
    eligible = np.flatnonzero(recall >= target_recall-1e-12)
    if eligible.size == 0:
        raise ValueError('Target run recall cannot be reached')
    order = sorted(eligible, key=lambda i: (false_alarms[i], -grid[i]))
    return float(grid[order[0]])


def select_thresholds(frame, probability, rules):
    target = frame.target.to_numpy()
    out = {}
    for rule in rules:
        if rule['basis'] == 'window_recall':
            out[rule['id']] = recall_threshold(target, probability, rule['target'])
        else:
            out[rule['id']] = run_recall_threshold(frame, probability, rule['target'])
    return out


def calibration_scores(directory, arm, seeds):
    raw = np.mean([np.load(directory/f'{arm}_seed{seed}'/'calibration.npy') for seed in seeds], axis=0)
    parameters = json.loads((directory/'calibrators.json').read_text())[arm]
    return SigmoidCalibration(parameters['slope'], parameters['intercept']).transform(raw)


def baseline_gate(config):
    """Baseline calibration probabilities need the frozen development feature shards."""
    walk = json.loads((Path(config['evidence']['baseline_artifact'])/'report.json').read_text())
    source = Path(walk['protocol']['source'])
    report = json.loads((source/'report.json').read_text())
    missing = [item['file'] for item in report['shards'] if not (source/'shards'/item['file']).exists()]
    return {'evaluable': not missing, 'shards_expected': len(report['shards']), 'shards_missing': len(missing),
            'reason': None if not missing else 'Frozen development feature shards are missing, so baseline '
                      'calibration probabilities cannot be recomputed and the stored threshold cannot be reproduced.'}


def run(source, expected, config_path, output):
    if output.exists():
        raise FileExistsError(output)
    config = json.loads(config_path.read_text())
    evidence = config['evidence']
    if sha(source/'report.json') != expected or expected != evidence['predictions_report_sha256']:
        raise ValueError('Final experiment manifest changed')
    report = json.loads((source/'report.json').read_text())
    gate = baseline_gate(config)
    if gate['evaluable']:
        raise NotImplementedError('Baseline recomputation is not implemented; the shards were expected missing')
    persistence = json.loads(Path(evidence['persistence_config']).read_text())
    tolerance = config['acceptance']['per_year_primary']['window_recall_drop_at_most']
    seeds = persistence_seeds = [24, 42, 97]
    rules = [config['control']]+config['candidates']
    arms = TCN_ARMS
    # Phase 1: thresholds from calibration windows only, written to disk before any evaluation file is read.
    chosen, stability = {}, []
    for year in config['years']:
        directory = source/str(year)
        for name in ['calibration-metadata.parquet', 'calibrators.json', 'thresholds.json']:
            rel = f'{year}/{name}'
            if sha(source/rel) != report['artifact_hashes'][rel]:
                raise ValueError(f'Changed annual evidence: {rel}')
        calibration = pd.read_parquet(directory/'calibration-metadata.parquet')
        stored = json.loads((directory/'thresholds.json').read_text())
        for arm in arms:
            probability = calibration_scores(directory, arm, seeds)
            selected = select_thresholds(calibration, probability, rules)
            if not np.isclose(selected['control_w95'], stored[arm], rtol=1e-12, atol=0):
                raise ValueError(f'Control does not reproduce the stored threshold: {year} {arm}')
            chosen[f'{year}/{arm}'] = selected
            maxima = positive_run_maxima(calibration, probability)
            for rule_id, threshold in selected.items():
                target = calibration.target.to_numpy()
                stability.append(dict(year=year, arm=arm, rule=rule_id, threshold=threshold,
                    ratio_to_control=threshold/selected['control_w95'],
                    calibration_positive_windows=int(target.sum()), calibration_positive_runs=len(maxima),
                    calibration_recall=float((probability[target == 1] >= threshold).mean()),
                    calibration_run_recall=float((maxima >= threshold).mean())))
    output.mkdir(parents=True)
    (output/'selected_thresholds.json').write_text(json.dumps(chosen, indent=2)+'\n')
    thresholds_sha = sha(output/'selected_thresholds.json')
    # Phase 2: evaluation windows and labels are read only now.
    stability = pd.DataFrame(stability)
    rows, intervals = [], []
    for year in config['years']:
        for name in ['predictions.parquet', 'finished.json']:
            rel = f'{year}/{name}'
            if sha(source/rel) != report['artifact_hashes'][rel]:
                raise ValueError(f'Changed annual evidence: {rel}')
        frame = pd.read_parquet(source/str(year)/'predictions.parquet')
        for arm in arms:
            selected = chosen[f'{year}/{arm}']
            results = {rule['id']: evaluate(frame, arm, selected[rule['id']], 1) for rule in rules}
            control, control_harp = results['control_w95']
            for rule in rules:
                values, per_harp = results[rule['id']]
                row = dict(year=year, arm=arm, rule=rule['id'], **values)
                if rule['id'] != 'control_w95':
                    flags = acceptance(values, control, tolerance)
                    row.update(flags)
                    row['primary_met'] = bool(all(flags.values()) and year in config['positive_years'])
                    for metric, interval in paired_bootstrap(control_harp, per_harp).items():
                        intervals.append(dict(year=year, arm=arm, rule=rule['id'], metric=metric, **interval))
                rows.append(row)
    table = pd.DataFrame(rows)
    table = table.merge(stability[['year', 'arm', 'rule', 'ratio_to_control', 'calibration_positive_windows',
        'calibration_positive_runs', 'calibration_recall', 'calibration_run_recall']], on=['year', 'arm', 'rule'])
    table['evaluation_recall_minus_calibration_recall'] = table.recall-table.calibration_recall
    summary = []
    for (arm, rule), group in table[table.rule != 'control_w95'].groupby(['arm', 'rule'], sort=False):
        gated = group[group.year.isin(config['positive_years'])]
        summary.append(dict(arm=arm, rule=rule, years_met=int(gated.primary_met.sum()),
            required_years=len(config['positive_years']),
            all_year_primary=bool(gated.primary_met.all() and len(gated) == len(config['positive_years']))))
    table.to_csv(output/'selection.csv', index=False)
    pd.DataFrame(intervals).to_csv(output/'intervals.csv', index=False)
    pd.DataFrame(summary).to_csv(output/'acceptance.csv', index=False)
    result = {'config_sha256': sha(config_path), 'source_report_sha256': expected,
        'selected_thresholds_sha256': thresholds_sha, 'baseline_gate': gate,
        'primary_arm': 'chronological' if not gate['evaluable'] else config['arms']['primary'],
        'years': config['years'], 'acceptance': summary,
        'bootstrap': {'draws': 1000, 'seed': 24, 'unit': 'full HARP, paired with control'},
        'reserved_test_accessed': False, 'model_promoted': False,
        'artifact_hashes': {p.name: sha(p) for p in sorted(output.iterdir())}}
    (output/'report.json').write_text(json.dumps(result, indent=2)+'\n')
    return result, table


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--source-sha256', required=True)
    parser.add_argument('--config', type=Path, default=Path('config/threshold-selection-v1.json'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result, _ = run(args.source, args.source_sha256, args.config, args.output)
    print(json.dumps(result['baseline_gate'], indent=1))
    print(pd.DataFrame(result['acceptance']).to_string(index=False))
