import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_operating_point_v2_is_a_target_redefinition_not_an_improvement():
    config = json.loads((ROOT / 'config/operating-point-v2.json').read_text())
    assert 'recall 0.90' in config['decision']
    assert 'Not a performance improvement' in config['what_this_is_not']
    assert 'not changed' in config['operational_scope']
    assert config['reserved_test_accessed'] is False
    expected = config['expected_development_performance_at_0.90']
    years = expected['years']
    for key in ['precision', 'delivered_recall', 'fp_windows', 'missed_positive_runs', 'missed_positive_runs_at_0.95']:
        assert len(expected[key]) == len(years), key
    assert all(a >= b for a, b in zip(expected['missed_positive_runs'], expected['missed_positive_runs_at_0.95']))


def test_decision_matches_the_frozen_review_artifact_when_present():
    artifact = ROOT / 'artifacts/operating_point_review_20261109_r1/curve.csv'
    if not artifact.exists():
        return
    import pandas as pd
    curve = pd.read_csv(artifact)
    config = json.loads((ROOT / 'config/operating-point-v2.json').read_text())
    expected = config['expected_development_performance_at_0.90']
    sub = curve[(curve.kind == 'deployable') & (curve.recall_target == 0.90)].set_index('year')
    for year, precision, fp, missed in zip(expected['years'], expected['precision'], expected['fp_windows'],
                                           expected['missed_positive_runs']):
        assert round(float(sub.loc[year, 'precision']), 4) == precision
        assert int(sub.loc[year, 'fp']) == fp and int(sub.loc[year, 'missed_positive_runs']) == missed
