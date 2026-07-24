import os
from types import SimpleNamespace

from tool_registry.lifecycle_adapters import (
    SOLID_EDGE_ALLOWED_ROOTS_ENV,
    _workspace_scoped_environment,
)


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
