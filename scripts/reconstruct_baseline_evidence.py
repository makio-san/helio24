"""Reconstruct baseline evidence in a new directory; require its frozen report hash.

Loads only trusted local experiment models. Does not modify original artifacts.
"""
from pathlib import Path
import argparse
import sys,json,hashlib
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np,pandas as pd,joblib
from helio24.calibration import cluster_intervals
from helio24.modeling import metrics
from helio24.metric_summary import enrich
from helio24.walk_forward import evaluable_metrics

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
root=args.root.resolve()
source=root/'artifacts/walk_forward_20261028_r1'
output=args.output.resolve();output.mkdir(parents=True,exist_ok=False)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,value):p.write_text(json.dumps(value,indent=2)+'\n')
protocol_path=root/'config/walk-forward-v1.json';protocol=json.loads(protocol_path.read_text())
prepared=json.loads((root/'artifacts/temporal_years_20261101_r1/prepared.json').read_text())
rows=[];folds=[];intervals=[];hashes={}
for year in protocol['evaluation_years']:
    original=next(f for f in prepared['folds'] if f['year']==year)
    fold={'year':year,'audit':original['audit'],'status':original['status']}
    directory=output/str(year);directory.mkdir()
    if original['status']!='complete':
        fold['reason']=original['reason'];write(directory/'split.json',fold)
        hashes[f'{year}/split.json']=sha(directory/'split.json');folds.append(fold);continue
    write(directory/'split.json',fold);hashes[f'{year}/split.json']=sha(directory/'split.json')
    stored=joblib.load(source/str(year)/'models.joblib');thresholds=stored['thresholds']
    write(directory/'thresholds.json',thresholds);hashes[f'{year}/thresholds.json']=sha(directory/'thresholds.json')
    predictions=pd.read_parquet(source/str(year)/'predictions.parquet')
    y=predictions.target.to_numpy(dtype=np.int8)
    for name,t in thresholds.items():
        p=predictions[name].to_numpy()
        rows.append({'year':year,'model':name,**evaluable_metrics(enrich(metrics(y,p,t)))})
        intervals.append({'year':year,'model':name,'intervals':cluster_intervals(y,p,predictions.harp,t,**protocol['bootstrap'])})
    errors=predictions.assign(fp=predictions.ensemble_alarm & predictions.target.eq(0),fn=~predictions.ensemble_alarm & predictions.target.eq(1))
    regions=errors.groupby('harp').agg(rows=('target','size'),positives=('target','sum'),fp=('fp','sum'),fn=('fn','sum'),mean_missing=('missing_fraction','mean')).reset_index()
    regions.sort_values('fp',ascending=False).to_csv(directory/'region_errors.csv',index=False)
    hashes[f'{year}/region_errors.csv']=sha(directory/'region_errors.csv')
    fold['error_summary']={'fp':int(regions.fp.sum()),'fn':int(regions.fn.sum()),'top10_region_fp':int(regions.nlargest(10,'fp').fp.sum()),'zero_positive_region_fp':int(regions.loc[regions.positives.eq(0),'fp'].sum())}
    folds.append(fold)
    for name in ['models.joblib','predictions.parquet']:hashes[f'{year}/{name}']=sha(source/str(year)/name)
    print('Reconstructed',year,flush=True)
pd.DataFrame(rows).to_csv(output/'metrics.csv',index=False);hashes['metrics.csv']=sha(output/'metrics.csv')
report={'protocol':protocol,'protocol_sha256':sha(protocol_path),'folds':folds,'metrics':rows,'conditional_cluster_intervals':intervals,'reserved_test_accessed':False,'code_hashes':{name:sha(root/name) for name in ['scripts/run_walk_forward.py','helio24/walk_forward.py','helio24/v2_training.py','helio24/modeling.py','helio24/calibration.py']},'artifact_hashes':dict(sorted(hashes.items()))}
write(output/'report.json',report)
expected=json.loads((root/'config/temporal-sequence-v2.json').read_text())['baseline_report_sha256']
print('Report bytes', (output/'report.json').stat().st_size,'SHA256',sha(output/'report.json'),'expected',expected,'match',sha(output/'report.json')==expected,flush=True)

if sha(output/'report.json') != expected:
    raise SystemExit('Reconstruction differs from the frozen reference; do not restore it.')
