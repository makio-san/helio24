import fcntl
import json

import pytest

from scripts import resume_temporal_queue as queue
from scripts.resume_temporal_job import sha256


@pytest.fixture
def experiment(tmp_path, monkeypatch):
    root = tmp_path
    output, cache, recovery = root/'run', root/'cache', root/'recovery'
    output.mkdir()
    protocol_path = root/'protocol.json'
    protocol = {'runner_code_hashes': {}, 'arms': ['chronological', 'shuffled_interior'],
                'seeds': [24], 'budget': {'maximum_neural_fits': 4}}
    queue.write_json(protocol_path, protocol)
    folds = [{'year': year, 'status': 'complete', 'input_hashes': {'train.npy': 'hash'}}
             for year in [2018, 2022]]
    prepared = {'protocol_sha256': sha256(protocol_path), 'cache': str(cache), 'folds': folds}
    queue.write_json(output/'prepared.json', prepared)
    for year in [2018, 2022]:
        (output/str(year)).mkdir()
    (output/'2018/evidence').write_text('saved')
    queue.write_json(output/'2018/finished.json', {'artifact_hashes': {'evidence': sha256(output/'2018/evidence')}})
    monkeypatch.setattr(queue, 'ensure_no_worker', lambda *_: None)
    return root, protocol_path, output, cache, sha256(output/'prepared.json'), recovery


def test_queue_preserves_finished_outputs_and_original_job_serialization(experiment, monkeypatch):
    root, protocol_path, output, cache, _, recovery = experiment
    original = (output/'2018/finished.json').read_bytes()
    called = []
    def worker(root, output, job_path, status_path, on_state):
        job = json.loads(job_path.read_text())
        called.append((job['arm'], job['seed']))
        on_state({'state': 'training', 'worker_pid': 123})
        assert json.loads((output/'progress.json').read_text())['status'] == 'training'
        (job_path.parent/'result.json').write_text('saved result')
    monkeypatch.setattr(queue, 'run_locked', worker)
    queue.run(*experiment)
    assert called == [('chronological', 24), ('shuffled_interior', 24)]
    assert (output/'2018/finished.json').read_bytes() == original
    state = json.loads((recovery/'status.json').read_text())
    assert state['completed_fits'] == state['planned_fits'] == 4
    assert state['state'] == 'fits_complete_awaiting_annual_evaluation'
    assert state['annual_evaluation_complete'] is False
    assert json.loads((output/'progress.json').read_text())['status'] == 'awaiting_annual_evaluation'
    # Match the original coordinator's field order and JSON representation.
    expected = {'protocol': str(protocol_path), 'protocol_sha256': sha256(protocol_path),
                'fold': str(output/'2022'), 'cache': str(cache), 'arm': 'chronological', 'seed': 24,
                'input_hashes': {'train.npy': 'hash'}}
    assert (output/'2022/chronological_seed24/job.json').read_text() == json.dumps(expected, indent=2)+'\n'


def test_changed_preparation_is_rejected_before_queue_creation(experiment):
    _, _, output, _, _, recovery = experiment
    (output/'prepared.json').write_text('{}')
    with pytest.raises(ValueError, match='Frozen input changed'):
        queue.run(*experiment)
    assert not recovery.exists()
    assert not list((output/'2022').glob('*/job.json'))


def test_worker_failure_stops_queue_before_later_jobs(experiment, monkeypatch):
    *_, recovery = experiment
    def fail(*args, **kwargs):raise RuntimeError('worker failed')
    monkeypatch.setattr(queue, 'run_locked', fail)
    with pytest.raises(RuntimeError, match='worker failed'):
        queue.run(*experiment)
    state = json.loads((recovery/'status.json').read_text())
    assert state['state'] == 'failed' and state['completed_fits'] == 2
    assert not (experiment[2]/'2022/shuffled_interior_seed24/job.json').exists()


def test_same_experiment_lock_excludes_another_queue(experiment):
    output = experiment[2]
    with (output/'.run.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(BlockingIOError):
            queue.run(*experiment)
    assert not experiment[-1].exists()
