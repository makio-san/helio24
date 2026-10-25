"""Verified streaming access to V2 tar archives without path extraction."""
import hashlib
from pathlib import Path
import tarfile
import tempfile
from urllib.error import URLError
from urllib.request import Request, urlopen

CHUNK = 4*1024*1024
MAX_MEMBER = 2*1024*1024*1024


class HashingReader:
    def __init__(self, source):
        self.source = source
        self.digest = hashlib.sha256()
        self.count = 0

    def read(self, size=-1):
        chunk = self.source.read(size)
        self.digest.update(chunk)
        self.count += len(chunk)
        return chunk


def stream_verified_archive(item, handle_member, *, temporary_root=None, opener=urlopen):
    """Call ``handle_member`` for each Parquet member, then verify full bytes."""
    request = Request(item['url'], headers={'Accept-Encoding': 'identity',
                                            'User-Agent': 'Helio24-development-audit/1'})
    results, names = [], set()
    with opener(request, timeout=120) as response:
        if response.status != 200:
            raise ValueError('Expected HTTP 200')
        length = int(response.headers['Content-Length'])
        etag = response.headers.get('ETag', '').strip('"')
        if length != item['content_length'] or etag != item['etag']:
            raise ValueError('Remote archive identity changed')
        reader = HashingReader(response)
        with tempfile.TemporaryDirectory(dir=temporary_root) as directory:
            destination = Path(directory) / 'member.parquet'
            with tarfile.open(fileobj=reader, mode='r|gz') as archive:
                for member in archive:
                    if member.isdir():
                        continue
                    if member.isfile() and Path(member.name).name == '_SUCCESS' and member.size == 0:
                        continue
                    if not member.isfile() or not member.name.endswith('.parquet'):
                        raise ValueError(f'Unexpected archive member: {member.name}')
                    if member.name in names or not 0 < member.size <= MAX_MEMBER:
                        raise ValueError('Duplicate, empty or oversized Parquet member')
                    names.add(member.name)
                    copied = 0
                    with archive.extractfile(member) as source, destination.open('wb') as target:
                        while chunk := source.read(CHUNK):
                            copied += len(chunk)
                            if copied > member.size:
                                raise ValueError('Parquet member exceeds declared size')
                            target.write(chunk)
                    if copied != member.size:
                        raise ValueError('Incomplete Parquet member')
                    results.append(handle_member(destination, member.name, member.size))
            while reader.read(CHUNK):
                pass
    if reader.count != item['content_length']:
        raise ValueError('Incomplete compressed archive')
    if reader.digest.hexdigest() != item['sha256']:
        raise ValueError('Compressed archive SHA-256 mismatch')
    return {'partition': item['partition'], 'members': len(names),
            'compressed_bytes': reader.count, 'sha256': reader.digest.hexdigest(),
            'results': results}


def stream_verified_archive_with_retries(item, handle_member, *, temporary_root=None,
                                         attempts=3, opener=urlopen):
    """Restart interrupted immutable archive transfers from byte zero."""
    for attempt in range(1, attempts+1):
        try:
            return stream_verified_archive(item, handle_member,
                                           temporary_root=temporary_root, opener=opener)
        except (tarfile.ReadError, URLError, TimeoutError, ConnectionError, OSError):
            if attempt == attempts:
                raise
            print(f'partition {item["partition"]}: transfer attempt {attempt} failed; retrying',
                  flush=True)
