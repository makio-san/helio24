"""Localize frozen TCN error changes without modifying the ongoing experiment."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
import pandas as pd
from helio24.data import ROOT
from helio24.full_data import sha256
from helio24.sequence_training import verify_files
from helio24.temporal_errors import compare,grouped_errors,measurement_bins
from helio24.walk_forward import annual_fold


def run(plan_path,output):
    if output.exists():raise ValueError('Preserve audit output')
    plan=json.loads(plan_path.read_text());source=ROOT/plan['source'];fields=plan['measurement_fields']
    prepared_path=source/'prepared.json';prepared=json.loads(prepared_path.read_text())
    protocol_path=ROOT/'config/temporal-sequence-v2.json'
    if sha256(protocol_path)!=prepared['protocol_sha256']:raise ValueError('Execution protocol changed')
    protocol=json.loads(protocol_path.read_text());basepath=ROOT/protocol['base_protocol']
    if sha256(basepath)!=protocol['base_protocol_sha256']:raise ValueError('Base protocol changed')
    base=json.loads(basepath.read_text());materialized=ROOT/base['source']
    if sha256(materialized/'report.json')!=base['source_sha256']:raise ValueError('Feature manifest changed')
    feature_report=json.loads((materialized/'report.json').read_text());frames=[]
    for shard in feature_report['shards']:
        path=materialized/'shards'/shard['file']
        if sha256(path)!=shard['sha256']:raise ValueError('Feature shard changed')
        frames.append(pd.read_parquet(path,columns=['harp','forecast_time','observation_start','prediction_end','role','target','missing_fraction',*fields]))
    table=pd.concat(frames,ignore_index=True)
    if table.duplicated(['harp','forecast_time']).any() or (table.forecast_time>=pd.Timestamp('2024-01-01',tz='UTC')).any():raise ValueError('Invalid development population')
    for role,expected in feature_report['rows'].items():
        g=table[table.role.eq(role)]
        if len(g)!=expected or int(g.target.sum())!=feature_report['positives'][role]:raise ValueError('Feature population changed')
    summaries=[];regions=[];qualities=[];runs=[];conditions=[];cutpoints=[];sources=[]
    for year in plan['years']:
        folder=source/str(year);finished=folder/'finished.json'
        evidence=json.loads(finished.read_text());verify_files(folder,evidence['artifact_hashes'])
        groups,audit=annual_fold(table,year)
        expected=next(f for f in prepared['folds'] if f['year']==year)
        if expected['status']!='complete' or audit!=expected['audit']:raise ValueError('Annual split changed')
        frame=pd.read_parquet(folder/'predictions.parquet');evaluation=groups['evaluation']
        columns=['harp','forecast_time','target','missing_fraction']
        pd.testing.assert_frame_equal(frame[columns].reset_index(drop=True),evaluation[columns].reset_index(drop=True))
        frame=frame.merge(evaluation[['harp','forecast_time',*fields]],on=['harp','forecast_time'],how='left',validate='one_to_one')
        thresholds=json.loads((folder/'thresholds.json').read_text());assigned={}
        for field in fields:
            assigned[field],cuts=measurement_bins(groups['train'][field],frame[field])
            for i,value in enumerate(cuts):cutpoints.append({'year':year,'field':field,'cut_index':i+1,'value':float(value)})
        for candidate,control in plan['comparisons']:
            summary,region,quality,extra,allruns,flags=compare(frame,candidate,control,thresholds)
            for prefix,arm in [('candidate',candidate),('control',control)]:
                metric=next(m for m in evidence['metrics'] if m['arm']==arm)
                for key,actual in [('n',summary['rows']),('fp',summary[f'{prefix}_fp']),('precision',summary[f'{prefix}_precision']),('recall',summary[f'{prefix}_recall'])]:
                    expected_value=metric[key]
                    if expected_value is None:
                        if actual is not None:raise ValueError('Undefined metric mismatch')
                    elif not np.isclose(actual,expected_value,rtol=0,atol=1e-12):raise ValueError('Frozen metric mismatch')
            for prefix,arm in [('candidate',candidate),('control',control)]:
                metric=next(m for m in evidence['metrics'] if m['arm']==arm)
                for key in ['average_precision','brier','log_loss','threshold']:
                    summary[f'{prefix}_{key}']=metric[key]
            tags={'year':year,'candidate':candidate,'control':control};summaries.append({**tags,**summary})
            for values,collection,run_type in [(region,regions,None),(quality,qualities,None),(extra,runs,'extra_fp'),(allruns,runs,'candidate_fp')]:
                values=values.copy()
                for k,v in tags.items():values[k]=v
                if run_type is not None:values['run_type']=run_type
                collection.append(values)
            for field in fields:
                # compare() sorts by region/time; join bins by preserved original index.
                flags['measurement_bin']=assigned[field].reindex(flags.index)
                condition=grouped_errors(flags,'measurement_bin');condition['field']=field
                for k,v in tags.items():condition[k]=v
                if int(condition.rows.sum())!=len(flags) or int(condition.extra_fp.sum())!=summary['extra_fp']:
                    raise ValueError('Measurement bins lost forecast windows')
                conditions.append(condition)
        sources.append({'year':year,'finished_sha256':sha256(finished),'prediction_sha256':sha256(folder/'predictions.parquet'),'thresholds_sha256':sha256(folder/'thresholds.json')})
        print(f'Audited {year}',flush=True)
    output.mkdir(parents=True)
    for name,value in [('summary',pd.DataFrame(summaries)),('regions',pd.concat(regions,ignore_index=True)),('missing_bins',pd.concat(qualities,ignore_index=True)),('runs',pd.concat(runs,ignore_index=True)),('measurement_bins',pd.concat(conditions,ignore_index=True)),('measurement_cutpoints',pd.DataFrame(cutpoints))]:value.to_csv(output/f'{name}.csv',index=False)
    report={'plan':plan,'plan_sha256':sha256(plan_path),'scope':'Fixed completed-year snapshot; post-hoc descriptive paired error audit; no model or threshold changes',
        'source':plan['source'],'completed_years':plan['years'],'source_folds':sources,'prepared_sha256':sha256(prepared_path),
        'feature_manifest_sha256':sha256(materialized/'report.json'),'protocol_sha256':sha256(protocol_path),
        'summaries':summaries,'reserved_test_accessed':False,
        'code_hashes':{n:sha256(ROOT/n) for n in ['helio24/temporal_errors.py','scripts/audit_temporal_errors.py']},
        'artifact_hashes':{p.name:sha256(p) for p in sorted(output.glob('*.csv'))}}
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(pd.DataFrame(summaries)[['year','candidate','control','extra_fp','removed_fp','net_fp','top10_extra_fp_share','top10_negative_share','complete_measurement_extra_fp','extra_fp_in_runs_ge6']].to_string(index=False))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--plan',type=Path,default=ROOT/'config/temporal-error-audit-v1.json');p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();run(a.plan.resolve(),a.output.resolve())
