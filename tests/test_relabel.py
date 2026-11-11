import json
from pathlib import Path

import pandas as pd
import pytest

from helio24.relabel import recover_unassigned_events, relabel_windows
from helio24.v2_contract import EVENT_COLUMNS

ROOT = Path(__file__).resolve().parents[1]
DAY = pd.Timestamp('2022-04-20').date()


def hek(*rows):
    return pd.DataFrame(rows, columns=['event_id', 'peak_time', 'goes_class'])


def test_recovery_outcomes_follow_the_frozen_rules():
    events = hek(('a', '2022-04-20 01:14:00+00:00', 'M1.2'), ('b', '2022-04-20 01:36:00+00:00', 'M7.2'),
                 ('c', '2022-04-20 23:10:00+00:00', 'X1.0'), ('d', '2022-04-20 05:00:00+00:00', 'M2.0'),
                 ('e', '2022-04-20 09:00:00+00:00', 'M3.0'))
    sgas = pd.DataFrame({'peak_time': pd.to_datetime(['2022-04-20 01:16', '2022-04-20 01:36', '2022-04-20 23:10',
                                                      '2022-04-20 05:00', '2022-04-20 09:30'], utc=True),
                         'goes_class': ['M1.2', 'M7.2', 'X1.0', 'M2.0', 'M3.0'],
                         'noaa': [12994, 12992, None, 12990, 12991]})
    mapping = pd.DataFrame({'harp': [1, 2, 4], 'date': [DAY]*3, 'noaa': [12994, 12992, 12992]})
    recovery = recover_unassigned_events(events, sgas, mapping).set_index('event_id')
    assert recovery.outcome.to_dict() == {'a': 'recovered', 'b': 'ambiguous', 'c': 'no_region',
                                          'd': 'unmapped', 'e': 'no_sgas_match'}
    assert recovery.harps['a'] == '1' and recovery.harps['b'] == '2;4' and recovery.regions['d'] == '12990'


def attached(harp, peak, confidence='high'):
    return dict(zip(EVENT_COLUMNS, [harp, peak, peak, peak, 'M5.0', confidence, True, False, False, 1, 0.0]))


def test_relabel_adds_recovered_positives_and_keeps_fail_closed_exclusions():
    windows = pd.DataFrame({'harp': [1, 2, 4, 3, 3, 1],
                            'forecast_time': pd.to_datetime(['2022-04-20 00:00']*4+['2022-04-21 06:00']*2, utc=True)})
    windows['prediction_end'] = windows.forecast_time+pd.Timedelta(hours=24)
    unassigned = hek(('a', '2022-04-20 01:14:00+00:00', 'M1.2'), ('b', '2022-04-20 01:36:00+00:00', 'M7.2'),
                     ('e', '2022-04-20 09:00:00+00:00', 'M3.0'), ('f', '2022-04-21 12:00:00+00:00', 'M3.0'))
    recovery = pd.DataFrame({'event_id': ['a', 'b', 'e', 'f'], 'peak_time': unassigned.peak_time,
                             'goes_class': unassigned.goes_class, 'regions': ['12994', '12992', '', ''],
                             'harps': ['1', '2;4', '', '3'], 'outcome': ['recovered', 'ambiguous', 'no_sgas_match', 'recovered']})
    events = pd.DataFrame([attached(3, '2022-04-20 03:00:00')])
    result = relabel_windows(windows, events, unassigned, recovery, inventory_complete=True)
    # f is unassigned under the frozen contract and recovered to HARP 3 here: HARP 3 turns positive, HARP 1 negative.
    assert list(result.label_status_v2) == ['excluded_unassigned_major_event']*3+['positive']+['excluded_unassigned_major_event']*2
    assert list(result.label_status) == ['positive', 'excluded_ambiguous_harp', 'excluded_ambiguous_harp',
                                         'positive', 'positive', 'negative']
    assert list(result.target) == [1, 0, 0, 1, 1, 0]
    with pytest.raises(ValueError):
        relabel_windows(windows, events, unassigned, recovery.assign(event_id=['a', 'b', 'e', 'zz']), inventory_complete=True)


def test_protocol_is_frozen_development_evidence():
    config = json.loads((ROOT/'config/relabel-v1.json').read_text())
    assert config['status'] == 'frozen_before_any_result' and config['reserved_test_accessed'] is False
    assert 'No override of V2 attachments' in config['prohibitions']
    assert set(config['association']['outcomes']) == {'recovered', 'ambiguous', 'unmapped', 'no_region', 'no_sgas_match'}
    assert set(config['walk_forward']['arms']) == {'frozen_models_old_labels', 'frozen_models_new_labels', 'relabelled_models'}
    assert set(config['reading']) == {'R1_labels_explain_cycle25', 'R2_accuracy_goal', 'R3_label_versus_model', 'R4_no_gain'}
