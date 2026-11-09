"""Evaluate causal flare-history context from issued NOAA SGAS products (config/activity-history-v1.json)."""
import argparse
from collections import Counter
import gc
import json
from pathlib import Path
import re

import numpy as np
import pandas as pd

from helio24.full_data import sha256
from helio24.modeling import metrics
from helio24.v2_training import load_development
from helio24.walk_forward import annual_fold
from scripts.audit_alarm_persistence import acceptance, evaluate, paired_bootstrap, sha
from scripts.audit_region_context_features import fit_candidate
from scripts.audit_region_context_sources import ISSUED, SAFETY, load_mapping

KEY = ['harp', 'forecast_time']
XRAY = re.compile(r'^([ABCMX])(\d+\.\d)$')
BACKGROUND = re.compile(r'X-ray Background\s+([ABCMX])(\d+\.\d)')
SCALE = {'A': -8, 'B': -7, 'C': -6, 'M': -5, 'X': -4}
FLAG = ['history_available', 'reports_3d', 'hours_since_issue']
HISTORY = [*FLAG, 'reg_c_1d', 'reg_mx_1d', 'reg_c_3d', 'reg_mx_3d', 'reg_events_3d', 'reg_max_logflux_3d',
           'reg_mx_life', 'reg_max_logflux_life', 'disk_mx_1d', 'disk_mx_3d', 'disk_max_logflux_1d',
           'xray_background_log']
CANDIDATES = {'flag': FLAG, 'history': HISTORY}
DAY, THREE = pd.Timedelta('27h'), pd.Timedelta('75h')


def log_flux(letter, number):
    return SCALE[letter]+float(np.log10(float(number)))


def parse_sgas(text):
    """Issue time, section A event rows (fixed-width columns) and the X-ray background of one SGAS product."""
    match = ISSUED.search(text)
    issued = pd.Timestamp(pd.to_datetime(match.group(1), format='%Y %b %d %H%M'), tz='UTC') if match else None
    events, unparsed, in_section = [], 0, False
    for line in text.splitlines():
        if line.startswith('A.'):
            in_section = True
            continue
        if line.startswith('B.'):
            in_section = False
        if not in_section or line.startswith('Begin') or not line.strip() or line.strip().lower() == 'none':
            continue
        padded = line.ljust(34)
        region, xray = padded[16:21].strip(), XRAY.match(padded[28:33].strip())
        if not re.fullmatch(r'[\d ]{4}', padded[1:5]) or (region and not region.isdigit()):
            unparsed += 1
            continue
        noaa = int(region) if region else None
        if noaa is not None and noaa < 5000:
            noaa += 10000
        events.append({'noaa': noaa, 'logflux': log_flux(*xray.groups()) if xray else np.nan})
    found = BACKGROUND.search(text)
    return issued, events, (log_flux(*found.groups()) if found else np.nan), unparsed


def load_sgas(directory):
    manifest = json.loads((directory/'manifest.json').read_text())
    reports, events, problems = [], [], Counter()
    for record in manifest['records']:
        if record['status'] != 'ok':
            problems['unavailable'] += 1
            continue
        path = directory/record['file']
        if sha256(path) != record['sha256']:
            raise ValueError(f'SGAS file changed: {record["file"]}')
        issued, rows, background, unparsed = parse_sgas(path.read_text(errors='replace'))
        problems['unparsed_event_lines'] += unparsed
        if issued is None:
            problems['no_issue_time'] += 1
            continue
        reports.append({'issued_utc': issued, 'background': background})
        events.extend({'issued_utc': issued, **row} for row in rows)
    reports = pd.DataFrame(reports).drop_duplicates('issued_utc').sort_values('issued_utc').reset_index(drop=True)
    return reports, pd.DataFrame(events), dict(problems)


def _window_stats(times, values, cutoff, span):
    """Count and max of values whose time lies in (cutoff - span, cutoff]; times sorted ascending."""
    hi = np.searchsorted(times, cutoff, side='right')
    lo = np.searchsorted(times, cutoff-span, side='right') if span is not None else np.zeros_like(hi)
    return lo, hi


def attach_history(frame, mapping, reports, events):
    """Causal flare history per window from SGAS products issued <= t - 30 min; region rows by the HARP's NOAA numbers."""
    base = frame[KEY].copy().reset_index(drop=True)
    base['forecast_time'] = pd.to_datetime(base.forecast_time, utc=True)
    cutoff = (base.forecast_time-SAFETY).to_numpy(dtype='datetime64[ns]')
    issued = reports.issued_utc.to_numpy(dtype='datetime64[ns]')
    day, three = DAY.to_timedelta64(), THREE.to_timedelta64()
    out = pd.DataFrame(index=base.index)
    lo, hi = _window_stats(issued, None, cutoff, three)
    out['reports_3d'] = (hi-lo).astype(float)
    latest = np.where(hi > 0, issued[np.maximum(hi-1, 0)], np.datetime64('NaT', 'ns'))
    hours = (cutoff-latest)/np.timedelta64(1, 'h')+SAFETY.total_seconds()/3600
    fresh = (hi > 0) & (hours <= 27.5)
    background = reports.background.to_numpy()
    out['xray_background_log'] = np.where(fresh, background[np.maximum(hi-1, 0)], np.nan)
    out['hours_since_issue'] = np.where(fresh, hours, np.nan)
    # Full-disk history.
    flare = events[events.logflux.notna()].sort_values('issued_utc')
    disk_t = flare.issued_utc.to_numpy(dtype='datetime64[ns]')
    disk_mx = np.concatenate([[0], np.cumsum(flare.logflux.to_numpy() >= -5)])
    for name, span in [('disk_mx_1d', day), ('disk_mx_3d', three)]:
        lo, hi = _window_stats(disk_t, None, cutoff, span)
        out[name] = np.where(fresh, disk_mx[hi]-disk_mx[lo], np.nan)
    daily_max = flare.groupby('issued_utc').logflux.max().reindex(reports.issued_utc).to_numpy()
    lo, hi = _window_stats(issued, None, cutoff, day)
    out['disk_max_logflux_1d'] = np.where(fresh & (hi > lo), daily_max[np.maximum(hi-1, 0)], np.nan)
    # Regional history through the HARP's NOAA numbers on the forecast date.
    base['date'] = base.forecast_time.dt.date
    pairs = base.reset_index()[['index', 'harp', 'date']].merge(mapping[['harp', 'date', 'noaa']], on=['harp', 'date'])
    numbered = np.zeros(len(base), dtype=bool)
    numbered[pairs['index'].unique()] = True
    names = ['reg_c_1d', 'reg_mx_1d', 'reg_c_3d', 'reg_mx_3d', 'reg_events_3d', 'reg_mx_life']
    sums = {name: np.zeros(len(base)) for name in names}
    best3, best_life = np.full(len(base), -np.inf), np.full(len(base), -np.inf)
    regional = {noaa: group.sort_values('issued_utc') for noaa, group in events.dropna(subset=['noaa']).groupby('noaa')}
    for noaa, rows in pairs.groupby('noaa'):
        group = regional.get(noaa)
        if group is None:
            continue
        index = rows['index'].to_numpy()
        cut = cutoff[index]
        times = group.issued_utc.to_numpy(dtype='datetime64[ns]')
        flux = group.logflux.to_numpy()
        is_c = np.concatenate([[0], np.cumsum((flux >= -6) & (flux < -5))])
        is_mx = np.concatenate([[0], np.cumsum(flux >= -5)])
        every = np.arange(len(times)+1)
        hi = np.searchsorted(times, cut, side='right')
        lo1 = np.searchsorted(times, cut-day, side='right')
        lo3 = np.searchsorted(times, cut-three, side='right')
        np.add.at(sums['reg_c_1d'], index, is_c[hi]-is_c[lo1])
        np.add.at(sums['reg_mx_1d'], index, is_mx[hi]-is_mx[lo1])
        np.add.at(sums['reg_c_3d'], index, is_c[hi]-is_c[lo3])
        np.add.at(sums['reg_mx_3d'], index, is_mx[hi]-is_mx[lo3])
        np.add.at(sums['reg_events_3d'], index, every[hi]-every[lo3])
        np.add.at(sums['reg_mx_life'], index, is_mx[hi])
        filled = np.where(np.isnan(flux), -np.inf, flux)
        running = np.concatenate([[-np.inf], np.maximum.accumulate(filled)])
        np.maximum.at(best_life, index, running[hi])
        recent = np.array([filled[a:b].max() if b > a else -np.inf for a, b in zip(lo3, hi)])
        np.maximum.at(best3, index, recent)
    known = numbered & (out.reports_3d.to_numpy() >= 1)
    out['history_available'] = known.astype(float)
    for name in names:
        out[name] = np.where(known, sums[name], np.nan)
    out['reg_max_logflux_3d'] = np.where(known & np.isfinite(best3), best3, np.nan)
    out['reg_max_logflux_life'] = np.where(known & np.isfinite(best_life), best_life, np.nan)
    out = out[HISTORY]
    out.index = frame.index
    return out


def run(config_path, output):
    if output.exists():
        raise FileExistsError(output)
    config = json.loads(config_path.read_text())
    evidence = config['evidence']
    source = Path(evidence['predictions'])
    if sha(source/'report.json') != evidence['predictions_report_sha256']:
        raise ValueError('Final experiment manifest changed')
    walk_report = json.loads((Path(evidence['baseline_artifact'])/'report.json').read_text())
    control_thresholds = json.loads(Path(evidence['control_thresholds']).read_text())
    if sha(Path(evidence['control_thresholds'])) != evidence['control_thresholds_sha256']:
        raise ValueError('Control thresholds changed')
    target = config['recall_target']
    base = {**json.loads(Path(evidence['base_protocol']).read_text()), 'required_recall': target}
    reports, events, problems = load_sgas(Path(evidence['sgas_directory']))
    mapping, _, _ = load_mapping(Path(evidence['mapping_directory']))
    original, _ = load_development(Path(base['source']), evidence['frozen_shards_report_sha256'])
    development = pd.concat(original.values(), ignore_index=True)
    del original
    output.mkdir(parents=True)
    thresholds, prepared, coverage = {}, {}, []
    for year in config['years']:
        groups, audit = annual_fold(development, year)
        if audit != next(f for f in walk_report['folds'] if f['year'] == year)['audit']:
            raise ValueError(f'Annual populations changed: {year}')
        groups['evaluation'] = groups['evaluation'].drop(columns=['target', 'label_status'])
        contexts = {role: attach_history(group, mapping, reports, events) for role, group in groups.items()}
        for role, context in contexts.items():
            coverage.append({'year': year, 'role': role, 'rows': len(context),
                             'history_available_share': float(context.history_available.mean()),
                             'reg_mx_3d_positive_share': float((context.reg_mx_3d > 0).mean())})
        chosen, probabilities = {'control': float(control_thresholds[str(year)][str(target)])}, {}
        for candidate, columns in CANDIDATES.items():
            chosen[candidate], probabilities[candidate] = fit_candidate(base, groups, contexts, columns)
            gc.collect()
        thresholds[str(year)] = chosen
        prepared[year] = groups['evaluation'][KEY].reset_index(drop=True).assign(**probabilities)
        print(f'{year}: thresholds {chosen}', flush=True)
        del groups, contexts
        gc.collect()
    (output/'thresholds.json').write_text(json.dumps(thresholds, indent=2)+'\n')
    pd.DataFrame(coverage).to_csv(output/'history_coverage.csv', index=False)
    thresholds_sha = sha(output/'thresholds.json')
    # Phase 2: evaluation labels are read only now.
    tolerance = config['acceptance']['per_year_primary']['window_recall_drop_at_most']
    candidates = ['control', *CANDIDATES]
    rows_out, intervals = [], []
    for year in config['years']:
        labels = pd.read_parquet(source/str(year)/'predictions.parquet',
                                 columns=[*KEY, 'target', 'missing_fraction', 'baseline'])
        frame = labels.merge(prepared[year], on=KEY, how='inner').rename(columns={'baseline': 'control'})
        if len(frame) != len(labels) or len(frame) != len(prepared[year]):
            raise ValueError(f'Evaluation keys do not match: {year}')
        y = frame.target.to_numpy()
        results = {c: evaluate(frame, c, thresholds[str(year)][c], 1) for c in candidates}
        control, control_harp = results['control']
        for candidate in candidates:
            values, per_harp = results[candidate]
            scores = metrics(y, frame[candidate].to_numpy(), thresholds[str(year)][candidate])
            tn = len(y)-values['tp']-values['fp']-values['fn']
            row = dict(year=year, candidate=candidate, **values, accuracy=(values['tp']+tn)/len(y),
                       always_negative_accuracy=float((y == 0).mean()),
                       average_precision=scores['average_precision'], brier=scores['brier'],
                       log_loss=scores['log_loss'], tss=scores['tss'])
            if candidate != 'control':
                flags = acceptance(values, control, tolerance)
                row.update(flags)
                row['primary_met'] = bool(all(flags.values()))
                for metric, interval in paired_bootstrap(control_harp, per_harp).items():
                    intervals.append(dict(year=year, candidate=candidate, metric=metric, **interval))
            rows_out.append(row)
        frame.to_parquet(output/f'predictions_{year}.parquet', index=False)
    table_out = pd.DataFrame(rows_out)
    summary = []
    for candidate in CANDIDATES:
        gated = table_out[table_out.candidate == candidate]
        summary.append(dict(candidate=candidate, years_met=int(gated.primary_met.sum()), required_years=len(gated),
                            met_years=[int(v) for v in gated.loc[gated.primary_met.astype(bool), 'year']]))
    table_out.to_csv(output/'results.csv', index=False)
    pd.DataFrame(intervals).to_csv(output/'intervals.csv', index=False)
    result = {'config_sha256': sha(config_path), 'thresholds_sha256': thresholds_sha, 'years': config['years'],
              'sgas_reports': len(reports), 'sgas_events': len(events), 'sgas_problems': problems,
              'acceptance': summary, 'constituent_fits': len(config['years'])*len(CANDIDATES)*2,
              'reserved_test_accessed': False, 'model_promoted': False,
              'artifact_hashes': {p.name: sha(p) for p in sorted(output.iterdir())}}
    (output/'report.json').write_text(json.dumps(result, indent=2)+'\n')
    return result, table_out


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=Path('config/activity-history-v1.json'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result, table = run(args.config, args.output)
    pd.set_option('display.width', 250)
    print(table[['year', 'candidate', 'tp', 'fp', 'fn', 'recall', 'precision', 'accuracy', 'average_precision',
                 'brier', 'primary_met']].round(4).to_string(index=False))
    print(json.dumps(result['acceptance']))
