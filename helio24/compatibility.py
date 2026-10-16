"""Schema-only compatibility gate for a future dataset bridge."""
from helio24.data import MAGNETIC_COLUMNS


def inspect_columns(columns):
    if len(columns) != len(set(columns)):
        raise ValueError('Duplicate source columns')
    by_lower = {}
    for name in columns:
        if name.lower() in by_lower:
            raise ValueError('Ambiguous case-normalized source columns')
        by_lower[name.lower()] = name
    mapping = {name: by_lower[name.lower()] for name in MAGNETIC_COLUMNS if name.lower() in by_lower}
    missing = [name for name in MAGNETIC_COLUMNS if name not in mapping]
    flags = [name for name in ['QUALITY', 'IS_TMFI'] if name.lower() not in by_lower]
    return dict(magnetic_column_mapping=mapping, missing_magnetic_columns=missing,
                missing_quality_columns=flags,
                outcome_columns_excluded=[name for name in columns if name.lower() in {
                    'start_time', 'peak_time', 'end_time', 'goes_class', 'confidence', 'has_goes',
                    'has_ssw', 'has_xrt', 'harp_vote', 'max_pair_distance_deg', 'peak_class'}],
                ready_for_model=False,
                pending_checks=['measurement units and numerical parity on old overlap',
                                'quality-mask equivalence or explicit versioned replacement',
                                'timestamp scale, cadence and observation/forecast boundaries',
                                'label identity, confidence and ambiguity rules',
                                'chronological split and HARP/interval purging'])
