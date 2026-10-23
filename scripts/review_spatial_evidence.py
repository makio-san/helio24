"""Freeze inspected historical browse frames and retain unresolved HARP identities."""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd
from PIL import Image
from helio24.data import ROOT
from helio24.full_data import sha256
from helio24.sensitivity import verify_report
from helio24.spatial_review import validate_frame, disposition

# Transcribed after viewing all six original images, not inferred from filenames.
WATERMARKS = {
    (8765, 'before'): '2014-08-21 13:13:45', (8765, 'peak'): '2014-08-21 13:31:00',
    (8765, 'end'): '2014-08-21 13:41:48', (8864, 'before'): '2014-09-03 13:14:45',
    (8864, 'peak'): '2014-09-03 13:54:12', (8864, 'end'): '2014-09-03 14:23:09',
}


def run():
    directory = ROOT / 'data/spatial_review'
    manifest_path = directory / 'manifest.json'
    manifest = json.loads(manifest_path.read_text())
    catalog_path = ROOT / 'data/flare_catalog.csv'
    if sha256(catalog_path) != manifest['catalog_sha256']:
        raise ValueError('Catalog changed')
    previous = ROOT / 'artifacts/source_review'
    verify_report(ROOT, previous, check_code=True)
    source_hashes = {str(manifest_path.relative_to(ROOT)): sha256(manifest_path),
                     str(catalog_path.relative_to(ROOT)): sha256(catalog_path),
                     'artifacts/source_review/report.json': sha256(previous / 'report.json')}
    records = [manifest['source_listing']]
    for frame in manifest['frames']:
        records.extend([frame['metadata'], frame.get('image', {})])
    for record in records:
        if record.get('status') != 'downloaded':
            raise ValueError('Missing spatial source')
        path = directory / record['file']
        if sha256(path) != record['sha256']:
            raise ValueError(f'Source changed: {path.name}')
        source_hashes[str(path.relative_to(ROOT))] = sha256(path)
    if len(manifest['frames']) != 6 or {(f['flare_id'], f['stage']) for f in manifest['frames']} != set(WATERMARKS):
        raise ValueError('Expected all six unique context frames')
    rows = []
    for frame in manifest['frames']:
        key = (frame['flare_id'], frame['stage'])
        metadata = json.loads((directory / frame['metadata']['file']).read_text())
        actual = validate_frame(frame, metadata, WATERMARKS[key])
        with Image.open(directory / frame['image']['file']) as picture:
            if picture.format != 'PNG' or picture.size != (1024, 1024):
                raise ValueError('Unexpected rendered image format')
            picture.verify()
        rows.append(dict(flare_id=key[0], stage=key[1], requested_utc=frame['requested_utc'], actual_utc=actual,
                         offset_seconds=frame['offset_seconds'], image_id=frame['image_id'],
                         image_file=frame['image']['file'], watermark_reviewed=True))
    cases = [disposition(k) for k in [8765, 8864]]
    output = ROOT / 'artifacts/spatial_review'
    output.mkdir(exist_ok=False)
    pd.DataFrame(rows).to_csv(output / 'frames.csv', index=False)
    pd.DataFrame(cases).to_csv(output / 'case_dispositions.csv', index=False)
    report = dict(scope='Qualitative two-event image-source review; unchanged labels, models and metrics',
                  cases=cases, frames=rows, source_hashes=source_hashes,
                  limitations=['Browse images, not calibrated FITS photometry', 'Saturation and exposure differences',
                               'Three timestamps do not exclude concurrent flares', 'No WCS HARP registration or definitive relabeling'],
                  code_hashes={p: sha256(ROOT / p) for p in ['scripts/fetch_spatial_review.py', 'scripts/review_spatial_evidence.py', 'helio24/spatial_review.py']},
                  artifact_hashes={p.name: sha256(p) for p in output.glob('*.csv')})
    (output / 'report.json').write_text(json.dumps(report, indent=2, allow_nan=False))
    print(pd.DataFrame(rows).to_string(index=False))
    print(json.dumps(cases, indent=2))


if __name__ == '__main__':
    run()
