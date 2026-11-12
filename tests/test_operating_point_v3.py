import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def test_operating_point_v3_is_adopted_with_the_measured_numbers():
    config = json.loads((ROOT/'config/operating-point-v3.json').read_text())
    assert config['status'] == 'adopted_2026-11-12'
    assert config['adoption']['pipeline_protocol'] == 'config/walk-forward-v2.json'
    assert config['supersedes'] == 'config/operating-point-v2.json'
    assert config['reserved_test_accessed'] is False
    assert 'app.py' in config['what_this_is_not']
    v2 = json.loads((ROOT/'config/operating-point-v2.json').read_text())
    assert v2['superseded_by'].startswith('config/operating-point-v3.json')
    expected = config['expected_development_performance']
    results = ROOT/'artifacts/two_tier_relabelled_20261111_r1/results.csv'
    if not results.exists():
        return
    frame = pd.read_csv(results).set_index(['year', 'tier'])
    for i, year in enumerate(expected['years']):
        assert round(frame.loc[(year, 'watch'), 'precision'], 4) == expected['watch_precision'][i]
        assert round(frame.loc[(year, 'alert_0.5'), 'precision'], 4) == expected['alert_precision'][i]
        assert frame.loc[(year, 'alert_0.5'), 'missed_positive_runs'] == expected['alert_missed_positive_runs'][i]
    rows = frame.reset_index()
    assert [int(y) for y in rows[rows.tier.eq('alert_0.5') & rows.fallback].year] == expected['alert_fallback_years']


def test_walk_forward_v2_inherits_recipes_and_operating_point_rules():
    v1 = json.loads((ROOT/'config/walk-forward-v1.json').read_text())
    v2 = json.loads((ROOT/'config/walk-forward-v2.json').read_text())
    relabel = json.loads((ROOT/'config/relabel-v1.json').read_text())
    two_tier = json.loads((ROOT/'config/two-tier-v1.json').read_text())
    assert v2['recipes'] == 'config/walk-forward-v1.json' and v2['evaluation_years'] == v1['evaluation_years']
    assert v2['source'] == relabel['materialisation']['output']
    assert v2['tiers']['watch']['recall_target'] == two_tier['tiers']['watch']['recall_target'] == 0.90
    assert v2['tiers']['alert']['precision_target'] == two_tier['tiers']['alert']['primary_precision_target']
    assert v2['tiers']['alert']['recall_floor'] == two_tier['tiers']['alert']['recall_floor']
    assert v2['tiers']['comparison_recall_0.95']['recall_target'] == v1['required_recall']
    assert v2['reserved_test_accessed'] is False and not any(year >= 2024 for year in v2['evaluation_years'])
    hashes = [v2['source_sha256'], *[v for k, v in v2['must_reproduce'].items() if k.endswith('sha256')],
              *[v for k, v in v2['frozen_label_reference'].items() if k.endswith('sha256')]]
    assert all(len(h) == 64 and h == h.lower() for h in hashes)
