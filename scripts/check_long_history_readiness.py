"""Check causal histories on existing raw region snapshots without fitting models."""
import json
from pathlib import Path
import shutil
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
import pandas as pd
from helio24.data import ROOT
from helio24.full_data import sha256
from helio24.long_history import history_features,HISTORY_COLUMNS
from helio24.v2_contract import utc_to_tai,V2_MEASUREMENTS


def run():
    out=ROOT/'artifacts/long_history_readiness_20261028'
    out.mkdir(parents=True,exist_ok=False)
    raw=ROOT/'data/region_audit_20261027_r2'
    report=json.loads((raw/'report.json').read_text())
    audit=ROOT/'artifacts/missed_regions_20261027_r2'
    frozen=json.loads((audit/'report.json').read_text())
    roles={'validation':(pd.Timestamp('2023-01-01',tz='UTC'),pd.Timestamp('2024-01-01',tz='UTC'))}
    rows=[];sources={}
    for item in report['records']:
        h=item['harp'];path=raw/item['file']
        if sha256(path)!=item['artifact_sha256']:raise ValueError('Raw snapshot changed')
        sources[str(path.relative_to(ROOT))]=sha256(path)
        path2=audit/f'harp_{h}_windows.csv'
        if sha256(path2)!=frozen['artifact_hashes'][path2.name]:raise ValueError('Windows changed')
        sources[str(path2.relative_to(ROOT))]=sha256(path2)
        observations=pd.read_parquet(path)
        windows=pd.read_csv(path2,parse_dates=['forecast_time'])
        result=history_features(observations,windows,roles)
        check=windows.copy();check['target']=1-check.target
        pd.testing.assert_frame_equal(result,history_features(observations,check,roles))
        raw_values=observations[['harp_number','obs_start',*V2_MEASUREMENTS.values()]].drop_duplicates().sort_values('obs_start')
        for hours in [24,48]:
            ids=result.index[result[f'history_{hours}h_available'].eq(1)]
            for i in ids:
                end=utc_to_tai(windows.loc[i,'forecast_time']);start=end-pd.Timedelta(hours=hours)
                a=raw_values[raw_values.obs_start.ge(start)&raw_values.obs_start.lt(end)]
                assert len(a)==hours*5
                mean=a.usflux.mean()
                value=result.loc[i,f'USFLUX__{hours}h_mean']
                if a.usflux.notna().sum()>=hours*5*.8:
                    np.testing.assert_allclose(value,mean,rtol=1e-9,atol=1e-12)
        rows.append({'harp':h,'rows':len(result),'available_24h':int(result.history_24h_available.sum()),
                     'available_48h':int(result.history_48h_available.sum()),'target_invariance':True})
        result.to_parquet(out/f'harp_{h}.parquet',index=False)
    outcome={'scope':'Two-region implementation check only; no model training or score change',
             'regions':rows,'features':len(HISTORY_COLUMNS),'free_bytes':shutil.disk_usage(ROOT).free,
             'required_bytes':5*1024**3,'full_materialization_complete':False,
             'source_hashes':sources,'code_sha256':sha256(Path(__file__)),
             'feature_code_sha256':sha256(ROOT/'helio24/long_history.py')}
    (out/'report.json').write_text(json.dumps(outcome,indent=2)+'\n')
    print(json.dumps(outcome,indent=2))


if __name__=='__main__':run()
