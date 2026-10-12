"""Memory-bounded feature preparation directly from verified SWAN-SF archives."""
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
import hashlib
import io
import json
from pathlib import Path
import tarfile

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from helio24.data import ROOT, parse_name, read_observation, extract_features


def sha256(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def prepare_partition(partition):
    destination = ROOT / 'data/full'
    destination.mkdir(parents=True, exist_ok=True)
    archive = ROOT / f'data/downloads/partition{partition}_instances.tar.gz'
    metadata = json.loads((ROOT / 'data/dataverse-metadata.json').read_text())
    info = next(f['dataFile'] for f in metadata['data']['latestVersion']['files'] if f['dataFile']['filename'] == archive.name)
    with archive.open('rb') as stream:
        checksum = hashlib.file_digest(stream, 'md5').hexdigest()
    if checksum != info['checksum']['value']:
        raise ValueError(f'Archive checksum mismatch: {archive.name}')
    fingerprint = hashlib.sha256((sha256(Path(__file__)) + sha256(ROOT / 'helio24/data.py') +
                                  sha256(ROOT / 'data/flare_catalog.csv')).encode()).hexdigest()
    output = destination / f'partition{partition}.parquet'
    audit_path = destination / f'partition{partition}.json'
    if output.exists() and audit_path.exists():
        audit = json.loads(audit_path.read_text())
        if (audit['code_catalog_hash'] == fingerprint and audit['archive_md5'] == checksum
                and audit['features_sha256'] == sha256(output)):
            print(f'Partition {partition}: verified feature cache reused', flush=True)
            return audit
    catalog = pd.read_csv(ROOT / 'data/flare_catalog.csv').set_index('flare_id')
    catalog['peak_time'] = pd.to_datetime(catalog.peak_time)
    events = catalog[['peak_time', 'goes_class']].to_dict('index')
    pending, exclusions = [], []
    counts, retained_counts, missing_totals = Counter(), Counter(), Counter()
    inspected = accepted = untrusted = 0
    writer = None
    partial = output.with_suffix('.parquet.part')

    def flush():
        nonlocal writer
        if not pending:
            return
        frame = pd.DataFrame(pending)
        for column in ['observation_start', 'observation_last', 'forecast_time', 'prediction_end', 'peak_time']:
            frame[column] = pd.to_datetime(frame[column]).astype('datetime64[ns]')
        batch = pa.Table.from_pandas(frame, preserve_index=False)
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
                frame = read_observation(io.BytesIO(tar.extractfile(member).read()), meta, magnetic_only=True)
                features, quality, missing = extract_features(frame)
                missing_totals.update(missing)
                untrusted += quality['untrusted_rows']
                reasons, peak = [], pd.NaT
                if meta['flare_id'] != -1:
                    event = events.get(meta['flare_id'])
                    if event is None:
                        reasons.append('catalog_id_missing')
                    else:
                        peak = event['peak_time']
                        if event['goes_class'] != meta['label'].split('@')[0]:
                            reasons.append('catalog_magnitude_mismatch')
                        if not meta['forecast_time'] <= peak < meta['prediction_end']:
                            reasons.append('catalog_peak_outside_window')
                if quality['max_missing_fraction'] > 0.2:
                    reasons.append('excessive_missing_or_untrusted')
                if reasons:
                    exclusions.append(dict(member=member.name, label=meta['label'], reasons=';'.join(reasons)))
                else:
                    pending.append(dict(partition=partition, archive_member=member.name, **meta,
                                        peak_time=peak, missing_fraction=quality['masked_missing']/1440, **features))
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
    pd.DataFrame(exclusions, columns=['member', 'label', 'reasons']).to_csv(destination / f'partition{partition}-exclusions.csv', index=False)
    audit = dict(partition=partition, archive_md5=checksum, code_catalog_hash=fingerprint,
                 features_sha256=sha256(output), inspected=inspected, accepted=accepted,
                 excluded=len(exclusions), full_class_counts=dict(counts), retained_class_counts=dict(retained_counts),
                 raw_missing_by_parameter=dict(missing_totals), untrusted_rows=untrusted)
    audit_path.write_text(json.dumps(audit, indent=2))
    print(f'Partition {partition}: complete ({accepted:,} accepted)', flush=True)
    return audit


def prepare_all(partitions=(1, 2, 3, 4, 5), workers=2):
    with ProcessPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(prepare_partition, partitions))
