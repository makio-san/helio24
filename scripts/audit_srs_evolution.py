"""Judge the 24-hour change of the issued SRS region description at the alert tier (config/srs-evolution-v1.json).

Run once from the repository root:
    OMP_NUM_THREADS=3 python -m scripts.audit_srs_evolution --config config/srs-evolution-v1.json --output artifacts/<name>_<YYYYMMDD>_r<n>
"""
import argparse
import gc
import json
from pathlib import Path

import numpy as np
import pandas as pd

from helio24.data import FEATURE_COLUMNS
from helio24.v2_training import load_development
from helio24.walk_forward import annual_fold
from scripts.audit_activity_history_relabelled import acceptance, fit_probabilities, paired_precision_bootstrap, precision_at_recall
from scripts.audit_alarm_persistence import sha
from scripts.audit_cycle25 import decomposition
from scripts.audit_cycle25_relabelled import alert_false_positive_origin
from scripts.audit_near_miss_weighting import blind, entry, meets_goal
from scripts.audit_region_context_features import CONTEXT, attach_context, srs_feature_table
from scripts.audit_region_context_sources import SAFETY, available_srs, load_mapping, load_srs
from scripts.audit_two_tier import point
from scripts.rebuild_walk_forward_v2 import select_thresholds

KEY = ['harp', 'forecast_time']
TIERS = ['watch', 'alert']
META = [*KEY, 'observation_start', 'prediction_end', 'target', 'label_status', 'missing_fraction']
RANKS = ['zurich_rank', 'penumbra_rank', 'compact_rank', 'mag_rank']
CHANGED = [*RANKS, 'area_log', 'spots_log']
LISTED = 'evo__earlier_listed'
EVOLUTION = [LISTED, *[f'evo__{name}_change' for name in CHANGED]]
REFERENCE = EVOLUTION[1]
CANDIDATES = {'srs_static': CONTEXT, 'srs_evolution': [*CONTEXT, *EVOLUTION]}
EARLIER_MIN_HOURS, EARLIER_MAX_HOURS = 12, 36
AVAILABLE = 'evolution_available'
CONSTITUENTS = 2
CYCLE25 = [2022, 2023]
RESERVED_START = pd.Timestamp('2024-01-01', tz='UTC')
READINGS = ['S1_evolution_helps', 'S2_refit_or_static_only', 'S3_no_gain']
LABELS = {'S1_evolution_helps': 'result:goal-met', 'S2_refit_or_static_only': 'result:partial', 'S3_no_gain': 'result:no-gain'}
POPULATION = ['train_rows', 'train_positives', 'calibration_rows', 'calibration_positives', 'evaluation_rows',
              'train_srs_available', 'evaluation_srs_available', 'train_evolution_available', 'evaluation_evolution_available']
HOUR = pd.Timedelta(hours=1).value


def check_protocol(config):
    """Refuse anything but the frozen candidates, feature lists, availability rule, budget and development years."""
    if not str(config.get('status', '')).startswith('frozen_before_any') or config.get('reserved_test_accessed') is not False:
        raise ValueError('Protocol is not frozen or touches the reserved test')
    if [c['id'] for c in config['candidates']] != list(CANDIDATES):
        raise ValueError('Candidate set differs from the frozen one')
    features = config['features']
    if features['added'] != CANDIDATES or features['changed_fields'] != CHANGED:
        raise ValueError('Feature list differs from the frozen one')
    if features['earlier_product_hours'] != {'min': EARLIER_MIN_HOURS, 'max': EARLIER_MAX_HOURS}:
        raise ValueError('The earlier SRS product is fixed at 12 to 36 hours before the SRS used')
    if features['safety_margin_minutes'] != SAFETY/pd.Timedelta(minutes=1):
        raise ValueError('The availability margin is fixed at 30 minutes')
    if features['reporting_flag'] != {'name': AVAILABLE, 'model_input': False} or AVAILABLE in sum(features['added'].values(), []):
        raise ValueError('The coverage flag is reporting only')
    if pd.Timestamp(config['srs_issue_dates_before'], tz='UTC') != RESERVED_START:
        raise ValueError('SRS products are read only with issue dates before 2024-01-01')
    years = config['years']
    if years != sorted(set(years)) or any(not 2012 <= year <= 2023 for year in years):
        raise ValueError('Only development years before the reserved test are allowed')
    if not set(CYCLE25) <= set(years):
        raise ValueError('The reading needs 2022 and 2023')
    budget = config['budget']
    if budget['constituent_fits'] != len(years)*len(CANDIDATES)*CONSTITUENTS or budget['downloads'] != 0:
        raise ValueError('Fit budget differs from candidates x years x constituents, or a download is asked for')
    if not set(config['alert_fallback_years']) <= set(years):
        raise ValueError('Alert fallback years must be evaluated years')


def refuse_reserved_sources(srs_directory, mapping_directory):
    """Stop before any product file is opened when a manifest lists a product of the reserved period."""
    for record in json.loads((srs_directory/'manifest.json').read_text())['records']:
        issued = record.get('issued_utc')
        if pd.Timestamp(record['date'], tz='UTC') >= RESERVED_START or (issued and pd.Timestamp(issued) >= RESERVED_START):
            raise ValueError(f'SRS product at or after 2024-01-01 in the source directory: {record["file"]}')
    for record in json.loads((mapping_directory/'manifest.json').read_text())['records']:
        if pd.Timestamp(f'{record["month"]}-01', tz='UTC') >= RESERVED_START:
            raise ValueError(f'HARP to NOAA month at or after 2024-01 in the source directory: {record["file"]}')


def load_sources(srs_directory, mapping_directory):
    """Issue times, encoded SRS rows and the HARP to NOAA mapping, none of them from the reserved period."""
    refuse_reserved_sources(srs_directory, mapping_directory)
    issued, rows, _ = load_srs(srs_directory)
    mapping, _, _ = load_mapping(mapping_directory)
    if issued.issued_utc.max() >= RESERVED_START or rows.issued_utc.max() >= RESERVED_START:
        raise ValueError('SRS product issued at or after 2024-01-01')
    if pd.Timestamp(mapping.date.max(), tz='UTC') >= RESERVED_START:
        raise ValueError('HARP to NOAA mapping at or after 2024-01-01')
    table = srs_feature_table(rows)
    if table.duplicated(['issued_utc', 'noaa']).any():
        raise ValueError('An SRS product lists a NOAA number twice')
    return issued, table, mapping


def _ns(times):
    return pd.to_datetime(pd.Series(np.asarray(times, dtype=object)), utc=True).to_numpy(dtype='datetime64[ns]').astype('int64')


def earlier_srs(issued, used):
    """For each SRS used, the latest SRS issued 12 to 36 hours before it (NaT if none, or if no SRS was used)."""
    order = np.sort(_ns(issued))
    known = pd.notna(pd.Series(np.asarray(used, dtype=object))).to_numpy()
    moment = np.where(known, _ns(used), 0)
    index = np.searchsorted(order, moment-EARLIER_MIN_HOURS*HOUR, side='right')-1
    valid = known & (index >= 0)
    valid[valid] = order[index[valid]] >= moment[valid]-EARLIER_MAX_HOURS*HOUR
    out = pd.Series(pd.NaT, index=range(len(moment)), dtype='datetime64[ns, UTC]')
    out[valid] = pd.to_datetime(order[index[valid]], utc=True)
    return out


def check_availability(forecast_time, used, earlier):
    """Both SRS products of a difference were issued at or before the forecast time minus 30 minutes."""
    forecast, now, before = (pd.Series(_ns(v)) for v in [forecast_time, used, earlier])
    has_now, has_before = pd.notna(pd.Series(np.asarray(used, dtype=object))), pd.notna(pd.Series(np.asarray(earlier, dtype=object)))
    cutoff = forecast-SAFETY.value
    if (now[has_now] > cutoff[has_now]).any() or (before[has_before] > cutoff[has_before]).any():
        raise ValueError('An SRS product issued after the forecast time minus 30 minutes reached a feature')
    if (has_before & ~has_now).any() or (before[has_before] >= now[has_before]).any():
        raise ValueError('The earlier SRS product is not earlier than the SRS used')
    if len(forecast) and (forecast.max() >= RESERVED_START.value or (has_now.any() and now[has_now].max() >= RESERVED_START.value)):
        raise ValueError('Reserved period reached the SRS features')


def attach_evolution(frame, mapping, issued, table):
    """Change of the matched SRS rows against the SRS issued one day earlier, over the NOAA numbers listed in both.

    The SRS used and the HARP's NOAA numbers are those of scripts.audit_region_context_features.attach_context.
    A window without an SRS row, or without an earlier product, has every value missing; a window whose NOAA
    numbers are all absent from the earlier product has LISTED 0 and every change missing, never zero.
    """
    forbidden = {'target', 'label_status', 'label_status_v2', 'role'} & set(frame.columns)
    if forbidden:
        raise ValueError(f'SRS features never see labels, label status or roles: {sorted(forbidden)}')
    base = frame[KEY].copy().reset_index(drop=True)
    base['forecast_time'] = pd.to_datetime(base.forecast_time, utc=True)
    base['date'] = base.forecast_time.dt.date
    base['used'] = available_srs(issued.issued_utc, base.forecast_time).to_numpy()
    base['earlier'] = earlier_srs(issued.issued_utc, base.used).to_numpy()
    check_availability(base.forecast_time, base.used, base.earlier)
    values = table[['issued_utc', 'noaa', *RANKS, 'area', 'nn']].copy()
    for part, columns in [(base, ['used', 'earlier']), (values, ['issued_utc'])]:
        for column in columns:
            part[column] = pd.to_datetime(part[column], utc=True).astype('datetime64[ns, UTC]')
    merged = base.reset_index().merge(mapping, on=['harp', 'date'], how='inner')
    now = merged.merge(values, left_on=['used', 'noaa'], right_on=['issued_utc', 'noaa'], how='inner').drop(columns='issued_utc')
    both = now.merge(values, left_on=['earlier', 'noaa'], right_on=['issued_utc', 'noaa'], how='inner', suffixes=('', '_earlier'))
    names = [*RANKS, 'area', 'nn']
    agg = both.groupby('index').agg(**{name: (name, 'max' if name in RANKS else 'sum') for name in names},
                                    **{f'{name}_earlier': (f'{name}_earlier', 'max' if name in RANKS else 'sum') for name in names})
    out = pd.DataFrame(index=base.index)
    comparable = out.index.isin(now['index']) & base.earlier.notna().to_numpy()
    out[LISTED] = np.where(comparable, out.index.isin(agg.index).astype(float), np.nan)
    for name in RANKS:
        out[f'evo__{name}_change'] = (agg[name]-agg[f'{name}_earlier']).reindex(out.index).astype(float)
    for name, source in [('area_log', 'area'), ('spots_log', 'nn')]:
        change = np.log1p(agg[source].astype(float))-np.log1p(agg[f'{source}_earlier'].astype(float))
        out[f'evo__{name}_change'] = change.reindex(out.index)
    out = out[EVOLUTION]
    out.index = frame.index
    return out


def srs_features(windows, mapping, issued, table):
    """The 13 static context features, the 7 evolution features and the reporting flag AVAILABLE for every window."""
    keys = windows[KEY]
    static = attach_context(keys, mapping, issued, table)
    evolution = attach_evolution(keys, mapping, issued, table)
    if (evolution[LISTED].notna() & static.srs_available.ne(1)).any() or (evolution[EVOLUTION[1:]].notna().any(axis=1) & evolution[LISTED].ne(1)).any():
        raise ValueError('Evolution values without a matched SRS row in both products')
    features = pd.concat([static, evolution], axis=1)
    features[AVAILABLE] = evolution[REFERENCE].notna()
    return features


def fold_population(split, contexts):
    """Label counts of the training and calibration roles and label-free coverage counts of the SRS features."""
    train, calibration, evaluation = split['train'], split['calibration'], split['evaluation']
    return dict(train_rows=len(train), train_positives=int(train.target.sum()),
                calibration_rows=len(calibration), calibration_positives=int(calibration.target.sum()),
                evaluation_rows=len(evaluation),
                train_srs_available=int(contexts['train'].srs_available.sum()),
                evaluation_srs_available=int(contexts['evaluation'].srs_available.sum()),
                train_evolution_available=int(contexts['train'][AVAILABLE].sum()),
                evaluation_evolution_available=int(contexts['evaluation'][AVAILABLE].sum()))


def fit_phase(config, base, pipeline, development, features, control_folds, control_thresholds, fit=fit_probabilities):
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
        contexts = {role: features.loc[group.index] for role, group in split.items()}
        counted = fold_population(split, contexts)
        if any(counted[k] != config['population'][str(year)][k] for k in POPULATION):
            raise ValueError(f'Population or SRS coverage differs from the protocol: {year}')
        split['evaluation'] = split['evaluation'].drop(columns=['target', 'label_status'])
        for role, context in contexts.items():
            coverage.append(dict(year=year, role=role, rows=len(context), srs_available=int(context.srs_available.sum()),
                                 evolution_available=int(context[AVAILABLE].sum()),
                                 earlier_listed=int(context[LISTED].eq(1).sum()), earlier_not_listed=int(context[LISTED].eq(0).sum()),
                                 **{f'missing__{column}': int(context[column].isna().sum()) for column in EVOLUTION}))
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
        frame[AVAILABLE] = contexts['evaluation'][AVAILABLE].to_numpy()
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
    pd.DataFrame(coverage).to_csv(output/'srs_coverage.csv', index=False)
    for year, frame in probabilities.items():
        frame.to_parquet(output/f'probabilities_{year}.parquet', index=False)
    manifest = {p.name: sha(p) for p in sorted(output.iterdir())}
    (output/'phase1.json').write_text(json.dumps(manifest, indent=2)+'\n')
    return manifest


def read(summary):
    """S1, S2 or S3, tried in this order; the first that holds is the reading."""
    evolution = summary['srs_evolution']
    specific = bool((evolution['all_year_primary'] and evolution['beats_srs_static_all_years'])
                    or (evolution['cycle25_primary'] and evolution['cycle25_bootstrap_lower_above_zero']
                        and evolution['beats_srs_static_cycle25']))
    meeting = [c for c in CANDIDATES if meets_goal(summary[c])]
    reading = READINGS[0] if specific else READINGS[1] if meeting else READINGS[2]
    return dict(reading=reading, srs_evolution_goal_met_and_beats_srs_static=int(specific), candidates_meeting_goal_against_control=meeting,
                outcome_label=LABELS[reading])


def evolution_subset(frame, alarm, year, name, available):
    """Alert counts on the evaluation windows with, or without, a computable 24-hour change (descriptive)."""
    kept = frame[AVAILABLE].to_numpy(dtype=bool) == available
    target = frame.target.eq(1).to_numpy()
    tp, fp, fn = (int((kept & a & b).sum()) for a, b in [(alarm, target), (alarm, ~target), (~alarm, target)])
    return dict(year=year, candidate=name, subset='change_available' if available else 'change_missing', windows=int(kept.sum()),
                window_share=float(kept.mean()), positives=int((kept & target).sum()),
                positive_share=float((kept & target).sum()/target.sum()) if target.any() else None,
                tp=tp, fp=fp, fn=fn, precision=tp/(tp+fp) if tp+fp else None, recall=tp/(tp+fn) if tp+fn else None)


def evaluate_phase(config, meta, control_dir, control_folds, thresholds, output):
    """Phase 2: evaluation labels are read only here, after phase 1 was written and hashed."""
    tolerance = config['acceptance']['per_year_primary']['window_recall_drop_at_most']
    names = ['control', *CANDIDATES]
    rows, intervals, subsets = [], [], []
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
            subsets.extend(evolution_subset(frame, alarms[name], year, name, available) for available in [True, False])
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
        evolution = year_rows[('srs_evolution', 'alert')]
        evolution['beats_srs_static'] = bool(all(acceptance(evolution, year_rows[('srs_static', 'alert')], tolerance).values()))
        interval = paired_precision_bootstrap(frame, alarms['srs_static'], alarms['srs_evolution'])
        intervals.append(dict(year=year, candidate='srs_evolution', reference='srs_static', metric='alert_precision_difference', **interval))
        evolution.update(precision_difference_to_srs_static_lower=interval['lower'], precision_difference_to_srs_static_upper=interval['upper'])
        rows.extend(year_rows.values())
        frame.to_parquet(output/f'predictions_{year}.parquet', index=False)
    table = pd.DataFrame(rows)
    table.to_csv(output/'results.csv', index=False)
    pd.DataFrame(intervals).to_csv(output/'intervals.csv', index=False)
    pd.DataFrame(subsets).to_csv(output/'evolution_subset.csv', index=False)
    alert = table[table.tier.eq('alert')]
    summary = {name: entry(alert[alert.candidate.eq(name)].set_index('year'), None if name == 'control' else 'control') for name in names}
    beats = alert[alert.candidate.eq('srs_evolution')].set_index('year').beats_srs_static.astype(bool)
    summary['srs_evolution'].update(beats_srs_static_years=[int(y) for y in beats.index[beats]], beats_srs_static_all_years=bool(beats.all()),
                                    beats_srs_static_cycle25=bool(beats[CYCLE25].all()))
    return table, summary


def run(config_path, output, fit=fit_probabilities):
    if output.exists():
        raise FileExistsError(output)
    config = json.loads(config_path.read_text())
    check_protocol(config)
    evidence = config['evidence']
    control_dir, srs_dir, mapping_dir = Path(evidence['control']), Path(evidence['srs_directory']), Path(evidence['mapping_directory'])
    for path, expected in [(Path(evidence['table'])/'report.json', evidence['table_report_sha256']),
                           (control_dir/'report.json', evidence['control_report_sha256']),
                           (Path(evidence['pipeline_protocol']), evidence['pipeline_protocol_sha256']),
                           (Path(evidence['base_protocol']), evidence['base_protocol_sha256']),
                           (srs_dir/'manifest.json', evidence['srs_manifest_sha256']),
                           (mapping_dir/'manifest.json', evidence['mapping_manifest_sha256'])]:
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
    # The manifests are checked for reserved products before any SRS or mapping file is opened.
    issued, srs_table, mapping = load_sources(srs_dir, mapping_dir)
    groups, _ = load_development(Path(evidence['table']), evidence['table_report_sha256'])
    development = pd.concat(groups.values(), ignore_index=True)[[*META, *FEATURE_COLUMNS]]
    del groups
    if development.forecast_time.max() >= RESERVED_START:
        raise ValueError('Reserved period in the development table')
    # SRS features come from the forecast key, the issued SRS and the HARP to NOAA mapping; no label column is passed.
    features = srs_features(development[KEY], mapping, issued, srs_table)
    del issued, srs_table, mapping
    output.mkdir(parents=True)
    thresholds, probabilities, coverage, fits = fit_phase(config, base, pipeline, development, features, control_folds, control_thresholds, fit)
    meta = development[META].copy()
    del development, features
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
              'srs_issue_dates_before': config['srs_issue_dates_before'],
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
