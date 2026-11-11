import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_two_tier_v2_inherits_every_rule_of_v1_unchanged():
    v1 = json.loads((ROOT/'config/two-tier-v1.json').read_text())
    v2 = json.loads((ROOT/'config/two-tier-v2.json').read_text())
    assert v2['status'] == 'frozen_before_any_result' and v2['reserved_test_accessed'] is False
    for key in ['recall_target']:
        assert v2['tiers']['watch'][key] == v1['tiers']['watch'][key]
    for key in ['precision_targets', 'primary_precision_target', 'recall_floor']:
        assert v2['tiers']['alert'][key] == v1['tiers']['alert'][key]
    assert v2['years'] == v1['years'] and v2['reported_per_tier_and_year'] == v1['reported_per_tier_and_year']
    assert 'No new precision targets, recall floors or tie rules' in v2['prohibitions']
    assert not any(value.endswith('_SHA256') for value in v2['evidence'].values() if isinstance(value, str) and value.isupper())
