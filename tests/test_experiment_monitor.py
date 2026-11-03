import hashlib
import json
from pathlib import Path
import pytest
from helio24.experiment_monitor import snapshot,command_matches


def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value))


@pytest.fixture
def experiment(tmp_path):
    run=tmp_path/'artifacts/temporal_years_20261101_r1'
    write(tmp_path/'config/temporal-sequence-v2.json',{'training':{'epochs':10},'seeds':[24,42],'arms':['chronological']})
    write(run/'prepared.json',{'protocol_sha256':'frozen','folds':[{'year':2014,'status':'complete'},{'year':2019,'status':'skipped'}]})
    write(run/'progress.json',{'status':'training','year':2014,'arm':'chronological','seed':42})
    complete=run/'2014/chronological_seed24';write(complete/'job.json',{'seed':24})
    write(complete/'result.json',{'epochs':10,'job_sha256':hashlib.sha256((complete/'job.json').read_bytes()).hexdigest()})
    for name in ['checkpoint.pt','calibration.npy','evaluation.npy']:(complete/name).touch()
    current=run/'2014/chronological_seed42';write(current/'progress.json',{'epoch':3,'training_loss':.5})
    (current/'worker.log').write_text('old traceback\n{"epoch":2,"training_loss":0.6}\n{"epoch":3,"training_loss":0.5}\n{"epoch":')
    write(tmp_path/'artifacts/runtime_recovery_test/launcher.json',{'pid':123,'command':['python','run.py','--output',str(run)]})
    return tmp_path,run,current


def probe(state):return lambda *_:{'state':state,'pid':123 if state=='running' else None}


def test_stopped_process_overrides_stale_training_record(experiment):
    root,run,current=experiment
    s=snapshot(root,process_probe=probe('stopped'))
    assert s['state']=='stopped' and (s['completed'],s['total'])==(1,2)
    assert s['current']['epoch']==3 and s['history']==[{'epoch':2,'training_loss':.6},{'epoch':3,'training_loss':.5}]
    assert s['last_record'] is not None


def test_old_failure_does_not_override_live_resumed_runner(experiment):
    import os,time
    root,run,_=experiment
    write(run/'failure.json',{'error':'old failure'})
    os.utime(run/'failure.json',(1,1))
    s=snapshot(root,process_probe=probe('running'))
    assert s['state']=='running' and s['failure'] is None
    future=time.time()+3600
    assert snapshot(root,process_probe=probe('running'),now=future)['state']=='running_stale'
    assert snapshot(root,process_probe=probe('unknown'))['state']=='unknown'
    assert snapshot(root,process_probe=probe('worker_only'))['state']=='worker_only'


def test_partial_records_and_bad_completion_markers_do_not_crash(experiment):
    root,run,current=experiment
    (current/'progress.json').write_text('{"epoch":')
    s=snapshot(root,process_probe=probe('running'))
    assert s['warnings'] and s['current']['epoch']==0
    write(run/'2014/chronological_seed24/result.json',{'epochs':10,'job_sha256':'wrong'})
    assert snapshot(root,process_probe=probe('stopped'))['completed']==0
    assert snapshot(root/'empty',process_probe=probe('stopped'))['state']=='not_started'


def test_completion_and_pid_identity_require_matching_records(experiment):
    root,run,current=experiment
    write(current/'job.json',{'seed':42})
    write(current/'result.json',{'epochs':10,'job_sha256':hashlib.sha256((current/'job.json').read_bytes()).hexdigest()})
    for name in ['checkpoint.pt','calibration.npy','evaluation.npy']:(current/name).touch()
    write(run/'report.json',{'metrics':[],'protocol_sha256':'frozen'})
    assert snapshot(root,process_probe=probe('stopped'))['state']=='completed'
    assert command_matches(['python','--output',str(run)],'--output',run)
    assert not command_matches(['python','--output',str(root/'other')],'--output',run)


def test_native_process_permission_errors_are_reported_as_unknown(experiment,monkeypatch):
    import psutil
    from helio24.experiment_monitor import probe_run
    root,run,_=experiment
    def denied(*args,**kwargs):raise PermissionError('process enumeration denied')
    monkeypatch.setattr(psutil,'process_iter',denied)
    assert probe_run(run,root,[])['state']=='unknown'


def test_probe_rejects_reused_pid_for_other_experiment(experiment,monkeypatch):
    import psutil
    from helio24.experiment_monitor import probe_run
    root,run,_=experiment
    command=['python',str(root/'scripts/run_temporal_years.py'),'--output',str(root/'other')]
    class Process:
        def cmdline(self):return command
        def status(self):return psutil.STATUS_RUNNING
    monkeypatch.setattr(psutil,'Process',lambda _:Process())
    monkeypatch.setattr(psutil,'process_iter',lambda _:[])
    launchers=[(root/'launcher.json',{'pid':123})]
    assert probe_run(run,root,launchers)['state']=='stopped'
    command[-1]=str(run)
    assert probe_run(run,root,launchers)=={'state':'running','pid':123}


def test_cloud_prepared_record_does_not_look_not_started(experiment,monkeypatch):
    from helio24 import experiment_monitor
    root,run,_=experiment
    monkeypatch.setattr(experiment_monitor,'is_placeholder',lambda path: path==run/'prepared.json')
    monkeypatch.setattr(experiment_monitor,'read_record',lambda *_:pytest.fail('Must not open placeholder records'))
    s=snapshot(root,process_probe=lambda *_:pytest.fail('Process status should remain unverified'))
    assert s['state']=='storage_unavailable'
    assert s['completed'] is None and s['total'] is None


def test_cloud_optional_record_is_skipped_without_opening(tmp_path,monkeypatch):
    from helio24 import experiment_monitor
    monkeypatch.setattr(experiment_monitor,'is_placeholder',lambda _:True)
    warnings=[]
    assert experiment_monitor.read_record(tmp_path/'progress.json',warnings) is None
    assert warnings==['cloud_placeholder:'+str(tmp_path/'progress.json')]


def test_cloud_job_identity_does_not_read_or_publish_false_counts(experiment,monkeypatch):
    from helio24 import experiment_monitor
    root,run,_=experiment
    monkeypatch.setattr(experiment_monitor,'is_placeholder',lambda path: path==run/'2014/chronological_seed24/job.json')
    s=snapshot(root,process_probe=probe('stopped'))
    assert s['state']=='storage_unavailable'
    assert s['completed'] is None and s['total'] is None


def test_relocated_runner_requires_launcher_path_and_matching_output(experiment,monkeypatch):
    import psutil
    from helio24.experiment_monitor import probe_run
    root,run,_=experiment
    runner=str(root/'local_execution/scripts/run_temporal_years.py')
    command=['python',runner,'--output',str(run)]
    class Process:
        def cmdline(self):return command
        def status(self):return psutil.STATUS_RUNNING
    monkeypatch.setattr(psutil,'Process',lambda _:Process())
    monkeypatch.setattr(psutil,'process_iter',lambda _:[])
    launchers=[(root/'launcher.json',{'pid':123,'command':command.copy()})]
    assert probe_run(run,root,launchers)=={'state':'running','pid':123}
    command[-1]=str(root/'other')
    assert probe_run(run,root,launchers)['state']=='stopped'
    command[-1]=str(run);command[1]=str(root/'unexpected/run_temporal_years.py')
    assert probe_run(run,root,launchers)['state']=='stopped'
