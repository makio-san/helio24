"""Rebuild a frozen HEK inventory from surviving raw responses and re-fetch only missing months."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd

from helio24.data import ROOT
from helio24.full_data import sha256
from helio24.hek_inventory import monthly_intervals, parse_month
from scripts.fetch_hek_major_inventory import fetch_month


def run(source, output, expected_events_sha256):
    if output.exists():
        raise FileExistsError(output)
    intervals = monthly_intervals('2010-05-01', '2024-01-01')
    raw = output/'raw'
    raw.mkdir(parents=True)
    results, fetched = [], []
    for start, end in intervals:
        name = f'{start:%Y-%m}.json'
        survived = source/'raw'/name
        if survived.exists():
            payload = survived.read_bytes()
            frame, url = parse_month(payload, start, end), None
        else:
            payload, frame, url = fetch_month(start, end)
            fetched.append(name)
            print(f'fetched {name}: {len(frame)} M/X events', flush=True)
        (raw/name).write_bytes(payload)
        results.append((start, end, frame, url, raw/name))
    events = pd.concat([value[2] for value in results], ignore_index=True)
    if events.event_id.duplicated().any():
        raise ValueError('Event IDs repeat across monthly ownership intervals')
    events.to_csv(output/'events.csv', index=False)
    months = [{'start': s.isoformat(), 'end': e.isoformat(), 'source': 'refetched' if p.name in fetched else 'surviving_raw',
               'events': len(f), 'response_bytes': p.stat().st_size, 'response_sha256': sha256(p)}
              for s, e, f, u, p in results]
    matches = sha256(output/'events.csv') == expected_events_sha256
    report = {
        'scope': 'Recovered HEK SWPC GOES M/X events with peak in [2010-05-01, 2024-01-01); surviving raw responses plus re-fetched months',
        'recovered_utc': datetime.now(timezone.utc).isoformat(),
        'months': len(months), 'refetched_months': fetched, 'events': len(events),
        'events_sha256': sha256(output/'events.csv'), 'expected_events_sha256': expected_events_sha256,
        'matches_frozen_events': matches,
        'raw_response_set_sha256': hashlib.sha256(''.join(m['response_sha256'] for m in months).encode()).hexdigest(),
        'code_hashes': {'helio24/hek_inventory.py': sha256(ROOT/'helio24/hek_inventory.py'),
                        'scripts/rebuild_hek_inventory.py': sha256(__file__)},
        'queries': months}
    (output/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k: v for k, v in report.items() if k not in {'queries', 'refetched_months'}}, indent=2))
    if not matches:
        raise ValueError('Rebuilt events.csv does not match the frozen hash; do not use this inventory')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--expected-events-sha256', required=True)
    args = parser.parse_args()
    run(args.source, args.output, args.expected_events_sha256)
