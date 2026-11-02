"""Conditional whole-region uncertainty for frozen probability predictions."""
import numpy as np
import pandas as pd


def checked(target, probability, harp):
    y=np.asarray(target,dtype=float);p=np.asarray(probability,dtype=float);h=np.asarray(harp)
    if y.ndim!=1 or p.ndim!=1 or h.ndim!=1 or len(y)!=len(p) or len(y)!=len(h) or not len(y):raise ValueError('Matching nonempty arrays required')
    if not np.isin(y,[0,1]).all() or not np.isfinite(p).all() or (p<0).any() or (p>1).any():raise ValueError('Invalid binary targets or probabilities')
    if pd.isna(h).any():raise ValueError('Missing region identifiers')
    codes,regions=pd.factorize(h,sort=True)
    return y,p,codes,len(regions)


def region_weights(codes, regions, draws, seed):
    if regions<2 or draws<2:raise ValueError('At least two regions and draws required')
    rng=np.random.default_rng(seed)
    return np.array([np.bincount(rng.integers(0,regions,regions),minlength=regions) for _ in range(draws)])


def interval(values):
    values=np.asarray(values);finite=values[np.isfinite(values)]
    return {'lower':float(np.quantile(finite,.025)) if len(finite) else None,'upper':float(np.quantile(finite,.975)) if len(finite) else None,
            'valid_draws':len(finite),'undefined_draws':len(values)-len(finite)}


def paired_probability_intervals(target,candidate,control,harp,draws=1000,seed=24):
    y,a,codes,k=checked(target,candidate,harp);_,b,_,_=checked(target,control,harp)
    weights=region_weights(codes,k,draws,seed);n=np.bincount(codes,minlength=k);den=weights@n
    eps=np.finfo(float).eps
    loss=lambda p:-(y*np.log(np.clip(p,eps,1-eps))+(1-y)*np.log1p(-np.clip(p,eps,1-eps)))
    result={}
    for name,delta in [('brier',(a-y)**2-(b-y)**2),('log_loss',loss(a)-loss(b))]:
        sums=np.bincount(codes,weights=delta,minlength=k)
        result[name]={'estimate':float(delta.mean()),**interval((weights@sums)/den)}
    return result


def reliability(target,probability,harp,edges,draws=1000,seed=24):
    y,p,codes,k=checked(target,probability,harp);edges=np.asarray(edges,dtype=float)
    if edges[0]!=0 or edges[-1]!=1 or not np.all(np.diff(edges)>0):raise ValueError('Increasing probability edges must span 0 to 1')
    bins=np.searchsorted(edges[1:-1],p,side='left');weights=region_weights(codes,k,draws,seed);rows=[]
    for i in range(len(edges)-1):
        take=bins==i;n=int(take.sum());positive=int(y[take].sum())
        counts=np.bincount(codes[take],minlength=k);positives=np.bincount(codes[take],weights=y[take],minlength=k)
        den=weights@counts;num=weights@positives
        samples=np.divide(num,den,out=np.full(draws,np.nan),where=den>0)
        mean=float(p[take].mean()) if n else None;rate=positive/n if n else None
        rows.append({'bin':i,'left':float(edges[i]),'right':float(edges[i+1]),'n':n,'positives':positive,'regions':int((counts>0).sum()),
                     'positive_regions':int((positives>0).sum()),'mean_probability':mean,'observed_rate':rate,
                     'observed_minus_predicted':rate-mean if n else None,**interval(samples)})
    return rows


def coverage_contrast(rows,candidate,control,required_years,required_all_years=None):
    """Keep required coverage explicit even when both arms lack future years."""
    from helio24.experiment_review import annual_contrast
    result=annual_contrast(rows,candidate,control)
    present={arm:{r['year'] for r in rows if r['arm']==arm and r['positives']>0} for arm in [candidate,control]}
    missing=sorted(set(required_years)-(present[candidate]&present[control]))
    result['required_positive_years']=len(set(required_years))
    result['missing_years']=','.join(map(str,missing)) or 'none'
    present_all={arm:{r['year'] for r in rows if r['arm']==arm} for arm in [candidate,control]}
    missing_all=sorted(set(required_all_years or required_years)-(present_all[candidate]&present_all[control]))
    result['missing_eligible_years']=','.join(map(str,missing_all)) or 'none'
    result['all_year_full']=result['all_year_full'] and not missing and not missing_all
    return result
