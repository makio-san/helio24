"""Synthetic end-to-end worker test, isolated from sklearn's native runtime."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import time
import numpy as np
import pytest
from helio24.full_data import sha256
from helio24.sequence_training import fit_scaler


def test_worker_resumes_final_checkpoint_and_rejects_changed_inputs(tmp_path):
    if importlib.util.find_spec('torch') is None:pytest.skip('Optional torch dependency')
    root=Path(__file__).resolve().parents[1]
    cache=tmp_path/'cache';fold=tmp_path/'fold';jobdir=tmp_path/'job'
    for p in [cache,fold,jobdir]:p.mkdir()
    x=np.random.default_rng(24).normal(size=(24,60,24)).astype('float32');x[0,0,0]=np.nan
    np.save(cache/'values.npy',x);np.save(cache/'order-24.npy',np.tile(np.arange(60,dtype='uint8'),(24,1)))
    for name,value in {'train':np.arange(16),'target':np.tile([0,1],8),'calibration':np.arange(16,20),'evaluation':np.arange(20,24)}.items():np.save(fold/f'{name}.npy',value)
    (fold/'scaler.json').write_text(json.dumps(fit_scaler(x,np.arange(16))))
    protocol=json.loads((root/'config/temporal-sequence-v1.json').read_text());protocol['training']['epochs']=100;protocol['training']['threads']=1
    protocolpath=tmp_path/'protocol.json';protocolpath.write_text(json.dumps(protocol))
    job={'protocol':str(protocolpath),'protocol_sha256':sha256(protocolpath),'fold':str(fold),'cache':str(cache),'seed':24,'arm':'chronological','input_hashes':{p.name:sha256(p) for p in fold.iterdir()}}
    jobpath=jobdir/'job.json';jobpath.write_text(json.dumps(job))
    command=[sys.executable,str(root/'scripts/temporal_worker.py'),'--job',str(jobpath)]
    with (tmp_path/'interrupted.log').open('w') as log:
        process=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT)
        deadline=time.monotonic()+60
        try:
            while not (jobdir/'progress.json').exists() and process.poll() is None and time.monotonic()<deadline:
                time.sleep(.005)
            assert (jobdir/'progress.json').exists()
            assert json.loads((jobdir/'progress.json').read_text())['epoch']<100
        finally:
            if process.poll() is None:process.terminate()
            process.wait(timeout=10)
    result=subprocess.run(command,capture_output=True,text=True,timeout=60)
    assert result.returncode==0,result.stdout+result.stderr
    first=np.load(jobdir/'evaluation.npy').copy();checkpoint_hash=sha256(jobdir/'checkpoint.pt')
    assert len(json.loads((jobdir/'result.json').read_text())['history'])==100
    uninterrupted=tmp_path/'uninterrupted';uninterrupted.mkdir()
    (uninterrupted/'job.json').write_text(jobpath.read_text())
    result=subprocess.run([*command[:-1],str(uninterrupted/'job.json')],capture_output=True,text=True,timeout=60)
    assert result.returncode==0,result.stdout+result.stderr
    np.testing.assert_equal(first,np.load(uninterrupted/'evaluation.npy'))
    (jobdir/'result.json').unlink();(jobdir/'evaluation.npy').unlink()
    result=subprocess.run(command,capture_output=True,text=True,timeout=60)
    assert result.returncode==0,result.stdout+result.stderr
    np.testing.assert_equal(first,np.load(jobdir/'evaluation.npy'))
    assert sha256(jobdir/'checkpoint.pt')==checkpoint_hash
    np.save(fold/'target.npy',np.zeros(16))
    result=subprocess.run(command,capture_output=True,text=True,timeout=60)
    assert result.returncode!=0 and 'Changed file' in result.stderr
