import pandas as pd
from helio24.calibration_periods import split_calibration


def test_calibration_halves_purge_overlap_and_shared_regions():
    t=pd.to_datetime(['2022-05-01','2022-06-30T12:00','2022-07-01T06:00','2022-08-01','2022-09-01'],utc=True,format='mixed')
    d=pd.DataFrame({'forecast_time':t,'observation_start':t-pd.Timedelta(hours=12),
                    'prediction_end':t+pd.Timedelta(hours=24),'harp':[1,2,3,1,4],'target':[1,0,1,0,1]})
    early,late,audit=split_calibration(d,2023)
    assert early.index.tolist()==[0] and late.index.tolist()==[4]
    assert audit['boundary_removed']==2 and audit['shared_harp_rows_removed']==1
    changed=d.copy();changed.loc[4,'target']=0
    other,_,_=split_calibration(changed,2023)
    pd.testing.assert_frame_equal(other,early)
