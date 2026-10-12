"""Strict SWAN-SF parsing and observation-only feature extraction."""
import json
import re
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
MAGNETIC_COLUMNS = (
    'TOTUSJH TOTBSQ TOTPOT TOTUSJZ ABSNJZH SAVNCPP USFLUX TOTFZ MEANPOT '
    'EPSZ MEANSHR SHRGT45 MEANGAM MEANGBT MEANGBZ MEANGBH MEANJZH TOTFY '
    'MEANJZD MEANALP TOTFX EPSY EPSX R_VALUE'
).split()
STATISTICS = ['mean', 'std', 'last', 'delta']
FEATURE_COLUMNS = [f'{column}__{stat}' for column in MAGNETIC_COLUMNS for stat in STATISTICS]
NAME_PATTERN = re.compile(r'(?P<label>.+)_ar(?P<harp>\d+)_s(?P<start>.+)_e(?P<end>.+)\.csv')
LABEL_PATTERN = re.compile(r'(?P<magnitude>[BCMX]\d+(?:\.\d+)?)@(?P<id>\d+):(?P<verification>Primary|Secondary)')


def parse_name(path):
    match = NAME_PATTERN.fullmatch(Path(path).name)
    if not match:
        raise ValueError(f'Unrecognized SWAN-SF filename: {Path(path).name}')
    label, harp, start, end = match.group('label', 'harp', 'start', 'end')
    start, end = pd.Timestamp(start), pd.Timestamp(end)
    if end - start != pd.Timedelta(hours=12) - pd.Timedelta(minutes=12):
        raise ValueError('Expected a 12-hour observation window with 60 timestamps')
    event = LABEL_PATTERN.fullmatch(label) if label != 'FQ' else None
    if label != 'FQ' and event is None:
        raise ValueError(f'Unrecognized or unverified outcome: {label}')
    forecast = start + pd.Timedelta(hours=12)
    return dict(harp=int(harp), observation_start=start, observation_last=end,
                forecast_time=forecast, prediction_end=forecast + pd.Timedelta(hours=24),
                label=label, flare_class='N' if label == 'FQ' else label[0],
                target=int(label[0] in 'MX'),
                flare_id=int(event['id']) if event else -1)


def read_observation(path, metadata=None):
    """Fail closed on malformed or future-containing observation files."""
    metadata = metadata or parse_name(path)
    frame = pd.read_csv(path, sep='\t', na_values=['None', 'null'])
    required = ['Timestamp', 'IS_TMFI', 'QUALITY', *MAGNETIC_COLUMNS]
    missing = set(required) - set(frame.columns)
    if missing:
        raise ValueError(f'Missing columns: {sorted(missing)}')
    stamps = pd.to_datetime(frame['Timestamp'], errors='raise')
    expected = pd.date_range(metadata['observation_start'], periods=60, freq='12min')
    if len(frame) != 60 or not np.array_equal(stamps.to_numpy(), expected.to_numpy()):
        raise ValueError('Observation timestamps are missing, duplicated, unordered, or outside the window')
    frame['Timestamp'] = stamps
    return frame


def trusted_measurements(frame):
    """Preserve timestamps and gaps while masking untrusted or nonfinite values."""
    measurements = frame[MAGNETIC_COLUMNS].apply(pd.to_numeric, errors='coerce')
    measurements = measurements.replace([np.inf, -np.inf], np.nan)
    trusted = frame['IS_TMFI'].astype(str).str.lower().isin(['true', '1', '1.0'])
    trusted &= pd.to_numeric(frame['QUALITY'], errors='coerce').eq(0)
    return measurements.where(trusted, np.nan, axis=0)


def extract_features(frame):
    """Only allow listed magnetic measurements; never labels, IDs or X-ray flux."""
    measurements = frame[MAGNETIC_COLUMNS].apply(pd.to_numeric, errors='coerce')
    measurements = measurements.replace([np.inf, -np.inf], np.nan)
    raw_missing = measurements.isna().sum()
    trusted = frame['IS_TMFI'].astype(str).str.lower().isin(['true', '1', '1.0'])
    trusted &= pd.to_numeric(frame['QUALITY'], errors='coerce').eq(0)
    measurements = trusted_measurements(frame)
    values = {}
    for column in MAGNETIC_COLUMNS:
        series = measurements[column]
        values.update({f'{column}__mean': series.mean(),
                       f'{column}__std': series.std(ddof=0),
                       f'{column}__last': series.iloc[-1],
                       f'{column}__delta': series.iloc[-1] - series.iloc[0]})
    quality = dict(raw_missing=int(raw_missing.sum()),
                   masked_missing=int(measurements.isna().sum().sum()),
                   untrusted_rows=int((~trusted).sum()),
                   max_missing_fraction=float(measurements.isna().mean().max()))
    return values, quality, raw_missing.to_dict()


def build_dataset(partitions=(1, 3, 5), root=ROOT):
    """Read manifest-selected files; save all exclusions and data-quality counts."""
    catalog = pd.read_csv(root / 'data/flare_catalog.csv').set_index('flare_id')
    records, exclusions, partition_audit = [], [], []
    for partition in partitions:
        manifest = json.loads((root / f'data/partition{partition}-manifest.json').read_text())
        missing_totals, quality_totals = Counter(), Counter()
        accepted = 0
        for relative in manifest['files']:
            path = root / relative
            meta = parse_name(path)
            frame = read_observation(path, meta)
            features, quality, missing = extract_features(frame)
            missing_totals.update(missing)
            quality_totals.update({k: quality[k] for k in ['raw_missing', 'masked_missing', 'untrusted_rows']})
            reason = None
            peak = pd.NaT
            if meta['flare_id'] != -1:
                if meta['flare_id'] not in catalog.index:
                    reason = 'Flare ID missing from official catalog'
                else:
                    event = catalog.loc[meta['flare_id']]
                    peak = pd.Timestamp(event['peak_time'])
                    if event['goes_class'] != meta['label'].split('@')[0]:
                        reason = 'Flare magnitude differs from official catalog'
                    elif not meta['forecast_time'] <= peak < meta['prediction_end']:
                        reason = 'Catalog peak outside the exact forecast window (including rounding ambiguity)'
            if quality['max_missing_fraction'] > 0.2:
                reason = 'More than 20% missing or untrusted values in at least one magnetic parameter'
            if reason:
                exclusions.append(dict(file=relative, partition=partition, label=meta['label'], reason=reason))
                continue
            records.append(dict(file=relative, partition=partition, **meta, peak_time=peak,
                                missing_fraction=quality['masked_missing'] / (60 * 24), **features))
            accepted += 1
        partition_audit.append(dict(partition=partition, fraction=manifest['fraction'],
                                    full_class_counts=manifest['full_class_counts'],
                                    sample_class_counts=manifest['sample_class_counts'],
                                    inspected=len(manifest['files']), accepted=accepted,
                                    missing_by_parameter=dict(missing_totals), **quality_totals))
        print(f'Partition {partition}: {accepted}/{len(manifest["files"])} observations retained', flush=True)
    table = pd.DataFrame(records).sort_values(['forecast_time', 'harp']).reset_index(drop=True)
    if table.duplicated(['harp', 'forecast_time']).any():
        raise ValueError('Duplicate HARP/forecast time across the selected partitions')
    table.attrs['sample_fractions'] = {str(p['partition']): p['fraction'] for p in partition_audit}
    destination = root / 'data/prepared'
    destination.mkdir(parents=True, exist_ok=True)
    table.to_parquet(destination / 'features.parquet', index=False)
    pd.DataFrame(exclusions, columns=['file', 'partition', 'label', 'reason']).to_csv(destination / 'exclusions.csv', index=False)
    audit = dict(partitions=partition_audit, excluded=len(exclusions), retained=len(table),
                 feature_columns=FEATURE_COLUMNS, observation_hours=12, prediction_hours=24,
                 forecast_boundary='observation_start + 12h; observation end is exclusive',
                 quality_rule='Each parameter must have at least 80% trusted finite observations')
    (destination / 'audit.json').write_text(json.dumps(audit, indent=2))
    return table, audit


def chronological_split(table, training=(1,), validation=(3,), test=(5,)):
    """Purge boundary windows and exclude HARP identities shared with earlier sets."""
    groups = [table[table.partition.isin(parts)].copy() for parts in (training, validation, test)]
    if any(group.empty for group in groups):
        raise ValueError('Train, validation and test must all contain records')
    if set(training) & set(validation) or set(training) & set(test) or set(validation) & set(test):
        raise ValueError('Partition assignments must be disjoint')
    removed = []
    for i in (0, 1):
        boundary = groups[i + 1].observation_start.min()
        before = len(groups[i])
        groups[i] = groups[i][groups[i].prediction_end <= boundary].copy()
        removed.append(dict(split=['train', 'validation'][i], boundary_purged=before-len(groups[i])))
    seen = set()
    for name, group in zip(['train', 'validation', 'test'], groups):
        overlap = set(group.harp) & seen
        before = len(group)
        group.drop(group[group.harp.isin(overlap)].index, inplace=True)
        seen.update(group.harp)
        removed.append(dict(split=name, shared_harp_removed=before-len(group), shared_harps=sorted(overlap)))
    for group in groups:
        if group.empty or group.target.nunique() != 2:
            raise ValueError('Each cleaned split must contain both target classes')
    for left, right in zip(groups, groups[1:]):
        if left.prediction_end.max() > right.observation_start.min():
            raise ValueError('Temporal overlap remains')
    return dict(zip(['train', 'validation', 'test'], groups)), removed
