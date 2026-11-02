from agent_adapters.hermes_gateway import (
    hermes_config_paths,
    hermes_wright_gateway_profile,
)
from agent_adapters.hermes import WRIGHT_SYSTEM_HINT


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


def test_explicit_config_does_not_sync_unrelated_host_locations(monkeypatch, tmp_path):
    selected = tmp_path / "isolated" / "config.yaml"
    monkeypatch.setenv("HERMES_CONFIG_PATH", str(selected))
    monkeypatch.setenv("HERMES_HOME", str(tmp_path / "other-home"))
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "other-local"))
    monkeypatch.setenv("HERMES_PROFILE", "other-profile")
    assert hermes_config_paths() == [str(selected)]


def test_wright_system_hint_has_no_solid_edge_tool_recipe():
    lowered = WRIGHT_SYSTEM_HINT.lower()

    assert "solid edge" not in lowered
    assert "providerid=solid_edge" not in lowered
    assert "cad.create_part_from_recipe" not in lowered
    assert "advertised descriptions and schemas" in lowered


def test_wright_system_hint_retries_deterministic_non_mutating_validation_errors():
    lowered = WRIGHT_SYSTEM_HINT.lower()

    assert "retryable validation errors" in lowered
    assert "no external state was changed" in lowered
    assert "apply every deterministic correction" in lowered
    assert "one revised tool call and retry" in lowered
    assert "repeats the same failure" in lowered


def test_native_gateway_binds_only_the_nonsecret_root_for_isolated_stdio(monkeypatch):
    monkeypatch.setenv("WRIGHT_HOME", "/tmp/isolated-wright")
    monkeypatch.setenv("WRIGHT_API_TOKEN", "must-not-copy")
    monkeypatch.setenv("OPENAI_API_KEY", "must-not-copy-either")
    profile = hermes_wright_gateway_profile(None, terminal_cwd="/tmp/workspace")
    assert profile.mcp_server_config()["env"] == {"WRIGHT_HOME": "/tmp/isolated-wright"}
    assert "env" not in hermes_wright_gateway_profile("/repo").mcp_server_config()
