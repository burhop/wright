from __future__ import annotations

import pytest
from data_vault import upgrade_database

from tool_registry.db import get_tools, insert_server, insert_tools
from tool_registry.gateway_models import GatewayToolResult
from tool_registry.models import (
    McpServer,
    McpTool,
    McpUiResourceMetadata,
    McpUiToolMetadata,
)


def _tool(meta: dict) -> McpTool:
    return McpTool(
        tool_id="server:render",
        server_id="server",
        name="render",
        input_schema={},
        annotations={},
        _meta=meta,
        is_enabled=True,
        created_at=1,
    )


def test_canonical_tool_ui_metadata_wins_and_preserves_upstream_values() -> None:
    tool = _tool(
        {
            "ui": {
                "resourceUri": "ui://server/canonical",
                "visibility": ["app"],
            },
            "ui/resourceUri": "ui://server/deprecated",
            "vendor/opaque": {"keep": True},
        }
    )

    assert tool.ui.resource_uri == "ui://server/canonical"
    assert tool.ui.visibility == frozenset({"app"})
    assert tool.ui.app_visible and not tool.ui.model_visible
    assert not tool.ui.accepted_deprecated_resource_uri
    assert tool.meta["vendor/opaque"] == {"keep": True}
    assert tool.model_dump(by_alias=True)["_meta"] == tool.meta


def test_deprecated_resource_uri_is_accepted_but_recorded() -> None:
    metadata = McpUiToolMetadata.from_upstream(
        {"ui/resourceUri": "ui://server/legacy"}
    )

    assert metadata.resource_uri == "ui://server/legacy"
    assert metadata.accepted_deprecated_resource_uri
    assert metadata.visibility == frozenset({"model", "app"})


@pytest.mark.parametrize(
    "metadata",
    [
        {"ui": {"resourceUri": "https://example.test/app"}},
        {"ui": {"visibility": ["everyone"]}},
        {"ui": {"visibility": "app"}},
    ],
)
def test_malformed_ui_authority_is_rejected(metadata: dict) -> None:
    with pytest.raises(ValueError):
        McpUiToolMetadata.from_upstream(metadata)


def test_content_item_ui_metadata_overrides_listing_defaults_without_loss() -> None:
    metadata = McpUiResourceMetadata.merge(
        {
            "ui": {
                "csp": {"connectDomains": ["https://listed.example"]},
                "prefersBorder": True,
            },
            "server/listing": "preserved",
        },
        {
            "ui": {
                "csp": {"connectDomains": []},
                "permissions": {"clipboardWrite": {}},
            },
            "server/content": "preserved",
        },
    )

    assert metadata.ui["csp"] == {"connectDomains": []}
    assert metadata.ui["prefersBorder"] is True
    assert metadata.ui["permissions"] == {"clipboardWrite": {}}
    assert metadata.upstream["server/listing"] == "preserved"
    assert metadata.upstream["server/content"] == "preserved"


def test_tool_result_preserves_every_content_type_structured_content_and_meta() -> None:
    blocks = [
        {"type": "text", "text": "Useful fallback", "_meta": {"item": 1}},
        {"type": "image", "data": "aW1hZ2U=", "mimeType": "image/png"},
        {"type": "audio", "data": "YXVkaW8=", "mimeType": "audio/wav"},
        {
            "type": "resource_link",
            "uri": "ui://server/details",
            "name": "Details",
        },
        {
            "type": "resource",
            "resource": {
                "uri": "wright://artifact/one",
                "mimeType": "text/plain",
                "text": "Embedded explanation",
            },
        },
    ]
    result = GatewayToolResult.from_upstream(
        {
            "content": blocks,
            "structuredContent": {"value": 42},
            "_meta": {"ui": {"resourceUri": "ui://server/app"}, "opaque": 7},
            "isError": False,
        }
    )

    assert [item["type"] for item in result.content] == [
        "text",
        "image",
        "audio",
        "resource_link",
        "resource",
    ]
    assert result.content[0]["_meta"] == {"item": 1}
    assert result.structured_content == {"value": 42}
    assert result.meta["opaque"] == 7
    fallback = result.meaningful_fallback()
    assert "Useful fallback" in fallback
    assert "Image content (image/png)" in fallback
    assert "Audio content (audio/wav)" in fallback
    assert "Resource: Details" in fallback
    assert "Embedded explanation" in fallback
    assert '"value": 42' in fallback


def test_structured_or_missing_ui_result_has_meaningful_model_fallback() -> None:
    structured = GatewayToolResult.from_upstream({"answer": 42})
    missing = GatewayToolResult.from_upstream({"content": []})

    assert structured.structured_content == {"answer": 42}
    assert structured.meaningful_fallback() == '{"answer": 42}'
    assert "no fallback content" in missing.meaningful_fallback()


def test_upstream_tool_metadata_round_trips_through_registry_database(tmp_path) -> None:
    database = tmp_path / "state.db"
    upgrade_database(database)
    insert_server(
        str(database),
        McpServer(
            server_id="server",
            name="Server",
            type="stdio",
            command=["server"],
            is_active=False,
            status="inactive",
            created_at=1,
            updated_at=1,
        ),
    )
    original = _tool(
        {
            "ui": {"resourceUri": "ui://server/app"},
            "vendor/opaque": {"keep": True},
        }
    )
    insert_tools(str(database), [original])

    restored = get_tools(str(database), "server")[0]
    assert restored.meta == original.meta
    assert restored.ui.resource_uri == "ui://server/app"
