import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_frozen_selection_protocol_uses_only_calibration_data_and_closed_budget():
    config = json.loads((ROOT / 'config/threshold-selection-v1.json').read_text())
    assert [c['id'] for c in config['candidates']] == ['w93', 'w90', 'run95', 'run90']
    assert config['control']['target'] == 0.95
    assert config['budget'] == {'candidate_rules': 4, 'model_fits': 0, 'other_targets': 0,
                                'evaluation_label_use_in_selection': 0}
    assert set(config['positive_years']) == set(config['years']) - {2018}
    assert 'No evaluation labels' in config['prohibitions'][0]
    assert any('2024-2025' in item for item in config['prohibitions'])
    assert config['acceptance']['per_year_primary']['window_recall_drop_at_most'] == 0.02
