"""Independent HARP association for V2-unassigned GOES M/X events (config/relabel-v1.json)."""
import numpy as np
import pandas as pd

from helio24.v2_contract import label_windows

OUTCOMES = ['recovered', 'ambiguous', 'unmapped', 'no_region', 'no_sgas_match']
STILL_UNASSIGNED = ['unmapped', 'no_region', 'no_sgas_match']


def recover_unassigned_events(hek, sgas, mapping, tolerance_minutes=5):
    """Attach each V2-unassigned HEK event to a HARP through SGAS region numbers and NOAA_ARS."""
    hek = hek.assign(peak_time=pd.to_datetime(hek.peak_time, utc=True))
    sgas = sgas.assign(peak_time=pd.to_datetime(sgas.peak_time, utc=True))
    by_key = {(d, n): sorted(set(g.harp.astype(int))) for (d, n), g in mapping.groupby(['date', 'noaa'])}
    rows = []
    for row in hek.itertuples():
        same = sgas[sgas.goes_class.eq(row.goes_class)
                    & (sgas.peak_time-row.peak_time).abs().le(pd.Timedelta(minutes=tolerance_minutes))]
        regions, harps = [], set()
        if same.empty:
            outcome = 'no_sgas_match'
        else:
            with_region = same.dropna(subset=['noaa'])
            regions = sorted(set(with_region.noaa.astype(int)))
            for match in with_region.itertuples():
                harps.update(by_key.get((match.peak_time.date(), int(match.noaa)), []))
            outcome = ('no_region' if not regions else 'unmapped' if not harps
                       else 'recovered' if len(harps) == 1 else 'ambiguous')
        rows.append(dict(event_id=row.event_id, peak_time=row.peak_time, goes_class=row.goes_class,
                         regions=';'.join(map(str, regions)), harps=';'.join(map(str, sorted(harps))),
                         outcome=outcome))
    return pd.DataFrame(rows, columns=['event_id', 'peak_time', 'goes_class', 'regions', 'harps', 'outcome'])


def _harps(value):
    return [int(v) for v in str(value).split(';') if v]


def relabel_windows(windows, attached_events, unassigned, recovery, *, inventory_complete=False):
    """Frozen contract labels plus recovered positives and ambiguous exclusions; keeps label_status_v2."""
    if not set(recovery.outcome) <= set(OUTCOMES):
        raise ValueError('Unknown recovery outcome')
    known = set(unassigned.event_id)
    if not set(recovery.event_id) <= known:
        raise ValueError('Recovery lists an event outside the unassigned inventory')
    remaining_ids = set(unassigned.event_id)-set(recovery[~recovery.outcome.isin(STILL_UNASSIGNED)].event_id)
    original = label_windows(windows, attached_events, unassigned, inventory_complete=inventory_complete)
    result = label_windows(windows, attached_events, unassigned[unassigned.event_id.isin(remaining_ids)],
                           inventory_complete=inventory_complete)
    starts = pd.DatetimeIndex(result.forecast_time).as_unit('ns').asi8
    ends = pd.DatetimeIndex(result.prediction_end).as_unit('ns').asi8
    harp = result.harp.to_numpy()
    recovered = np.zeros(len(result), dtype=bool)
    ambiguous = np.zeros(len(result), dtype=bool)
    for row in recovery.itertuples():
        if row.outcome not in {'recovered', 'ambiguous'}:
            continue
        peak = pd.Timestamp(row.peak_time).tz_convert('UTC').as_unit('ns').value
        inside = (starts <= peak) & (peak < ends) & np.isin(harp, _harps(row.harps))
        if row.outcome == 'recovered':
            recovered |= inside
        else:
            ambiguous |= inside
    status = result.label_status.to_numpy(dtype=object)
    result['label_status'] = np.select(
        [(status == 'positive') | recovered, (status == 'excluded_ambiguous_harp') | ambiguous,
         status == 'excluded_unassigned_major_event'],
        ['positive', 'excluded_ambiguous_harp', 'excluded_unassigned_major_event'], default='negative')
    result['target'] = result.label_status.eq('positive').astype(int)
    result['label_status_v2'] = original.label_status.to_numpy()
    return result
