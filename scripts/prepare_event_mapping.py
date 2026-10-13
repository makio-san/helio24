"""Recover verified event associations from the existing partition-4 archive."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from helio24.event_mapping import prepare_mapping

if __name__ == '__main__':
    print(prepare_mapping())
