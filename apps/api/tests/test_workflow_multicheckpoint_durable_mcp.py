"""Normal approval API resumes with a real, isolated stdio MCP output operation.

Only the initial model response is deterministic. File creation runs in a child
MCP server through StdioRunner and GatewayService, with no campaign host access.
"""

import asyncio
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from fastapi import HTTPException

from api.routers import workspace as router
from api.schemas.workspace import (
    WorkflowApprovalDecisionRequest,
    WorkflowApprovalResumeRequest,
    WorkflowSourceRunRequest,
)
from tool_registry import McpServer
from tool_registry.gateway_notifications import GatewayNotificationHub
from tool_registry.gateway_service import GatewayService
from tool_registry.runners.stdio import StdioRunner
from workspace_service.executor import BoundedExecutor
from workspace_service.workflow_integration_policy import (
    LOCAL_REVIEW_BINDING,
    LOCAL_REVIEW_DESTINATION,
    WorkflowIntegrationPolicyService,
)
from workspace_service.workflow_mcp_execution import schema_digest
from workspace_service.workflow_sources import WorkspaceWorkflowSourceUseCases
from packages.workspace_service.tests.test_workflow_artifact_review import port, section
from packages.workspace_service.tests.test_workflow_execution_continuation import order
from packages.workspace_service.tests.test_workflow_external_action_execution import (
    service,
)


ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location(
    "stdio_qualification", ROOT / "scripts/qualify_stdio_mcp.py"
)
qualification = importlib.util.module_from_spec(spec)
spec.loader.exec_module(qualification)

SERVER = '''import json
from pathlib import Path
import sys
from mcp.server.fastmcp import FastMCP

root = Path(sys.argv[1]).resolve()
mcp = FastMCP("isolated-continuation-test")

@mcp.tool()
def write_result() -> dict:
    """Write the fixed isolated integration-test result exactly once per call."""
    target = root / "outputs/attempt/native-result.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    with (root / "tool-dispatches.jsonl").open("a", encoding="utf-8") as log:
        log.write(json.dumps({"operation": "write_result"}) + "\\n")
    result = {"test_operation": True, "squared_samples": [n*n for n in range(5)]}
    target.write_text(json.dumps(result), encoding="utf-8")
    return {"path": "outputs/attempt/native-result.json", "bytes": target.stat().st_size}

if __name__ == "__main__":
    mcp.run(transport="stdio")
'''


def fresh_service(root):
    """Reopen SQLite and source/file adapters; retain no prior service state."""
    svc = service(root)
    svc.workflow_sources = WorkspaceWorkflowSourceUseCases(BoundedExecutor())
    svc.workflow_integration_policies = WorkflowIntegrationPolicyService(
        str(root / "state.db"), enabled=True
    )
    svc.lifecycle = SimpleNamespace(
        get_by_session=lambda _: {"workspace_id": "ws", "local_path": str(root)}
    )
    svc.ensure_workspace_path_safe = lambda path: path
    return svc


def graph(tool):
    text = section(
        "workflow",
        "two_reviews",
        name="Two durable reviews",
        purpose="Test real continuation",
        discipline="engineering",
        reviewed_ai_suggestions=False,
    )
    common = dict(
        purpose="Isolated integration test",
        group=None,
        tool=None,
        reusable_step=None,
        inputs=[],
    )
    text += section(
        "task",
        "package",
        name="Package",
        step_type="work",
        performed_by="ai_assisted",
        outputs=[port("package_response")],
        prompt="Return the fixed test package.",
        settings={
            "output_format": "json",
            "save_output": True,
            "output_filename": "outputs/attempt/package.json",
        },
        **common,
    )
    for key in ("approve_first", "approve_second"):
        text += section(
            "task",
            key,
            name=key,
            step_type="review",
            performed_by="engineer",
            outputs=[],
            instructions="Review the recorded test package.",
            settings={
                "authoring_template": "external-action-approval",
                "action_kind": "local_review",
                "approval_binding": LOCAL_REVIEW_BINDING,
                "approval_destination": LOCAL_REVIEW_DESTINATION,
                "approval_settings": {"review_task_id": key},
                "approval_action": {"kind": "local_review", "mode": "review_only"},
            },
            **common,
        )
    text += section(
        "task",
        "final_tool",
        name="Actual output operation",
        step_type="work",
        instructions="Call the fixed test output operation.",
        performed_by="configured_tool",
        outputs=[{**port("final_response"), "kind": "structured_result"}],
        settings={
            "authoring_template": "mcp-tool",
            "mcp_tool": tool.name,
            "mcp_server": tool.server_id,
            "mcp_schema_digest": schema_digest(tool),
            "mcp_arguments": "{}",
            "output_format": "json",
            "save_output": True,
            "output_filename": "outputs/attempt/tool-response.json",
            "expected_files": "outputs/attempt/native-result.json",
        },
        **common,
    )
    for index, (before, after) in enumerate(
        zip(
            ("package", "approve_first", "approve_second"),
            ("approve_first", "approve_second", "final_tool"),
        )
    ):
        text += order(f"next_{index}", before, after)
    return text


@pytest_asyncio.fixture
async def case(tmp_path, monkeypatch):
    script = tmp_path / "test_mcp_server.py"
    script.write_text(SERVER, encoding="utf-8")
    command = [sys.executable, "-B", str(script), str(tmp_path)]
    runner = StdioRunner(command, cwd=str(tmp_path), operation_timeout=15)
    await runner.start()
    try:
        server = McpServer(
            server_id="isolated-output",
            name="Test output",
            type="stdio",
            command=command,
            is_active=True,
            is_installed=True,
            status="active",
            created_at=1,
            updated_at=1,
            risk_level="low",
            default_enabled=False,
        )
        catalog = qualification._Catalog(server, await runner.list_tools())
        gateway = GatewayService(
            workspaces=qualification._Workspaces(tmp_path, server.server_id),
            catalog=catalog,
            lifecycle=qualification._Lifecycle(runner),
            audit=qualification._Audit(),
            notifier=GatewayNotificationHub(),
            operation_timeout=15,
        )
        svc = fresh_service(tmp_path)
        tool = catalog.tools(server.server_id)[0]
        path = "workflows/two-reviews.workflow.wflow"
        document = await svc.workflow_sources.create(str(tmp_path), path, graph(tool))
        (tmp_path / "brief.md").write_bytes(
            b"Fictional test package; no external destination."
        )
        grant = svc.workflow_integration_policies.enroll(
            campaign_id="durable-mcp-test",
            dataset_id="case-01",
            dataset_digest="d" * 64,
            workspace_id="ws",
            source_path=path,
            source_digest=document.storage_digest,
            input_files={
                "brief.md": hashlib.sha256(
                    (tmp_path / "brief.md").read_bytes()
                ).hexdigest()
            },
            output_root="outputs/attempt",
            approval_mode="auto",
            allowed_tools=[
                {
                    "server_id": tool.server_id,
                    "name": tool.name,
                    "schema_digest": schema_digest(tool),
                }
            ],
        )
        generate = AsyncMock(return_value='{"package":"isolated test ready"}')
        monkeypatch.setattr(router, "generate_workflow_response", generate)
        request = SimpleNamespace(
            headers={},
            app=SimpleNamespace(state=SimpleNamespace(gateway_service=gateway)),
        )
        body = WorkflowSourceRunRequest(
            session_id="session",
            path=path,
            expected_storage_digest=document.storage_digest,
            integration_policy_digest=grant,
        )
        started = await router.run_workflow_source_endpoint(body, request, svc)
        yield SimpleNamespace(
            root=tmp_path,
            gateway=gateway,
            request=request,
            started=started,
            generate=generate,
        )
    finally:
        await runner.stop()


def checkpoint(case, result=None):
    result = result or case.started.model_dump(mode="json")
    return fresh_service(case.root).workflow_external_actions.lookup(
        result["approval"]["checkpoint_id"]
    )


async def decide(case, current):
    return await router.decide_workflow_approval_checkpoint_endpoint(
        current.run_id,
        current.checkpoint_id,
        WorkflowApprovalDecisionRequest(
            session_id="session",
            subject_digest=current.subject_digest,
            decision="approved",
            auto=True,
            request_id=f"decide-{current.step_id}",
        ),
        case.request,
        fresh_service(case.root),
    )


async def resume(case, current):
    return await router.resume_workflow_approval_checkpoint_endpoint(
        current.run_id,
        WorkflowApprovalResumeRequest(
            session_id="session",
            checkpoint_id=current.checkpoint_id,
            subject_digest=current.subject_digest,
            request_id=f"resume-{current.step_id}",
        ),
        case.request,
        fresh_service(case.root),
    )


def dispatch_count(case):
    path = case.root / "tool-dispatches.jsonl"
    return len(path.read_text().splitlines()) if path.exists() else 0


def record(case):
    return json.loads((case.root / case.started.run_log_path).read_text())


async def second_approved(case):
    first = checkpoint(case)
    await decide(case, first)
    continued = await resume(case, first)
    second = checkpoint(case, continued.execution_result)
    await decide(case, second)
    assert dispatch_count(case) == 0
    return first, second


@pytest.mark.asyncio
async def test_two_checkpoint_api_restarts_and_duplicate_resumes_execute_real_mcp_once(
    case,
):
    first = checkpoint(case)
    assert case.started.status == "awaiting_approval"
    assert dispatch_count(case) == 0
    approved = await decide(case, first)
    assert approved.actor == "integration_test:durable-mcp-test"
    assert (await decide(case, first)).model_dump(mode="json") == approved.model_dump(
        mode="json"
    )
    middle = await resume(case, first)
    assert middle.execution_result["status"] == "awaiting_approval"
    assert dispatch_count(case) == 0
    second = checkpoint(case, middle.execution_result)
    assert second.step_id == "approve_second"
    await decide(case, second)
    final = await resume(case, second)
    assert final.execution_result["status"] == "completed"
    assert [step["task_id"] for step in final.execution_result["steps"]] == [
        "package",
        "approve_first",
        "approve_second",
        "final_tool",
    ]
    output = case.root / "outputs/attempt/native-result.json"
    assert json.loads(output.read_text())["squared_samples"] == [0, 1, 4, 9, 16]
    outputs = final.execution_result["outputs"]
    assert any(
        item["output_path"] == "outputs/attempt/native-result.json"
        and item["sha256"] == hashlib.sha256(output.read_bytes()).hexdigest()
        for item in outputs
    )
    assert (await resume(case, second)).model_dump(mode="json") == final.model_dump(
        mode="json"
    )
    assert (await resume(case, first)).model_dump(mode="json") == middle.model_dump(
        mode="json"
    )
    assert dispatch_count(case) == 1
    case.generate.assert_awaited_once()
    durable = record(case)
    assert durable["status"] == "completed"
    kinds = [event["kind"] for event in durable["events"]]
    assert kinds.count("run_started") == 1 and kinds.count("run_resumed") == 2
    assert kinds.count("approval_decided") == 2


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "boundary", ["before_dispatch", "after_dispatch", "lost_response"]
)
async def test_interrupted_final_mcp_is_durable_unknown_and_cannot_replay(
    case, monkeypatch, boundary
):
    _, second = await second_approved(case)
    actual_call = case.gateway.call_tool
    reached = asyncio.Event()

    async def interrupted(*args, **kwargs):
        if boundary != "before_dispatch":
            await actual_call(*args, **kwargs)
        reached.set()
        if boundary == "lost_response":
            raise OSError("Test transport lost response after actual child output")
        await asyncio.Event().wait()

    monkeypatch.setattr(case.gateway, "call_tool", interrupted)
    pending = asyncio.create_task(resume(case, second))
    await asyncio.wait_for(reached.wait(), timeout=20)
    if boundary != "lost_response":
        pending.cancel()
        with pytest.raises(asyncio.CancelledError):
            await pending
    else:
        # The ordinary execution pipeline may return a failed result or map it
        # to an API error; either must durably prevent another tool invocation.
        try:
            result = await pending
            assert result.execution_result["status"] == "failed"
        except (HTTPException, OSError):
            pass
    expected_calls = 0 if boundary == "before_dispatch" else 1
    assert dispatch_count(case) == expected_calls
    monkeypatch.setattr(case.gateway, "call_tool", actual_call)
    with pytest.raises(HTTPException) as blocked:
        await resume(case, second)
    assert blocked.value.detail["code"] == "workflow_continuation_outcome_unknown"
    assert dispatch_count(case) == expected_calls
    assert record(case)["status"] in {"failed", "cancelled"}


@pytest.mark.asyncio
async def test_cancellation_after_durable_outcome_returns_cached_completion(
    case, monkeypatch
):
    from workspace_service import workflow_approval_execution as approval_execution

    _, second = await second_approved(case)
    original = approval_execution.record_workflow_resume

    async def lose_completed_response(**kwargs):
        result = await original(**kwargs)
        assert result["status"] == "completed"
        raise asyncio.CancelledError(
            "Test caller disconnected after durable completion"
        )

    monkeypatch.setattr(
        approval_execution, "record_workflow_resume", lose_completed_response
    )
    with pytest.raises(asyncio.CancelledError):
        await resume(case, second)
    assert dispatch_count(case) == 1
    assert record(case)["status"] == "completed"
    monkeypatch.setattr(approval_execution, "record_workflow_resume", original)
    recovered = await resume(case, second)
    assert recovered.execution_result["status"] == "completed"
    assert dispatch_count(case) == 1
