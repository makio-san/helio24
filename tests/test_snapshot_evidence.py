import json
from pathlib import Path

import pytest

from scripts.snapshot_evidence import digest, snapshot


def test_snapshot_preserves_verified_bytes_and_records_missing(tmp_path):
    root = tmp_path/'project'
    source = root/'experiment'
    source.mkdir(parents=True)
    (source/'result.bin').write_bytes(b'frozen evidence')
    (source/'report.json').write_text(json.dumps({'artifact_hashes':{
        'result.bin':digest(source/'result.bin'), 'lost.bin':'0'*64}}))
    output = tmp_path/'backup'
    result = snapshot(root, ['experiment'], output)
    assert not result['complete']
    assert result['unavailable'] == [{'path':'experiment/lost.bin', 'reason':'missing'}]
    assert (output/'experiment/result.bin').read_bytes() == b'frozen evidence'
    assert not (output/'experiment/result.bin').stat().st_mode & 0o222
    with pytest.raises(FileExistsError):
        snapshot(root, ['experiment'], output)


def test_snapshot_rejects_modified_frozen_evidence(tmp_path):
    root = tmp_path/'project'
    source = root/'experiment'
    source.mkdir(parents=True)
    (source/'result.bin').write_bytes(b'changed')
    (source/'report.json').write_text(json.dumps({'artifact_hashes':{'result.bin':'0'*64}}))
    with pytest.raises(ValueError, match='hash mismatch'):
        snapshot(root, ['experiment'], tmp_path/'backup')
    assert not (tmp_path/'backup/snapshot.json').exists()


def test_snapshot_rejects_cloud_destination_and_source_escape(tmp_path):
    with pytest.raises(ValueError, match='outside iCloud'):
        snapshot(tmp_path, [], Path.home()/'Desktop/forbidden-backup')
    with pytest.raises(ValueError, match='Invalid source'):
        snapshot(tmp_path, ['..'], tmp_path/'backup')
