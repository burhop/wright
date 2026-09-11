import asyncio
import json
from dataclasses import replace
from pathlib import Path
import pytest
from tool_registry.gateway_models import GatewayTool, GatewayToolResult
from workspace_service.workflow_cad import CadDocument, CadTask, parse_cad
from workspace_service.workflow_mcp_execution import WorkflowMcpRuntime
from workspace_service.workflow_source_execution import PromptStep, WorkflowSourceExecutionError, compile_prompt_workflow
from packages.workspace_service.tests.test_workflow_source_execution import task, source
from packages.workspace_service.tests.test_workflow_mcp_execution import Gateway


def settings(**patch):
    return dict(source='session', document_id='original', edit_mode='in_place', save_native=True,
                native_path='model.psm', policy='indexed', exports=[], **patch)


class CadGateway(Gateway):
    def __init__(self):
        self.calls=[]; self.docs=[{'documentId':'original','displayName':'Original','isDirty':True},{'documentId':'other','displayName':'Other','isDirty':False}]
    def list_tools(self,*args):
        names=['cad.list_providers','cad.list_documents','cad.open_document','cad.save_document','cad.export_document','cad.set_variable','cad.create_sheet_metal_from_recipe']
        return tuple(GatewayTool(name=n,server_id='cad',tool_name=n,description=n,input_schema={'type':'object','properties':{'providerId':{'type':'string'},'documentId':{'type':'string'},'active':{'type':'boolean'}}}, annotations={'readOnlyHint':n.startswith('cad.list_')}) for n in names)
    async def call_tool(self,session,request,name,args,**kw):
        self.calls.append((name,dict(args)))
        if name=='cad.list_providers': value=[{'providerId':'solid_edge','isDefault':True,'capabilities':{'exports':['step']}}]
        elif name=='cad.list_documents': value=list(self.docs)
        elif name=='cad.open_document': value=self.docs[0]
        else:
            doc=next(d for d in self.docs if d['documentId']==args['documentId'])
            if args.get('copy'):
                doc={**doc,'documentId':'copy','displayName':'Copy'};self.docs.append(doc)
            if 'outputPath' in args:
                Path(args['outputPath']).write_bytes(b'CAD result '+str(len(self.calls)).encode())
            if name=='cad.save_document':doc['isDirty']=False
            value={'isSuccess':True,'document':dict(doc)}
        return GatewayToolResult(content=(),structured_content={'result':value})


def runner(root,config=None,responses=None):
    gateway=CadGateway(); runtime=WorkflowMcpRuntime(gateway,workspace_id='workspace',session_id='session')
    step=PromptStep('edit','Edit model','Enlarge the flange.',None,(),'text','',False,'indexed',server_id='cad',agent_task=True,cad=config or settings(),cad_from='create.model')
    async def emit(*a,**kw):pass
    return gateway,CadTask(runtime,step,str(root),responses or {},emit)


@pytest.mark.parametrize('document', [None, {'documentId': 'original'}])
def test_native_material_discovery_is_read_only_and_provider_bound(tmp_path, document):
    _, run = runner(tmp_path, {**settings(), 'source': 'new'})
    run.caps = {'provider_id': 'solid_edge'}
    run.document = document
    tool = GatewayTool(
        name='materials', server_id='cad', tool_name='cad.list_materials',
        description='Read exact installed native material names.',
        input_schema={'type': 'object', 'additionalProperties': False, 'properties': {
            'providerId': {'type': 'string'}, 'query': {'type': 'string'},
            'library': {'type': 'string'}, 'limit': {'type': 'integer'},
            'offset': {'type': 'integer'},
        }}, annotations={'readOnlyHint': True},
    )
    assert run.allows_tool(tool)
    arguments = {'query': '5052', 'library': 'Materials-DIN', 'limit': 25, 'offset': 0}
    assert run.guard(tool, dict(arguments)) == {**arguments, 'providerId': 'solid_edge'}
    with pytest.raises(WorkflowSourceExecutionError, match='different CAD provider'):
        run.guard(tool, {'providerId': 'other'})
    untrusted_tool = replace(tool, annotations={'readOnlyHint': False})
    assert not run.allows_tool(untrusted_tool)
    with pytest.raises(WorkflowSourceExecutionError, match='cannot be bound'):
        run.guard(untrusted_tool, {})


def test_active_window_change_does_not_redirect_edits_or_exports(tmp_path):
    config=settings();config['exports']=[{'format':'step','path':'model.step','port':'export'}]
    g,run=runner(tmp_path,config)
    async def scenario():
        await run.start()
        g.docs.reverse()  # User activates a different document while the AI works.
        tool=next(t for t in run.runtime.task_tools(run.step) if t.tool_name=='cad.set_variable')
        assert run.guard(tool,{'active':True})=={'active':False,'providerId':'solid_edge','documentId':'original'}
        ref,files=await run.finish()
        assert ref.document['documentId']=='original'
        assert {f['output_path'] for f in files}=={'model.psm','model.step'}
        assert all(a['documentId']=='original' for n,a in g.calls if n in {'cad.save_document','cad.export_document'})
    asyncio.run(scenario())


def test_copy_uses_in_memory_save_and_leaves_original_dirty(tmp_path):
    cfg=settings();cfg.update(edit_mode='copy',copy_path='copy.psm')
    (tmp_path/'copy.psm').write_bytes(b'previous')
    g,run=runner(tmp_path,cfg)
    async def scenario():
        await run.start();assert run.document['documentId']=='copy'
        ref,files=await run.finish();assert ref.document['documentId']=='copy'
        assert [f['output_path'] for f in files]==['copy-001.psm']
    asyncio.run(scenario())
    assert g.docs[0]['isDirty'] is True
    assert (tmp_path/'copy.psm').read_bytes()==b'previous'
    assert next(a for n,a in g.calls if n=='cad.save_document')['copy'] is True


def test_upstream_document_cannot_cross_server_or_reopen_by_filename(tmp_path):
    cfg=settings();cfg.update(source='upstream',from_port='model')
    _,run=runner(tmp_path,cfg,{'create.model':CadDocument('different',{'documentId':'original'})})
    with pytest.raises(WorkflowSourceExecutionError,match='different server'):asyncio.run(run.start())
    g,run=runner(tmp_path,cfg,{'create.model':CadDocument('cad',{'documentId':'closed'})})
    with pytest.raises(WorkflowSourceExecutionError,match='no longer open'):asyncio.run(run.start())
    assert not any(n=='cad.open_document' for n,a in g.calls)


def test_closed_model_and_unsupported_export_fail_without_saving(tmp_path):
    g,run=runner(tmp_path)
    async def scenario():
        await run.start();g.docs=[]
        with pytest.raises(WorkflowSourceExecutionError,match='closed'):await run.finish()
    asyncio.run(scenario());assert not list(tmp_path.iterdir())
    cfg=settings();cfg['exports']=[{'format':'invented','path':'file.bad'}]
    _,run=runner(tmp_path,cfg)
    with pytest.raises(WorkflowSourceExecutionError,match='unavailable'):asyncio.run(run.start())


@pytest.mark.parametrize('patch',[{'native_path':'../escape.psm'},{'source':'session','document_id':''},{'source':'upstream','from_port':''},{'save_native':False,'exports':[]}])
def test_missing_target_or_final_deliverables_rejected_before_execution(patch):
    cfg=settings();cfg.update(patch)
    with pytest.raises(WorkflowSourceExecutionError):parse_cad(json.dumps(cfg),terminal=True)


def test_final_cad_saves_model_without_forcing_narrative_file():
    plan=compile_prompt_workflow(source(task('cad',fmt='text',authoring_template='mcp-task',mcp_server='cad',cad=json.dumps(settings()))))
    assert plan.steps[0].cad['document_id']=='original'
    assert not plan.steps[0].save


def test_retargeting_another_document_is_rejected(tmp_path):
    _,run=runner(tmp_path)
    async def scenario():
        await run.start()
        tool=next(t for t in run.runtime.task_tools(run.step) if t.tool_name=='cad.set_variable')
        with pytest.raises(WorkflowSourceExecutionError,match='different CAD document'):run.guard(tool,{'documentId':'other'})
    asyncio.run(scenario())


@pytest.mark.parametrize('selector', [None, {}, {'active': True}, {'documentId': 'original', 'active': True}])
def test_inspection_pins_nested_document_to_task_model(tmp_path, selector):
    _, run = runner(tmp_path, settings())
    run.caps = {'provider_id': 'solid_edge'}
    run.document = {'documentId': 'original'}
    tool = GatewayTool(name='inspect', server_id='cad', tool_name='cad.verify_inspection_requirements',
                       description='Inspect native geometry', input_schema={'type':'object','properties':{'request':{'type':'object'},'providerId':{'type':'string'}}},
                       annotations={'readOnlyHint':True})
    requirements = [{'id':'body', 'kind':'body_count'}]
    arguments = {'request': {'document':selector, 'requirements':requirements}}
    guarded = run.guard(tool, arguments)
    assert guarded['request']['document'] == {'documentId':'original', 'active':False}
    assert guarded['request']['requirements'] == requirements
    assert guarded['providerId'] == 'solid_edge'


@pytest.mark.parametrize('inspection_request', [None, [], {'document':[]}, {'document':{'documentId':'other'}}, {'document':{'documentId':'other','active':True}}])
def test_inspection_rejects_invalid_or_unrelated_nested_document(tmp_path, inspection_request):
    _, run = runner(tmp_path, settings())
    run.caps = {'provider_id':'solid_edge'}
    run.document = {'documentId':'original'}
    tool = GatewayTool(name='inspect',server_id='cad',tool_name='cad.verify_inspection_requirements',
                       description='Inspect native geometry',input_schema={'type':'object','properties':{'request':{'type':'object'}}},
                       annotations={'readOnlyHint':True})
    with pytest.raises(WorkflowSourceExecutionError):
        run.guard(tool, {'request':inspection_request})


def test_model_reference_passes_through_two_tasks_independently_of_text(tmp_path):
    from workspace_service.workflow_source_execution import execute_prompt_workflow, PromptWorkflow
    from packages.workspace_service.tests.test_workflow_source_execution import service
    cfg=settings();cfg['save_native']=False
    first=PromptStep('first','First edit','Inspect the selected model.',None,(),'text','',False,'indexed',(('model','cad_model'),('response','text')),server_id='cad',agent_task=True,cad=cfg)
    second_cfg=settings();second_cfg.update(source='upstream',from_port='model')
    second=replace(first,id='second',title='Second edit',cad=second_cfg,cad_from='first.model')
    gateway=CadGateway();runtime=WorkflowMcpRuntime(gateway,workspace_id='workspace',session_id='session')
    decisions=0
    async def decide(messages,tools,**kwargs):
        nonlocal decisions
        decisions+=1
        if decisions%2:
            selected=next(t for t in tools if 'cad.list_variables' in t['function']['description']) if any('cad.list_variables' in t['function']['description'] for t in tools) else next(t for t in tools if 'cad.set_variable' in t['function']['description'])
            return {'role':'assistant','tool_calls':[{'id':str(decisions),'type':'function','function':{'name':selected['function']['name'],'arguments':'{"active":true}'}}]}
        return {'role':'assistant','content':json.dumps({'status':'completed','response':'Inspected the model.','evidence':[1]})}
    result=asyncio.run(execute_prompt_workflow(service=service(tmp_path),workspace_dir=str(tmp_path),plan=PromptWorkflow('Chain',(first,second),{}),input_values={},response_generator=None,action_generator=decide,tool_runtime=runtime))
    assert [s['cad_document']['documentId'] for s in result['steps']]==['original','original']
    assert [r['kind'] for r in result['results']] == ['cad_model', 'cad_model']
    assert len(result['results'][1]['representations']) == 2  # live document + saved native model
    assert result['results'][1]['provenance']['input_revisions'] == (('original', None),)
    assert [f['output_path'] for f in result['outputs']]==['model.psm']
    assert not list(tmp_path.glob('*.txt'))
    assert all(a['documentId']=='original' and a['active'] is False for n,a in gateway.calls if n=='cad.set_variable')


def test_upstream_revision_change_rejected_before_modifying(tmp_path):
    cfg=settings();cfg.update(source='upstream',from_port='model')
    g,run=runner(tmp_path,cfg,{'create.model':CadDocument('cad',{'documentId':'original','revision':'v1'})})
    g.docs[0]['revision']='v2'
    with pytest.raises(WorkflowSourceExecutionError,match='changed after'):
        asyncio.run(run.start())
    assert not any(n in {'cad.save_document','cad.set_variable'} for n,a in g.calls)


@pytest.mark.parametrize('state',['unchanged','dirty','changed_file'])
def test_handoff_retains_only_unchanged_native_representation(tmp_path,state):
    import hashlib
    from workspace_service.workflow_results import EngineeringResult,Representation,Provenance
    path=tmp_path/'model.psm';path.write_bytes(b'saved-model')
    native=Representation('workspace_file','model.psm','psm',durability='persistent',sha256=hashlib.sha256(path.read_bytes()).hexdigest(),size_bytes=path.stat().st_size)
    live=Representation('application_document','original',provider_id='cad:solid_edge',resource_id='original',durability='session')
    result=EngineeringResult('first:model','cad_model','Model',(live,native),Provenance('run','first','model'))
    cfg=settings();cfg.update(source='upstream',from_port='model',save_native=False,exports=[])
    gateway,run=runner(tmp_path,cfg,{'create.model':CadDocument('cad',{'documentId':'original'},result)})
    gateway.docs[0]['isDirty']=state=='dirty'
    if state=='changed_file':path.write_bytes(b'changed-model')
    async def scenario():
        await run.start();await run.finish()
        current=run.engineering_result('run')
        assert current.persistent==(state=='unchanged')
    asyncio.run(scenario())


def test_export_returns_post_export_document_state_without_saving_it(tmp_path):
    config=settings();config.update(save_native=False,exports=[{'format':'step','path':'model.step','port':'export'}])
    gateway,run=runner(tmp_path,config)
    gateway.docs[0]['isDirty']=False
    original_call=gateway.call_tool
    async def call(session,request,name,args,**kwargs):
        value=await original_call(session,request,name,args,**kwargs)
        if name=='cad.export_document':gateway.docs[0]['isDirty']=True
        return value
    gateway.call_tool=call
    events=[]
    async def emit(kind,**data):events.append({'kind':kind,**data})
    run.emit=emit
    async def scenario():
        await run.start()
        document,files=await run.finish()
        assert document.document['isDirty'] is True
        assert [f['output_path'] for f in files]==['model.step']
        assert any('modified during export' in e.get('message','') for e in events)
    asyncio.run(scenario())
    assert not any(name=='cad.save_document' for name,_ in gateway.calls)


def test_sheet_metal_task_excludes_unrelated_creation_contracts(tmp_path):
    _,run=runner(tmp_path,{**settings(),'source':'new'})
    tools=run.runtime.task_tools(run.step)
    sheet=next(t for t in tools if t.tool_name=='cad.create_sheet_metal_from_recipe')
    assert run.allows_tool(sheet)
    assert not run.allows_tool(replace(sheet,tool_name='cad.create_part_from_recipe'))
    assert not run.allows_tool(replace(sheet,tool_name='cad.create_assembly_from_recipe'))


def test_created_model_switches_to_bound_inspection_and_cannot_be_recreated(tmp_path):
    _, run = runner(tmp_path, {**settings(), 'source':'new'})
    sheet = next(t for t in run.runtime.task_tools(run.step)
                 if t.tool_name == 'cad.create_sheet_metal_from_recipe')
    inspect = replace(sheet, name='cad.measure_body_extents',
                      tool_name='cad.measure_body_extents', annotations={'readOnlyHint':True})
    assert run.allows_tool(sheet)
    run.caps = {'provider_id':'solid_edge'}
    run.observe(sheet, {'document':{'documentId':'created'}})
    assert not run.allows_tool(sheet)
    assert run.allows_tool(inspect)
    assert run.guard(inspect, {'active':True}) == {
        'providerId':'solid_edge', 'documentId':'created', 'active':False}
    with pytest.raises(WorkflowSourceExecutionError, match='not create a replacement'):
        run.guard(sheet, {})


def test_rejected_recipe_returns_correction_before_any_mutation(tmp_path):
    from workspace_service.workflow_mcp_execution import schema_digest
    g,run=runner(tmp_path,{**settings(),'source':'new'})
    template=next(t for t in g.list_tools() if t.tool_name=='cad.create_sheet_metal_from_recipe')
    validator=replace(template,name='cad.validate_sheet_metal_recipe',tool_name='cad.validate_sheet_metal_recipe',annotations={'readOnlyHint':True})
    original_tools=g.list_tools
    g.list_tools=lambda *a:(*original_tools(),validator)
    called=[]
    async def reject(session,request,name,args,**kwargs):
        called.append((name,args,kwargs))
        return GatewayToolResult(content=(),is_error=True,structured_content={'isValid':False,'issues':[{'code':'dimension_side','argument':'steps[0].dimensionSide','message':'Only outside is supported.','suggestedFix':'Use outside.'}]})
    async def scenario():
        await run.start()
        g.call_tool=reject
        with pytest.raises(WorkflowSourceExecutionError,match='Only outside is supported'):
            await run.validate_creation(template,{'recipe':{'mode':'commit'}})
    asyncio.run(scenario())
    assert called[0][0]=='cad.validate_sheet_metal_recipe'
    assert called[0][1]['recipe']['mode']=='preview'
    assert called[0][2]['timeout']==120
    assert not list(tmp_path.iterdir())
