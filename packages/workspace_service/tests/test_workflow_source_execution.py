from __future__ import annotations
import asyncio
import json
from types import SimpleNamespace
import pytest
from workspace_service.workflow_source_execution import compile_prompt_workflow, execute_prompt_workflow, prepare_prompt_workflow, validate_response, WorkflowSourceExecutionError
from workspace_service.adapters.filesystem import LocalWorkspaceFiles


def task(key='report', prompt='Write a short report.', fmt='html', **settings):
    values = {'output_format': fmt, 'output_filename': f'{key}.' + {'html':'html','text':'txt','markdown':'md','json':'json'}[fmt], **settings}
    return f'''task {key}
  name: "{key}"
  step_type: work
  performed_by: ai_assisted
  inputs: [{{"key":"{key}_prompt","kind":"engineering_document","name":"Prompt","required":false}}]
  outputs: [{{"key":"{key}_response","kind":"engineering_document","name":"Response"}}]
  prompt: {json.dumps(prompt)}
  settings: {json.dumps(values)}
  tool: null
  reusable_step: null
end
'''


def source(*tasks, links=()):
    result = 'workflow test\n  name: "Test workflow"\nend\n' + ''.join(tasks)
    for i, (a, b) in enumerate(links):
        result += f'connection edge_{i}\n  type: item\n  from: "{a}.{a}_response"\n  to: "{b}.{b}_prompt"\n  label: "Prompt"\n  when: null\nend\n'
    return result


def service(root, text=''):
    adapter = LocalWorkspaceFiles.__new__(LocalWorkspaceFiles)
    adapter.workspace_dir = str(root)
    async def write_generated(workspace_dir, path, content, policy):
        return await asyncio.to_thread(adapter.write_generated, path, content.encode(), policy)
    async def write_generated_bytes(workspace_dir, path, content, policy):
        return await asyncio.to_thread(adapter.write_generated, path, content, policy)
    async def read(*args):
        return SimpleNamespace(source=text, storage_digest='a'*64)
    return SimpleNamespace(files=SimpleNamespace(write_generated=write_generated,write_generated_bytes=write_generated_bytes), workflow_sources=SimpleNamespace(read=read))


HTML='<!doctype html><html><body>Report</body></html>'


def test_model_timeout_preserves_completed_output_and_names_current_failure(tmp_path):
    plan = compile_prompt_workflow(source(
        task('first', fmt='text', save_output=True),
        task('second', prompt_source='connection', prompt_input='second_prompt'),
        links=[('first', 'second')]))
    async def generate(prompt, fmt):
        if fmt == 'html':
            raise TimeoutError('The model did not finish responding within 180 seconds.')
        return 'Completed design input'
    with pytest.raises(WorkflowSourceExecutionError) as error:
        asyncio.run(execute_prompt_workflow(service=service(tmp_path), workspace_dir=str(tmp_path),
            plan=plan, input_values={}, response_generator=generate))
    assert error.value.code == 'MODEL_TIMEOUT'
    assert 'Model Setup' not in error.value.correction
    assert 'shorter response' in error.value.correction
    assert (tmp_path / 'first.txt').read_text() == 'Completed design input'
    assert not (tmp_path / 'second.html').exists()


def test_chained_response_is_prompt_and_only_terminal_step_saves(tmp_path):
    plan = compile_prompt_workflow(source(task('first',fmt='text'),task('second',prompt='',prompt_source='connection',prompt_input='second_prompt'), links=[('first','second')]))
    calls=[]
    async def generate(prompt, fmt):
        calls.append((prompt,fmt))
        return 'Write an HTML report about steel.' if fmt=='text' else HTML
    result=asyncio.run(execute_prompt_workflow(service=service(tmp_path),workspace_dir=str(tmp_path),plan=plan,input_values={},response_generator=generate))
    assert calls==[('Write a short report.','text'),('Write an HTML report about steel.','html')]
    assert len(result['outputs'])==1
    assert result['outputs'][0]['output_path']=='second.html'
    assert not (tmp_path/'first.txt').exists()
    assert (tmp_path/'second.html').read_text()==HTML
    assert result['steps'][1]['prompt']==calls[1][0]


def test_intermediate_copy_and_each_terminal_branch_saves(tmp_path):
    plan=compile_prompt_workflow(source(task('first',fmt='text',save_output=True),task('a',prompt_source='connection',prompt_input='a_prompt'),task('b',fmt='markdown',prompt_source='connection',prompt_input='b_prompt'),links=[('first','a'),('first','b')]))
    async def generate(prompt,fmt): return HTML if fmt=='html' else 'Response'
    result=asyncio.run(execute_prompt_workflow(service=service(tmp_path),workspace_dir=str(tmp_path),plan=plan,input_values={},response_generator=generate))
    assert {item['output_path'] for item in result['outputs']}=={'first.txt','a.html','b.md'}


def test_indexed_names_are_exclusive_across_concurrent_runs(tmp_path):
    plan=compile_prompt_workflow(source(task()))
    async def generate(prompt,fmt): return HTML
    async def run():
        return await asyncio.gather(*(execute_prompt_workflow(service=service(tmp_path),workspace_dir=str(tmp_path),plan=plan,input_values={},response_generator=generate) for _ in range(6)))
    results=asyncio.run(run())
    assert {r['output_path'] for r in results}=={'report.html',*(f'report-{n:03d}.html' for n in range(1,6))}
    assert all(path.read_text()==HTML for path in tmp_path.glob('*.html'))
    assert not list(tmp_path.glob('.wright-output-*'))


def test_overwrite_only_after_all_responses_validate(tmp_path):
    existing=tmp_path/'report.html';existing.write_text('previous report')
    plan=compile_prompt_workflow(source(task(file_policy='overwrite')))
    async def invalid(prompt,fmt): return 'not HTML'
    with pytest.raises(WorkflowSourceExecutionError):
        asyncio.run(execute_prompt_workflow(service=service(tmp_path),workspace_dir=str(tmp_path),plan=plan,input_values={},response_generator=invalid))
    assert existing.read_text()=='previous report'
    async def valid(prompt,fmt): return HTML
    result=asyncio.run(execute_prompt_workflow(service=service(tmp_path),workspace_dir=str(tmp_path),plan=plan,input_values={},response_generator=valid))
    assert result['output_path']=='report.html'
    assert existing.read_text()==HTML
    assert not (tmp_path/'report-001.html').exists()


@pytest.mark.parametrize('policy', ['indexed', 'overwrite'])
def test_completed_document_survives_downstream_failure_without_replacing_previous_file(tmp_path, policy):
    (tmp_path/'first.txt').write_text('previous design')
    plan = compile_prompt_workflow(source(
        task('first', fmt='text', save_output=True, file_policy=policy),
        task('second', prompt_source='connection', prompt_input='second_prompt'),
        links=[('first', 'second')]))
    events = []
    async def emit(event): events.append(event)
    async def generate(prompt, fmt):
        if fmt == 'html':
            raise RuntimeError('Supplier login required')
        return 'Completed new design'
    with pytest.raises(RuntimeError, match='Supplier login required'):
        asyncio.run(execute_prompt_workflow(service=service(tmp_path), workspace_dir=str(tmp_path),
            plan=plan, input_values={}, response_generator=generate, on_event=emit))
    assert (tmp_path/'first.txt').read_text() == 'previous design'
    saved = [event for event in events if event['kind'] == 'output_saved']
    if policy == 'indexed':
        assert (tmp_path/'first-001.txt').read_text() == 'Completed new design'
        assert [event['output_path'] for event in saved] == ['first-001.txt']
        assert any(event['kind'] == 'result_ready' for event in events)
    else:
        assert not (tmp_path/'first-001.txt').exists()
        assert not saved


@pytest.mark.parametrize('settings',[{'output_filename':'../report.html'},{'output_filename':'.git/report.html'},{'output_filename':'report.txt'},{'file_policy':'unknown'},{'file_policy':[]},{'output_format':{}},{'prompt_source':[]},{'prompt_source':'connection'},{'save_output':'false'}])
def test_invalid_settings_rejected_before_generation(settings):
    with pytest.raises(WorkflowSourceExecutionError): compile_prompt_workflow(source(task(**settings)))


def test_cycle_and_shared_overwrite_rejected():
    with pytest.raises(WorkflowSourceExecutionError,match='cycle'):
        compile_prompt_workflow(source(task('a',prompt_source='connection',prompt_input='a_prompt'),task('b',prompt_source='connection',prompt_input='b_prompt'),links=[('a','b'),('b','a')]))
    with pytest.raises(WorkflowSourceExecutionError,match='overwrite'):
        compile_prompt_workflow(source(task('a',output_filename='same.html',file_policy='overwrite',save_output=True),task('b',output_filename='same.html'),links=[('a','b')]))


def test_unchanged_digest_required_and_missing_prompt_fails(tmp_path):
    text=source(task())
    with pytest.raises(WorkflowSourceExecutionError,match='changed'):
        asyncio.run(prepare_prompt_workflow(service=service(tmp_path,text),workspace_dir=str(tmp_path),path='workflows/test.workflow.wflow',expected_digest='b'*64))
    with pytest.raises(WorkflowSourceExecutionError,match='enter a prompt'):
        compile_prompt_workflow(source(task(prompt='')))


def test_response_formats():
    assert validate_response('```json\n{"ok":true}\n```','json')=='{"ok":true}'
    assert validate_response('# Report','markdown')=='# Report'
    assert validate_response('text','text')=='text'
    with pytest.raises(WorkflowSourceExecutionError): validate_response('{broken','json')
    with pytest.raises(WorkflowSourceExecutionError): validate_response('NaN','json')


def test_step_events_capture_actual_prompt_and_written_path(tmp_path):
    plan=compile_prompt_workflow(source(task()))
    events=[]
    async def emit(event): events.append(event)
    async def generate(prompt,fmt): return HTML
    asyncio.run(execute_prompt_workflow(service=service(tmp_path),workspace_dir=str(tmp_path),plan=plan,input_values={},response_generator=generate,on_event=emit))
    assert [e['kind'] for e in events]==['step_started','step_completed','result_ready','output_saved']
    assert events[0]['prompt']=='Write a short report.'
    assert events[-1]['output_path']=='report.html'
