"""Alert-tier results of the adopted pipeline with a 72-hour forecast horizon (config/horizon-72h-v1.json)."""
import argparse
import gc
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, precision_recall_curve

from helio24.v2_training import load_development
from helio24.walk_forward import annual_fold
from scripts.audit_activity_history_relabelled import KEY, TIERS, fit_probabilities
from scripts.audit_alarm_persistence import sha
from scripts.audit_cycle25 import decomposition
from scripts.audit_two_tier import point
from scripts.rebuild_walk_forward_v2 import select_thresholds

HORIZON, BASE = 72, 24
HOUR_NS = 3_600_000_000_000


def extend_labels(table, horizon=HORIZON, base=BASE):
    """72-hour labels as the OR of the 24-hour targets of windows in [t, t+horizon-base]; unknown labels are removed."""
    span = horizon-base
    kept = []
    for harp, group in table.groupby('harp', sort=False):
        group = group.sort_values('forecast_time')
        rounded = pd.DatetimeIndex(group.forecast_time).round('h')
        hours = rounded.as_unit('ns').asi8//HOUR_NS
        if len(np.unique(hours)) != len(hours):
            raise ValueError(f'Two windows of HARP {harp} fall in one hour')
        n = len(hours)
        target = group.target.to_numpy(dtype=np.int64)
        end = np.searchsorted(hours, hours+span)
        end_ok = np.minimum(end, n-1)
        has_end = (end < n) & (hours[end_ok] == hours+span)
        broken = np.concatenate([[0], np.cumsum(np.diff(hours) > base)])
        covered = (broken[end_ok]-broken[np.arange(n)]) == 0
        known = has_end & covered
        positives = np.concatenate([[0], np.cumsum(target)])
        label = (positives[end_ok+1]-positives[np.arange(n)]) > 0
        part = group[known].copy()
        part['target24'] = part.target
        part['target'] = label[known].astype(int)
        part['label_status'] = np.where(part.target.eq(1), 'positive', 'negative')
        part['prediction_end'] = part.forecast_time+pd.Timedelta(hours=horizon)
        kept.append(part)
    return pd.concat(kept, ignore_index=True)


def read(entry, baseline_years=3):
    """W1: every year meets the alert target on 72 hours; W2: more years than the 24-hour control; else W3."""
    if entry['all_years_goal']:
        return 'W1_goal_met_on_72h'
    return 'W2_partial' if len(entry['years_precision_at_least_0.50']) > baseline_years else 'W3_no_gain'


def tier_row(scored, tier, chosen, year):
    row = point(scored, tier, chosen, year)
    tp, fp, fn, tn = (int(row[k]) for k in ['tp', 'fp', 'fn', 'tn'])
    n = tp+fp+fn+tn
    row.update(f1=2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else np.nan, positive_share=(tp+fn)/n,
               lift=(tp/(tp+fp))/((tp+fn)/n) if tp+fp and tp+fn else np.nan)
    return row


def best_f1(target, probability):
    precision, recall, _ = precision_recall_curve(target, probability)
    f1 = 2*precision*recall/np.maximum(precision+recall, 1e-12)
    index = int(np.nanargmax(f1))
    return float(f1[index]), float(precision[index]), float(recall[index])


def run(config_path, output):
    if output.exists():
        raise FileExistsError(output)
    config = json.loads(config_path.read_text())
    evidence = config['evidence']
    for path, expected in [(Path(evidence['table'])/'report.json', evidence['table_report_sha256']),
                           (Path(evidence['control_24h'])/'report.json', evidence['control_24h_report_sha256'])]:
        if sha(path) != expected:
            raise ValueError(f'Input changed: {path}')
    pipeline = json.loads(Path(evidence['pipeline_protocol']).read_text())
    base = json.loads(Path(evidence['base_protocol']).read_text())
    groups, _ = load_development(Path(evidence['table']), evidence['table_report_sha256'])
    table24 = pd.concat(groups.values(), ignore_index=True)
    del groups
    table72 = extend_labels(table24)
    table72.drop(columns='role', inplace=True)
    candidates = [c['id'] for c in config['candidates']]
    output.mkdir(parents=True)
    thresholds, probabilities = {}, {}
    # Phase 1: fits and thresholds; evaluation labels are dropped before any fit and never read here.
    for year in config['years']:
        split, _ = annual_fold(table72, year)
        split['evaluation'] = split['evaluation'].drop(columns=['target', 'target24', 'label_status'])
        empty = {role: pd.DataFrame(index=group.index) for role, group in split.items()}
        y_cal = split['calibration'].target.to_numpy(dtype=np.int8)
        thresholds[str(year)], probabilities[year] = {}, {}
        for candidate in candidates:
            fitted = split if candidate == 'm72' else {
                role: group.assign(target=group.target24) if role != 'evaluation' else group for role, group in split.items()}
            p_cal, p_eval = fit_probabilities(base, fitted, empty, [])
            thresholds[str(year)][candidate] = select_thresholds(pipeline, y_cal, p_cal)
            probabilities[year][candidate] = p_eval
        probabilities[year]['key'] = split['evaluation'][KEY].reset_index(drop=True)
        print(f'{year}: alert thresholds ' + ', '.join(f'{c}={thresholds[str(year)][c]["alert"]["threshold"]:.4f}' for c in candidates), flush=True)
        del split, empty
        gc.collect()
    (output/'thresholds.json').write_text(json.dumps(thresholds, indent=2)+'\n')
    thresholds_sha = sha(output/'thresholds.json')
    # Phase 2: evaluation labels are read only now.
    rows, counts = [], []
    for year in config['years']:
        split, audit24 = annual_fold(table24, year)
        split, audit72 = annual_fold(table72, year)
        counts.extend({'year': year, 'horizon': 24 if a is audit24 else 72, **r} for a in (audit24, audit72) for r in a)
        evaluation = split['evaluation'][[*KEY, 'target', 'missing_fraction']].reset_index(drop=True)
        key = probabilities[year].pop('key')
        if not key.equals(evaluation[KEY]):
            raise ValueError(f'Evaluation windows differ: {year}')
        frame = evaluation.copy()
        for candidate in candidates:
            frame[candidate] = probabilities[year][candidate]
            scored = evaluation.assign(probability=frame[candidate])
            chosen = thresholds[str(year)][candidate]
            parts = decomposition(scored, chosen['watch']['threshold'])
            oracle = best_f1(frame.target.to_numpy(), frame[candidate].to_numpy())
            for tier in TIERS:
                row = tier_row(scored, tier, chosen[tier], year)
                row.update(candidate=candidate, average_precision=average_precision_score(frame.target, frame[candidate]),
                           within_flaring_ap=parts['within_flaring_ap'], region_ap=parts['region_ap'],
                           best_threshold_f1=oracle[0], best_threshold_precision=oracle[1], best_threshold_recall=oracle[2])
                rows.append(row)
        frame.to_parquet(output/f'predictions_{year}.parquet', index=False)
        del split
    table = pd.DataFrame(rows)
    table.to_csv(output/'results.csv', index=False)
    pd.DataFrame(counts).to_csv(output/'window_counts.csv', index=False)
    alert = table[table.tier.eq('alert')]
    summary = {}
    for candidate in candidates:
        part = alert[alert.candidate.eq(candidate)].set_index('year')
        reaching = [int(y) for y in part.index if part.precision[y] >= 0.5]
        entry = {'years_precision_at_least_0.50': reaching,
                 'alert_fallback_years': [int(y) for y in part.index if part.fallback[y]],
                 'years_accuracy_above_always_negative': [int(y) for y in part.index if part.accuracy[y] > part.always_negative_accuracy[y]]}
        entry['all_years_goal'] = bool(len(reaching) == len(part) and not entry['alert_fallback_years']
                                       and len(entry['years_accuracy_above_always_negative']) == len(part))
        entry['reading'] = read(entry)
        summary[candidate] = entry
    result = {'config_sha256': sha(config_path), 'thresholds_sha256': thresholds_sha, 'years': config['years'],
              'development_basis': 'relabelled table, walk-forward-v2, operating-point-v3', 'horizon_hours': HORIZON,
              'acceptance': summary, 'reading': summary['m72']['reading'], 'constituent_fits': len(config['years'])*len(candidates)*2,
              'reserved_test_accessed': False, 'model_promoted': False,
              'artifact_hashes': {p.name: sha(p) for p in sorted(output.iterdir())}}
    (output/'report.json').write_text(json.dumps(result, indent=2)+'\n')
    return result, table


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=Path('config/horizon-72h-v1.json'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result, table = run(args.config, args.output)
    pd.set_option('display.width', 250)
    print(table[['year', 'candidate', 'tier', 'fallback', 'tp', 'fp', 'recall', 'precision', 'f1', 'accuracy', 'always_negative_accuracy',
                 'positive_share', 'lift', 'missed_positive_runs', 'positive_runs', 'average_precision']].round(4).to_string(index=False))
    print(json.dumps({'acceptance': result['acceptance'], 'reading': result['reading']}, indent=1))
