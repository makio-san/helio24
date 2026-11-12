"""Evaluate SGAS flare-history features at the alert tier of the adopted pipeline (config/activity-history-v2.json)."""
import argparse
import gc
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score

from helio24.calibration import SigmoidCalibration
from helio24.data import FEATURE_COLUMNS
from helio24.v2_training import candidate_models, load_development
from helio24.walk_forward import annual_fold
from scripts.audit_activity_history import CANDIDATES, attach_history, load_sgas
from scripts.audit_alarm_persistence import sha
from scripts.audit_cycle25 import decomposition
from scripts.audit_cycle25_relabelled import alert_false_positive_origin
from scripts.audit_region_context_sources import load_mapping
from scripts.audit_two_tier import point
from scripts.rebuild_walk_forward_v2 import select_thresholds

KEY = ['harp', 'forecast_time']
TIERS = ['watch', 'alert']


def fit_probabilities(base, groups, contexts, columns):
    """Unchanged recipes on the 96 summaries plus context columns; calibrated 0.45/0.55 ensemble on calibration and evaluation."""
    x = {role: np.hstack([groups[role][FEATURE_COLUMNS].to_numpy(dtype=np.float32),
                          contexts[role][columns].to_numpy(dtype=np.float32)]) for role in ['train', 'calibration', 'evaluation']}
    y_train = groups['train'].target.to_numpy(dtype=np.int8)
    y_cal = groups['calibration'].target.to_numpy(dtype=np.int8)
    weight = base['ensemble']['logistic_weight']
    calibrated, evaluated = {}, {}
    for name, model in candidate_models(base).items():
        model.fit(x['train'], y_train)
        raw = np.clip(model.predict_proba(x['calibration'])[:, 1], 1e-9, 1-1e-9)
        calibrator = SigmoidCalibration().fit(raw, y_cal)
        calibrated[name] = calibrator.transform(raw)
        evaluated[name] = calibrator.transform(np.clip(model.predict_proba(x['evaluation'])[:, 1], 1e-9, 1-1e-9))
        del model
    return (weight*calibrated['logistic']+(1-weight)*calibrated['xgboost'],
            weight*evaluated['logistic']+(1-weight)*evaluated['xgboost'])


def precision_at_recall(target, probability, recall):
    """Precision at the lowest evaluation-year threshold that still delivers `recall` (oracle-matched, descriptive)."""
    order = np.argsort(-np.asarray(probability), kind='stable')
    y = np.asarray(target)[order]
    tp = np.cumsum(y)
    reached = np.searchsorted(tp, int(np.ceil(recall*y.sum()-1e-9)), side='left')
    reached = min(max(reached, 0), len(y)-1)
    return float(tp[reached]/(reached+1))


def paired_precision_bootstrap(frame, control_alarm, candidate_alarm, draws=1000, seed=24):
    """HARP-cluster bootstrap of alert precision difference, candidate minus control."""
    target = frame.target.eq(1).to_numpy()
    counts = pd.DataFrame({'harp': frame.harp.to_numpy(), 'ctp': control_alarm & target, 'cfp': control_alarm & ~target,
                           'ntp': candidate_alarm & target, 'nfp': candidate_alarm & ~target}).groupby('harp').sum().to_numpy(dtype=float)
    rng = np.random.default_rng(seed)
    differences = []
    for _ in range(draws):
        ctp, cfp, ntp, nfp = counts[rng.integers(0, len(counts), len(counts))].sum(axis=0)
        if ctp+cfp and ntp+nfp:
            differences.append(ntp/(ntp+nfp)-ctp/(ctp+cfp))
    if not differences:
        return dict(lower=None, upper=None, draws_used=0)
    return dict(lower=float(np.quantile(differences, .025)), upper=float(np.quantile(differences, .975)), draws_used=len(differences))


def acceptance(row, control, tolerance):
    return dict(precision_higher_than_control=bool(pd.notna(row['precision']) and pd.notna(control['precision'])
                                                   and row['precision'] > control['precision']),
                missed_positive_runs_not_above_control=bool(row['missed_positive_runs'] <= control['missed_positive_runs']),
                window_recall_drop_within_tolerance=bool(row['recall'] >= control['recall']-tolerance))


def read(summary):
    def passes(candidate):
        s = summary[candidate]
        return s['all_year_primary'] or (s['cycle25_primary'] and s['cycle25_bootstrap_lower_above_zero'])
    history, flag = passes('history'), passes('flag')
    return 'R2_refit_only' if history and flag else 'R1_history_helps' if history else 'R3_no_gain'


def run(config_path, output):
    if output.exists():
        raise FileExistsError(output)
    config = json.loads(config_path.read_text())
    evidence = config['evidence']
    control_dir = Path(evidence['control'])
    for path, expected in [(Path(evidence['table'])/'report.json', evidence['table_report_sha256']),
                           (control_dir/'report.json', evidence['control_report_sha256']),
                           (Path(evidence['sgas_directory'])/'manifest.json', evidence['sgas_manifest_sha256']),
                           (Path(evidence['mapping_directory'])/'manifest.json', evidence['mapping_manifest_sha256'])]:
        if sha(path) != expected:
            raise ValueError(f'Input changed: {path}')
    control_report = json.loads((control_dir/'report.json').read_text())
    pipeline = json.loads(Path(evidence['pipeline_protocol']).read_text())
    base = json.loads(Path(evidence['base_protocol']).read_text())
    reports, events, problems = load_sgas(Path(evidence['sgas_directory']))
    mapping, _, _ = load_mapping(Path(evidence['mapping_directory']))
    groups, _ = load_development(Path(evidence['table']), evidence['table_report_sha256'])
    development = pd.concat(groups.values(), ignore_index=True)
    del groups
    output.mkdir(parents=True)
    thresholds, prepared, coverage = {}, {}, []
    for year in config['years']:
        split, audit = annual_fold(development, year)
        if audit != next(f for f in control_report['folds'] if f['year'] == year)['audit']:
            raise ValueError(f'Annual populations changed: {year}')
        split['evaluation'] = split['evaluation'].drop(columns=['target', 'label_status'])
        contexts = {role: attach_history(group, mapping, reports, events) for role, group in split.items()}
        for role, context in contexts.items():
            coverage.append({'year': year, 'role': role, 'rows': len(context),
                             'history_available_share': float(context.history_available.mean()),
                             'reg_mx_3d_positive_share': float((context.reg_mx_3d > 0).mean())})
        y_cal = split['calibration'].target.to_numpy(dtype=np.int8)
        chosen = {'control': json.loads((control_dir/str(year)/'thresholds.json').read_text())}
        probabilities = {}
        for candidate, columns in CANDIDATES.items():
            p_cal, probabilities[candidate] = fit_probabilities(base, split, contexts, columns)
            chosen[candidate] = select_thresholds(pipeline, y_cal, p_cal)
            gc.collect()
        thresholds[str(year)] = chosen
        prepared[year] = split['evaluation'][KEY].reset_index(drop=True).assign(**probabilities)
        print(f'{year}: alert thresholds ' + ', '.join(f'{c}={v["alert"]["threshold"]:.4f}' for c, v in chosen.items()), flush=True)
        del split, contexts
        gc.collect()
    (output/'thresholds.json').write_text(json.dumps(thresholds, indent=2)+'\n')
    pd.DataFrame(coverage).to_csv(output/'history_coverage.csv', index=False)
    thresholds_sha = sha(output/'thresholds.json')
    # Phase 2: evaluation labels are read only now.
    tolerance = config['acceptance']['per_year_primary']['window_recall_drop_at_most']
    candidates = ['control', *CANDIDATES]
    rows, intervals = [], []
    for year in config['years']:
        labels = pd.read_parquet(control_dir/str(year)/'predictions.parquet', columns=[*KEY, 'target', 'missing_fraction', 'ensemble'])
        frame = labels.merge(prepared[year], on=KEY, how='inner').rename(columns={'ensemble': 'control'})
        if len(frame) != len(labels) or len(frame) != len(prepared[year]):
            raise ValueError(f'Evaluation keys do not match: {year}')
        frame = frame.sort_values(KEY).reset_index(drop=True)
        year_rows = {}
        for candidate in candidates:
            scored = frame[[*KEY, 'target', 'missing_fraction']].assign(probability=frame[candidate])
            chosen = thresholds[str(year)][candidate]
            parts = decomposition(scored, chosen['watch']['threshold'])
            origin = alert_false_positive_origin(scored, chosen['alert']['threshold'])
            for tier in TIERS:
                row = point(scored, tier, chosen[tier], year)
                row.update(candidate=candidate, average_precision=parts['overall_ap'], within_flaring_ap=parts['within_flaring_ap'],
                           region_ap=parts['region_ap'])
                if tier == 'alert':
                    row.update(alert_fp_share_never_flaring_harps=origin['alert_fp_share_never_flaring_harps'],
                               alert_fp_share_within_72h_of_positive=origin['alert_fp_share_within_72h_of_positive'])
                year_rows[(candidate, tier)] = row
        control = year_rows[('control', 'alert')]
        control_alarm = frame.control.ge(thresholds[str(year)]['control']['alert']['threshold']).to_numpy()
        for candidate in CANDIDATES:
            row = year_rows[(candidate, 'alert')]
            flags = acceptance(row, control, tolerance)
            row.update(flags)
            row['primary_met'] = bool(all(flags.values()))
            row['precision_at_control_recall'] = precision_at_recall(frame.target.to_numpy(), frame[candidate].to_numpy(), control['recall'])
            alarm = frame[candidate].ge(thresholds[str(year)][candidate]['alert']['threshold']).to_numpy()
            interval = paired_precision_bootstrap(frame, control_alarm, alarm)
            intervals.append(dict(year=year, candidate=candidate, metric='alert_precision_difference', **interval))
            row.update(precision_difference_lower=interval['lower'], precision_difference_upper=interval['upper'])
        control['precision_at_control_recall'] = control['precision']
        rows.extend(year_rows.values())
        frame.to_parquet(output/f'predictions_{year}.parquet', index=False)
    table = pd.DataFrame(rows)
    table.to_csv(output/'results.csv', index=False)
    pd.DataFrame(intervals).to_csv(output/'intervals.csv', index=False)
    alert = table[table.tier.eq('alert')]
    summary = {}
    for candidate in candidates:
        part = alert[alert.candidate.eq(candidate)].set_index('year')
        entry = {'years_precision_at_least_0.50': [int(y) for y in part.index if pd.notna(part.precision[y]) and part.precision[y] >= 0.5],
                 'alert_fallback_years': [int(y) for y in part.index if part.fallback[y]]}
        if candidate != 'control':
            met = part.primary_met.astype(bool)
            entry.update(met_years=[int(y) for y in part.index[met]], all_year_primary=bool(met.all()),
                         cycle25_primary=bool(met[[2022, 2023]].all()),
                         cycle25_bootstrap_lower_above_zero=bool((part.loc[[2022, 2023], 'precision_difference_lower'].astype(float) > 0).all()))
        summary[candidate] = entry
    result = {'config_sha256': sha(config_path), 'thresholds_sha256': thresholds_sha, 'years': config['years'],
              'development_basis': 'relabelled table, walk-forward-v2, operating-point-v3',
              'sgas_reports': len(reports), 'sgas_events': len(events), 'sgas_problems': problems,
              'acceptance': summary, 'reading': read(summary), 'constituent_fits': len(config['years'])*len(CANDIDATES)*2,
              'reserved_test_accessed': False, 'model_promoted': False,
              'artifact_hashes': {p.name: sha(p) for p in sorted(output.iterdir())}}
    (output/'report.json').write_text(json.dumps(result, indent=2)+'\n')
    return result, table


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=Path('config/activity-history-v2.json'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result, table = run(args.config, args.output)
    pd.set_option('display.width', 250)
    print(table[['year', 'candidate', 'tier', 'fallback', 'tp', 'fp', 'recall', 'precision', 'accuracy', 'always_negative_accuracy',
                 'missed_positive_runs', 'positive_runs', 'average_precision', 'within_flaring_ap']].round(4).to_string(index=False))
    print(json.dumps({'acceptance': result['acceptance'], 'reading': result['reading']}, indent=1))
