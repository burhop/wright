from __future__ import annotations

from pathlib import Path

from wright_engineering.manager_profiles import codex_mcp_config


def test_codex_stdio_profile_connects_directly_to_wright(tmp_path: Path) -> None:
    config = codex_mcp_config(
        workspace=tmp_path / "workspace",
        session_id="session-codex",
        workspace_id="workspace-codex",
        wright_home=tmp_path / "wright-home",
    )
    assert config["command"] == "wright"
    assert config["args"][:3] == ["mcp", "serve", "--stdio"]
    assert config["env"]["WRIGHT_MANAGER_ID"] == "codex"
    assert "HERMES_HOME" not in config["env"]
    assert config["args"][-4:] == [
        "--session-id",
        "session-codex",
        "--workspace-id",
        "workspace-codex",
    ]


def test_codex_http_profile_uses_provider_neutral_endpoint(tmp_path: Path) -> None:
    config = codex_mcp_config(
        transport="streamable-http",
        wright_home=tmp_path / "wright-home",
    )
    assert config == {
        "url": "http://127.0.0.1:8000/mcp",
        "bearer_token_env_var": "WRIGHT_API_TOKEN",
    }
