"""Fresh-process torch fitting/inference; never reads evaluation targets."""
import argparse
import json
import os
from pathlib import Path
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
import torch
from helio24.temporal_model import TemporalClassifier
from helio24.sequence_training import transform,verify_files
from helio24.full_data import sha256


def run(job_path):
    job=json.loads(job_path.read_text());directory=job_path.parent
    protocol_path=Path(job['protocol']);fold=Path(job['fold']);cache=Path(job['cache'])
    if sha256(protocol_path)!=job['protocol_sha256']:raise ValueError('Protocol changed')
    protocol=json.loads(protocol_path.read_text());settings=protocol['training']
    verify_files(Path(__file__).resolve().parents[1],protocol.get('runner_code_hashes',{}))
    if job['arm'] not in protocol['arms'] or job['seed'] not in protocol['seeds']:
        raise ValueError('Unknown arm or seed')
    verify_files(fold,job['input_hashes'])
    seed=job['seed'];torch.set_num_threads(settings['threads']);torch.manual_seed(seed);np.random.seed(seed)
    torch.use_deterministic_algorithms(True)
    if any(n in sys.modules for n in ['sklearn','xgboost']):raise RuntimeError('Worker must isolate neural runtime')
    values=np.load(cache/'values.npy',mmap_mode='r');orders=np.load(cache/f'order-{seed}.npy',mmap_mode='r')
    scaler=json.loads((fold/'scaler.json').read_text())
    train=np.load(fold/'train.npy');y=np.load(fold/'target.npy')
    if len(train)!=len(y) or set(np.unique(y))!={0,1}:raise ValueError('Training needs both classes')
    def batch(indices):
        x=transform(values[indices],scaler)
        if job['arm']=='shuffled_interior':x=x[np.arange(len(x))[:,None],orders[indices]]
        return torch.from_numpy(x)
    model=TemporalClassifier();optimizer=torch.optim.AdamW(model.parameters(),lr=settings['learning_rate'],weight_decay=settings['weight_decay'],betas=tuple(settings['betas']),eps=settings['eps'])
    loss_fn=torch.nn.BCEWithLogitsLoss(pos_weight=torch.tensor(float((y==0).sum()/(y==1).sum())))
    rng=np.random.default_rng(seed);first=0;history=[];checkpoint=directory/'checkpoint.pt'
    if checkpoint.exists():
        # Trusted local state only, produced by this job; never load downloaded checkpoints.
        state=torch.load(checkpoint,map_location='cpu',weights_only=False)
        if state['job_sha256']!=sha256(job_path):raise ValueError('Checkpoint belongs to another job')
        model.load_state_dict(state['model']);optimizer.load_state_dict(state['optimizer']);torch.set_rng_state(state['torch_rng']);rng.bit_generator.state=state['numpy_rng'];first=state['epoch'];history=state['history']
    size=settings['batch_size']
    for epoch in range(first,settings['epochs']):
        model.train();order=rng.permutation(len(train));total=0.;start=time.perf_counter()
        for offset in range(0,len(order),size):
            take=order[offset:offset+size];optimizer.zero_grad(set_to_none=True)
            loss=loss_fn(model(batch(train[take])),torch.tensor(y[take],dtype=torch.float32))
            if not torch.isfinite(loss):raise ValueError('Nonfinite training loss')
            loss.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),settings['gradient_clip_norm'],error_if_nonfinite=True);optimizer.step()
            if not all(torch.isfinite(p).all() for p in model.parameters()):raise ValueError('Nonfinite parameters')
            total+=loss.item()*len(take)
        history.append({'epoch':epoch+1,'training_loss':total/len(train),'seconds':time.perf_counter()-start})
        state={'job_sha256':sha256(job_path),'epoch':epoch+1,'model':model.state_dict(),'optimizer':optimizer.state_dict(),'torch_rng':torch.get_rng_state(),'numpy_rng':rng.bit_generator.state,'history':history}
        torch.save(state,directory/'checkpoint.tmp');os.replace(directory/'checkpoint.tmp',checkpoint)
        (directory/'progress.json').write_text(json.dumps(history[-1],indent=2)+'\n')
        print(json.dumps({'arm':job['arm'],'seed':seed,**history[-1]}),flush=True)
    model.eval()
    with torch.no_grad():
        for role in ['calibration','evaluation']:
            indices=np.load(fold/f'{role}.npy');pred=[]
            for start in range(0,len(indices),size):pred.append(torch.sigmoid(model(batch(indices[start:start+size]))).numpy())
            p=np.concatenate(pred)
            if not np.isfinite(p).all():raise ValueError('Nonfinite prediction')
            np.save(directory/f'{role}.npy',p)
    result={'job_sha256':sha256(job_path),'epochs':settings['epochs'],'history':history,'torch_version':torch.__version__,'artifact_hashes':{name:sha256(directory/name) for name in ['checkpoint.pt','calibration.npy','evaluation.npy']}}
    (directory/'result.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--job',type=Path,required=True);run(p.parse_args().job.resolve())
