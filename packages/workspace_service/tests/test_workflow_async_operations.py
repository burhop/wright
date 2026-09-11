"""Simulated remote service contracts. These are not live FEA results."""
import asyncio
from dataclasses import replace
import pytest
from tool_registry.gateway_models import GatewayTool,GatewayToolResult
from workspace_service.workflow_mcp_execution import WorkflowMcpRuntime,schema_digest
from workspace_service.workflow_source_execution import PromptStep,WorkflowSourceExecutionError
from packages.workspace_service.tests.test_workflow_mcp_execution import Gateway


def remote(states=('working','completed')):
    profile={'version':1,'status_tool':'status','cancel_tool':'cancel','poll_seconds':.05}
    tools=[GatewayTool(name='fea__submit',server_id='fea',tool_name='submit',description='Submit analysis',input_schema={'type':'object'},upstream_meta={'wright/operation':profile})]
    tools.extend(GatewayTool(name='fea__'+name,server_id='fea',tool_name=name,description=name,input_schema={'type':'object','properties':{'operation_id':{'type':'string'}},'required':['operation_id'],'additionalProperties':False},annotations={'readOnlyHint':name=='status'}) for name in ('status','cancel'))
    g=Gateway();g.list_tools=lambda *a:tuple(tools);sequence=iter(states);last='working'
    async def call(session,request,name,args,**kw):
        nonlocal last
        g.calls.append((name,args))
        if name=='fea__submit':value={'operation_id':'job-123'}
        elif name=='fea__status':
            last=next(sequence,last);value={'status':last,'result':{'stress':12,'units':'MPa'}}
        else:value={'accepted':True}
        return GatewayToolResult(content=(),structured_content=value)
    g.call_tool=call
    runtime=WorkflowMcpRuntime(g,workspace_id='w',session_id='s')
    step=PromptStep('analysis','Analysis','',None,(),'json','',False,'indexed',tool_name=tools[0].name,server_id='fea',schema_digest=schema_digest(tools[0]),timeout_seconds=2)
    return g,runtime,step,tools


def test_submission_is_polled_to_completion_once():
    g,r,s,_=remote();events=[]
    async def emit(kind,**kw):events.append((kind,kw))
    result=asyncio.run(r.call(s,{},on_event=emit))
    assert result[0]=={'stress':12,'units':'MPa'}
    assert [n for n,a in g.calls]==['fea__submit','fea__status','fea__status']
    assert [e[1]['state'] for e in events]==['submitted','working','completed','results_collected']
    assert all(a['operation_id']=='job-123' for n,a in g.calls if n!='fea__submit')


def test_timeout_requests_cancel_without_resubmission_or_false_completion():
    g,r,s,_=remote(('working',));events=[]
    async def emit(kind,**kw):events.append(kw)
    with pytest.raises(TimeoutError):asyncio.run(r.call(replace(s,timeout_seconds=.07),{},on_event=emit))
    assert [n for n,a in g.calls].count('fea__submit')==1
    assert g.calls[-1][0]=='fea__cancel'
    assert events[-1]['state']=='cancellation_requested'


def test_missing_status_capability_rejected_before_submission():
    g,r,s,tools=remote();g.list_tools=lambda *a:(tools[0],)
    with pytest.raises(WorkflowSourceExecutionError,match='status_tool'):asyncio.run(r.call(s,{}))
    assert not g.calls


@pytest.mark.parametrize('state',['failed','cancelled','input_required','mystery'])
def test_unfinished_or_unknown_job_is_never_success(state):
    g,r,s,_=remote((state,))
    with pytest.raises(WorkflowSourceExecutionError):asyncio.run(r.call(s,{}))
    assert [n for n,a in g.calls].count('fea__submit')==1
