"""Strict acquisition helpers for the HEK SWPC GOES major-flare inventory."""
from calendar import monthrange
import json
from urllib.parse import urlencode

import pandas as pd

from helio24.v2_contract import parse_flare_class


HEK_ENDPOINT = 'https://www.lmsal.com/hek/her'
REQUIRED_FIELDS = {
    'kb_archivid', 'event_starttime', 'event_peaktime', 'event_endtime',
    'fl_goescls', 'obs_observatory', 'frm_name',
}


def monthly_intervals(start, end):
    """Return contiguous UTC-naive calendar-month query intervals."""
    left, stop = pd.Timestamp(start), pd.Timestamp(end)
    if left.tzinfo is not None or stop.tzinfo is not None or left >= stop:
        raise ValueError('HEK interval must use increasing timezone-naive UTC values')
    intervals = []
    while left < stop:
        days = monthrange(left.year, left.month)[1]
        right = min(left.normalize()+pd.Timedelta(days=days-left.day+1), stop)
        intervals.append((left, right))
        left = right
    return intervals


def query_url(start, end):
    params = {
        'cosec': 2, 'cmd': 'search', 'type': 'column', 'event_type': 'fl',
        'event_starttime': start.isoformat(), 'event_endtime': end.isoformat(),
        'event_coordsys': 'helioprojective',
        'x1': -5000, 'x2': 5000, 'y1': -5000, 'y2': 5000,
        'param0': 'OBS_Observatory', 'op0': '=', 'value0': 'GOES',
        'param1': 'FL_GOESCls', 'op1': '>=', 'value1': 'M1',
        'result_limit': 20000,
    }
    return HEK_ENDPOINT+'?'+urlencode(params)


def parse_month(payload, start, end):
    """Validate one raw response and assign events by half-open peak month."""
    document = json.loads(payload.decode('iso-8859-1'))
    if document.get('overmax') is not False:
        raise ValueError('HEK response is truncated or lacks an overmax declaration')
    rows = document.get('result')
    if not isinstance(rows, list):
        raise ValueError('HEK result must be a list')
    accepted = []
    for row in rows:
        missing = REQUIRED_FIELDS-set(row)
        if missing:
            raise ValueError(f'HEK event lacks fields: {sorted(missing)}')
        if row['obs_observatory'] != 'GOES':
            raise ValueError('HEK response contains a non-GOES event')
        letter, _ = parse_flare_class(row['fl_goescls'])
        if letter not in {'M', 'X'}:
            raise ValueError('HEK response contains a sub-M event')
        times = {name: pd.Timestamp(row[source]).tz_localize('UTC')
                 for name, source in [('start_time', 'event_starttime'),
                                      ('peak_time', 'event_peaktime'),
                                      ('end_time', 'event_endtime')]}
        if not times['start_time'] <= times['peak_time'] <= times['end_time']:
            raise ValueError('HEK flare start/peak/end order is invalid')
        peak_naive = times['peak_time'].tz_localize(None)
        if not start <= peak_naive < end:
            continue
        accepted.append({
            'event_id': str(row['kb_archivid']), **times,
            'goes_class': str(row['fl_goescls']).strip().upper(),
            'provider': str(row['frm_name']),
        })
    frame = pd.DataFrame(accepted, columns=[
        'event_id', 'start_time', 'peak_time', 'end_time', 'goes_class', 'provider'])
    if frame.event_id.duplicated().any():
        raise ValueError('HEK response contains duplicate event IDs')
    return frame.sort_values(['peak_time', 'event_id']).reset_index(drop=True)
