import hashlib
import json
import socket
from pathlib import Path

import pytest
from workspace_service.workflow_run_record import recent_workflow_runs, _execution_snapshot


def setup_record(root, events=(), **extra):
    source='workflows/example.workflow.wflow'
    (root/'workflows').mkdir(exist_ok=True)
    (root/source).write_text('workflow example\nend',encoding='utf-8')
    record={'workflow_path':source,'source_digest':hashlib.sha256((root/source).read_bytes()).hexdigest(),
            'status':'running','started_at':'2026-09-08T10:00:00.100Z','events':list(events),
            'owner':{'host':socket.gethostname(),'lease':'controlled-test'},**extra}
    folder=root/'runs/example';folder.mkdir(parents=True,exist_ok=True)
    path=folder/'20260908T100000Z-cccccccccccc.json'
    path.write_text(json.dumps(record),encoding='utf-8')
    return source,path,record


def event(kind, task='cad', **extra):
    return {'kind':kind,'task_id':task,'task_title':task.title(),'at':'2026-09-08T10:00:00Z',**extra}


def artifact(task,path):
    return {'schema_version':1,'id':'run:'+task,'name':task,'kind':'file',
            'provenance':{'run_id':'run','task_id':task,'output_port':'result','input_revisions':[['upstream','A']]},
            'representations':[{'kind':'workspace_file','location':path,'durability':'persistent','format':'html'}], 'exports':[]}


def test_active_snapshot_has_recorded_predecessor_and_compact_counts(tmp_path,monkeypatch):
    monkeypatch.setattr('workspace_service.workflow_resource_lease.lease_is_active',lambda _:True)
    source,path,_=setup_record(tmp_path,[event('step_started','design',execution_kind='ai'),event('step_completed','design'),
      event('step_started',execution_kind='mcp_task',prompt='PRIVATE PROMPT'),event('task_progress',available_tools=[],tool_calls=0),
      event('tool_started',arguments={'large':'SECRET'}),event('tool_completed',result={'native':'SECRET'}),event('task_progress',message='Reviewing tool results',available_tools=[],tool_calls=1)])
    original=path.read_bytes()
    summary=recent_workflow_runs(tmp_path,source,latest_only=True)[0]
    s=summary['execution']
    assert s['active_task_id']=='cad' and s['completed_task_ids']==['design']
    assert (s['model_call_count'],s['tool_call_count'],s['tool_completed_count'])==(3,1,1)
    assert s['last_progress']['task_title']=='Cad'
    assert summary['source_matches_current'] is True
    assert 'SECRET' not in json.dumps(summary) and 'PRIVATE PROMPT' not in json.dumps(summary)
    assert path.read_bytes()==original


def test_revision_invalidates_completion_and_results_until_explicit_restart():
    events=[event('step_completed','design'),event('step_completed'),event('result_ready',engineering_result=artifact('cad','old.psm')),
            event('output_saved',output_path='old.psm',output_format='psm'),event('step_completed','check'),
            event('design_revision',invalidated_task_ids=['cad','check'],revision=1)]
    s,results,_=_execution_snapshot({'events':events},'running')
    assert s['completed_task_ids']==['design'] and s['active_task_id'] is None
    assert s['outputs']==[] and results==[] and s['revision_count']==1
    events.append(event('step_started',execution_kind='mcp_task'))
    s,_,_=_execution_snapshot({'events':events},'running')
    assert s['active_task_id']=='cad'


def test_step_restart_removes_previous_artifact_without_inventing_completion():
    events=[event('step_completed'),event('result_ready',engineering_result=artifact('cad','old.psm')),
            event('step_started',execution_kind='mcp_task')]
    s,results,_=_execution_snapshot({'events':events},'running')
    assert s['completed_task_ids']==[] and results==[]


@pytest.mark.parametrize('lease,state',[(None,'unknown'),(False,'interrupted')])
def test_unconfirmed_or_released_lease_never_pulses(tmp_path,monkeypatch,lease,state):
    monkeypatch.setattr('workspace_service.workflow_resource_lease.lease_is_active',lambda _:lease)
    source,_,_=setup_record(tmp_path,[event('step_started',execution_kind='mcp_task')])
    summary=recent_workflow_runs(tmp_path,source,latest_only=True)[0]
    assert summary['status']==state and summary['execution']['active_task_id'] is None


@pytest.mark.parametrize('state',['completed','failed','pending_review','cancelled'])
def test_terminal_snapshot_retains_partial_outputs_and_end_but_clears_active(tmp_path,state):
    source,_,_=setup_record(tmp_path,[event('step_started',execution_kind='ai'),event('result_ready',engineering_result=artifact('cad','report.html'))],
                           status=state,error='Example failure' if state=='failed' else None,execution_ended_at='2026-09-08T10:01:00Z')
    summary=recent_workflow_runs(tmp_path,source,latest_only=True)[0]
    assert summary['execution']['active_task_id'] is None and summary['run_id']=='run'
    assert summary['results'][0]['representations'][0]['location']=='report.html'
    assert summary['results'][0]['provenance']['input_revisions']==[['upstream','A']]
    assert summary['execution_ended_at']=='2026-09-08T10:01:00Z'


def test_stale_saved_source_keeps_exact_run_identity(tmp_path):
    source,_,record=setup_record(tmp_path,status='completed')
    (tmp_path/source).write_text('workflow edited\nend')
    summary=recent_workflow_runs(tmp_path,source,latest_only=True)[0]
    assert summary['source_matches_current'] is False and summary['source_digest']==record['source_digest']


def test_unreadable_lease_is_unknown_not_missing_history(tmp_path,monkeypatch):
    def unavailable(_):raise PermissionError('Controlled ownership probe denial')
    monkeypatch.setattr('workspace_service.workflow_resource_lease.lease_is_active',unavailable)
    source,_,_=setup_record(tmp_path,[event('step_started',execution_kind='mcp_task')])
    summary=recent_workflow_runs(tmp_path,source,latest_only=True)[0]
    assert summary['status']=='unknown' and summary['execution']['active_task_id'] is None


def test_latest_reads_one_timestamp_group_and_orders_same_second_by_start(tmp_path,monkeypatch):
    source,path,record=setup_record(tmp_path,status='completed')
    for second in range(10):
        (path.parent/f'20260908T0959{second:02d}Z-ffffffffffff.json').write_text(json.dumps(record))
    newest=path.parent/'20260908T100000Z-aaaaaaaaaaaa.json'
    newest.write_text(json.dumps({**record,'started_at':'2026-09-08T10:00:00.999Z'}))
    opened=[];original=Path.open
    def track(self,*args,**kwargs):
        if self.suffix=='.json':opened.append(self.name)
        return original(self,*args,**kwargs)
    monkeypatch.setattr(Path,'open',track)
    found=recent_workflow_runs(tmp_path,source,latest_only=True)
    assert len(found)==1 and found[0]['path'].endswith(newest.name)
    assert len(opened)==2, 'Polling should not read the ten older native logs'


def test_latest_ignores_malformed_foreign_and_escaping_records(tmp_path):
    source,path,record=setup_record(tmp_path,status='completed')
    (path.parent/'20260908T100003Z-a.json').write_text('{')
    (path.parent/'20260908T100002Z-a.json').write_text(json.dumps({**record,'events':['not-an-event']}))
    (path.parent/'20260908T100001Z-a.json').write_text(json.dumps({**record,'workflow_path':'other/example.workflow.wflow'}))
    assert recent_workflow_runs(tmp_path,source,latest_only=True)[0]['path'].endswith(path.name)
    with pytest.raises(ValueError):recent_workflow_runs(tmp_path,'../outside.workflow.wflow',latest_only=True)


def test_projection_is_byte_bounded_and_native_payloads_never_appear():
    results=[artifact('task'+str(i),'reports/'+('p'*2000)+str(i)+'.html') for i in range(100)]
    s,projected,_=_execution_snapshot({'events':[event('tool_completed',result={'native':'X'*1000000})],
                                     'result':{'results':results}},'completed')
    assert s['truncated'] is True and len(json.dumps([s,projected],ensure_ascii=True).encode())<=64*1024
    assert 'native' not in json.dumps(s)


def test_default_history_keeps_original_last_event_and_no_snapshot(tmp_path):
    source,_,_=setup_record(tmp_path,[event('tool_completed',result={'native':'full evidence'})],status='completed')
    summary=recent_workflow_runs(tmp_path,source)[0]
    assert summary['last_event']['result']=={'native':'full evidence'} and 'execution' not in summary


def test_actual_cad_export_progress_does_not_count_as_model_decisions():
    fixture=json.loads((Path(__file__).parent/'fixtures/run-progress-dispatch-20260908.json').read_text())
    snapshot,_,_=_execution_snapshot({'events':fixture['events']},'interrupted')
    assert len([e for e in fixture['events'] if e['kind']=='task_progress'])==3
    assert snapshot['model_call_count']==fixture['expected_model_call_count']==1
    assert snapshot['active_task_id'] is None
