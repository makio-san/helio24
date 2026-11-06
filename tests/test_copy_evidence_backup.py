import pytest
from scripts.copy_evidence_backup import copy_backup


def test_internal_destination_is_rejected_before_copy(tmp_path):
    source = tmp_path/'source'
    source.mkdir()
    with pytest.raises(ValueError, match='external disk'):
        copy_backup(source, tmp_path/'backup')
    assert not (tmp_path/'backup').exists()


def test_existing_backup_cannot_be_overwritten(tmp_path):
    source = tmp_path/'source'
    target = tmp_path/'backup'
    source.mkdir()
    target.mkdir()
    with pytest.raises(FileExistsError):
        copy_backup(source, target)
