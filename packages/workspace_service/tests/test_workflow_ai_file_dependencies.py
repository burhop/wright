"""Binary handoffs carry verified metadata to scoped AI tools, never document text."""

import asyncio
import hashlib
import json
from dataclasses import replace
from types import SimpleNamespace

import pytest

from workspace_service.workflow_source_execution import (
    WorkflowSourceExecutionError,
    compile_prompt_workflow,
    execute_prompt_workflow,
)
from .test_workflow_ai_task import call, done, source
from .test_workflow_mcp_execution import edge, mcp, runtime
from .test_workflow_source_execution import service, task
from workspace_service.workflow_references import (
    WorkflowReference,
    verified_file_dependencies,
)


@pytest.mark.parametrize(
    "behavior", ["unchanged", "changed", "missing", "not_exported"]
)
def test_cad_export_identity_reaches_declared_binary_dependency(tmp_path, behavior):
    from .test_workflow_cad import CadGateway, settings
    from .test_workflow_ai_task import legacy_instruction_profile
    from .test_workflow_mcp_execution import TOOL
    from tool_registry.gateway_models import GatewayToolResult
    from workspace_service.workflow_mcp_execution import WorkflowMcpRuntime
    from workspace_service.workflow_source_execution import PromptStep, PromptWorkflow

    config = settings()
    config.update(
        save_native=False,
        exports=[{"format": "step", "path": "model.step", "port": "export"}],
    )
    if behavior == "not_exported":
        config["exports"] = []
    first = PromptStep(
        "first",
        "Export selected CAD",
        "Inspect and export selected model.",
        None,
        (),
        "text",
        "",
        False,
        "indexed",
        (("model", "cad_model"), ("export", "workspace_file")),
        server_id="cad",
        agent_task=True,
        cad=config,
        instruction_set=legacy_instruction_profile(),
    )
    consumer = replace(
        first,
        id="consume",
        title="Inspect exact CAD export",
        cad=None,
        server_id="docs",
        references=(("file", "first.export"),),
        file_dependencies={"first.export": "model.step"},
        output_ports=(("response", "engineering_document"),),
    )

    class Gateway(CadGateway):
        def list_tools(self, *args):
            return (*super().list_tools(*args), TOOL)

        async def call_tool(self, session, request, name, args, **kwargs):
            if name == TOOL.name:
                self.calls.append((name, dict(args)))
                return GatewayToolResult(
                    content=(),
                    structured_content={
                        "result": hashlib.sha256(
                            (tmp_path / "model.step").read_bytes()
                        ).hexdigest()
                    },
                )
            return await super().call_tool(session, request, name, args, **kwargs)

    gateway = Gateway()
    runner = WorkflowMcpRuntime(gateway, workspace_id="workspace", session_id="session")
    events, messages = [], []
    count = 0

    async def decide(turn, tools, **kwargs):
        nonlocal count
        count += 1
        messages.append(turn)
        if count % 2 == 0:
            return done("Actual provider evidence")
        chosen = next(
            t
            for t in tools
            if ("cad.set_variable" if count == 1 else TOOL.tool_name)
            in t["function"]["description"]
        )
        args = (
            {"active": True} if count == 1 else {"query": "Inspect exact exported STEP"}
        )
        return {
            "role": "assistant",
            "tool_calls": [
                {
                    "id": str(count),
                    "type": "function",
                    "function": {
                        "name": chosen["function"]["name"],
                        "arguments": json.dumps(args),
                    },
                }
            ],
        }

    async def emit(event):
        events.append(event)
        if event["kind"] == "step_completed" and event["task_id"] == "first":
            if behavior == "changed":
                (tmp_path / "model.step").write_bytes(b"changed")
            if behavior == "missing":
                (tmp_path / "model.step").unlink()

    async def execute():
        return await execute_prompt_workflow(
            service=service(tmp_path),
            workspace_dir=str(tmp_path),
            plan=PromptWorkflow("CAD export handoff", (first, consumer), {}),
            input_values={},
            response_generator=None,
            action_generator=decide,
            tool_runtime=runner,
            on_event=emit,
        )

    if behavior != "unchanged":
        with pytest.raises(WorkflowSourceExecutionError, match="connected file"):
            asyncio.run(execute())
        assert count == 2
        assert not any(name == TOOL.name for name, _ in gateway.calls)
        if behavior == "not_exported":
            assert not any(
                e["kind"] == "step_completed" and e["task_id"] == "first"
                for e in events
            )
        return
    asyncio.run(execute())
    expected = hashlib.sha256((tmp_path / "model.step").read_bytes()).hexdigest()
    assert expected in json.dumps(messages[2])
    assert "contents are not inlined" in json.dumps(messages[2])
    assert any(name == TOOL.name for name, _ in gateway.calls)


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


@pytest.mark.parametrize(
    "binding",
    [
        {"source": "latest"},
        {"source": "connected_output", "path": "guessed.dat"},
        {},
        [],
        None,
        1,
    ],
)
def test_connected_dependency_requires_the_exact_typed_binding(binding):
    with pytest.raises(WorkflowSourceExecutionError, match="file dependencies"):
        compile_prompt_workflow(graph(dependency=binding))


def test_connected_dependency_rejects_a_receipt_for_another_output(tmp_path):
    from workspace_service.workflow_results import file_result, Provenance

    plan = compile_prompt_workflow(graph(dependency={"source": "connected_output"}))
    value = file_result(
        {
            "output_path": "native.dat",
            "sha256": "a" * 64,
            "output_format": "dat",
            "output_bytes": 10,
        },
        Provenance("run", "other-producer", "other-port"),
    )
    with pytest.raises(WorkflowSourceExecutionError, match="another connected output"):
        verified_file_dependencies(
            plan.steps[-1], {"search.search_result": value}, str(tmp_path)
        )


@pytest.mark.parametrize("behavior", ["unchanged", "changed", "missing", "wrong_path"])
@pytest.mark.parametrize("connected", [False, True])
def test_binary_metadata_is_pinned_before_the_ai_consumer(
    tmp_path, behavior, connected
):
    payload = b"OPAQUE_FIXTURE_CONTENT\x00\xff\x80"
    plan = compile_prompt_workflow(
        graph(
            dependency="other.dat"
            if behavior == "wrong_path"
            else ({"source": "connected_output"} if connected else "native.dat")
        )
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


@pytest.mark.parametrize(
    "behavior",
    ["unchanged", "changed", "missing", "wrong_path", "wrong_size", "no_size"],
)
def test_supplied_file_dependency_preserves_prepared_identity(tmp_path, behavior):
    content = b'{"profile":"opaque fixture input"}'
    file = tmp_path / "profile.json"
    file.write_bytes(content)
    pinned = WorkflowReference.from_bytes("profile.json", content, image=False)
    if behavior == "changed":
        file.write_bytes(b"changed bytes")
    elif behavior == "missing":
        file.unlink()
    elif behavior == "wrong_path":
        pinned = replace(pinned, path="another.json")
    elif behavior == "wrong_size":
        pinned = replace(pinned, size_bytes=len(content) + 1)
    elif behavior == "no_size":
        pinned = replace(pinned, size_bytes=None)
    step = SimpleNamespace(
        title="Consume prepared file", file_dependencies={"input.file": "profile.json"}
    )
    if behavior != "unchanged":
        with pytest.raises(WorkflowSourceExecutionError, match="connected file"):
            verified_file_dependencies(step, {"input.file": pinned}, str(tmp_path))
        return
    records = verified_file_dependencies(step, {"input.file": pinned}, str(tmp_path))
    assert records == [
        {
            "path": "profile.json",
            "sha256": hashlib.sha256(content).hexdigest(),
            "kind": "workspace_file",
            "source_port": "input.file",
        }
    ]


@pytest.mark.parametrize("agent", [False, True])
@pytest.mark.parametrize("changed", [False, True])
def test_supplied_file_reaches_exact_and_ai_tool_consumers(tmp_path, agent, changed):
    content = b"opaque prepared profile"
    (tmp_path / "profile.json").write_bytes(content)
    pinned = WorkflowReference.from_bytes("profile.json", content, image=False)
    if changed:
        (tmp_path / "profile.json").write_bytes(b"changed after preparation")
    declared = """input supplied
  name: "Prepared profile"
  provided_by: engineer
  inputs: []
  outputs: [{"key":"file","name":"File","kind":"workspace_file"}]
  settings: {"value_source":"file","file_path":"profile.json"}
end
"""
    if agent:
        consumer = task(
            "consume",
            fmt="text",
            prompt="Use the prepared file.",
            authoring_template="mcp-task",
            mcp_server="docs",
            mcp_file_dependencies={"consume_prompt": "profile.json"},
        )
        consumer = consumer.replace(
            '"kind":"engineering_document"', '"kind":"workspace_file"', 1
        )
        target = "consume.consume_prompt"
    else:
        consumer = mcp(
            mcp_arguments=json.dumps({"query": "Use prepared profile"}),
            mcp_argument_ports="{}",
            mcp_file_dependencies={"search_query": "profile.json"},
        )
        consumer = consumer.replace(
            '"kind":"engineering_document"', '"kind":"workspace_file"', 1
        )
        target = "search.search_query"
    plan = compile_prompt_workflow(
        source(declared, consumer) + edge("supplied.file", target)
    )
    gateway, runner = runtime()
    replies = iter([call("Inspect prepared profile"), done("Fixture result")])
    prompts = []

    async def decide(prompt, *args, **kwargs):
        prompts.append(prompt)
        return next(replies)

    async def generate(*args, **kwargs):
        raise AssertionError("No plain model calls")

    async def execute():
        return await execute_prompt_workflow(
            service=service(tmp_path),
            workspace_dir=str(tmp_path),
            plan=plan,
            input_values={"supplied": pinned},
            response_generator=generate,
            action_generator=decide,
            tool_runtime=runner,
        )

    if changed:
        with pytest.raises(
            WorkflowSourceExecutionError, match="connected file changed"
        ):
            asyncio.run(execute())
        assert not gateway.calls and not prompts
        return
    result = asyncio.run(execute())
    assert len(gateway.calls) == 1
    record = result["steps"][0]
    assert record["references"] == [
        {
            "path": "profile.json",
            "sha256": pinned.sha256,
            "kind": "workspace_file",
            "source_port": "supplied.file",
        }
    ]
    if agent:
        assert pinned.sha256 in json.dumps(prompts[0])
        assert "opaque prepared profile" not in json.dumps(prompts[0])
