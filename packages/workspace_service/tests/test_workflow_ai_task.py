import asyncio
import json

import pytest

from workspace_service.workflow_source_execution import compile_prompt_workflow, execute_prompt_workflow, WorkflowSourceExecutionError
from packages.workspace_service.tests.test_workflow_source_execution import task, source, service
from packages.workspace_service.tests.test_workflow_mcp_execution import runtime


def plan(**settings):
    return compile_prompt_workflow(source(task("research", fmt="text", authoring_template="mcp-task", mcp_server="docs", **settings)))


def done(response, evidence=(1,)):
    return {"role": "assistant", "content": json.dumps({"status": "completed", "response": response, "evidence": list(evidence)})}


def call(query="bracket", name="tool_0"):
    return {"role": "assistant", "content": None, "tool_calls": [{"id": "call_1", "type": "function", "function": {"name": name, "arguments": json.dumps({"query": query})}}]}


def test_ai_task_discovers_tools_calls_twice_and_feeds_downstream(tmp_path):
    workflow = compile_prompt_workflow(source(
        task("research", fmt="text", authoring_template="mcp-task", mcp_server="docs"),
        task("report", fmt="text", prompt="", prompt_source="connection", prompt_input="report_prompt"),
        links=[("research", "report")]))
    gateway, runner = runtime()
    replies = iter([call("bracket"), call("sheet metal"), done("Verified findings", (1,2))])
    seen, events = [], []
    async def decide(messages, tools, **kwargs):
        seen.append((list(messages), tools, kwargs))
        return next(replies)
    async def generate(prompt, fmt):
        assert prompt == "Verified findings"
        return "Report from verified findings"
    async def emit(event):
        events.append(event)
    result = asyncio.run(execute_prompt_workflow(service=service(tmp_path), workspace_dir=str(tmp_path), plan=workflow,
        input_values={}, response_generator=generate, action_generator=decide, tool_runtime=runner, on_event=emit))
    assert len(gateway.calls) == 2
    assert seen[0][2]["required"] is False and seen[-1][2]["required"] is False
    assert all(t["function"]["name"] == "tool_0" for t in seen[0][1])
    assert '"documents"' in seen[1][0][-1]["content"]
    assert len(result["steps"][0]["tool_calls"]) == 2
    assert [e["kind"] for e in events].count("tool_completed") == 2
    from workspace_service.workflow_mcp_execution import schema_digest
    progress = [e for e in events if e['kind'] == 'task_progress']
    assert len(progress) == 3
    assert all(e['available_tools'] == [{'alias':'tool_0',
        'tool':runner.task_tools(workflow.steps[0])[0].name,
        'schema_digest':schema_digest(runner.task_tools(workflow.steps[0])[0])}]
        for e in progress)
    assert not (tmp_path / "research.txt").exists()
    assert (tmp_path / "report.txt").read_text() == "Report from verified findings"


@pytest.mark.parametrize("change_during_decision", [False, True])
def test_task_refreshes_catalog_before_deciding_but_checks_contract_again_before_call(tmp_path, change_during_decision):
    from dataclasses import replace
    from packages.workspace_service.tests.test_workflow_mcp_execution import TOOL
    updated = replace(TOOL, input_schema={**TOOL.input_schema, "properties":{
        **TOOL.input_schema["properties"], "locale":{"type":"string"}}}, provenance={"server_revision":"live"})
    gateway, runner = runtime()
    catalog = [TOOL]
    gateway.list_tools = lambda *_: tuple(catalog)
    actions = 0
    async def decide(messages, tools, **kwargs):
        nonlocal actions
        actions += 1
        assert tools[0]["function"]["name"] == "tool_0"
        if actions == 1:
            if change_during_decision:
                catalog[0] = updated
            return call("first query")
        assert "locale" in tools[0]["function"]["parameters"]["properties"]
        return call("second query") if actions == 2 else done("Both current tools used", (1,2))
    original_call = gateway.call_tool
    async def invoke(*args, **kwargs):
        result = await original_call(*args, **kwargs)
        catalog[0] = updated
        return result
    gateway.call_tool = invoke
    async def execute():
        return await execute_prompt_workflow(service=service(tmp_path),workspace_dir=str(tmp_path),plan=plan(),
            input_values={},response_generator=None,action_generator=decide,tool_runtime=runner)
    if change_during_decision:
        with pytest.raises(WorkflowSourceExecutionError, match="definition has changed"):
            asyncio.run(execute())
        assert not gateway.calls
    else:
        asyncio.run(execute())
        assert len(gateway.calls) == 2


@pytest.mark.parametrize("replies,expected", [
    ([{"content": "Done"}], "evidence"),
    ([call(name="another_server")], "outside"),
    ([call(), call()], "again"),
])
def test_task_refuses_unsupported_or_unevidenced_completion(tmp_path, replies, expected):
    gateway, runner = runtime()
    actions = iter(replies)
    async def decide(*args, **kwargs): return next(actions)
    with pytest.raises(WorkflowSourceExecutionError, match=expected):
        asyncio.run(execute_prompt_workflow(service=service(tmp_path), workspace_dir=str(tmp_path), plan=plan(),
            input_values={}, response_generator=None, action_generator=decide, tool_runtime=runner))
    assert not list(tmp_path.iterdir())


def test_limit_does_not_make_one_extra_tool_call(tmp_path):
    gateway, runner = runtime()
    actions = iter([call("first"), call("second")])
    async def decide(*args, **kwargs): return next(actions)
    with pytest.raises(WorkflowSourceExecutionError, match="limit"):
        asyncio.run(execute_prompt_workflow(service=service(tmp_path), workspace_dir=str(tmp_path), plan=plan(max_tool_calls=1),
            input_values={}, response_generator=None, action_generator=decide, tool_runtime=runner))
    assert len(gateway.calls) == 1


@pytest.mark.parametrize('name,official,allowed', [
    ('browser_navigate', True, True),
    ('browser_click', True, False),
    ('browser_navigate', False, False),
])
def test_browser_navigation_can_repeat_without_allowing_duplicate_mutations(tmp_path, name, official, allowed):
    from dataclasses import replace
    from packages.workspace_service.tests.test_workflow_mcp_execution import TOOL
    tool = replace(TOOL, tool_name=name, provenance={'source_url':
        'https://github.com/microsoft/playwright-mcp' if official else 'https://example.com/other'})
    gateway, runner = runtime()
    gateway.list_tools = lambda *_: (tool,)
    replies = iter([call(), call(), done('Revisited the same page', (1, 2))])
    async def decide(*args, **kwargs): return next(replies)
    async def run():
        return await execute_prompt_workflow(service=service(tmp_path), workspace_dir=str(tmp_path), plan=plan(),
            input_values={}, response_generator=None, action_generator=decide, tool_runtime=runner)
    if allowed:
        asyncio.run(run())
        assert len(gateway.calls) == 2
    else:
        with pytest.raises(WorkflowSourceExecutionError, match='requested again'):
            asyncio.run(run())
        assert len(gateway.calls) == 1


def test_cancel_interrupts_pending_decision_without_files(tmp_path):
    gateway, runner = runtime()
    async def scenario():
        entered = asyncio.Event()
        async def decide(*args, **kwargs):
            entered.set()
            await asyncio.Future()
        work = asyncio.create_task(execute_prompt_workflow(service=service(tmp_path), workspace_dir=str(tmp_path), plan=plan(),
            input_values={}, response_generator=None, action_generator=decide, tool_runtime=runner))
        await entered.wait()
        work.cancel()
        with pytest.raises(asyncio.CancelledError): await work
    asyncio.run(scenario())
    assert not gateway.calls and not list(tmp_path.iterdir())


@pytest.mark.parametrize("settings", [{"mcp_server": ""}, {"max_tool_calls": 0}, {"max_tool_calls": True}, {"max_tool_calls": 33}, {"max_tool_calls": 1.5}, {"timeout_seconds": 601}])
def test_task_preflight_rejects_missing_server_and_invalid_limits(settings):
    configuration = {"authoring_template": "mcp-task", "mcp_server": "docs", **settings}
    with pytest.raises(WorkflowSourceExecutionError):
        compile_prompt_workflow(source(task(fmt="text", **configuration)))


def test_task_limit_32_compiles_and_defaults_and_time_ceiling_are_preserved():
    assert plan(max_tool_calls=32, timeout_seconds=600).steps[0].max_tool_calls == 32
    default = plan().steps[0]
    assert default.max_tool_calls == 8 and default.timeout_seconds == 300


@pytest.mark.parametrize('finish_at_limit', [False, True])
def test_full_32_call_budget_completes_or_blocks_33rd_call(tmp_path, finish_at_limit):
    gateway, runner = runtime()
    replies = iter([*(call(f'observation {index}') for index in range(32)),
                    done('All observations collected', tuple(range(1, 33))) if finish_at_limit else call('33rd')])
    async def decide(*args, **kwargs):
        return next(replies)
    async def run():
        return await execute_prompt_workflow(service=service(tmp_path), workspace_dir=str(tmp_path),
            plan=plan(max_tool_calls=32), input_values={}, response_generator=None,
            action_generator=decide, tool_runtime=runner)
    if finish_at_limit:
        result = asyncio.run(run())
        assert len(result['steps'][0]['tool_calls']) == 32
    else:
        with pytest.raises(WorkflowSourceExecutionError, match='limit'):
            asyncio.run(run())
        assert not list(tmp_path.iterdir())
    assert len(gateway.calls) == 32


@pytest.mark.parametrize("state", ["missing", "empty", "unchanged"])
def test_task_cannot_claim_a_file_it_did_not_produce(tmp_path, state):
    from workspace_service.workflow_references import snapshot_task_files, verify_task_files
    target = tmp_path / "part.step"
    if state != "missing": target.write_text("old CAD" if state == "unchanged" else "")
    before = snapshot_task_files(str(tmp_path), ("part.step",))
    with pytest.raises(WorkflowSourceExecutionError, match="expected file"):
        verify_task_files(str(tmp_path), ("part.step",), before)


def test_verified_tool_file_is_exposed_with_digest(tmp_path):
    gateway, runner = runtime()
    actions = iter([call(), done("Verified tool-created file")])
    async def decide(*args, **kwargs):
        action = next(actions)
        if not action.get("tool_calls"): (tmp_path / "part.step").write_text("tool-created CAD fixture")
        return action
    result = asyncio.run(execute_prompt_workflow(service=service(tmp_path), workspace_dir=str(tmp_path),
        plan=plan(expected_files="part.step"), input_values={}, response_generator=None,
        action_generator=decide, tool_runtime=runner))
    assert result["outputs"][0]["output_path"] == "part.step"
    assert len(result["outputs"][0]["sha256"]) == 64


def test_reference_contents_and_image_bytes_reach_the_model(tmp_path):
    from workspace_service.workflow_references import WorkflowReference
    workflow = compile_prompt_workflow(source(task(fmt="text")))
    from dataclasses import replace
    step = replace(workflow.steps[0], references=(("Document", "doc"), ("Image", "image")))
    workflow = replace(workflow, steps=(step,))
    image = WorkflowReference.from_bytes("fixture.png", b"\x89PNG\r\n\x1a\nfixture", image=True)
    doc = WorkflowReference.from_bytes("brief.md", b"Actual design brief: 12 mm flange", image=False)
    async def generate(prompt, fmt, **kwargs):
        assert "Actual design brief: 12 mm flange" in prompt
        assert kwargs["images"] == [image.image_url]
        return "The actual document and image were supplied"
    asyncio.run(execute_prompt_workflow(service=service(tmp_path), workspace_dir=str(tmp_path), plan=workflow,
        input_values={"doc":doc, "image":image}, response_generator=generate))


def test_mcp_task_receives_image_on_each_decision_and_records_reference_identity(tmp_path):
    from workspace_service.workflow_references import WorkflowReference
    image_input = '''input image
  name: "Sketch"
  provided_by: engineer
  inputs: []
  outputs: [{"key":"image_response","kind":"reference_images","name":"Sketch","quantity":"one"}]
  settings: {"input_mode":"workspace-file","workspace_file":"sketch.png"}
end
'''
    research = task("research", fmt="text", authoring_template="mcp-task", mcp_server="docs").replace(
        '"key":"research_prompt","kind":"engineering_document"', '"key":"research_prompt","kind":"reference_images"')
    workflow = compile_prompt_workflow(source(image_input, research, links=[("image","research")]))
    image = WorkflowReference.from_bytes("sketch.png", b"\x89PNG\r\n\x1a\nfixture", image=True)
    gateway, runner = runtime()
    actions = iter([call(), done("Used the supplied sketch and tool result")])
    decisions = []
    async def decide(messages, tools, **kwargs):
        content = next(m["content"] for m in messages if m["role"] == "user")
        assert content[0]["type"] == "text" and "sketch.png" in content[0]["text"]
        assert content[1] == {"type":"image_url", "image_url":{"url":image.image_url}}
        decisions.append(True)
        return next(actions)
    result = asyncio.run(execute_prompt_workflow(service=service(tmp_path), workspace_dir=str(tmp_path),
        plan=workflow, input_values={"image":image}, response_generator=None, action_generator=decide, tool_runtime=runner))
    assert len(decisions) == 2 and len(gateway.calls) == 1
    assert result["steps"][0]["references"] == [{"path":"sketch.png", "sha256":image.sha256, "kind":"image"}]


@pytest.mark.parametrize("path,data,image", [("bad.png", b"text", True), ("file.pdf", b"%PDF\x00\xff", False), ("empty.txt", b"", False)])
def test_unreadable_reference_fails_explicitly(path, data, image):
    from workspace_service.workflow_references import WorkflowReference
    with pytest.raises(ValueError): WorkflowReference.from_bytes(path, data, image=image)


def test_task_reports_missing_requirements_without_an_unrelated_tool_call(tmp_path):
    gateway, runner = runtime()
    async def decide(*args, **kwargs):
        return {"content": json.dumps({"status":"blocked", "response":"Provide the sheet thickness before creating the design.", "evidence":[]})}
    with pytest.raises(WorkflowSourceExecutionError, match="sheet thickness") as error:
        asyncio.run(execute_prompt_workflow(service=service(tmp_path), workspace_dir=str(tmp_path), plan=plan(),
            input_values={}, response_generator=None, action_generator=decide, tool_runtime=runner))
    assert error.value.code == "TASK_BLOCKED"
    assert not gateway.calls and not list(tmp_path.iterdir())


def test_fabricated_completion_evidence_does_not_pass(tmp_path):
    gateway, runner = runtime()
    actions = iter([call(), done("Success claimed", (99,))])
    async def decide(*args, **kwargs): return next(actions)
    with pytest.raises(WorkflowSourceExecutionError, match="evidence"):
        asyncio.run(execute_prompt_workflow(service=service(tmp_path), workspace_dir=str(tmp_path), plan=plan(),
            input_values={}, response_generator=None, action_generator=decide, tool_runtime=runner))
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("state", ["completed", "failed", "cancelled"])
def test_run_record_survives_completion_failure_and_cancellation(tmp_path, state):
    from workspace_service.workflow_run_record import record_workflow_run
    async def execute(emit):
        await emit({"kind":"tool_started", "tool":"docs__search", "arguments":{"query":"bracket"}})
        # Inspect the on-disk checkpoint while execution is still in progress.
        checkpoint=json.loads(next((tmp_path/'runs/example').glob('*.json')).read_text())
        assert checkpoint['status']=='running' and checkpoint['events'][-1]['kind']=='tool_started'
        if state == "failed": raise RuntimeError("server unavailable")
        if state == "cancelled": raise asyncio.CancelledError()
        return {"outputs":[], "steps":[]}
    async def scenario():
        try:
            await record_workflow_run(service=service(tmp_path), workspace_dir=str(tmp_path), source_path="workflows/example.workflow.wflow",
                source_digest="a"*64, execute=execute)
        except (RuntimeError, asyncio.CancelledError): pass
    asyncio.run(scenario())
    files=list((tmp_path / "runs/example").glob("*.json"))
    assert len(files) == 1
    record=json.loads(files[0].read_text())
    assert record["status"] == state and record["events"][-1]["tool"] == "docs__search"
    assert record["source_digest"] == "a"*64


def test_read_only_tool_can_be_rechecked_within_call_budget(tmp_path):
    from dataclasses import replace
    from packages.workspace_service.tests.test_workflow_mcp_execution import TOOL
    gateway, runner = runtime()
    readable = replace(TOOL, annotations={"readOnlyHint": True})
    gateway.list_tools = lambda *args: (readable,)
    actions = iter([call(), call(), done("Rechecked the current result", (2,))])
    async def decide(*args, **kwargs): return next(actions)
    asyncio.run(execute_prompt_workflow(service=service(tmp_path), workspace_dir=str(tmp_path), plan=plan(),
        input_values={}, response_generator=None, action_generator=decide, tool_runtime=runner))
    assert len(gateway.calls) == 2
