"""Resume one existing frozen job while unrelated historical inputs are offline.

This does not replace annual preparation or evaluation. The original coordinator
must verify the whole run and evaluate it after all inputs become available.
"""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from helio24.storage_preflight import inspect_storage


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def verify(path, expected):
    available = inspect_storage([path])
    if not available['available']:
        raise ValueError(f'Input unavailable: {path}')
    if sha256(path) != expected:
        raise ValueError(f'Frozen input changed: {path}')


def read_json(path):
    if not inspect_storage([path])['available']:
        raise ValueError(f'Input unavailable: {path}')
    return json.loads(Path(path).read_text())


def validate_job(root, output, job_path):
    """Validate only this prescribed fit; do not read evaluation labels."""
    job = read_json(job_path)
    prepared = read_json(output/'prepared.json')
    protocol_path = Path(job['protocol'])
    verify(protocol_path, prepared['protocol_sha256'])
    protocol = read_json(protocol_path)
    fold_path, cache = Path(job['fold']), Path(job['cache'])
    if str(cache) != prepared['cache'] or job_path.parent.parent != fold_path:
        raise ValueError('Job paths differ from prepared run')
    if fold_path.parent != output or (fold_path/'finished.json').exists():
        raise ValueError('Expected an unfinished fold in this run')
    fold = next((f for f in prepared['folds'] if str(f['year']) == fold_path.name and f['status'] == 'complete'), None)
    if fold is None or job['arm'] not in protocol['arms'] or job['seed'] not in protocol['seeds']:
        raise ValueError('Job is not prescribed by the frozen protocol')
    if job_path != fold_path/f"{job['arm']}_seed{job['seed']}"/'job.json':
        raise ValueError('Unexpected job location')
    expected = {'protocol': str(protocol_path), 'protocol_sha256': prepared['protocol_sha256'],
                'fold': str(fold_path), 'cache': str(cache), 'arm': job['arm'], 'seed': job['seed'],
                'input_hashes': {k: v for k, v in fold['input_hashes'].items() if not k.endswith('-metadata.parquet')}}
    if job != expected:
        raise ValueError('Job differs from the frozen prepared inputs')
    for name, expected_hash in protocol['runner_code_hashes'].items():
        verify(root/name, expected_hash)
    for key in ['direction', 'base_protocol', 'smoke']:
        verify(root/protocol[key], protocol[key+'_sha256'])
    verify(cache/'report.json', prepared['cache_sha256'])
    cached = read_json(cache/'report.json')
    for name, expected_hash in cached['artifact_hashes'].items():
        verify(cache/name, expected_hash)
    for name, expected_hash in job['input_hashes'].items():
        verify(fold_path/name, expected_hash)
    result_path = job_path.parent/'result.json'
    if result_path.exists():
        result = read_json(result_path)
        if result['job_sha256'] != sha256(job_path) or result['epochs'] != protocol['training']['epochs']:
            raise ValueError('Completed result differs from the job')
        if set(result['artifact_hashes']) != {'checkpoint.pt', 'calibration.npy', 'evaluation.npy'}:
            raise ValueError('Completed result lacks required artifacts')
        for name, expected_hash in result['artifact_hashes'].items():
            verify(job_path.parent/name, expected_hash)
        return True
    for name in ['checkpoint.pt', 'worker.log']:
        path = job_path.parent/name
        if path.exists() and not inspect_storage([path])['available']:
            raise ValueError(f'Resume state unavailable: {path}')
    return False


def ensure_no_worker(output):
    import psutil
    for process in psutil.process_iter(['cmdline', 'status']):
        command = process.info['cmdline'] or []
        if process.info['status'] == psutil.STATUS_ZOMBIE:
            continue
        if any(Path(part).name == 'temporal_worker.py' for part in command) and '--job' in command:
            position = command.index('--job')+1
            if position < len(command) and Path(command[position]).resolve().is_relative_to(output):
                raise RuntimeError('An existing worker belongs to this experiment')


def run(root, output, job_path, status_path):
    def status(state, **extra):
        record = {'state': state, 'scope': 'single_prescribed_fit', 'pid': os.getpid(),
                  'job': str(job_path), 'output': str(output), 'annual_evaluation_complete': False, **extra}
        temporary = status_path.with_suffix('.tmp')
        temporary.write_text(json.dumps(record, indent=2)+'\n')
        temporary.replace(status_path)

    with (output/'.run.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            ensure_no_worker(output)
            status('verifying')
            if validate_job(root, output, job_path):
                status('already_complete')
                return
            with (job_path.parent/'worker.log').open('a') as log:
                worker = subprocess.Popen([sys.executable, str(root/'scripts/temporal_worker.py'), '--job', str(job_path)],
                                          stdout=log, stderr=subprocess.STDOUT)
                try:
                    status('training', worker_pid=worker.pid)
                    code = worker.wait()
                except BaseException:
                    if worker.poll() is None:
                        worker.terminate()
                        worker.wait()
                    raise
                if code:
                    raise RuntimeError(f'Frozen worker exited with code {code}')
            if not validate_job(root, output, job_path):
                raise ValueError('Worker exited without a verified result')
            status('fit_complete')
        except BaseException as error:
            status('failed', error=repr(error))
            raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--job', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--status', type=Path, required=True)
    args = parser.parse_args()
    run(Path(__file__).resolve().parents[1], args.output.resolve(), args.job.resolve(), args.status.resolve())
