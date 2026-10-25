from io import BytesIO
import tarfile

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from helio24.v2_archive import stream_verified_archive


class Response(BytesIO):
    status = 200

    def __init__(self, payload, etag):
        super().__init__(payload)
        self.headers = {'Content-Length': str(len(payload)), 'ETag': '"'+etag+'"'}

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def archive_bytes(tmp_path):
    parquet = tmp_path / 'sample.parquet'
    pq.write_table(pa.table({'harp_number': [1], 'obs_start': [pd.Timestamp('2023-01-01')]}), parquet)
    stream = BytesIO()
    with tarfile.open(fileobj=stream, mode='w:gz') as archive:
        archive.add(parquet, arcname='part/sample.parquet')
        marker = tarfile.TarInfo('part/_SUCCESS')
        marker.size = 0
        archive.addfile(marker, BytesIO())
    return stream.getvalue()


def test_verified_archive_uses_fixed_temporary_path_and_checks_full_hash(tmp_path):
    payload = archive_bytes(tmp_path)
    import hashlib
    item = {'partition': 1, 'url': 'https://example.test/archive.tar.gz',
            'content_length': len(payload), 'etag': 'frozen',
            'sha256': hashlib.sha256(payload).hexdigest()}
    seen = []
    result = stream_verified_archive(
        item, lambda path, name, size: seen.append((path.name, name, size)),
        temporary_root=tmp_path, opener=lambda request, timeout: Response(payload, 'frozen'))
    assert result['members'] == 1
    assert seen[0][0] == 'member.parquet'
    assert seen[0][1] == 'part/sample.parquet'
    bad = item | {'sha256': '0'*64}
    with pytest.raises(ValueError, match='SHA-256'):
        stream_verified_archive(bad, lambda *args: None, temporary_root=tmp_path,
                                opener=lambda request, timeout: Response(payload, 'frozen'))
