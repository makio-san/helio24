"""Snapshot small public NOAA/JSOC records for the three disputed events."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
from urllib.parse import urlencode, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from helio24.data import ROOT
from helio24.full_data import sha256

NOAA = 'https://www.ngdc.noaa.gov/stp/space-weather/swpc-products/daily_reports/'
JSOC = 'http://jsoc.stanford.edu/'
KEYS = 'HARPNUM,T_REC,NOAA_AR,NOAA_NUM,NOAA_ARS,LAT_MIN,LAT_MAX,LON_MIN,LON_MAX,QUALITY'


def sources():
    result = {}
    for date, following in [('20140821', '20140822'), ('20140903', '20140904'), ('20141218', '20141219')]:
        result[date+'events.txt'] = NOAA+f'solar_event_reports/{date[:4]}/{date[4:6]}/{date}events.txt'
        result[following+'SRS.txt'] = NOAA+f'solar_region_summaries/{following[:4]}/{following[4:6]}/{following}SRS.txt'
    result['all_harps_with_noaa_ars.txt'] = JSOC+'doc/data/hmi/harpnum_to_noaa/all_harps_with_noaa_ars.txt'
    result['SolarEventReport.pdf'] = NOAA+'solar_event_reports/docs/SolarEventReport.pdf'
    for harp, date, hour in [(4466, '2014.08.21', '13'), (4502, '2014.09.03', '13'),
                             (4920, '2014.12.18', '21'), (4941, '2014.12.18', '21')]:
        params = dict(op='rs_list', ds=f'hmi.sharp_720s[{harp}][{date}_{hour}:00:00_TAI/1h]', key=KEYS)
        result[f'harp_{harp}.json'] = JSOC+'cgi-bin/ajax/jsoc_info?'+urlencode(params)
    return result


def run(root=ROOT):
    directory = root / 'data/source_review'
    if directory.exists():
        raise RuntimeError('Preserve the existing source snapshot before fetching again')
    directory.mkdir(parents=True)

    def fetch(item):
        name, url = item
        path = directory / name
        command = ['curl', '--fail', '--silent', '--show-error', '--location', '--max-time', '25',
                   '--max-filesize', '1048576', '--proto', '=http,https', '--output', str(path),
                   '--write-out', '%{url_effective}', url]
        result = subprocess.run(command, capture_output=True, text=True, timeout=30)
        record = dict(url=url, final_url=result.stdout.strip(), retrieved_utc=datetime.now(timezone.utc).isoformat(),
                      status='downloaded' if result.returncode == 0 else 'unavailable',
                      transport=urlsplit(result.stdout.strip() or url).scheme,
                      error=result.stderr.strip() or None)
        if result.returncode == 0:
            record.update(sha256=sha256(path), bytes=path.stat().st_size)
        elif path.exists():
            path.unlink()
        return name, record

    with ThreadPoolExecutor(max_workers=4) as pool:
        records = dict(pool.map(fetch, sources().items()))
    manifest = dict(scope='Three-event source review; public metadata only', sources=records,
                    code_sha256=sha256(__file__),
                    transport_note='JSOC uses published HTTP after HTTPS certificate verification failed; '
                    'HTTP content is not transport-authenticated. TLS verification is never disabled.')
    (directory / 'manifest.json').write_text(json.dumps(manifest, indent=2))
    for name, record in records.items():
        print(name, record['status'], record.get('error') or '')


if __name__ == '__main__':
    run()
