import fcntl
from pathlib import Path

from scripts import await_temporal_resume as waiter


def test_missing_inputs_do_not_trigger_process_or_lock_checks(tmp_path, monkeypatch):
    monkeypatch.setattr(waiter, 'inspect_temporal_inputs', lambda *_: {'available': False, 'blockers': [{'reason': 'missing'}]})
    def unexpected(*args):raise AssertionError('Do not launch or check processes with missing inputs')
    monkeypatch.setattr(waiter, 'ensure_no_worker', unexpected)
    assert waiter.readiness(tmp_path, tmp_path/'protocol', tmp_path, tmp_path/'cache')[0] == 'waiting_for_inputs'


def test_existing_worker_and_runner_lock_delay_handoff(tmp_path, monkeypatch):
    monkeypatch.setattr(waiter, 'inspect_temporal_inputs', lambda *_: {'available': True, 'blockers': []})
    def active(*args):raise RuntimeError('Existing worker')
    monkeypatch.setattr(waiter, 'ensure_no_worker', active)
    args = (tmp_path, tmp_path/'protocol', tmp_path, tmp_path/'cache')
    assert waiter.readiness(*args)[0] == 'waiting_for_worker'
    monkeypatch.setattr(waiter, 'ensure_no_worker', lambda *_: None)
    with (tmp_path/'.run.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert waiter.readiness(*args)[0] == 'waiting_for_lock'
    assert waiter.readiness(*args)[0] == 'ready'


def test_wait_timeout_does_not_claim_training_started(tmp_path, monkeypatch):
    times = iter([0, 2])
    monkeypatch.setattr(waiter.time, 'monotonic', lambda: next(times))
    monkeypatch.setattr(waiter, 'readiness', lambda *_: ('waiting_for_inputs', {'blockers': [], 'placeholder_bytes': 10}))
    states = []
    assert not waiter.wait_until_ready(tmp_path, tmp_path/'p', tmp_path, tmp_path/'c', 1, 30,
                                       lambda state, **_: states.append(state))
    assert states == ['waiting_for_inputs', 'waiting_timeout']
