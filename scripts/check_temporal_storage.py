"""Fail before training if required local files are cloud placeholders or missing."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from helio24.temporal_storage import inspect_temporal_inputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--cache', type=Path, required=True)
    parser.add_argument('--protocol', type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    result = inspect_temporal_inputs(root, args.run, args.cache, args.protocol)
    print(json.dumps(result, indent=2))
    return 0 if result['available'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
