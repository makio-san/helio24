import pandas as pd
from scripts.audit_false_alarms import summarize


def test_runs_break_at_missing_times_true_positives_and_region_changes():
    d=pd.DataFrame({'harp':[1,1,1,1,1,2],
        'forecast_time':pd.to_datetime(['2023-01-01T00:00Z','2023-01-01T01:00Z',
        '2023-01-01T03:00Z','2023-01-01T04:00Z','2023-01-01T05:00Z','2023-01-01T06:00Z']),
        'target':[0,0,0,1,0,0],'missing_fraction':[0,0,.02,0,.1,0],
        'ensemble_alarm':[True]*6,'logistic_alarm':[True]*6,'xgboost_alarm':[False]*6})
    result,regions,missing,runs=summarize(d,2023)
    assert sorted(runs.windows)==[1,1,1,2]
    assert result['fp']==5 and result['negatives']==5 and result['fpr']==1
    assert result['complete_measurement_fp']==3
    assert result['both_models_alarm_fp']==0
    assert result['zero_positive_region_fp']==1
    assert missing.fp.sum()==5 and regions.negatives.sum()==5
