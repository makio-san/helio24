import numpy as np
import pandas as pd
from helio24.hard_negatives import mining_split, training_weights, paired_deltas


def test_mining_is_temporal_and_weight_budget_matches():
    t=pd.to_datetime(['2019-05-01','2020-05-01','2021-05-01','2021-06-01'],utc=True)
    d=pd.DataFrame({'harp':[1,1,2,3],'forecast_time':t,'observation_start':t-pd.Timedelta(hours=12),
                    'prediction_end':t+pd.Timedelta(hours=24),'target':[1,0,0,0]})
    teacher,mining=mining_split(d,2023)
    assert teacher.index.tolist()==[0] and mining.index.tolist()==[2,3]
    a,b,selected=training_weights(d,mining,np.array([.5,.5]))
    assert selected.index.tolist()==[2]
    assert a[0]==b[0]==1 and a[2]==3 and a[1]==a[3]==1
    np.testing.assert_allclose(a.sum(),b.sum())


def test_paired_identical_predictions_have_zero_differences():
    result=paired_deltas([0,1,0,1],[.1,.8,.7,.9],[.1,.8,.7,.9],[1,1,2,2],.5,.5,draws=30)
    for value in result.values():assert value['lower']==value['upper']==0
