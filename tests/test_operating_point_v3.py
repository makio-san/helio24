import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def test_operating_point_v3_is_a_frozen_proposal_with_the_measured_numbers():
    config = json.loads((ROOT/'config/operating-point-v3.json').read_text())
    assert config['status'].startswith('proposal_frozen') and config['status'].endswith('not_adopted')
    assert config['reserved_test_accessed'] is False
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
