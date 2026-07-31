import os
from types import SimpleNamespace

import pytest

from tool_registry.lifecycle_adapters import (
    DatabaseLifecycleAdapter,
    EngineMcpUiResourceReader,
)
from tool_registry.runners.stdio import StdioRunner


def test_two_server_identities_receive_the_same_generic_workspace_binding(
    tmp_path, monkeypatch
) -> None:
    workspace = tmp_path / "workspace"
    servers = {
        server_id: SimpleNamespace(
            server_id=server_id,
            name=name,
            source_url=source,
            type="stdio",
            command=["example-mcp", "--root", "{workspace.path}"],
            env_vars={"EXISTING": "value"},
            launch_env={"SERVER_ROOT": "{workspace.path}"},
            category="utilities",
        )
        for server_id, name, source in (
            ("alpha", "Alpha", "https://example.test/alpha"),
            ("beta", "Completely Different", "https://example.test/beta"),
        )
    }
    monkeypatch.setattr(
        "tool_registry.lifecycle_adapters.required_credentials", lambda server: []
    )
    monkeypatch.setattr(
        "tool_registry.lifecycle_adapters.McpSafetyPolicy.can_start",
        lambda *args, **kwargs: SimpleNamespace(allowed=True, reason="allowed"),
    )
    monkeypatch.setattr(
        "tool_registry.lifecycle_adapters.get_server",
        lambda db_path, server_id: servers[server_id],
    )
    adapter = DatabaseLifecycleAdapter(str(tmp_path / "state.db"))

    first = adapter.build_runner("alpha", str(workspace), None)
    second = adapter.build_runner("beta", str(workspace), None)

    expected = os.path.realpath(os.path.abspath(workspace))
    assert first.command == second.command == ["example-mcp", "--root", expected]
    assert first.env == second.env == {"EXISTING": "value", "SERVER_ROOT": expected}


def test_unbound_server_launch_configuration_is_unchanged(
    tmp_path, monkeypatch
) -> None:
    server = SimpleNamespace(
        server_id="unbound",
        name="Unbound",
        source_url="https://example.test/unbound",
        type="stdio",
        command=["example-mcp", "--mode", "normal"],
        env_vars={"EXISTING": "value"},
        launch_env={"MODE": "normal"},
        category="utilities",
    )
    monkeypatch.setattr(
        "tool_registry.lifecycle_adapters.required_credentials", lambda server: []
    )
    monkeypatch.setattr(
        "tool_registry.lifecycle_adapters.McpSafetyPolicy.can_start",
        lambda *args, **kwargs: SimpleNamespace(allowed=True, reason="allowed"),
    )
    monkeypatch.setattr(
        "tool_registry.lifecycle_adapters.get_server",
        lambda db_path, server_id: server,
    )

    runner = DatabaseLifecycleAdapter(str(tmp_path / "state.db")).build_runner(
        "unbound", None, None
    )

    assert runner.command == ["example-mcp", "--mode", "normal"]
    assert runner.env == {"EXISTING": "value", "MODE": "normal"}


def test_stdio_runner_inherits_adapter_operation_timeout(tmp_path, monkeypatch) -> None:
    adapter = DatabaseLifecycleAdapter(
        str(tmp_path / "state.db"),
        operation_timeout=47.5,
    )
    server = SimpleNamespace(
        server_id="stdio-server",
        name="Example MCP",
        source_url="https://example.test",
        type="stdio",
        command=["example-mcp"],
        env_vars={},
        launch_env={},
        category=None,
    )
    monkeypatch.setattr(
        "tool_registry.lifecycle_adapters.required_credentials",
        lambda server: [],
    )
    monkeypatch.setattr(
        "tool_registry.lifecycle_adapters.McpSafetyPolicy.can_start",
        lambda *args, **kwargs: SimpleNamespace(allowed=True, reason="allowed"),
    )
    monkeypatch.setattr(
        "tool_registry.lifecycle_adapters.get_server",
        lambda db_path, server_id: server,
    )

    runner = adapter.build_runner("stdio-server", None, None)

    assert isinstance(runner, StdioRunner)
    assert runner.operation_timeout == 47.5


@pytest.mark.asyncio
async def test_child_resource_notifications_invalidate_exact_connection_and_uri() -> None:
    handlers = []

    class Runner:
        def add_notification_handler(self, handler) -> None:
            handlers.append(handler)

    class Engine:
        def __init__(self) -> None:
            self.lifecycle = SimpleNamespace(runner_for=lambda server_id: Runner())

        def child_connection_id(self, server_id: str) -> str:
            return f"{server_id}:7"

        async def list_child_resources(self, server_id: str):
            return {"resources": []}

        async def read_child_resource(self, server_id: str, uri: str):
            return {"contents": []}

        async def subscribe_child_resource(self, server_id: str, uri: str) -> None:
            return None

    invalidations = []
    reader = EngineMcpUiResourceReader(
        Engine(),
        invalidate=lambda **values: invalidations.append(values) or 1,
    )
    await reader.list_resources("server")
    assert len(handlers) == 1

    await handlers[0](
        "notifications/resources/updated",
        {"uri": "ui://server/app"},
    )
    await handlers[0]("notifications/resources/list_changed", {})

    assert invalidations == [
        {
            "server_connection_id": "server:7",
            "uri": "ui://server/app",
        },
        {"server_connection_id": "server:7", "uri": None},
    ]
