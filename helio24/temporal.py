"""Leakage-safe recent-evolution features streamed from SWAN-SF archives."""
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
import hashlib
import io
import json
import tarfile

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from helio24.data import MAGNETIC_COLUMNS, ROOT, extract_features, parse_name, read_observation, trusted_measurements
from helio24.full_data import sha256

HORIZON_SAMPLES = {1: 5, 3: 15, 6: 30}
TEMPORAL_STATISTICS = ('slope', 'change', 'diff_std')
TEMPORAL_FEATURE_COLUMNS = [
    f'{column}__recent_{hours}h_{stat}'
    for column in MAGNETIC_COLUMNS
    for hours in HORIZON_SAMPLES
    for stat in TEMPORAL_STATISTICS
]


def extract_temporal_features(frame):
    """Summarize only trusted measurements from the final 1, 3 and 6 hours."""
    values = trusted_measurements(frame).to_numpy(dtype=float, na_value=np.nan, copy=True)
    features = {}
    cadence_hours = 12 / 60
    for column_index, column in enumerate(MAGNETIC_COLUMNS):
        for hours, samples in HORIZON_SAMPLES.items():
            series = values[-samples:, column_index]
            finite = np.isfinite(series)
            positions = np.arange(samples, dtype=float)[finite] * cadence_hours
            observed = series[finite]
            slope = change = diff_std = np.nan
            if len(observed) >= 2:
                centered = positions - positions.mean()
                denominator = np.dot(centered, centered)
                if denominator > 0:
                    slope = np.dot(centered, observed-observed.mean()) / denominator
                change = observed[-1] - observed[0]
            adjacent = np.diff(series)
            adjacent = adjacent[np.isfinite(adjacent)]
            if len(adjacent) >= 2:
                diff_std = adjacent.std(ddof=0)
            prefix = f'{column}__recent_{hours}h_'
            features[prefix+'slope'] = float(slope)
            features[prefix+'change'] = float(change)
            features[prefix+'diff_std'] = float(diff_std)
    return features


def prepare_temporal_partition(partition):
    """Create a bounded temporal-feature cache without expanding an archive."""
    destination = ROOT / 'data/temporal'
    destination.mkdir(parents=True, exist_ok=True)
    archive = ROOT / f'data/downloads/partition{partition}_instances.tar.gz'
    metadata = json.loads((ROOT / 'data/dataverse-metadata.json').read_text())
    info = next(
        item['dataFile'] for item in metadata['data']['latestVersion']['files']
        if item['dataFile']['filename'] == archive.name
    )
    with archive.open('rb') as stream:
        checksum = hashlib.file_digest(stream, 'md5').hexdigest()
    if checksum != info['checksum']['value']:
        raise ValueError(f'Archive checksum mismatch: {archive.name}')
    fingerprint = hashlib.sha256((
        sha256(__file__) + sha256(ROOT / 'helio24/data.py') +
        sha256(ROOT / 'data/flare_catalog.csv')
    ).encode()).hexdigest()
    output = destination / f'partition{partition}.parquet'
    audit_path = destination / f'partition{partition}.json'
    if output.exists() and audit_path.exists():
        audit = json.loads(audit_path.read_text())
        if (audit['code_catalog_hash'] == fingerprint and audit['archive_md5'] == checksum
                and audit['features_sha256'] == sha256(output)):
            print(f'Partition {partition}: verified temporal cache reused', flush=True)
            return audit

    catalog = pd.read_csv(ROOT / 'data/flare_catalog.csv').set_index('flare_id')
    catalog['peak_time'] = pd.to_datetime(catalog.peak_time)
    events = catalog[['peak_time', 'goes_class']].to_dict('index')
    pending, counts, retained_counts = [], Counter(), Counter()
    inspected = accepted = excluded = 0
    writer = None
    partial = output.with_suffix('.parquet.part')

    def flush():
        nonlocal writer
        if not pending:
            return
        batch = pa.Table.from_pandas(pd.DataFrame(pending), preserve_index=False)
        if writer is None:
            writer = pq.ParquetWriter(partial, batch.schema, compression='zstd')
        writer.write_table(batch)
        pending.clear()

    try:
        with tarfile.open(archive, 'r|gz') as tar:
            for member in tar:
                if not member.isfile() or not member.name.endswith('.csv'):
                    continue
                meta = parse_name(member.name)
                inspected += 1
                counts[meta['flare_class']] += 1
                extracted = tar.extractfile(member)
                if extracted is None:
                    raise ValueError(f'Archive member cannot be read: {member.name}')
                frame = read_observation(io.BytesIO(extracted.read()), meta, magnetic_only=True)
                _, quality, _ = extract_features(frame)
                reasons = []
                if meta['flare_id'] != -1:
                    event = events.get(meta['flare_id'])
                    if event is None:
                        reasons.append('catalog_id_missing')
                    else:
                        if event['goes_class'] != meta['label'].split('@')[0]:
                            reasons.append('catalog_magnitude_mismatch')
                        if not meta['forecast_time'] <= event['peak_time'] < meta['prediction_end']:
                            reasons.append('catalog_peak_outside_window')
                if quality['max_missing_fraction'] > 0.2:
                    reasons.append('excessive_missing_or_untrusted')
                if reasons:
                    excluded += 1
                else:
                    pending.append(dict(
                        archive_member=member.name,
                        partition=partition,
                        harp=meta['harp'],
                        forecast_time=meta['forecast_time'].to_datetime64(),
                        target=meta['target'],
                        **extract_temporal_features(frame),
                    ))
                    accepted += 1
                    retained_counts[meta['flare_class']] += 1
                if inspected % 5000 == 0:
                    flush()
                    print(f'Partition {partition}: inspected {inspected:,}, retained {accepted:,}', flush=True)
        flush()
    finally:
        if writer is not None:
            writer.close()
    if not accepted:
        raise ValueError(f'No accepted observations in partition {partition}')
    partial.replace(output)
    audit = dict(
        partition=partition,
        archive_md5=checksum,
        code_catalog_hash=fingerprint,
        features_sha256=sha256(output),
        inspected=inspected,
        accepted=accepted,
        excluded=excluded,
        full_class_counts=dict(counts),
        retained_class_counts=dict(retained_counts),
        temporal_features=len(TEMPORAL_FEATURE_COLUMNS),
        horizons_hours=list(HORIZON_SAMPLES),
    )
    audit_path.write_text(json.dumps(audit, indent=2))
    print(f'Partition {partition}: complete ({accepted:,} accepted)', flush=True)
    return audit


def prepare_temporal_all(partitions=(1, 2, 3, 4, 5), workers=2):
    with ProcessPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(prepare_temporal_partition, partitions))
