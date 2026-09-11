from __future__ import annotations

import time

import pytest

from data_vault import upgrade_database

from tool_registry.db import insert_server, insert_tools, update_server
from tool_registry.gateway_adapters import (
    DatabaseGatewayCatalog,
    EngineGatewayLifecycle,
)
from tool_registry.models import McpServer, McpTool
from tool_registry.gateway_models import GatewayError, GatewayErrorCode, GatewayWorkspaceScopeError
from tool_registry.runners.stdio import StdioRunner


def _server(server_id: str, *, risk_level: str) -> McpServer:
    now = int(time.time())
    return McpServer(
        server_id=server_id,
        name=server_id,
        type="stdio",
        command=["server"],
        is_active=True,
        is_installed=True,
        status="active",
        risk_level=risk_level,
        approval_gates=["wright-mcp-appliance-bundle"],
        created_at=now,
        updated_at=now,
    )


def _tool(server_id: str) -> McpTool:
    return McpTool(
        tool_id=f"{server_id}:ping",
        server_id=server_id,
        name="ping",
        description="Ping",
        input_schema={"type": "object"},
        is_enabled=True,
        created_at=int(time.time()),
    )


def test_database_gateway_catalog_projects_only_policy_required_approvals(
    tmp_path,
) -> None:
    db_path = str(tmp_path / "gateway-adapter.db")
    upgrade_database(db_path)
    insert_server(db_path, _server("bundled-low-risk", risk_level="low"))
    insert_tools(db_path, [_tool("bundled-low-risk")])
    insert_server(db_path, _server("machine-high-risk", risk_level="high"))
    insert_tools(db_path, [_tool("machine-high-risk")])

    catalog = DatabaseGatewayCatalog(db_path)

    low_risk_tool = catalog.tools("bundled-low-risk")[0]
    high_risk_tool = catalog.tools("machine-high-risk")[0]

    assert low_risk_tool.required_approvals == frozenset()
    assert high_risk_tool.required_approvals == frozenset(
        {"wright-mcp-appliance-bundle"}
    )


def test_database_gateway_server_revision_ignores_health_but_tracks_authority(
    tmp_path,
) -> None:
    db_path = str(tmp_path / "gateway-revision.db")
    upgrade_database(db_path)
    server = _server("remote-server", risk_level="low")
    insert_server(db_path, server)
    insert_tools(db_path, [_tool("remote-server")])
    catalog = DatabaseGatewayCatalog(db_path)

    initial = catalog.tools("remote-server")[0].provenance["server_revision"]
    update_server(
        db_path,
        "remote-server",
        {
            "is_active": False,
            "status": "inactive",
            "updated_at": server.updated_at + 1,
        },
    )
    after_health_change = catalog.tools("remote-server")[0].provenance[
        "server_revision"
    ]
    update_server(
        db_path,
        "remote-server",
        {"command": ["replacement-server"], "updated_at": server.updated_at + 2},
    )
    after_authority_change = catalog.tools("remote-server")[0].provenance[
        "server_revision"
    ]

    assert after_health_change == initial
    assert after_authority_change != initial


class _Lifecycle:
    def __init__(self) -> None:
        self.runner = None

    def runner_for(self, server_id: str):
        return self.runner


class _Engine:
    def __init__(self, *, starts_successfully: bool = True) -> None:
        self.lifecycle = _Lifecycle()
        self.starts: list[tuple[str, str, object]] = []
        self.starts_successfully = starts_successfully

    async def start_server(
        self,
        server_id: str,
        workspace_path: str,
        *,
        approval_context,
    ) -> None:
        self.starts.append((server_id, workspace_path, approval_context))
        if self.starts_successfully:
            self.lifecycle.runner = object()


@pytest.mark.asyncio
async def test_engine_gateway_notifies_after_lazy_tool_discovery() -> None:
    engine = _Engine()
    changed: list[str] = []
    lifecycle = EngineGatewayLifecycle(
        engine,  # type: ignore[arg-type]
        tools_changed=changed.append,
    )

    await lifecycle.ensure_started(
        "remote-server",
        workspace_path="D:\\workspace",
        approval_context={"workspace_approvals": ["network_access_approval"]},
    )
    await lifecycle.ensure_started(
        "remote-server",
        workspace_path="D:\\workspace",
        approval_context={"workspace_approvals": ["network_access_approval"]},
    )

    assert len(engine.starts) == 1
    assert changed == ["remote-server"]


@pytest.mark.asyncio
async def test_engine_gateway_does_not_notify_after_failed_discovery() -> None:
    engine = _Engine(starts_successfully=False)
    changed: list[str] = []
    lifecycle = EngineGatewayLifecycle(
        engine,  # type: ignore[arg-type]
        tools_changed=changed.append,
    )

    await lifecycle.ensure_started(
        "remote-server",
        workspace_path="D:\\workspace",
        approval_context={},
    )

    assert changed == []


@pytest.mark.asyncio
@pytest.mark.parametrize('runner_scope', ['other-workspace', None])
async def test_browser_gateway_rejects_cached_runner_with_wrong_workspace(
    tmp_path, runner_scope
) -> None:
    db_path = str(tmp_path / 'browser-scope.db')
    upgrade_database(db_path)
    server = _server('browser', risk_level='low')
    server.source_url = 'https://github.com/microsoft/playwright-mcp'
    insert_server(db_path, server)
    engine = _Engine()
    engine.db_path = db_path
    runner = StdioRunner(['node', 'browser-cli.js'], cwd=(
        str(tmp_path / runner_scope) if runner_scope else None
    ))
    engine.lifecycle.runner = runner

    with pytest.raises(GatewayError, match='different or unspecified workspace') as error:
        await EngineGatewayLifecycle(engine).ensure_started(
            'browser', workspace_path=str(tmp_path / 'requested-workspace'),
            approval_context={},
        )

    assert error.value.code is GatewayErrorCode.INVALID_BINDING
    assert isinstance(error.value, GatewayWorkspaceScopeError)
    assert 'Disable' in str(error.value)
    assert str(tmp_path) not in str(error.value)
    assert engine.lifecycle.runner is runner
    assert engine.starts == []


@pytest.mark.asyncio
@pytest.mark.parametrize('source_url', [
    'https://github.com/microsoft/playwright-mcp',
    'https://example.test/other-server',
])
async def test_browser_gateway_reuses_matching_scope_and_leaves_other_servers_alone(
    tmp_path, source_url
) -> None:
    db_path = str(tmp_path / 'browser-matching-scope.db')
    upgrade_database(db_path)
    server = _server('browser', risk_level='low')
    server.source_url = source_url
    insert_server(db_path, server)
    engine = _Engine()
    engine.db_path = db_path
    workspace = tmp_path / 'workspace'
    # Relative components normalize to the same root; unrelated servers retain
    # their existing application/session lifecycle even with another cwd.
    cwd = str(workspace / 'nested' / '..') if 'microsoft' in source_url else None
    runner = StdioRunner(['node', 'browser-cli.js'], cwd=cwd)
    engine.lifecycle.runner = runner

    await EngineGatewayLifecycle(engine).ensure_started(
        'browser', workspace_path=str(workspace), approval_context={},
    )

    assert engine.lifecycle.runner is runner
    assert engine.starts == []


@pytest.mark.asyncio
async def test_browser_gateway_checks_runner_reused_by_concurrent_activation(tmp_path):
    db_path = str(tmp_path / 'browser-activation-race.db')
    upgrade_database(db_path)
    server = _server('browser', risk_level='low')
    server.source_url = 'https://github.com/microsoft/playwright-mcp'
    insert_server(db_path, server)
    runner = StdioRunner(['node', 'browser-cli.js'], cwd=str(tmp_path / 'other'))

    class ConcurrentEngine(_Engine):
        async def start_server(self, server_id, workspace_path, *, approval_context):
            self.lifecycle.runner = runner

    engine = ConcurrentEngine()
    engine.db_path = db_path
    changed = []
    lifecycle = EngineGatewayLifecycle(engine, tools_changed=changed.append)
    with pytest.raises(GatewayError, match='different or unspecified workspace'):
        await lifecycle.ensure_started(
            'browser', workspace_path=str(tmp_path / 'requested'), approval_context={},
        )
    assert changed == []
    assert engine.lifecycle.runner is runner
