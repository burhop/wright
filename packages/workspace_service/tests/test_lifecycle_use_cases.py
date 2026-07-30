from __future__ import annotations

from types import SimpleNamespace

import pytest

from workspace_service.use_cases.context import WorkspaceContextUseCases
from workspace_service.use_cases.lifecycle import WorkspaceLifecycleUseCases
from workspace_service.use_cases.tools import WorkspaceToolUseCases

from .fakes import RecordingRepository


def test_lifecycle_context_and_tools_use_only_injected_repository():
    repository = RecordingRepository()
    repository.add("ws-a", "session-a", "/work/a")
    lifecycle = WorkspaceLifecycleUseCases(repository)
    context = WorkspaceContextUseCases(repository)
    tools = WorkspaceToolUseCases(
        repository,
        lambda: ["cad", "solver"],
        lambda session_id: repository.enabled_tools(
            repository.get_by_session(session_id)["workspace_id"]
        ),
        lambda: [],
    )

    assert lifecycle.get_by_session("session-a")["workspace_id"] == "ws-a"
    context.save("ws-a", {"units": "metric"})
    assert context.load("ws-a")["context_data"] == {"units": "metric"}
    assert tools.list_by_workspace("ws-a").enabled_tools == ["cad", "solver"]
    tools.set_by_session("session-a", "cad", False)
    assert repository.tools["ws-a"] == ["solver"]


@pytest.mark.asyncio
async def test_workspace_tool_status_reports_returned_start_error_before_gateway_mismatch():
    repository = RecordingRepository()
    repository.add("ws-a", "session-a", "/work/a")
    repository.set_enabled_tools("ws-a", ["cad-mcp"])
    server = SimpleNamespace(
        server_id="cad-mcp",
        name="CAD MCP",
        is_installed=True,
        status="inactive",
        error_message=None,
        approval_gates=[],
    )
    tools = WorkspaceToolUseCases(
        repository,
        lambda: ["CAD MCP"],
        lambda session_id: repository.enabled_tools(
            repository.get_by_session(session_id)["workspace_id"]
        ),
        lambda: [server],
    )

    class ReturningErrorEngine:
        _active_runners = {}

        async def start_server(self, *_args, **_kwargs):
            return SimpleNamespace(
                status="error",
                error_message="spawn failed",
                is_active=False,
            )

    result = await tools.status(
        repository.get_by_id("ws-a"),
        mcp_engine=ReturningErrorEngine(),
        config_paths=[],
    )

    assert result["status"] == "error"
    assert "CAD MCP: spawn failed" in result["message"]
