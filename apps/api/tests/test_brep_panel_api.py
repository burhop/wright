from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest
from fastapi import Response

from api.routers import workspace as workspace_router
from api.schemas.workspace import BrepPanelRequest, BrepToolRequest


class _WorkspaceService:
    lifecycle = SimpleNamespace(
        get_by_session=lambda _session_id: {"workspace_id": "workspace-1"}
    )

    async def resolve_workspace_dir(self, session_id, _engine):
        assert session_id == "session-1"
        return "D:\\workspaces\\demo"


class _McpEngine:
    def __init__(self, server):
        self.server = server
        self.lifecycle = SimpleNamespace(runner_for=lambda _server_id: None)
        self.started = []
        self.called = []

    async def start_server(self, server_id, workspace_dir, *, approval_context):
        self.started.append((server_id, workspace_dir, approval_context))
        return self.server

    async def call_tool(self, server_id, tool_name, arguments, *, approval_context):
        self.called.append((server_id, tool_name, arguments, approval_context))
        return {
            "content": [
                {
                    "type": "text",
                    "text": """{
                      "connected": false,
                      "controlUrl": "http://127.0.0.1:61234/?token=abcdefghijklmnopqrstuvwxyz012345",
                      "moduleUrl": "http://127.0.0.1:5190/src/CAD.ts"
                    }""",
                }
            ]
        }


class _ConcurrentMcpEngine(_McpEngine):
    def __init__(self, server):
        super().__init__(server)
        self.runner = None
        self.lifecycle = SimpleNamespace(runner_for=lambda _server_id: self.runner)

    async def start_server(self, server_id, workspace_dir, *, approval_context):
        self.started.append((server_id, workspace_dir, approval_context))
        await asyncio.sleep(0.05)
        self.runner = SimpleNamespace(is_running=lambda: True)
        return self.server


@pytest.mark.asyncio
async def test_brep_panel_starts_workspace_bound_mcp_and_returns_control_page(
    monkeypatch,
):
    server = SimpleNamespace(
        server_id="brep-server",
        name="BREP MCP",
        source_url="https://github.com/mmiscool/BREP-MCP",
        is_installed=True,
        env_vars={"BREP_CAD_MODULE_URL": "http://127.0.0.1:5173/src/CAD.ts"},
        approval_gates=[],
        status="active",
        error_message=None,
    )
    mcp_engine = _McpEngine(server)
    monkeypatch.setattr(workspace_router, "get_servers", lambda _path: [server])

    def update(_path, _server_id, changes):
        server.env_vars = changes["env_vars"]
        return server

    monkeypatch.setattr(workspace_router, "update_server", update)
    monkeypatch.setattr(
        workspace_router, "wait_for_brep_module", lambda _module_url: None
    )
    response = Response()

    result = await workspace_router.brep_panel_endpoint(
        BrepPanelRequest(session_id="session-1"),
        SimpleNamespace(
            app=SimpleNamespace(state=SimpleNamespace(mcp_engine=mcp_engine))
        ),
        response,
        SimpleNamespace(),
        _WorkspaceService(),
    )

    assert result.control_url.startswith("http://127.0.0.1:61234/")
    assert result.module_url == "http://127.0.0.1:5190/src/CAD.ts"
    assert server.env_vars["BREP_MCP_AUTO_OPEN"] == "0"
    assert len(mcp_engine.started) == 1
    assert mcp_engine.called[0][1] == "brep.app.status"
    assert response.headers["cache-control"] == "no-store"


@pytest.mark.asyncio
async def test_brep_panel_coalesces_concurrent_workspace_restore_requests(
    monkeypatch,
):
    server = SimpleNamespace(
        server_id="brep-server",
        name="BREP MCP",
        source_url="https://github.com/mmiscool/BREP-MCP",
        is_installed=True,
        env_vars={"BREP_CAD_MODULE_URL": "http://127.0.0.1:5190/src/CAD.ts"},
        approval_gates=[],
        status="active",
        error_message=None,
    )
    mcp_engine = _ConcurrentMcpEngine(server)
    monkeypatch.setattr(workspace_router, "get_servers", lambda _path: [server])

    def update(_path, _server_id, changes):
        server.env_vars = changes["env_vars"]
        return server

    monkeypatch.setattr(workspace_router, "update_server", update)
    monkeypatch.setattr(
        workspace_router, "wait_for_brep_module", lambda _module_url: None
    )

    async def open_panel():
        return await workspace_router.brep_panel_endpoint(
            BrepPanelRequest(session_id="session-1"),
            SimpleNamespace(
                app=SimpleNamespace(state=SimpleNamespace(mcp_engine=mcp_engine))
            ),
            Response(),
            SimpleNamespace(),
            _WorkspaceService(),
        )

    first, second = await asyncio.gather(open_panel(), open_panel())

    assert first.module_url == second.module_url
    assert len(mcp_engine.started) == 1


@pytest.mark.asyncio
async def test_brep_tool_uses_the_panel_owned_mcp_process(monkeypatch):
    server = SimpleNamespace(
        server_id="brep-server",
        name="BREP MCP",
        source_url="https://github.com/mmiscool/BREP-MCP",
        is_installed=True,
        env_vars={
            "BREP_CAD_MODULE_URL": "http://127.0.0.1:5190/src/CAD.ts",
            "BREP_MCP_APP_PORT": "0",
            "BREP_MCP_AUTO_OPEN": "0",
        },
        approval_gates=[],
        status="active",
        error_message=None,
    )
    mcp_engine = _McpEngine(server)
    monkeypatch.setattr(workspace_router, "get_servers", lambda _path: [server])

    result = await workspace_router.brep_tool_endpoint(
        BrepToolRequest(
            session_id="session-1",
            tool_name="brep.app.status",
            arguments={},
        ),
        SimpleNamespace(
            app=SimpleNamespace(state=SimpleNamespace(mcp_engine=mcp_engine))
        ),
        SimpleNamespace(),
        _WorkspaceService(),
    )

    assert result["content"]
    assert len(mcp_engine.started) == 1
    assert mcp_engine.called[0][0:3] == (
        "brep-server",
        "brep.app.status",
        {},
    )
