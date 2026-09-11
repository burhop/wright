import asyncio
import copy
import hashlib
import json

import pytest

from workspace_service.workflow_campaign import inventory, observed_call_metrics, run_campaign, run_case
from packages.workspace_service.tests.test_workflow_artifact_review import source


def test_inventory_counts_two_ai_tasks_and_one_terminal_human_review(tmp_path):
    (tmp_path/'workflows').mkdir()
    (tmp_path/'workflows/rfq.workflow.wflow').write_text(source(),encoding='utf-8')
    case=inventory(tmp_path)['cases'][0]
    assert case['compiles']
    assert case['model_call_bound']==case['ai_task_count']==2
    assert case['human_review_count']==1
    assert not case['live_verified'] and not case['user_accepted']


class Reply:
    def __init__(self,value):self.value=value
    def raise_for_status(self):pass
    def json(self):return self.value


class Stream:
    def __init__(self,events):self.events=events
    async def __aenter__(self):return self
    async def __aexit__(self,*args):pass
    def raise_for_status(self):pass
    async def aiter_lines(self):
        for event in self.events:yield json.dumps(event)


class Client:
    def __init__(self,entries):self.entries=entries;self.requests=[]
    async def __aenter__(self):return self
    async def __aexit__(self,*args):pass
    async def get(self,url,params):
        self.requests.append(('GET',url,params))
        assert url.endswith('/workflow-sources')
        return Reply({'source':self.entries[params['path']]['source'],'storage_digest':'digest'})
    def stream(self,method,url,**kwargs):
        self.requests.append((method,url,kwargs))
        assert method=='POST' and url.endswith('/workflow-sources/run')
        return Stream(self.entries[kwargs['json']['path']]['events'])


def fixture(tmp_path,identity='rfq',terminal='pending_review'):
    text=source();path=f'workflows/{identity}.workflow.wflow'
    data=b'<html><body>RFQ draft only</body></html>'
    (tmp_path/f'{identity}.html').write_bytes(data)
    result={'status':terminal,'outputs':[{'output_path':f'{identity}.html','output_bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}]}
    if terminal=='pending_review':result['review']={'review_id':'a'*32,'state':'pending','actor':None}
    events=[{'kind':'step_started','task_id':key,'execution_kind':'ai'} for key in ('extract','draft')]
    events += [{'kind':'step_completed','task_id':key} for key in ('extract','draft')]
    events += [{'kind':'review_requested','task_id':'engineer'}] if terminal=='pending_review' else []
    events += [{'kind':terminal,'result':result}]
    case={'id':identity,'path':path,'source_sha256':hashlib.sha256(text.encode()).hexdigest(),'inputs':[],
          'expected_outputs':[{'kind':'file'}],'model_call_bound':2,'compiles':True,'applications':['shared-server']}
    return case,{'source':text,'events':events}


def test_pending_review_releases_campaign_slot_without_becoming_a_pass_or_submitting_decision(tmp_path,monkeypatch):
    first,a=fixture(tmp_path);second,b=fixture(tmp_path,'second','completed')
    client=Client({first['path']:a,second['path']:b})
    import httpx
    monkeypatch.setattr(httpx,'AsyncClient',lambda **kwargs:client)
    results=asyncio.run(run_campaign({'workspace':str(tmp_path),'cases':[first,second]},ids=['rfq','second'],
        api='http://example.invalid',session='test',output_dir=tmp_path/'attempts',concurrency=1,max_model_calls=4))
    pending,completed=results
    assert pending['status']=='pending_review' and completed['status']=='structure_verified'
    assert pending['execution_ended_at'] and 'completed_at' not in pending
    assert pending['live_verified'] is False and pending['user_accepted'] is False
    assert pending['human_decision_submitted'] is False and pending['engineering_review_required'] is True
    assert pending['checks'][0]['passed']  # File structure is evidence, not human acceptance.
    assert pending['call_metrics']['ai_calls_started']==pending['call_metrics']['ai_calls_completed']==2
    assert pending['call_metrics']['mcp_tool_results_recorded']==0
    assert len(client.requests)==4 and len(list((tmp_path/'attempts').glob('*.json')))==2


@pytest.mark.parametrize('mutation',['missing-id','approved','duplicate','wrong-event'])
def test_invalid_or_conflicting_terminal_review_receipts_do_not_create_acceptance(tmp_path,mutation):
    case,entry=fixture(tmp_path)
    if mutation=='missing-id':entry['events'][-1]['result']['review'].pop('review_id')
    if mutation=='approved':entry['events'][-1]['result']['review']['state']='approved'
    if mutation=='duplicate':entry['events'].append(copy.deepcopy(entry['events'][-1]))
    if mutation=='wrong-event':entry['events'][-1]['kind']='completed'
    result=asyncio.run(run_case(case,root=tmp_path,api='http://example.invalid',session='test',timeout=2,client=Client({case['path']:entry})))
    assert result['status']=='failed' and not result['user_accepted']
    assert result['error'] and result['completed_at']


def test_observation_timeout_does_not_claim_server_execution_ended(tmp_path):
    case,entry=fixture(tmp_path)
    class TimedOutClient(Client):
        async def get(self,*args,**kwargs):raise TimeoutError('No terminal receipt')
    result=asyncio.run(run_case(case,root=tmp_path,api='http://example.invalid',session='test',timeout=2,
                               client=TimedOutClient({case['path']:entry})))
    assert result['status']=='timed_out' and result['observation_ended_at']
    assert 'execution_ended_at' not in result
    assert 'server may have partial operations' in result['error']


def test_call_metrics_count_actual_attempts_and_keep_agent_transport_unknown():
    events=[{'kind':'step_started','task_id':'a','execution_kind':'ai'},
            {'kind':'step_completed','task_id':'a'},
            {'kind':'step_started','task_id':'a','execution_kind':'ai'},
            {'kind':'step_completed','task_id':'a'},
            {'kind':'step_started','task_id':'cad','execution_kind':'mcp_task'},
            {'kind':'task_progress','task_id':'cad','available_tools':[]},
            {'kind':'tool_started','task_id':'cad'},
            {'kind':'tool_completed','task_id':'cad','status':'invalid_arguments'},
            {'kind':'task_progress','task_id':'cad','available_tools':[]},
            {'kind':'tool_started','task_id':'cad'},
            {'kind':'tool_completed','task_id':'cad','status':'succeeded'},
            {'kind':'step_started','task_id':'review','execution_kind':'human_review'},
            {'kind':'review_requested','task_id':'review'},
            {'kind':'step_completed','task_id':'review'}]
    before=copy.deepcopy(events);metrics=observed_call_metrics(events)
    assert metrics['ai_calls_started']==metrics['ai_calls_completed']==2
    assert metrics['agent_tasks_started']==1 and metrics['agent_decisions_started']==2
    assert metrics['mcp_tool_results_recorded']==metrics['mcp_tool_calls_started']==2
    assert metrics['mcp_tool_calls_failed']==metrics['mcp_tool_calls_succeeded']==1
    assert metrics['model_transport_calls'] is None and events==before
