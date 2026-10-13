from pathlib import Path
import json

import pytest
from streamlit.testing.v1 import AppTest

from helio24 import data

ROOT = Path(__file__).resolve().parents[1]


def test_no_model_has_actionable_empty_state(monkeypatch, tmp_path):
    monkeypatch.setattr(data, 'ROOT', tmp_path)
    app = AppTest.from_file(str(ROOT / 'app.py'), default_timeout=30).run()
    assert not app.exception
    assert 'No evaluated model artifacts were found' in app.info[0].value
    assert len(app.metric) == 0


@pytest.mark.skipif(not (ROOT / 'artifacts/report.json').exists(), reason='Requires local real-data experiment')
def test_replay_and_validation_threshold_do_not_change_saved_test_metrics():
    app = AppTest.from_file(str(ROOT / 'app.py'), default_timeout=30).run()
    assert not app.exception
    fixed = [metric.value for metric in app.metric[:7]]
    report = json.loads((ROOT / 'artifacts/report.json').read_text())
    saved = next(row for row in report['metrics'] if row['split'] == 'validation' and row['model'] == report['selection']['model'])
    assert app.metric[-3].value == f'{100*saved["recall"]:.1f}%'
    app.toggle[0].set_value(True).run()
    assert not app.exception
    assert any('Window outcome' in item.value for item in app.markdown)
    app.slider[0].set_value(100.0).run()
    assert not app.exception
    assert [metric.value for metric in app.metric[:7]] == fixed
    assert app.metric[-1].value == '0'
    if len(app.selectbox[0].options) > 1:
        app.selectbox[0].set_value(int(app.selectbox[0].options[1].split()[-1])).run()
        assert not app.exception
        assert app.toggle[0].value is False


@pytest.mark.skipif(not (ROOT / 'artifacts/report.json').exists(), reason='Requires local real-data experiment')
def test_error_filters_replay_matching_outcomes_without_changing_test_metrics():
    app = AppTest.from_file(str(ROOT / 'app.py'), default_timeout=30).run()
    fixed = [metric.value for metric in app.metric[3:7]]
    for mode, outcome in [('Misses', 'Miss'), ('False alarms', 'False alarm'), ('Hits', 'Hit')]:
        app.radio[0].set_value(mode).run()
        assert not app.exception
        app.toggle[0].set_value(True).run()
        assert not app.exception
        assert any(item.value == f'**Window outcome:** {outcome}' for item in app.markdown)
        assert [metric.value for metric in app.metric[3:7]] == fixed
    app.radio[0].set_value('All windows').run()
    assert not app.exception


@pytest.mark.skipif(not (ROOT / 'artifacts/event_audit/report.json').exists(), reason='Requires local event audit')
def test_event_audit_reveal_and_region_change_preserve_replay_metrics():
    app = AppTest.from_file(str(ROOT / 'app.py'), default_timeout=30).run()
    assert not app.exception
    fixed = [metric.value for metric in app.metric]
    assert any(tab.label == 'Alarm & event audit' for tab in app.tabs)
    app.checkbox[0].set_value(True).run()
    assert not app.exception
    assert [metric.value for metric in app.metric] == fixed
    selector = app.selectbox(key='event_region_false_hours')
    next_harp = int(selector.options[1].split()[-1])
    selector.set_value(next_harp).run()
    assert not app.exception
    assert not app.checkbox[0].value
    assert [metric.value for metric in app.metric] == fixed
