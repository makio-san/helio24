"""Scan pre-2024 V2 identifiers through verified archives without reading outcomes."""
import argparse
from collections import Counter, defaultdict
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
from helio24.v2_contract import tai_to_utc, tai_utc_offset, utc_to_tai
from helio24.v2_sources import validate_manifest


def inspect_member(path, name, size, cutoff_tai, roles):
    frame = pd.read_parquet(path, columns=['harp_number', 'obs_start'],
                            filters=[('obs_start', '<', cutoff_tai)])
    if frame.empty:
        return {'member': name, 'member_bytes': size, 'joined_rows': 0,
                'observation_rows': 0, 'harps': {}}
    clocks = pd.to_datetime(frame.obs_start, errors='raise')
    if clocks.dt.tz is not None or clocks.ge(cutoff_tai).any():
        raise ValueError('Development filter failed at the Parquet scan boundary')
    frame = frame.assign(obs_start=clocks)
    joined_rows = len(frame)
    frame = frame.drop_duplicates(['harp_number', 'obs_start'])
    if frame.harp_number.isna().any() or (frame.harp_number <= 0).any():
        raise ValueError('Invalid HARP identifier')
    audit = {}
    for harp, group in frame.groupby('harp_number'):
        stamps = group.obs_start.sort_values().reset_index(drop=True)
        diffs = stamps.diff().iloc[1:]
        bad = diffs.ne(pd.Timedelta(minutes=12))
        counts, boundary_removed, leap_removed = Counter(), 0, 0
        bad_prefix = bad.astype(int).cumsum()
        for start_index in range(0, max(0, len(stamps)-59), 5):
            end_index = start_index+59
            bad_before = int(bad_prefix.iloc[start_index-1]) if start_index else 0
            if int(bad_prefix.iloc[end_index-1])-bad_before:
                continue
            start_tai = stamps.iloc[start_index]
            forecast_tai = start_tai+pd.Timedelta(hours=12)
            if tai_utc_offset(start_tai) != tai_utc_offset(forecast_tai):
                leap_removed += 1
                continue
            observation_start = tai_to_utc(start_tai)
            forecast = tai_to_utc(forecast_tai)
            prediction_end = forecast+pd.Timedelta(hours=24)
            assigned = False
            for role, (left, right) in roles.items():
                if left <= forecast < right:
                    assigned = True
                    if observation_start >= left and prediction_end <= right:
                        counts[role] += 1
                    else:
                        boundary_removed += 1
                    break
            if not assigned:
                boundary_removed += 1
        audit[str(int(harp))] = {
            'rows': len(stamps), 'first_tai': stamps.iloc[0].isoformat(),
            'last_tai': stamps.iloc[-1].isoformat(),
            'cadence_breaks': int(bad.sum()), 'candidate_windows': dict(counts),
            'boundary_removed': boundary_removed, 'leap_removed': leap_removed,
        }
    return {'member': name, 'member_bytes': size, 'joined_rows': joined_rows,
            'observation_rows': len(frame), 'harps': audit}


def scan_partition(item, cutoff_tai, roles, attempts=3):
    return stream_verified_archive_with_retries(
        item, lambda path, name, size: inspect_member(
            path, name, size, cutoff_tai, roles),
        temporary_root=ROOT / 'data/cache', attempts=attempts)


def run(output, workers=4):
    manifest_path = ROOT / 'config/swan_sf_v2_sources.verified.json'
    protocol_path = ROOT / 'config/experiment5-v3.json'
    manifest = json.loads(manifest_path.read_text())
    protocol = json.loads(protocol_path.read_text())
    errors = validate_manifest(manifest, require_hashes=True)
    if errors:
        raise ValueError('; '.join(errors))
    if output.exists():
        raise RuntimeError('Preserve the existing layout audit')
    roles = {name: tuple(map(pd.Timestamp, protocol['roles'][name]))
             for name in ['train', 'calibration', 'validation']}
    cutoff_tai = utc_to_tai(pd.Timestamp(protocol['roles']['test'][0]))
    partitions = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(scan_partition, item, cutoff_tai, roles): item['partition']
                   for item in manifest['archives']}
        for future in as_completed(futures):
            result = future.result()
            partitions.append(result)
            print(f'partition {result["partition"]}: {result["members"]} members verified', flush=True)

    locations, harp_rows = defaultdict(list), defaultdict(lambda: Counter())
    joined_rows = observation_rows = cadence_breaks = boundary_removed = leap_removed = 0
    for partition in partitions:
        for member in partition['results']:
            joined_rows += member['joined_rows']
            observation_rows += member['observation_rows']
            for harp, values in member['harps'].items():
                locations[harp].append((partition['partition'], member['member']))
                cadence_breaks += values['cadence_breaks']
                boundary_removed += values['boundary_removed']
                leap_removed += values['leap_removed']
                harp_rows[harp].update(values['candidate_windows'])
    split_harps = {harp: where for harp, where in locations.items() if len(where) != 1}
    role_counts, shared_removed, owners = Counter(), Counter(), {}
    order = ['train', 'calibration', 'validation']
    for harp, counts in harp_rows.items():
        active = [role for role in order if counts[role]]
        if not active:
            continue
        owner = active[0]
        owners[harp] = owner
        role_counts[owner] += counts[owner]
        for role in active[1:]:
            shared_removed[role] += counts[role]
    report = {
        'scope': 'Identifier-only pre-2024 Parquet scan; no outcome, measurement or model columns',
        'completed_utc': datetime.now(timezone.utc).isoformat(),
        'parquet_filter': f'obs_start < {cutoff_tai.isoformat()} TAI',
        'joined_rows': joined_rows,
        'distinct_observation_rows_within_members': observation_rows,
        'harps': len(locations),
        'archive_members': sum(item['members'] for item in partitions),
        'harps_spanning_members': len(split_harps),
        'cadence_breaks': cadence_breaks,
        'candidate_windows_after_role_boundaries_and_harp_ownership': dict(role_counts),
        'boundary_windows_removed': boundary_removed,
        'leap_crossing_windows_removed': leap_removed,
        'shared_harp_windows_removed': dict(shared_removed),
        'ready_for_measurement_scan': not split_harps and all(role_counts[role] for role in order),
        'source_hashes': {
            'config/swan_sf_v2_sources.verified.json': sha256(manifest_path),
            'config/experiment5-v3.json': sha256(protocol_path),
        },
        'code_hashes': {
            'helio24/v2_archive.py': sha256(ROOT / 'helio24/v2_archive.py'),
            'helio24/v2_contract.py': sha256(ROOT / 'helio24/v2_contract.py'),
            'scripts/audit_v2_layout.py': sha256(ROOT / 'scripts/audit_v2_layout.py'),
        },
        'partitions': [{k: v for k, v in item.items() if k != 'results'}
                       for item in sorted(partitions, key=lambda value: value['partition'])],
        'split_harps': split_harps,
    }
    output.mkdir(parents=True)
    (output / 'report.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k: v for k, v in report.items() if k not in {'source_hashes', 'code_hashes', 'split_harps'}}, indent=2))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'artifacts/v2_layout_audit')
    parser.add_argument('--workers', type=int, choices=range(1, 5), default=4)
    args = parser.parse_args()
    run(args.output, args.workers)
