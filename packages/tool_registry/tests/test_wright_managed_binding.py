from __future__ import annotations

import os

import pytest

from tool_registry.wright_managed_servers import trusted_managed_launch_environment


def test_rivet_binding_uses_canonical_workspace_and_trusted_identities(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    database = tmp_path / "state.db"

    environment = trusted_managed_launch_environment(
        "rivet-workflows",
        workspace_path=str(workspace / ".." / "workspace"),
        database_path=str(database),
        binding={"workspace_id": "ws-1", "session_id": "session-1"},
    )

    assert environment == {
        "WRIGHT_RIVET_MCP_WORKSPACE": os.path.realpath(workspace),
        "WRIGHT_RIVET_MCP_DATABASE": os.path.realpath(database),
        "WRIGHT_RIVET_MCP_WORKSPACE_ID": "ws-1",
        "WRIGHT_RIVET_MCP_SESSION_ID": "session-1",
    }


@pytest.mark.parametrize(
    "binding",
    [
        {},
        {"workspace_id": "", "session_id": "session"},
        {"workspace_id": "workspace", "session_id": "bad\nvalue"},
    ],
)
def test_rivet_binding_rejects_missing_or_unsafe_authority(tmp_path, binding):
    with pytest.raises(ValueError):
        trusted_managed_launch_environment(
            "rivet-workflows",
            workspace_path=str(tmp_path),
            database_path=str(tmp_path / "state.db"),
            binding=binding,
        )


def test_non_managed_server_gets_no_trusted_environment(tmp_path):
    assert (
        trusted_managed_launch_environment(
            "user-server",
            workspace_path=str(tmp_path),
            database_path=str(tmp_path / "state.db"),
            binding={"workspace_id": "ws", "session_id": "session"},
        )
        == {}
    )
