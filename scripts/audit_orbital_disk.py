"""Orbital phase and disk position systematics of the SHARP summaries at the alert tier (config/orbital-disk-v1.json).

Run once from the repository root:
    OMP_NUM_THREADS=3 python -m scripts.audit_orbital_disk --config config/orbital-disk-v1.json --output artifacts/<name>_<YYYYMMDD>_r<n>
"""
import argparse
import gc
import json
from pathlib import Path

import numpy as np
import pandas as pd

from helio24.data import FEATURE_COLUMNS
from helio24.orbital_disk import (BAND, BANDS, FLAG, KEY, ORBITAL, PERIODS_HOURS, POSITION, ROTATION_DEG_PER_DAY, SAFETY, SIDE, SIDES,
                                  disk_position_features, orbital_phase_features, srs_positions, utc_hour)
from helio24.v2_training import load_development
from helio24.walk_forward import annual_fold
from scripts.audit_activity_history_relabelled import acceptance, fit_probabilities, paired_precision_bootstrap, precision_at_recall
from scripts.audit_alarm_persistence import sha
from scripts.audit_cycle25 import decomposition
from scripts.audit_cycle25_relabelled import alert_false_positive_origin
from scripts.audit_near_miss_weighting import blind, entry, meets_goal
from scripts.audit_region_context_sources import load_mapping, load_srs
from scripts.audit_two_tier import point
from scripts.rebuild_walk_forward_v2 import select_thresholds

TIERS = ['watch', 'alert']
META = [*KEY, 'observation_start', 'prediction_end', 'target', 'label_status', 'missing_fraction']
CANDIDATES = {'srs_flag': [FLAG], 'orbital_phase': ORBITAL, 'disk_position': POSITION, 'both': [*ORBITAL, *POSITION]}
FLAG_REFERENCE = 'srs_flag'
POSITION_CANDIDATES = ['disk_position', 'both']
CONSTITUENTS = 2
CYCLE25 = [2022, 2023]
RESERVED_START = pd.Timestamp('2024-01-01', tz='UTC')
READINGS = ['S1_systematics_help', 'S2_refit_or_flag_only', 'S3_no_gain']
LABELS = {'S1_systematics_help': 'result:goal-met', 'S2_refit_or_flag_only': 'result:partial', 'S3_no_gain': 'result:no-gain'}
POPULATION = ['train_rows', 'train_positives', 'calibration_rows', 'calibration_positives', 'evaluation_rows',
              'train_srs_located', 'calibration_srs_located', 'evaluation_srs_located', 'train_positives_srs_located']
CALENDAR_WORDS = ['date', 'day', 'doy', 'month', 'year', 'calendar', 'season']
REPORTING_ONLY = [BAND, SIDE]


def check_protocol(config):
    """Refuse anything but the frozen candidates, feature lists, rules, budget and development years."""
    if not str(config.get('status', '')).startswith('frozen_before_any') or config.get('reserved_test_accessed') is not False:
        raise ValueError('Protocol is not frozen or touches the reserved test')
    if [c['id'] for c in config['candidates']] != list(CANDIDATES):
        raise ValueError('Candidate set differs from the frozen one')
    features = config['features']
    if features['added'] != CANDIDATES:
        raise ValueError('Feature list differs from the frozen one')
    added = sum(features['added'].values(), [])
    if any(word in column.lower() for column in added for word in CALENDAR_WORDS):
        raise ValueError('No date, day-of-year or other calendar feature may enter a model')
    if set(REPORTING_ONLY) & set(added) or features['reporting_only'] != {'columns': REPORTING_ONLY, 'model_input': False}:
        raise ValueError('Disk bands and sides are reporting only')
    if features['orbital']['periods_hours'] != PERIODS_HOURS:
        raise ValueError('Orbital periods are fixed')
    disk = features['disk']
    if disk['rotation_deg_per_day'] != ROTATION_DEG_PER_DAY or disk['availability_safety_minutes'] != SAFETY.total_seconds()/60:
        raise ValueError('Rotation rate and SRS availability rule are fixed')
    if disk['bands'] != BANDS or disk['sides'] != SIDES:
        raise ValueError('Reporting bands are fixed')
    if config['descriptive']['feeds_rule'] is not False:
        raise ValueError('The descriptive part never feeds a rule')
    years = config['years']
    if years != sorted(set(years)) or any(not 2012 <= year <= 2023 for year in years):
        raise ValueError('Only development years before the reserved test are allowed')
    if not set(CYCLE25) <= set(years):
        raise ValueError('The reading needs 2022 and 2023')
    if config['budget']['constituent_fits'] != len(years)*len(CANDIDATES)*CONSTITUENTS:
        raise ValueError('Fit budget differs from candidates x years x constituents')
    if not set(config['alert_fallback_years']) <= set(years):
        raise ValueError('Alert fallback years must be evaluated years')


def check_sources(evidence, sources):
    """Source manifests must be the hashed ones and hold nothing at or after 2024-01-01; checked before any SRS file is read."""
    for key in ['srs', 'mapping']:
        manifest_path = Path(evidence[f'{key}_directory'])/'manifest.json'
        if sha(manifest_path) != evidence[f'{key}_manifest_sha256']:
            raise ValueError(f'Source manifest changed: {manifest_path}')
        manifest = json.loads(manifest_path.read_text())
        dates = [r.get('date') or r.get('month') for r in manifest['records']]
        if max(manifest['period']) >= '2024-01-01' or max(dates) >= '2024-01':
            raise ValueError(f'Source reaches the reserved period: {manifest_path}')
    issued, rows, problems = load_srs(Path(evidence['srs_directory']))
    mapping, mapping_problems, _ = load_mapping(Path(evidence['mapping_directory']))
    counted = dict(srs_products=len(issued), srs_rows=len(rows), srs_problems=problems, mapping_problems=mapping_problems)
    if counted != sources['counts'] or issued.issued_utc.max() >= RESERVED_START:
        raise ValueError('Source counts differ from the protocol or reach the reserved period')
    return issued, rows, mapping


def context_features(keys, mapping, issued, rows):
    """Orbital and disk features (and the reporting-only band and side) of all stored windows, from keys and sources only."""
    return pd.concat([orbital_phase_features(keys), disk_position_features(keys, mapping, issued, srs_positions(issued, rows))], axis=1)


def fold_population(split, contexts):
    """Label counts of the training and calibration roles and label-free SRS location coverage of every role."""
    train, calibration, evaluation = split['train'], split['calibration'], split['evaluation']
    located = {role: contexts[role][FLAG].eq(1) for role in split}
    return dict(train_rows=len(train), train_positives=int(train.target.sum()),
                calibration_rows=len(calibration), calibration_positives=int(calibration.target.sum()),
                evaluation_rows=len(evaluation),
                train_srs_located=int(located['train'].sum()), calibration_srs_located=int(located['calibration'].sum()),
                evaluation_srs_located=int(located['evaluation'].sum()),
                train_positives_srs_located=int((train.target.eq(1) & located['train']).sum()))


def fit_phase(config, base, pipeline, development, context, control_folds, control_thresholds, fit=fit_probabilities):
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
        contexts = {role: context.loc[group.index] for role, group in split.items()}
        counted = fold_population(split, contexts)
        if any(counted[k] != config['population'][str(year)][k] for k in POPULATION):
            raise ValueError(f'Population or SRS location coverage differs from the protocol: {year}')
        split['evaluation'] = split['evaluation'].drop(columns=['target', 'label_status'])
        for role, part in contexts.items():
            coverage.append(dict(year=year, role=role, rows=len(part), srs_located=int(part[FLAG].sum()),
                                 **{f'band__{b}': int(part[BAND].eq(b).sum()) for b in BANDS},
                                 **{f'missing__{c}': int(part[c].isna().sum()) for c in [*ORBITAL, *POSITION]}))
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
        for column in REPORTING_ONLY:
            frame[column] = contexts['evaluation'][column].to_numpy()
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
    pd.DataFrame(coverage).to_csv(output/'disk_coverage.csv', index=False)
    for year, frame in probabilities.items():
        frame.to_parquet(output/f'probabilities_{year}.parquet', index=False)
    manifest = {p.name: sha(p) for p in sorted(output.iterdir())}
    (output/'phase1.json').write_text(json.dumps(manifest, indent=2)+'\n')
    return manifest


def on_path(entry_, beats_all, beats_cycle25):
    """Goal against control by a path, with the reference beaten in every year of that same path."""
    return bool((entry_['all_year_primary'] and beats_all) or
                (entry_['cycle25_primary'] and entry_['cycle25_bootstrap_lower_above_zero'] and beats_cycle25))


def read(summary):
    """S1, S2 or S3, tried in this order; the first that holds is the reading. Only alert acceptance flags enter it."""
    effects = {'orbital_phase': meets_goal(summary['orbital_phase'])}
    for name in POSITION_CANDIDATES:
        part = summary[name]
        effects[name] = on_path(part, part['beats_srs_flag_all_years'], part['beats_srs_flag_cycle25'])
    met = [name for name in ['orbital_phase', *POSITION_CANDIDATES] if effects[name]]
    meeting = [c for c in CANDIDATES if meets_goal(summary[c])]
    reading = READINGS[0] if met else READINGS[1] if meeting else READINGS[2]
    return dict(reading=reading, systematics_effects_met=len(met), effects_met=met, candidates_meeting_goal_against_control=meeting,
                outcome_label=LABELS[reading])


def group_counts(frame, alarm, year, name, grouping, groups):
    """Alert TP, FP, FN, precision and recall per group (descriptive; uses evaluation labels and never feeds a rule)."""
    target = frame.target.eq(1).to_numpy()
    rows = []
    for group in groups:
        kept = (frame[grouping].astype(str) == str(group)).to_numpy()
        tp, fp, fn = (int((kept & a & b).sum()) for a, b in [(alarm, target), (alarm, ~target), (~alarm, target)])
        rows.append(dict(year=year, candidate=name, grouping=grouping, group=group, windows=int(kept.sum()),
                         positives=int((kept & target).sum()), tp=tp, fp=fp, fn=fn,
                         precision=tp/(tp+fp) if tp+fp else None, recall=tp/(tp+fn) if tp+fn else None))
    return rows


def _within(values, harps):
    return values-pd.DataFrame(values).groupby(harps).transform('mean').to_numpy()


def periodicity(frame, column, year, name):
    """Within-HARP share of the variance of the logit explained by 24 and 12 hour harmonics of the UTC hour (label-free)."""
    p = np.clip(frame[column].to_numpy(dtype=float), 1e-9, 1-1e-9)
    logit = np.log(p/(1-p))
    harps = frame.harp.to_numpy()
    hour = utc_hour(frame.forecast_time)
    harmonics = {period: np.column_stack([np.sin(2*np.pi*hour/period), np.cos(2*np.pi*hour/period)]) for period in PERIODS_HOURS}
    y = _within(logit[:, None], harps)[:, 0]
    total, overall = float((y**2).sum()), float(((logit-logit.mean())**2).sum())
    if total <= 1e-12*max(overall, 1.0):
        total = 0.0
    row = dict(year=year, candidate=name, windows=len(frame), harps=int(pd.Series(harps).nunique()),
               within_harp_share_of_total_variance=total/overall if overall else None)
    for label, x in [('24h', harmonics[24]), ('12h', harmonics[12]), ('24h_and_12h', np.hstack([harmonics[24], harmonics[12]]))]:
        xd = _within(x, harps)
        beta = np.linalg.lstsq(xd, y, rcond=None)[0]
        row[f'within_harp_share_{label}'] = 1-float(((y-xd@beta)**2).sum())/total if total else None
    return row


def evaluate_phase(config, meta, control_dir, control_folds, thresholds, output):
    """Phase 2: evaluation labels are read only here, after phase 1 was written and hashed."""
    tolerance = config['acceptance']['per_year_primary']['window_recall_drop_at_most']
    names = ['control', *CANDIDATES]
    rows, intervals, groups, periodic = [], [], [], []
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
        frame['utc_hour'] = np.floor(utc_hour(frame.forecast_time)).astype(int)
        year_rows, alarms = {}, {}
        for name in names:
            scored = frame[[*KEY, 'target', 'missing_fraction']].assign(probability=frame[name])
            chosen = thresholds[str(year)][name]
            parts = decomposition(scored, chosen['watch']['threshold'])
            origin = alert_false_positive_origin(scored, chosen['alert']['threshold'])
            alarms[name] = frame[name].ge(chosen['alert']['threshold']).to_numpy()
            groups.extend(group_counts(frame, alarms[name], year, name, 'utc_hour', range(24)))
            groups.extend(group_counts(frame, alarms[name], year, name, BAND, BANDS))
            groups.extend(group_counts(frame, alarms[name], year, name, SIDE, SIDES))
            periodic.append(periodicity(frame, name, year, name))
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
        for name in POSITION_CANDIDATES:
            row = year_rows[(name, 'alert')]
            row['beats_srs_flag'] = bool(all(acceptance(row, year_rows[(FLAG_REFERENCE, 'alert')], tolerance).values()))
            interval = paired_precision_bootstrap(frame, alarms[FLAG_REFERENCE], alarms[name])
            intervals.append(dict(year=year, candidate=name, reference=FLAG_REFERENCE, metric='alert_precision_difference', **interval))
            row.update(precision_difference_to_srs_flag_lower=interval['lower'], precision_difference_to_srs_flag_upper=interval['upper'])
        rows.extend(year_rows.values())
        frame.to_parquet(output/f'predictions_{year}.parquet', index=False)
    table = pd.DataFrame(rows)
    table.to_csv(output/'results.csv', index=False)
    pd.DataFrame(intervals).to_csv(output/'intervals.csv', index=False)
    grouped = pd.DataFrame(groups)
    grouped[grouped.grouping.eq('utc_hour')].to_csv(output/'by_hour.csv', index=False)
    grouped[grouped.grouping.isin([BAND, SIDE])].to_csv(output/'by_disk.csv', index=False)
    pd.DataFrame(periodic).to_csv(output/'logit_periodicity.csv', index=False)
    alert = table[table.tier.eq('alert')]
    summary = {name: entry(alert[alert.candidate.eq(name)].set_index('year'), None if name == 'control' else 'control') for name in names}
    for name in POSITION_CANDIDATES:
        beats = alert[alert.candidate.eq(name)].set_index('year').beats_srs_flag.astype(bool)
        summary[name].update(beats_srs_flag_years=[int(y) for y in beats.index[beats]], beats_srs_flag_all_years=bool(beats.all()),
                             beats_srs_flag_cycle25=bool(beats[CYCLE25].all()))
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
                           (Path(evidence['base_protocol']), evidence['base_protocol_sha256']),
                           (Path(evidence['availability_protocol']), evidence['availability_protocol_sha256'])]:
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
    issued, rows, mapping = check_sources(evidence, config['sources'])
    pipeline = json.loads(Path(evidence['pipeline_protocol']).read_text())
    base = json.loads(Path(evidence['base_protocol']).read_text())
    groups, _ = load_development(Path(evidence['table']), evidence['table_report_sha256'])
    development = pd.concat(groups.values(), ignore_index=True)[[*META, *FEATURE_COLUMNS]]
    del groups
    if development.forecast_time.max() >= RESERVED_START:
        raise ValueError('Reserved period in the development table')
    # Orbital and disk features come from the forecast keys and the SRS sources of all stored windows; no label column is passed.
    context = context_features(development[KEY], mapping, issued, rows)
    output.mkdir(parents=True)
    thresholds, probabilities, coverage, fits = fit_phase(config, base, pipeline, development, context, control_folds, control_thresholds, fit)
    meta = development[META].copy()
    del development, context
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
              'descriptive_feeds_rule': False, 'reserved_test_accessed': False, 'model_promoted': False, 'threshold_adopted': False,
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
