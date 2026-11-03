import json
from pathlib import Path

import pytest

from helio24 import temporal_storage


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


@pytest.fixture
def inputs(tmp_path):
    root = tmp_path
    run, cache = root/'run', root/'cache'
    protocol = {'runner_code_hashes': {'helio24/model.py': 'hash'},
                'direction': 'config/direction.json', 'base_protocol': 'config/base.json',
                'smoke': 'smoke/report.json', 'baseline_artifact': 'baseline',
                'short_control': 'short', 'arms': ['chronological'], 'seeds': [24]}
    write(root/'config/temporal-sequence-v2.json', protocol)
    for name in ['helio24/model.py', 'config/direction.json', 'config/base.json',
                 'smoke/report.json', 'baseline/report.json', 'short/report.json',
                 'baseline/2018/predictions.parquet', 'baseline/2018/thresholds.json',
                 'short/2018/predictions.parquet', 'short/2018/thresholds.json']:
        write(root/name, {})
    write(run/'prepared.json', {'artifact_hashes': {'2018/train.npy': 'hash'},
                                'folds': [{'year': 2018, 'status': 'complete'}]})
    write(run/'2018/train.npy', [])
    write(cache/'report.json', {'artifact_hashes': {'values.npy': 'hash'}})
    write(cache/'values.npy', [])
    return root, run, cache


def test_deleted_declared_input_blocks_resume_even_when_directory_exists(inputs):
    root, run, cache = inputs
    assert temporal_storage.inspect_temporal_inputs(*inputs)['available']
    (cache/'values.npy').unlink()
    result = temporal_storage.inspect_temporal_inputs(*inputs)
    assert not result['available']
    assert {'path': str(cache/'values.npy'), 'reason': 'missing'} in result['blockers']
    assert not result['integrity_verified']


def test_finished_fold_requires_every_saved_artifact_but_no_unused_reference(inputs):
    root, run, cache = inputs
    write(run/'2018/finished.json', {'artifact_hashes': {'chronological_seed24/checkpoint.pt': 'hash'}})
    (root/'baseline/2018/predictions.parquet').unlink()
    result = temporal_storage.inspect_temporal_inputs(*inputs)
    assert [b['path'] for b in result['blockers']] == [str(run/'2018/chronological_seed24/checkpoint.pt')]
    write(run/'2018/chronological_seed24/checkpoint.pt', {})
    assert temporal_storage.inspect_temporal_inputs(*inputs)['available']


def test_placeholder_manifest_is_not_opened(inputs, monkeypatch):
    root, run, cache = inputs
    path = cache/'report.json'
    original_inspect = temporal_storage.inspect_storage
    original_read = Path.read_text

    def inspect(paths):
        result = original_inspect(paths)
        if path in paths:
            result['available'] = False
            result['blockers'].append({'path': str(path), 'reason': 'cloud_placeholder'})
        return result

    def read(self, *args, **kwargs):
        assert self != path, 'Cloud manifest must not be opened'
        return original_read(self, *args, **kwargs)

    monkeypatch.setattr(temporal_storage, 'inspect_storage', inspect)
    monkeypatch.setattr(Path, 'read_text', read)
    assert not temporal_storage.inspect_temporal_inputs(*inputs)['available']


@pytest.mark.parametrize('record', ['broken JSON', {'artifact_hashes': {'../outside': 'hash'}}, []])
def test_invalid_or_escaping_manifest_fails_closed(inputs, record):
    _, _, cache = inputs
    (cache/'report.json').write_text(record if isinstance(record, str) else json.dumps(record))
    result = temporal_storage.inspect_temporal_inputs(*inputs)
    assert not result['available']
    assert any(b['reason'] == 'invalid_manifest' for b in result['blockers'])
