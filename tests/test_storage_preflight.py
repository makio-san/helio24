from pathlib import Path
from types import SimpleNamespace

from helio24 import storage_preflight


def test_local_files_and_missing_inputs(tmp_path):
    (tmp_path/'present').write_text('data')
    result = storage_preflight.inspect_storage([tmp_path, tmp_path/'absent'])
    assert not result['available']
    assert result['files_checked'] == 1
    assert result['blockers'] == [{'path': str(tmp_path/'absent'), 'reason': 'missing'}]
    assert result['integrity_verified'] is False


def test_placeholder_detection_never_reads_contents(tmp_path, monkeypatch):
    path = tmp_path/'cloud.npy'
    path.touch()
    original = Path.stat

    def metadata(self, *args, **kwargs):
        if self == path:
            return SimpleNamespace(st_flags=storage_preflight.SF_DATALESS, st_size=4096, st_mode=0o100644)
        return original(self, *args, **kwargs)

    def no_read(*args, **kwargs):
        raise AssertionError('Preflight must not read placeholder contents')

    monkeypatch.setattr(Path, 'stat', metadata)
    monkeypatch.setattr(Path, 'read_bytes', no_read)
    monkeypatch.setattr(Path, 'read_text', no_read)
    result = storage_preflight.inspect_storage([path, path])
    assert storage_preflight.is_placeholder(path)
    assert result['files_checked'] == 1
    assert result['placeholder_bytes'] == 4096
    assert result['blockers'][0]['reason'] == 'cloud_placeholder'


def test_metadata_permission_failure_is_not_reported_as_available(tmp_path, monkeypatch):
    def denied(*args, **kwargs):
        raise PermissionError('not accessible')
    monkeypatch.setattr(Path, 'stat', denied)
    result = storage_preflight.inspect_storage([tmp_path])
    assert not result['available']
    assert result['blockers'][0]['reason'] == 'inaccessible'
