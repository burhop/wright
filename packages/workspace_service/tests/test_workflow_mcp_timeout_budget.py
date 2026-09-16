"""Canonical operations survive gateway defaults but retain its hard deadline."""

import asyncio
from dataclasses import replace
from types import SimpleNamespace

import pytest

from tool_registry.gateway_models import GatewayTool
from tool_registry.gateway_notifications import GatewayNotificationHub
from tool_registry.gateway_service import GatewayService
from workspace_service.workflow_mcp_execution import WorkflowMcpRuntime, schema_digest
from workspace_service.workflow_source_execution import (
    PromptStep,
    WorkflowSourceExecutionError,
)


class Workspaces:
    def resolve_binding(self, **kwargs):
        return {**kwargs, "workspace_path": "/tmp"}

    def enabled_server_ids(self, _session):
        return {"solver"}


TOOL = GatewayTool(
    name="solver__run",
    server_id="solver",
    tool_name="run",
    description="Run a solver",
    input_schema={"type": "object"},
    annotations={"readOnlyHint": True},
)


class Catalog:
    def servers(self):
        return (
            SimpleNamespace(
                server_id="solver",
                is_active=True,
                is_installed=True,
                status="active",
                risk_level="read-only",
            ),
        )

    def tools(self, _server_id):
        return (TOOL,)

    def resources(self, _session):
        return ()


class Lifecycle:
    async def ensure_started(self, *args, **kwargs):
        pass

    async def call_tool(self, *args, **kwargs):
        await asyncio.sleep(0.06)
        return {
            "content": [{"type": "text", "text": "Actual delayed operation finished"}]
        }


@pytest.mark.asyncio
@pytest.mark.parametrize("maximum, succeeds", [(1, True), (0.025, False)])
async def test_declared_budget_and_gateway_hard_limit(maximum, succeeds):
    gateway = GatewayService(
        workspaces=Workspaces(),
        catalog=Catalog(),
        lifecycle=Lifecycle(),
        audit=SimpleNamespace(record=lambda event: None),
        notifier=GatewayNotificationHub(),
        operation_timeout=0.01,
        maximum_timeout=maximum,
    )
    runtime = WorkflowMcpRuntime(
        gateway, workspace_id="workspace", session_id="binding"
    )
    step = PromptStep(
        "solve",
        "Solve",
        "Solve",
        None,
        (),
        "json",
        "result.json",
        True,
        "indexed",
        tool_name=TOOL.name,
        server_id=TOOL.server_id,
        schema_digest=schema_digest(TOOL),
    )
    step = replace(step, timeout_seconds=1)
    if succeeds:
        result = await runtime.call(step, {})
        assert "Actual delayed operation finished" in str(result)
    else:
        with pytest.raises(WorkflowSourceExecutionError, match="timeout"):
            await runtime.call(step, {})
