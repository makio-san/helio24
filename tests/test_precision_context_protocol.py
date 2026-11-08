import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load():
    return json.loads((ROOT / 'config/precision-context-v1.json').read_text())


def test_candidates_budget_and_zero_stage_one_fits():
    config = load()
    assert [c['id'] for c in config['candidates']] == ['control', 'recal', 'context']
    assert 'Zero stage-one fits' in config['stage_one']
    assert '84 small logistic fits' in config['stage_two']['fits']
    assert 'No search' in config['stage_two']['model']


def test_context_is_causal_and_catalog_free():
    config = load()
    source = config['context_features']['source']
    assert 'strictly before' in source and 'No labels' in source and 'no other HARPs' in source
    assert 'never assumed quiet' in config['context_features']['missing_history']
    assert any('No external flare catalog' in item for item in config['prohibitions'])
    assert any('No evaluation labels' in item for item in config['prohibitions'])
    assert any('2024-2025' in item for item in config['prohibitions'])


def test_acceptance_matches_project_rules_and_threshold_order():
    config = load()
    rules = config['acceptance']['per_year_primary']
    assert rules['window_recall_drop_at_most'] == 0.02
    assert set(config['positive_years']) == set(config['years']) - {2018}
    assert 'before any evaluation label is read' in config['order_of_operations']
    assert 'precision 0.30' in config['acceptance']['target_distance']
    assert 'recal' in config['acceptance']['attribution']
