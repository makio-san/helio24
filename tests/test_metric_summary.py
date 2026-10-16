import pytest

from helio24.metric_summary import enrich
from helio24.modeling import metrics


def test_derived_metrics_use_confusion_counts_without_mutation():
    saved = metrics([1, 1, 0, 0, 0], [.9, .2, .8, .1, .1], .5)
    result = enrich(saved)
    assert result['accuracy'] == pytest.approx(.6)
    assert result['f1'] == pytest.approx(.5)
    assert result['balanced_accuracy'] == pytest.approx((.5+2/3)/2)
    assert result['always_quiet_accuracy'] == pytest.approx(.6)
    assert 'accuracy' not in saved
    for key in ['n', 'positives', 'alarms', 'recall', 'precision', 'tss']:
        bad = dict(saved)
        bad[key] += 1
        with pytest.raises(ValueError):
            enrich(bad)


def test_undefined_scores_are_not_fabricated():
    row = enrich(metrics([1, 0], [.1, .1], .5))
    assert not row['precision_defined']
    assert row['precision'] == 0  # Preserve the saved implementation's convention.
    assert row['recall_defined']
    assert row['f1'] == 0
    row = enrich(metrics([0, 0], [.1, .1], .5))
    assert row['balanced_accuracy'] is None
    assert row['f1'] is None
    assert not row['recall_defined']


def test_saved_report_contains_all_operating_points_and_is_immutable():
    from helio24.data import ROOT
    from helio24.sensitivity import verify_report
    from scripts.report_metrics import run
    import pandas as pd
    directory = ROOT / 'artifacts/metrics_summary'
    if not (directory / 'report.json').exists():
        pytest.skip('Requires local report artifacts')
    report = verify_report(ROOT, directory, check_code=True)
    frame = pd.read_csv(directory / 'all_metrics.csv')
    assert len(frame) == report['rows'] == 50
    assert set(frame.experiment) == {'experiment1', 'experiment2', 'experiment3'}
    assert len(pd.read_csv(directory / 'headline_metrics.csv')) == 3
    assert 'data:image/png;base64,' in (directory / 'report.html').read_text()
    with pytest.raises(RuntimeError, match='Preserve'):
        run(ROOT)
