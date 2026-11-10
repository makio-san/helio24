import json
from pathlib import Path

import pandas as pd

from scripts.audit_label_coverage import classify, parse_major_events

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = """A.  Energetic Events
Begin  Max  End  Rgn   Loc   Xray  Op 245MHz 10cm   Sweep
 0107 0114 0120  2994 N12E44 M1.2  1n
 0120 0136 0144  2992        M7.2     200
 1415 1415 1415                       110
 1739 1756 1813  2993 N20E27 C7.7  Sf 150
 2300 2310 2320       N10W10 X1.0
B.  Proton Events:  None.
"""


def test_parse_major_events_uses_the_previous_ut_day_and_five_digit_regions():
    events = parse_major_events(SAMPLE, '2022-04-21')
    assert [e['goes_class'] for e in events] == ['M1.2', 'M7.2', 'X1.0']
    assert events[0]['peak_time'] == pd.Timestamp('2022-04-20 01:14', tz='UTC') and events[0]['noaa'] == 12994
    assert events[2]['noaa'] is None


def test_classify_separates_covered_hidden_and_missing_windows():
    events = pd.DataFrame({'peak_time': pd.to_datetime(['2022-04-20 01:14', '2022-04-20 01:36', '2022-04-20 23:10', '2022-04-21 05:00'], utc=True),
                           'goes_class': ['M1.2', 'M7.2', 'X1.0', 'M2.0'], 'noaa': [12994, 12992, 12995, 12990]})
    mapping = pd.DataFrame({'harp': [1, 2, 4, 3], 'date': [pd.Timestamp('2022-04-20').date()]*4, 'noaa': [12994, 12992, 12992, 12995]})
    table = pd.DataFrame({'harp': [1, 2], 'forecast_time': pd.to_datetime(['2022-04-20 00:00', '2022-04-20 00:00']),
                          'prediction_end': pd.to_datetime(['2022-04-21 00:00']*2), 'target': [1, 0]})
    best, mapped = classify(events, mapping, table)
    status = best.set_index('goes_class').status
    assert status['M1.2'] == 'covered' and status['M7.2'] == 'hidden' and status['X1.0'] == 'no_window' and status['M2.0'] == 'unmapped'
    assert best.set_index('goes_class').ambiguous['M7.2'] and not best.set_index('goes_class').ambiguous['M1.2']


def test_protocol_is_a_frozen_data_audit():
    config = json.loads((ROOT/'config/label-coverage-v1.json').read_text())
    assert config['status'] == 'frozen_before_any_result' and config['reserved_test_accessed'] is False
    assert 'No relabelling in this audit' in config['prohibitions']
    assert config['evaluation_years'] == [2014, 2015, 2016, 2017, 2022, 2023] and 2024 not in config['years']
    assert set(config['reading']) == {'R1_coverage_collapsed', 'R2_labels_hold', 'mixed'}
