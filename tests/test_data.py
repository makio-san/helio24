import numpy as np
import pandas as pd
import pytest

from helio24.data import MAGNETIC_COLUMNS, FEATURE_COLUMNS, parse_name, extract_features, read_observation, chronological_split, trusted_measurements


def test_forecast_boundary_and_target():
    record = parse_name('M1.0@12:Primary_ar7_s2011-01-01T00:00:00_e2011-01-01T11:48:00.csv')
    assert record['forecast_time'] == pd.Timestamp('2011-01-01 12:00')
    assert record['prediction_end'] == pd.Timestamp('2011-01-02 12:00')
    assert record['target'] == 1
    assert parse_name('C1.0@12:Primary_ar7_s2011-01-01T00:00:00_e2011-01-01T11:48:00.csv')['target'] == 0


def observation():
    return pd.DataFrame({**{c: np.arange(60, dtype=float) for c in MAGNETIC_COLUMNS},
                         'IS_TMFI': True, 'QUALITY': 0,
                         'Timestamp': pd.date_range('2011-01-01', periods=60, freq='12min')})


def test_outcome_columns_never_change_features():
    frame = observation()
    first, _, _ = extract_features(frame)
    frame['MFLARE_LABEL'] = 'future event'
    frame['XR_MAX'] = 999999
    second, _, _ = extract_features(frame)
    assert first == second
    assert set(first) == set(FEATURE_COLUMNS)


def test_untrusted_endpoint_is_not_used():
    frame = observation()
    frame.loc[59, 'QUALITY'] = 1
    frame.loc[59, 'USFLUX'] = 1e30
    features, quality, _ = extract_features(frame)
    assert np.isnan(features['USFLUX__last'])
    assert np.isnan(features['USFLUX__delta'])
    assert features['USFLUX__mean'] == 29
    assert quality['untrusted_rows'] == 1


def test_plot_measurements_preserve_invalid_gaps_and_match_features():
    frame = observation()
    frame.loc[10, 'QUALITY'] = 1
    frame.loc[20, 'USFLUX'] = np.inf
    frame.loc[30, 'IS_TMFI'] = False
    clean = trusted_measurements(frame)
    assert len(clean) == 60
    assert clean.index.equals(frame.index)
    assert clean.loc[[10, 20, 30], 'USFLUX'].isna().all()
    features, _, _ = extract_features(frame)
    assert clean.USFLUX.mean() == features['USFLUX__mean']


def test_future_row_is_rejected(tmp_path):
    path = tmp_path / 'FQ_ar7_s2011-01-01T00:00:00_e2011-01-01T11:48:00.csv'
    frame = observation()
    frame.loc[59, 'Timestamp'] = pd.Timestamp('2011-01-01 12:00')
    frame.to_csv(path, sep='\t', index=False)
    with pytest.raises(ValueError, match='timestamps'):
        read_observation(path)


def test_splits_purge_windows_and_shared_regions():
    rows = []
    for p, day in [(1, '2011-01-01'), (3, '2012-01-01'), (5, '2013-01-01')]:
        for y in [0, 1]:
            start = pd.Timestamp(day)
            rows.append(dict(partition=p, harp=p*10+y, target=y, observation_start=start,
                             prediction_end=start+pd.Timedelta(hours=36)))
    rows.append(dict(rows[0], partition=3, observation_start=pd.Timestamp('2012-01-01'),
                     prediction_end=pd.Timestamp('2012-01-02 12:00')))
    rows.append(dict(rows[0], harp=99, observation_start=pd.Timestamp('2011-12-31'),
                     prediction_end=pd.Timestamp('2012-01-01 12:00')))
    groups, audit = chronological_split(pd.DataFrame(rows))
    assert [len(g) for g in groups.values()] == [2, 2, 2]
    assert audit[0]['boundary_purged'] == 1
    assert set(groups['train'].harp).isdisjoint(groups['validation'].harp)
