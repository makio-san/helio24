"""Stream official V2 raw archives to SHA-256 without saving archive bodies."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from helio24.data import ROOT
from helio24.full_data import sha256
from helio24.v2_sources import validate_manifest

CHUNK = 4*1024*1024


def hash_archive(item):
    digest, received = hashlib.sha256(), 0
    request = Request(item['url'], headers={'Accept-Encoding': 'identity',
                                            'User-Agent': 'Helio24-source-audit/1'})
    with urlopen(request, timeout=120) as response:
        if response.status != 200:
            raise ValueError(f'Partition {item["partition"]}: expected HTTP 200')
        length = int(response.headers['Content-Length'])
        etag = response.headers.get('ETag', '').strip('"')
        if length != item['content_length'] or etag != item['etag']:
            raise ValueError(f'Partition {item["partition"]}: remote identity changed')
        while chunk := response.read(CHUNK):
            digest.update(chunk)
            received += len(chunk)
            if received > item['content_length']:
                raise ValueError(f'Partition {item["partition"]}: oversized response')
            if received % (256*1024*1024) < CHUNK:
                print(f'partition {item["partition"]}: {received}/{length} bytes', flush=True)
    if received != item['content_length']:
        raise ValueError(f'Partition {item["partition"]}: incomplete response')
    return {'partition': item['partition'], 'url': item['url'], 'bytes': received,
            'etag': item['etag'], 'sha256': digest.hexdigest()}


def run(output, workers=2):
    manifest_path = ROOT / 'config/swan_sf_v2_sources.json'
    manifest = json.loads(manifest_path.read_text())
    errors = validate_manifest(manifest)
    if errors:
        raise ValueError('; '.join(errors))
    if output.exists():
        raise RuntimeError('Preserve the existing archive hash audit')
    results = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(hash_archive, item): item['partition'] for item in manifest['archives']}
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            print(f'partition {result["partition"]}: {result["sha256"]}', flush=True)
    output.mkdir(parents=True)
    report = {
        'scope': 'Byte-for-byte streaming hashes; archive bodies were not saved',
        'completed_utc': datetime.now(timezone.utc).isoformat(),
        'manifest_sha256': sha256(manifest_path),
        'script_sha256': sha256(__file__),
        'archives': sorted(results, key=lambda item: item['partition']),
    }
    (output / 'hashes.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'artifacts/v2_archive_hashes')
    parser.add_argument('--workers', type=int, choices=range(1, 5), default=2)
    args = parser.parse_args()
    run(args.output, args.workers)
