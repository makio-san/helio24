"""Verify completed annual TCN outputs and freeze an interim or final comparison."""
import argparse
import json
import os
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
os.environ.setdefault('MPLCONFIGDIR',str(Path(__file__).resolve().parents[1]/'data/cache/matplotlib'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from helio24.data import ROOT
from helio24.full_data import sha256
from helio24.sequence_training import verify_files
from helio24.modeling import metrics
from helio24.metric_summary import enrich
from helio24.walk_forward import evaluable_metrics
from helio24.probability_review import paired_probability_intervals,reliability,coverage_contrast


def run(source,output,plan_path,years=None,require_complete=False):
    if output.exists():raise ValueError('Preserve snapshot')
    plan=json.loads(plan_path.read_text());prepared=json.loads((source/'prepared.json').read_text())
    protocol_path=ROOT/'config/temporal-sequence-v2.json'
    if sha256(protocol_path)!=prepared['protocol_sha256']:raise ValueError('Execution protocol changed')
    protocol=json.loads(protocol_path.read_text());eligible=[f['year'] for f in prepared['folds'] if f['status']=='complete']
    if require_complete:
        if years is not None:raise ValueError('Final mode derives all eligible years')
        if not (source/'report.json').exists() or not all((source/str(y)/'finished.json').exists() for y in eligible):raise ValueError('Final experiment is not complete')
        final=json.loads((source/'report.json').read_text());verify_files(source,final['artifact_hashes']);years=eligible
    elif not years:raise ValueError('Specify explicit interim years or --require-complete')
    years=sorted(years)
    if len(set(years))!=len(years) or not set(years)<=set(eligible):raise ValueError('Invalid snapshot years')
    refs={};reference_hashes={}
    for arm,path,expected,original_name in [('baseline',protocol['baseline_artifact'],protocol['baseline_report_sha256'],'ensemble'),
        ('short_training',protocol['short_control'],protocol['short_control_sha256'],'shared_train_one_year')]:
        folder=ROOT/path
        if sha256(folder/'report.json')!=expected:raise ValueError('Reference report changed')
        reference=json.loads((folder/'report.json').read_text());reference_hashes[path]=expected
        refs[arm]=[{**m,'arm':arm} for m in reference['metrics'] if m.get('model',m.get('arm'))==original_name]
    all_metrics=[];curve=[];intervals=[];sources=[];outcomes=[]
    comparisons=plan['comparisons'];bootstrap=plan['bootstrap'];options={k:bootstrap[k] for k in ['draws','seed']}
    for year in years:
        directory=source/str(year);report=json.loads((directory/'finished.json').read_text());verify_files(directory,report['artifact_hashes'])
        frame=pd.read_parquet(directory/'predictions.parquet');thresholds=json.loads((directory/'thresholds.json').read_text())
        if frame.duplicated(['harp','forecast_time']).any() or (frame.forecast_time>=pd.Timestamp('2024-01-01T00:00Z')).any():raise ValueError('Invalid evaluation keys')
        for saved in report['metrics']:
            arm=saved['arm'];actual=evaluable_metrics(enrich(metrics(frame.target,frame[arm],thresholds[arm])))
            for key,value in actual.items():
                if value is None:
                    if saved.get(key) is not None:raise ValueError('Undefined score differs')
                elif isinstance(value,(bool,np.bool_)):
                    if saved.get(key)!=bool(value):raise ValueError('Metric flag differs')
                elif not np.isclose(saved[key],value,rtol=1e-10,atol=1e-12):raise ValueError(f'Metric differs: {year}/{arm}/{key}')
            all_metrics.append(saved)
        for arm in plan['arms']:
            for row in reliability(frame.target,frame[arm],frame.harp,plan['probability_bins'],**options):curve.append({'year':year,'arm':arm,**row})
        for candidate,control in comparisons:
            old=next(i for i in report['paired_intervals'] if i['arm']==candidate and i['control']==control)
            for metric,values in old['differences'].items():
                a=next(m[metric] for m in report['metrics'] if m['arm']==candidate);b=next(m[metric] for m in report['metrics'] if m['arm']==control)
                intervals.append({'year':year,'candidate':candidate,'control':control,'metric':metric,'estimate':a-b if a is not None and b is not None else None,**values,'undefined_draws':bootstrap['draws']-values['valid_draws']})
            for metric,values in paired_probability_intervals(frame.target,frame[candidate],frame[control],frame.harp,**options).items():
                intervals.append({'year':year,'candidate':candidate,'control':control,'metric':metric,**values})
        sources.append({'year':year,'finished_sha256':sha256(directory/'finished.json'),'predictions_sha256':sha256(directory/'predictions.parquet')})
        print(f'Verified and evaluated {year}',flush=True)
    # Full reference coverage exposes missing positive years in every contrast.
    for candidate,control in comparisons:
        rows=[m for m in all_metrics if m['arm']==candidate]
        controls=refs.get(control,[m for m in all_metrics if m['arm']==control])
        required=[f['year'] for f in prepared['folds'] if f['status']=='complete' and
                  next(a['positives'] for a in f['audit'] if a['role']=='evaluation')>0]
        outcomes.append(coverage_contrast(rows+controls,candidate,control,required,eligible))
    rows=pd.DataFrame(all_metrics);seed_rows=[]
    for (year,arm),g in rows[rows.arm.str.contains('_seed')].assign(arm=lambda d:d.arm.str.replace(r'_seed\d+$','',regex=True)).groupby(['year','arm']):
        item={'year':year,'arm':arm,'seeds':len(g)}
        for metric in ['precision','recall','fp','average_precision','brier','log_loss']:
            item[f'{metric}_min']=float(g[metric].min()) if g[metric].notna().any() else None
            item[f'{metric}_max']=float(g[metric].max()) if g[metric].notna().any() else None
        seed_rows.append(item)
    folds=[]
    for f in prepared['folds']:
        evaluation=next(a for a in f['audit'] if a['role']=='evaluation')
        folds.append({'year':f['year'],'status':'included' if f['year'] in years else 'not_in_snapshot' if f['status']=='complete' else 'skipped',
            'rows':evaluation['rows'],'positives':evaluation['positives'],'reason':f.get('reason','')})
    output.mkdir(parents=True)
    for name,value in [('metrics',rows),('comparisons',pd.DataFrame(outcomes)),('intervals',pd.DataFrame(intervals)),('reliability',pd.DataFrame(curve)),('seed_spread',pd.DataFrame(seed_rows)),('folds',pd.DataFrame(folds))]:value.to_csv(output/f'{name}.csv',index=False)
    # Standalone scientific figure, with all populated bins on the full 0-1 range.
    fig,axes=plt.subplots((len(years)+1)//2,2,figsize=(11,4*((len(years)+1)//2)),squeeze=False)
    curves=pd.DataFrame(curve)
    for ax,year in zip(axes.flat,years):
        for arm,color in [('baseline','#586875'),('chronological','#d87a22')]:
            d=curves[(curves.year==year)&curves.arm.eq(arm)&curves.n.gt(0)]
            ax.plot(d.mean_probability,d.observed_rate,'o-',color=color,label=arm,markersize=3)
        ax.plot([0,1],[0,1],'--',color='#aaa',linewidth=1);ax.set(xlim=(0,1),ylim=(0,1),title=str(year),xlabel='Mean forecast probability',ylabel='Observed M/X window rate');ax.legend();ax.grid(alpha=.2)
    for ax in list(axes.flat)[len(years):]:ax.set_visible(False)
    fig.suptitle('Frozen annual probability reliability · populated bins; conditional intervals in CSV')
    fig.tight_layout();fig.savefig(output/'reliability.png',dpi=180);plt.close(fig)
    result={'status':'final_complete' if require_complete else 'interim_snapshot','selected_years':years,'eligible_years':eligible,
        'missing_eligible_years':[y for y in eligible if y not in years],'source':str(source.relative_to(ROOT)),
        'protocol_sha256':sha256(protocol_path),'prepared_sha256':sha256(source/'prepared.json'),'plan':plan,'plan_sha256':sha256(plan_path),
        'source_folds':sources,'reference_hashes':reference_hashes,'comparisons':outcomes,'model_promoted':False,'reserved_test_accessed':False,
        'code_hashes':{p:sha256(ROOT/p) for p in ['helio24/probability_review.py','scripts/evaluate_temporal_snapshot.py']},
        'artifact_hashes':{p.name:sha256(p) for p in sorted(output.iterdir()) if p.is_file()}}
    (output/'report.json').write_text(json.dumps(result,indent=2)+'\n')
    print(pd.DataFrame(outcomes).to_string(index=False))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,default=ROOT/'artifacts/temporal_years_20261101_r1');p.add_argument('--output',type=Path,required=True);p.add_argument('--plan',type=Path,default=ROOT/'config/temporal-evaluation-report-v1.json');p.add_argument('--years',nargs='+',type=int);p.add_argument('--require-complete',action='store_true')
    a=p.parse_args();run(a.source.resolve(),a.output.resolve(),a.plan.resolve(),a.years,a.require_complete)
