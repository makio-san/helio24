"""Validation helpers for immutable SWAN-SF-V2 source identities."""
from urllib.parse import urlsplit

EXPECTED_PARTITIONS = {1, 2, 3, 4}
EXPECTED_HOST = 'dmlab.cs.gsu.edu'


def validate_manifest(manifest, *, require_hashes=False):
    errors = []
    archives = manifest.get('archives', [])
    partitions = [item.get('partition') for item in archives]
    if len(archives) != 4 or set(partitions) != EXPECTED_PARTITIONS or len(partitions) != len(set(partitions)):
        errors.append('exactly one archive is required for each partition 1-4')
    for item in archives:
        parts = urlsplit(item.get('url', ''))
        expected_name = f'swan-mvts-part{item.get("partition")}.tar.gz'
        if parts.scheme != 'https' or parts.hostname != EXPECTED_HOST or not parts.path.endswith('/'+expected_name):
            errors.append(f'invalid archive URL for partition {item.get("partition")}')
        if not isinstance(item.get('content_length'), int) or item.get('content_length', 0) <= 0:
            errors.append(f'invalid content length for partition {item.get("partition")}')
        if not item.get('etag') or not item.get('last_modified'):
            errors.append(f'missing HTTP identity for partition {item.get("partition")}')
        digest = item.get('sha256')
        if digest is not None and (not isinstance(digest, str) or len(digest) != 64
                                   or any(char not in '0123456789abcdef' for char in digest)):
            errors.append(f'invalid SHA-256 for partition {item.get("partition")}')
        if require_hashes and digest is None:
            errors.append(f'missing SHA-256 for partition {item.get("partition")}')
    return errors
