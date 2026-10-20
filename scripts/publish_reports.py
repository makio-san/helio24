"""Publish reviewed Turkish and English report editions without retraining."""
import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from helio24.bilingual_reports import publish
from helio24.data import ROOT


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'artifacts/bilingual_reports')
    args = parser.parse_args()
    publish(ROOT, args.output.resolve())
    print(args.output.resolve() / 'index.html')
