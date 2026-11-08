"""Provenance and coverage audit of the SRS and HARP-NOAA sources (config/region-context-sources-v1.json)."""
import argparse
from collections import Counter
import json
from pathlib import Path
import re

import numpy as np
import pandas as pd

from helio24.full_data import sha256
from helio24.v2_training import load_development

ISSUED = re.compile(r'^:Issued: (\d{4} [A-Z][a-z]{2} \d{2} \d{4}) UTC\s*$', re.M)
ROW = re.compile(r'^(\d{4})\s+([NS]\d{2}[EW]\d{2})\s+(\d{3})\s+(\d{4})\s+([A-Z][a-z]{2})\s+(\d{2})\s+(\d{2})\s+(\S+)\s*$')
SAFETY = pd.Timedelta('30min')


def parse_srs(text):
    """Issue time and section I rows (regions with sunspots) of one SRS product."""
    match = ISSUED.search(text)
    issued = pd.Timestamp(pd.to_datetime(match.group(1), format='%Y %b %d %H%M'), tz='UTC') if match else None
    rows, in_section = [], False
    for line in text.splitlines():
        if line.startswith('I.'):
            in_section = True
            continue
        if line.startswith(('IA.', 'II.', 'III.')):
            in_section = False
        if in_section:
            found = ROW.match(line.strip())
            if found:
                number, location, lo, area, z, ll, nn, mag = found.groups()
                rows.append({'noaa': 10000+int(number) if int(number) < 5000 else int(number), 'location': location,
                             'area': int(area), 'z': z, 'll': int(ll), 'nn': int(nn), 'mag_type': mag})
    return issued, rows


def load_srs(directory):
    manifest = json.loads((directory/'manifest.json').read_text())
    issued, rows, problems = [], [], Counter()
    for record in manifest['records']:
        if record['status'] != 'ok':
            problems['unavailable'] += 1
            continue
        path = directory/record['file']
        if sha256(path) != record['sha256']:
            raise ValueError(f'SRS file changed: {record["file"]}')
        when, regions = parse_srs(path.read_text(errors='replace'))
        if when is None:
            problems['no_issue_time'] += 1
            continue
        issued.append({'date': record['date'], 'issued_utc': when})
        rows.extend({'issued_utc': when, **region} for region in regions)
    return pd.DataFrame(issued), pd.DataFrame(rows), dict(problems)


def load_mapping(directory):
    manifest = json.loads((directory/'manifest.json').read_text())
    frames, problems = [], Counter()
    for record in manifest['records']:
        if record['status'] != 'ok':
            problems['unavailable'] += 1
            continue
        path = directory/record['file']
        if sha256(path) != record['sha256']:
            raise ValueError(f'Mapping file changed: {record["file"]}')
        payload = json.loads(path.read_text())
        keywords = {k['name']: k['values'] for k in payload.get('keywords', [])}
        if not keywords:
            continue
        frame = pd.DataFrame({'harp': pd.to_numeric(keywords['HARPNUM']), 't_rec': keywords['T_REC'],
                              'noaa_ars': keywords['NOAA_ARS']})
        frames.append(frame)
    mapping = pd.concat(frames, ignore_index=True)
    mapping['date'] = pd.to_datetime(mapping.t_rec.str.slice(0, 10), format='%Y.%m.%d').dt.date
    mapping = mapping[~mapping.noaa_ars.isin(['MISSING', '', '0'])]
    mapping = mapping.assign(noaa=mapping.noaa_ars.str.split(',')).explode('noaa')
    mapping['noaa'] = pd.to_numeric(mapping.noaa, errors='coerce')
    mapping = mapping.dropna(subset=['noaa']).astype({'noaa': int})
    return mapping[['harp', 'date', 'noaa']].drop_duplicates(), dict(problems), manifest['http_fallback_months']


def available_srs(issued, times, safety=SAFETY):
    """Latest SRS issue time at or before each forecast time minus the safety margin (NaT if none)."""
    order = np.sort(issued.to_numpy())
    cutoff = (pd.to_datetime(times, utc=True)-safety).to_numpy()
    index = np.searchsorted(order, cutoff, side='right')-1
    out = pd.Series(pd.NaT, index=range(len(cutoff)), dtype='datetime64[ns, UTC]')
    valid = index >= 0
    out[valid] = pd.to_datetime(order[index[valid]], utc=True)
    return out


def coverage(windows, mapping, issued, srs_rows):
    """Per window: NOAA numbers on the forecast date; whether one appears in the SRS available at issue time."""
    frame = windows[['harp', 'forecast_time', 'target', 'role']].copy()
    frame['forecast_time'] = pd.to_datetime(frame.forecast_time, utc=True)
    frame['date'] = frame.forecast_time.dt.date
    frame['available_srs'] = available_srs(issued.issued_utc, frame.forecast_time).to_numpy()
    merged = frame.reset_index().merge(mapping, on=['harp', 'date'], how='left')
    merged['has_noaa'] = merged.noaa.notna()
    srs_keys = set(zip(srs_rows.issued_utc, srs_rows.noaa))
    merged['in_srs'] = [((t, n) in srs_keys) if pd.notna(n) and pd.notna(t) else False
                        for t, n in zip(merged.available_srs, merged.noaa)]
    per_window = merged.groupby('index').agg(has_noaa=('has_noaa', 'any'), in_srs=('in_srs', 'any'))
    frame = frame.join(per_window)
    frame['year'] = frame.forecast_time.dt.year
    return frame


def run(config_path, srs_dir, mapping_dir, output):
    if output.exists():
        raise FileExistsError(output)
    config = json.loads(config_path.read_text())
    issued, srs_rows, srs_problems = load_srs(srs_dir)
    mapping, mapping_problems, http_months = load_mapping(mapping_dir)
    shards = Path(config.get('frozen_shards_report', 'artifacts/v2_development_features_20261025_r2/report.json')).parent
    original, _ = load_development(shards, '62a64b3d94b9f7ec1624e5596fc86e636922a0e696968259b55ff0c8739c5f82')
    windows = pd.concat(original.values(), ignore_index=True)
    frame = coverage(windows, mapping, issued, srs_rows)
    output.mkdir(parents=True)
    by_year = frame.groupby('year').agg(windows=('harp', 'size'), positives=('target', 'sum'),
        harps=('harp', 'nunique'), share_with_noaa=('has_noaa', 'mean'), share_in_available_srs=('in_srs', 'mean'))
    positives = frame[frame.target.eq(1)].groupby('year').agg(
        positive_share_with_noaa=('has_noaa', 'mean'), positive_share_in_available_srs=('in_srs', 'mean'))
    by_year = by_year.join(positives).reset_index()
    by_year.to_csv(output/'coverage_by_year.csv', index=False)
    vocab = srs_rows.assign(year=srs_rows.issued_utc.dt.year).groupby('year').agg(
        mag_types=('mag_type', lambda s: sorted(set(s))), z_classes=('z', 'nunique'), rows=('noaa', 'size')).reset_index()
    vocab.to_csv(output/'srs_vocabulary_by_year.csv', index=False)
    issue_hours = issued.issued_utc.dt.hour+issued.issued_utc.dt.minute/60
    report = {
        'config_sha256': sha256(config_path),
        'srs': {'files_with_issue_time': len(issued), 'problems': srs_problems, 'region_rows': len(srs_rows),
                'issue_hour_utc_min': float(issue_hours.min()), 'issue_hour_utc_max': float(issue_hours.max()),
                'issue_hour_utc_share_at_0030': float((issue_hours == 0.5).mean()),
                'mag_type_vocabulary': sorted(set(srs_rows.mag_type))},
        'mapping': {'rows': len(mapping), 'harps_with_noaa': int(mapping.harp.nunique()), 'problems': mapping_problems,
                    'http_fallback_months': http_months},
        'development_windows': int(len(frame)), 'development_harps': int(frame.harp.nunique()),
        'share_with_noaa': float(frame.has_noaa.mean()), 'share_in_available_srs': float(frame.in_srs.mean()),
        'positive_share_with_noaa': float(frame.loc[frame.target.eq(1), 'has_noaa'].mean()),
        'positive_share_in_available_srs': float(frame.loc[frame.target.eq(1), 'in_srs'].mean()),
        'safety_margin': str(SAFETY), 'reserved_test_accessed': False,
        'artifact_hashes': {p.name: sha256(p) for p in sorted(output.iterdir())}}
    (output/'report.json').write_text(json.dumps(report, indent=2, default=str)+'\n')
    return report, by_year


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=Path('config/region-context-sources-v1.json'))
    parser.add_argument('--srs', type=Path, required=True)
    parser.add_argument('--mapping', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report, by_year = run(args.config, args.srs, args.mapping, args.output)
    print(json.dumps({k: v for k, v in report.items() if k != 'artifact_hashes'}, indent=1, default=str))
    print(by_year.round(4).to_string(index=False))
