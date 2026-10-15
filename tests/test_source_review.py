import json

import pandas as pd
import pytest

from helio24.source_review import match_xra, parse_events, parse_harp_table, parse_jsoc, parse_srs


def test_noaa_rows_preserve_conflicting_regions_and_missing_fields():
    text = ''':Date: 2014 09 03
3300       1320   1354      1423  G15  5   XRA  1-8A      M2.5    6.6E-02   2155
3300       1407   1409      1420  HOL  3   FLA  S14W18    SF      ERU       2152
3400       1500   ////      1510  SVI  C   RSP  025-052   VI/1
'''
    rows = parse_events(text, pd.Timestamp('2014-09-03'))
    event = dict(start_time='2014-09-03 13:20', peak_time='2014-09-03 13:54',
                 end_time='2014-09-03 14:23', goes_class='M2.5')
    xra, related = match_xra(rows, event)
    assert xra['noaa_region'] == 12155
    assert [row['noaa_region'] for row in related] == [12155, 12152]
    assert related[1]['location_frequency'] == 'S14W18'
    assert rows[2]['noaa_region'] is None
    assert rows[2]['maximum'] == '////'
    with pytest.raises(ValueError, match='one exact'):
        match_xra(rows+[xra], event)
    with pytest.raises(ValueError, match='date mismatch'):
        parse_events(text, pd.Timestamp('2014-09-04'))


def test_optical_time_qualifier_is_not_lost():
    text = ''':Date: 2014 12 18
 550      B2217   2223      2345  LEA  3   FLA  S11E15    2N      UMB       2241
'''
    row = parse_events(text, pd.Timestamp('2014-12-18'))[0]
    assert row['begin'] == 'B2217'
    assert row['event_number'] == '550'
    assert row['noaa_region'] == 12241


def test_missing_harp_mapping_is_not_a_negative_association():
    table = parse_harp_table('HARPNUM NOAA_ARS\n4920 12235,12237,12238,12242\n4941 12241\n')
    assert table[4941] == [12241]
    assert 4466 not in table
    with pytest.raises(ValueError, match='Duplicate HARP'):
        parse_harp_table('HARPNUM NOAA_ARS\n4941 12241\n4941 12242\n')
    payload = dict(status=0, count=1, keywords=[
        dict(name='HARPNUM', values=['4466']), dict(name='T_REC', values=['2014.08.21_13:24:00_TAI']),
        dict(name='NOAA_ARS', values=['MISSING'])])
    row = parse_jsoc(json.dumps(payload), 4466)[0]
    assert not row['noaa_association_available']
    assert row['noaa_regions'] == []
    assert row['T_REC'].endswith('_TAI')
    assert parse_jsoc('{"status": 0, "count": 0}', 4466) == []
    with pytest.raises(ValueError, match='query failed'):
        parse_jsoc('{"status": 1, "error": "missing series"}', 4466)
    with pytest.raises(ValueError, match='HARP or time scale'):
        parse_jsoc(json.dumps(payload), 4502)


def test_srs_keeps_validity_instead_of_assigning_peak_time():
    validity, rows = parse_srs('''I. Regions with Sunspots. Locations Valid at 21/2400Z
Nmbr Location Lo Area
2148 N05E27 324 0100
2149 N12E77 276 0070
IA. H-alpha Plages without Spots.
2142 N05W48 041
''')
    assert '21/2400Z' in validity
    assert [row['noaa_region'] for row in rows] == [12148, 12149]


def test_real_source_review_integrity_and_no_overwrite():
    from helio24.data import ROOT
    from helio24.sensitivity import verify_report
    from scripts.review_event_sources import run
    directory = ROOT / 'artifacts/source_review'
    if not (directory / 'report.json').exists():
        pytest.skip('Requires local source snapshot and review')
    report = verify_report(ROOT, directory, check_code=True)
    assert len(report['cases']) == 3
    assert all(row['noaa_xra_status'] == 'exact_match' for row in report['cases'])
    assert report['cases'][1]['source_region_conflict'] is True
    with pytest.raises(RuntimeError, match='Preserve'):
        run(ROOT)
