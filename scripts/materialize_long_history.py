"""Add causal 24/48-hour history to the unchanged frozen development population."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import shutil
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pandas as pd
from helio24.data import ROOT
from helio24.full_data import sha256
from helio24.long_history import history_features,HISTORY_COLUMNS
from helio24.v2_archive import stream_verified_archive_with_retries
from helio24.v2_contract import V2_MEASUREMENTS,utc_to_tai


def run(output, workers=1):
    required_bytes = (5 if workers == 1 else 8)*1024**3
    if shutil.disk_usage(output.parent).free < required_bytes:
        raise RuntimeError(f"Need at least {required_bytes//1024**3} GiB free for archive verification and history shards")
    base=ROOT/'artifacts/v2_development_features_20261025_r2'
    expected='62a64b3d94b9f7ec1624e5596fc86e636922a0e696968259b55ff0c8739c5f82'
    if sha256(base/'report.json')!=expected:raise ValueError('Base report changed')
    report=json.loads((base/'report.json').read_text())
    frames=[]
    for item in report['shards']:
        path=base/'shards'/item['file']
        if sha256(path)!=item['sha256']:raise ValueError('Base shard changed')
        frames.append(pd.read_parquet(path,columns=['harp','forecast_time','role']))
    keys=pd.concat(frames,ignore_index=True)
    if keys.duplicated(['harp','forecast_time']).any():raise ValueError('Duplicate baseline keys')
    if set(keys.role)!={'train','calibration','validation'}:raise ValueError('Reserved role')
    groups={int(h):g.reset_index(drop=True) for h,g in keys.groupby('harp')}
    protocol_path=ROOT/'config/experiment5-v7.json'
    protocol=json.loads(protocol_path.read_text())
    roles={k:tuple(map(pd.Timestamp,v)) for k,v in protocol['roles'].items() if k!='test'}
    manifest_path=ROOT/'config/swan_sf_v2_sources.verified.json'
    manifest=json.loads(manifest_path.read_text())
    (output/'shards').mkdir(parents=True,exist_ok=False)
    def scan(item):
        def member(path,name,size):
            raw=pd.read_parquet(path,columns=['harp_number','obs_start',*V2_MEASUREMENTS.values()],
                filters=[('obs_start','<',utc_to_tai(pd.Timestamp('2024-01-01T00:00:00Z')))])
            raw=raw.drop_duplicates();parts=[]
            for harp,g in raw.groupby('harp_number'):
                if int(harp) in groups:parts.append(history_features(g,groups[int(harp)],roles))
            if not parts:return {'member':name,'rows':0}
            frame=pd.concat(parts,ignore_index=True)
            frame[HISTORY_COLUMNS]=frame[HISTORY_COLUMNS].astype('float32')
            dest=output/'shards'/f"partition-{item['partition']}-{hashlib.sha256(name.encode()).hexdigest()[:12]}.parquet"
            frame.to_parquet(dest,index=False,compression='zstd')
            coverage=frame.merge(keys,on=['harp','forecast_time'],validate='one_to_one')
            print(f"partition {item['partition']}: {len(frame)} history rows saved",flush=True)
            return {'member':name,'rows':len(frame),'file':dest.name,'sha256':sha256(dest),
                    'availability':{role:{f'{h}h':int(g[f'history_{h}h_available'].sum()) for h in [24,48]}
                                    for role,g in coverage.groupby('role')}}
        return stream_verified_archive_with_retries(item,member,temporary_root=ROOT/'data/cache')
    with ThreadPoolExecutor(max_workers=workers) as pool:records=list(pool.map(scan,manifest['archives']))
    shards=[r for p in records for r in p['results'] if r['rows']]
    actual=pd.concat([pd.read_parquet(output/'shards'/r['file'],columns=['harp','forecast_time']) for r in shards])
    if actual.duplicated(['harp','forecast_time']).any():raise ValueError('Duplicate history keys')
    merged=keys.merge(actual,on=['harp','forecast_time'],how='outer',indicator=True,validate='one_to_one')
    if not merged._merge.eq('both').all():raise ValueError('Population changed')
    result={'scope':'Raw pre-2024 observations only; unchanged development forecast keys',
            'rows':len(actual),'features':HISTORY_COLUMNS,'shards':shards,'reserved_test_accessed':False,
            'base_report_sha256':expected,'manifest_sha256':sha256(manifest_path),
            'protocol_sha256':sha256(protocol_path),
            'code_hashes':{n:sha256(ROOT/n) for n in ['helio24/long_history.py','scripts/materialize_long_history.py']},
            'partitions':[{k:v for k,v in p.items() if k!='results'} for p in records]}
    (output/'report.json').write_text(json.dumps(result,indent=2)+'\n')
    print(f"Verified {len(actual)} unchanged forecast keys",flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--workers',type=int,choices=[1,2],default=1)
    args=parser.parse_args();run(args.output.resolve(),args.workers)
