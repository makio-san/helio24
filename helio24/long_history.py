"""Long histories from raw magnetic observations, independent of target filtering."""
import numpy as np
import pandas as pd
from helio24.data import MAGNETIC_COLUMNS
from helio24.v2_contract import V2_MEASUREMENTS, utc_to_tai, TAI_TRANSITIONS

HOURS = (24, 48)
HISTORY_COLUMNS = [f'{field}__{hours}h_{stat}' for hours in HOURS
                   for field in MAGNETIC_COLUMNS for stat in ['mean','std','delta','relative_delta']]
HISTORY_COLUMNS += [f'history_{hours}h_{stat}' for hours in HOURS for stat in ['available','missing_fraction']]


def history_features(observations, windows, roles):
    """Keep every forecast; unavailable history is missing, never a dropped row."""
    required = ['harp_number','obs_start',*V2_MEASUREMENTS.values()]
    raw=observations[required].drop_duplicates().sort_values('obs_start')
    if raw.harp_number.nunique()!=1 or windows.harp.nunique()!=1 or int(raw.harp_number.iloc[0])!=int(windows.harp.iloc[0]):
        raise ValueError('One matching HARP required')
    if raw.obs_start.duplicated().any():raise ValueError('Conflicting raw measurements')
    clocks=pd.DatetimeIndex(raw.obs_start)
    if clocks.tz is not None:raise ValueError('Raw clocks must be naive TAI')
    times=clocks.as_unit('ns').asi8
    forecast=pd.DatetimeIndex(windows.forecast_time)
    if forecast.tz is None:raise ValueError('Forecast timestamps require UTC')
    ftime=pd.DatetimeIndex([utc_to_tai(t) for t in forecast]).as_unit('ns').asi8
    end=np.searchsorted(times,ftime,side='left')
    numeric=raw[list(V2_MEASUREMENTS.values())].apply(pd.to_numeric,errors='coerce').to_numpy(dtype=float, copy=True)
    numeric[~np.isfinite(numeric)]=np.nan
    finite=np.isfinite(numeric);filled=np.where(finite,numeric,0.)
    counts=np.vstack([np.zeros((1,24)),finite.cumsum(axis=0)])
    sums=np.vstack([np.zeros((1,24)),filled.cumsum(axis=0)])
    squares=np.vstack([np.zeros((1,24)),np.square(filled).cumsum(axis=0)])
    step=pd.Timedelta(minutes=12).value
    gaps=np.r_[0,np.cumsum(np.diff(times)!=step)]
    result=windows[['harp','forecast_time']].copy()
    for hours in HOURS:
        size=hours*5;start=end-size
        valid=(start>=0)&(end>0)&(end<=len(times))
        left=np.clip(start,0,len(times)-1);right=np.clip(end-1,0,len(times)-1)
        valid &= (times[left]==ftime-hours*pd.Timedelta(hours=1).value)&(times[right]==ftime-step)
        valid &= gaps[right]==gaps[left]
        for transition, _ in TAI_TRANSITIONS:
            valid &= ~((times[left] < transition.value) & (ftime >= transition.value))
        for role in windows.role.unique():
            if role not in roles:raise ValueError('Unknown or reserved role')
            valid &= (~windows.role.eq(role).to_numpy()) | (forecast-pd.Timedelta(hours=hours)>=roles[role][0])
        ids=np.flatnonzero(valid)
        block=np.full((len(windows),24,4),np.nan)
        missing=np.full(len(windows),np.nan)
        if len(ids):
            a,b=start[ids],end[ids]
            n=counts[b]-counts[a];den=np.where(n>0,n,np.nan)
            mean=(sums[b]-sums[a])/den
            std=np.sqrt(np.maximum((squares[b]-squares[a])/den-mean**2,0.))
            delta=numeric[b-1]-numeric[a]
            scale=np.abs(mean)+std
            relative=np.divide(delta,scale,out=np.full_like(delta,np.nan),where=scale>0)
            values=np.stack([mean,std,delta,np.clip(relative,-100,100)],axis=2)
            values[n<size*.8]=np.nan
            block[ids]=values
            missing[ids]=1-n.sum(axis=1)/(size*24)
        cols=[f'{field}__{hours}h_{stat}' for field in MAGNETIC_COLUMNS for stat in ['mean','std','delta','relative_delta']]
        frame=pd.DataFrame(block.reshape(len(windows),-1),columns=cols,index=windows.index)
        result=pd.concat([result,frame],axis=1)
        result[f'history_{hours}h_available']=valid.astype(float)
        result[f'history_{hours}h_missing_fraction']=missing
    return result[['harp','forecast_time',*HISTORY_COLUMNS]]
