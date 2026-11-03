import fcntl
import importlib.util
import json
from pathlib import Path

import pytest


spec = importlib.util.spec_from_file_location('resume_job', Path(__file__).resolve().parents[1]/'scripts/resume_temporal_job.py')
resume = importlib.util.module_from_spec(spec)
spec.loader.exec_module(resume)


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


@pytest.fixture
def job(tmp_path):
    root = tmp_path
    output, cache = root/'run', root/'cache'
    fold = output/'2018'
    job_path = fold/'chronological_seed24/job.json'
    protocol_path = root/'config/protocol.json'
    code = root/'scripts/temporal_worker.py'
    write(code, {})
    write(cache/'values.npy', [1])
    write(cache/'report.json', {'artifact_hashes': {'values.npy': resume.sha256(cache/'values.npy')}})
    protocol = {'arms': ['chronological'], 'seeds': [24], 'training': {'epochs': 10},
                'runner_code_hashes': {'scripts/temporal_worker.py': resume.sha256(code)}}
    for key in ['direction', 'base_protocol', 'smoke']:
        name = f'config/{key}.json'
        write(root/name, {})
        protocol[key] = name
        protocol[key+'_sha256'] = resume.sha256(root/name)
    write(protocol_path, protocol)
    write(fold/'train.npy', [1])
    input_hashes = {'train.npy': resume.sha256(fold/'train.npy')}
    prepared = {'protocol_sha256': resume.sha256(protocol_path), 'cache': str(cache),
                'cache_sha256': resume.sha256(cache/'report.json'),
                'folds': [{'year': 2018, 'status': 'complete', 'input_hashes': input_hashes}]}
    write(output/'prepared.json', prepared)
    write(job_path, {'protocol': str(protocol_path), 'protocol_sha256': prepared['protocol_sha256'],
                     'fold': str(fold), 'cache': str(cache), 'arm': 'chronological', 'seed': 24,
                     'input_hashes': input_hashes})
    return root, output, job_path


def test_prescribed_job_can_run_without_unrelated_historical_reports(job):
    assert resume.validate_job(*job) is False


@pytest.mark.parametrize('target', ['cache/values.npy', 'run/2018/train.npy', 'scripts/temporal_worker.py'])
def test_changed_cache_fold_or_source_is_rejected(job, target):
    root, _, _ = job
    (root/target).write_text('modified')
    with pytest.raises(ValueError, match='Frozen input changed'):
        resume.validate_job(*job)


def test_job_cannot_replace_frozen_input_hashes(job):
    root, _, job_path = job
    (root/'run/2018/train.npy').write_text('modified')
    record = json.loads(job_path.read_text())
    record['input_hashes']['train.npy'] = resume.sha256(root/'run/2018/train.npy')
    write(job_path, record)
    with pytest.raises(ValueError, match='differs from the frozen prepared inputs'):
        resume.validate_job(*job)


def test_existing_runner_lock_prevents_second_worker(job):
    root, output, job_path = job
    with (output/'.run.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(BlockingIOError):
            resume.run(root, output, job_path, root/'status.json')
    assert not (root/'status.json').exists()


def test_finished_result_is_verified_without_rerunning(job):
    root, output, path = job
    for name in ['checkpoint.pt', 'calibration.npy', 'evaluation.npy']:
        write(path.parent/name, {})
    result = {'job_sha256': resume.sha256(path), 'epochs': 10,
              'artifact_hashes': {name: resume.sha256(path.parent/name) for name in ['checkpoint.pt', 'calibration.npy', 'evaluation.npy']}}
    write(path.parent/'result.json', result)
    assert resume.validate_job(*job) is True
    (path.parent/'checkpoint.pt').write_text('changed')
    with pytest.raises(ValueError, match='Frozen input changed'):
        resume.validate_job(*job)


def test_orphan_worker_is_rejected_even_without_runner_lock(job, monkeypatch):
    from types import SimpleNamespace
    import psutil
    root, output, path = job
    worker = SimpleNamespace(info={'cmdline': ['python', '/local/temporal_worker.py', '--job', str(path)], 'status': psutil.STATUS_RUNNING})
    monkeypatch.setattr(psutil, 'process_iter', lambda *_: [worker])
    with pytest.raises(RuntimeError, match='existing worker'):
        resume.run(root, output, path, root/'status.json')
    assert json.loads((root/'status.json').read_text())['state'] == 'failed'
