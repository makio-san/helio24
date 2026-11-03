"""Wait for local inputs and an idle experiment, then run the frozen coordinator."""
import argparse
from datetime import datetime, timezone
import fcntl
import json
from pathlib import Path
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from helio24.temporal_storage import inspect_temporal_inputs
from scripts.resume_temporal_job import ensure_no_worker


def readiness(root, protocol, output, cache):
    inputs = inspect_temporal_inputs(root, output, cache, protocol)
    if not inputs['available']:
        return 'waiting_for_inputs', inputs
    try:
        ensure_no_worker(output)
    except RuntimeError:
        return 'waiting_for_worker', inputs
    try:
        with (output/'.run.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        return 'waiting_for_lock', inputs
    return 'ready', inputs


def wait_until_ready(root, protocol, output, cache, timeout, interval, save):
    deadline = time.monotonic()+timeout
    while True:
        state, inputs = readiness(root, protocol, output, cache)
        save(state, blockers=inputs['blockers'], placeholder_bytes=inputs['placeholder_bytes'])
        if state == 'ready':
            return True
        remaining = deadline-time.monotonic()
        if remaining <= 0:
            save('waiting_timeout', blockers=inputs['blockers'])
            return False
        time.sleep(min(interval, remaining))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--protocol', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--cache', type=Path, required=True)
    parser.add_argument('--recovery', type=Path, required=True)
    parser.add_argument('--timeout-seconds', type=int, default=86400)
    args = parser.parse_args()
    if args.timeout_seconds <= 0:
        parser.error('--timeout-seconds must be positive')
    root = Path(__file__).resolve().parents[1]
    protocol, output, cache, recovery = (p.resolve() for p in [args.protocol, args.output, args.cache, args.recovery])
    recovery.mkdir(exist_ok=False)

    def save(state, **extra):
        record = {'state': state, 'checked_utc': datetime.now(timezone.utc).isoformat(),
                  'scope': 'annual_coordinator_resume', **extra}
        temporary = recovery/'status.tmp'
        temporary.write_text(json.dumps(record, indent=2)+'\n')
        temporary.replace(recovery/'status.json')

    try:
        if not wait_until_ready(root, protocol, output, cache, args.timeout_seconds, 30, save):
            return 2
        command = [sys.executable, '-u', str(root/'scripts/run_temporal_years.py'),
                   '--protocol', str(protocol), '--output', str(output), '--cache', str(cache)]
        with (recovery/'coordinator.log').open('x') as log:
            process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT)
            launcher = {'pid': process.pid, 'command': command, 'started_utc': datetime.now(timezone.utc).isoformat(),
                        'reason': 'All declared resume inputs are local and no worker or runner lock was active; frozen coordinator performs full hash verification.'}
            (recovery/'launcher.json').write_text(json.dumps(launcher, indent=2)+'\n')
            save('coordinator_active', pid=process.pid)
            code = process.wait()
        save('coordinator_complete' if code == 0 else 'failed', returncode=code)
        return code
    except BaseException as error:
        save('failed', error=repr(error))
        raise


if __name__ == '__main__':
    raise SystemExit(main())
