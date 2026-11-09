"""Fetch one SHARP CEA Br map per development HARP-day from JSOC, resize it and keep a hashed manifest."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import threading
from urllib.parse import urlencode

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from helio24.full_data import sha256

ROOT = Path(__file__).resolve().parents[1]
RESERVED_START = pd.Timestamp('2024-01-01')


def resize(image, shape):
    """Area mean over valid pixels; cells without a valid pixel become 0."""
    import torch
    from torch.nn.functional import adaptive_avg_pool2d
    valid = np.isfinite(image)
    values = torch.from_numpy(np.where(valid, image, 0.0).astype(np.float32))[None, None]
    weight = torch.from_numpy(valid.astype(np.float32))[None, None]
    total = adaptive_avg_pool2d(values, shape)[0, 0].numpy()
    share = adaptive_avg_pool2d(weight, shape)[0, 0].numpy()
    return np.where(share > 0, total/np.where(share > 0, share, 1.0), 0.0).astype(np.float16)


def month_index(month, cache, config):
    """Return (harp, t_rec, dims, path) rows of one month, querying JSOC only when not cached."""
    if month >= RESERVED_START:
        raise ValueError('Reserved period must not be indexed')
    days = (month+pd.offsets.MonthBegin(1)-month).days
    path = cache/f'{month:%Y%m}.json'
    if not path.exists():
        query = urlencode({'op': 'rs_list', 'ds': f'{config["source"]["series"]}[][{month:%Y.%m.%d}_TAI/{days}d@1d]',
                           'key': 'HARPNUM,T_REC', 'seg': config['source']['segment']})
        url = 'http://jsoc.stanford.edu/cgi-bin/ajax/jsoc_info?'+query
        subprocess.run(['curl', '--fail', '--silent', '--max-time', '180', '--retry', '2', '--output', str(path), url],
                       check=True)
    payload = json.loads(path.read_text())
    if not payload.get('keywords'):
        return []
    keys = {item['name']: item['values'] for item in payload['keywords']}
    segment = {item['name']: item for item in payload['segments']}[config['source']['segment']]
    return [(int(h), t, d, p) for h, t, d, p in zip(keys['HARPNUM'], keys['T_REC'], segment['dims'], segment['values'])]


def build_index(config, cache):
    cache.mkdir(parents=True, exist_ok=True)
    start, end = config['scope']['index_period']
    rows = [row for month in pd.date_range(start, end, freq='MS') for row in month_index(month, cache, config)]
    index = pd.DataFrame(rows, columns=['harp', 't_rec', 'dims', 'path'])
    index['date'] = index.t_rec.str[:10].str.replace('.', '-', regex=False)
    if (pd.to_datetime(index.date) >= RESERVED_START).any():
        raise ValueError('Index reached the reserved period')
    return index[index.path.str.endswith('.fits')]


def development_days(config):
    from helio24.v2_training import load_development
    frames, _ = load_development(ROOT/config['scope']['frozen_shards'], config['scope']['frozen_shards_report_sha256'])
    table = pd.concat(frames.values(), ignore_index=True)[['harp', 'forecast_time']]
    table['date'] = pd.to_datetime(table.forecast_time, utc=True).dt.strftime('%Y-%m-%d')
    return table.groupby(['harp', 'date']).size().rename('windows').reset_index()


def fetch_one(row, output, config, log, lock):
    from astropy.io import fits
    target = output/'maps'/str(row.harp)/f'{row.date}.npy'
    raw = output/'raw'/f'{row.harp}_{row.date}.fits'
    url = config['source']['files']+row.path
    result = subprocess.run(['curl', '--fail', '--silent', '--show-error', '--max-time', '300', '--retry', '3',
                             '--max-filesize', '60000000', '--proto', '=https', '--output', str(raw), url],
                            capture_output=True, text=True)
    record = {'harp': int(row.harp), 'date': row.date, 't_rec': row.t_rec, 'url': url,
              'retrieved_utc': datetime.now(timezone.utc).isoformat()}
    try:
        if result.returncode != 0:
            raise OSError(result.stderr.strip()[:200] or f'curl {result.returncode}')
        with fits.open(raw) as hdul:
            image = np.asarray(hdul[1].data, dtype=np.float64)
        record.update(raw_bytes=raw.stat().st_size, raw_sha256=sha256(raw), width=int(image.shape[1]),
                      height=int(image.shape[0]), nan_fraction=round(float(1-np.isfinite(image).mean()), 6))
        small = resize(image, tuple(config['processing']['output_shape_height_width']))
        target.parent.mkdir(parents=True, exist_ok=True)
        np.save(target, small)
        record.update(status='ok', map=str(target.relative_to(output)),
                      map_sha256=hashlib.sha256(small.tobytes()).hexdigest())
    except Exception as error:  # an unavailable or unreadable record is listed, never imputed
        record.update(status='unavailable', error=str(error)[:200])
    raw.unlink(missing_ok=True)
    with lock:
        with log.open('a') as handle:
            handle.write(json.dumps(record)+'\n')
    return record


def run(config_path, output, cache, workers, limit):
    config = json.loads(config_path.read_text())
    days = development_days(config)
    todo = days.merge(build_index(config, cache), on=['harp', 'date'], how='inner').sort_values(['date', 'harp'])
    (output/'raw').mkdir(parents=True, exist_ok=True)
    log = output/'records.jsonl'
    done = set()
    if log.exists():  # resume: a record already logged as ok is not requested again
        for line in log.read_text().splitlines():
            item = json.loads(line)
            if item['status'] == 'ok':
                done.add((item['harp'], item['date']))
    rows = [row for row in todo.itertuples() if (row.harp, row.date) not in done]
    if limit:
        rows = rows[:limit]
    lock = threading.Lock()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        list(pool.map(lambda row: fetch_one(row, output, config, log, lock), rows))
    latest = {}
    for line in log.read_text().splitlines() if log.exists() else []:
        item = json.loads(line)
        latest[(item['harp'], item['date'])] = item
    ok = [item for item in latest.values() if item['status'] == 'ok']
    manifest = {'config': str(config_path), 'config_sha256': sha256(config_path), 'code_sha256': sha256(Path(__file__)),
                'development_harp_days': len(days), 'harp_days_with_a_record': len(todo), 'maps_ok': len(ok),
                'unavailable': len(latest)-len(ok), 'not_yet_requested': len(todo)-len(latest),
                'raw_bytes': sum(item['raw_bytes'] for item in ok), 'records_sha256': sha256(log) if log.exists() else None,
                'reserved_test_accessed': False}
    (output/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print(json.dumps(manifest, indent=1))
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=ROOT/'config/sharp-maps-v1.json')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--index-cache', type=Path, required=True)
    parser.add_argument('--workers', type=int, default=4)
    parser.add_argument('--limit', type=int, default=0)
    args = parser.parse_args()
    run(args.config, args.output, args.index_cache, args.workers, args.limit)
