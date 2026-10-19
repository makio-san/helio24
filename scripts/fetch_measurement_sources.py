"""Snapshot five historical SHARP headers; no flare labels or future records."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
from urllib.parse import urlencode

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from helio24.data import ROOT
from helio24.full_data import sha256


def run():
    output = ROOT / 'data/measurement_sources'
    output.mkdir(exist_ok=False)
    selection = ROOT / 'artifacts/v2_overlap/report.json'
    records = json.loads(selection.read_text())['selected']
    keys = 'HARPNUM,T_REC,T_OBS,QUALITY,USFLUX,MEANPOT,TOTPOT,MEANSHR,SHRGT45,CDELT1,RSUN_REF,RSUN_OBS,DSUN_OBS'

    def fetch(record):
        stamp = datetime.fromisoformat(record['observation_start']).strftime('%Y.%m.%d_%H:%M:%S')
        # This queries the stored clock as TAI, explicitly a hypothesis, not a UTC conversion.
        query = dict(op='rs_list', ds=f"hmi.sharp_cea_720s[{record['harp']}][{stamp}_TAI]", key=keys)
        path = output / f"harp_{record['harp']}.json"
        attempts = []
        for scheme in ['https', 'http']:
            url = f'{scheme}://jsoc.stanford.edu/cgi-bin/ajax/jsoc_info?' + urlencode(query)
            result = subprocess.run(['curl', '--fail', '--silent', '--show-error', '--location', '--max-time', '20',
                                     '--max-filesize', '1048576', '--proto', '=http,https', '--output', str(path),
                                     '--write-out', '%{url_effective}', url], capture_output=True, text=True, timeout=25)
            attempts.append(dict(url=url, final_url=result.stdout.strip(), returncode=result.returncode,
                                 error=result.stderr.strip(), retrieved_utc=datetime.now(timezone.utc).isoformat()))
            if result.returncode == 0:
                return dict(harp=record['harp'], clock=record['observation_start'], status='downloaded',
                            transport=scheme, attempts=attempts, file=path.name, sha256=sha256(path))
            path.unlink(missing_ok=True)
        return dict(harp=record['harp'], status='unavailable', attempts=attempts)

    with ThreadPoolExecutor(max_workers=5) as pool:
        sources = list(pool.map(fetch, records))
    manifest = dict(selection_sha256=sha256(selection), code_sha256=sha256(Path(__file__)), sources=sources,
                    note='Clock-as-TAI hypothesis only. HTTP fallback is unauthenticated; TLS verification is never disabled.')
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2))
    print(json.dumps(sources, indent=2))


if __name__ == '__main__':
    run()
