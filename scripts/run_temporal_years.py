"""Prepare and execute the frozen annual TCN comparison using isolated workers."""
import argparse
import fcntl
import json
from pathlib import Path
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
import pandas as pd
from helio24.data import ROOT
from helio24.full_data import sha256
from helio24.sequence_training import prepare_cache,align_indices,fit_scaler,verify_files
from helio24.v2_training import load_development,METADATA
from helio24.walk_forward import annual_fold,evaluable_metrics
from helio24.calibration import SigmoidCalibration,recall_threshold
from helio24.modeling import metrics
from helio24.metric_summary import enrich
from helio24.hard_negatives import paired_deltas
from helio24.experiment_review import annual_contrast


def write_json(path,value):
    temporary=path.with_suffix('.tmp');temporary.write_text(json.dumps(value,indent=2)+'\n');temporary.replace(path)


def prepare(protocol_path,output,cache):
    protocol=json.loads(protocol_path.read_text())
    for p,h in [(ROOT/protocol['direction'],protocol['direction_sha256']),
                (ROOT/protocol['smoke'],protocol['smoke_sha256']),
                (ROOT/protocol['base_protocol'],protocol['base_protocol_sha256']),
                (ROOT/protocol['baseline_artifact']/'report.json',protocol['baseline_report_sha256']),
                (ROOT/protocol['short_control']/'report.json',protocol['short_control_sha256']),
                (ROOT/protocol['architecture']['implementation'],protocol['architecture']['implementation_sha256'])]:
        if sha256(p)!=h:raise ValueError(f'Frozen input changed: {p}')
    verify_files(ROOT,protocol['runner_code_hashes'])
    if (output/'prepared.json').exists():
        prepared=json.loads((output/'prepared.json').read_text())
        if prepared['protocol_sha256']!=sha256(protocol_path) or prepared['cache']!=str(cache):raise ValueError('Prepared run differs')
        verify_files(output,prepared['artifact_hashes'])
        cached=json.loads((cache/'report.json').read_text());verify_files(cache,cached['artifact_hashes'])
        if sha256(cache/'report.json')!=prepared['cache_sha256']:raise ValueError('Cache manifest changed')
        return protocol,prepared
    if output.exists():raise ValueError('Incomplete preparation: use new output')
    prepare_cache(ROOT/protocol['sequence_source'],protocol['sequence_report_sha256'],cache,protocol['seeds'])
    base=json.loads((ROOT/protocol['base_protocol']).read_text())
    groups,_=load_development(ROOT/base['source'],base['source_sha256']);table=pd.concat(groups.values(),ignore_index=True);del groups
    baseline=json.loads((ROOT/protocol['baseline_artifact']/'report.json').read_text())
    for reference in [protocol['baseline_artifact'],protocol['short_control']]:
        root=ROOT/reference;r=json.loads((root/'report.json').read_text());verify_files(root,r['artifact_hashes'])
    keys=pd.read_parquet(cache/'keys.parquet');values=np.load(cache/'values.npy',mmap_mode='r')
    if len(keys)!=len(table):raise ValueError('Full population size changed')
    align_indices(keys,table)
    output.mkdir(parents=True);folds=[]
    for year in protocol['evaluation_years']:
        split,audit=annual_fold(table,year);old=next(f for f in baseline['folds'] if f['year']==year)
        if audit!=old['audit']:raise ValueError('Annual population changed')
        record={'year':year,'status':old['status'],'audit':audit}
        if old['status']!='complete':record['reason']=old['reason'];folds.append(record);continue
        directory=output/str(year);directory.mkdir()
        for role,g in split.items():
            np.save(directory/f'{role}.npy',align_indices(keys,g))
            if role=='train':np.save(directory/'target.npy',g.target.to_numpy(dtype=np.int8))
            else:g[METADATA].to_parquet(directory/f'{role}-metadata.parquet',index=False)
        scaler=fit_scaler(values,np.load(directory/'train.npy'));write_json(directory/'scaler.json',scaler)
        # References must use identical evaluation keys and labels; no scoring here.
        evaluation=split['evaluation']
        for reference in [protocol['baseline_artifact'],protocol['short_control']]:
            oldp=pd.read_parquet(ROOT/reference/str(year)/'predictions.parquet')
            pd.testing.assert_frame_equal(evaluation[['harp','forecast_time','target']].reset_index(drop=True),oldp[['harp','forecast_time','target']].reset_index(drop=True))
        record['input_hashes']={p.name:sha256(p) for p in directory.iterdir() if p.is_file()}
        folds.append(record);print(f'Prepared {year}: {len(split["train"])} training windows',flush=True)
    prepared={'protocol_sha256':sha256(protocol_path),'cache':str(cache),'cache_sha256':sha256(cache/'report.json'),'folds':folds,
        'artifact_hashes':{str(p.relative_to(output)):sha256(p) for p in sorted(output.rglob('*')) if p.is_file()}}
    write_json(output/'prepared.json',prepared);return protocol,prepared


def evaluate_fold(protocol, directory, year):
    calibration=pd.read_parquet(directory/'calibration-metadata.parquet');calibrators={};thresholds={}
    for arm in protocol['arms']:
        scores=[]
        for seed in protocol['seeds']:
            name=f'{arm}_seed{seed}';p=np.load(directory/name/'calibration.npy');scores.append(p)
            calibrators[name]=SigmoidCalibration().fit(p,calibration.target)
            thresholds[name]=recall_threshold(calibration.target,calibrators[name].transform(p),.95)
        p=np.mean(scores,axis=0);calibrators[arm]=SigmoidCalibration().fit(p,calibration.target)
        thresholds[arm]=recall_threshold(calibration.target,calibrators[arm].transform(p),.95)
    reference=ROOT/protocol['baseline_artifact']/str(year);short=ROOT/protocol['short_control']/str(year)
    thresholds['baseline']=json.loads((reference/'thresholds.json').read_text())['ensemble']
    thresholds['short_training']=json.loads((short/'thresholds.json').read_text())['shared_train_one_year']
    write_json(directory/'thresholds.json',thresholds)
    write_json(directory/'calibrators.json',{k:{'slope':v.slope,'intercept':v.intercept} for k,v in calibrators.items()})
    # Evaluation targets are used for metrics only after thresholds are persisted.
    prediction=pd.read_parquet(directory/'evaluation-metadata.parquet')
    prediction['baseline']=pd.read_parquet(reference/'predictions.parquet').ensemble.to_numpy()
    prediction['short_training']=pd.read_parquet(short/'predictions.parquet').shared_train_one_year.to_numpy()
    for arm in protocol['arms']:
        scores=[]
        for seed in protocol['seeds']:
            name=f'{arm}_seed{seed}';p=np.load(directory/name/'evaluation.npy');scores.append(p)
            prediction[name]=calibrators[name].transform(p)
        prediction[arm]=calibrators[arm].transform(np.mean(scores,axis=0))
    rows=[{'year':year,'arm':arm,**evaluable_metrics(enrich(metrics(prediction.target,prediction[arm],t)))} for arm,t in thresholds.items()]
    intervals=[]
    for arm,control in [(a,c) for a in protocol['arms'] for c in ['baseline','short_training']]+[('chronological','shuffled_interior')]:
        intervals.append({'arm':arm,'control':control,'differences':paired_deltas(prediction.target,prediction[arm],prediction[control],prediction.harp,thresholds[arm],thresholds[control],draws=protocol['uncertainty']['draws'],seed=protocol['uncertainty']['seed'])})
    prediction.to_parquet(directory/'predictions.parquet',index=False)
    result={'year':year,'metrics':rows,'paired_intervals':intervals,'artifact_hashes':{str(p.relative_to(directory)):sha256(p) for p in sorted(directory.rglob('*')) if p.is_file() and p.name not in ['finished.json','worker.log']}}
    write_json(directory/'finished.json',result);return result


def execute(protocol_path,output,cache,protocol,prepared):
    if (output/'report.json').exists():raise ValueError('Completed experiment is frozen')
    results=[]
    for fold in prepared['folds']:
        if fold['status']!='complete':continue
        year=fold['year'];directory=output/str(year)
        if (directory/'finished.json').exists():
            result=json.loads((directory/'finished.json').read_text());verify_files(directory,result['artifact_hashes']);results.append(result);continue
        for arm in protocol['arms']:
            for seed in protocol['seeds']:
                dest=directory/f'{arm}_seed{seed}';dest.mkdir(exist_ok=True)
                job={'protocol':str(protocol_path),'protocol_sha256':sha256(protocol_path),'fold':str(directory),'cache':str(cache),'arm':arm,'seed':seed,
                     'input_hashes':{k:v for k,v in fold['input_hashes'].items() if not k.endswith('-metadata.parquet')}}
                path=dest/'job.json'
                if path.exists():
                    if json.loads(path.read_text())!=job:raise ValueError('Job changed')
                else:write_json(path,job)
                if (dest/'result.json').exists():
                    r=json.loads((dest/'result.json').read_text())
                    if r['job_sha256']!=sha256(path):raise ValueError('Completed job changed')
                    verify_files(dest,r['artifact_hashes']);continue
                write_json(output/'progress.json',{'status':'training','year':year,'arm':arm,'seed':seed,'completed_years':[r['year'] for r in results]})
                with (dest/'worker.log').open('a') as log:
                    subprocess.run([sys.executable,str(ROOT/'scripts/temporal_worker.py'),'--job',str(path)],stdout=log,stderr=subprocess.STDOUT,check=True)
        result=evaluate_fold(protocol,directory,year);results.append(result)
        print(f'Completed annual evaluation {year}',flush=True)
    rows=[r for f in results for r in f['metrics']]
    contrasts=[annual_contrast(rows,a,c) for a,c in [('chronological','baseline'),('shuffled_interior','baseline'),('chronological','shuffled_interior'),('chronological','short_training')]]
    pd.DataFrame(rows).to_csv(output/'metrics.csv',index=False)
    report={'protocol':protocol,'protocol_sha256':sha256(protocol_path),'folds':prepared['folds'],'metrics':rows,'contrasts':contrasts,'paired_intervals':[{'year':f['year'],**i} for f in results for i in f['paired_intervals']],
            'model_promoted':False,'reserved_test_accessed':False,'artifact_hashes':{str(p.relative_to(output)):sha256(p) for p in sorted(output.rglob('*')) if p.is_file() and p.name not in ['progress.json','worker.log','run.log']}}
    write_json(output/'report.json',report);write_json(output/'progress.json',{'status':'complete','completed_years':[r['year'] for r in results]})


def run(protocol_path,output,cache,prepare_only=False):
    protocol,prepared=prepare(protocol_path,output,cache)
    if prepare_only:return
    with (output/'.run.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        execute(protocol_path,output,cache,protocol,prepared)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--protocol',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--cache',type=Path,required=True);p.add_argument('--prepare-only',action='store_true')
    a=p.parse_args()
    try:
        run(a.protocol.resolve(),a.output.resolve(),a.cache.resolve(),a.prepare_only)
    except BlockingIOError:
        raise SystemExit('Another runner holds this experiment lock')
    except Exception as error:
        if (a.output/'prepared.json').exists() and not (a.output/'report.json').exists():
            write_json(a.output/'failure.json',{'error':repr(error),'status':'failed'})
        raise
