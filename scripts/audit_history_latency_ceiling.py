"""Zero-latency regional flare history as an optimistic ceiling at the alert tier (config/history-latency-ceiling-v1.json)."""
import argparse
import gc
import json
from pathlib import Path
import re

import numpy as np
import pandas as pd

from helio24.full_data import sha256
from helio24.v2_training import load_development
from helio24.walk_forward import annual_fold
from scripts.audit_activity_history import XRAY, log_flux
from scripts.audit_activity_history_relabelled import (KEY, TIERS, acceptance, fit_probabilities, paired_precision_bootstrap,
                                                       precision_at_recall)
from scripts.audit_alarm_persistence import sha
from scripts.audit_cycle25 import decomposition
from scripts.audit_cycle25_relabelled import alert_false_positive_origin
from scripts.audit_region_context_sources import ISSUED, SAFETY, load_mapping
from scripts.audit_two_tier import point
from scripts.rebuild_walk_forward_v2 import select_thresholds

FEATURES = ['event_available', 'reg_mx_6h', 'reg_mx_12h', 'reg_mx_24h', 'reg_mx_72h', 'reg_c_24h', 'reg_c_72h', 'reg_events_24h',
            'reg_max_logflux_24h', 'reg_max_logflux_72h', 'reg_hours_since_mx', 'reg_hours_since_event', 'reg_mx_life',
            'reg_max_logflux_life', 'disk_mx_24h', 'disk_max_logflux_24h']
HOUR = 3_600_000_000_000
CLOCK = re.compile(r'\d{4}')


def parse_event_times(text):
    """Section A rows of one SGAS product with the event time (End, else Max, else Begin) on the UT day before issue."""
    match = ISSUED.search(text)
    if not match:
        return []
    day = pd.Timestamp(pd.to_datetime(match.group(1), format='%Y %b %d %H%M'), tz='UTC').normalize()-pd.Timedelta('1D')
    rows, in_section = [], False
    for line in text.splitlines():
        if line.startswith('A.'):
            in_section = True
            continue
        if line.startswith('B.'):
            in_section = False
        if not in_section or line.startswith('Begin') or not line.strip() or line.strip().lower() == 'none':
            continue
        padded = line.ljust(34)
        begin, peak, end = padded[1:5], padded[6:10], padded[11:15]
        region, xray = padded[16:21].strip(), XRAY.match(padded[28:33].strip())
        if not CLOCK.fullmatch(begin) or (region and not region.isdigit()):
            continue
        chosen = next((value for value in [end, peak, begin] if CLOCK.fullmatch(value)), begin)
        minutes = int(chosen[:2])*60+int(chosen[2:])
        if minutes < int(begin[:2])*60+int(begin[2:]):
            minutes += 1440
        noaa = int(region) if region else None
        if noaa is not None and noaa < 5000:
            noaa += 10000
        rows.append({'event_time': day+pd.Timedelta(minutes=minutes), 'noaa': noaa,
                     'logflux': log_flux(*xray.groups()) if xray else np.nan})
    return rows


def load_events(directory):
    manifest = json.loads((directory/'manifest.json').read_text())
    rows = []
    for record in manifest['records']:
        if record['status'] != 'ok':
            continue
        path = directory/record['file']
        if sha256(path) != record['sha256']:
            raise ValueError(f'SGAS file changed: {record["file"]}')
        rows.extend(parse_event_times(path.read_text(errors='replace')))
    events = pd.DataFrame(rows).sort_values('event_time').reset_index(drop=True)
    events['ns'] = events.event_time.astype('datetime64[ns, UTC]').astype('int64')
    return events


def _range_max(values, lo, hi):
    return np.array([values[a:b].max() if b > a else -np.inf for a, b in zip(lo, hi)])


def attach_event_history(frame, mapping, events):
    """Zero-latency history: events whose event time is <= t - 30 min, whatever the issue time. Not deployable."""
    base = frame[KEY].copy().reset_index(drop=True)
    base['forecast_time'] = pd.to_datetime(base.forecast_time, utc=True)
    cutoff = (base.forecast_time-SAFETY).astype('datetime64[ns, UTC]').astype('int64').to_numpy()
    margin = int(SAFETY.total_seconds()*1e9)
    out = pd.DataFrame(index=base.index)
    classed = events[events.logflux.notna()]
    times, flux = classed.ns.to_numpy(), classed.logflux.to_numpy()
    mx = np.concatenate([[0], np.cumsum(flux >= -5)])
    hi, lo = np.searchsorted(times, cutoff, side='right'), np.searchsorted(times, cutoff-24*HOUR, side='right')
    out['disk_mx_24h'] = (mx[hi]-mx[lo]).astype(float)
    best = _range_max(flux, lo, hi)
    out['disk_max_logflux_24h'] = np.where(np.isfinite(best), best, np.nan)
    base['date'] = base.forecast_time.dt.date
    pairs = base.reset_index()[['index', 'harp', 'date']].merge(mapping[['harp', 'date', 'noaa']], on=['harp', 'date'])
    numbered = np.zeros(len(base), dtype=bool)
    numbered[pairs['index'].unique()] = True
    counts = ['reg_mx_6h', 'reg_mx_12h', 'reg_mx_24h', 'reg_mx_72h', 'reg_c_24h', 'reg_c_72h', 'reg_events_24h', 'reg_mx_life']
    sums = {name: np.zeros(len(base)) for name in counts}
    best24, best72, best_life = (np.full(len(base), -np.inf) for _ in range(3))
    last_mx, last_event = np.full(len(base), np.inf), np.full(len(base), np.inf)
    regional = {noaa: group for noaa, group in events.dropna(subset=['noaa']).groupby('noaa')}
    for noaa, rows in pairs.groupby('noaa'):
        group = regional.get(noaa)
        if group is None:
            continue
        index = rows['index'].to_numpy()
        cut = cutoff[index]
        times, flux = group.ns.to_numpy(), group.logflux.to_numpy()
        is_c = np.concatenate([[0], np.cumsum((flux >= -6) & (flux < -5))])
        is_mx = np.concatenate([[0], np.cumsum(flux >= -5)])
        every = np.arange(len(times)+1)
        hi = np.searchsorted(times, cut, side='right')
        lo = {hours: np.searchsorted(times, cut-hours*HOUR, side='right') for hours in [6, 12, 24, 72]}
        for hours in [6, 12, 24, 72]:
            np.add.at(sums[f'reg_mx_{hours}h'], index, is_mx[hi]-is_mx[lo[hours]])
        np.add.at(sums['reg_c_24h'], index, is_c[hi]-is_c[lo[24]])
        np.add.at(sums['reg_c_72h'], index, is_c[hi]-is_c[lo[72]])
        np.add.at(sums['reg_events_24h'], index, every[hi]-every[lo[24]])
        np.add.at(sums['reg_mx_life'], index, is_mx[hi])
        filled = np.where(np.isnan(flux), -np.inf, flux)
        np.maximum.at(best24, index, _range_max(filled, lo[24], hi))
        np.maximum.at(best72, index, _range_max(filled, lo[72], hi))
        np.maximum.at(best_life, index, np.concatenate([[-np.inf], np.maximum.accumulate(filled)])[hi])
        mx_times = times[flux >= -5]
        position = np.searchsorted(mx_times, cut, side='right')
        since_mx = np.where(position > 0, (cut-mx_times[np.maximum(position-1, 0)]+margin)/HOUR, np.inf) if len(mx_times) else np.full(len(cut), np.inf)
        since_event = np.where(hi > 0, (cut-times[np.maximum(hi-1, 0)]+margin)/HOUR, np.inf)
        np.minimum.at(last_mx, index, since_mx)
        np.minimum.at(last_event, index, since_event)
    out['event_available'] = numbered.astype(float)
    for name in counts:
        out[name] = np.where(numbered, sums[name], np.nan)
    for name, values in [('reg_max_logflux_24h', best24), ('reg_max_logflux_72h', best72), ('reg_max_logflux_life', best_life),
                         ('reg_hours_since_mx', last_mx), ('reg_hours_since_event', last_event)]:
        out[name] = np.where(numbered & np.isfinite(values), values, np.nan)
    out = out[FEATURES]
    out.index = frame.index
    return out


def read(entry):
    passed = entry['all_year_primary'] or (entry['cycle25_primary'] and entry['cycle25_bootstrap_lower_above_zero'])
    return 'L1_latency_binding' if passed else 'L2_no_gain_at_zero_latency'


def run(config_path, output):
    if output.exists():
        raise FileExistsError(output)
    config = json.loads(config_path.read_text())
    evidence = config['evidence']
    control_dir, causal_dir = Path(evidence['control']), Path(evidence['causal_history'])
    for path, expected in [(Path(evidence['table'])/'report.json', evidence['table_report_sha256']),
                           (control_dir/'report.json', evidence['control_report_sha256']),
                           (causal_dir/'report.json', evidence['causal_history_report_sha256']),
                           (Path(evidence['sgas_directory'])/'manifest.json', evidence['sgas_manifest_sha256']),
                           (Path(evidence['mapping_directory'])/'manifest.json', evidence['mapping_manifest_sha256'])]:
        if sha(path) != expected:
            raise ValueError(f'Input changed: {path}')
    if config['features'] != FEATURES:
        raise ValueError('Feature list differs from the frozen protocol')
    control_report = json.loads((control_dir/'report.json').read_text())
    causal_report = json.loads((causal_dir/'report.json').read_text())
    if sha(causal_dir/'thresholds.json') != causal_report['thresholds_sha256']:
        raise ValueError('Causal history thresholds changed')
    causal_thresholds = json.loads((causal_dir/'thresholds.json').read_text())
    pipeline = json.loads(Path(evidence['pipeline_protocol']).read_text())
    base = json.loads(Path(evidence['base_protocol']).read_text())
    events = load_events(Path(evidence['sgas_directory']))
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
        contexts = {role: attach_event_history(group, mapping, events) for role, group in split.items()}
        for role, context in contexts.items():
            coverage.append({'year': year, 'role': role, 'rows': len(context), 'event_available_share': float(context.event_available.mean()),
                             'reg_mx_24h_positive_share': float((context.reg_mx_24h > 0).mean()),
                             'reg_mx_72h_positive_share': float((context.reg_mx_72h > 0).mean())})
        y_cal = split['calibration'].target.to_numpy(dtype=np.int8)
        p_cal, p_eval = fit_probabilities(base, split, contexts, FEATURES)
        thresholds[str(year)] = {'control': causal_thresholds[str(year)]['control'], 'history': causal_thresholds[str(year)]['history'],
                                 'event_time': select_thresholds(pipeline, y_cal, p_cal)}
        prepared[year] = split['evaluation'][KEY].reset_index(drop=True).assign(event_time=p_eval)
        print(f'{year}: alert thresholds ' + ', '.join(f'{c}={v["alert"]["threshold"]:.4f}' for c, v in thresholds[str(year)].items()), flush=True)
        del split, contexts
        gc.collect()
    (output/'thresholds.json').write_text(json.dumps(thresholds, indent=2)+'\n')
    pd.DataFrame(coverage).to_csv(output/'coverage.csv', index=False)
    thresholds_sha = sha(output/'thresholds.json')
    # Phase 2: evaluation labels are read only now.
    tolerance = config['acceptance']['per_year_primary']['window_recall_drop_at_most']
    candidates = ['control', 'history', 'event_time']
    rows, intervals = [], []
    for year in config['years']:
        stored = pd.read_parquet(causal_dir/f'predictions_{year}.parquet', columns=[*KEY, 'target', 'missing_fraction', 'control', 'history'])
        frame = stored.merge(prepared[year], on=KEY, how='inner')
        if len(frame) != len(stored) or len(frame) != len(prepared[year]):
            raise ValueError(f'Evaluation keys do not match: {year}')
        frame = frame.sort_values(KEY).reset_index(drop=True)
        year_rows, alarms = {}, {}
        for candidate in candidates:
            scored = frame[[*KEY, 'target', 'missing_fraction']].assign(probability=frame[candidate])
            chosen = thresholds[str(year)][candidate]
            parts = decomposition(scored, chosen['watch']['threshold'])
            origin = alert_false_positive_origin(scored, chosen['alert']['threshold'])
            alarms[candidate] = frame[candidate].ge(chosen['alert']['threshold']).to_numpy()
            for tier in TIERS:
                row = point(scored, tier, chosen[tier], year)
                row.update(candidate=candidate, average_precision=parts['overall_ap'], within_flaring_ap=parts['within_flaring_ap'],
                           region_ap=parts['region_ap'])
                if tier == 'alert':
                    row.update(alert_fp_share_never_flaring_harps=origin['alert_fp_share_never_flaring_harps'],
                               alert_fp_share_within_72h_of_positive=origin['alert_fp_share_within_72h_of_positive'])
                year_rows[(candidate, tier)] = row
        control = year_rows[('control', 'alert')]
        for candidate in candidates:
            row = year_rows[(candidate, 'alert')]
            row['precision_at_control_recall'] = precision_at_recall(frame.target.to_numpy(), frame[candidate].to_numpy(), control['recall'])
            if candidate == 'control':
                continue
            flags = acceptance(row, control, tolerance)
            row.update(flags)
            row['primary_met'] = bool(all(flags.values()))
            interval = paired_precision_bootstrap(frame, alarms['control'], alarms[candidate])
            intervals.append(dict(year=year, candidate=candidate, against='control', **interval))
            row.update(precision_difference_lower=interval['lower'], precision_difference_upper=interval['upper'])
        versus = paired_precision_bootstrap(frame, alarms['history'], alarms['event_time'])
        intervals.append(dict(year=year, candidate='event_time', against='history', **versus))
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
              'development_basis': 'relabelled table, walk-forward-v2, operating-point-v3', 'deployable': False,
              'sgas_event_rows': len(events), 'acceptance': summary, 'reading': read(summary['event_time']),
              'constituent_fits': len(config['years'])*2, 'reserved_test_accessed': False, 'model_promoted': False,
              'artifact_hashes': {p.name: sha(p) for p in sorted(output.iterdir())}}
    (output/'report.json').write_text(json.dumps(result, indent=2)+'\n')
    return result, table


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=Path('config/history-latency-ceiling-v1.json'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result, table = run(args.config, args.output)
    pd.set_option('display.width', 250)
    print(table[['year', 'candidate', 'tier', 'fallback', 'tp', 'fp', 'recall', 'precision', 'accuracy', 'always_negative_accuracy',
                 'missed_positive_runs', 'positive_runs', 'average_precision', 'within_flaring_ap']].round(4).to_string(index=False))
    print(json.dumps({'acceptance': result['acceptance'], 'reading': result['reading']}, indent=1))
