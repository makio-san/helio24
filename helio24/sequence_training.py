"""Torch-free sequence indexing and training-only preprocessing."""
import hashlib
import json
import shutil
from pathlib import Path
import numpy as np
import pandas as pd
from helio24.full_data import sha256


def signed_log(values):
    x=np.asarray(values,dtype=np.float64)
    return np.sign(x)*np.log1p(np.abs(x))


def fit_scaler(values, indices, batch_size=128):
    count=np.zeros(24,dtype=np.int64);total=np.zeros(24);squares=np.zeros(24)
    for start in range(0,len(indices),batch_size):
        x=signed_log(values[indices[start:start+batch_size]])
        finite=np.isfinite(x);x=np.where(finite,x,0.)
        count+=finite.sum(axis=(0,1));total+=x.sum(axis=(0,1));squares+=(x*x).sum(axis=(0,1))
    if (count==0).any():raise ValueError('A training channel has no observations')
    mean=total/count;std=np.sqrt(np.maximum(squares/count-mean**2,0))
    std[std<1e-6]=1
    return {'mean':mean.tolist(),'std':std.tolist(),'count':count.tolist()}


def transform(values, scaler):
    missing=~np.isfinite(values)
    x=signed_log(values);x=np.clip((x-np.array(scaler['mean']))/np.array(scaler['std']),-8,8)
    x=np.where(missing,0,x)
    out=np.concatenate([x,missing.astype(float)],axis=2).astype('float32')
    if not np.isfinite(out).all():raise ValueError('Nonfinite network input')
    return out


def key_permutation(seed, harp, forecast_time):
    clock=pd.Timestamp(forecast_time)
    if clock.tz is None:raise ValueError('Timezone required')
    payload=f'{seed}|{int(harp)}|{clock.tz_convert("UTC").isoformat()}'.encode()
    value=int.from_bytes(hashlib.sha256(payload).digest()[:8],'little')
    return np.r_[0,np.random.default_rng(value).permutation(np.arange(1,59)),59].astype('uint8')


def verify_files(root, hashes):
    for name,expected in hashes.items():
        if sha256(root/name)!=expected:raise ValueError(f'Changed file: {name}')


def prepare_cache(source, expected, output, seeds):
    if sha256(source/'report.json')!=expected:raise ValueError('Sequence manifest changed')
    if (output/'report.json').exists():
        report=json.loads((output/'report.json').read_text())
        if report['source_sha256']!=expected or report['seeds']!=seeds:raise ValueError('Cache identity changed')
        verify_files(output,report['artifact_hashes']);return report
    if output.exists():raise ValueError('Incomplete cache: use a new directory')
    report=json.loads((source/'report.json').read_text())
    if shutil.disk_usage(output.parent).free < report['rows']*60*24*4+1024**3:
        raise RuntimeError('Insufficient disk space for sequence cache')
    output.mkdir(parents=True)
    values=np.lib.format.open_memmap(output/'values.npy',mode='w+',dtype='float32',shape=(report['rows'],60,24))
    keys=[];offset=0
    for shard in report['shards']:
        verify_files(source/'shards',{shard['file']:shard['sha256'],shard['keys']:shard['keys_sha256']})
        frame=pd.read_parquet(source/'shards'/shard['keys'])
        with np.load(source/'shards'/shard['file'],allow_pickle=False) as stored:
            x=stored['values'];mask=stored['missing']
            if x.shape!=(len(frame),60,24) or not np.array_equal(~np.isfinite(x),mask):raise ValueError('Sequence shape or mask changed')
            values[offset:offset+len(frame)]=x
        keys.append(frame);offset+=len(frame)
    values.flush();del values
    keys=pd.concat(keys,ignore_index=True)
    if offset!=report['rows'] or keys.duplicated(['harp','forecast_time']).any():raise ValueError('Cache population changed')
    if (keys.forecast_time>=pd.Timestamp('2024-01-01',tz='UTC')).any():raise ValueError('Reserved keys')
    keys.to_parquet(output/'keys.parquet',index=False)
    for seed in seeds:
        orders=np.lib.format.open_memmap(output/f'order-{seed}.npy',mode='w+',dtype='uint8',shape=(len(keys),60))
        for i,row in enumerate(keys.itertuples()):orders[i]=key_permutation(seed,row.harp,row.forecast_time)
        orders.flush();del orders
    result={'source_sha256':expected,'rows':len(keys),'seeds':seeds,'artifact_hashes':{p.name:sha256(p) for p in sorted(output.iterdir()) if p.is_file()}}
    (output/'report.json').write_text(json.dumps(result,indent=2)+'\n');return result


def align_indices(keys, windows):
    index=pd.MultiIndex.from_frame(keys[['harp','forecast_time']])
    wanted=pd.MultiIndex.from_frame(windows[['harp','forecast_time']])
    if index.has_duplicates or wanted.has_duplicates:raise ValueError('Duplicate forecast keys')
    result=index.get_indexer(wanted)
    if (result<0).any():raise ValueError('Missing forecast key')
    return result
