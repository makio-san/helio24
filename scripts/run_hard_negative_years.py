"""Evaluate frozen hard-negative and weight-matched controls across annual folds."""
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
from helio24.walk_forward import annual_fold,evaluable_metrics
from helio24.calibration import SigmoidCalibration,recall_threshold
from helio24.modeling import metrics
from helio24.metric_summary import enrich
from helio24.hard_negatives import mining_split,training_weights,paired_deltas


def run(protocol_path,output):
    if output.exists():raise ValueError('Preserve existing experiment')
    protocol=json.loads(protocol_path.read_text());base_path=ROOT/protocol['base_protocol']
    if sha256(base_path)!=protocol['base_protocol_sha256']:raise ValueError('Base protocol changed')
    if sha256(ROOT/protocol['evidence'])!=protocol['evidence_sha256']:raise ValueError('Audit changed')
    base=json.loads(base_path.read_text());origin=ROOT/protocol['baseline_artifact']
    if sha256(origin/'report.json')!=protocol['baseline_report_sha256']:raise ValueError('Baseline changed')
    frozen=json.loads((origin/'report.json').read_text())
    for name,digest in frozen['artifact_hashes'].items():
        if sha256(origin/name)!=digest:raise ValueError('Baseline artifact changed')
    groups,_=load_development(ROOT/base['source'],base['source_sha256'])
    table=pd.concat(groups.values(),ignore_index=True);del groups
    output.mkdir(parents=True);rows=[];folds=[];intervals=[]
    for year in protocol['evaluation_years']:
        groups,audit=annual_fold(table,year)
        oldfold=next(f for f in frozen['folds'] if f['year']==year)
        if audit!=oldfold['audit']:raise ValueError('Annual populations changed')
        fold={'year':year,'audit':audit,'status':oldfold['status']}
        if oldfold['status']!='complete':
            fold['reason']=oldfold['reason'];folds.append(fold);continue
        directory=output/str(year);directory.mkdir()
        teacher_data,mining=mining_split(groups['train'],year)
        if teacher_data.target.nunique()!=2 or mining.empty:
            fold.update(status='unavailable',reason='Insufficient teacher classes or mining negatives')
            folds.append(fold);continue
        teacher=candidate_models(base)['xgboost']
        teacher.fit(teacher_data[FEATURE_COLUMNS].to_numpy(dtype=np.float32),teacher_data.target)
        score=teacher.predict_proba(mining[FEATURE_COLUMNS].to_numpy(dtype=np.float32))[:,1]
        weights,uniform,chosen=training_weights(groups['train'],mining,score,
            protocol['teacher']['fraction'],protocol['student']['hard_negative_weight'])
        chosen[['harp','forecast_time','target','score']].to_parquet(directory/'mined_negatives.parquet',index=False)
        fold.update(teacher_rows=len(teacher_data),eligible_negatives=len(mining),hard_negatives=len(chosen),
                    targeted_weight_sum=float(weights.sum()),uniform_weight_sum=float(uniform.sum()))
        del teacher,teacher_data,mining,chosen
        X={role:g[FEATURE_COLUMNS].to_numpy(dtype=np.float32) for role,g in groups.items()}
        y={role:g.target.to_numpy(dtype=np.int8) for role,g in groups.items()}
        previous=joblib.load(origin/str(year)/'models.joblib')
        logistic=previous['models']['logistic'];logcal=previous['calibrators']['logistic']
        lp=logcal.transform(logistic.predict_proba(X['calibration'])[:,1])
        thresholds={'baseline_unweighted':previous['thresholds']['ensemble']};students={}
        for arm,w in [('hard_negative_weighted',weights),('uniform_negative_matched_weight',uniform)]:
            student=candidate_models(base)['xgboost']
            student.fit(X['train'],y['train'],xgbclassifier__sample_weight=w)
            raw=student.predict_proba(X['calibration'])[:,1]
            cal=SigmoidCalibration().fit(raw,y['calibration'])
            cp=.45*lp+.55*cal.transform(raw)
            thresholds[arm]=recall_threshold(y['calibration'],cp,protocol['required_recall'])
            students[arm]=(student,cal)
        (directory/'thresholds.json').write_text(json.dumps(thresholds,indent=2)+'\n')
        joblib.dump({'students':students,'thresholds':thresholds,'baseline':str(origin/str(year))},directory/'models.joblib')
        original=pd.read_parquet(origin/str(year)/'predictions.parquet')
        pd.testing.assert_frame_equal(original[METADATA].reset_index(drop=True),groups['evaluation'][METADATA].reset_index(drop=True))
        prediction=original[METADATA].copy();prediction['baseline_unweighted']=original.ensemble
        lp=logcal.transform(logistic.predict_proba(X['evaluation'])[:,1])
        for arm,(student,cal) in students.items():prediction[arm]=.45*lp+.55*cal.transform(student.predict_proba(X['evaluation'])[:,1])
        year_rows={}
        for arm in protocol['arms']:
            m=evaluable_metrics(enrich(metrics(y['evaluation'],prediction[arm],thresholds[arm])))
            year_rows[arm]=m;rows.append({'year':year,'arm':arm,**m})
        for control in ['baseline_unweighted','uniform_negative_matched_weight']:
            delta=paired_deltas(y['evaluation'],prediction.hard_negative_weighted,prediction[control],
                prediction.harp,thresholds['hard_negative_weighted'],thresholds[control],
                draws=protocol['uncertainty']['draws'],seed=protocol['uncertainty']['seed'])
            intervals.append({'year':year,'control':control,'differences':delta})
        old,new=year_rows['baseline_unweighted'],year_rows['hard_negative_weighted']
        fold['passes_gate']=(new['precision'] is not None and new['precision']>old['precision'] and
            new['recall'] is not None and new['recall']>=.95 and new['average_precision']>=old['average_precision'] and
            new['brier']<=old['brier'] and new['log_loss']<=old['log_loss']) if new['positives'] else None
        fold['beats_uniform_precision']=(new['precision']>year_rows['uniform_negative_matched_weight']['precision']) if new['precision'] is not None else False
        prediction.to_parquet(directory/'predictions.parquet',index=False)
        (directory/'fold.json').write_text(json.dumps(fold,indent=2)+'\n');folds.append(fold)
        print(f'{year}: baseline P={old["precision"]} R={old["recall"]} FP={old["fp"]}; hard P={new["precision"]} R={new["recall"]} FP={new["fp"]}',flush=True)
        del X,y,groups,previous,students,student,logistic,original,prediction
        gc.collect()
    pd.DataFrame(rows).to_csv(output/'metrics.csv',index=False)
    positive=[f for f in folds if f.get('passes_gate') is not None]
    gate=bool(positive) and all(f['passes_gate'] and f['beats_uniform_precision'] for f in positive) and not any(f['status']=='unavailable' for f in folds)
    result={'protocol':protocol,'protocol_sha256':sha256(protocol_path),'folds':folds,'metrics':rows,
        'paired_intervals':intervals,'all_year_gate_passed':gate,'model_promoted':False,'reserved_test_accessed':False,
        'code_hashes':{n:sha256(ROOT/n) for n in ['scripts/run_hard_negative_years.py','helio24/hard_negatives.py','helio24/walk_forward.py','helio24/v2_training.py','helio24/calibration.py']},
        'artifact_hashes':{str(p.relative_to(output)):sha256(p) for p in sorted(output.rglob('*')) if p.is_file()}}
    (output/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(output/'report.json',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--protocol',type=Path,default=ROOT/'config/hard-negative-v2.json')
    p.add_argument('--output',type=Path,required=True);a=p.parse_args();run(a.protocol.resolve(),a.output.resolve())
