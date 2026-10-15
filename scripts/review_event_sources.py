"""Compare three SWAN-SF events with a saved NOAA/JSOC source snapshot."""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd

from helio24.data import ROOT
from helio24.full_data import sha256
from helio24.sensitivity import verify_report
from helio24.source_review import match_xra, parse_events, parse_harp_table, parse_jsoc, parse_srs

CASES = {8765: [4466], 8864: [4502], 9529: [4920, 4941]}


def run(root=ROOT):
    directory = root / 'data/source_review'
    output = root / 'artifacts/source_review'
    if output.exists():
        raise RuntimeError('Preserve the existing source review before rerunning')
    manifest_path = directory / 'manifest.json'
    manifest = json.loads(manifest_path.read_text())
    for name, entry in manifest['sources'].items():
        if entry['status'] == 'downloaded' and sha256(directory / name) != entry['sha256']:
            raise ValueError(f'Source snapshot changed: {name}')

    def read(name):
        entry = manifest['sources'][name]
        if entry['status'] != 'downloaded':
            return None
        return (directory / name).read_text()

    verify_report(root, root / 'artifacts/event_provenance', check_code=True)
    verify_report(root, root / 'artifacts/label_sensitivity', check_code=True)
    catalog = pd.read_csv(root / 'data/flare_catalog.csv').set_index('flare_id')
    annotations = pd.read_csv(root / 'artifacts/event_provenance/annotations.csv')
    table_text = read('all_harps_with_noaa_ars.txt')
    harp_table = parse_harp_table(table_text) if table_text is not None else {}
    cases, rows, keywords, positions = [], [], [], []
    for flare_id, harps in CASES.items():
        event = catalog.loc[flare_id].to_dict()
        date = pd.Timestamp(event['start_time'])
        name = date.strftime('%Y%m%devents.txt')
        text = read(name)
        summary = dict(flare_id=flare_id, date=str(date.date()), goes_class=event['goes_class'],
                       catalog_noaa_region=int(event['noaa_active_region']), candidate_harps=harps,
                       noaa_xra_status='unavailable', noaa_xra_region=None, noaa_event_number=None,
                       report_regions=[], optical_positions=[], source_region_conflict=None,
                       harp_evidence=[], adjudication='unresolved; no automatic relabeling')
        if text is not None:
            xra, related = match_xra(parse_events(text, date), event)
            regions = sorted({row['noaa_region'] for row in related if row['noaa_region'] is not None})
            summary.update(noaa_xra_status='exact_match', noaa_xra_region=xra['noaa_region'],
                           noaa_event_number=xra['event_number'], report_regions=regions,
                           source_region_conflict=len(regions) > 1,
                           optical_positions=[row['location_frequency'] for row in related if row['kind'] == 'FLA'])
            rows.extend(dict(flare_id=flare_id, source=name, **row) for row in related)
        srs_name = (date+pd.Timedelta(days=1)).strftime('%Y%m%dSRS.txt')
        srs_text = read(srs_name)
        if srs_text is not None:
            validity, regions = parse_srs(srs_text)
            positions.extend(dict(flare_id=flare_id, source=srs_name, validity=validity, **row) for row in regions)
        for harp in harps:
            text = read(f'harp_{harp}.json')
            samples = parse_jsoc(text, harp) if text is not None else []
            keywords.extend(dict(flare_id=flare_id, **sample) for sample in samples)
            available = [sample for sample in samples if sample['noaa_association_available']]
            summary['harp_evidence'].append(dict(
                harp=harp, table_status='present' if harp in harp_table else
                ('absent_from_current_table' if table_text is not None else 'unavailable'),
                table_noaa_regions=harp_table.get(harp), keyword_records=len(samples),
                records_with_noaa_association=len(available),
                keyword_noaa_regions=sorted({region for sample in available for region in sample['noaa_regions']}),
                transport=manifest['sources'][f'harp_{harp}.json']['transport']))
        cases.append(summary)
    source_paths = [manifest_path, root / 'data/flare_catalog.csv', root / 'docs/source-review-protocol.md',
                    root / 'artifacts/event_provenance/report.json',
                    root / 'artifacts/event_provenance/annotations.csv',
                    root / 'artifacts/label_sensitivity/report.json']
    source_paths += [directory / name for name, entry in manifest['sources'].items() if entry['status'] == 'downloaded']
    report = dict(scope='Exploratory primary-source review; unchanged labels and predictions', cases=cases,
                  source_hashes={str(p.relative_to(root)): sha256(p) for p in source_paths},
                  code_hashes={name: sha256(root / name) for name in [
                      'helio24/source_review.py', 'scripts/review_event_sources.py', 'scripts/fetch_source_review.py']})
    output.mkdir(parents=True)
    pd.DataFrame(rows).to_csv(output / 'noaa_event_rows.csv', index=False)
    pd.DataFrame(keywords).to_csv(output / 'jsoc_keywords.csv', index=False)
    pd.DataFrame(positions).to_csv(output / 'noaa_region_positions.csv', index=False)
    annotations[annotations.flare_id.isin(CASES)].to_csv(output / 'archive_annotations.csv', index=False)
    (output / 'protocol.md').write_text((root / 'docs/source-review-protocol.md').read_text())
    report['artifact_hashes'] = {p.name: sha256(p) for p in output.iterdir()}
    (output / 'report.json').write_text(json.dumps(report, indent=2, allow_nan=False))
    print(json.dumps(cases, indent=2))
    return report


if __name__ == '__main__':
    run()
