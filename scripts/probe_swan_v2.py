"""Read one bounded V2 Parquet member's schema; do not score or inspect labels."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import tarfile
import time
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pyarrow.parquet as pq
from helio24.data import ROOT, MAGNETIC_COLUMNS
from helio24.full_data import sha256

URL = 'https://dmlab.cs.gsu.edu/solar/swan-sf/swan-mvts-part1.tar.gz'
LIMIT = 400*1024*1024


def run(root=ROOT):
    output = root / 'data/compatibility_probe'
    output.mkdir(parents=True, exist_ok=True)
    destination = output / 'first_member.parquet'
    if destination.exists() or (output / 'schema.json').exists():
        raise RuntimeError('Preserve the existing compatibility sample before rerunning')
    start, digest = time.monotonic(), hashlib.sha256()
    request = Request(URL, headers={'Range': f'bytes=0-{LIMIT-1}'})
    with urlopen(request, timeout=30) as response:
        if response.status != 206 or not response.headers.get('Content-Range', '').startswith('bytes 0-'):
            raise ValueError('Expected bounded HTTP range response')
        class LimitedReader:
            count = 0

            def read(self, size):
                if time.monotonic()-start > 180 or self.count+size > LIMIT:
                    raise ValueError('Compatibility probe transfer limit reached')
                chunk = response.read(size)
                self.count += len(chunk)
                digest.update(chunk)
                return chunk

        reader = LimitedReader()
        with tarfile.open(fileobj=reader, mode='r|gz') as archive:
            for member in archive:
                if not member.isfile():
                    continue
                if not member.name.endswith('.parquet') or member.size > LIMIT:
                    raise ValueError('Unexpected or oversized first archive member')
                # Fixed destination: never extract paths supplied by the archive.
                temporary = destination.with_suffix('.part')
                copied = 0
                with temporary.open('wb') as target, archive.extractfile(member) as source:
                    while chunk := source.read(1024*1024):
                        copied += len(chunk)
                        if copied > LIMIT:
                            raise ValueError('Uncompressed member limit reached')
                        target.write(chunk)
                if copied != member.size:
                    raise ValueError('Incomplete Parquet member')
                schema = pq.read_schema(temporary)
                metadata = pq.read_metadata(temporary)
                temporary.rename(destination)
                report = dict(url=URL, retrieved_utc=datetime.now(timezone.utc).isoformat(),
                              http_status=response.status, content_range=response.headers['Content-Range'],
                              etag=response.headers.get('ETag'), member=member.name,
                              bytes_received=reader.count, compressed_prefix_sha256=digest.hexdigest(),
                              member_bytes=copied, member_sha256=sha256(destination),
                              rows=metadata.num_rows, row_groups=metadata.num_row_groups,
                              schema=str(schema), columns=schema.names,
                              magnetic_names_present=[name for name in MAGNETIC_COLUMNS if name in schema.names],
                              magnetic_names_missing=[name for name in MAGNETIC_COLUMNS if name not in schema.names],
                              scope='One member schema only; no target values, predictions, or performance inspected',
                              code_sha256=sha256(__file__))
                (output / 'schema.json').write_text(json.dumps(report, indent=2))
                print(json.dumps(report, indent=2))
                return report
    raise ValueError('No regular archive member found')


if __name__ == '__main__':
    run()
