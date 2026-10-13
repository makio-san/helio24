import numpy as np
import pandas as pd
import pytest

from helio24.data import FEATURE_COLUMNS
from helio24.temporal import TEMPORAL_FEATURE_COLUMNS
from helio24.temporal_experiment import (
    chronological_fold,
    error_audit,
    merge_feature_tables,
    promotion_decision,
)


def test_feature_merge_requires_exact_identity():
    base = pd.DataFrame([dict(archive_member='a', partition=1, harp=7,
                              forecast_time=pd.Timestamp('2011-01-01'), target=0,
                              **{column: 1.0 for column in FEATURE_COLUMNS})])
    temporal = pd.DataFrame([dict(archive_member='a', partition=1, harp=7,
                                  forecast_time=pd.Timestamp('2011-01-01'), target=0,
                                  **{column: 2.0 for column in TEMPORAL_FEATURE_COLUMNS})])
    merged = merge_feature_tables(base, temporal)
    assert len(merged) == 1
    assert merged[TEMPORAL_FEATURE_COLUMNS].eq(2).all().all()
    temporal.loc[0, 'target'] = 1
    with pytest.raises(ValueError, match='identities'):
        merge_feature_tables(base, temporal)


def test_walk_forward_fold_purges_overlap_and_shared_regions():
    rows = []
    for partition, start in [(1, '2011-01-01'), (2, '2012-01-01')]:
        for target in [0, 1]:
            observation = pd.Timestamp(start) + pd.Timedelta(hours=target)
            rows.append(dict(partition=partition, harp=partition*10+target, target=target,
                             observation_start=observation,
                             forecast_time=observation+pd.Timedelta(hours=12),
                             prediction_end=observation+pd.Timedelta(hours=36)))
    rows.append(dict(rows[0], observation_start=pd.Timestamp('2011-12-31 13:00'),
                     forecast_time=pd.Timestamp('2012-01-01 01:00'),
                     prediction_end=pd.Timestamp('2012-01-02 01:00'), harp=99))
    rows.extend([dict(rows[2], harp=10), dict(rows[3], harp=10)])
    train, evaluation, audit = chronological_fold(pd.DataFrame(rows), (1,), 2)
    assert len(train) == 2
    assert len(evaluation) == 2
    assert audit['boundary_removed'] == 1
    assert audit['shared_harp_rows_removed'] == 2
    assert set(train.harp).isdisjoint(evaluation.harp)


def test_promotion_rule_requires_fold_majority_and_pooled_reduction():
    rows = []
    for fold, control_fp, temporal_fp, control_ap, temporal_ap in [
        ('A', 10, 8, .3, .31), ('B', 20, 18, .4, .4), ('C', 5, 6, .5, .49),
    ]:
        for model, fp, ap in [('control', control_fp, control_ap),
                              ('temporal', temporal_fp, temporal_ap)]:
            rows.append(dict(fold=fold, model=model, recall_target=.9, fp=fp,
                             average_precision=ap))
    decision = promotion_decision(rows)
    assert decision['promising'] is True
    rows[-1]['fp'] = 25
    assert promotion_decision(rows)['promising'] is False


def test_error_audit_reports_denominators_and_region_concentration():
    frame = pd.DataFrame(dict(
        harp=[1, 1, 2, 2],
        forecast_time=pd.to_datetime(['2014-01-01', '2014-02-01', '2014-04-01', '2014-05-01']),
        target=[1, 0, 1, 0],
        missing_fraction=[0, .005, .02, .06],
    ))
    audited, quarter, missingness, harp, summary = error_audit(
        frame, np.array([.9, .8, .1, .2]), .5
    )
    assert audited.outcome.tolist() == ['hit', 'false_alarm', 'miss', 'correct_quiet']
    assert quarter.windows.sum() == 4
    assert missingness.windows.sum() == 4
    assert harp.errors.sum() == 2
    assert summary['top_10_region_error_share'] == 1
