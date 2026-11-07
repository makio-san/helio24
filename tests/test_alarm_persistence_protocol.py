import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_frozen_protocol_limits_candidates_and_keeps_test_closed():
    config = json.loads((ROOT / 'config/alarm-persistence-v1.json').read_text())
    assert [c['k'] for c in config['candidates']] == [1, 3, 6]
    assert config['budget'] == {'candidate_rules': 2, 'model_fits': 0, 'threshold_changes': 0, 'other_k_values': 0}
    assert config['years'] == [2014, 2015, 2016, 2017, 2018, 2022, 2023]
    assert set(config['positive_years']) == set(config['years']) - {2018}
    assert any('2024-2025' in item for item in config['prohibitions'])
    assert config['acceptance']['per_year_primary']['window_recall_drop_at_most'] == 0.02
