import pandas as pd
import pytest

from helio24.data import FEATURE_COLUMNS, MAGNETIC_COLUMNS
from helio24.v2_contract import (
    EVENT_COLUMNS, audit_event_rows, extract_window, label_windows, prepare_events,
    prepare_unassigned_major_events, tai_to_utc,
    utc_to_tai,
)


def event(harp, peak, goes='M1.0', confidence='high', has_goes=True):
    peak = pd.Timestamp(peak)
    return dict(harp_number=harp, start_time=peak-pd.Timedelta(minutes=5),
                peak_time=peak, end_time=peak+pd.Timedelta(minutes=5),
                goes_class=goes, confidence=confidence, has_goes=has_goes,
                has_ssw=False, has_xrt=False, harp_vote='1-0',
                max_pair_distance_deg=None)


def windows():
    return pd.DataFrame([dict(harp=7, forecast_time=pd.Timestamp('2023-01-01T00:00Z'),
                                   prediction_end=pd.Timestamp('2023-01-02T00:00Z'))])


def empty_unassigned():
    return pd.DataFrame(columns=['event_id', 'peak_time', 'goes_class'])


def test_tai_to_utc_uses_historical_offsets_and_rejects_invalid_inputs():
    assert tai_to_utc('2011-01-01 00:00:00') == pd.Timestamp('2010-12-31 23:59:26Z')
    assert tai_to_utc('2013-01-01 00:00:00') == pd.Timestamp('2012-12-31 23:59:25Z')
    assert tai_to_utc('2016-01-01 00:00:00') == pd.Timestamp('2015-12-31 23:59:24Z')
    assert tai_to_utc('2023-01-01 00:00:00') == pd.Timestamp('2022-12-31 23:59:23Z')
    assert utc_to_tai('2023-01-01T00:00Z') == pd.Timestamp('2023-01-01 00:00:37')
    assert tai_to_utc(utc_to_tai('2023-01-01T00:00Z')) == pd.Timestamp('2023-01-01T00:00Z')
    with pytest.raises(ValueError, match='timezone-naive'):
        tai_to_utc('2023-01-01T00:00Z')
    with pytest.raises(ValueError, match='leap-second'):
        tai_to_utc('2017-01-01 00:00:36')


def test_labeling_is_half_open_goes_only_and_requires_complete_inventory():
    attached = pd.DataFrame([event(7, '2023-01-01 00:00:00'),
                             event(7, '2023-01-02 00:00:00', goes='X1.0')])
    with pytest.raises(ValueError, match='Complete unassigned'):
        label_windows(windows(), attached, empty_unassigned())
    result = label_windows(windows(), attached, empty_unassigned(), inventory_complete=True)
    assert result.loc[0, 'target'] == 1
    assert result.loc[0, 'label_status'] == 'positive'
    attached.loc[0, 'has_goes'] = False
    result = label_windows(windows(), attached, empty_unassigned(), inventory_complete=True)
    assert result.loc[0, 'target'] == 0


def test_ambiguous_and_unassigned_major_events_block_negative_labels():
    ambiguous = pd.DataFrame([event(7, '2023-01-01 12:00:00', confidence='very_low')])
    result = label_windows(windows(), ambiguous, empty_unassigned(), inventory_complete=True)
    assert result.loc[0, 'label_status'] == 'excluded_ambiguous_harp'
    unassigned = pd.DataFrame([dict(event_id='g1', peak_time=pd.Timestamp('2023-01-01T12:00Z'),
                                         goes_class='M2.0')])
    result = label_windows(windows(), pd.DataFrame(columns=EVENT_COLUMNS), unassigned,
                           inventory_complete=True)
    assert result.loc[0, 'label_status'] == 'excluded_unassigned_major_event'
    bad = unassigned.assign(goes_class='C9.9')
    with pytest.raises(ValueError, match='only M/X'):
        prepare_unassigned_major_events(bad)


def test_vectorized_labeling_keeps_positive_priority_across_regions():
    frame = pd.DataFrame([
        dict(harp=7, forecast_time=pd.Timestamp('2023-01-01T00:00Z'),
             prediction_end=pd.Timestamp('2023-01-02T00:00Z')),
        dict(harp=8, forecast_time=pd.Timestamp('2023-01-01T00:00Z'),
             prediction_end=pd.Timestamp('2023-01-02T00:00Z')),
        dict(harp=8, forecast_time=pd.Timestamp('2023-01-02T00:00Z'),
             prediction_end=pd.Timestamp('2023-01-03T00:00Z')),
    ])
    attached = pd.DataFrame([event(7, '2023-01-01 12:00:00'),
                             event(8, '2023-01-01 12:00:00', confidence='very_low')])
    unassigned = pd.DataFrame([
        dict(event_id='g1', peak_time=pd.Timestamp('2023-01-01T13:00Z'), goes_class='M2.0')])
    result = label_windows(frame, attached, unassigned, inventory_complete=True)
    assert result.target.tolist() == [1, 0, 0]
    assert result.label_status.tolist() == [
        'positive', 'excluded_ambiguous_harp', 'negative']


def test_labeling_normalizes_timestamp_resolution_before_interval_search():
    frame = windows()
    frame['forecast_time'] = frame.forecast_time.dt.as_unit('ns')
    frame['prediction_end'] = frame.prediction_end.dt.as_unit('ns')
    unassigned = pd.DataFrame([
        dict(event_id='g1', peak_time=pd.Timestamp('2023-01-01T12:00Z'), goes_class='M2.0')])
    unassigned['peak_time'] = unassigned.peak_time.dt.as_unit('us')
    result = label_windows(frame, pd.DataFrame(columns=EVENT_COLUMNS), unassigned,
                           inventory_complete=True)
    assert result.loc[0, 'label_status'] == 'excluded_unassigned_major_event'


def test_event_validation_fails_on_unknown_confidence_and_bad_order():
    frame = pd.DataFrame([event(7, '2023-01-01 12:00:00', confidence='guess')])
    with pytest.raises(ValueError, match='Unknown confidence'):
        prepare_events(frame)
    frame = pd.DataFrame([event(7, '2023-01-01 12:00:00')])
    frame.loc[0, 'start_time'] = pd.Timestamp('2023-01-01 13:00:00')
    with pytest.raises(ValueError, match='order'):
        prepare_events(frame)


def test_event_audit_quarantines_only_the_invalid_row():
    good = event(7, '2023-01-01 12:00:00')
    bad = event(8, '2023-01-02 12:00:00')
    bad['start_time'] = pd.Timestamp('2023-01-02 13:00:00')
    events, errors = audit_event_rows(pd.DataFrame([good, bad]))
    assert events.harp_number.tolist() == [7]
    assert errors == {'Flare start/peak/end order is invalid': 1}


def test_window_requires_exact_cadence_and_applies_finite_quality_policy():
    times = pd.date_range('2023-02-01', periods=60, freq='12min')
    frame = pd.DataFrame({'harp_number': 9, 'obs_start': times})
    for index, name in enumerate(MAGNETIC_COLUMNS):
        frame[name.lower()] = range(index, index+60)
    result = extract_window(frame)
    assert result['forecast_time'] == pd.Timestamp('2023-02-01 11:59:23Z')
    assert len([name for name in result if name in FEATURE_COLUMNS]) == 96
    frame.loc[:12, MAGNETIC_COLUMNS[0].lower()] = None
    with pytest.raises(ValueError, match='20%'):
        extract_window(frame)
    frame = frame.iloc[:-1]
    with pytest.raises(ValueError, match='60 rows'):
        extract_window(frame)
