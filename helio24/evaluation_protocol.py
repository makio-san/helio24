"""Development-only chronological metadata split and prerequisite checks."""
import pandas as pd

REQUIRED_GATES = {
    'measurement_semantics', 'quality_policy', 'utc_conversion',
    'label_inclusion_policy', 'versioned_dataset_manifest',
    'development_coverage_audit', 'training_runner_review',
}


def protocol_errors(protocol):
    errors = []
    if not isinstance(protocol.get('id'), str) or not protocol.get('id'):
        errors.append('invalid protocol ID')
    if not isinstance(protocol.get('version'), int) or protocol.get('version', 0) <= 0:
        errors.append('version must be a positive integer')
    for name in ['observation_hours', 'prediction_hours']:
        if not isinstance(protocol.get(name), (int, float)) or protocol.get(name, 0) <= 0:
            errors.append(f'{name} must be positive')
    recall = protocol.get('primary_recall')
    if not isinstance(recall, (int, float)) or not 0 < recall <= 1:
        errors.append('primary_recall must be in (0, 1]')
    roles = protocol.get('roles', {})
    names = ['train', 'calibration', 'validation', 'test']
    if set(roles) != set(names):
        errors.append('roles must define train, calibration, validation and test')
    else:
        parsed = []
        for name in names:
            if not isinstance(roles[name], list) or len(roles[name]) != 2:
                errors.append(f'{name} must have one start and one end')
                continue
            try:
                start, end = map(pd.Timestamp, roles[name])
            except (TypeError, ValueError):
                errors.append(f'{name} boundaries must be valid timestamps')
                continue
            if start.tzinfo is None or end.tzinfo is None or str(start.tz) != 'UTC' or str(end.tz) != 'UTC':
                errors.append(f'{name} boundaries must be explicit UTC')
            if start >= end:
                errors.append(f'{name} must have positive duration')
            parsed.append((name, start, end))
        if len(parsed) == len(names):
            for left, right in zip(parsed, parsed[1:]):
                if left[2] != right[1]:
                    errors.append(f'{left[0]} and {right[0]} must be contiguous')
    if set(protocol.get('candidates', {})) != {'baseline', 'logistic', 'xgboost'}:
        errors.append('candidate set must be baseline, logistic and xgboost')
    return errors


def preflight(protocol):
    gates = protocol.get('gates', {})
    missing = sorted(REQUIRED_GATES - set(gates))
    pending = sorted(k for k in REQUIRED_GATES if gates.get(k) != 'verified')
    # Status is a separate lock: changing individual gate strings cannot unlock training.
    frozen_contract = protocol.get('status') == 'execution_contract_frozen'
    errors = protocol_errors(protocol)
    return dict(protocol_id=protocol.get('id'), protocol_version=protocol.get('version'),
                ready_for_training=not pending and frozen_contract and not errors,
                missing_gates=missing, pending_gates=pending, execution_contract_frozen=frozen_contract,
                protocol_errors=errors,
                final_test_allowed=False,
                note='Readiness check only; no data, labels, model fitting or final-test access.')


def require_training_ready(protocol):
    state = preflight(protocol)
    if not state['ready_for_training']:
        details = state['pending_gates']+state['protocol_errors']
        if not state['execution_contract_frozen']:
            details.append('execution contract is not frozen')
        raise ValueError('Training prerequisites unresolved: '+', '.join(details))


def development_split(metadata, protocol):
    """Split explicit-time metadata only; reject any reserved-period input."""
    columns = ['harp', 'observation_start', 'forecast_time', 'prediction_end']
    if set(metadata.columns) != set(columns):
        raise ValueError('Supply metadata only; no labels, features or extra fields')
    frame = metadata.copy()
    for name in columns[1:]:
        if frame[name].isna().any() or any(pd.Timestamp(v).tzinfo is None for v in frame[name]):
            raise ValueError('Every timestamp must have an explicit time zone')
        frame[name] = pd.to_datetime(frame[name], utc=True)
    if frame.harp.isna().any() or not pd.api.types.is_integer_dtype(frame.harp) or (frame.harp <= 0).any():
        raise ValueError('HARP IDs must be positive integers')
    if frame.duplicated(['harp', 'forecast_time']).any():
        raise ValueError('Duplicate HARP/forecast metadata')
    if not (frame.forecast_time-frame.observation_start).eq(pd.Timedelta(hours=protocol['observation_hours'])).all():
        raise ValueError('Observation interval differs from protocol')
    if not (frame.prediction_end-frame.forecast_time).eq(pd.Timedelta(hours=protocol['prediction_hours'])).all():
        raise ValueError('Prediction interval differs from protocol')
    test_start = pd.Timestamp(protocol['roles']['test'][0])
    if (frame.forecast_time >= test_start).any():
        raise ValueError('Reserved test period must not be supplied to development splitting')
    seen, groups, audit = set(), {}, []
    for role in ['train', 'calibration', 'validation']:
        start, end = map(pd.Timestamp, protocol['roles'][role])
        assigned = frame[frame.forecast_time.ge(start) & frame.forecast_time.lt(end)].copy()
        eligible = assigned[assigned.observation_start.ge(start) & assigned.prediction_end.le(end)].copy()
        shared = set(eligible.harp) & seen
        retained = eligible[~eligible.harp.isin(shared)].sort_values(['forecast_time', 'harp']).copy()
        groups[role] = retained
        audit.append(dict(role=role, assigned=len(assigned), boundary_removed=len(assigned)-len(eligible),
                          shared_harp_rows_removed=len(eligible)-len(retained), shared_harps=sorted(map(int, shared)),
                          retained=len(retained)))
        seen.update(retained.harp)
    assigned_count = sum(row['assigned'] for row in audit)
    return groups, dict(roles=audit, outside_development_roles=len(frame)-assigned_count,
                       empty_roles=[k for k, v in groups.items() if v.empty])
