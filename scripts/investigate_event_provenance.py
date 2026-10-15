"""Inspect both archive history methods and timing conventions; no relabeling."""
import hashlib
import io
import json
from pathlib import Path
import sys
import tarfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd

from helio24.data import ROOT, parse_name
from helio24.event_mapping import parse_annotations
from helio24.full_data import sha256
from helio24.provenance import association_evidence, timing_evidence


def run(root=ROOT):
    output = root / 'artifacts/event_provenance'
    if output.exists():
        raise RuntimeError('Preserve the existing provenance investigation before rerunning')
    archive = root / 'data/downloads/partition4_instances.tar.gz'
    metadata = json.loads((root / 'data/dataverse-metadata.json').read_text())
    source = next(f['dataFile'] for f in metadata['data']['latestVersion']['files']
                  if f['dataFile']['filename'] == archive.name)
    with archive.open('rb') as stream:
        archive_md5 = hashlib.file_digest(stream, 'md5').hexdigest()
    if archive_md5 != source['checksum']['value']:
        raise ValueError('Archive checksum mismatch')
    catalog = pd.read_csv(root / 'data/flare_catalog.csv').set_index('flare_id')
    if not catalog.index.is_unique:
        raise ValueError('Duplicate catalog event')
    catalog_rows = catalog.to_dict('index')
    columns = ['MFLARE_LABEL', 'XFLARE_LABEL', 'MFLARE_LABEL_LOC', 'XFLARE_LABEL_LOC']
    locations = ['LAT_MIN', 'LAT_MAX', 'LON_MIN', 'LON_MAX', 'IS_TMFI', 'QUALITY']
    unique, filenames, case_measurements = {}, [], {}
    inspected = 0
    with tarfile.open(archive, 'r|gz') as tar:
        for member in tar:
            if not member.isfile() or not member.name.endswith('.csv'):
                continue
            meta = parse_name(member.name)
            inspected += 1
            if meta['target'] or meta['harp'] == 4502:
                filenames.append(dict(archive_member=member.name, **meta))
            frame = pd.read_csv(io.BytesIO(tar.extractfile(member).read()), sep='\t',
                                usecols=['Timestamp', *columns, *locations])
            for column in columns:
                for stamp, annotation in frame.loc[frame[column].notna(), ['Timestamp', column]].itertuples(index=False, name=None):
                    for magnitude, flare_id, verification in parse_annotations(annotation):
                        event = catalog_rows.get(flare_id)
                        if event is None or event['goes_class'] != magnitude:
                            raise ValueError(f'Catalog mismatch for event {flare_id}')
                        key = (meta['harp'], stamp, column, flare_id)
                        record = dict(harp=meta['harp'], timestamp=stamp, source=column, flare_id=flare_id,
                                      magnitude=magnitude, verification=verification, peak_time=event['peak_time'],
                                      **timing_evidence(stamp, event['peak_time']))
                        if key in unique and unique[key] != record:
                            raise ValueError('Overlapping copies disagree on an annotation')
                        unique[key] = record
            if meta['harp'] == 4502:
                for record in frame.to_dict('records'):
                    stamp = pd.Timestamp(record['Timestamp'])
                    if abs(stamp-pd.Timestamp(catalog_rows[8864]['peak_time'])) <= pd.Timedelta(hours=1):
                        case_measurements[str(stamp)] = record
            if inspected % 10000 == 0:
                print(f'Provenance: {inspected:,} windows inspected', flush=True)
    annotations = pd.DataFrame(unique.values()).sort_values(['flare_id', 'harp', 'timestamp', 'source'])
    verified = annotations[annotations.verification.isin(['Primary', 'Secondary'])]
    associations = association_evidence(verified)
    timing = verified.groupby('source').agg(
        records=('flare_id', 'size'), unique_events=('flare_id', 'nunique'),
        nearest_compatible=('nearest_12min_compatible', 'sum'),
        containing_compatible=('containing_12min_compatible', 'sum'),
        min_offset_minutes=('offset_minutes', 'min'), max_offset_minutes=('offset_minutes', 'max'))
    filenames = pd.DataFrame(filenames)
    case = annotations[annotations.flare_id == 8864]
    case_peak = pd.Timestamp(catalog_rows[8864]['peak_time'])
    case_windows = filenames[(filenames.harp == 4502) & (filenames.forecast_time <= case_peak) &
                             (filenames.prediction_end > case_peak)]
    report = dict(scope='Archive provenance investigation; no relabeling, refitting, or threshold changes',
                  inspected=inspected, archive_md5=archive_md5,
                  case_event=8864, case_associations=associations[associations.flare_id == 8864].to_dict('records'),
                  case_history_records=case.to_dict('records'),
                  case_filename_harps=sorted(map(int, filenames.loc[filenames.flare_id == 8864, 'harp'].unique())),
                  case_region_forecasts_covering_peak=len(case_windows),
                  case_region_positive_forecasts=int(case_windows.target.sum()),
                  timing=timing.reset_index().to_dict('records'),
                  association_method_counts=associations.association_method.value_counts().to_dict(),
                  source_hashes={str(path.relative_to(root)): sha256(path) for path in [
                      root / 'data/flare_catalog.csv', root / 'data/dataverse-metadata.json',
                      root / 'artifacts/event_audit/report.json']},
                  code_hashes={name: sha256(root / name) for name in [
                      'helio24/provenance.py', 'helio24/event_mapping.py', 'helio24/data.py',
                      'scripts/investigate_event_provenance.py']})
    output.mkdir(parents=True)
    annotations.to_csv(output / 'annotations.csv', index=False)
    associations.to_csv(output / 'associations.csv', index=False)
    timing.to_csv(output / 'timing.csv')
    filenames.to_csv(output / 'filenames.csv', index=False)
    case_windows.to_csv(output / 'case_windows.csv', index=False)
    pd.DataFrame(case_measurements.values()).sort_values('Timestamp').to_csv(output / 'case_measurements.csv', index=False)
    report['artifact_hashes'] = {p.name: sha256(p) for p in output.iterdir()}
    (output / 'report.json').write_text(json.dumps(report, indent=2, allow_nan=False))
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    run()
