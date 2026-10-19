"""Inert public drafts; never copy keys, change existing providers or grant tools."""

from pathlib import Path
import pytest
from tool_registry.models import EnvVarDefinition, McpServer


@pytest.fixture
def template(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1]))
    from desktop_connection_template import replacement_template

    return replacement_template


def server(**changes):
    return McpServer(
        **{
            "server_id": "old",
            "deployment_mode": "user-reviewed-import",
            "name": "Old",
            "type": "stdio",
            "command": ["uvx", "example-mcp==1.0.0"],
            "is_active": False,
            "is_installed": True,
            "status": "inactive",
            "created_at": 1,
            "updated_at": 1,
            **changes,
        }
    )


def test_replacement_is_new_named_draft_with_refs_only_and_old_source_unchanged(
    template,
):
    original = server(
        env_vars={"API_KEY": "placeholder-old-private-value"},
        launch_env={
            "RUN_MODE": "read-only",
            "ACCESS_TOKEN": "placeholder-must-not-copy",
        },
    )
    before = original.model_dump_json()
    result = template(original)
    assert result == {
        "name": "",
        "type": "stdio",
        "command": "uvx",
        "arguments": ["example-mcp==1.0.0"],
        "url": "",
        "environmentFields": ["API_KEY", "RUN_MODE", "ACCESS_TOKEN"],
        "publicCandidates": {"RUN_MODE": "read-only"},
    }
    assert "placeholder-old-private-value" not in str(
        result
    ) and "placeholder-must-not-copy" not in str(result)
    assert original.model_dump_json() == before


def test_http_header_fields_are_refs_and_private_urls_or_embedded_secrets_are_not_projected(
    template,
):
    result = template(
        server(
            type="sse",
            command="https://provider.example/mcp",
            env_vars=[
                EnvVarDefinition(
                    name="Authorization", label="Auth", target="http_header"
                )
            ],
        )
    )
    assert (
        result["headerFields"] == ["Authorization"]
        and result["environmentFields"] == []
    )
    assert (
        template(
            server(
                type="sse",
                command="https://provider.example/mcp?token=placeholder-private",
            )
        )
        is None
    )
    assert (
        template(server(command=["example", "--api-key", "placeholder-private"]))
        is None
    )


def test_legacy_source_is_not_inferred_public(template):
    assert (
        template(
            server(
                deployment_mode="catalog",
                command=["fixture", "PRIVATE_CONFIGURATION"],
                launch_env={"CONFIG": "PRIVATE_VALUE"},
            )
        )
        is None
    )
