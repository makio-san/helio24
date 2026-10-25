"""Audit pre-2024 V2 measurements and attached events without fitting a model."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
import pandas as pd

from helio24.data import ROOT
from helio24.full_data import sha256
from helio24.v2_archive import stream_verified_archive_with_retries
from helio24.v2_contract import EVENT_COLUMNS, V2_MEASUREMENTS, prepare_events, utc_to_tai
from helio24.v2_coverage import ROLE_ORDER, audit_harp
from helio24.v2_sources import validate_manifest


def inspect_member(path, name, size, cutoff_tai, roles):
    columns = ['harp_number', 'obs_start', *V2_MEASUREMENTS.values(), *EVENT_COLUMNS[1:]]
    joined = pd.read_parquet(path, columns=columns,
                             filters=[('obs_start', '<', cutoff_tai)])
    if joined.empty:
        return {'member': name, 'member_bytes': size, 'joined_rows': 0,
                'observation_rows': 0, 'harps': {}, 'events': []}
    observations = joined[['harp_number', 'obs_start', *V2_MEASUREMENTS.values()]].drop_duplicates()
    if observations.duplicated(['harp_number', 'obs_start']).any():
        raise ValueError('Conflicting measurements at one HARP/time key')
    events = prepare_events(joined[EVENT_COLUMNS])
    audits = {}
    for harp, group in observations.groupby('harp_number'):
        harp_events = events[events.harp_number.eq(harp)]
        audits[str(int(harp))] = audit_harp(group, harp_events, roles)
    return {
        'member': name, 'member_bytes': size, 'joined_rows': len(joined),
        'observation_rows': len(observations), 'harps': audits,
        'events': events[EVENT_COLUMNS].to_dict('records'),
    }


def scan_partition(item, cutoff_tai, roles):
    return stream_verified_archive_with_retries(
        item, lambda path, name, size: inspect_member(path, name, size, cutoff_tai, roles),
        temporary_root=ROOT / 'data/cache')


def run(output, workers=4):
    manifest_path = ROOT / 'config/swan_sf_v2_sources.verified.json'
    protocol_path = ROOT / 'config/experiment5-v3.json'
    manifest = json.loads(manifest_path.read_text())
    protocol = json.loads(protocol_path.read_text())
    errors = validate_manifest(manifest, require_hashes=True)
    if errors:
        raise ValueError('; '.join(errors))
    if output.exists():
        raise RuntimeError('Preserve the existing coverage audit')
    roles = {name: tuple(map(pd.Timestamp, protocol['roles'][name])) for name in ROLE_ORDER}
    cutoff_tai = utc_to_tai(pd.Timestamp(protocol['roles']['test'][0]))
    partitions = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(scan_partition, item, cutoff_tai, roles): item['partition']
                   for item in manifest['archives']}
        for future in as_completed(futures):
            result = future.result()
            partitions.append(result)
            print(f'partition {result["partition"]}: {result["members"]} members verified', flush=True)

    locations, audits, event_rows = {}, {}, []
    joined_rows = observation_rows = 0
    for partition in partitions:
        for member in partition['results']:
            joined_rows += member['joined_rows']
            observation_rows += member['observation_rows']
            event_rows.extend(member['events'])
            for harp, audit in member['harps'].items():
                if harp in audits:
                    raise ValueError(f'HARP {harp} spans archive members')
                audits[harp] = audit
                locations[harp] = [partition['partition'], member['member']]

    role_totals = {role: Counter() for role in ROLE_ORDER}
    shared_removed = {role: Counter() for role in ROLE_ORDER}
    role_coverage = {role: [None, None] for role in ROLE_ORDER}
    boundary_removed = leap_removed = cadence_removed = 0
    for audit in audits.values():
        boundary_removed += audit['boundary_removed']
        leap_removed += audit['leap_removed']
        cadence_removed += audit['cadence_removed']
        active = [role for role in ROLE_ORDER
                  if audit['roles'][role].get('candidate_windows', 0)]
        if not active:
            continue
        owner = active[0]
        role_totals[owner].update(audit['roles'][owner])
        bounds = audit['forecast_coverage'][owner]
        if bounds[0] is not None:
            first, last = map(pd.Timestamp, bounds)
            current_first, current_last = role_coverage[owner]
            role_coverage[owner] = [first if current_first is None or first < current_first else current_first,
                                    last if current_last is None or last > current_last else current_last]
        for role in active[1:]:
            shared_removed[role].update(audit['roles'][role])

    events = prepare_events(pd.DataFrame(event_rows, columns=EVENT_COLUMNS))
    letters = np.array([value.strip().upper()[0] for value in events.goes_class])
    strong_goes = events.has_goes.to_numpy(dtype=bool) & np.isin(letters, ['M', 'X'])
    major_events = events.loc[strong_goes].assign(letter=letters[strong_goes])
    confidence_counts = (major_events.groupby(['letter', 'confidence']).size()
                         .rename('events').reset_index().to_dict('records'))
    for row in confidence_counts:
        row['events'] = int(row['events'])
    role_rows = {}
    for role in ROLE_ORDER:
        totals = dict(role_totals[role])
        positions = totals.get('quality_retained', 0)*60*len(V2_MEASUREMENTS)
        totals['measurement_positions_retained'] = positions
        totals['missing_fraction_retained'] = (
            totals.get('missing_positions_retained', 0)/positions if positions else None)
        role_rows[role] = totals
    report = {
        'scope': 'Pre-2024 measurements and attached events; no final-test rows, external unassigned-event inventory, model fitting or scoring',
        'completed_utc': datetime.now(timezone.utc).isoformat(),
        'parquet_filter': f'obs_start < {cutoff_tai.isoformat()} TAI',
        'joined_rows': joined_rows,
        'distinct_observation_rows': observation_rows,
        'harps': len(audits),
        'role_totals_after_harp_ownership': role_rows,
        'role_forecast_coverage': {
            role: [value.isoformat() if value is not None else None
                   for value in role_coverage[role]] for role in ROLE_ORDER},
        'shared_harp_windows_removed': {role: dict(shared_removed[role]) for role in ROLE_ORDER},
        'boundary_windows_removed': boundary_removed,
        'leap_crossing_windows_removed': leap_removed,
        'cadence_windows_removed': cadence_removed,
        'attached_events': len(events),
        'attached_goes_major_events': int(strong_goes.sum()),
        'attached_goes_major_class_confidence': confidence_counts,
        'label_state': 'Known attached positives counted; nonpositive windows unresolved until a complete independent GOES M/X inventory is frozen',
        'development_coverage_gate': 'pending_unassigned_major_event_inventory',
        'source_hashes': {
            'config/swan_sf_v2_sources.verified.json': sha256(manifest_path),
            'config/experiment5-v3.json': sha256(protocol_path),
        },
        'code_hashes': {
            'helio24/v2_archive.py': sha256(ROOT / 'helio24/v2_archive.py'),
            'helio24/v2_contract.py': sha256(ROOT / 'helio24/v2_contract.py'),
            'helio24/v2_coverage.py': sha256(ROOT / 'helio24/v2_coverage.py'),
            'scripts/audit_v2_development_coverage.py': sha256(__file__),
        },
        'partitions': [{k: v for k, v in item.items() if k != 'results'}
                       for item in sorted(partitions, key=lambda value: value['partition'])],
    }
    output.mkdir(parents=True)
    (output / 'report.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k: v for k, v in report.items() if not k.endswith('_hashes')}, indent=2))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path,
                        default=ROOT / 'artifacts/v2_development_coverage')
    parser.add_argument('--workers', type=int, choices=range(1, 5), default=4)
    args = parser.parse_args()
    run(args.output, args.workers)
