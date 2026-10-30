"""Compare one- and two-year calibration with identical classifier training."""
import argparse
import gc
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import joblib
import numpy as np
import pandas as pd
from helio24.data import ROOT,FEATURE_COLUMNS
from helio24.full_data import sha256
from helio24.v2_training import load_development,candidate_models,METADATA
from helio24.calibration_windows import calibration_windows
from helio24.calibration import SigmoidCalibration,recall_threshold
from helio24.hard_negatives import paired_deltas
from helio24.walk_forward import evaluable_metrics
from helio24.modeling import metrics
from helio24.metric_summary import enrich


def run(protocol_path,output):
    if output.exists():raise ValueError('Preserve existing run')
    protocol=json.loads(protocol_path.read_text());origin=ROOT/protocol['baseline_artifact'];basepath=ROOT/protocol['base_protocol']
    for p,h in [(origin/'report.json',protocol['baseline_report_sha256']),(basepath,protocol['base_protocol_sha256']),
                (ROOT/protocol['evidence'],protocol['evidence_sha256'])]:
        if sha256(p)!=h:raise ValueError('Source changed')
    frozen=json.loads((origin/'report.json').read_text());base=json.loads(basepath.read_text())
    for p,h in frozen['artifact_hashes'].items():
        if sha256(origin/p)!=h:raise ValueError('Baseline artifact changed')
    original,_=load_development(ROOT/base['source'],base['source_sha256'])
    table=pd.concat(original.values(),ignore_index=True);del original
    output.mkdir(parents=True);rows=[];folds=[];intervals=[]
    for year in protocol['evaluation_years']:
        groups,audit=calibration_windows(table,year);directory=output/str(year);directory.mkdir()
        fold={'year':year,'audit':audit,'unavailable':{}};thresholds={};calibrators={};models=None
        oldfold=next(f for f in frozen['folds'] if f['year']==year)
        evaluation=groups['evaluation'][METADATA].reset_index(drop=True)
        if evaluation.empty:
            fold.update(status='skipped',reason='Empty evaluation');folds.append(fold);continue
        if oldfold['status']=='complete':
            oldp=pd.read_parquet(origin/str(year)/'predictions.parquet')
            merged=evaluation.merge(oldp[['harp','forecast_time','target','ensemble']],on=['harp','forecast_time'],
                how='left',validate='one_to_one',indicator=True,suffixes=('','_old'))
            if not merged._merge.eq('both').all() or not merged.target.eq(merged.target_old).all():raise ValueError('Baseline alignment failed')
            evaluation['original_baseline']=merged.ensemble.to_numpy()
            oldmodel=joblib.load(origin/str(year)/'models.joblib')
            thresholds['original_baseline']=oldmodel['thresholds']['ensemble'];del oldmodel,oldp,merged
        else:fold['unavailable']['original_baseline']=oldfold['reason']
        available=[]
        for period in ['one_year','two_year']:
            arm=f'shared_train_{period}'
            if groups['train'].target.nunique()!=2 or groups[period].target.nunique()!=2:
                fold['unavailable'][arm]='Training or calibration lacks both classes'
            else:available.append(period)
        if available:
            models=candidate_models(base);x=groups['train'][FEATURE_COLUMNS].to_numpy(dtype=np.float32)
            for model in models.values():model.fit(x,groups['train'].target)
            del x
            for period in available:
                arm=f'shared_train_{period}';frame=groups[period];parts=[];calibrators[arm]={}
                x=frame[FEATURE_COLUMNS].to_numpy(dtype=np.float32)
                for name in ['logistic','xgboost']:
                    raw=models[name].predict_proba(x)[:,1]
                    cal=SigmoidCalibration().fit(raw,frame.target);calibrators[arm][name]=cal
                    parts.append(cal.transform(raw))
                thresholds[arm]=recall_threshold(frame.target,.45*parts[0]+.55*parts[1],protocol['required_recall'])
            del x
        # No evaluation predictions for new arms before all thresholds are frozen.
        (directory/'thresholds.json').write_text(json.dumps(thresholds,indent=2)+'\n')
        if models is not None:
            joblib.dump({'models':models,'calibrators':calibrators,'thresholds':thresholds,'features':FEATURE_COLUMNS},directory/'models.joblib')
            raw={n:m.predict_proba(groups['evaluation'][FEATURE_COLUMNS].to_numpy(dtype=np.float32))[:,1] for n,m in models.items()}
            for arm,c in calibrators.items():evaluation[arm]=.45*c['logistic'].transform(raw['logistic'])+.55*c['xgboost'].transform(raw['xgboost'])
        local={}
        for arm,t in thresholds.items():
            m=evaluable_metrics(enrich(metrics(evaluation.target,evaluation[arm],t)))
            rows.append({'year':year,'arm':arm,**m});local[arm]=m
        candidate='shared_train_two_year'
        fold['passes_gate']=None
        if candidate in local:
            for control in ['original_baseline','shared_train_one_year']:
                if control in local:
                    intervals.append({'year':year,'control':control,'differences':paired_deltas(evaluation.target,
                        evaluation[candidate],evaluation[control],evaluation.harp,thresholds[candidate],thresholds[control],**protocol['bootstrap'])})
            if local[candidate]['positives'] and 'original_baseline' in local:
                n=local[candidate]
                fold['passes_gate']=all(c in local and n['precision'] is not None and n['precision']>local[c]['precision'] and
                    n['recall']>=.95 and n['average_precision']>=local[c]['average_precision'] and n['brier']<=local[c]['brier'] and
                    n['log_loss']<=local[c]['log_loss'] for c in ['original_baseline','shared_train_one_year'])
        fold['status']='complete' if local else 'skipped'
        evaluation.to_parquet(directory/'predictions.parquet',index=False)
        (directory/'fold.json').write_text(json.dumps(fold,indent=2)+'\n');folds.append(fold)
        print(year,{a:{k:m[k] for k in ['precision','recall','fp']} for a,m in local.items()},flush=True)
        del groups,evaluation,models,calibrators
        gc.collect()
    pd.DataFrame(rows).to_csv(output/'metrics.csv',index=False)
    required=[f['year'] for f in frozen['folds'] if f['status']=='complete' and any(a['role']=='evaluation' and a['positives']>0 for a in f['audit'])]
    gate=bool(required) and all(next(f for f in folds if f['year']==year).get('passes_gate') is True for year in required)
    result={'protocol':protocol,'protocol_sha256':sha256(protocol_path),'folds':folds,'metrics':rows,'paired_intervals':intervals,
        'all_year_gate_passed':gate,'model_promoted':False,'reserved_test_accessed':False,
        'code_hashes':{p:sha256(ROOT/p) for p in ['scripts/run_calibration_windows.py','helio24/calibration_windows.py','helio24/calibration.py','helio24/hard_negatives.py','helio24/v2_training.py']},
        'artifact_hashes':{str(p.relative_to(output)):sha256(p) for p in sorted(output.rglob('*')) if p.is_file()}}
    (output/'report.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--protocol',type=Path,default=ROOT/'config/calibration-windows-v1.json')
    p.add_argument('--output',type=Path,required=True);a=p.parse_args();run(a.protocol.resolve(),a.output.resolve())
