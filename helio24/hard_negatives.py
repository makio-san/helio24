"""Training-only hard-negative mining and paired region uncertainty."""
import numpy as np
import pandas as pd


def mining_split(train, year):
    boundary = pd.Timestamp(f'{year-3}-01-01', tz='UTC')
    teacher = train[train.prediction_end.le(boundary)].copy()
    mining = train[train.observation_start.ge(boundary) & train.target.eq(0)].copy()
    mining = mining[~mining.harp.isin(teacher.harp.unique())]
    return teacher, mining


def training_weights(train, mining, scores, fraction=.1, weight=3.):
    if not len(mining) or len(scores)!=len(mining) or not np.isfinite(scores).all():
        raise ValueError('Finite mining scores required')
    ranked=mining.assign(score=scores).sort_values(['score','forecast_time','harp'],ascending=[False,True,True])
    chosen=ranked.head(int(np.ceil(fraction*len(ranked))))
    if not chosen.target.eq(0).all() or not chosen.index.isin(train.index).all():
        raise ValueError('Only training negatives may be weighted')
    targeted=np.ones(len(train));targeted[train.index.isin(chosen.index)]=weight
    uniform=np.ones(len(train));negative=train.target.eq(0).to_numpy()
    uniform[negative]=1+(weight-1)*len(chosen)/negative.sum()
    return targeted,uniform,chosen


def paired_deltas(target, first, second, harp, first_threshold, second_threshold, draws=1000, seed=24):
    """Candidate minus control on the same resampled HARP clusters."""
    y=np.asarray(target,dtype=bool);a=np.asarray(first)>=first_threshold;b=np.asarray(second)>=second_threshold
    d=pd.DataFrame({'harp':np.asarray(harp),'atp':a&y,'afp':a&~y,'afn':~a&y,
                    'btp':b&y,'bfp':b&~y,'bfn':~b&y})
    totals=d.groupby('harp',sort=True).sum().to_numpy(dtype=float)
    rng=np.random.default_rng(seed)
    s=np.array([totals[rng.integers(0,len(totals),len(totals))].sum(axis=0) for _ in range(draws)])
    def div(a,b):return np.divide(a,b,out=np.full_like(a,np.nan),where=b>0)
    tp,fp,fn,ctp,cfp,cfn=s.T
    values={'precision':div(tp,tp+fp)-div(ctp,ctp+cfp),'recall':div(tp,tp+fn)-div(ctp,ctp+cfn),'fp':fp-cfp}
    return {k:{'lower':float(np.quantile(v[np.isfinite(v)],.025)) if np.isfinite(v).any() else None,
               'upper':float(np.quantile(v[np.isfinite(v)],.975)) if np.isfinite(v).any() else None,
               'valid_draws':int(np.isfinite(v).sum())} for k,v in values.items()}
