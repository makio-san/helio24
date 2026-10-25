"""Development-only chronological metadata split and prerequisite checks."""
import pandas as pd

REQUIRED_GATES = {
    'measurement_semantics', 'quality_policy', 'utc_conversion',
    'label_inclusion_policy', 'versioned_dataset_manifest',
    'development_coverage_audit', 'training_runner_review',
}


def preflight(protocol):
    gates = protocol.get('gates', {})
    missing = sorted(REQUIRED_GATES - set(gates))
    pending = sorted(k for k in REQUIRED_GATES if gates.get(k) != 'verified')
    # Status is a separate lock: changing individual gate strings cannot unlock training.
    frozen_contract = protocol.get('status') == 'execution_contract_frozen'
    return dict(protocol_id=protocol['id'], ready_for_training=not pending and frozen_contract,
                missing_gates=missing, pending_gates=pending, execution_contract_frozen=frozen_contract,
                final_test_allowed=False,
                note='Readiness check only; no data, labels, model fitting or final-test access.')


def require_training_ready(protocol):
    state = preflight(protocol)
    if not state['ready_for_training']:
        raise ValueError('Training prerequisites unresolved: '+', '.join(state['pending_gates']))


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
