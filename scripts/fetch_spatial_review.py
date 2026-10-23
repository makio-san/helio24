"""Fetch bounded AIA 131 context for two disputed historical flare identities."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
from urllib.parse import urlencode

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd
from helio24.data import ROOT
from helio24.full_data import sha256

API = 'https://api.helioviewer.org/v2/'


def run():
    output = ROOT / 'data/spatial_review'
    output.mkdir(exist_ok=False)
    catalog_path = ROOT / 'data/flare_catalog.csv'
    catalog = pd.read_csv(catalog_path).set_index('flare_id')

    def fetch(name, url, limit=5000000):
        path = output / name
        result = subprocess.run(['curl', '--fail', '--silent', '--show-error', '--location',
                                 '--max-time', '45', '--max-filesize', str(limit), '--proto', '=https',
                                 '--output', str(path), '--write-out', '%{url_effective}', url],
                                capture_output=True, text=True, timeout=50)
        record = dict(file=name, url=url, final_url=result.stdout.strip(),
                      retrieved_utc=datetime.now(timezone.utc).isoformat(),
                      status='downloaded' if result.returncode == 0 else 'unavailable', error=result.stderr.strip())
        if result.returncode:
            path.unlink(missing_ok=True)
        else:
            record.update(sha256=sha256(path), bytes=path.stat().st_size)
        return record

    sources = fetch('sources.json', API+'getDataSources/')
    if sources['status'] != 'downloaded':
        raise RuntimeError('Cannot verify AIA source identifier')
    source_id = json.loads((output / 'sources.json').read_text())['SDO']['AIA']['131']['sourceId']
    tasks = []
    for flare_id in [8765, 8864]:
        event = catalog.loc[flare_id]
        for stage, stamp in [('before', pd.Timestamp(event.start_time)-pd.Timedelta(minutes=5)),
                             ('peak', pd.Timestamp(event.peak_time)), ('end', pd.Timestamp(event.end_time))]:
            tasks.append((flare_id, stage, stamp.strftime('%Y-%m-%dT%H:%M:%SZ')))

    def frame(task):
        flare_id, stage, requested = task
        stem = f'{flare_id}_{stage}'
        metadata = fetch(stem+'.json', API+'getClosestImage/?'+urlencode(dict(date=requested, sourceId=source_id)))
        result = dict(flare_id=flare_id, stage=stage, requested_utc=requested, metadata=metadata)
        if metadata['status'] != 'downloaded':
            return result
        value = json.loads((output / metadata['file']).read_text())
        actual = pd.Timestamp(value['date'], tz='UTC')
        delta = abs((actual-pd.Timestamp(requested)).total_seconds())
        result.update(actual_utc=actual.isoformat(), offset_seconds=delta, image_id=value['id'])
        if delta > 60:
            result['rejection'] = 'Nearest image exceeds 60-second tolerance'
            return result
        params = dict(date=actual.strftime('%Y-%m-%dT%H:%M:%SZ'), imageScale=2.4,
                      layers='[SDO,AIA,AIA,131,1,100]', x0=0, y0=0, width=1024, height=1024,
                      display='true', watermark='true', events='[]', eventLabels='false')
        result['image'] = fetch(stem+'.png', API+'takeScreenshot/?'+urlencode(params))
        if result['image']['status'] == 'downloaded' and not (output / (stem+'.png')).read_bytes().startswith(b'\x89PNG\r\n\x1a\n'):
            result['rejection'] = 'Screenshot response is not PNG'
        return result

    with ThreadPoolExecutor(max_workers=3) as pool:
        frames = list(pool.map(frame, tasks))
    manifest = dict(scope='Two disputed development events; AIA 131 browse images, not calibrated photometry',
                    catalog_sha256=sha256(catalog_path), code_sha256=sha256(Path(__file__)), source_id=source_id,
                    source_listing=sources, frames=frames,
                    note='Metadata and rendered image are separate requests; inspect watermark to verify rendered time.')
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2))
    for row in frames:
        print(row['flare_id'], row['stage'], row.get('actual_utc'), row.get('rejection'), row.get('image', {}).get('status'), flush=True)


if __name__ == '__main__':
    run()
