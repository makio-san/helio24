import json
from pathlib import Path

import numpy as np
import pandas as pd

from scripts.audit_activity_history import HISTORY, attach_history, parse_sgas

ROOT = Path(__file__).resolve().parents[1]
TEXT = """:Product: 0911SGAS.txt
:Issued: 2014 Sep 11 0245 UTC
A.  Energetic Events
Begin  Max  End  Rgn   Loc   Xray  Op 245MHz 10cm   Sweep
 0000      0344                                        IV           
 0512 0524 0532  2157 S16E05 C2.4  Sf 440                           
 1721 1745 1820  2158 N14E02 X1.6  2b 3800   1300      IV           
 1826 1827 1901  2157 S17W01       Sf 720    330                    
B.  Proton Events:  None
10 cm 160  SSN 161  Afr/Ap 009/009   X-ray Background B7.6
"""


def test_parse_sgas_reads_issue_time_regions_and_classes():
    issued, events, background, unparsed = parse_sgas(TEXT)
    assert issued == pd.Timestamp('2014-09-11 02:45', tz='UTC') and unparsed == 0
    assert [e['noaa'] for e in events] == [None, 12157, 12158, 12157]
    assert np.isclose(events[2]['logflux'], -4+np.log10(1.6)) and np.isnan(events[3]['logflux'])
    assert np.isclose(background, -7+np.log10(7.6))


def test_history_uses_only_products_issued_before_the_forecast():
    issued, rows, background, _ = parse_sgas(TEXT)
    reports = pd.DataFrame([{'issued_utc': issued, 'background': background}])
    events = pd.DataFrame([{'issued_utc': issued, **r} for r in rows])
    frame = pd.DataFrame({'harp': [1, 1, 2, 3], 'forecast_time': pd.to_datetime(
        ['2014-09-11 03:00', '2014-09-11 04:00', '2014-09-11 04:00', '2014-09-11 04:00'], utc=True)})
    mapping = pd.DataFrame({'harp': [1, 2], 'date': [pd.Timestamp('2014-09-11').date()]*2, 'noaa': [12158, 12157]})
    out = attach_history(frame, mapping, reports, events)
    assert list(out.columns) == HISTORY
    assert out.history_available.tolist() == [0.0, 1.0, 1.0, 0.0]  # 03:00 is inside the 30 min margin; HARP 3 unnumbered
    assert np.isnan(out.reg_mx_3d[0]) and out.reg_mx_3d[1] == 1 and out.reg_mx_3d[2] == 0
    assert out.reg_c_1d[2] == 1 and out.reg_events_3d[2] == 2
    assert np.isnan(out.reg_mx_1d[3]) and out.disk_mx_1d[3] == 1  # disk context does not need a NOAA number


def test_protocol_is_frozen_at_the_v2_operating_point():
    config = json.loads((ROOT/'config/activity-history-v1.json').read_text())
    assert config['recall_target'] == 0.9 and config['reserved_test_accessed'] is False
    assert config['budget']['hyperparameter_search'] == 0 and 2018 not in config['years']
