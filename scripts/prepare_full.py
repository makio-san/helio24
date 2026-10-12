"""Stream full archives without expanding hundreds of thousands of raw files."""
import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from helio24.full_data import prepare_all

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--partitions', nargs='+', type=int, default=[1, 2, 3, 4, 5], choices=range(1, 6))
    parser.add_argument('--workers', type=int, default=2, choices=[1, 2, 3])
    args = parser.parse_args()
    prepare_all(args.partitions, args.workers)
