import numpy as np

from scripts.audit_full_metrics import counts, ranking_metrics, threshold_metrics


def test_threshold_metrics_identities():
    y = np.array([1, 1, 0, 0, 0, 0, 1, 0])
    p = np.array([0.9, 0.2, 0.8, 0.1, 0.05, 0.3, 0.7, 0.01])
    m = threshold_metrics(y, p, 0.5)
    assert (m['tp'], m['fp'], m['fn'], m['tn']) == (2, 1, 1, 4)
    assert np.isclose(m['far'], 1-m['precision'])
    assert np.isclose(m['tss'], m['recall']-m['fpr'])
    assert np.isclose(m['balanced_accuracy'], (m['recall']+(1-m['fpr']))/2)
    assert np.isclose(m['accuracy'], 6/8)
    assert np.isclose(m['always_negative_accuracy'], 5/8)
    assert np.isclose(m['f1'], 2*m['precision']*m['recall']/(m['precision']+m['recall']))


def test_counts_and_ranking():
    y = np.array([1, 0, 1, 0])
    assert counts(y, np.array([True, True, False, False])) == (1, 1, 1, 1)
    r = ranking_metrics(y, np.array([0.9, 0.1, 0.8, 0.2]))
    assert r['roc_auc'] == 1.0 and r['ap'] == 1.0 and r['prevalence'] == 0.5
