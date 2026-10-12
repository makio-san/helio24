import pandas as pd

from helio24.review import classify_windows, review_export


def test_review_uses_frozen_threshold_including_equality():
    frame = pd.DataFrame({'probability': [0.5, 0.7, 0.1, 0.2], 'target': [1, 0, 1, 0]})
    result = classify_windows(frame, 0.5)
    assert result.outcome.tolist() == ['Hits', 'False alarms', 'Misses', 'Correct quiet forecasts']
    assert 'outcome' not in frame.columns


def test_export_excludes_local_paths_and_measurements():
    frame = pd.DataFrame([dict(harp=1, forecast_time='2015-01-01', prediction_end='2015-01-02',
                               label='FQ', probability=0.5, target=0, file='/local/private/file',
                               USFLUX=123)])
    exported = review_export(classify_windows(frame, 0.4))
    assert 'False alarms' in exported
    assert '/local' not in exported
    assert 'USFLUX' not in exported
