"""Measure which GOES M/X flares reach a positive label (config/label-coverage-v1.json)."""
import argparse
import json
from pathlib import Path
import re

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score

from helio24.full_data import sha256
from helio24.v2_training import load_development
from scripts.audit_alarm_persistence import sha
from scripts.audit_region_context_sources import load_mapping

KEY = ['harp', 'forecast_time']
XRAY = re.compile(r'^([MX])(\d+\.\d)$')


def parse_major_events(text, report_date):
    """M/X rows of section A: peak time on the previous UT day, region number (None if absent)."""
    events, in_section = [], False
    for line in text.splitlines():
        if line.startswith('A.'):
            in_section = True
            continue
        if line.startswith('B.'):
            break
        if not in_section or line.startswith('Begin') or not line.strip():
            continue
        padded = line.ljust(34)
        peak, region, xray = padded[6:10].strip(), padded[16:21].strip(), XRAY.match(padded[28:33].strip())
        if not xray or not re.fullmatch(r'\d{4}', peak):
            continue
        noaa = int(region) if region.isdigit() else None
        if noaa is not None and noaa < 5000:
            noaa += 10000
        day = pd.Timestamp(report_date)-pd.Timedelta(days=1)
        events.append(dict(peak_time=pd.Timestamp(day.strftime('%Y-%m-%d')+f' {peak[:2]}:{peak[2:]}', tz='UTC'),
                           goes_class=xray.group(1)+xray.group(2), noaa=noaa))
    return events


def load_sgas_major_events(directory):
    manifest = json.loads((directory/'manifest.json').read_text())
    rows = []
    for record in manifest['records']:
        if record['status'] != 'ok':
            continue
        path = directory/record['file']
        if sha256(path) != record['sha256']:
            raise ValueError(f'SGAS file changed: {record["file"]}')
        rows.extend(parse_major_events(path.read_text(errors='replace'), record['date']))
    events = pd.DataFrame(rows).drop_duplicates(['peak_time', 'goes_class', 'noaa']).sort_values('peak_time')
    events['year'] = events.peak_time.dt.year
    return events.reset_index(drop=True)


def classify(events, mapping, table):
    """Map each event to HARPs through NOAA_ARS and classify it against the development windows."""
    mapped = events.dropna(subset=['noaa']).assign(date=lambda f: f.peak_time.dt.date, noaa=lambda f: f.noaa.astype(int))
    mapped = mapped.merge(mapping, on=['date', 'noaa'], how='left')
    starts = table.forecast_time.to_numpy(dtype='datetime64[ns]')
    ends = table.prediction_end.to_numpy(dtype='datetime64[ns]')
    by_harp = {h: idx for h, idx in table.groupby('harp').indices.items()}
    target = table.target.to_numpy()
    status, event_harps = [], []
    for row in mapped.itertuples():
        if pd.isna(row.harp):
            status.append('unmapped')
            event_harps.append(None)
            continue
        idx = by_harp.get(int(row.harp))
        if idx is None:
            status.append('no_window')
        else:
            peak = np.datetime64(row.peak_time.tz_convert(None), 'ns')
            inside = idx[(starts[idx] <= peak) & (peak < ends[idx])]
            status.append('no_window' if not len(inside) else ('covered' if target[inside].any() else 'hidden'))
        event_harps.append(int(row.harp))
    mapped = mapped.assign(status=status, harp=event_harps)
    rank = {'covered': 0, 'hidden': 1, 'no_window': 2, 'unmapped': 3}
    best = (mapped.assign(rank=mapped.status.map(rank)).sort_values('rank')
            .groupby(['peak_time', 'goes_class', 'noaa'], as_index=False).first())
    best['ambiguous'] = mapped.groupby(['peak_time', 'goes_class', 'noaa']).harp.nunique().reindex(
        pd.MultiIndex.from_frame(best[['peak_time', 'goes_class', 'noaa']])).gt(1).to_numpy()
    return best.drop(columns='rank'), mapped


def hek_match(sgas, hek):
    hek = hek.assign(peak_time=pd.to_datetime(hek.peak_time, utc=True), year=lambda f: f.peak_time.dt.year)
    matched = []
    for row in hek.itertuples():
        same = sgas[sgas.goes_class.eq(row.goes_class) & (sgas.peak_time-row.peak_time).abs().le(pd.Timedelta(minutes=5))]
        matched.append(same.index[0] if len(same) else None)
    return hek.assign(sgas_index=matched)


def run(config_path, output):
    if output.exists():
        raise FileExistsError(output)
    config = json.loads(config_path.read_text())
    evidence = config['evidence']
    hek_path = Path(evidence['hek_unassigned_events'])
    if sha(hek_path) != evidence['hek_unassigned_events_sha256']:
        raise ValueError('HEK unassigned inventory changed')
    if sha(Path(evidence['watch_tier_thresholds'])) != evidence['watch_tier_thresholds_sha256']:
        raise ValueError('Watch tier thresholds changed')
    thresholds = json.loads(Path(evidence['watch_tier_thresholds']).read_text())
    original, _ = load_development(Path(evidence['frozen_shards']), evidence['frozen_shards_report_sha256'])
    table = pd.concat(original.values(), ignore_index=True)[[*KEY, 'prediction_end', 'target']]
    del original
    table['forecast_time'] = pd.to_datetime(table.forecast_time, utc=True).dt.tz_convert(None)
    table['prediction_end'] = pd.to_datetime(table.prediction_end, utc=True).dt.tz_convert(None)
    mapping, _, _ = load_mapping(Path(evidence['mapping_directory']))
    sgas = load_sgas_major_events(Path(evidence['sgas_directory']))
    sgas = sgas[sgas.year.isin(config['years'])].reset_index(drop=True)
    best, mapped = classify(sgas, mapping, table)
    hek = hek_match(sgas, pd.read_csv(hek_path))
    hek = hek[hek.year.isin(config['years'])]
    best_status = best.set_index(['peak_time', 'goes_class', 'noaa']).status
    hek['sgas_status'] = [None if i is None else best_status.get((sgas.peak_time[i], sgas.goes_class[i], sgas.noaa[i]), 'unmapped')
                          for i in hek.sgas_index]
    output.mkdir(parents=True)
    rows = []
    for year in config['years']:
        s = sgas[sgas.year.eq(year)]
        b = best[best.peak_time.dt.year.eq(year)]
        h = hek[hek.year.eq(year)]
        counts = b.status.value_counts()
        mapped_n = int(counts.get('covered', 0)+counts.get('hidden', 0)+counts.get('no_window', 0))
        rows.append(dict(year=year, sgas_mx_events=len(s), with_region=int(s.noaa.notna().sum()),
                         mapped_to_harp=mapped_n, ambiguous=int(b.ambiguous.sum()),
                         covered=int(counts.get('covered', 0)), hidden=int(counts.get('hidden', 0)),
                         no_window=int(counts.get('no_window', 0)),
                         covered_share=counts.get('covered', 0)/mapped_n if mapped_n else None,
                         hek_unassigned=len(h), hek_unassigned_sgas_matched=int(h.sgas_index.notna().sum()),
                         hek_unassigned_mapped=int(h.sgas_status.isin(['covered', 'hidden', 'no_window']).sum()),
                         hek_unassigned_hidden=int(h.sgas_status.eq('hidden').sum()),
                         positive_windows=int(table[table.forecast_time.dt.year.eq(year)].target.sum())))
    coverage = pd.DataFrame(rows)
    effect = []
    source = Path(evidence['predictions'])
    if sha(source/'report.json') != evidence['predictions_report_sha256']:
        raise ValueError('Final experiment manifest changed')
    hidden_harps = {}
    for year in config['evaluation_years']:
        frame = pd.read_parquet(source/str(year)/'predictions.parquet', columns=[*KEY, 'target', 'baseline'])
        flaring = set(frame[frame.target.eq(1)].harp)
        m = mapped[mapped.peak_time.dt.year.eq(year) & mapped.status.isin(['hidden', 'no_window'])]
        hidden = sorted(set(m.harp.dropna().astype(int))-flaring)
        hidden_harps[str(year)] = hidden
        in_hidden = frame.harp.isin(hidden)
        alarm = frame.baseline.ge(thresholds[str(year)]['0.9'])
        fp = alarm & frame.target.eq(0)
        kept = frame[~in_hidden]
        tp = int((alarm & frame.target.eq(1)).sum())
        effect.append(dict(year=year, hidden_harps=len(hidden), hidden_harp_windows=int(in_hidden.sum()),
                           fp_windows=int(fp.sum()), fp_windows_hidden_harps=int((fp & in_hidden).sum()),
                           fp_share_hidden_harps=float((fp & in_hidden).sum()/fp.sum()) if fp.sum() else None,
                           precision=tp/(tp+int(fp.sum())), precision_without_hidden=tp/(tp+int((fp & ~in_hidden).sum())),
                           ap=float(average_precision_score(frame.target, frame.baseline)),
                           ap_without_hidden=float(average_precision_score(kept.target, kept.baseline))))
    effect = pd.DataFrame(effect)
    coverage.to_csv(output/'coverage.csv', index=False)
    effect.to_csv(output/'evaluation_effect.csv', index=False)
    best.to_csv(output/'sgas_events.csv', index=False)
    hek.drop(columns='sgas_index').to_csv(output/'hek_unassigned_cross_check.csv', index=False)
    (output/'hidden_harps.json').write_text(json.dumps(hidden_harps, indent=1)+'\n')
    share = coverage.set_index('year').covered_share
    reading = {'R1_coverage_collapsed': bool(share[2022] < 0.5 and share[2023] < 0.5 and share[2014] >= 0.5 and share[2015] >= 0.5),
               'R2_labels_hold': bool(share[2022] >= 0.5 and share[2023] >= 0.5)}
    result = {'config_sha256': sha(config_path), 'reading': reading, 'reserved_test_accessed': False,
              'relabelled': False, 'model_promoted': False,
              'artifact_hashes': {p.name: sha(p) for p in sorted(output.iterdir())}}
    (output/'report.json').write_text(json.dumps(result, indent=2)+'\n')
    return result, coverage, effect


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=Path('config/label-coverage-v1.json'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result, coverage, effect = run(args.config, args.output)
    pd.set_option('display.width', 250)
    print(coverage.round(4).to_string(index=False))
    print(effect.round(4).to_string(index=False))
    print(json.dumps(result['reading']))
