"""Real document publisher with synthetic observation input; no engineering run."""

import asyncio
import json
from dataclasses import replace
from pathlib import Path

import pytest
from tool_registry.gateway_models import GatewayToolResult
from workspace_service.workflow_mcp_execution import WorkflowMcpRuntime, schema_digest
from workspace_service.workflow_run_paths import bind_run_paths
from workspace_service.workflow_source_execution import (
    compile_prompt_workflow,
    execute_prompt_workflow,
    WorkflowSourceExecutionError,
)
from workspace_service.workspace_document_gateway import (
    WorkspaceDocumentGatewayProvider,
)
from .test_workspace_document_gateway import _fixture
from .test_workflow_mcp_execution import Gateway, TOOL, edge
from .test_workflow_source_execution import service, source, task
from .test_workflow_ai_task import call, done

REPO = Path(__file__).resolve().parents[3]


@pytest.mark.parametrize("allowed", [True, False])
def test_recorded_observations_reach_exact_publisher_without_model_rewrite(
    tmp_path, allowed
):
    _, root, artifacts, scope = _fixture(tmp_path)
    provider = WorkspaceDocumentGatewayProvider(artifacts)
    document_tool = provider.tools(scope)[0]
    handle = (
        REPO
        / "prototypes/desktop-harness/engineering-experience/handle/replacement-handle-draft.workflow.wflow"
    ).read_text()
    retained = (
        "task retain_slice_observations\n"
        + handle.split("task retain_slice_observations\n", 1)[1].split("\nend", 1)[0]
        + "\nend\n"
    )
    workflow = compile_prompt_workflow(
        source(
            task(
                "observe",
                fmt="json",
                authoring_template="mcp-task",
                mcp_server="docs",
                mcp_response_source="tool_observations",
            ),
            retained,
        )
        + edge(
            "observe.observe_response",
            "retain_slice_observations.retention_observations",
        )
    )
    assert workflow.steps[1].schema_digest == schema_digest(document_tool)
    run_id = "a" * 32
    workflow = bind_run_paths(workflow, run_id)
    gateway = Gateway()
    gateway.list_tools = lambda *_: (
        replace(TOOL, annotations={"readOnlyHint": True}),
        document_tool,
    )
    gateway.workspace_approvals_for_model_call = lambda *_: {
        "workspace_enabled",
        *(["workspace_write_approval"] if allowed else []),
    }
    captured = []

    async def dispatch(session_id, request_id, name, arguments, **kwargs):
        if name == TOOL.name:
            return GatewayToolResult(
                content=(), structured_content={"ok": True, "measured": "fixture only"}
            )
        assert name == document_tool.name
        captured.append(dict(arguments))
        result = await provider.call(
            scope,
            document_tool,
            arguments,
            request_id=request_id,
            approval_context={"workspace_approvals": kwargs["workspace_approvals"]},
            progress_callback=None,
        )
        return GatewayToolResult.from_upstream(result)

    gateway.call_tool = dispatch
    runner = WorkflowMcpRuntime(
        gateway, workspace_id=scope.workspace_id, session_id="fixture"
    )
    replies = iter([call(), done('{"invented":"must never replace observations"}')])

    async def decide(*args, **kwargs):
        return next(replies)

    async def execute():
        return await execute_prompt_workflow(
            service=service(root),
            workspace_dir=str(root),
            plan=workflow,
            input_values={},
            response_generator=None,
            action_generator=decide,
            tool_runtime=runner,
            run_id=run_id,
        )

    destination = root / f"results/{run_id}/slice-observations/recorded-responses.json"
    if not allowed:
        with pytest.raises(WorkflowSourceExecutionError):
            asyncio.run(execute())
        assert not destination.exists()
        return
    result = asyncio.run(execute())
    assert len(captured) == 1
    assert (
        destination.read_text()
        == captured[0]["content"]
        == result["steps"][0]["response"]
    )
    observed = json.loads(destination.read_text())
    assert observed["observations"]["value"][0]["result"]["measured"] == "fixture only"
    assert "invented" not in destination.read_text()
    output = next(
        o
        for o in result["outputs"]
        if o["output_path"].endswith("recorded-responses.json")
    )
    assert output["output_port"] == "retained_observations"
