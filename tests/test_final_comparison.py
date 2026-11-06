import hashlib
import json

import pytest
from streamlit.testing.v1 import AppTest

from helio24.final_comparison import load_comparison


def fixture(root):
    folder = root/'artifacts/final'
    folder.mkdir(parents=True)
    (root/'config').mkdir()
    (folder/'metrics.csv').write_text('year,arm,precision,recall,fp,tp,fn,accuracy,average_precision,brier,log_loss,positives\n2018,baseline,0,,10,0,0,0.9,,0.01,0.02,0\n2018,chronological,0,,15,0,0,0.8,,0.02,0.03,0\n')
    (folder/'comparisons.csv').write_text('candidate,control,precision_win_count,required_positive_years,full_met_count\nchronological,baseline,1,6,0\n')
    report = {'status':'final_complete','missing_eligible_years':[], 'selected_years':[2018],
              'artifact_hashes':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.iterdir()}}
    (folder/'report.json').write_text(json.dumps(report))
    (root/'config/dashboard-comparison-v1.json').write_text(json.dumps({'source':'artifacts/final',
        'report_sha256':hashlib.sha256((folder/'report.json').read_bytes()).hexdigest()}))
    return folder


def render(root):
    from helio24.final_comparison import render_final_comparison
    render_final_comparison(root)


def test_comparison_renders_zero_positive_year_without_false_recall(tmp_path):
    fixture(tmp_path)
    app = AppTest.from_function(render, args=(str(tmp_path),)).run()
    assert not app.exception
    assert any('undefined' in m.value for m in app.info)
    assert [m.value for m in app.metric] == ['1', '1 / 6', '0 / 6']


def test_comparison_rejects_tampered_metrics(tmp_path):
    folder = fixture(tmp_path)
    with (folder/'metrics.csv').open('a') as stream:
        stream.write('\nchanged')
    with pytest.raises(ValueError, match='hash check'):
        load_comparison(tmp_path)
    app = AppTest.from_function(render, args=(str(tmp_path),)).run()
    assert not app.exception
    assert not app.metric
