"""Audit calibration score drift and threshold sensitivity without selecting a model."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import joblib
import numpy as np
import pandas as pd
from helio24.data import ROOT,FEATURE_COLUMNS
from helio24.full_data import sha256
from helio24.v2_training import load_development
from helio24.walk_forward import annual_fold
from helio24.calibration_periods import split_calibration
from helio24.threshold_audit import summarize_scores


def run(output):
    if output.exists():raise ValueError('Preserve audit')
    protocol_path=ROOT/'config/calibration-periods-v1.json';protocol=json.loads(protocol_path.read_text())
    origin=ROOT/protocol['baseline_artifact'];basepath=ROOT/protocol['base_protocol']
    if sha256(origin/'report.json')!=protocol['baseline_report_sha256'] or sha256(basepath)!=protocol['base_protocol_sha256']:
        raise ValueError('Source changed')
    frozen=json.loads((origin/'report.json').read_text());base=json.loads(basepath.read_text())
    for path,digest in frozen['artifact_hashes'].items():
        if sha256(origin/path)!=digest:raise ValueError('Artifact changed')
    groups,_=load_development(ROOT/base['source'],base['source_sha256']);table=pd.concat(groups.values(),ignore_index=True);del groups
    output.mkdir(parents=True);summaries=[];details=[];sources={str((origin/'report.json').relative_to(ROOT)):sha256(origin/'report.json')}
    for fold in frozen['folds']:
        if fold['status']!='complete':continue
        year=fold['year'];groups,audit=annual_fold(table,year)
        if audit!=fold['audit']:raise ValueError('Population changed')
        early,late,_=split_calibration(groups['calibration'],year)
        artifact=joblib.load(origin/str(year)/'models.joblib')
        for period,frame in [('full',groups['calibration']),('early',early),('late',late)]:
            x=frame[FEATURE_COLUMNS].to_numpy(dtype=np.float32)
            probabilities={name:artifact['calibrators'][name].transform(model.predict_proba(x)[:,1])
                           for name,model in artifact['models'].items()}
            p=.45*probabilities['logistic']+.55*probabilities['xgboost']
            summary,influences=summarize_scores(frame,p)
            if period=='full' and not np.isclose(summary['threshold'],artifact['thresholds']['ensemble'],rtol=0,atol=1e-14):
                raise ValueError('Frozen threshold does not reproduce')
            summaries.append({'evaluation_year':year,'calibration_year':year-1,'period':period,**summary})
            details.extend({'evaluation_year':year,'period':period,**row} for row in influences)
            scores=frame[['harp','forecast_time','target']].copy();scores['probability']=p
            scores.to_parquet(output/f'{year}-{period}.parquet',index=False)
        print(f'{year}: three periods audited',flush=True)
    pd.DataFrame(summaries).to_csv(output/'summary.csv',index=False)
    pd.DataFrame(details).to_csv(output/'region_influence.csv',index=False)
    r={'scope':'Calibration-only post-hoc diagnostic with fixed full-year calibrators; no evaluation score access, retraining or threshold deployment',
       'source_hashes':sources,'protocol_sha256':sha256(protocol_path),'reserved_test_accessed':False,
       'summaries':summaries,'code_hashes':{n:sha256(ROOT/n) for n in ['scripts/audit_calibration_scores.py','helio24/threshold_audit.py','helio24/calibration_periods.py']},
       'artifact_hashes':{p.name:sha256(p) for p in sorted(output.iterdir()) if p.is_file()}}
    (output/'report.json').write_text(json.dumps(r,indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    run(p.parse_args().output.resolve())
