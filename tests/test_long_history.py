import numpy as np
import pandas as pd
from helio24.long_history import history_features,HISTORY_COLUMNS
from helio24.v2_contract import V2_MEASUREMENTS,tai_to_utc


def example():
    time=pd.date_range('2023-01-02',periods=300,freq='12min')
    raw=pd.DataFrame({'harp_number':1,'obs_start':time,
                      **{name:np.arange(300,dtype=float)+1 for name in V2_MEASUREMENTS.values()}})
    window=pd.DataFrame({'harp':[1],'forecast_time':[tai_to_utc(time[240])],'role':['validation'],'target':[1]})
    roles={'validation':(pd.Timestamp('2023-01-01',tz='UTC'),pd.Timestamp('2024-01-01',tz='UTC'))}
    return raw,window,roles


def test_future_and_labels_cannot_change_history():
    raw,window,roles=example()
    expected=history_features(raw,window,roles)
    assert expected['TOTUSJH__48h_mean'].iloc[0]==120.5
    assert expected['TOTUSJH__24h_delta'].iloc[0]==119
    raw.loc[240:,list(V2_MEASUREMENTS.values())]=1e30
    window['target']=0
    pd.testing.assert_frame_equal(expected,history_features(raw,window,roles))


def test_short_or_gapped_history_keeps_forecast_with_missing_features():
    raw,window,roles=example()
    result=history_features(raw.iloc[1:],window,roles)
    assert len(result)==1 and result.history_48h_available.iloc[0]==0
    assert result.history_24h_available.iloc[0]==1
    result=history_features(raw.drop(index=200),window,roles)
    assert result.history_24h_available.iloc[0]==0
    assert result['TOTUSJH__24h_mean'].isna().all()
    assert len(HISTORY_COLUMNS)==196


def test_history_cannot_cross_role_boundary():
    raw,window,roles=example()
    roles['validation']=(window.forecast_time.iloc[0]-pd.Timedelta(hours=36),roles['validation'][1])
    result=history_features(raw,window,roles)
    assert result.history_24h_available.iloc[0]==1
    assert result.history_48h_available.iloc[0]==0
