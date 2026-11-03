"""Fail before training if required local files are cloud placeholders or missing."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from helio24.storage_preflight import inspect_storage


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--cache', type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    # Inspect only development inputs. Never traverse the reserved test dataset.
    paths = [root/'config', root/'helio24', root/'scripts/run_temporal_years.py',
             root/'scripts/temporal_worker.py', args.run, args.cache,
             root/'artifacts/temporal_smoke_20261101_r1/report.json',
             root/'artifacts/walk_forward_20261028_r1',
             root/'artifacts/calibration_windows_20261030_r1']
    result = inspect_storage(paths)
    result['scope'] = 'Frozen temporal-sequence-v2 resume inputs; metadata only, not a hash verification.'
    print(json.dumps(result, indent=2))
    return 0 if result['available'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
