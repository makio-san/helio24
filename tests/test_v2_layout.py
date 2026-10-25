import tarfile

from scripts import audit_v2_layout


def test_partition_scan_retries_an_incomplete_transfer(monkeypatch):
    calls = []

    def stream(item, handler, *, temporary_root):
        calls.append(item['partition'])
        if len(calls) == 1:
            raise tarfile.ReadError('unexpected end of data')
        return {'partition': item['partition'], 'members': 0, 'results': []}

    monkeypatch.setattr(audit_v2_layout, 'stream_verified_archive', stream)
    result = audit_v2_layout.scan_partition({'partition': 2}, None, {}, attempts=2)
    assert result['partition'] == 2
    assert calls == [2, 2]
