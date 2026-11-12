import json
from pathlib import Path

import pandas as pd

from scripts.audit_cycle25_relabelled import alert_false_positive_origin

ROOT = Path(__file__).resolve().parents[1]


def test_alert_false_positive_origin_separates_never_flaring_from_near_misses():
    t = pd.Timestamp('2023-01-01')
    hours = [0, 24, 200, 0, 24, 0]
    frame = pd.DataFrame({'harp': [1, 1, 1, 2, 2, 3], 'forecast_time': [t+pd.Timedelta(hours=h) for h in hours],
                          'target': [1, 0, 0, 0, 0, 0], 'probability': [.9, .8, .7, .6, .1, .2]})
    out = alert_false_positive_origin(frame, 0.5)
    # alarms: four windows; FP: harp 1 at +24 h (near), harp 1 at +200 h (far), harp 2 at 0 h (never flaring)
    assert out['alert_windows'] == 4 and out['alert_fp_windows'] == 3
    assert out['alert_fp_share_never_flaring_harps'] == 1/3
    assert out['alert_fp_share_within_72h_of_positive'] == 1/3


def test_protocol_v2_inherits_measures_and_readings_on_the_adopted_basis():
    v1 = json.loads((ROOT/'config/cycle25-diagnostic-v1.json').read_text())
    v2 = json.loads((ROOT/'config/cycle25-diagnostic-v2.json').read_text())
    pipeline = json.loads((ROOT/'config/walk-forward-v2.json').read_text())
    assert v2['status'] == 'frozen_before_any_result' and v2['reserved_test_accessed'] is False
    assert v2['years'] == v1['years'] and v2['eras'] == v1['eras'] and v2['budget'] == v1['budget']
    assert v2['evidence']['table'] == pipeline['source'] and v2['evidence']['table_report_sha256'] == pipeline['source_sha256']
    assert v2['evidence']['base_protocol'] == v1['evidence']['base_protocol'] == pipeline['recipes']
    assert 'config/cycle25-diagnostic-v1.json' in v2['measures']['inherited']
    assert 'No fit' in v2['measures']['D5_alert_false_positive_origin']
    assert v2['prohibitions'] == v1['prohibitions']
