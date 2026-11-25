"""Place each window in the stored life of its HARP and judge the alert tier (config/life-phase-v1.json).

Run once from the repository root:
    OMP_NUM_THREADS=3 python -m scripts.audit_life_phase --config config/life-phase-v1.json --output artifacts/<name>_<YYYYMMDD>_r<n>
"""
import argparse
import gc
import json
from pathlib import Path

import numpy as np
import pandas as pd

from helio24.data import FEATURE_COLUMNS
from helio24.life_phase import (AGE, GAP, GAP_SPACING_HOURS, GAP_SPAN_HOURS, KEY, LAGS_HOURS, MEASUREMENTS, PHASE_COLUMNS, RATIO_CLIP,
                                SOURCE_COLUMNS, Z_CLIP, life_phase_features)
from helio24.v2_training import load_development
from helio24.walk_forward import annual_fold
from scripts.audit_activity_history_relabelled import acceptance, fit_probabilities, paired_precision_bootstrap, precision_at_recall
from scripts.audit_alarm_persistence import sha
from scripts.audit_cycle25 import decomposition
from scripts.audit_cycle25_relabelled import alert_false_positive_origin
from scripts.audit_near_miss_weighting import blind, entry, meets_goal
from scripts.audit_two_tier import point
from scripts.rebuild_walk_forward_v2 import select_thresholds

TIERS = ['watch', 'alert']
META = [*KEY, 'observation_start', 'prediction_end', 'target', 'label_status', 'missing_fraction']
CANDIDATES = {'age_only': [AGE], 'life_phase': [AGE, *PHASE_COLUMNS]}
CONSTITUENTS = 2
CYCLE25 = [2022, 2023]
RESERVED_START = pd.Timestamp('2024-01-01', tz='UTC')
READINGS = ['L1_life_phase_helps', 'L2_refit_or_age_only', 'L3_no_gain']
LABELS = {'L1_life_phase_helps': 'result:goal-met', 'L2_refit_or_age_only': 'result:partial', 'L3_no_gain': 'result:no-gain'}
POPULATION = ['train_rows', 'train_positives', 'calibration_rows', 'calibration_positives', 'evaluation_rows',
              'train_recent_gap_72h', 'evaluation_recent_gap_72h', 'evaluation_younger_than_72h']


def check_protocol(config):
    """Refuse anything but the frozen candidates, feature lists, budget and development years."""
    if not str(config.get('status', '')).startswith('frozen_before_any') or config.get('reserved_test_accessed') is not False:
        raise ValueError('Protocol is not frozen or touches the reserved test')
    if [c['id'] for c in config['candidates']] != list(CANDIDATES):
        raise ValueError('Candidate set differs from the frozen one')
    features = config['features']
    if features['measurements'] != MEASUREMENTS or features['lags_hours'] != LAGS_HOURS or features['source_columns'] != SOURCE_COLUMNS:
        raise ValueError('Measurements and lags are fixed')
    if features['added'] != CANDIDATES or features['clip'] != {'ratio_to_running_max': RATIO_CLIP, 'running_z': Z_CLIP}:
        raise ValueError('Feature list or clip differs from the frozen one')
    if any('count' in column for columns in features['added'].values() for column in columns) or GAP in sum(features['added'].values(), []):
        raise ValueError('Window counts and gap flags are never model inputs')
    if features['gap_flag'] != {'name': GAP, 'spacing_hours': GAP_SPACING_HOURS, 'span_hours': GAP_SPAN_HOURS, 'model_input': False}:
        raise ValueError('The gap flag is fixed and reporting only')
    years = config['years']
    if years != sorted(set(years)) or any(not 2012 <= year <= 2023 for year in years):
        raise ValueError('Only development years before the reserved test are allowed')
    if not set(CYCLE25) <= set(years):
        raise ValueError('The reading needs 2022 and 2023')
    if config['budget']['constituent_fits'] != len(years)*len(CANDIDATES)*CONSTITUENTS:
        raise ValueError('Fit budget differs from candidates x years x constituents')
    if not set(config['alert_fallback_years']) <= set(years):
        raise ValueError('Alert fallback years must be evaluated years')


def fold_population(split, contexts):
    """Label counts of the training and calibration roles and label-free coverage counts of the life features."""
    train, calibration, evaluation = split['train'], split['calibration'], split['evaluation']
    return dict(train_rows=len(train), train_positives=int(train.target.sum()),
                calibration_rows=len(calibration), calibration_positives=int(calibration.target.sum()),
                evaluation_rows=len(evaluation),
                train_recent_gap_72h=int(contexts['train'][GAP].sum()),
                evaluation_recent_gap_72h=int(contexts['evaluation'][GAP].sum()),
                evaluation_younger_than_72h=int(contexts['evaluation'][f'life__{MEASUREMENTS[0]}__change_72h'].isna().sum()))


def fit_phase(config, base, pipeline, development, life, control_folds, control_thresholds, fit=fit_probabilities):
    """Phase 1: fits and thresholds. Labels at or after each evaluation year are hidden before the fold is built."""
    budget = config['budget']['constituent_fits']
    thresholds, probabilities, coverage, fits = {}, {}, [], 0
    for year in config['years']:
        split, audit = annual_fold(blind(development, year), year)
        stored = control_folds[year]
        # The evaluation positives of the stored audit are a label count; they are compared in phase 2 only.
        if audit[:2] != stored[:2] or any(audit[2][k] != stored[2][k] for k in audit[2] if k != 'positives'):
            raise ValueError(f'Annual populations changed: {year}')
        if split['evaluation'].target.any() or max(g.prediction_end.max() for g in split.values()) > RESERVED_START:
            raise ValueError(f'Evaluation labels or reserved period reached phase 1: {year}')
        contexts = {role: life.loc[group.index] for role, group in split.items()}
        counted = fold_population(split, contexts)
        if any(counted[k] != config['population'][str(year)][k] for k in POPULATION):
            raise ValueError(f'Population or life-feature coverage differs from the protocol: {year}')
        split['evaluation'] = split['evaluation'].drop(columns=['target', 'label_status'])
        for role, context in contexts.items():
            coverage.append(dict(year=year, role=role, rows=len(context), recent_gap_72h=int(context[GAP].sum()),
                                 **{f'missing__{column}': int(context[column].isna().sum()) for column in [AGE, *PHASE_COLUMNS]}))
        y_cal = split['calibration'].target.to_numpy(dtype=np.int8)
        chosen = {'control': control_thresholds[year]}
        frame = split['evaluation'][KEY].reset_index(drop=True)
        for candidate, columns in CANDIDATES.items():
            if fits+CONSTITUENTS > budget:
                raise RuntimeError('Fit budget of the protocol would be exceeded')
            p_cal, p_eval = fit(base, split, contexts, columns)
            fits += CONSTITUENTS
            chosen[candidate] = select_thresholds(pipeline, y_cal, p_cal)
            frame[candidate] = p_eval
            gc.collect()
        frame[GAP] = contexts['evaluation'][GAP].to_numpy()
        thresholds[str(year)], probabilities[year] = chosen, frame
        print(f'{year}: alert thresholds ' + ', '.join(f'{c}={v["alert"]["threshold"]:.4f}' for c, v in chosen.items()), flush=True)
        del split, contexts
        gc.collect()
    if fits != budget:
        raise RuntimeError('Constituent fits differ from the protocol budget')
    return thresholds, probabilities, coverage, fits


def freeze_phase(output, thresholds, probabilities, coverage):
    """Write thresholds, feature lists, coverage and candidate probabilities and hash them; nothing later may change them."""
    (output/'thresholds.json').write_text(json.dumps(thresholds, indent=2)+'\n')
    (output/'features.json').write_text(json.dumps({name: [*FEATURE_COLUMNS, *columns] for name, columns in CANDIDATES.items()}, indent=2)+'\n')
    pd.DataFrame(coverage).to_csv(output/'life_coverage.csv', index=False)
    for year, frame in probabilities.items():
        frame.to_parquet(output/f'probabilities_{year}.parquet', index=False)
    manifest = {p.name: sha(p) for p in sorted(output.iterdir())}
    (output/'phase1.json').write_text(json.dumps(manifest, indent=2)+'\n')
    return manifest


def read(summary):
    """L1, L2 or L3, tried in this order; the first that holds is the reading."""
    life = summary['life_phase']
    specific = bool((life['all_year_primary'] and life['beats_age_only_all_years'])
                    or (life['cycle25_primary'] and life['cycle25_bootstrap_lower_above_zero'] and life['beats_age_only_cycle25']))
    meeting = [c for c in CANDIDATES if meets_goal(summary[c])]
    reading = READINGS[0] if specific else READINGS[1] if meeting else READINGS[2]
    return dict(reading=reading, life_phase_goal_met_and_beats_age_only=int(specific), candidates_meeting_goal_against_control=meeting,
                outcome_label=LABELS[reading])


def complete_history(frame, alarm, year, name):
    """Alert counts on evaluation windows without a stored-window gap in the last 72 hours (descriptive)."""
    kept = ~frame[GAP].to_numpy(dtype=bool)
    target = frame.target.eq(1).to_numpy()
    tp, fp, fn = (int((kept & a & b).sum()) for a, b in [(alarm, target), (alarm, ~target), (~alarm, target)])
    return dict(year=year, candidate=name, windows=int(kept.sum()), window_share=float(kept.mean()),
                positives=int((kept & target).sum()), positive_share=float((kept & target).sum()/target.sum()) if target.any() else None,
                positive_rate_with_gap=float(target[~kept].mean()) if (~kept).any() else None,
                positive_rate_without_gap=float(target[kept].mean()) if kept.any() else None,
                tp=tp, fp=fp, fn=fn, precision=tp/(tp+fp) if tp+fp else None, recall=tp/(tp+fn) if tp+fn else None)


def evaluate_phase(config, meta, control_dir, control_folds, thresholds, output):
    """Phase 2: evaluation labels are read only here, after phase 1 was written and hashed."""
    tolerance = config['acceptance']['per_year_primary']['window_recall_drop_at_most']
    names = ['control', *CANDIDATES]
    rows, intervals, complete = [], [], []
    for year in config['years']:
        split, audit = annual_fold(meta, year)
        if audit != control_folds[year]:
            raise ValueError(f'Annual populations changed: {year}')
        labels = split['evaluation'][[*KEY, 'target', 'missing_fraction']]
        stored = pd.read_parquet(control_dir/str(year)/'predictions.parquet', columns=[*KEY, 'target', 'ensemble'])
        candidate = pd.read_parquet(output/f'probabilities_{year}.parquet')
        frame = labels.merge(stored.rename(columns={'ensemble': 'control', 'target': 'stored_target'}), on=KEY, how='inner')
        frame = frame.merge(candidate, on=KEY, how='inner')
        if not len(frame) == len(labels) == len(stored) == len(candidate):
            raise ValueError(f'Evaluation keys do not match: {year}')
        if not frame.target.eq(frame.stored_target).all():
            raise ValueError(f'Stored control labels differ from the relabelled table: {year}')
        if frame.forecast_time.max() >= RESERVED_START:
            raise ValueError('Reserved period reached the evaluation')
        frame = frame.drop(columns='stored_target').sort_values(KEY).reset_index(drop=True)
        year_rows, alarms = {}, {}
        for name in names:
            scored = frame[[*KEY, 'target', 'missing_fraction']].assign(probability=frame[name])
            chosen = thresholds[str(year)][name]
            parts = decomposition(scored, chosen['watch']['threshold'])
            origin = alert_false_positive_origin(scored, chosen['alert']['threshold'])
            alarms[name] = frame[name].ge(chosen['alert']['threshold']).to_numpy()
            complete.append(complete_history(frame, alarms[name], year, name))
            for tier in TIERS:
                row = point(scored, tier, chosen[tier], year)
                row.update(candidate=name, average_precision=parts['overall_ap'], within_flaring_ap=parts['within_flaring_ap'],
                           region_ap=parts['region_ap'])
                if tier == 'alert':
                    row.update(alert_fp_share_never_flaring_harps=origin['alert_fp_share_never_flaring_harps'],
                               alert_fp_share_within_72h_of_positive=origin['alert_fp_share_within_72h_of_positive'])
                year_rows[(name, tier)] = row
        control = year_rows[('control', 'alert')]
        control['precision_at_control_recall'] = control['precision']
        for name in CANDIDATES:
            row = year_rows[(name, 'alert')]
            flags = acceptance(row, control, tolerance)
            row.update(flags)
            row['primary_met'] = bool(all(flags.values()))
            row['precision_at_control_recall'] = precision_at_recall(frame.target.to_numpy(), frame[name].to_numpy(), control['recall'])
            interval = paired_precision_bootstrap(frame, alarms['control'], alarms[name])
            intervals.append(dict(year=year, candidate=name, reference='control', metric='alert_precision_difference', **interval))
            row.update(precision_difference_lower=interval['lower'], precision_difference_upper=interval['upper'])
        life = year_rows[('life_phase', 'alert')]
        life['beats_age_only'] = bool(all(acceptance(life, year_rows[('age_only', 'alert')], tolerance).values()))
        interval = paired_precision_bootstrap(frame, alarms['age_only'], alarms['life_phase'])
        intervals.append(dict(year=year, candidate='life_phase', reference='age_only', metric='alert_precision_difference', **interval))
        life.update(precision_difference_to_age_only_lower=interval['lower'], precision_difference_to_age_only_upper=interval['upper'])
        rows.extend(year_rows.values())
        frame.to_parquet(output/f'predictions_{year}.parquet', index=False)
    table = pd.DataFrame(rows)
    table.to_csv(output/'results.csv', index=False)
    pd.DataFrame(intervals).to_csv(output/'intervals.csv', index=False)
    pd.DataFrame(complete).to_csv(output/'complete_history.csv', index=False)
    alert = table[table.tier.eq('alert')]
    summary = {name: entry(alert[alert.candidate.eq(name)].set_index('year'), None if name == 'control' else 'control') for name in names}
    beats = alert[alert.candidate.eq('life_phase')].set_index('year').beats_age_only.astype(bool)
    summary['life_phase'].update(beats_age_only_years=[int(y) for y in beats.index[beats]], beats_age_only_all_years=bool(beats.all()),
                                 beats_age_only_cycle25=bool(beats[CYCLE25].all()))
    return table, summary


def run(config_path, output, fit=fit_probabilities):
    if output.exists():
        raise FileExistsError(output)
    config = json.loads(config_path.read_text())
    check_protocol(config)
    evidence = config['evidence']
    control_dir = Path(evidence['control'])
    for path, expected in [(Path(evidence['table'])/'report.json', evidence['table_report_sha256']),
                           (control_dir/'report.json', evidence['control_report_sha256']),
                           (Path(evidence['pipeline_protocol']), evidence['pipeline_protocol_sha256']),
                           (Path(evidence['base_protocol']), evidence['base_protocol_sha256'])]:
        if sha(path) != expected:
            raise ValueError(f'Input changed: {path}')
    control_report = json.loads((control_dir/'report.json').read_text())
    control_folds = {f['year']: f['audit'] for f in control_report['folds'] if f['year'] in config['years']}
    control_thresholds = {}
    for year in config['years']:
        for name in ['thresholds.json', 'predictions.parquet']:
            if sha(control_dir/str(year)/name) != control_report['artifact_hashes'][f'{year}/{name}']:
                raise ValueError(f'Stored control file changed: {year}/{name}')
        control_thresholds[year] = json.loads((control_dir/str(year)/'thresholds.json').read_text())
    fallback = [year for year in config['years'] if control_thresholds[year]['alert']['fallback']]
    if fallback != config['alert_fallback_years']:
        raise ValueError('Stored alert fallback years differ from the protocol')
    pipeline = json.loads(Path(evidence['pipeline_protocol']).read_text())
    base = json.loads(Path(evidence['base_protocol']).read_text())
    groups, _ = load_development(Path(evidence['table']), evidence['table_report_sha256'])
    development = pd.concat(groups.values(), ignore_index=True)[[*META, *FEATURE_COLUMNS]]
    del groups
    if development.forecast_time.max() >= RESERVED_START:
        raise ValueError('Reserved period in the development table')
    # Life features come from the forecast key and six measurement summaries of all stored windows; no label column is passed.
    life = life_phase_features(development[[*KEY, *SOURCE_COLUMNS]])
    output.mkdir(parents=True)
    thresholds, probabilities, coverage, fits = fit_phase(config, base, pipeline, development, life, control_folds, control_thresholds, fit)
    meta = development[META].copy()
    del development, life
    gc.collect()
    phase1 = freeze_phase(output, thresholds, probabilities, coverage)
    del probabilities
    phase1_sha = sha(output/'phase1.json')
    table, summary = evaluate_phase(config, meta, control_dir, control_folds, thresholds, output)
    if {name: sha(output/name) for name in phase1} != phase1:
        raise RuntimeError('Phase 1 files changed after evaluation labels were read')
    decision = read(summary)
    result = {'config_sha256': sha(config_path), 'phase1_sha256': phase1_sha, 'thresholds_sha256': phase1['thresholds.json'],
              'features_sha256': phase1['features.json'], 'years': config['years'], 'alert_fallback_years_control': fallback,
              'development_basis': 'relabelled table, walk-forward-v2, operating-point-v3',
              'feature_counts': {name: len(FEATURE_COLUMNS)+len(columns) for name, columns in CANDIDATES.items()},
              'acceptance': summary, 'decision': decision, 'reading': decision['reading'], 'constituent_fits': fits,
              'reserved_test_accessed': False, 'model_promoted': False, 'threshold_adopted': False,
              'artifact_hashes': {p.name: sha(p) for p in sorted(output.iterdir())}}
    (output/'report.json').write_text(json.dumps(result, indent=2)+'\n')
    return result, table


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result, table = run(args.config, args.output)
    pd.set_option('display.width', 250)
    print(table[['year', 'candidate', 'tier', 'fallback', 'tp', 'fp', 'recall', 'precision', 'accuracy', 'always_negative_accuracy',
                 'missed_positive_runs', 'positive_runs', 'average_precision', 'within_flaring_ap']].round(4).to_string(index=False))
    print(json.dumps({'acceptance': result['acceptance'], 'decision': result['decision']}, indent=1))
