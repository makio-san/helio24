import numpy as np
import pandas as pd
import pytest
from helio24.temporal_errors import compare,measurement_bins


def test_paired_errors_keep_exposure_and_break_runs_at_gaps_and_positives():
    d=pd.DataFrame({'harp':[1,1,1,1,1,2],'forecast_time':pd.to_datetime(['2023-01-01T00:00Z','2023-01-01T01:00Z','2023-01-01T03:00Z','2023-01-01T04:00Z','2023-01-01T05:00Z','2023-01-01T06:00Z']),
        'target':[0,0,0,1,0,0],'missing_fraction':[0,0,.02,0,.1,0],
        'new':[.8,.8,.8,.8,.1,.8],'old':[.1,.1,.1,.1,.8,.8]})
    summary,regions,bins,runs,_,_=compare(d,'new','old',{'new':.5,'old':.5})
    assert (summary['candidate_fp'],summary['control_fp'])==(4,2)
    assert (summary['extra_fp'],summary['removed_fp'],summary['shared_fp'],summary['net_fp'])==(3,1,1,2)
    assert summary['extra_tp']==1 and summary['removed_tp']==0
    assert sorted(runs.windows)==[1,2]
    assert regions.negatives.sum()==5 and bins.negatives.sum()==5
    assert summary['complete_measurement_extra_fp']==2
    assert summary['top10_negative_share']==4/5
    with pytest.raises(ValueError,match='Duplicate'):compare(pd.concat([d,d.iloc[[0]]]),'new','old',{'new':.5,'old':.5})


def test_measurement_bins_use_only_training_and_preserve_missing_values():
    train=pd.Series([0,1,2,3,4]);future=pd.Series([-100,1,3,1e30,np.nan])
    bins,cuts=measurement_bins(train,future)
    np.testing.assert_equal(cuts,[1,2,3])
    assert bins.astype(str).tolist()==['bin1','bin1','bin3','bin4','unavailable']
    _,same=measurement_bins(train,pd.Series([999999]))
    np.testing.assert_equal(cuts,same)
    tied,cuts=measurement_bins(pd.Series([0,0,0,0]),pd.Series([0,1,np.nan]))
    assert len(cuts)==1 and tied.astype(str).tolist()==['bin1','bin2','unavailable']
