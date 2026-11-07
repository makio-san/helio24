"""Freeze one fixed-date NOAA report per eligible development year."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess


def fetch(output):
    output.mkdir(parents=True, exist_ok=False)
    def one(year):
        date = f'{year}0903'
        url = f'https://www.ngdc.noaa.gov/stp/space-weather/swpc-products/daily_reports/solar_event_reports/{year}/09/{date}events.txt'
        path = output/f'{date}events.txt'
        response = subprocess.run(['curl', '-fLsS', '--proto', '=https', '--proto-redir', '=https',
            '--max-time', '25', '--max-filesize', '1048576', '-o', str(path), url],
            capture_output=True, text=True, timeout=30)
        row = {'year':year, 'url':url, 'file':path.name,
               'status':'downloaded' if response.returncode == 0 else 'unavailable',
               'error':response.stderr.strip(), 'retrieved_utc':datetime.now(timezone.utc).isoformat()}
        if response.returncode == 0:
            row['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
        elif path.exists():
            path.unlink()
        return row
    with ThreadPoolExecutor(max_workers=4) as pool:
        rows = list(pool.map(one, [2014, 2015, 2016, 2017, 2018, 2022, 2023]))
    (output/'manifest.json').write_text(json.dumps({
        'scope':'Fixed September 3 sample per eligible year; not a full coverage audit',
        'sources':rows}, indent=2)+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    fetch(parser.parse_args().output)
