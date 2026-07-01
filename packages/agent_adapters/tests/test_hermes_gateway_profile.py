from agent_adapters.hermes_gateway import hermes_config_paths, hermes_wright_gateway_profile


def test_hermes_gateway_profile_preserves_wrightgateway_key():
    profile = hermes_wright_gateway_profile("/workspace")

    assert profile.provider_name == "hermes"
    assert profile.server_name == "wrightgateway"
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
    assert profile.terminal_config() == {"cwd": "/workspace"}
    assert profile.workspace_context_filename == ".hermes.md"


def test_hermes_config_paths_are_hermes_specific():
    paths = hermes_config_paths()

    assert paths
    assert all(".hermes" in path for path in paths)

