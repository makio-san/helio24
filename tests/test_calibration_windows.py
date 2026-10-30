import pandas as pd
from helio24.calibration_windows import calibration_windows


def test_nested_windows_share_training_and_exclude_future_and_shared_regions():
    t=pd.to_datetime(['2019-05-01','2019-12-31T18:00','2020-05-01','2021-05-01',
                      '2021-07-01','2022-05-01','2022-06-01'],utc=True,format='mixed')
    d=pd.DataFrame({'harp':[1,2,3,4,1,5,3],'forecast_time':t,
        'observation_start':t-pd.Timedelta(hours=12),'prediction_end':t+pd.Timedelta(hours=24),
        'target':[1,0,1,0,1,1,0]})
    g,a=calibration_windows(d,2022)
    assert g['train'].harp.tolist()==[1]
    assert g['two_year'].harp.tolist()==[3,4]
    assert g['one_year'].harp.tolist()==[4]
    assert g['evaluation'].harp.tolist()==[5]
    assert a['roles']['two_year']['positive_regions']==1
    changed=d.copy();changed.loc[5:,'target']=0
    other,_=calibration_windows(changed,2022)
    for role in ['train','one_year','two_year']:pd.testing.assert_frame_equal(g[role],other[role])
