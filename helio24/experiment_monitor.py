"""Read-only experiment monitoring; never load model checkpoints or fit models."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
from helio24.storage_preflight import is_placeholder


def read_record(path, warnings):
    try:
        if is_placeholder(path):
            warnings.append('cloud_placeholder:'+str(path))
            return None
        record=json.loads(path.read_text())
        if not isinstance(record,dict):raise ValueError('Expected object')
        return record
    except FileNotFoundError:
        return None
    except (OSError, ValueError):
        warnings.append(str(path.name))
        return None


def command_matches(command, option, directory):
    try:
        return Path(command[command.index(option)+1]).resolve()==directory.resolve()
    except (ValueError, IndexError, TypeError):
        return False


def probe_run(directory, root, launchers):
    """Verify PID identity; detect active orphan workers and permission failures."""
    try:
        import psutil
    except ImportError:
        return {'state':'unknown','pid':None}
    denied=False
    for path,record in launchers:
        pid=record.get('pid')
        if not isinstance(pid,int) or isinstance(pid,bool):continue
        expected=record.get('command',[])
        runner=next((part for part in expected if isinstance(part,str) and Path(part).name=='run_temporal_years.py'),str(root/'scripts/run_temporal_years.py'))
        try:
            process=psutil.Process(pid);command=process.cmdline()
            if process.status()!=psutil.STATUS_ZOMBIE and runner in command and command_matches(command,'--output',directory):
                return {'state':'running','pid':pid}
        except (psutil.NoSuchProcess, psutil.ZombieProcess):pass
        except (psutil.AccessDenied,OSError):denied=True
    try:
        for process in psutil.process_iter(['pid','cmdline','status']):
            try:
                command=process.info['cmdline'] or []
                if not any(Path(part).name=='temporal_worker.py' for part in command) or process.info['status']==psutil.STATUS_ZOMBIE:continue
                job=Path(command[command.index('--job')+1]).resolve()
                if job.is_relative_to(directory.resolve()):return {'state':'worker_only','pid':process.pid}
            except (ValueError, IndexError, psutil.NoSuchProcess, psutil.AccessDenied, OSError):continue
    except (psutil.AccessDenied,OSError):denied=True
    return {'state':'unknown' if denied else 'stopped','pid':None}


def read_epoch_history(directory):
    """Bounded log tail; tolerate old tracebacks and partially written log lines."""
    try:
        if is_placeholder(directory/'worker.log'):return []
        with (directory/'worker.log').open('rb') as stream:
            stream.seek(0,2);stream.seek(max(0,stream.tell()-65536))
            lines=stream.read().decode('utf-8',errors='replace').splitlines()
    except OSError:return []
    history={}
    for line in lines:
        try:
            row=json.loads(line)
            epoch=row.get('epoch');loss=row.get('training_loss')
            if isinstance(epoch,int) and isinstance(loss,(float,int)):
                history[epoch]={'epoch':epoch,'training_loss':loss}
        except (ValueError,AttributeError):continue
    return [history[k] for k in sorted(history)]


def snapshot(root, directory=None, *, now=None, process_probe=probe_run):
    root=Path(root).resolve();directory=Path(directory or root/'artifacts/temporal_years_20261101_r1').resolve()
    now=time.time() if now is None else now;warnings=[]
    unavailable=[]
    for path in [directory/'prepared.json',root/'config/temporal-sequence-v2.json']:
        try:
            if is_placeholder(path):unavailable.append(str(path))
        except FileNotFoundError:pass
        except OSError:unavailable.append(str(path))
    if unavailable:
        return {'state':'storage_unavailable','completed':None,'total':None,'epochs':None,
                'current':None,'jobs':[],'history':[],'finished_years':[],
                'last_record':None,'record_age_seconds':None,'pid':None,'failure':None,
                'warnings':unavailable,'directory':str(directory)}
    prepared=read_record(directory/'prepared.json',warnings)
    protocol=read_record(root/'config/temporal-sequence-v2.json',warnings) or {}
    maximum_epochs=protocol.get('training',{}).get('epochs',10)
    seeds=protocol.get('seeds',[24,42,97]);arms=protocol.get('arms',['chronological','shuffled_interior'])
    jobs=[];latest_record=None
    for fold in (prepared or {}).get('folds',[]):
        if fold.get('status')!='complete':continue
        for arm in arms:
            for seed in seeds:
                path=directory/str(fold['year'])/f'{arm}_seed{seed}'
                result=read_record(path/'result.json',warnings);progress=read_record(path/'progress.json',warnings)
                complete=False
                if isinstance(result,dict):
                    try:
                        if is_placeholder(path/'job.json'):
                            warnings.append('cloud_placeholder:'+str(path/'job.json'))
                        else:
                            complete=(result.get('epochs')==maximum_epochs and result.get('job_sha256')==hashlib.sha256((path/'job.json').read_bytes()).hexdigest()
                                      and all((path/name).exists() for name in ['checkpoint.pt','calibration.npy','evaluation.npy']))
                    except OSError:pass
                    if not complete:warnings.append(f'{fold["year"]}/{arm}_seed{seed}/result.json')
                raw_epoch=(progress or {}).get('epoch',0)
                if not isinstance(raw_epoch,int) or isinstance(raw_epoch,bool):
                    warnings.append(f'{fold["year"]}/{arm}_seed{seed}/progress.json');raw_epoch=0
                epoch=maximum_epochs if complete else min(maximum_epochs,max(0,raw_epoch))
                state='complete' if complete else 'in_progress' if progress else 'pending'
                updated=None
                for name in ['result.json','progress.json']:
                    try:
                        stamp=(path/name).stat().st_mtime
                        updated=max(updated or stamp,stamp);latest_record=max(latest_record or stamp,stamp)
                    except OSError:pass
                jobs.append({'year':fold['year'],'arm':arm,'seed':seed,'epoch':epoch,'state':state,'updated':updated})
    launchers=[]
    candidates=list(directory.glob('launcher*.json'))+list((root/'artifacts').glob('runtime_recovery_*/launcher*.json'))
    for path in candidates:
        record=read_record(path,warnings)
        if isinstance(record,dict) and command_matches(record.get('command',[]),'--output',directory):launchers.append((path,record))
    launchers.sort(key=lambda item:item[0].stat().st_mtime,reverse=True)
    latest_launch=launchers[0][0].stat().st_mtime if launchers else None
    process=process_probe(directory,root,launchers) if prepared else {'state':'stopped','pid':None}
    progress=read_record(directory/'progress.json',warnings) or {}
    final=read_record(directory/'report.json',warnings)
    completed=sum(j['state']=='complete' for j in jobs);total=len(jobs)
    current=next((j for j in jobs if (j['year'],j['arm'],j['seed'])==(progress.get('year'),progress.get('arm'),progress.get('seed'))),None)
    history=read_epoch_history(directory/str(current['year'])/f"{current['arm']}_seed{current['seed']}") if current else []
    failure=read_record(directory/'failure.json',warnings);current_failure=False
    if failure:
        try:current_failure=latest_launch is None or (directory/'failure.json').stat().st_mtime>latest_launch
        except OSError:pass
    final_valid=(isinstance(final,dict) and isinstance(final.get('metrics'),list)
                 and final.get('protocol_sha256')==(prepared or {}).get('protocol_sha256'))
    if final_valid and total and completed==total:state='completed'
    elif process['state']=='running':
        last_activity=max([v for v in [latest_record,latest_launch] if v is not None],default=now)
        state='running_stale' if now-last_activity>900 else 'running'
    elif process['state']=='worker_only':state='worker_only'
    elif process['state']=='unknown':state='unknown'
    elif not prepared:state='not_started'
    else:state='failed' if current_failure else 'stopped'
    finished_years=[]
    for fold in (prepared or {}).get('folds',[]):
        if (directory/str(fold['year'])/'finished.json').exists():finished_years.append(fold['year'])
    if any(warning.startswith('cloud_placeholder:') for warning in warnings):
        state='storage_unavailable';completed=None;total=None
    return {'state':state,'completed':completed,'total':total,'epochs':maximum_epochs,'current':current,'jobs':jobs,'history':history,
            'finished_years':finished_years,'last_record':datetime.fromtimestamp(latest_record,timezone.utc).isoformat() if latest_record else None,
            'record_age_seconds':max(0,now-latest_record) if latest_record else None,'pid':process.get('pid'),
            'failure':failure if current_failure else None,'warnings':sorted(set(warnings)),'directory':str(directory)}
