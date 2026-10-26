"""Run the frozen Experiment 5 development-only model comparison."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from helio24.data import ROOT
from helio24.full_data import sha256
from helio24.v2_training import fit_development, load_development


def run(output, materialized, protocol_path):
    protocol = json.loads(protocol_path.read_text())
    expected = protocol['development_data']['report_sha256']
    groups, materialization = load_development(materialized, expected)
    report = fit_development(groups, protocol, output)
    report.update({
        'scope': 'Pre-2024 train/calibration/validation only; no reserved test access',
        'completed_utc': datetime.now(timezone.utc).isoformat(),
        'source_hashes': {
            str(protocol_path.relative_to(ROOT)): sha256(protocol_path),
            str((materialized / 'report.json').relative_to(ROOT)):
                sha256(materialized / 'report.json'),
        },
        'materialization_rows': materialization['rows'],
        'code_hashes': {name: sha256(ROOT / name) for name in [
            'helio24/modeling.py', 'helio24/calibration.py',
            'helio24/v2_training.py', 'scripts/run_v2_development.py']},
    })
    (output / 'report.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({key: value for key, value in report.items()
                      if key not in {'artifact_hashes', 'source_hashes', 'code_hashes'}},
                     indent=2))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--materialized', type=Path, required=True)
    parser.add_argument('--protocol', type=Path, required=True)
    args = parser.parse_args()
    run(args.output.resolve(), args.materialized.resolve(), args.protocol.resolve())
