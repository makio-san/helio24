import json
from pathlib import Path

import numpy as np
import pandas as pd

from scripts.audit_history_latency_ceiling import FEATURES, attach_event_history, parse_event_times, read

ROOT = Path(__file__).resolve().parents[1]
SGAS = ''':Product: 0502SGAS.txt
:Issued: 2023 May 02 0245 UTC
A.  Energetic Events
Begin  Max  End  Rgn   Loc   Xray  Op 245MHz 10cm   Sweep
 0210 0217 0222  3288        C3.9     110
 0313 0313 0314                       150
 2350 0005 0010  3293        M2.4
 1254      1622                                        IV
B.  Proton Events:  None.
'''


def test_event_times_fall_on_the_day_before_issue_and_cross_midnight():
    rows = parse_event_times(SGAS)
    assert [str(r['event_time']) for r in rows] == ['2023-05-01 02:22:00+00:00', '2023-05-01 03:14:00+00:00',
                                                    '2023-05-02 00:10:00+00:00', '2023-05-01 16:22:00+00:00']
    assert rows[0]['noaa'] == 13288 and rows[1]['noaa'] is None and np.isnan(rows[1]['logflux'])
    assert np.isclose(rows[2]['logflux'], -5+np.log10(2.4))


def test_zero_latency_history_uses_only_events_before_the_safety_margin():
    events = pd.DataFrame(parse_event_times(SGAS)).sort_values('event_time').reset_index(drop=True)
    events['ns'] = events.event_time.astype('datetime64[ns, UTC]').astype('int64')
    times = pd.to_datetime(['2023-05-02 00:30', '2023-05-02 00:40', '2023-05-02 12:00', '2023-05-02 12:00'], utc=True)
    frame = pd.DataFrame({'harp': [1, 1, 1, 2], 'forecast_time': times})
    mapping = pd.DataFrame({'harp': [1], 'date': [pd.Timestamp('2023-05-02').date()], 'noaa': [13293]})
    out = attach_event_history(frame, mapping, events)
    assert list(out.columns) == FEATURES
    # The M2.4 ended 00:10: invisible at 00:30 (cutoff 00:00), visible at 00:40.
    assert out.reg_mx_6h.tolist()[:3] == [0.0, 1.0, 0.0] and out.reg_mx_12h.tolist()[:3] == [0.0, 1.0, 1.0]
    assert np.isnan(out.reg_hours_since_mx[0]) and np.isclose(out.reg_hours_since_mx[1], 0.5)
    assert np.isclose(out.reg_hours_since_mx[2], 11+50/60) and np.isclose(out.reg_max_logflux_24h[2], -5+np.log10(2.4))
    assert out.disk_mx_24h.tolist() == [0.0, 1.0, 1.0, 1.0]
    # HARP 2 has no NOAA number: regional values are missing, never zero.
    assert out.event_available.tolist() == [1.0, 1.0, 1.0, 0.0] and np.isnan(out.reg_mx_24h[3])


def test_reading_and_frozen_protocol():
    assert read(dict(all_year_primary=False, cycle25_primary=True, cycle25_bootstrap_lower_above_zero=True)) == 'L1_latency_binding'
    assert read(dict(all_year_primary=False, cycle25_primary=True, cycle25_bootstrap_lower_above_zero=False)) == 'L2_no_gain_at_zero_latency'
    config = json.loads((ROOT/'config/history-latency-ceiling-v1.json').read_text())
    v2 = json.loads((ROOT/'config/activity-history-v2.json').read_text())
    assert config['status'] == 'frozen_before_any_candidate_result' and config['reserved_test_accessed'] is False
    assert config['features'] == FEATURES and config['source_scan']['nothing_downloaded'] is True
    assert config['acceptance']['per_year_primary'] == v2['acceptance']['per_year_primary'] and config['years'] == v2['years']
    assert config['evidence']['table_report_sha256'] == v2['evidence']['table_report_sha256']
    assert set(config['reading']) == {'L1_latency_binding', 'L2_no_gain_at_zero_latency'}
