"""Descriptive score and positive-region influence diagnostics."""
import numpy as np
import pandas as pd
from helio24.calibration import recall_threshold


def summarize_scores(frame, probability):
    p=np.asarray(probability,dtype=float)
    if len(p)!=len(frame) or not np.isfinite(p).all():raise ValueError('Finite aligned scores required')
    y=frame.target.to_numpy();counts=frame.loc[frame.target.eq(1)].groupby('harp').size().sort_values(ascending=False)
    n=int(counts.sum())
    result={'rows':len(frame),'positives':n,'positive_regions':len(counts),
        'top1_positive_share':float(counts.head(1).sum()/n) if n else None,
        'top3_positive_share':float(counts.head(3).sum()/n) if n else None,
        'concentration_equivalent_regions':float(n*n/(counts.astype(float)**2).sum()) if n else None}
    for label,name in [(0,'negative'),(1,'positive')]:
        values=p[y==label]
        for q in [.05,.5,.95]:result[f'{name}_q{int(q*100):02}']=float(np.quantile(values,q)) if len(values) else None
    if set(np.unique(y))!={0,1}:return result,[]
    threshold=recall_threshold(y,p,.95)
    result['threshold']=threshold
    result['negative_alarm_rate']=float((p[y==0]>=threshold).mean())
    influences=[]
    for harp in counts.index:
        keep=frame.harp.ne(harp).to_numpy()
        new=recall_threshold(y[keep],p[keep],.95) if set(np.unique(y[keep]))=={0,1} else None
        influences.append({'harp':int(harp),'removed_positives':int(counts.loc[harp]),
            'removed_rows':int((~keep).sum()),'threshold_without_region':new,
            'threshold_delta':new-threshold if new is not None else None})
    valid=[r['threshold_without_region'] for r in influences if r['threshold_without_region'] is not None]
    result.update(loro_valid=len(valid),loro_undefined=len(influences)-len(valid),
        loro_min=min(valid) if valid else None,loro_max=max(valid) if valid else None)
    return result,influences
