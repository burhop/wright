from agent_adapters.hermes_gateway import (
    hermes_config_paths,
    hermes_wright_gateway_profile,
)


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


def test_hermes_config_paths_include_active_windows_and_wright_profile(
    monkeypatch, tmp_path
):
    hermes_home = tmp_path / "home"
    local_app_data = tmp_path / "local"
    monkeypatch.setenv("HERMES_HOME", str(hermes_home))
    monkeypatch.setenv("LOCALAPPDATA", str(local_app_data))
    monkeypatch.delenv("HERMES_CONFIG_PATH", raising=False)
    monkeypatch.delenv("HERMES_PROFILE", raising=False)

    paths = hermes_config_paths()

    assert str(local_app_data / "hermes" / "config.yaml") in paths
    assert str(hermes_home / "profiles" / "wright" / "config.yaml") in paths
    assert str(hermes_home / "config.yaml") in paths


def test_hermes_gateway_profile_can_bind_exact_workspace_session():
    profile = hermes_wright_gateway_profile(
        "/wright",
        session_id="session-1",
        workspace_id="workspace-1",
        terminal_cwd="/workspace/project",
    )

    assert profile.args == [
        "run",
        "--project",
        "/wright",
        "python",
        "-m",
        "api.gateway_stdio",
        "--session-id",
        "session-1",
        "--workspace-id",
        "workspace-1",
        "--principal-id",
        "local-admin",
    ]
    assert profile.gateway_project_dir == "/wright"
    assert profile.terminal_config() == {"cwd": "/workspace/project"}
