import asyncio
import json

import anyio
import pytest
from starlette.responses import StreamingResponse
from workspace_service.workflow_run_record import record_workflow_run, recent_workflow_runs
from packages.workspace_service.tests.test_workflow_source_execution import service


@pytest.mark.parametrize('blocked_storage',[False,True])
def test_asgi_disconnect_persists_cancelled_end_and_partial_without_completed_tool(tmp_path,monkeypatch,blocked_storage):
    monkeypatch.setattr('workspace_service.workflow_run_record._FINAL_CHECKPOINT_SECONDS',.05)
    (tmp_path/'workflows').mkdir()
    source='workflows/example.workflow.wflow'
    (tmp_path/source).write_text('workflow example\nend')
    svc=service(tmp_path)
    write=svc.files.write_generated
    async def checkpoint(workspace,path,content,policy):
        if json.loads(content)['status']=='cancelled':
            # A real asynchronous file executor can suspend before publication.
            if blocked_storage:await anyio.sleep_forever()
            await anyio.sleep(.01)
        return await write(workspace,path,content,policy)
    svc.files.write_generated=checkpoint
    async def scenario():
        started=asyncio.Event()
        async def execute(emit):
            await emit({'kind':'result_ready','task_id':'design','engineering_result':{'id':'partial','provenance':{'task_id':'design'}}})
            await emit({'kind':'tool_started','task_id':'quote','tool':'browser_click'})
            started.set()
            await asyncio.Event().wait()
            pytest.fail('Execution must not be shielded from disconnect')
        async def body():
            await record_workflow_run(service=svc,workspace_dir=tmp_path,source_path=source,source_digest='exact',execute=execute)
            yield b'completed'
        sent=[]
        async def receive():
            await started.wait()
            return {'type':'http.disconnect'}
        async def send(message):sent.append(message)
        async with asyncio.timeout(2):
            await StreamingResponse(body())({'type':'http','asgi':{'version':'3.0','spec_version':'2.0'}},receive,send)
        assert not any(m.get('body')==b'completed' for m in sent)
    asyncio.run(scenario())
    path=next((tmp_path/'runs/example').glob('*.json'))
    raw=json.loads(path.read_text())
    assert raw['status']==('running' if blocked_storage else 'cancelled')
    if not blocked_storage:
        assert raw['execution_ended_at'] and raw['completed_at']==raw['execution_ended_at']
    assert raw['partial_results']['partial']['provenance']['task_id']=='design'
    assert raw['events'][-1]['kind']=='tool_started'
    assert not any(e['kind']=='tool_completed' for e in raw['events'])
    assert recent_workflow_runs(tmp_path,source)[0]['status']==('interrupted' if blocked_storage else 'cancelled')
