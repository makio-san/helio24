"""Snapshot protocol readiness without opening any observation or outcome data."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from helio24.data import ROOT
from helio24.full_data import sha256
from helio24.evaluation_protocol import preflight


def run(output):
    config = ROOT / 'config/experiment5.json'
    state = preflight(json.loads(config.read_text()))
    state['source_hashes'] = {p: sha256(ROOT / p) for p in [
        'config/experiment5.json', 'docs/fifth-experiment-protocol.md',
        'docs/fifth-experiment-protocol.tr.md', 'helio24/evaluation_protocol.py',
        'scripts/check_evaluation_protocol.py']}
    output.mkdir(parents=True, exist_ok=False)
    (output / 'preflight.json').write_text(json.dumps(state, indent=2)+'\n')
    print(json.dumps(state, indent=2))
    return 0 if state['ready_for_training'] else 2


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'artifacts/experiment5_preflight')
    args = parser.parse_args()
    sys.exit(run(args.output))
