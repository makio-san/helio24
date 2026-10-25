"""Reconcile pre-2024 V2 attached events with the frozen HEK major inventory."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd

from helio24.data import ROOT
from helio24.full_data import sha256
from helio24.v2_archive import stream_verified_archive_with_retries
from helio24.v2_contract import EVENT_COLUMNS, audit_event_rows, prepare_events, utc_to_tai
from helio24.v2_labels import reconcile_major_events
from helio24.v2_sources import validate_manifest


def inspect_member(path, name, size, cutoff_tai):
    frame = pd.read_parquet(path, columns=['obs_start', *EVENT_COLUMNS],
                            filters=[('obs_start', '<', cutoff_tai)])
    events, errors = audit_event_rows(frame[EVENT_COLUMNS])
    return {'member': name, 'member_bytes': size,
            'events': events[EVENT_COLUMNS].to_dict('records'),
            'event_errors': errors}


def scan_partition(item, cutoff_tai):
    return stream_verified_archive_with_retries(
        item, lambda path, name, size: inspect_member(path, name, size, cutoff_tai),
        temporary_root=ROOT / 'data/cache')


def run(output, inventory, workers=1):
    if output.exists():
        raise RuntimeError('Preserve the existing label inventory audit')
    manifest_path = ROOT / 'config/swan_sf_v2_sources.verified.json'
    protocol_path = ROOT / 'config/experiment5-v4.json'
    manifest = json.loads(manifest_path.read_text())
    protocol = json.loads(protocol_path.read_text())
    errors = validate_manifest(manifest, require_hashes=True)
    if errors:
        raise ValueError('; '.join(errors))
    inventory_report_path = inventory / 'report.json'
    inventory_events_path = inventory / 'events.csv'
    inventory_report = json.loads(inventory_report_path.read_text())
    if sha256(inventory_events_path) != inventory_report['events_sha256']:
        raise ValueError('Frozen HEK events hash mismatch')
    cutoff_tai = utc_to_tai(pd.Timestamp(protocol['roles']['test'][0]))
    partitions = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(scan_partition, item, cutoff_tai): item['partition']
                   for item in manifest['archives']}
        for future in as_completed(futures):
            result = future.result()
            partitions.append(result)
            print(f'partition {result["partition"]}: {result["members"]} members verified', flush=True)

    rows, event_errors = [], Counter()
    for partition in partitions:
        for member in partition['results']:
            rows.extend(member['events'])
            event_errors.update(member['event_errors'])
    attached = prepare_events(pd.DataFrame(rows, columns=EVENT_COLUMNS))
    external = pd.read_csv(inventory_events_path)
    reconciliation, unassigned, v2_only, conflicts = reconcile_major_events(attached, external)
    output.mkdir(parents=True)
    unassigned.to_csv(output / 'unassigned_major_events.csv', index=False)
    v2_only.to_csv(output / 'v2_only_peak_class.csv', index=False)
    conflicts.to_csv(output / 'peak_class_conflicts.csv', index=False)
    complete = not reconciliation['v2_only_peak_class'] and not reconciliation['peak_class_conflicts']
    report = {
        'scope': 'Pre-2024 V2 attached GOES M/X events versus frozen monthly HEK/SWPC inventory; no model fitting or scoring',
        'completed_utc': datetime.now(timezone.utc).isoformat(),
        'parquet_filter': f'obs_start < {cutoff_tai.isoformat()} TAI',
        'reconciliation': reconciliation,
        'invalid_attached_event_rows_excluded': sum(event_errors.values()),
        'invalid_attached_event_reasons': dict(event_errors),
        'inventory_complete_for_labeling': complete,
        'decision': ('Complete inventory may be used with fail-closed exclusions'
                     if complete else 'Inventory reconciliation requires adjudication'),
        'source_hashes': {
            'config/swan_sf_v2_sources.verified.json': sha256(manifest_path),
            'config/experiment5-v4.json': sha256(protocol_path),
            str(inventory_report_path.relative_to(ROOT)): sha256(inventory_report_path),
            str(inventory_events_path.relative_to(ROOT)): sha256(inventory_events_path),
        },
        'artifact_hashes': {
            'unassigned_major_events.csv': sha256(output / 'unassigned_major_events.csv'),
            'v2_only_peak_class.csv': sha256(output / 'v2_only_peak_class.csv'),
            'peak_class_conflicts.csv': sha256(output / 'peak_class_conflicts.csv'),
        },
        'code_hashes': {
            'helio24/v2_archive.py': sha256(ROOT / 'helio24/v2_archive.py'),
            'helio24/v2_contract.py': sha256(ROOT / 'helio24/v2_contract.py'),
            'helio24/v2_labels.py': sha256(ROOT / 'helio24/v2_labels.py'),
            'scripts/audit_v2_label_inventory.py': sha256(__file__),
        },
        'partitions': [{k: v for k, v in item.items() if k != 'results'}
                       for item in sorted(partitions, key=lambda value: value['partition'])],
    }
    (output / 'report.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k: v for k, v in report.items()
                      if k not in {'source_hashes', 'artifact_hashes', 'code_hashes'}}, indent=2))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path,
                        default=ROOT / 'artifacts/v2_label_inventory')
    parser.add_argument('--inventory', type=Path, required=True)
    parser.add_argument('--workers', type=int, choices=range(1, 3), default=1)
    args = parser.parse_args()
    run(args.output, args.inventory.resolve(), args.workers)
