import json
import shutil

import pandas as pd
import pytest

from helio24.events import alarm_episodes, match_events
from helio24.sensitivity import assert_reference, build_mapping, compare, load_sensitivity


@pytest.fixture
def evidence():
    windows, _ = alarm_episodes(pd.DataFrame([
        dict(harp=harp, forecast_time=pd.Timestamp('2014-01-01'),
             prediction_end=pd.Timestamp('2014-01-02'), probability=probability,
             target=0, missing_fraction=0.) for harp, probability in [(10, .8), (20, .1)]]), .5)
    catalog = pd.DataFrame([dict(flare_id=i, goes_class='M1.0', start_time='2014-01-01 12:05',
                                 peak_time='2014-01-01 12:11') for i in range(1, 5)])
    annotations = pd.DataFrame([
        dict(flare_id=i, harp=harp, magnitude='M1.0', verification=verification, source=source,
             timestamp=f'2014-01-01 12:{minute:02d}') for i, harp, source, minute, verification in [
            (1, 10, 'MFLARE_LABEL_LOC', 0, 'Primary'),
            (2, 20, 'MFLARE_LABEL_LOC', 6, 'Secondary'),
            (3, 10, 'MFLARE_LABEL', 6, 'Primary'),
            (3, 20, 'MFLARE_LABEL_LOC', 6, 'Primary'),
            (4, 20, 'MFLARE_LABEL_LOC', 6, 'Non-verified')]])
    filenames = pd.DataFrame([dict(flare_id=i, harp=10, target=1, label=f'M1.0@{i}:Primary',
                                   forecast_time='2014-01-01', prediction_end='2014-01-02') for i in [2, 4]])
    return windows, annotations, filenames, catalog


def test_timing_ambiguity_common_denominator_and_input_immutability(evidence):
    original = [x.copy(deep=True) for x in evidence]
    result = compare(*evidence)
    events = result['events'].set_index(['variant', 'flare_id'])
    assert events.loc[('nearest_location', 1), 'status'] == 'unmapped'
    assert events.loc[('containing_location', 1), 'status'] == 'evaluated'
    # Filename evidence does not override a conflicting verified history HARP.
    assert events.loc[('nearest_location', 2), 'status'] == 'ambiguous'
    assert events.loc[('nearest_noaa', 2), 'detected']
    # Same event ID on different HARPs must not enter the common denominator.
    assert events.loc[('nearest_noaa', 3), 'detected']
    assert not events.loc[('nearest_location', 3), 'detected']
    assert events.loc[('nearest_union', 3), 'status'] == 'ambiguous'
    assert set(result['events'].query('common_same_harp').flare_id) == {4}
    assert result['metrics'].common_events.eq(1).all()
    assert result['metrics'].common_recall.eq(1.).all()
    assert not result['conflicts'].query("variant == 'nearest_location'").flare_id.eq(2).any()
    assert result['transitions'].query("variant == 'nearest_noaa' and flare_id == 3").changed.all()
    for before, after in zip(original, evidence):
        pd.testing.assert_frame_equal(before, after)


def test_invalid_catalog_and_reference_fail_closed(evidence):
    windows, annotations, filenames, catalog = evidence
    bad = catalog.copy()
    bad.loc[bad.flare_id == 2, 'goes_class'] = 'X1.0'
    with pytest.raises(ValueError, match='Catalog mismatch'):
        build_mapping(annotations, filenames, bad, 'nearest', 'location')
    mapping = build_mapping(annotations, filenames, catalog, 'nearest', 'location')
    reference = match_events(windows, mapping, catalog)
    results = compare(*evidence)
    assert_reference(results['events'], reference)
    reference.loc[reference.flare_id == 4, 'detected'] = False
    with pytest.raises(AssertionError):
        assert_reference(results['events'], reference)


def test_no_events_evaluated_produces_missing_recall(evidence):
    windows, annotations, filenames, catalog = evidence
    result = compare(windows, annotations.iloc[:0], filenames.iloc[:0], catalog)
    assert result['metrics'].evaluated.eq(0).all()
    assert result['metrics'].recall.isna().all()
    assert result['metrics'].common_recall.isna().all()
    assert result['conflicts'].empty


def test_runner_preserves_inputs_refuses_overwrite_and_verifies_outputs(tmp_path, evidence, capsys):
    from helio24.data import ROOT
    from helio24.full_data import sha256
    from scripts.run_label_sensitivity import run

    windows, annotations, filenames, catalog = evidence
    audit = tmp_path / 'artifacts/event_audit'
    provenance = tmp_path / 'artifacts/event_provenance'
    for directory in [audit, provenance, tmp_path / 'data']:
        directory.mkdir(parents=True)
    code_paths = ['helio24/sensitivity.py', 'helio24/events.py', 'helio24/event_mapping.py',
                  'scripts/run_label_sensitivity.py', 'docs/label-sensitivity-protocol.md']
    for name in code_paths:
        (tmp_path / name).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, tmp_path / name)
    catalog.to_csv(tmp_path / 'data/flare_catalog.csv', index=False)
    annotations.to_csv(provenance / 'annotations.csv', index=False)
    filenames.to_csv(provenance / 'filenames.csv', index=False)
    windows.to_parquet(audit / 'windows.parquet', index=False)
    mapping = build_mapping(annotations, filenames, catalog, 'nearest', 'location')
    match_events(windows, mapping, catalog).to_csv(audit / 'events.csv', index=False)
    for directory in [audit, provenance]:
        report = dict(source_hashes={'data/flare_catalog.csv': sha256(tmp_path / 'data/flare_catalog.csv')},
                      code_hashes={}, artifact_hashes={p.name: sha256(p) for p in directory.iterdir()},
                      threshold=.5, false_alarm_region_hours=1.)
        (directory / 'report.json').write_text(json.dumps(report))
    before = {str(p): sha256(p) for d in [audit, provenance] for p in d.iterdir()}
    run(tmp_path)
    report, metrics, _ = load_sensitivity(tmp_path)
    assert len(metrics) == 6
    assert report['reference_reproduced']
    assert all(sha256(p) == digest for p, digest in before.items())
    with pytest.raises(RuntimeError, match='Preserve'):
        run(tmp_path)
    (tmp_path / 'artifacts/label_sensitivity/metrics.csv').write_text('changed')
    with pytest.raises(ValueError, match='input changed'):
        load_sensitivity(tmp_path)
