from agent_adapters import AgentContextMaterializationRequest
from agent_adapters.openclaw import (
    openclaw_context_materializer,
    openclaw_wright_gateway_profile,
)


def test_openclaw_stub_uses_wright_gateway_protocol_without_hermes_paths():
    profile = openclaw_wright_gateway_profile("/workspace")

    assert profile.provider_name == "openclaw"
    assert profile.display_name == "Wright gateway"
    assert profile.command == "uv"
    assert profile.args == [
        "run",
        "--project",
        "/workspace",
        "python",
        "-m",
        "tool_registry.gateway",
    ]
    assert profile.workspace_context_filename is None
    assert "hermes" not in " ".join([profile.server_name, *profile.args]).lower()


def test_openclaw_context_materializer_writes_no_hermes_files(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    result = openclaw_context_materializer().materialize(
        AgentContextMaterializationRequest(
            db_path=str(tmp_path / "state.db"),
            workspace_path=str(workspace),
        )
    )

    assert result.provider_id == "openclaw"
    assert result.files_written == ()
    assert not (workspace / ".hermes.md").exists()
