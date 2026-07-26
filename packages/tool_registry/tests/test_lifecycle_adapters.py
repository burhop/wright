import os
from types import SimpleNamespace

from tool_registry.lifecycle_adapters import (
    DatabaseLifecycleAdapter,
    SOLID_EDGE_ALLOWED_ROOTS_ENV,
    _workspace_scoped_environment,
)
from tool_registry.runners.stdio import StdioRunner


def test_solid_edge_runner_environment_includes_bound_workspace(tmp_path) -> None:
    configured = tmp_path / "configured"
    workspace = tmp_path / "workspace"
    server = SimpleNamespace(
        name="Solid Edge MCP",
        source_url="https://github.com/burhop/SolidEdgeMCP",
    )

    result = _workspace_scoped_environment(
        server,
        {SOLID_EDGE_ALLOWED_ROOTS_ENV: str(configured)},
        str(workspace),
    )

    roots = result[SOLID_EDGE_ALLOWED_ROOTS_ENV].split(os.pathsep)
    assert roots == [str(configured), os.path.abspath(workspace)]


def test_non_solid_edge_environment_is_unchanged(tmp_path) -> None:
    server = SimpleNamespace(name="Other MCP", source_url="https://example.test")
    original = {"EXISTING": "value"}

    assert _workspace_scoped_environment(server, original, str(tmp_path)) == original


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
