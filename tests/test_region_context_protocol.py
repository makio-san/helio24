import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load():
    return json.loads((ROOT / 'config/region-context-v1.json').read_text())


def test_candidates_budget_and_unchanged_recipes():
    config = load()
    assert [c['id'] for c in config['candidates']] == ['control', 'flag', 'context']
    assert config['budget'] == {'candidate_recipes': 2, 'years': 7, 'constituent_fits': 28,
                                'hyperparameter_search': 0, 'feature_sets_after_results': 0}
    assert len(config['context_features']) == 13
    assert 'unchanged' in config['training']


def test_availability_rule_is_causal_and_never_quiet():
    config = load()
    rule = config['availability_rule']
    assert 't - 30 minutes' in rule and 'never encoded as quiet' in rule
    assert any('No future SRS' in item for item in config['prohibitions'])
    assert any('No flare catalog' in item for item in config['prohibitions'])
    assert any('2024-2025' in item for item in config['prohibitions'])


def test_acceptance_and_attribution_match_project_rules():
    config = load()
    assert config['acceptance']['per_year_primary']['window_recall_drop_at_most'] == 0.02
    assert set(config['positive_years']) == set(config['years']) - {2018}
    assert 'flag' in config['acceptance']['attribution']
    assert 'before any evaluation label is read' in config['training']
