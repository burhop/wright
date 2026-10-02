"""Binary handoffs carry verified metadata to scoped AI tools, never document text."""

import asyncio
import hashlib
import json

import pytest

from workspace_service.workflow_source_execution import (
    WorkflowSourceExecutionError,
    compile_prompt_workflow,
    execute_prompt_workflow,
)
from .test_workflow_ai_task import call, done
from .test_workflow_mcp_execution import edge, mcp, runtime
from .test_workflow_source_execution import service, source, task


def graph(*, agent=True, dependency="native.dat"):
    producer = mcp(
        mcp_arguments=json.dumps({"query": "Create opaque fixture file"}),
        mcp_argument_ports="{}",
        expected_files="native.dat",
        expected_file_ports={"search_result": "native.dat"},
    ).replace('"kind":"structured_result"', '"kind":"workspace_file"')
    consumer = task(
        "consume",
        fmt="text",
        prompt="Inspect the connected native file through the selected tool.",
        **({"authoring_template": "mcp-task", "mcp_server": "docs"} if agent else {}),
        mcp_file_dependencies={"consume_prompt": dependency},
    ).replace('"kind":"engineering_document"', '"kind":"workspace_file"', 1)
    return source(producer, consumer) + edge(
        "search.search_result", "consume.consume_prompt"
    )


def test_ai_dependency_compiles_and_plain_ai_rejects_tool_files():
    plan = compile_prompt_workflow(graph())
    assert plan.steps[-1].file_dependencies == {"search.search_result": "native.dat"}
    with pytest.raises(WorkflowSourceExecutionError, match="require a configured tool"):
        compile_prompt_workflow(graph(agent=False))


@pytest.mark.parametrize("dependency", ["../outside", "/absolute", "C:/outside"])
def test_ai_dependency_rejects_non_workspace_locators(dependency):
    with pytest.raises(WorkflowSourceExecutionError):
        compile_prompt_workflow(graph(dependency=dependency))


@pytest.mark.parametrize("behavior", ["unchanged", "changed", "missing", "wrong_path"])
def test_binary_metadata_is_pinned_before_the_ai_consumer(tmp_path, behavior):
    payload = b"OPAQUE_FIXTURE_CONTENT\x00\xff\x80"
    plan = compile_prompt_workflow(
        graph(dependency="other.dat" if behavior == "wrong_path" else "native.dat")
    )
    gateway, runner = runtime()
    original = gateway.call_tool

    async def produce(*args, **kwargs):
        if len(gateway.calls) == 0:
            (tmp_path / "native.dat").write_bytes(payload)
        return await original(*args, **kwargs)

    gateway.call_tool = produce
    messages = []
    events = []
    replies = iter([call("Read the verified fixture file"), done("Fixture inspection")])

    async def generate(*args, **kwargs):
        raise AssertionError("No plain model or document reader is used")

    async def decide(turn, *args, **kwargs):
        messages.append(turn)
        return next(replies)

    async def emit(event):
        events.append(event)
        if event["kind"] == "step_completed" and event["task_id"] == "search":
            if behavior == "changed":
                (tmp_path / "native.dat").write_bytes(b"changed bytes")
            elif behavior == "missing":
                (tmp_path / "native.dat").unlink()

    async def execute():
        return await execute_prompt_workflow(
            service=service(tmp_path),
            workspace_dir=str(tmp_path),
            plan=plan,
            input_values={},
            response_generator=generate,
            action_generator=decide,
            tool_runtime=runner,
            on_event=emit,
        )

    if behavior != "unchanged":
        with pytest.raises(WorkflowSourceExecutionError, match="connected file"):
            asyncio.run(execute())
        assert not messages and len(gateway.calls) == 1
        diagnostic = events[-1]
        assert diagnostic["kind"] == "step_diagnostic"
        assert diagnostic["task_id"] == "consume"
        assert diagnostic["code"] == "WORKFLOW_NOT_READY"
        assert "connected file" in diagnostic["message"]
        assert not any(
            event["kind"] == "step_started" and event["task_id"] == "consume"
            for event in events
        )
        return
    result = asyncio.run(execute())
    prompt = json.dumps(messages[0])
    assert hashlib.sha256(payload).hexdigest() in prompt
    assert "native.dat" in prompt and "contents are not inlined" in prompt
    assert "OPAQUE_FIXTURE_CONTENT" not in prompt
    consumer = next(step for step in result["steps"] if step["task_id"] == "consume")
    assert consumer["references"] == [
        {
            "path": "native.dat",
            "sha256": hashlib.sha256(payload).hexdigest(),
            "kind": "workspace_file",
            "source_port": "search.search_result",
        }
    ]
