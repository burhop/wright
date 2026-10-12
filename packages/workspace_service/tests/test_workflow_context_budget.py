"""Accepted source freezes its complete-evidence budget; adapter support is explicit."""

import pytest
import asyncio
import json
from .test_workflow_ai_task import plan
from .test_workflow_ai_task import call, done
from .test_workflow_source_execution import source, task, service
from .test_workflow_mcp_execution import runtime
from tool_registry.gateway_models import GatewayToolResult
from workspace_service.workflow_source_execution import (
    compile_prompt_workflow,
    execute_prompt_workflow,
    WorkflowSourceExecutionError,
)
from workspace_service.workflow_mcp_execution import workflow_decision_kwargs


def test_budget_is_saved_and_old_defaults_are_preserved():
    assert plan().steps[0].mcp_context_budget_bytes is None
    step = plan(mcp_context_budget_bytes=400_000).steps[0]
    assert step.mcp_context_budget_bytes == 400_000

    async def adapter(*args, context_budget_bytes=None, **kwargs):
        pass

    assert (
        workflow_decision_kwargs(adapter, step, None)["context_budget_bytes"] == 400_000
    )


@pytest.mark.parametrize("value", [True, "400000", 0, 16383, 1048577, 400000.0])
def test_invalid_budget_is_not_silently_coerced(value):
    with pytest.raises(WorkflowSourceExecutionError, match="byte context budget"):
        plan(mcp_context_budget_bytes=value)


def test_non_mcp_task_cannot_select_budget():
    with pytest.raises(WorkflowSourceExecutionError, match="only for an MCP task"):
        compile_prompt_workflow(source(task("text", mcp_context_budget_bytes=400_000)))


def test_unsupported_adapter_fails_before_dispatch():
    async def legacy(messages, tools, required=False):
        pass

    with pytest.raises(WorkflowSourceExecutionError, match="does not support"):
        workflow_decision_kwargs(
            legacy, plan(mcp_context_budget_bytes=400_000).steps[0], None
        )


@pytest.mark.parametrize("budget", [None, 400_000])
def test_large_host_envelope_respects_saved_budget_and_old_guard(tmp_path, budget):
    workflow = plan(**({"mcp_context_budget_bytes": budget} if budget else {}))
    native = {
        "observations": [
            {"id": i, "value": "x" * 260, "disposition": "fail"} for i in range(520)
        ]
    }
    gateway, runner = runtime()
    gateway.result = GatewayToolResult(
        structured_content=native,
        content=({"type": "text", "text": json.dumps(native)},),
    )
    messages = []

    async def decide(conversation, tools, **kwargs):
        messages.append(conversation)
        if len(messages) == 1:
            return call()
        assert kwargs["context_budget_bytes"] == 400_000
        result = json.loads(conversation[-1]["content"])
        assert result["result"] == native
        return done("Retained all native failures")

    async def generate(*args, **kwargs):
        return "unused"

    execution = execute_prompt_workflow(
        service=service(tmp_path),
        workspace_dir=str(tmp_path),
        plan=workflow,
        input_values={},
        response_generator=generate,
        action_generator=decide,
        tool_runtime=runner,
    )
    if budget is None:
        with pytest.raises(WorkflowSourceExecutionError, match="tool result exceeds"):
            asyncio.run(execution)
        assert len(messages) == 1
    else:
        asyncio.run(execution)
        assert len(messages) == 2
