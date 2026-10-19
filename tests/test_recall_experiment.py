import numpy as np
import pandas as pd
import pytest

from helio24.recall_experiment import decision, development_roles, region_weights


def test_region_weights_give_equal_total_mass():
    regions = np.array([1, 1, 1, 2, 3, 3])
    weights = region_weights(regions)
    assert weights.mean() == pytest.approx(1)
    assert [weights[regions == k].sum() for k in [1, 2, 3]] == pytest.approx([2, 2, 2])


@pytest.mark.parametrize('field,value', [('recall', .949), ('fp', 101), ('average_precision', .39), ('brier', .021), ('log_loss', .11)])
def test_failed_quality_check_blocks_promotion(field, value):
    control = dict(model='control', recall=.95, fp=100, average_precision=.4, brier=.02, log_loss=.1)
    row = control | dict(model='candidate', fp=80)
    assert decision(row, control)['stretch_target']
    row[field] = value
    assert not decision(row, control)['promising']


def test_audit_partition_is_rejected_before_processing():
    with pytest.raises(ValueError, match='Only development'):
        development_roles(pd.DataFrame({'partition': [1, 2, 3, 4, 5]}), {})


def test_purge_and_region_exclusion_reproduce_frozen_counts():
    rows = []
    for part, day in [(1, 1), (2, 2), (3, 5), (4, 9)]:
        for target in [0, 1]:
            start = pd.Timestamp(f'2020-01-{day:02}')
            rows.append(dict(partition=part, harp=part*10+target, target=target,
                             observation_start=start, forecast_time=start+pd.Timedelta(hours=1),
                             prediction_end=start+pd.Timedelta(days=1)))
    rows.append(rows[0] | dict(prediction_end=pd.Timestamp('2020-01-06')))
    rows.append(rows[4] | dict(harp=10))
    frozen = dict(roles={k: dict(n=n, positives=n//2, harps=n) for k, n in [('train', 4), ('calibration', 2), ('validation', 2)]},
                  purge_audit=[dict(role=k, boundary=f'2020-01-{d:02}') for k, d in [('train', 5), ('calibration', 9), ('validation', 12)]])
    groups, audit = development_roles(pd.DataFrame(rows), frozen)
    assert audit[0]['boundary_removed'] == 1
    assert audit[1]['shared_harp_rows_removed'] == 1
    assert set(groups['train'].harp).isdisjoint(groups['calibration'].harp)
