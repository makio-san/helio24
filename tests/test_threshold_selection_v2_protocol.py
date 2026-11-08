import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    return json.loads((ROOT / 'config' / name).read_text())


def test_v2_keeps_v1_rules_and_closed_budget():
    v1, v2 = load('threshold-selection-v1.json'), load('threshold-selection-v2.json')
    for key in ['candidates', 'budget', 'years', 'positive_years', 'acceptance', 'inference']:
        assert v2[key] == v1[key], key
    assert v2['selection'].startswith('Identical to threshold-selection-v1')
    assert 'recall_threshold' in v2['selection'] and 'fewest calibration false-alarm windows' in v2['selection']
    rule = ['id', 'basis', 'target']
    assert {k: v2['control'][k] for k in rule} == {k: v1['control'][k] for k in rule}
    assert v2['budget']['model_fits'] == 0
    assert v2['budget']['evaluation_label_use_in_selection'] == 0


def test_v2_gate_is_label_free_and_has_no_fallback():
    config = load('threshold-selection-v2.json')
    steps = config['baseline_gate']['steps']
    assert [step[:2] for step in steps] == ['G1', 'G2', 'G3', 'G4']
    assert 'Label-free' in steps[3]
    failure = config['baseline_gate']['failure']
    assert 'No fallback' in failure and 'no retraining' in failure
    assert any('fallback' in item for item in config['prohibitions'])
    assert any('2024-2025' in item for item in config['prohibitions'])
    assert 'ensemble' in config['arm']['definition']
    assert config['evidence']['shard_count'] == 20


def test_v2_evidence_hashes_are_pinned_and_v1_stays_unchanged():
    config = load('threshold-selection-v2.json')
    for key, value in config['evidence'].items():
        if key.endswith('_sha256'):
            assert len(value) == 64 and set(value) <= set('0123456789abcdef'), key
    assert config['evidence']['frozen_shards_report_sha256'] == \
        '62a64b3d94b9f7ec1624e5596fc86e636922a0e696968259b55ff0c8739c5f82'
    assert load('threshold-selection-v1.json')['id'] == 'threshold-selection-v1'
