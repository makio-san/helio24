import tarfile

from helio24 import v2_archive


def test_partition_scan_retries_an_incomplete_transfer(monkeypatch):
    calls = []

    def stream(item, handler, *, temporary_root, opener):
        calls.append(item['partition'])
        if len(calls) == 1:
            raise tarfile.ReadError('unexpected end of data')
        return {'partition': item['partition'], 'members': 0, 'results': []}

    monkeypatch.setattr(v2_archive, 'stream_verified_archive', stream)
    result = v2_archive.stream_verified_archive_with_retries(
        {'partition': 2}, lambda *args: None, attempts=2)
    assert result['partition'] == 2
    assert calls == [2, 2]
