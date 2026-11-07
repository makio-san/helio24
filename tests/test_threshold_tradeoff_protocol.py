import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_frozen_threshold_protocol_limits_candidates_and_keeps_test_closed():
    config = json.loads((ROOT / 'config/threshold-tradeoff-v1.json').read_text())
    assert config['deployable_candidates']['multipliers'] == [1.25, 1.5, 2.0]
    assert config['deployable_candidates']['budget'] == {'candidate_rules': 3, 'model_fits': 0, 'other_multipliers': 0}
    assert set(config['positive_years']) == set(config['years']) - {2018}
    assert 'not deployable' in config['oracle_references']['nature']
    assert any('2024-2025' in item for item in config['prohibitions'])
    persistence = json.loads((ROOT / config['evidence']['persistence_config']).read_text())
    assert persistence['evidence']['predictions_report_sha256'] == config['evidence']['predictions_report_sha256']
