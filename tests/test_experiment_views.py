from streamlit.testing.v1 import AppTest
import pytest


def render(root):
    from helio24.experiment_views import render_training_tab
    render_training_tab(root)


def test_monitor_renders_without_model_artifacts_and_handles_refresh(tmp_path):
    app=AppTest.from_function(render,args=(str(tmp_path),),default_timeout=10).run()
    assert not app.exception
    assert any('No prepared experiment' in item.value for item in app.info)
    app.button[0].click().run()
    assert not app.exception


@pytest.mark.parametrize('state,label',[('stopped','Stopped'),('queue_running','Training queue active')])
def test_monitor_displays_saved_fit_counts_and_process_state(tmp_path,monkeypatch,state,label):
    from helio24 import experiment_views
    from helio24.experiment_monitor import snapshot
    monkeypatch.setattr(experiment_views,'snapshot',lambda root,directory: snapshot(root,directory,process_probe=lambda *_:{'state':state,'pid':None}))
    import json
    run=tmp_path/'artifacts/temporal_years_20261101_r1';run.mkdir(parents=True)
    (tmp_path/'config').mkdir()
    (tmp_path/'config/temporal-sequence-v2.json').write_text(json.dumps({'training':{'epochs':10},'seeds':[24],'arms':['chronological']}))
    (run/'prepared.json').write_text(json.dumps({'folds':[{'year':2014,'status':'complete'}]}))
    (run/'progress.json').write_text(json.dumps({'year':2014,'arm':'chronological','seed':24,'status':'training'}))
    job=run/'2014/chronological_seed24';job.mkdir(parents=True)
    (job/'progress.json').write_text(json.dumps({'epoch':2}))
    app=AppTest.from_function(render,args=(str(tmp_path),),default_timeout=10).run()
    assert not app.exception
    messages=app.warning if state=='stopped' else app.success
    assert any(item.value==label for item in messages)
    if state=='queue_running':assert any('Annual evaluation follows' in item.value for item in app.caption)
    assert [m.value for m in app.metric][:3]==['0 / 1','2014','2 / 10']


def test_cloud_storage_state_hides_unverified_counts(tmp_path,monkeypatch):
    from helio24 import experiment_views
    monkeypatch.setattr(experiment_views,'snapshot',lambda *_:{'state':'storage_unavailable'})
    app=AppTest.from_function(render,args=(str(tmp_path),),default_timeout=10).run()
    assert not app.exception
    assert not app.metric
    assert any('cloud placeholders' in item.value for item in app.warning)
