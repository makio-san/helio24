"""Descriptive paired error localization on identical frozen forecast keys."""
import numpy as np
import pandas as pd


def add_error_flags(frame, candidate, control, thresholds):
    d=frame.sort_values(['harp','forecast_time']).copy()
    if d.duplicated(['harp','forecast_time']).any():raise ValueError('Duplicate forecast keys')
    if not d.target.isin([0,1]).all():raise ValueError('Binary targets required')
    for arm in [candidate,control]:
        if not np.isfinite(d[arm]).all() or not d[arm].between(0,1).all():raise ValueError('Invalid probabilities')
    a=d[candidate].ge(thresholds[candidate]);b=d[control].ge(thresholds[control]);negative=d.target.eq(0)
    for name,flag in {'negative':negative,'candidate_fp':negative&a,'control_fp':negative&b,
                      'extra_fp':negative&a&~b,'removed_fp':negative&~a&b,'shared_fp':negative&a&b,
                      'extra_tp':~negative&a&~b,'removed_tp':~negative&~a&b,
                      'candidate_tp':~negative&a,'control_tp':~negative&b}.items():d[name]=flag
    return d


def grouped_errors(d, column):
    r=d.groupby(column,observed=False,dropna=False).agg(rows=('target','size'),positives=('target','sum'),negatives=('negative','sum'),
        candidate_fp=('candidate_fp','sum'),control_fp=('control_fp','sum'),extra_fp=('extra_fp','sum'),removed_fp=('removed_fp','sum'),
        shared_fp=('shared_fp','sum'),extra_tp=('extra_tp','sum'),removed_tp=('removed_tp','sum')).reset_index()
    r['net_fp']=r.candidate_fp-r.control_fp
    if not r.net_fp.eq(r.extra_fp-r.removed_fp).all():raise ValueError('Paired decomposition failed')
    for arm in ['candidate','control']:r[f'{arm}_fpr']=r[f'{arm}_fp']/r.negatives.replace(0,np.nan)
    r['fpr_delta']=r.candidate_fpr-r.control_fpr
    return r


def error_runs(d, flag):
    d=d.sort_values(['harp','forecast_time'])
    contiguous=d.harp.eq(d.harp.shift())&d.forecast_time.diff().eq(pd.Timedelta(hours=1))
    group=(~(contiguous&d[flag]&d[flag].shift(fill_value=False))).cumsum()
    r=d[d[flag]].groupby(group[d[flag]]).agg(harp=('harp','first'),start=('forecast_time','min'),end=('forecast_time','max'),windows=(flag,'size')).reset_index(drop=True)
    return r


def missing_bins(values):
    bins=pd.cut(values,[-1e-12,0,.01,.05,1],labels=['zero','(0,0.01]','(0.01,0.05]','(0.05,1]'])
    return bins.cat.add_categories('unavailable').fillna('unavailable')


def measurement_bins(training, evaluation):
    finite=np.asarray(training,dtype=float);finite=finite[np.isfinite(finite)]
    if not len(finite):raise ValueError('No finite training measurements')
    cuts=np.unique(np.quantile(finite,[.25,.5,.75]))
    edges=np.r_[-np.inf,cuts,np.inf]
    labels=[f'bin{i+1}' for i in range(len(edges)-1)]
    result=pd.cut(evaluation.replace([np.inf,-np.inf],np.nan),edges,labels=labels,include_lowest=True)
    return result.cat.add_categories('unavailable').fillna('unavailable'),cuts


def compare(frame,candidate,control,thresholds):
    d=add_error_flags(frame,candidate,control,thresholds);regions=grouped_errors(d,'harp')
    extra=error_runs(d,'extra_fp');allruns=error_runs(d,'candidate_fp')
    top=regions[regions.extra_fp.gt(0)].sort_values(['extra_fp','harp'],ascending=[False,True]).head(10)
    neg=int(d.negative.sum());nextra=int(d.extra_fp.sum());fp=int(d.candidate_fp.sum());basefp=int(d.control_fp.sum())
    summary={'rows':len(d),'positives':int(d.target.sum()),'negatives':neg,'candidate_fp':fp,'control_fp':basefp,
        'extra_fp':nextra,'removed_fp':int(d.removed_fp.sum()),'shared_fp':int(d.shared_fp.sum()),'net_fp':fp-basefp,
        'extra_tp':int(d.extra_tp.sum()),'removed_tp':int(d.removed_tp.sum()),
        'top10_extra_fp':int(top.extra_fp.sum()),'top10_extra_fp_share':float(top.extra_fp.sum()/nextra) if nextra else None,
        'top10_negative_share':float(top.negatives.sum()/neg) if neg else None,
        'complete_measurement_extra_fp':int(d.loc[d.missing_fraction.eq(0),'extra_fp'].sum()),
        'zero_positive_region_extra_fp':int(regions.loc[regions.positives.eq(0),'extra_fp'].sum()),
        'extra_fp_in_runs_ge6':int(extra.loc[extra.windows.ge(6),'windows'].sum()),
        'max_extra_run':int(extra.windows.max()) if len(extra) else 0,
        'candidate_fp_in_runs_ge6':int(allruns.loc[allruns.windows.ge(6),'windows'].sum())}
    for arm,column in [('candidate',candidate),('control',control)]:
        tp=int(d[f'{arm}_tp'].sum());alarms=tp+summary[f'{arm}_fp']
        summary[f'{arm}_precision']=tp/alarms if alarms else None
        summary[f'{arm}_recall']=tp/summary['positives'] if summary['positives'] else None
    if summary['net_fp']!=summary['extra_fp']-summary['removed_fp']:raise ValueError('Net error mismatch')
    d['missing_bin']=missing_bins(d.missing_fraction)
    quality=grouped_errors(d,'missing_bin')
    return summary,regions,quality,extra,allruns,d
