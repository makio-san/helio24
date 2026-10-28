import pandas as pd
import pytest
from helio24.walk_forward import annual_fold, evaluable_metrics


def test_fold_purges_overlap_and_shared_regions():
    times = pd.to_datetime(['2020-06-01', '2020-12-31T18:00', '2021-06-01',
                            '2021-07-01', '2022-01-01T06:00', '2022-06-01'], utc=True, format='mixed')
    table = pd.DataFrame({'forecast_time': times, 'observation_start': times-pd.Timedelta(hours=12),
                          'prediction_end': times+pd.Timedelta(hours=24), 'harp': [1,2,1,3,4,5],
                          'target': [0,1,1,0,1,1]})
    groups, audit = annual_fold(table, 2022)
    assert groups['train'].harp.tolist() == [1]
    assert groups['calibration'].harp.tolist() == [3]
    assert groups['evaluation'].harp.tolist() == [5]
    assert audit[0]['boundary_removed'] == 1
    assert audit[1]['shared_harp_rows_removed'] == 1
    changed = table.copy(); changed.loc[5, 'target'] = 0
    other, _ = annual_fold(changed, 2022)
    pd.testing.assert_frame_equal(groups['train'], other['train'])
    pd.testing.assert_frame_equal(groups['calibration'], other['calibration'])
    with pytest.raises(ValueError):
        annual_fold(table, 2024)


def test_no_positive_year_has_undefined_recall():
    result = evaluable_metrics({'recall_defined': False, 'precision_defined': True,
                               'recall': 0., 'precision': 0., 'fp': 10})
    assert result['recall'] is None and result['average_precision'] is None
    assert result['precision'] == 0. and result['fp'] == 10
