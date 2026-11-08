"""Fetch NOAA SWPC Solar Region Summaries for the development period over HTTPS with a hashed manifest."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess
import sys

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from helio24.full_data import sha256

BASE = 'https://www.ngdc.noaa.gov/stp/space-weather/swpc-products/daily_reports/solar_region_summaries'
ISSUED = re.compile(r'^:Issued: (\d{4} [A-Z][a-z]{2} \d{2} \d{4}) UTC\s*$', re.M)


def issue_time(text):
    match = ISSUED.search(text)
    if not match:
        return None
    return datetime.strptime(match.group(1), '%Y %b %d %H%M').replace(tzinfo=timezone.utc).isoformat()


def fetch_one(day, output):
    name = f'{day:%Y%m%d}SRS.txt'
    path = output/name
    url = f'{BASE}/{day:%Y}/{day:%m}/{name}'
    result = subprocess.run(['curl', '--fail', '--silent', '--show-error', '--max-time', '60',
                             '--max-filesize', '200000', '--proto', '=https', '--output', str(path), url],
                            capture_output=True, text=True)
    record = {'date': f'{day:%Y-%m-%d}', 'file': name, 'url': url, 'returncode': result.returncode,
              'retrieved_utc': datetime.now(timezone.utc).isoformat()}
    if result.returncode != 0:
        record.update(status='unavailable', error=result.stderr.strip()[:200])
        path.unlink(missing_ok=True)
        return record
    text = path.read_text(errors='replace')
    record.update(status='ok', bytes=path.stat().st_size, sha256=sha256(path), issued_utc=issue_time(text))
    return record


def run(output, start, end, workers):
    output.mkdir(parents=True, exist_ok=False)
    days = pd.date_range(start, end, freq='D')
    with ThreadPoolExecutor(max_workers=workers) as pool:
        records = list(pool.map(lambda d: fetch_one(d, output), days))
    manifest = {'source': BASE, 'period': [str(start), str(end)], 'files_expected': len(days),
                'files_ok': sum(r['status'] == 'ok' for r in records),
                'files_without_issue_time': sum(r['status'] == 'ok' and not r.get('issued_utc') for r in records),
                'bytes': sum(r.get('bytes', 0) for r in records),
                'code_sha256': sha256(Path(__file__)), 'records': records}
    (output/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print(json.dumps({k: v for k, v in manifest.items() if k != 'records'}, indent=1))
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--start', default='2010-05-01')
    parser.add_argument('--end', default='2023-12-31')
    parser.add_argument('--workers', type=int, default=4)
    args = parser.parse_args()
    run(args.output, args.start, args.end, args.workers)
