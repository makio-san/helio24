"""Verified streaming access to V2 tar archives without path extraction."""
import hashlib
from pathlib import Path
import tarfile
import tempfile
from urllib.error import URLError
from urllib.request import Request, urlopen

CHUNK = 4*1024*1024
MAX_MEMBER = 2*1024*1024*1024


class IncompleteArchiveError(ValueError):
    """The server closed an otherwise valid immutable transfer too early."""


def stream_verified_archive(item, handle_member, *, temporary_root=None, opener=urlopen):
    """Call ``handle_member`` for each Parquet member, then verify full bytes."""
    request = Request(item['url'], headers={'Accept-Encoding': 'identity',
                                            'User-Agent': 'Helio24-development-audit/1'})
    results, names = [], set()
    with tempfile.TemporaryDirectory(dir=temporary_root) as directory:
        archive_path = Path(directory) / 'archive.tar.gz'
        digest, received = hashlib.sha256(), 0
        with opener(request, timeout=120) as response, archive_path.open('wb') as target:
            if response.status != 200:
                raise ValueError('Expected HTTP 200')
            length = int(response.headers['Content-Length'])
            etag = response.headers.get('ETag', '').strip('"')
            if length != item['content_length'] or etag != item['etag']:
                raise ValueError('Remote archive identity changed')
            while chunk := response.read(CHUNK):
                received += len(chunk)
                if received > item['content_length']:
                    raise ValueError('Oversized compressed archive')
                digest.update(chunk)
                target.write(chunk)
        if received != item['content_length']:
            raise IncompleteArchiveError('Incomplete compressed archive')
        if digest.hexdigest() != item['sha256']:
            raise ValueError('Compressed archive SHA-256 mismatch')
        with archive_path.open('rb') as archive_source:
            destination = Path(directory) / 'member.parquet'
            with tarfile.open(fileobj=archive_source, mode='r|gz') as archive:
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
    return {'partition': item['partition'], 'members': len(names),
            'compressed_bytes': received, 'sha256': digest.hexdigest(),
            'results': results}


def stream_verified_archive_with_retries(item, handle_member, *, temporary_root=None,
                                         attempts=3, opener=urlopen):
    """Restart interrupted immutable archive transfers from byte zero."""
    for attempt in range(1, attempts+1):
        try:
            return stream_verified_archive(item, handle_member,
                                           temporary_root=temporary_root, opener=opener)
        except (IncompleteArchiveError, tarfile.ReadError, URLError, TimeoutError,
                ConnectionError, OSError):
            if attempt == attempts:
                raise
            print(f'partition {item["partition"]}: transfer attempt {attempt} failed; retrying',
                  flush=True)
