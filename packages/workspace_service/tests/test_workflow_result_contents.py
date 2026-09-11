"""Content handoff contracts; no application/model execution is simulated as live."""
import asyncio
import hashlib
import json
from dataclasses import replace
import pytest
from workspace_service.workflow_references import reference_from_result
from workspace_service.workflow_results import EngineeringResult, Representation, Provenance
from workspace_service.workflow_source_execution import compile_prompt_workflow, execute_prompt_workflow, WorkflowSourceExecutionError
from packages.workspace_service.tests.test_workflow_source_execution import service, source, task


def exported(data=b'Use a 25 mm flange.', *, path='export.md', fmt='markdown'):
    return EngineeringResult('run:producer:export', 'file', path,
        (Representation('workspace_file',path,fmt,durability='persistent',
                        sha256=hashlib.sha256(data).hexdigest(),size_bytes=len(data)),),
        Provenance('run','producer','export'))


def reader(root):
    host = service(root)
    async def read_reference(workspace_dir, path):
        from workspace_service.workspace_path import WorkspacePath
        return WorkspacePath(workspace_dir).resolve(path,must_exist=True).read_bytes()
    host.files.read_reference = read_reference
    return host


@pytest.mark.parametrize('prompt_source', [False, True])
def test_named_export_contents_reach_downstream_prompt_with_identity(tmp_path,prompt_source):
    data=b'Use a 25 mm flange.'
    (tmp_path/'export.md').write_bytes(data)
    workflow=compile_prompt_workflow(source(task(fmt='text')))
    step=replace(workflow.steps[0],prompt_from='producer.export' if prompt_source else None,
                 references=() if prompt_source else (('Export','producer.export'),))
    workflow=replace(workflow,steps=(step,))
    async def generate(prompt,fmt):
        assert data.decode() in prompt
        if prompt_source: assert prompt==data.decode()
        return 'Verified document response'
    result=asyncio.run(execute_prompt_workflow(service=reader(tmp_path),workspace_dir=str(tmp_path),plan=workflow,
        input_values={'producer.export':exported(data)},response_generator=generate))
    assert result['steps'][0]['references']==[{'path':'export.md','sha256':hashlib.sha256(data).hexdigest(),'kind':'text'}]


def test_named_image_export_reaches_model_as_pixels(tmp_path):
    data=b'\xff\xd8\xfftest-image'
    (tmp_path/'view.jpg').write_bytes(data)
    workflow=compile_prompt_workflow(source(task(fmt='text')))
    workflow=replace(workflow,steps=(replace(workflow.steps[0],references=(('View','producer.export'),)),))
    async def generate(prompt,fmt,*,images):
        assert images[0].startswith('data:image/jpeg;base64,')
        assert 'view.jpg' in prompt
        return 'Image received'
    asyncio.run(execute_prompt_workflow(service=reader(tmp_path),workspace_dir=str(tmp_path),plan=workflow,
        input_values={'producer.export':exported(data,path='view.jpg',fmt='screenshot_jpeg')},response_generator=generate))


@pytest.mark.parametrize('problem', ['changed','missing','unverified','binary','cloud','ambiguous','model'])
def test_result_contents_fail_explicitly_without_model_call(tmp_path,problem):
    value=exported()
    (tmp_path/'export.md').write_bytes(b'Use a 25 mm flange.')
    if problem=='changed': (tmp_path/'export.md').write_bytes(b'Use a 99 mm flange.')
    if problem=='missing': (tmp_path/'export.md').unlink()
    if problem=='unverified': value=replace(value,representations=(replace(value.representations[0],sha256=None),))
    if problem=='binary': value=replace(value,representations=(replace(value.representations[0],format='step'),))
    if problem=='cloud': value=replace(value,representations=(Representation('cloud_resource','https://example.invalid/export.md','markdown',provider_id='cloud',resource_id='export'),))
    if problem=='ambiguous': value=replace(value,representations=(value.representations[0],replace(value.representations[0],location='second.md')))
    if problem=='model': value=replace(value,kind='cad_model')
    with pytest.raises(WorkflowSourceExecutionError) as error:
        asyncio.run(reference_from_result(value,service=reader(tmp_path),workspace_dir=str(tmp_path),task_title='Read export'))
    assert error.value.correction


@pytest.mark.parametrize('image_export', [True, False])
def test_compiled_cad_export_connection_reads_pixels_or_rejects_binary(tmp_path, image_export):
    """Exercise compiler, CAD export collection and consuming model in one run."""
    from packages.workspace_service.tests.test_workflow_cad import CadGateway, settings
    from workspace_service.workflow_mcp_execution import WorkflowMcpRuntime
    from tool_registry.gateway_models import GatewayToolResult

    fmt, path = ('screenshot_jpeg', 'view.jpg') if image_export else ('step', 'model.step')
    data = b'\xff\xd8\xfftest-cad-preview' if image_export else b'ISO-10303-21;\nEND-ISO-10303-21;'
    config = settings()
    config.update(save_native=False, exports=[{'format': fmt, 'path': path, 'port': 'cad_response'}])
    cad = task('cad', fmt='text', authoring_template='mcp-task', mcp_server='cad', cad=json.dumps(config))
    cad = cad.replace('"kind":"engineering_document","name":"Response"', '"kind":"workspace_file","name":"Export"')
    consumer = task('review', fmt='text')
    plan = compile_prompt_workflow(source(cad, consumer, links=[('cad', 'review')]))
    assert plan.steps[0].output_ports == (('cad_response', 'workspace_file'),)
    gateway = CadGateway()
    original_call = gateway.call_tool
    async def call(session, request, name, args, **kwargs):
        if name == 'cad.list_providers':
            return GatewayToolResult(content=(), structured_content={'result': [dict(providerId='solid_edge', isDefault=True, capabilities={'exports': [fmt]})]})
        result = await original_call(session, request, name, args, **kwargs)
        if name == 'cad.export_document':
            from pathlib import Path
            Path(args['outputPath']).write_bytes(data)
        return result
    gateway.call_tool = call
    decisions = 0
    async def decide(messages, tools, **kwargs):
        nonlocal decisions
        decisions += 1
        if decisions == 1:
            selected = next(t for t in tools if 'cad.set_variable' in t['function']['description'])
            return {'role': 'assistant', 'tool_calls': [{'id': 'one', 'type': 'function', 'function': {'name': selected['function']['name'], 'arguments': '{}'}}]}
        return {'role': 'assistant', 'content': json.dumps({'status': 'completed', 'response': 'Model inspected.', 'evidence': [1]})}
    model_calls = []
    async def generate(prompt, output_format, *, images):
        model_calls.append(prompt)
        assert image_export
        import base64
        assert base64.b64decode(images[0].split(',', 1)[1]) == data
        assert 'contents are not inlined' not in prompt
        return 'Preview reviewed.'
    async def execute():
        return await execute_prompt_workflow(service=reader(tmp_path), workspace_dir=str(tmp_path), plan=plan,
            input_values={}, response_generator=generate, action_generator=decide,
            tool_runtime=WorkflowMcpRuntime(gateway, workspace_id='workspace', session_id='session'))
    if image_export:
        result = asyncio.run(execute())
        assert len(model_calls) == 1
        assert result['steps'][1]['references'] == [{'path': path, 'sha256': hashlib.sha256(data).hexdigest(), 'kind': 'image'}]
        assert result['results'][0]['exports'][0]['representations'][0]['sha256'] == hashlib.sha256(data).hexdigest()
    else:
        with pytest.raises(WorkflowSourceExecutionError, match='cannot be read as document contents'):
            asyncio.run(execute())
        assert not model_calls
    assert any(name == 'cad.export_document' for name, _ in gateway.calls)


@pytest.mark.parametrize('whole_arguments', [True, False])
@pytest.mark.parametrize('changed', [True, False])
def test_exact_mcp_consumes_verified_exported_text_or_json(tmp_path, whole_arguments, changed):
    from packages.workspace_service.tests.test_workflow_mcp_execution import mcp, edge, runtime
    data=b'{"query":"bend relief","limit":2}' if whole_arguments else b'bend relief'
    filename='arguments.json' if whole_arguments else 'query.txt'
    (tmp_path/filename).write_bytes(b'changed' if changed else data)
    opts={'mcp_arguments_source':'connection','mcp_arguments_input':'search_query'} if whole_arguments else {}
    workflow=compile_prompt_workflow(source(task('producer',fmt='json'),mcp(**opts))+edge('producer.producer_response','search.search_query'))
    workflow=replace(workflow,steps=(workflow.steps[1],))
    gateway,tool_runtime=runtime()
    async def execute():
        return await execute_prompt_workflow(service=reader(tmp_path),workspace_dir=str(tmp_path),plan=workflow,
            input_values={'producer.producer_response':exported(data,path=filename,fmt='json' if whole_arguments else 'text')},
            response_generator=None,tool_runtime=tool_runtime)
    if changed:
        with pytest.raises(WorkflowSourceExecutionError,match='changed after it was produced'):
            asyncio.run(execute())
        assert not gateway.calls
    else:
        result=asyncio.run(execute())
        assert gateway.calls[0][0][3]=={'query':'bend relief','limit':2 if whole_arguments else 3}
        assert result['steps'][0]['references']==[{'path':filename,'sha256':hashlib.sha256(data).hexdigest(),'kind':'text'}]
