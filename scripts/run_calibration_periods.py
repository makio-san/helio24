"""Compare temporally separated calibration and threshold selection annually."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import joblib
import numpy as np
import pandas as pd
from helio24.data import ROOT, FEATURE_COLUMNS
from helio24.full_data import sha256
from helio24.v2_training import load_development,METADATA
from helio24.walk_forward import annual_fold,evaluable_metrics
from helio24.calibration_periods import split_calibration
from helio24.calibration import SigmoidCalibration,recall_threshold
from helio24.hard_negatives import paired_deltas
from helio24.modeling import metrics
from helio24.metric_summary import enrich


def run(protocol_path,output):
    if output.exists():raise ValueError('Preserve experiment')
    protocol=json.loads(protocol_path.read_text());origin=ROOT/protocol['baseline_artifact']
    base_path=ROOT/protocol['base_protocol']
    if sha256(base_path)!=protocol['base_protocol_sha256'] or sha256(origin/'report.json')!=protocol['baseline_report_sha256']:
        raise ValueError('Frozen source changed')
    frozen=json.loads((origin/'report.json').read_text());base=json.loads(base_path.read_text())
    for name,digest in frozen['artifact_hashes'].items():
        if sha256(origin/name)!=digest:raise ValueError('Source artifact changed')
    groups,_=load_development(ROOT/base['source'],base['source_sha256'])
    table=pd.concat(groups.values(),ignore_index=True);del groups
    output.mkdir(parents=True);rows=[];folds=[];intervals=[]
    for year in protocol['evaluation_years']:
        groups,audit=annual_fold(table,year);prior=next(f for f in frozen['folds'] if f['year']==year)
        if audit!=prior['audit']:raise ValueError('Population changed')
        fold={'year':year,'status':prior['status']}
        if prior['status']!='complete':
            fold['reason']=prior['reason'];folds.append(fold);continue
        directory=output/str(year);directory.mkdir()
        early,late,half_audit=split_calibration(groups['calibration'],year);fold.update(half_audit)
        artifact=joblib.load(origin/str(year)/'models.joblib')
        original=pd.read_parquet(origin/str(year)/'predictions.parquet')
        pd.testing.assert_frame_equal(original[METADATA].reset_index(drop=True),groups['evaluation'][METADATA].reset_index(drop=True))
        thresholds={'baseline_full_year':artifact['thresholds']['ensemble']}
        calibrators={};unavailable={}
        if late.target.nunique()!=2:
            unavailable.update({arm:'Late half lacks both classes' for arm in protocol['arms'][1:]})
        else:
            late_raw={n:model.predict_proba(late[FEATURE_COLUMNS].to_numpy(dtype=np.float32))[:,1] for n,model in artifact['models'].items()}
            cp=.45*artifact['calibrators']['logistic'].transform(late_raw['logistic'])+.55*artifact['calibrators']['xgboost'].transform(late_raw['xgboost'])
            thresholds['late_threshold_control']=recall_threshold(late.target,cp,protocol['required_recall'])
            if early.target.nunique()!=2:
                unavailable['separated_calibration']='Early half lacks both classes'
            else:
                for n,model in artifact['models'].items():
                    raw=model.predict_proba(early[FEATURE_COLUMNS].to_numpy(dtype=np.float32))[:,1]
                    calibrators[n]=SigmoidCalibration().fit(raw,early.target)
                cp=.45*calibrators['logistic'].transform(late_raw['logistic'])+.55*calibrators['xgboost'].transform(late_raw['xgboost'])
                thresholds['separated_calibration']=recall_threshold(late.target,cp,protocol['required_recall'])
        fold['unavailable']=unavailable
        (directory/'thresholds.json').write_text(json.dumps(thresholds,indent=2)+'\n')
        joblib.dump({'calibrators':calibrators,'thresholds':thresholds,'baseline':str(origin/str(year))},directory/'calibration.joblib')
        prediction=original[METADATA].copy();prediction['baseline_full_year']=original.ensemble
        if 'late_threshold_control' in thresholds:prediction['late_threshold_control']=original.ensemble
        if 'separated_calibration' in thresholds:
            raw={n:model.predict_proba(groups['evaluation'][FEATURE_COLUMNS].to_numpy(dtype=np.float32))[:,1] for n,model in artifact['models'].items()}
            prediction['separated_calibration']=.45*calibrators['logistic'].transform(raw['logistic'])+.55*calibrators['xgboost'].transform(raw['xgboost'])
        local={}
        for arm,t in thresholds.items():
            m=evaluable_metrics(enrich(metrics(prediction.target,prediction[arm],t)))
            rows.append({'year':year,'arm':arm,**m});local[arm]=m
        if 'separated_calibration' in thresholds:
            for control in ['baseline_full_year','late_threshold_control']:
                intervals.append({'year':year,'control':control,'differences':paired_deltas(prediction.target,
                    prediction.separated_calibration,prediction[control],prediction.harp,
                    thresholds['separated_calibration'],thresholds[control],**protocol['bootstrap'])})
            old,new=local['baseline_full_year'],local['separated_calibration']
            fold['passes_gate']=(new['precision'] is not None and new['precision']>old['precision'] and new['recall']>=.95 and
                new['average_precision']>=old['average_precision'] and new['brier']<=old['brier'] and new['log_loss']<=old['log_loss']) if new['positives'] else None
            print(f'{year}: baseline P={old["precision"]} R={old["recall"]} FP={old["fp"]}; separated P={new["precision"]} R={new["recall"]} FP={new["fp"]}',flush=True)
        else:print(f'{year}: unavailable {unavailable}',flush=True)
        prediction.to_parquet(directory/'predictions.parquet',index=False)
        (directory/'fold.json').write_text(json.dumps(fold,indent=2)+'\n');folds.append(fold)
    pd.DataFrame(rows).to_csv(output/'metrics.csv',index=False)
    positive=[f for f in folds if f.get('passes_gate') is not None]
    missing=any('separated_calibration' in f.get('unavailable',{}) for f in folds)
    gate=bool(positive) and not missing and all(f['passes_gate'] for f in positive)
    result={'protocol':protocol,'protocol_sha256':sha256(protocol_path),'metrics':rows,'folds':folds,
        'paired_intervals':intervals,'all_year_gate_passed':gate,'model_promoted':False,'reserved_test_accessed':False,
        'code_hashes':{n:sha256(ROOT/n) for n in ['scripts/run_calibration_periods.py','helio24/calibration_periods.py','helio24/calibration.py','helio24/hard_negatives.py']},
        'artifact_hashes':{str(p.relative_to(output)):sha256(p) for p in sorted(output.rglob('*')) if p.is_file()}}
    (output/'report.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--protocol',type=Path,default=ROOT/'config/calibration-periods-v1.json')
    p.add_argument('--output',type=Path,required=True);a=p.parse_args();run(a.protocol.resolve(),a.output.resolve())
