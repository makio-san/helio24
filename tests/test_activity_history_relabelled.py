import json
from pathlib import Path

import numpy as np
import pandas as pd

from scripts.audit_activity_history_relabelled import acceptance, paired_precision_bootstrap, precision_at_recall, read

ROOT = Path(__file__).resolve().parents[1]


def test_precision_at_recall_matches_the_ranking():
    target = np.array([1, 0, 1, 0, 0])
    probability = np.array([.9, .8, .7, .6, .1])
    assert precision_at_recall(target, probability, 0.5) == 1.0
    assert np.isclose(precision_at_recall(target, probability, 1.0), 2/3)


def test_acceptance_needs_precision_gain_without_losing_runs_or_recall():
    control = dict(precision=.4, recall=.5, missed_positive_runs=3)
    assert all(acceptance(dict(precision=.5, recall=.49, missed_positive_runs=3), control, .02).values())
    assert not acceptance(dict(precision=.4, recall=.6, missed_positive_runs=2), control, .02)['precision_higher_than_control']
    assert not acceptance(dict(precision=.6, recall=.47, missed_positive_runs=3), control, .02)['window_recall_drop_within_tolerance']
    assert not acceptance(dict(precision=.6, recall=.5, missed_positive_runs=4), control, .02)['missed_positive_runs_not_above_control']


def test_paired_bootstrap_is_zero_for_identical_alarms_and_positive_for_fewer_false_alarms():
    frame = pd.DataFrame({'harp': np.repeat(np.arange(20), 4), 'target': np.tile([1, 0, 0, 0], 20)})
    control = np.tile([True, True, True, False], 20)
    same = paired_precision_bootstrap(frame, control, control)
    assert same['lower'] == same['upper'] == 0.0
    better = paired_precision_bootstrap(frame, control, np.tile([True, True, False, False], 20))
    assert better['lower'] > 0


def test_reading_follows_the_frozen_rule():
    passing = dict(all_year_primary=False, cycle25_primary=True, cycle25_bootstrap_lower_above_zero=True)
    failing = dict(all_year_primary=False, cycle25_primary=True, cycle25_bootstrap_lower_above_zero=False)
    assert read({'history': passing, 'flag': failing}) == 'R1_history_helps'
    assert read({'history': passing, 'flag': passing}) == 'R2_refit_only'
    assert read({'history': failing, 'flag': passing}) == 'R3_no_gain'


def test_protocol_v2_keeps_features_and_moves_to_the_adopted_basis():
    v1 = json.loads((ROOT/'config/activity-history-v1.json').read_text())
    v2 = json.loads((ROOT/'config/activity-history-v2.json').read_text())
    pipeline = json.loads((ROOT/'config/walk-forward-v2.json').read_text())
    assert v2['status'] == 'frozen_before_any_candidate_result' and v2['reserved_test_accessed'] is False
    assert v2['years'] == v1['years'] and v2['budget'] == v1['budget']
    assert [c['id'] for c in v2['candidates']] == [c['id'] for c in v1['candidates']]
    assert v2['evidence']['table'] == pipeline['source'] and v2['evidence']['table_report_sha256'] == pipeline['source_sha256']
    assert v2['evidence']['sgas_directory'] == v1['evidence']['sgas_directory']
    assert v2['acceptance']['tier'] == 'alert' and set(v2['reading']) == {'R1_history_helps', 'R2_refit_only', 'R3_no_gain'}
