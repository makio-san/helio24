from pathlib import Path

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
