import pandas as pd

from helio24.v2_labels import reconcile_major_events


def attached(harp, peak, goes):
    peak = pd.Timestamp(peak)
    return {
        'harp_number': harp, 'start_time': peak-pd.Timedelta(minutes=5),
        'peak_time': peak, 'end_time': peak+pd.Timedelta(minutes=5),
        'goes_class': goes, 'confidence': 'high', 'has_goes': True,
        'has_ssw': False, 'has_xrt': False, 'harp_vote': '1-0',
        'max_pair_distance_deg': 0.0,
    }


def test_reconciliation_separates_unassigned_and_class_conflicts():
    v2 = pd.DataFrame([attached(1, '2023-01-01 12:00', 'M1.0'),
                       attached(2, '2023-01-02 12:00', 'M2.0')])
    external = pd.DataFrame([
        {'event_id': 'e1', 'peak_time': '2023-01-01T12:00Z', 'goes_class': 'M1.0'},
        {'event_id': 'e2', 'peak_time': '2023-01-02T12:00Z', 'goes_class': 'M2.1'},
        {'event_id': 'e3', 'peak_time': '2023-01-03T12:00Z', 'goes_class': 'X1.0'},
    ])
    summary, unassigned, v2_only, conflicts = reconcile_major_events(v2, external)
    assert summary == {
        'attached_associations': 2, 'attached_distinct_peak_class': 2,
        'external_rows': 3, 'external_distinct_peak_class': 3,
        'exact_peak_class_matches': 1, 'v2_only_peak_class': 1,
        'external_unassigned_peak_class': 2, 'peak_class_conflicts': 1,
    }
    assert unassigned.event_id.tolist() == ['e2', 'e3']
    assert len(v2_only) == len(conflicts) == 1
