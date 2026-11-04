"""Run remaining prescribed fits serially, deferring annual evaluation.

The scientific worker and job serialization are unchanged. A single experiment
lock covers the whole queue; the original coordinator evaluates it afterwards.
"""
import argparse
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.resume_temporal_job import ensure_no_worker, read_json, run_locked, verify


def write_json(path, record):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(record, indent=2)+'\n')
    temporary.replace(path)


def prescribed_job(protocol_path, output, cache, protocol_sha256, fold, arm, seed):
    return {'protocol': str(protocol_path), 'protocol_sha256': protocol_sha256,
            'fold': str(output/str(fold['year'])), 'cache': str(cache), 'arm': arm, 'seed': seed,
            'input_hashes': {name: value for name, value in fold['input_hashes'].items()
                             if not name.endswith('-metadata.parquet')}}


def run(root, protocol_path, output, cache, prepared_sha256, recovery):
    with (output/'.run.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        ensure_no_worker(output)
        if (output/'report.json').exists():
            raise ValueError('Completed annual experiment is frozen')
        verify(output/'prepared.json', prepared_sha256)
        prepared = read_json(output/'prepared.json')
        verify(protocol_path, prepared['protocol_sha256'])
        protocol = read_json(protocol_path)
        if str(cache) != prepared['cache']:
            raise ValueError('Cache path differs from prepared run')
        for name, value in protocol['runner_code_hashes'].items():
            verify(root/name, value)
        active_folds = [fold for fold in prepared['folds'] if fold['status'] == 'complete']
        planned = len(active_folds)*len(protocol['arms'])*len(protocol['seeds'])
        if planned > protocol['budget']['maximum_neural_fits']:
            raise ValueError('Prepared jobs exceed frozen fit budget')
        if recovery.exists():
            raise FileExistsError('Use a fresh recovery directory')
        recovery.mkdir(parents=True)
        completed = 0
        evaluated_years = []

        def status(state, **extra):
            write_json(recovery/'status.json', {
                'state': state, 'scope': 'prescribed_fit_queue', 'pid': os.getpid(),
                'checked_utc': datetime.now(timezone.utc).isoformat(),
                'completed_fits': completed, 'planned_fits': planned,
                'evaluated_years': evaluated_years, 'annual_evaluation_complete': False,
                'prepared_sha256': prepared_sha256, **extra})

        try:
            status('verifying_completed_work')
            for fold in active_folds:
                year = fold['year']
                directory = output/str(year)
                finished = directory/'finished.json'
                if finished.exists():
                    record = read_json(finished)
                    for name, value in record['artifact_hashes'].items():
                        verify(directory/name, value)
                    completed += len(protocol['arms'])*len(protocol['seeds'])
                    evaluated_years.append(year)
                    status('verifying_completed_work')
                    continue
                for arm in protocol['arms']:
                    for seed in protocol['seeds']:
                        job = prescribed_job(protocol_path, output, cache, prepared['protocol_sha256'], fold, arm, seed)
                        destination = directory/f'{arm}_seed{seed}'
                        destination.mkdir(exist_ok=True)
                        job_path = destination/'job.json'
                        if job_path.exists():
                            if read_json(job_path) != job:
                                raise ValueError('Existing job differs from frozen plan')
                        else:
                            write_json(job_path, job)
                        identity = {'year': year, 'arm': arm, 'seed': seed}
                        status('processing_job', **identity)
                        if not (destination/'result.json').exists():
                            write_json(output/'progress.json', {'status': 'verifying', **identity,
                                                               'completed_years': evaluated_years})
                        def on_state(record):
                            if record['state'] == 'training':
                                write_json(output/'progress.json', {'status': 'training', **identity,
                                                                   'completed_years': evaluated_years})
                                status('training', **identity, worker_pid=record['worker_pid'])
                        run_locked(root, output, job_path, recovery/'current_job.json', on_state=on_state)
                        completed += 1
                        status('job_complete', **identity)
            write_json(output/'progress.json', {'status': 'awaiting_annual_evaluation',
                                               'completed_years': evaluated_years})
            status('fits_complete_awaiting_annual_evaluation')
        except BaseException as error:
            status('failed', error=repr(error))
            raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--protocol', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--cache', type=Path, required=True)
    parser.add_argument('--prepared-sha256', required=True)
    parser.add_argument('--recovery', type=Path, required=True)
    args = parser.parse_args()
    run(Path(__file__).resolve().parents[1], args.protocol.resolve(), args.output.resolve(),
        args.cache.resolve(), args.prepared_sha256, args.recovery.resolve())
