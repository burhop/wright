from agent_adapters.openclaw import openclaw_wright_gateway_profile


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

