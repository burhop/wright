import asyncio
import json
import socket
import pytest
from workspace_service.workflow_run_record import record_workflow_run, recent_workflow_runs
from workspace_service.workflow_resource_lease import ApplicationLease
from packages.workspace_service.tests.test_workflow_source_execution import service


def workflow(root):
    (root/'workflows').mkdir()
    (root/'workflows/example.workflow.wflow').write_text('workflow example\nend')
    return 'workflows/example.workflow.wflow'


def test_history_distinguishes_active_owner_and_completed_run(tmp_path):
    source=workflow(tmp_path)
    async def execute(emit):
        history=recent_workflow_runs(str(tmp_path),source)
        assert history[0]['status']=='running'
        return {'outputs':[],'steps':[],'results':[]}
    asyncio.run(record_workflow_run(service=service(tmp_path),workspace_dir=str(tmp_path),source_path=source,
        source_digest='digest',execute=execute))
    assert recent_workflow_runs(str(tmp_path),source)[0]['status']=='completed'


def test_unfinished_record_is_interrupted_only_when_known_host_lease_is_released(tmp_path):
    source=workflow(tmp_path)
    folder=tmp_path/'runs/example';folder.mkdir(parents=True)
    record={'workflow_path':source,'status':'running','started_at':'2026-09-07T00:00:00Z','events':[],
        'owner':{'host':socket.gethostname(),'lease':'history-test-'+tmp_path.name}}
    path=folder/'run.json'
    async def scenario():
        async with ApplicationLease(record['owner']['lease']):
            path.write_text(json.dumps(record))
            assert recent_workflow_runs(str(tmp_path),source)[0]['status']=='running'
        assert recent_workflow_runs(str(tmp_path),source)[0]['status']=='interrupted'
    asyncio.run(scenario())
    assert json.loads(path.read_text())['status']=='running', 'History must not rewrite execution evidence'
    record['owner']['host']='another-host'
    path.write_text(json.dumps(record))
    assert recent_workflow_runs(str(tmp_path),source)[0]['status']=='unknown'


def test_history_is_scoped_to_exact_workflow_and_rejects_path_escape(tmp_path):
    source=workflow(tmp_path)
    folder=tmp_path/'runs/example';folder.mkdir(parents=True)
    (folder/'foreign.json').write_text(json.dumps({'workflow_path':'other/example.workflow.wflow','status':'completed'}))
    (folder/'invalid.json').write_text('{')
    (folder/'invalid-list.json').write_text('[]')
    assert recent_workflow_runs(str(tmp_path),source)==[]
    with pytest.raises(ValueError):recent_workflow_runs(str(tmp_path),'../outside.wflow')
