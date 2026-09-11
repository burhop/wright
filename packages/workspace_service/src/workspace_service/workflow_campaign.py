"""Development workflow inventory and bounded runs through the normal API.

This is not the frozen process-100 qualification/holdout program. Every attempt
is retained, and format checks do not claim engineering design acceptance.
"""
import asyncio
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from .workflow_source_execution import _parse, compile_prompt_workflow, WorkflowSourceExecutionError, validate_workspace_authoring_shape
from .workspace_path import WorkspacePath


def sha(data):
    return hashlib.sha256(data).hexdigest()


def planned_scenarios():
    """Inventory actual legacy scenarios without counting them as runnable wflow files."""
    import yaml
    root=Path(__file__).parent/'engineering_scenario_catalog'
    catalog=yaml.safe_load((root/'catalog.yaml').read_text(encoding='utf-8'))
    cases=[]
    for entry in catalog['scenarios']:
        path=root/entry['manifest']
        scenario=yaml.safe_load(path.read_text(encoding='utf-8'))
        cases.append({'id':'SCENARIO-'+scenario['scenario_id'],'name':scenario['title'],
            'purpose':scenario['summary'],'source':str(path),'source_sha256':sha(path.read_bytes()),
            'state':'planned_migration','authored':False,'runnable':False,'live_verified':False,
            'applications':scenario['domains'],'capabilities':scenario['capabilities'],
            'inputs':scenario['inputs'],'expected_outputs':scenario['artifacts'],
            'verification_criteria':scenario['assertions'],'fixture_provenance':scenario['provenance'],
            'blockers':['Legacy Rivet fixture; author a workspace .wflow and bind real application capabilities before a live run.']})
    return cases


def inventory(root: Path):
    cases=[]
    for path in sorted((root/'workflows').glob('*.wflow')):
        data=path.read_bytes(); relative=path.relative_to(root).as_posix()
        case={'id':'WF-'+sha(relative.encode())[:12], 'path':relative, 'source_sha256':sha(data),
              'name':path.name, 'purpose':'', 'authored':True, 'runnable':False, 'live_verified':False,
              'user_accepted':False, 'blockers':[], 'inputs':[], 'expected_outputs':[], 'applications':[],
              'verification_criteria':['Source revision matches inventory', 'Returned files exist with matching digest and valid format'],
              'model_call_bound':0, 'category':'development'}
        if path.name.startswith('image-redesign-acceptance-'):
            case['category']='authoring-rehearsal'
        try:
            text=data.decode('utf-8-sig'); sections=_parse(text)
            definition=next(s for s in sections if s['kind']=='workflow')
            case.update(name=definition['fields'].get('name',path.name),purpose=definition['fields'].get('purpose',''),definition_id=definition['id'])
            try:
                validate_workspace_authoring_shape(text)
                case['authoring_shape_valid']=True
            except WorkflowSourceExecutionError as error:
                case['authoring_shape_valid']=False
                case['blockers'].append(str(error))
            plan=compile_prompt_workflow(text)
            case['compiles']=True
            case['model_call_bound']=sum(0 if s.human_review else s.max_tool_calls+1 if s.agent_task else 0 if s.tool_name else 1 for s in plan.steps)
            case['ai_task_count']=sum(not s.human_review and not s.tool_name for s in plan.steps)
            case['human_review_count']=sum(bool(s.human_review) for s in plan.steps)
            for key,fields in plan.inputs.items():
                settings=fields.get('settings',{})
                case['inputs'].append({'name':fields.get('name',key),'path':settings.get('workspace_file'),
                    'inline':bool(settings.get('input_text'))})
                if settings.get('workspace_file'):
                    target=WorkspacePath(str(root)).resolve(settings['workspace_file'])
                    if not target.is_file():case['blockers'].append(f'Missing input file: {settings["workspace_file"]}')
            for step in plan.steps:
                if step.server_id:case['applications'].append(step.server_id)
                if step.save:case['expected_outputs'].append({'kind':'file','path':step.output_path,'format':step.output_format,'policy':step.file_policy})
                if step.application:
                    case['expected_outputs'].append({'kind':step.application.get('kind','application_resource'),'source':step.application['source']})
                    case['verification_criteria'].append('Inspect the resulting resource identity and revision through the application; completion text is insufficient.')
                if step.cad:
                    case['expected_outputs'].append({'kind':'cad_model','source':step.cad['source'],'edit_mode':step.cad.get('edit_mode')})
                    case['expected_outputs'].extend({'kind':'file','path':e['path'],'format':e['format'],'policy':e.get('policy','indexed')} for e in step.cad.get('exports',[]))
                    if step.cad['source']=='workspace':
                        f=WorkspacePath(str(root)).resolve(step.cad['file'])
                        item={'name':'CAD model','path':step.cad['file'],'preserve':step.cad.get('edit_mode')=='copy'}
                        if f.is_file():item['sha256']=sha(f.read_bytes())
                        else:case['blockers'].append(f'Missing CAD file: {step.cad["file"]}')
                        case['inputs'].append(item)
                    if step.cad['source']=='session':case['blockers'].append('Select and verify the intended open application document before this run.')
                    case['verification_criteria'].append('Review task-specific dimensions/properties independently; file format alone is insufficient.')
            case['applications']=sorted(set(case['applications']))
            case['blockers'].append('Live application/model availability and engineering oracle not yet verified for this source revision.')
        except (WorkflowSourceExecutionError,ValueError,StopIteration) as error:
            case.update(compiles=False);case['blockers'].append(str(error))
        cases.append(case)
    return {'schema_version':1,'program':'workflow-development','target':100,
            'qualification_counts_unchanged':True,'created_at':datetime.now(timezone.utc).isoformat(),
            'workspace':str(root),'cases':cases,'planned_cases':planned_scenarios()}


def verify_output(root, output):
    """Structural checks only; model/analysis oracles remain separately required."""
    path=WorkspacePath(str(root)).resolve(output['output_path'],must_exist=True)
    data=path.read_bytes()
    if not data or len(data)!=output['output_bytes']:raise ValueError('Output size differs from the run record.')
    if output.get('sha256') and sha(data)!=output['sha256']:raise ValueError('Output digest differs from the run record.')
    suffix=path.suffix.lower()
    if suffix in {'.html','.htm'}:
        text=data.decode('utf-8').lower()
        if '<html' not in text or '</html>' not in text:raise ValueError('Output is not a complete HTML document.')
    elif suffix=='.json':json.loads(data)
    elif suffix in {'.step','.stp'}:
        if not data.lstrip().startswith(b'ISO-10303-21;') or b'END-ISO-10303-21;' not in data:raise ValueError('Invalid STEP exchange structure.')
    elif suffix in {'.psm','.par','.asm','.dft'}:
        if not data.startswith(bytes.fromhex('d0cf11e0a1b11ae1')):raise ValueError('Invalid native compound-document header.')
    elif suffix in {'.png','.jpg','.jpeg','.gif','.webp'}:
        from .workflow_references import image_media_type
        image_media_type(path.name,data)
        # Signature and digest only: rendering/content review is separate evidence.
    elif suffix not in {'.txt','.md','.csv'}:
        raise ValueError(f'No format oracle registered for {suffix}; cannot count as verified.')
    return {'path':output['output_path'],'sha256':sha(data),'bytes':len(data),'check':'structure','passed':True}


async def run_case(case, *, root, api, session, timeout, client):
    attempt={'id':uuid4().hex,'case_id':case['id'],'source_sha256':case['source_sha256'],
             'started_at':datetime.now(timezone.utc).isoformat(),'profile':'live','status':'running',
             'events':[],'checks':[],'user_accepted':False}
    try:
        original={i['path']:sha(WorkspacePath(str(root)).resolve(i['path'],must_exist=True).read_bytes()) for i in case['inputs'] if i.get('preserve')}
        async with asyncio.timeout(timeout):
            response=await client.get(api+'/api/workspace/workflow-sources',params={'session_id':session,'path':case['path']})
            response.raise_for_status(); document=response.json()
            if sha(document['source'].encode())!=case['source_sha256']:
                raise ValueError('Workflow changed since inventory. Refresh and review its manifest entry.')
            async with client.stream('POST',api+'/api/workspace/workflow-sources/run',json={'session_id':session,'path':case['path'],'expected_storage_digest':document['storage_digest']},headers={'accept':'application/x-ndjson'}) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line:continue
                    event=json.loads(line);attempt['events'].append(event)
                    if event['kind']=='failed':raise ValueError(event.get('message','Workflow failed'))
                    if event['kind'] in {'completed','pending_review'}:
                        if 'result' in attempt:raise ValueError('Duplicate terminal workflow receipt; inspect the saved run before retrying.')
                        result=event['result']
                        if event['kind']=='pending_review':
                            review=result.get('review',{})
                            if result.get('status')!='pending_review' or review.get('state')!='pending' or not review.get('review_id'):
                                raise ValueError('Invalid pending-review receipt; no human decision or acceptance is inferred.')
                        elif result.get('status')=='pending_review':
                            raise ValueError('Completed receipt conflicts with pending-review result.')
                        attempt['result']=result
                        attempt['terminal_event']=event['kind']
            if 'result' not in attempt:raise ValueError('Connection ended without a terminal workflow receipt; inspect the saved run log before retrying.')
            for output in attempt['result'].get('outputs',[]):attempt['checks'].append(verify_output(root,output))
            from .workflow_campaign_oracles import verify_engineering_assertions
            assertions=case.get('engineering_assertions',[])
            attempt['checks'].extend(verify_engineering_assertions(attempt['result'],assertions))
            for path,digest in original.items():
                if sha(WorkspacePath(str(root)).resolve(path,must_exist=True).read_bytes())!=digest:raise ValueError(f'Original model changed: {path}')
                attempt['checks'].append({'path':path,'check':'original_unchanged','passed':True})
            if not attempt['checks']:raise ValueError('No output oracle ran; completion alone is insufficient.')
            pending=attempt['terminal_event']=='pending_review'
            attempt['status']='pending_review' if pending else 'engineering_verified' if assertions else 'structure_verified'
            attempt['engineering_assertions']=assertions
            attempt['engineering_review_required']=pending or any(o['kind'] in {'cad_model','analysis','application_resource'} for o in case['expected_outputs'])
            if pending:
                attempt.update(review=attempt['result']['review'],live_verified=False,human_decision_submitted=False)
    except TimeoutError:
        attempt.update(status='timed_out',error='Observation timed out. The server may have partial operations; inspect its run record before rerunning.')
    except Exception as error:
        attempt.update(status='failed',error=str(error))
    ended=datetime.now(timezone.utc).isoformat()
    attempt['observation_ended_at']=ended
    if attempt.get('terminal_event') in {'completed','pending_review'}:attempt['execution_ended_at']=ended
    if attempt['status']!='pending_review':attempt['completed_at']=ended
    attempt['call_metrics']=observed_call_metrics(attempt['events'])
    return attempt


def observed_call_metrics(events):
    """Count recorded execution events, never infer calls from block count.

    Agent decisions can contain transport-level corrections/retries not exposed
    in these events. They are recorded separately, not billed/model-call totals.
    """
    active={}; ai_started=ai_completed=agent_started=decisions=direct_tools=0
    tool_started=tool_recorded=tool_succeeded=tool_failed=0
    for event in events:
        kind=event.get('kind') or event.get('type')
        if kind=='step_started':
            execution=event.get('execution_kind')
            active[event.get('task_id')]=execution
            ai_started+=execution=='ai'
            agent_started+=execution=='mcp_task'
            direct_tools+=execution=='mcp'
        elif kind=='step_completed':
            ai_completed+=active.pop(event.get('task_id'),None)=='ai'
        elif kind=='task_progress' and isinstance(event.get('available_tools'),list):
            decisions+=1
        elif kind=='tool_started':tool_started+=1
        elif kind=='tool_completed':
            tool_recorded+=1
            tool_succeeded+=event.get('status')=='succeeded'
            tool_failed+=event.get('status') in {'failed','invalid_arguments'}
    return dict(ai_calls_started=ai_started,ai_calls_completed=ai_completed,
                agent_tasks_started=agent_started,agent_decisions_started=decisions,
                direct_tool_steps_started=direct_tools,mcp_tool_calls_started=tool_started,
                mcp_tool_results_recorded=tool_recorded,mcp_tool_calls_succeeded=tool_succeeded,
                mcp_tool_calls_failed=tool_failed,model_transport_calls=None,
                basis='Recorded step/tool events; Engineer review is not an AI call. Agent transport retries, tokens and billing are unavailable.')


async def run_campaign(manifest, *, ids, api, session, output_dir, max_runs=3, max_model_calls=40, timeout=600, concurrency=1):
    import httpx
    if not 1<=max_runs<=20 or not 1<=concurrency<=4 or not 1<=timeout<=3600 or not 1<=max_model_calls<=500:
        raise ValueError('Use bounded runs (1–20), concurrency (1–4), timeout (1–3600s) and model calls (1–500).')
    cases=[c for c in manifest['cases'] if c['id'] in ids]
    if not ids or set(ids)!={c['id'] for c in cases}:raise ValueError('Select explicit known workflow IDs.')
    if len(cases)>max_runs or sum(c['model_call_bound'] for c in cases)>max_model_calls:raise ValueError('Selected workflows exceed the campaign budget.')
    if any(not c['compiles'] for c in cases):raise ValueError('A selected workflow does not compile.')
    if any(c.get('authoring_shape_valid') is False for c in cases):raise ValueError('A selected workflow has invalid workspace authoring fields.')
    # Application calls remain serial across cases sharing a server. No claim of
    # a dollar budget: model decisions are bounded; vendor billing is external.
    locks={app:asyncio.Lock() for c in cases for app in c['applications']}
    semaphore=asyncio.Semaphore(concurrency)
    root=Path(manifest['workspace']);output_dir=Path(output_dir);output_dir.mkdir(parents=True,exist_ok=True)
    async with httpx.AsyncClient(timeout=timeout) as client:
        async def run(case):
            from contextlib import AsyncExitStack
            async with semaphore, AsyncExitStack() as stack:
                for app in sorted(case['applications']):await stack.enter_async_context(locks[app])
                result=await run_case(case,root=root,api=api,session=session,timeout=timeout,client=client)
                path=output_dir/(result['id']+'.json')
                with path.open('x',encoding='utf-8') as stream:json.dump(result,stream,indent=2)
                return result
        return await asyncio.gather(*(run(c) for c in cases))
