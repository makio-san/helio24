"""Recover catalog/HARP associations from archive evidence, never model inputs."""
import hashlib
import io
import json
import re
import tarfile

import pandas as pd

from helio24.data import ROOT, parse_name
from helio24.full_data import sha256

ANNOTATION = re.compile(r'([MX]\d+(?:\.\d+)?)@(\d+):(Primary|Secondary|Non-verified)')


def parse_annotations(value):
    """Accept compact, optionally bracketed lists; reject unrecognized payloads."""
    if pd.isna(value) or str(value).strip() in ('', 'None', 'null'):
        return []
    text = str(value).strip()
    matches = list(ANNOTATION.finditer(text))
    remainder = ANNOTATION.sub('', text)
    if not matches or remainder.strip(" []{}(),'\";|\t"):
        raise ValueError(f'Unrecognized history annotation: {text}')
    return [(m[1], int(m[2]), m[3]) for m in matches]


def prepare_mapping(root=ROOT):
    destination = root / 'data/event_mapping'
    destination.mkdir(parents=True, exist_ok=True)
    archive = root / 'data/downloads/partition4_instances.tar.gz'
    metadata = json.loads((root / 'data/dataverse-metadata.json').read_text())
    source = next(f['dataFile'] for f in metadata['data']['latestVersion']['files']
                  if f['dataFile']['filename'] == archive.name)
    with archive.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'md5').hexdigest()
    if digest != source['checksum']['value']:
        raise ValueError('Partition-4 archive checksum mismatch')
    fingerprint = dict(archive_md5=digest, catalog_sha256=sha256(root / 'data/flare_catalog.csv'),
                       code_sha256=sha256(__file__), data_code_sha256=sha256(root / 'helio24/data.py'))
    manifest = destination / 'manifest.json'
    if manifest.exists():
        saved = json.loads(manifest.read_text())
        if saved['source'] == fingerprint and all(
            sha256(destination / name) == value for name, value in saved['files'].items()
        ):
            return saved
    catalog = pd.read_csv(root / 'data/flare_catalog.csv').set_index('flare_id')
    if not catalog.index.is_unique:
        raise ValueError('Catalog IDs must be unique')
    events = catalog.to_dict('index')
    evidence, rejected, seen = {}, [], set()
    inspected = 0

    def add(harp, magnitude, flare_id, verification, source_name, time, end=None):
        key = (harp, flare_id, source_name, str(time))
        if key in seen:
            return
        seen.add(key)
        event = events.get(flare_id)
        reason = None
        if verification not in ('Primary', 'Secondary'):
            reason = 'unverified'
        elif event is None:
            reason = 'catalog_id_missing'
        elif event['goes_class'] != magnitude:
            reason = 'catalog_magnitude_mismatch'
        else:
            peak = pd.Timestamp(event['peak_time'])
            if source_name == 'filename' and not time <= peak < end:
                reason = 'peak_outside_forecast'
            elif source_name == 'history_location' and abs(peak-time) > pd.Timedelta(minutes=6):
                reason = 'peak_not_near_annotation'
        if reason:
            rejected.append(dict(harp=harp, flare_id=flare_id, source=source_name,
                                 timestamp=str(time), reason=reason))
        else:
            evidence.setdefault((harp, flare_id), set()).add(source_name)

    with tarfile.open(archive, 'r|gz') as tar:
        for member in tar:
            if not member.isfile() or not member.name.endswith('.csv'):
                continue
            meta = parse_name(member.name)
            inspected += 1
            if meta['target']:
                magnitude, rest = meta['label'].split('@')
                _, verification = rest.split(':')
                add(meta['harp'], magnitude, meta['flare_id'], verification, 'filename',
                    meta['forecast_time'], meta['prediction_end'])
            frame = pd.read_csv(io.BytesIO(tar.extractfile(member).read()), sep='\t',
                                usecols=['Timestamp', 'MFLARE_LABEL_LOC', 'XFLARE_LABEL_LOC'])
            for column in ['MFLARE_LABEL_LOC', 'XFLARE_LABEL_LOC']:
                for stamp, value in frame.loc[frame[column].notna(), ['Timestamp', column]].itertuples(index=False, name=None):
                    for magnitude, flare_id, verification in parse_annotations(value):
                        add(meta['harp'], magnitude, flare_id, verification, 'history_location', pd.Timestamp(stamp))
            if inspected % 10000 == 0:
                print(f'Mapping: {inspected:,} archive windows inspected', flush=True)
    rows = [dict(harp=harp, flare_id=flare_id, evidence=';'.join(sorted(sources)))
            for (harp, flare_id), sources in sorted(evidence.items())]
    mapping = pd.DataFrame(rows, columns=['harp', 'flare_id', 'evidence'])
    mapping['ambiguous'] = mapping.groupby('flare_id').harp.transform('nunique').gt(1)
    mapping.to_csv(destination / 'associations.csv', index=False)
    pd.DataFrame(rejected, columns=['harp', 'flare_id', 'source', 'timestamp', 'reason']).to_csv(
        destination / 'rejected.csv', index=False)
    result = dict(source=fingerprint, inspected=inspected, associations=len(mapping), rejected=len(rejected),
                  files={name: sha256(destination / name) for name in ['associations.csv', 'rejected.csv']})
    manifest.write_text(json.dumps(result, indent=2))
    return result
