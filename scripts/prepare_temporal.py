"""Stream recent-evolution features from verified SWAN-SF archives."""
import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from helio24.temporal import prepare_temporal_all


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--partitions', nargs='+', type=int, default=[1, 2, 3, 4, 5])
    parser.add_argument('--workers', type=int, choices=[1, 2, 3], default=2)
    arguments = parser.parse_args()
    prepare_temporal_all(arguments.partitions, arguments.workers)
