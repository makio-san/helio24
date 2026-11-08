"""Fetch daily HARP to NOAA region associations from JSOC, one query per month, with a hashed manifest."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
from urllib.parse import urlencode

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from helio24.full_data import sha256

KEYS = 'HARPNUM,T_REC,NOAA_AR,NOAA_ARS,NOAA_NUM'


def fetch_month(month_start, output):
    days = (month_start+pd.offsets.MonthBegin(1)-month_start).days
    name = f'{month_start:%Y%m}.json'
    path = output/name
    ds = f'hmi.sharp_cea_720s[][{month_start:%Y.%m.%d}_TAI/{days}d@1d]'
    attempts = []
    for scheme in ['https', 'http']:
        url = f'{scheme}://jsoc.stanford.edu/cgi-bin/ajax/jsoc_info?'+urlencode({'op': 'rs_list', 'ds': ds, 'key': KEYS})
        result = subprocess.run(['curl', '--fail', '--silent', '--show-error', '--location', '--max-time', '180',
                                 '--max-filesize', '20000000', '--proto', '=http,https', '--output', str(path), url],
                                capture_output=True, text=True)
        attempts.append({'transport': scheme, 'returncode': result.returncode, 'error': result.stderr.strip()[:200],
                         'retrieved_utc': datetime.now(timezone.utc).isoformat()})
        if result.returncode == 0:
            try:
                payload = json.loads(path.read_text())
            except json.JSONDecodeError:
                path.unlink(missing_ok=True)
                continue
            if payload.get('status') != 0:
                path.unlink(missing_ok=True)
                attempts[-1]['jsoc_status'] = payload.get('status')
                continue
            return {'month': f'{month_start:%Y-%m}', 'file': name, 'ds': ds, 'status': 'ok', 'transport': scheme,
                    'count': payload.get('count'), 'bytes': path.stat().st_size, 'sha256': sha256(path), 'attempts': attempts}
    path.unlink(missing_ok=True)
    return {'month': f'{month_start:%Y-%m}', 'file': name, 'ds': ds, 'status': 'unavailable', 'attempts': attempts}


def run(output, start, end):
    output.mkdir(parents=True, exist_ok=False)
    months = pd.date_range(pd.Timestamp(start).replace(day=1), end, freq='MS')
    records = [fetch_month(m, output) for m in months]
    manifest = {'series': 'hmi.sharp_cea_720s', 'keys': KEYS, 'cadence': '1d', 'period': [str(start), str(end)],
                'months_expected': len(months), 'months_ok': sum(r['status'] == 'ok' for r in records),
                'http_fallback_months': sum(r.get('transport') == 'http' for r in records),
                'bytes': sum(r.get('bytes', 0) for r in records), 'code_sha256': sha256(Path(__file__)),
                'limitation': 'HTTP fallback is unauthenticated; TLS verification is not disabled. NOAA_ARS availability time is not stated by JSOC.',
                'records': records}
    (output/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print(json.dumps({k: v for k, v in manifest.items() if k != 'records'}, indent=1))
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--start', default='2010-05-01')
    parser.add_argument('--end', default='2023-12-31')
    args = parser.parse_args()
    run(args.output, args.start, args.end)
