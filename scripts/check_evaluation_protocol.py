"""Snapshot protocol readiness without opening any observation or outcome data."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from helio24.data import ROOT
from helio24.full_data import sha256
from helio24.evaluation_protocol import preflight


def run(output, config=ROOT / 'config/experiment5.json'):
    config = config.resolve()
    if not config.is_relative_to(ROOT.resolve()) or config.suffix != '.json':
        raise ValueError('Protocol config must be a JSON file inside the project')
    state = preflight(json.loads(config.read_text()))
    protocol = json.loads(config.read_text())
    legacy = ['docs/fifth-experiment-protocol.md', 'docs/fifth-experiment-protocol.tr.md']
    evidence = protocol.get('evidence_files', legacy)
    relative_config = str(config.relative_to(ROOT.resolve()))
    sources = [relative_config, *evidence, 'helio24/evaluation_protocol.py',
               'scripts/check_evaluation_protocol.py']
    if len(sources) != len(set(sources)):
        raise ValueError('Protocol evidence files must be unique')
    missing = [name for name in sources if not (ROOT / name).is_file()]
    if missing:
        raise ValueError(f'Missing protocol evidence: {missing}')
    state['source_hashes'] = {name: sha256(ROOT / name) for name in sources}
    output.mkdir(parents=True, exist_ok=False)
    (output / 'preflight.json').write_text(json.dumps(state, indent=2)+'\n')
    print(json.dumps(state, indent=2))
    return 0 if state['ready_for_training'] else 2


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'artifacts/experiment5_preflight')
    parser.add_argument('--config', type=Path, default=ROOT / 'config/experiment5.json')
    args = parser.parse_args()
    sys.exit(run(args.output, args.config))
