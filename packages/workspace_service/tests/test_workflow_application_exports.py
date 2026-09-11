"""Local export adapter contracts; no installed application is invoked."""

import asyncio
import hashlib
import json
from dataclasses import replace
from pathlib import Path
import pytest
from tool_registry.gateway_models import GatewayToolResult
from workspace_service.workflow_mcp_execution import WorkflowMcpRuntime
from workspace_service.workflow_source_execution import (
    compile_prompt_workflow,
    execute_prompt_workflow,
    WorkflowSourceExecutionError,
)
from packages.workspace_service.tests.test_workflow_application_task import (
    PROFILE,
    CloudGateway,
)
from packages.workspace_service.tests.test_workflow_source_execution import (
    task,
    source,
    service,
)
from packages.workspace_service.tests.test_workflow_mcp_execution import edge


def local_exporter(monkeypatch, data, problem=None):
    monkeypatch.setitem(PROFILE, "export_path_argument", "output_path")
    monkeypatch.setitem(PROFILE, "formats", ["markdown"])
    gateway = CloudGateway()
    original_tools = gateway.list_tools

    def tools(*args):
        return tuple(
            replace(
                t,
                input_schema={
                    **t.input_schema,
                    "properties": {
                        **t.input_schema["properties"],
                        "output_path": {"type": "string"},
                    },
                },
            )
            if t.tool_name == "export"
            else t
            for t in original_tools(*args)
        )

    gateway.list_tools = tools
    original_call = gateway.call_tool

    async def call(session, request, name, args, **kwargs):
        if name == "export":
            gateway.calls.append((name, dict(args)))
            if problem != "missing":
                Path(args["output_path"]).write_bytes(
                    b"" if problem == "empty" else data
                )
            return GatewayToolResult(
                content=(),
                structured_content={
                    "format": "step" if problem == "format" else args["format"],
                    "isSuccess": True,
                },
            )
        return await original_call(session, request, name, args, **kwargs)

    gateway.call_tool = call
    return gateway


def plan(policy="indexed"):
    config = dict(
        source="new",
        output_port="model",
        exports=[
            dict(
                port="export",
                format="markdown",
                name="reports/analysis.md",
                policy=policy,
            )
        ],
    )
    producer = task(
        "analysis",
        fmt="text",
        authoring_template="mcp-task",
        mcp_server="cloud",
        application_resource=json.dumps(config),
    )
    producer = producer.replace(
        '"key":"analysis_response","kind":"engineering_document","name":"Response"',
        '"key":"export","kind":"workspace_file","name":"Analysis export"',
    )
    return compile_prompt_workflow(
        source(producer, task("review", fmt="text"))
        + edge("analysis.export", "review.review_prompt")
    )


async def decide(messages, tools, **kwargs):
    if not any(m.get("role") == "tool" for m in messages):
        alias = next(
            t["function"]["name"]
            for t in tools
            if t["function"]["description"].startswith("create:")
        )
        return {
            "role": "assistant",
            "tool_calls": [
                {
                    "id": "create",
                    "type": "function",
                    "function": {"name": alias, "arguments": "{}"},
                }
            ],
        }
    return {
        "role": "assistant",
        "content": json.dumps(
            {
                "status": "completed",
                "response": "Application result created.",
                "evidence": [1],
            }
        ),
    }


@pytest.mark.parametrize("policy", ["indexed", "overwrite"])
def test_application_exports_real_file_contents_to_next_block(
    tmp_path, monkeypatch, policy
):
    data = b"# Analysis\nVerified model export content."
    previous = tmp_path / "reports/analysis.md"
    previous.parent.mkdir()
    previous.write_bytes(b"Previous output")
    gateway = local_exporter(monkeypatch, data)
    svc = service(tmp_path)

    async def read_reference(root, path):
        return (tmp_path / path).read_bytes()

    svc.files.read_reference = read_reference

    async def generate(prompt, fmt):
        assert data.decode() in prompt
        return "Reviewed exported document."

    result = asyncio.run(
        execute_prompt_workflow(
            service=svc,
            workspace_dir=str(tmp_path),
            plan=plan(policy),
            input_values={},
            response_generator=generate,
            action_generator=decide,
            tool_runtime=WorkflowMcpRuntime(
                gateway, workspace_id="workspace", session_id="session"
            ),
        )
    )
    actual = "reports/analysis-001.md" if policy == "indexed" else "reports/analysis.md"
    assert (tmp_path / actual).read_bytes() == data
    if policy == "indexed":
        assert previous.read_bytes() == b"Previous output"
    assert {o["output_path"] for o in result["outputs"]} == {actual, "review.txt"}
    assert (
        len(result["results"]) == 2
    )  # model with grouped export, plus review; no duplicate export result
    exported = result["results"][0]["exports"][0]
    assert exported["representations"][0]["location"] == actual
    assert exported["representations"][0]["sha256"] == hashlib.sha256(data).hexdigest()
    assert (
        result["steps"][1]["references"][0]["sha256"]
        == hashlib.sha256(data).hexdigest()
    )
    assert not list(tmp_path.glob(".wright-export-*"))
    provider_path = next(
        args["output_path"] for name, args in gateway.calls if name == "export"
    )
    assert Path(provider_path).is_relative_to(tmp_path)
    assert not Path(provider_path).exists()


@pytest.mark.parametrize("problem", ["missing", "empty", "format"])
def test_failed_export_does_not_overwrite_previous_file_or_run_consumer(
    tmp_path, monkeypatch, problem
):
    previous = tmp_path / "reports/analysis.md"
    previous.parent.mkdir()
    previous.write_bytes(b"Previous output")
    gateway = local_exporter(monkeypatch, b"new", problem)

    async def generate(*args):
        pytest.fail("Consumer must not run after failed export")

    with pytest.raises(WorkflowSourceExecutionError):
        asyncio.run(
            execute_prompt_workflow(
                service=service(tmp_path),
                workspace_dir=str(tmp_path),
                plan=plan("overwrite"),
                input_values={},
                response_generator=generate,
                action_generator=decide,
                tool_runtime=WorkflowMcpRuntime(
                    gateway, workspace_id="workspace", session_id="session"
                ),
            )
        )
    assert previous.read_bytes() == b"Previous output"
    assert (
        len(list(tmp_path.glob(".wright-export-*"))) == 1
    )  # incomplete evidence is retained


def test_export_paths_are_validated_before_application_creation(tmp_path, monkeypatch):
    gateway = local_exporter(monkeypatch, b"new")
    workflow = plan()
    config = {
        **workflow.steps[0].application,
        "exports": [dict(port="export", format="markdown", name="../escape.md")],
    }
    workflow = replace(
        workflow,
        steps=(replace(workflow.steps[0], application=config), *workflow.steps[1:]),
    )
    with pytest.raises(WorkflowSourceExecutionError):
        asyncio.run(
            execute_prompt_workflow(
                service=service(tmp_path),
                workspace_dir=str(tmp_path),
                plan=workflow,
                input_values={},
                response_generator=None,
                action_generator=decide,
                tool_runtime=WorkflowMcpRuntime(
                    gateway, workspace_id="workspace", session_id="session"
                ),
            )
        )
    assert not gateway.calls


@pytest.mark.parametrize("cancelled", [False, True])
def test_later_export_failure_keeps_first_file_in_durable_partial_results(
    tmp_path, monkeypatch, cancelled
):
    from workspace_service.workflow_run_record import record_workflow_run

    gateway = local_exporter(monkeypatch, b"# First complete export")
    original_call = gateway.call_tool
    exports = 0

    async def call(session, request, name, args, **kwargs):
        nonlocal exports
        if name == "export":
            exports += 1
            if exports == 2:
                Path(args["output_path"]).write_bytes(b"incomplete provider bytes")
                if cancelled:
                    raise asyncio.CancelledError()
                raise WorkflowSourceExecutionError(
                    "EXPORT_FAILED",
                    "Provider failed",
                    "Inspect the application before retrying.",
                )
        return await original_call(session, request, name, args, **kwargs)

    gateway.call_tool = call
    workflow = plan()
    config = workflow.steps[0].application
    config = {
        **config,
        "exports": [
            *config["exports"],
            dict(port="second", format="markdown", name="reports/second.md"),
        ],
    }
    workflow = replace(
        workflow,
        steps=(replace(workflow.steps[0], application=config), *workflow.steps[1:]),
    )
    svc = service(tmp_path)

    async def execute(emit):
        return await execute_prompt_workflow(
            service=svc,
            workspace_dir=str(tmp_path),
            plan=workflow,
            input_values={},
            response_generator=None,
            action_generator=decide,
            tool_runtime=WorkflowMcpRuntime(
                gateway, workspace_id="workspace", session_id="session"
            ),
            on_event=emit,
        )

    with pytest.raises(
        asyncio.CancelledError if cancelled else WorkflowSourceExecutionError
    ):
        asyncio.run(
            record_workflow_run(
                service=svc,
                workspace_dir=str(tmp_path),
                source_path="workflows/export.workflow.wflow",
                source_digest="a" * 64,
                execute=execute,
            )
        )
    record = json.loads(next((tmp_path / "runs/export").glob("*.json")).read_text())
    assert record["status"] == ("cancelled" if cancelled else "failed")
    partial = list(record["partial_results"].values())
    assert len(partial) == 1 and len(partial[0]["exports"]) == 1
    assert (
        partial[0]["exports"][0]["representations"][0]["location"]
        == "reports/analysis.md"
    )
    assert (tmp_path / "reports/analysis.md").read_bytes() == b"# First complete export"
    assert not (tmp_path / "reports/second.md").exists()
    assert (
        next(tmp_path.glob(".wright-export-*/second.md")).read_bytes()
        == b"incomplete provider bytes"
    )
    assert any("Export incomplete" in e.get("message", "") for e in record["events"])
    assert exports == 2  # no resubmission of the interrupted export
