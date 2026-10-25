"""Reconcile attached V2 GOES events with an independent major-flare inventory."""
import pandas as pd

from helio24.v2_contract import parse_flare_class, prepare_events


def reconcile_major_events(attached_frame, external_frame):
    attached = prepare_events(attached_frame)
    attached = attached[attached.has_goes].copy()
    attached['letter'] = [parse_flare_class(value)[0] for value in attached.goes_class]
    attached = attached[attached.letter.isin(['M', 'X'])].copy()
    attached['peak_time'] = attached.peak_time_utc

    required = {'event_id', 'peak_time', 'goes_class'}
    if not required <= set(external_frame.columns):
        raise ValueError(f'External inventory lacks fields: {sorted(required-set(external_frame.columns))}')
    external = external_frame[list(required)].copy()
    external['peak_time'] = pd.to_datetime(external.peak_time, utc=True, errors='raise')
    external['goes_class'] = external.goes_class.astype(str).str.strip().str.upper()
    if external.event_id.isna().any() or external.event_id.duplicated().any():
        raise ValueError('External event IDs must be present and unique')
    if not all(parse_flare_class(value)[0] in {'M', 'X'} for value in external.goes_class):
        raise ValueError('External inventory must contain M/X events only')

    keys = ['peak_time', 'goes_class']
    attached_keys = attached[keys].drop_duplicates()
    external_keys = external.sort_values('event_id').drop_duplicates(keys)
    exact = attached_keys.merge(external_keys[keys], on=keys)
    v2_only = attached_keys.merge(external_keys[keys], on=keys, how='left', indicator=True)
    v2_only = v2_only[v2_only._merge.eq('left_only')].drop(columns='_merge')
    external_only = external_keys.merge(attached_keys, on=keys, how='left', indicator=True)
    external_only = external_only[external_only._merge.eq('left_only')].drop(columns='_merge')
    peak_conflicts = (attached_keys.merge(external_keys, on='peak_time', suffixes=('_v2', '_external'))
                      .query('goes_class_v2 != goes_class_external'))
    unassigned = external_only[['event_id', 'peak_time', 'goes_class']].copy()
    return {
        'attached_associations': len(attached),
        'attached_distinct_peak_class': len(attached_keys),
        'external_rows': len(external),
        'external_distinct_peak_class': len(external_keys),
        'exact_peak_class_matches': len(exact),
        'v2_only_peak_class': len(v2_only),
        'external_unassigned_peak_class': len(unassigned),
        'peak_class_conflicts': len(peak_conflicts),
    }, unassigned.sort_values(['peak_time', 'goes_class']).reset_index(drop=True), v2_only, peak_conflicts
