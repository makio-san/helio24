import json

import pandas as pd
import pytest

from helio24.hek_inventory import monthly_intervals, parse_month, query_url


def event(**changes):
    row = {
        'kb_archivid': 'ivo://event/1',
        'event_starttime': '2023-01-31T23:55:00',
        'event_peaktime': '2023-02-01T00:02:00',
        'event_endtime': '2023-02-01T00:08:00',
        'fl_goescls': 'M1.2', 'obs_observatory': 'GOES', 'frm_name': 'SWPC',
    }
    return row | changes


def payload(rows, overmax=False):
    return json.dumps({'result': rows, 'association': [], 'overmax': overmax}).encode()


def test_month_intervals_and_query_are_explicit():
    intervals = monthly_intervals('2023-01-15', '2023-03-01')
    assert intervals == [(pd.Timestamp('2023-01-15'), pd.Timestamp('2023-02-01')),
                         (pd.Timestamp('2023-02-01'), pd.Timestamp('2023-03-01'))]
    url = query_url(*intervals[0])
    assert 'value0=GOES' in url and 'value1=M1' in url and 'result_limit=20000' in url


def test_month_parser_assigns_by_peak_and_rejects_truncation():
    january = parse_month(payload([event()]), pd.Timestamp('2023-01-01'),
                          pd.Timestamp('2023-02-01'))
    february = parse_month(payload([event()]), pd.Timestamp('2023-02-01'),
                           pd.Timestamp('2023-03-01'))
    assert january.empty
    assert february[['event_id', 'goes_class', 'provider']].iloc[0].tolist() == [
        'ivo://event/1', 'M1.2', 'SWPC']
    with pytest.raises(ValueError, match='truncated'):
        parse_month(payload([], overmax=True), pd.Timestamp('2023-01-01'),
                    pd.Timestamp('2023-02-01'))


def test_month_parser_rejects_invalid_event_contract():
    bad = event(event_endtime='2023-01-31T23:56:00')
    with pytest.raises(ValueError, match='order'):
        parse_month(payload([bad]), pd.Timestamp('2023-01-01'),
                    pd.Timestamp('2023-03-01'))
