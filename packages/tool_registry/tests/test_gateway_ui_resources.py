from __future__ import annotations

from typing import Any

import pytest

from tool_registry.gateway_models import GatewaySessionContext
from tool_registry.ui.resources import McpUiResourceStore


def _session(session_id: str = "session-one") -> GatewaySessionContext:
    return GatewaySessionContext(
        session_id,
        "principal",
        "workspace-one",
        "/workspace/one",
        "stdio",
    )


class Reader:
    def __init__(self) -> None:
        self.reads = 0
        self.value = "<h1>first</h1>"
        self.subscriptions: list[tuple[str, str]] = []

    def connection_id(self, server_id: str) -> str:
        return f"{server_id}:generation-1"

    async def list_resources(self, server_id: str) -> dict[str, Any]:
        return {"resources": []}

    async def read_resource(self, server_id: str, uri: str) -> dict[str, Any]:
        self.reads += 1
        return {
            "contents": [
                {
                    "uri": uri,
                    "mimeType": "text/html;profile=mcp-app",
                    "text": self.value,
                    "_meta": {"ui": {"csp": {"connectDomains": []}}},
                }
            ]
        }

    async def subscribe_resource(self, server_id: str, uri: str) -> None:
        self.subscriptions.append((server_id, uri))


@pytest.mark.asyncio
async def test_exact_read_succeeds_when_ui_uri_is_omitted_from_list() -> None:
    reader = Reader()
    store = McpUiResourceStore(reader)

    binding = await store.read(_session(), "server-one", "ui://shared/app")

    assert binding.content == "<h1>first</h1>"
    assert binding.media_type == "text/html;profile=mcp-app"
    assert binding.server_connection_id == "server-one:generation-1"
    assert binding.subscribed
    assert reader.subscriptions == [("server-one", "ui://shared/app")]


@pytest.mark.asyncio
async def test_content_hash_cache_is_invalidated_by_exact_resource_update() -> None:
    reader = Reader()
    store = McpUiResourceStore(reader)
    session = _session()
    first = await store.read(session, "server-one", "ui://shared/app")
    cached = await store.read(session, "server-one", "ui://shared/app")
    assert cached is first
    assert reader.reads == 1

    reader.value = "<h1>updated</h1>"
    assert store.invalidate(
        server_connection_id="server-one:generation-1",
        uri="ui://shared/app",
    ) == 1
    updated = await store.read(session, "server-one", "ui://shared/app")

    assert reader.reads == 2
    assert updated.content == "<h1>updated</h1>"
    assert updated.content_hash != first.content_hash
    assert updated.source_version == updated.content_hash
