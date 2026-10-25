import copy
import json
from pathlib import Path

from helio24.v2_sources import validate_manifest

ROOT = Path(__file__).resolve().parents[1]


def manifest():
    return json.loads((ROOT / 'config/swan_sf_v2_sources.json').read_text())


def test_pending_source_manifest_has_valid_remote_identities():
    spec = manifest()
    assert validate_manifest(spec) == []
    errors = validate_manifest(spec, require_hashes=True)
    assert len(errors) == 4
    assert all('missing SHA-256' in error for error in errors)


def test_source_manifest_rejects_wrong_host_partition_and_digest():
    spec = copy.deepcopy(manifest())
    spec['archives'][0]['url'] = 'https://example.com/swan-mvts-part1.tar.gz'
    spec['archives'][1]['partition'] = 1
    spec['archives'][2]['sha256'] = 'not-a-digest'
    errors = validate_manifest(spec)
    assert any('partition 1-4' in error for error in errors)
    assert any('invalid archive URL' in error for error in errors)
    assert any('invalid SHA-256' in error for error in errors)
