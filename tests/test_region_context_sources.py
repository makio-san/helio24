import pandas as pd

from scripts.audit_region_context_sources import available_srs, parse_srs

SRS = """:Product: 0903SRS.txt
:Issued: 2023 Sep 03 0030 UTC
Joint USAF/NOAA Solar Region Summary
I.  Regions with Sunspots.  Locations Valid at 02/2400Z
Nmbr Location  Lo  Area  Z   LL   NN Mag Type
3413 N10W89   099  0150 Dso  05   05 Beta
3417 S08E07   003  0080 Dsi  09   16 Beta-Gamma-Delta
IA. H-alpha Plages without Spots.  Locations Valid at 02/2400Z Sep
Nmbr  Location  Lo
3416  S19W38   048
II. Regions Due to Return 03 Sep to 05 Sep
Nmbr Lat    Lo
3410 S30    280
"""


def test_parse_srs_reads_issue_time_and_only_sunspot_regions():
    issued, rows = parse_srs(SRS)
    assert issued == pd.Timestamp('2023-09-03 00:30', tz='UTC')
    assert [r['noaa'] for r in rows] == [13413, 13417]
    assert rows[1]['mag_type'] == 'Beta-Gamma-Delta' and rows[1]['area'] == 80 and rows[1]['z'] == 'Dsi'


def test_parse_srs_without_issue_line_returns_none():
    issued, rows = parse_srs('I.  Regions with Sunspots\n3413 N10W89   099  0150 Dso  05   05 Beta\n')
    assert issued is None and len(rows) == 1


def test_available_srs_respects_safety_margin_and_absence():
    issued = pd.Series(pd.to_datetime(['2023-09-02 00:30', '2023-09-03 00:30'], utc=True))
    times = pd.Series(pd.to_datetime(['2023-09-03 00:45', '2023-09-03 01:00', '2023-09-01 12:00'], utc=True))
    out = available_srs(issued, times)
    assert out[0] == pd.Timestamp('2023-09-02 00:30', tz='UTC')  # 00:45 is inside the 30 min margin
    assert out[1] == pd.Timestamp('2023-09-03 00:30', tz='UTC')
    assert pd.isna(out[2])
