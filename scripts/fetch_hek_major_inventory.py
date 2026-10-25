"""Freeze monthly HEK/SWPC GOES M/X responses for V2 development labeling."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd

from helio24.data import ROOT
from helio24.full_data import sha256
from helio24.hek_inventory import monthly_intervals, parse_month, query_url


def fetch_month(start, end, attempts=3, opener=urlopen):
    url = query_url(start, end)
    error = None
    for _ in range(attempts):
        try:
            request = Request(url, headers={'Accept-Encoding': 'identity',
                                            'User-Agent': 'Helio24-label-audit/1'})
            with opener(request, timeout=120) as response:
                if response.status != 200:
                    raise ValueError(f'HEK returned HTTP {response.status}')
                payload = response.read()
            frame = parse_month(payload, start, end)
            return payload, frame, url
        except (OSError, TimeoutError, ConnectionError) as candidate:
            error = candidate
    raise error


def run(output, workers=2):
    if output.exists():
        raise RuntimeError('Preserve the existing HEK inventory audit')
    raw = output / 'raw'
    raw.mkdir(parents=True)
    intervals = monthly_intervals('2010-05-01', '2024-01-01')
    results = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(fetch_month, start, end): (start, end)
                   for start, end in intervals}
        for future in as_completed(futures):
            start, end = futures[future]
            payload, frame, url = future.result()
            name = f'{start:%Y-%m}.json'
            path = raw / name
            path.write_bytes(payload)
            results.append((start, end, frame, url, path))
            print(f'{start:%Y-%m}: {len(frame)} M/X events', flush=True)

    results.sort(key=lambda value: value[0])
    events = pd.concat([value[2] for value in results], ignore_index=True)
    if events.event_id.duplicated().any():
        raise ValueError('Event IDs repeat across monthly ownership intervals')
    duplicate_peak_class = events.duplicated(['peak_time', 'goes_class'], keep=False)
    duplicate_keys = events.loc[duplicate_peak_class, ['peak_time', 'goes_class']].drop_duplicates()
    events.to_csv(output / 'events.csv', index=False)
    months = [{
        'start': start.isoformat(), 'end': end.isoformat(), 'url': url,
        'events': len(frame), 'response_bytes': path.stat().st_size,
        'response_sha256': sha256(path),
    } for start, end, frame, url, path in results]
    report = {
        'scope': 'Official HEK SWPC GOES M/X events with peak in [2010-05-01, 2024-01-01)',
        'retrieved_utc': datetime.now(timezone.utc).isoformat(),
        'months': len(months), 'events': len(events),
        'distinct_peak_class_events': int(
            len(events.drop_duplicates(['peak_time', 'goes_class']))),
        'duplicate_peak_class_keys': len(duplicate_keys),
        'duplicate_peak_class_rows': int(duplicate_peak_class.sum()),
        'providers': {str(k): int(v) for k, v in events.provider.value_counts().items()},
        'class_counts': {str(k): int(v) for k, v in events.goes_class.str[0].value_counts().items()},
        'raw_response_set_sha256': hashlib.sha256(''.join(
            month['response_sha256'] for month in months).encode()).hexdigest(),
        'events_sha256': sha256(output / 'events.csv'),
        'code_hashes': {
            'helio24/hek_inventory.py': sha256(ROOT / 'helio24/hek_inventory.py'),
            'scripts/fetch_hek_major_inventory.py': sha256(__file__),
        },
        'queries': months,
    }
    (output / 'report.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'queries'}, indent=2))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path,
                        default=ROOT / 'artifacts/hek_major_inventory')
    parser.add_argument('--workers', type=int, choices=range(1, 5), default=2)
    args = parser.parse_args()
    run(args.output, args.workers)
