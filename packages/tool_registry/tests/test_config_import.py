from datetime import UTC, datetime

from fixtures.mcp_imports import CLAUDE_MULTI_SERVER, PLAIN_LOCAL, VSCODE_WITH_INPUT
from tool_registry.config_import import preview_configuration

NOW = datetime(2026, 8, 12, 12, tzinfo=UTC)


def test_claude_multi_server_normalizes_without_secret_values() -> None:
    preview = preview_configuration(CLAUDE_MULTI_SERVER, now=NOW)
    assert preview["detected_format"] == "claude_mcp_servers"
    assert [draft["name"] for draft in preview["drafts"]] == ["local", "remote"]
    local = preview["drafts"][0]
    assert local["transport"] == "stdio"
    assert local["command"] == "uvx"
    assert local["arguments"] == ["safe-mcp"]
    assert local["environment_requirements"] == [
        {"name": "API_TOKEN", "credential_required": True, "value_supplied": True}
    ]
    assert "secret-value" not in str(preview)
    assert preview["source_discarded"] is True


def test_vscode_input_becomes_credential_requirement() -> None:
    preview = preview_configuration(VSCODE_WITH_INPUT, now=NOW)
    draft = preview["drafts"][0]
    assert preview["detected_format"] == "vscode_servers"
    assert draft["transport"] == "streamable_http"
    assert draft["endpoint"] == "https://example.invalid/mcp"
    assert draft["header_requirements"] == [
        {"name": "Authorization", "credential_required": True, "value_supplied": True}
    ]
    assert "Bearer" not in str(preview)


def test_plain_server_is_stable_and_exact() -> None:
    first = preview_configuration(PLAIN_LOCAL, now=NOW)
    second = preview_configuration(PLAIN_LOCAL, now=NOW)
    assert first == second
    assert first["detected_format"] == "plain_server"
    assert first["drafts"][0]["name"] == "local"
    assert len(first["drafts"][0]["draft_digest"]) == 64
