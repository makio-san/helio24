"""Materialize the relabelled pre-2024 development table (config/relabel-v1.json)."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
import pandas as pd

from helio24.data import FEATURE_COLUMNS, ROOT
from helio24.full_data import sha256
from helio24.relabel import recover_unassigned_events, relabel_windows
from helio24.v2_archive import stream_verified_archive_with_retries
from helio24.v2_contract import EVENT_COLUMNS, V2_MEASUREMENTS, audit_event_rows, utc_to_tai
from helio24.v2_features import extract_harp_windows
from helio24.v2_sources import validate_manifest
from helio24.v2_training import load_development
from scripts.audit_label_coverage import load_sgas_major_events
from scripts.audit_region_context_sources import load_mapping

EXPECTED = {'harp', 'role', 'observation_start', 'forecast_time', 'prediction_end', 'missing_fraction',
            *FEATURE_COLUMNS, 'target', 'label_status', 'label_status_v2'}


def inspect_member(path, name, size, partition, roles, unassigned, recovery, shards):
    columns = ['harp_number', 'obs_start', *V2_MEASUREMENTS.values(), *EVENT_COLUMNS[1:]]
    joined = pd.read_parquet(path, columns=columns, filters=[('obs_start', '<', utc_to_tai(roles['test'][0]))])
    empty = {'member': name, 'member_bytes': size, 'joined_rows': 0, 'observation_rows': 0, 'harps': [],
             'retained_rows': 0, 'label_status': {}, 'label_status_v2': {}, 'transitions': {},
             'role_rows': {}, 'role_positives': {}, 'extraction': {}, 'event_errors': {}, 'shard': None}
    if joined.empty:
        return empty
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
    if windows.empty:
        return {**empty, 'joined_rows': len(joined), 'observation_rows': len(observations),
                'harps': sorted(map(int, observations.harp_number.unique())),
                'extraction': dict(extraction), 'event_errors': event_errors}
    windows = relabel_windows(windows, events, unassigned, recovery, inventory_complete=True)
    status, status_v2 = Counter(windows.label_status), Counter(windows.label_status_v2)
    transitions = Counter(f'{a}->{b}' for a, b in zip(windows.label_status_v2, windows.label_status))
    windows = windows[~windows.label_status.str.startswith('excluded_')].copy()
    if set(windows.columns) != EXPECTED:
        raise ValueError('Unexpected materialized feature schema')
    shard_id = hashlib.sha256(name.encode()).hexdigest()[:12]
    shard = shards/f'partition-{partition}-{shard_id}.parquet'
    windows.to_parquet(shard, index=False, compression='zstd')
    return {'member': name, 'member_bytes': size, 'joined_rows': len(joined), 'observation_rows': len(observations),
            'harps': sorted(map(int, observations.harp_number.unique())), 'retained_rows': len(windows),
            'label_status': dict(status), 'label_status_v2': dict(status_v2), 'transitions': dict(transitions),
            'role_rows': {str(k): int(v) for k, v in windows.role.value_counts().items()},
            'role_positives': {str(k): int(v) for k, v in windows.groupby('role').target.sum().items()},
            'extraction': dict(extraction), 'event_errors': event_errors,
            'shard': {'file': shard.name, 'bytes': shard.stat().st_size, 'sha256': sha256(shard)}}


def recovery_table(config):
    evidence = config['evidence']
    hek_path = ROOT/evidence['hek_unassigned_events']
    if sha256(hek_path) != evidence['hek_unassigned_events_sha256']:
        raise ValueError('HEK unassigned inventory changed')
    unassigned = pd.read_csv(hek_path)
    sgas = load_sgas_major_events(ROOT/evidence['sgas_directory'])
    mapping, problems, fallback = load_mapping(ROOT/evidence['mapping_directory'])
    recovery = recover_unassigned_events(unassigned, sgas, mapping)
    return unassigned, recovery, {'mapping_problems': problems, 'mapping_http_fallback_months': fallback}


def verify_against_frozen(output, config):
    """Every frozen window keeps its features and frozen status; new windows were excluded before."""
    evidence = config['evidence']
    frozen_groups, _ = load_development(ROOT/evidence['frozen_shards'], evidence['frozen_shards_report_sha256'])
    frozen = pd.concat(frozen_groups.values(), ignore_index=True)
    del frozen_groups
    report = json.loads((output/'report.json').read_text())
    new = pd.concat([pd.read_parquet(output/'shards'/item['file']) for item in report['shards']], ignore_index=True)
    key = ['harp', 'forecast_time']
    if new.duplicated(key).any():
        raise ValueError('Duplicate relabelled HARP/forecast key')
    position = frozen[key].merge(new[key].assign(_row=np.arange(len(new))), on=key, how='left')
    if position._row.isna().any():
        raise ValueError('A frozen window is missing from the relabelled table')
    rows = position._row.to_numpy(dtype=int)
    if not np.array_equal(frozen.label_status.to_numpy(), new.label_status_v2.to_numpy()[rows]):
        raise ValueError('A frozen window changed its frozen-contract status')
    for column in FEATURE_COLUMNS:
        if not np.array_equal(frozen[column].to_numpy(dtype=float), new[column].to_numpy(dtype=float)[rows], equal_nan=True):
            raise ValueError(f'A frozen window changed its features: {column}')
    added = np.ones(len(new), dtype=bool)
    added[rows] = False
    if not new.label_status_v2.to_numpy()[added].astype(str).tolist() == [s for s in new.label_status_v2.to_numpy()[added] if s.startswith('excluded_')]:
        raise ValueError('A new window was not excluded under the frozen contract')
    turned = int((frozen.target.to_numpy() != new.target.to_numpy()[rows]).sum())
    return {'frozen_windows': int(len(frozen)), 'frozen_windows_found': int(len(rows)),
            'features_identical': True, 'frozen_status_identical': True,
            'added_windows': int(added.sum()), 'added_positive_windows': int(new.target.to_numpy()[added].sum()),
            'frozen_windows_turned_positive': turned,
            'rows': int(len(new)), 'positives': int(new.target.sum())}


def run(config_path, output):
    if output.exists():
        raise RuntimeError('Preserve the existing relabelled materialization')
    config = json.loads(config_path.read_text())
    evidence = config['evidence']
    manifest_path = ROOT/evidence['source_manifest']
    if sha256(manifest_path) != evidence['source_manifest_sha256']:
        raise ValueError('Source manifest changed')
    manifest = json.loads(manifest_path.read_text())
    if validate_manifest(manifest, require_hashes=True):
        raise ValueError('The verified source manifest is invalid')
    protocol = json.loads((ROOT/evidence['role_protocol']).read_text())
    if protocol.get('version') != 5:
        raise ValueError('This materializer requires the frozen Experiment 5 v5 contract')
    source_report = json.loads((ROOT/evidence['inventory_audit']/'report.json').read_text())
    if not source_report.get('inventory_complete_for_labeling'):
        raise ValueError('The major-event inventory is not complete for labeling')
    roles = {name: tuple(map(pd.Timestamp, bounds)) for name, bounds in protocol['roles'].items()}
    unassigned, recovery, mapping_notes = recovery_table(config)
    output.mkdir(parents=True)
    recovery.to_csv(output/'recovery.csv', index=False)
    shards = output/'shards'
    shards.mkdir()
    partitions = []
    for item in manifest['archives']:
        result = stream_verified_archive_with_retries(
            item, lambda path, name, size: inspect_member(path, name, size, item['partition'], roles,
                                                          unassigned, recovery, shards),
            temporary_root=ROOT/'data/cache')
        partitions.append(result)
        print(f'partition {result["partition"]}: {result["members"]} members verified', flush=True)
    seen, duplicate_harps = set(), set()
    totals, status, status_v2, transitions = Counter(), Counter(), Counter(), Counter()
    role_rows, role_positives, extraction, event_errors, shard_records = Counter(), Counter(), Counter(), Counter(), []
    for partition in partitions:
        for member in partition['results']:
            current = set(member['harps'])
            duplicate_harps.update(seen & current)
            seen.update(current)
            totals.update({key: member[key] for key in ['joined_rows', 'observation_rows', 'retained_rows']})
            status.update(member['label_status'])
            status_v2.update(member['label_status_v2'])
            transitions.update(member['transitions'])
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
    recovery_by_year = (recovery.assign(year=pd.to_datetime(recovery.peak_time, utc=True).dt.year)
                        .groupby(['year', 'outcome']).size().unstack(fill_value=0))
    recovery_by_year.to_csv(output/'recovery_by_year.csv')
    report = {
        'scope': 'Pre-2024 V2 development features with recovered GOES M/X labels; no model fitting, scoring or reserved test access',
        'protocol_sha256': sha256(config_path),
        'completed_utc': datetime.now(timezone.utc).isoformat(),
        'feature_count': len(FEATURE_COLUMNS), 'feature_columns': FEATURE_COLUMNS,
        'rows': {name: int(role_rows[name]) for name in roles if name != 'test'},
        'positives': {name: int(role_positives[name]) for name in roles if name != 'test'},
        'recovery_outcomes': {k: int(v) for k, v in recovery.outcome.value_counts().items()},
        'label_status_before_exclusion': {k: int(status[k]) for k in sorted(status)},
        'label_status_v2_before_exclusion': {k: int(status_v2[k]) for k in sorted(status_v2)},
        'transitions': {k: int(transitions[k]) for k in sorted(transitions)},
        'joined_rows': int(totals['joined_rows']), 'observation_rows': int(totals['observation_rows']),
        'retained_rows': int(totals['retained_rows']), 'harps': len(seen),
        'extraction_audit': dict(extraction),
        'invalid_attached_event_rows_excluded': int(sum(event_errors.values())),
        'invalid_attached_event_reasons': dict(event_errors),
        **mapping_notes,
        'source_hashes': {evidence['source_manifest']: sha256(manifest_path),
                          evidence['role_protocol']: sha256(ROOT/evidence['role_protocol']),
                          evidence['hek_unassigned_events']: sha256(ROOT/evidence['hek_unassigned_events']),
                          'recovery.csv': sha256(output/'recovery.csv')},
        'code_hashes': {name: sha256(ROOT/name) for name in [
            'helio24/v2_archive.py', 'helio24/v2_contract.py', 'helio24/v2_features.py', 'helio24/relabel.py',
            'scripts/materialize_relabelled_development.py']},
        'shards': sorted(shard_records, key=lambda value: value['file']),
        'partitions': [{k: v for k, v in p.items() if k != 'results'} for p in sorted(partitions, key=lambda v: v['partition'])],
        'reserved_test_accessed': False,
    }
    (output/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    report['frozen_consistency'] = verify_against_frozen(output, config)
    (output/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k: report[k] for k in ['rows', 'positives', 'recovery_outcomes', 'label_status_before_exclusion',
                                              'label_status_v2_before_exclusion', 'transitions', 'frozen_consistency']}, indent=2))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=ROOT/'config/relabel-v1.json')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    run(args.config.resolve(), args.output.resolve())
