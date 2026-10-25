"""Materialize labeled pre-2024 V2 development features without fitting models."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd

from helio24.data import FEATURE_COLUMNS, ROOT
from helio24.full_data import sha256
from helio24.v2_archive import stream_verified_archive_with_retries
from helio24.v2_contract import (
    EVENT_COLUMNS, V2_MEASUREMENTS, audit_event_rows, label_windows, utc_to_tai,
)
from helio24.v2_features import extract_harp_windows
from helio24.v2_sources import validate_manifest


def inspect_member(path, name, size, partition, roles, unassigned, shards):
    columns = ['harp_number', 'obs_start', *V2_MEASUREMENTS.values(), *EVENT_COLUMNS[1:]]
    joined = pd.read_parquet(path, columns=columns,
                             filters=[('obs_start', '<', utc_to_tai(roles['test'][0]))])
    if joined.empty:
        return {'member': name, 'member_bytes': size, 'joined_rows': 0,
                'observation_rows': 0, 'harps': [], 'retained_rows': 0,
                'label_status': {}, 'extraction': {}, 'event_errors': {}}
    observations = joined[['harp_number', 'obs_start', *V2_MEASUREMENTS.values()]].drop_duplicates()
    if observations.duplicated(['harp_number', 'obs_start']).any():
        raise ValueError('Conflicting measurements at one HARP/time key')
    events, event_errors = audit_event_rows(joined[EVENT_COLUMNS])
    frames, extraction = [], Counter()
    development_roles = {name: bounds for name, bounds in roles.items() if name != 'test'}
    for _, group in observations.groupby('harp_number'):
        frame, audit = extract_harp_windows(group, development_roles)
        frames.append(frame)
        extraction.update(audit)
    windows = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    if not windows.empty:
        windows = label_windows(windows, events, unassigned, inventory_complete=True)
        status = Counter(windows.label_status)
        windows = windows[~windows.label_status.str.startswith('excluded_')].copy()
        expected = {'harp', 'role', 'observation_start', 'forecast_time',
                    'prediction_end', 'missing_fraction', *FEATURE_COLUMNS,
                    'target', 'label_status'}
        if set(windows.columns) != expected:
            raise ValueError('Unexpected materialized feature schema')
        shard_id = hashlib.sha256(name.encode()).hexdigest()[:12]
        shard = shards / f'partition-{partition}-{shard_id}.parquet'
        windows.to_parquet(shard, index=False, compression='zstd')
        shard_record = {'file': str(shard.name), 'bytes': shard.stat().st_size,
                        'sha256': sha256(shard)}
    else:
        status, shard_record = Counter(), None
    return {
        'member': name, 'member_bytes': size, 'joined_rows': len(joined),
        'observation_rows': len(observations),
        'harps': sorted(map(int, observations.harp_number.unique())),
        'retained_rows': len(windows), 'label_status': dict(status),
        'role_rows': ({str(k): int(v) for k, v in windows.role.value_counts().items()}
                      if not windows.empty else {}),
        'role_positives': ({str(k): int(v) for k, v in windows.groupby('role').target.sum().items()}
                           if not windows.empty else {}),
        'extraction': dict(extraction), 'event_errors': event_errors,
        'shard': shard_record,
    }


def scan_partition(item, roles, unassigned, shards):
    return stream_verified_archive_with_retries(
        item, lambda path, name, size: inspect_member(
            path, name, size, item['partition'], roles, unassigned, shards),
        temporary_root=ROOT / 'data/cache')


def run(output, inventory_audit, protocol_path, workers=1):
    if output.exists():
        raise RuntimeError('Preserve the existing development materialization')
    manifest_path = ROOT / 'config/swan_sf_v2_sources.verified.json'
    manifest = json.loads(manifest_path.read_text())
    protocol = json.loads(protocol_path.read_text())
    source_report_path = inventory_audit / 'report.json'
    source_report = json.loads(source_report_path.read_text())
    unassigned_path = inventory_audit / 'unassigned_major_events.csv'
    if validate_manifest(manifest, require_hashes=True):
        raise ValueError('The verified source manifest is invalid')
    if not source_report.get('inventory_complete_for_labeling'):
        raise ValueError('The major-event inventory is not complete for labeling')
    expected_hash = source_report['artifact_hashes']['unassigned_major_events.csv']
    if sha256(unassigned_path) != expected_hash:
        raise ValueError('The unassigned-event inventory hash changed')
    if protocol.get('version') != 5:
        raise ValueError('This materializer requires the frozen Experiment 5 v5 contract')
    roles = {name: tuple(map(pd.Timestamp, bounds)) for name, bounds in protocol['roles'].items()}
    unassigned = pd.read_csv(unassigned_path)
    output.mkdir(parents=True)
    shards = output / 'shards'
    shards.mkdir()
    partitions = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(scan_partition, item, roles, unassigned, shards): item['partition']
                   for item in manifest['archives']}
        for future in as_completed(futures):
            result = future.result()
            partitions.append(result)
            print(f'partition {result["partition"]}: {result["members"]} members verified',
                  flush=True)

    seen, duplicate_harps = set(), set()
    totals = Counter()
    role_rows, role_positives = Counter(), Counter()
    extraction, event_errors = Counter(), Counter()
    shard_records = []
    for partition in partitions:
        for member in partition['results']:
            current = set(member['harps'])
            duplicate_harps.update(seen & current)
            seen.update(current)
            totals.update({key: member[key] for key in
                           ['joined_rows', 'observation_rows', 'retained_rows']})
            totals.update(member['label_status'])
            role_rows.update(member['role_rows'])
            role_positives.update(member['role_positives'])
            extraction.update(member['extraction'])
            event_errors.update(member['event_errors'])
            if member['shard']:
                shard_records.append(member['shard'])
    if duplicate_harps:
        raise ValueError(f'HARPs span archive members: {sorted(duplicate_harps)[:10]}')
    if set(role_rows) != {'train', 'calibration', 'validation'}:
        raise ValueError('Every development role must contain retained rows')
    if any(role_positives[name] <= 0 or role_positives[name] >= role_rows[name]
           for name in role_rows):
        raise ValueError('Every development role must contain both classes')
    report = {
        'scope': 'Pre-2024 V2 development features and fail-closed GOES M/X labels; no model fitting, scoring or reserved test access',
        'completed_utc': datetime.now(timezone.utc).isoformat(),
        'feature_count': len(FEATURE_COLUMNS),
        'feature_columns': FEATURE_COLUMNS,
        'rows': {name: int(role_rows[name]) for name in roles if name != 'test'},
        'positives': {name: int(role_positives[name]) for name in roles if name != 'test'},
        'label_status_before_exclusion': {key: int(totals[key]) for key in
                                          ['positive', 'negative',
                                           'excluded_ambiguous_harp',
                                           'excluded_unassigned_major_event']},
        'joined_rows': int(totals['joined_rows']),
        'observation_rows': int(totals['observation_rows']),
        'retained_rows': int(totals['retained_rows']),
        'harps': len(seen),
        'extraction_audit': dict(extraction),
        'invalid_attached_event_rows_excluded': int(sum(event_errors.values())),
        'invalid_attached_event_reasons': dict(event_errors),
        'source_hashes': {
            str(manifest_path.relative_to(ROOT)): sha256(manifest_path),
            str(protocol_path.relative_to(ROOT)): sha256(protocol_path),
            str(source_report_path.relative_to(ROOT)): sha256(source_report_path),
            str(unassigned_path.relative_to(ROOT)): sha256(unassigned_path),
        },
        'code_hashes': {name: sha256(ROOT / name) for name in [
            'helio24/v2_archive.py', 'helio24/v2_contract.py',
            'helio24/v2_features.py', 'scripts/materialize_v2_development.py']},
        'shards': sorted(shard_records, key=lambda value: value['file']),
        'partitions': [{key: value for key, value in partition.items() if key != 'results'}
                       for partition in sorted(partitions, key=lambda value: value['partition'])],
    }
    (output / 'report.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({key: value for key, value in report.items()
                      if key not in {'feature_columns', 'shards', 'source_hashes', 'code_hashes'}},
                     indent=2))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--inventory-audit', type=Path, required=True)
    parser.add_argument('--protocol', type=Path,
                        default=ROOT / 'config/experiment5-v5.json')
    parser.add_argument('--workers', type=int, choices=range(1, 3), default=1)
    args = parser.parse_args()
    run(args.output.resolve(), args.inventory_audit.resolve(), args.protocol.resolve(), args.workers)
