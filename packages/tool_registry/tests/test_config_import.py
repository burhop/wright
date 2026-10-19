from datetime import UTC, datetime

from mcp_import_fixtures import (
    CLAUDE_MULTI_SERVER,
    PLAIN_LOCAL,
    VSCODE_WITH_INPUT,
)
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


def test_public_environment_is_explicit_and_private_fields_remain_value_free():
    import json

    source = {
        "name": "Example",
        "command": "uvx",
        "args": ["example-mcp"],
        "env": {"API_KEY": "synthetic-private", "RUN_MODE": "read-only"},
    }
    default = preview_configuration(source, now=NOW)["drafts"][0]
    assert "read-only" not in json.dumps(
        default
    ) and "synthetic-private" not in json.dumps(default)
    assert {item["name"] for item in default["env_vars"]} == {"API_KEY", "RUN_MODE"}
    explicit = preview_configuration(
        {**source, "public_env": {"RUN_MODE": "read-only"}}, now=NOW
    )["drafts"][0]
    assert explicit["launch_env"] == {"RUN_MODE": "read-only"}
    assert explicit["env_vars"] == [
        {"name": "API_KEY", "label": "API_KEY", "required": True, "secret": True}
    ]
    assert "synthetic-private" not in json.dumps(explicit)
    assert explicit["draft_digest"] != default["draft_digest"]


def test_public_environment_cannot_declare_credential_names_or_undeclared_fields():
    for public in (
        {"API_KEY": "synthetic-private"},
        {"other": "value"},
        {"RUN_MODE": "x" * 4097},
    ):
        draft = preview_configuration(
            {
                "command": "uvx",
                "env": {"API_KEY": "", "RUN_MODE": ""},
                "public_env": public,
            },
            now=NOW,
        )["drafts"][0]
        assert "public_environment_invalid" in {
            item["code"] for item in draft["errors"]
        }
        assert "launch_env" not in draft
        assert "synthetic-private" not in str(draft)


def test_private_http_header_definitions_reach_plan_without_values():
    import json

    draft = preview_configuration(
        {
            "name": "Remote",
            "type": "http",
            "url": "https://provider.example/mcp",
            "headers": {"Authorization": "Bearer placeholder-private"},
        },
        now=NOW,
    )["drafts"][0]
    assert not draft["errors"]
    assert draft["env_vars"][0]["target"] == "http_header"
    assert (
        draft["env_vars"][0]["name"] == "Authorization"
        and draft["env_vars"][0]["secret"]
    )
    assert "placeholder-private" not in json.dumps(draft)
    for headers in ({"Host": "value"}, {"Authorization": "a", "authorization": "b"}):
        invalid = preview_configuration(
            {"url": "https://provider.example/mcp", "headers": headers}, now=NOW
        )["drafts"][0]
        assert invalid["errors"]
