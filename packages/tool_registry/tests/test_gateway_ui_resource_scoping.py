from __future__ import annotations

from typing import Any

import pytest

from tool_registry.gateway_models import GatewaySessionContext
from tool_registry.ui.resources import McpUiResourceStore


class ScopedReader:
    def __init__(self) -> None:
        self.connections = {"one": "one:g1", "two": "two:g1"}

    def connection_id(self, server_id: str) -> str:
        return self.connections[server_id]

    async def list_resources(self, server_id: str) -> dict[str, Any]:
        return {
            "resources": [
                {
                    "uri": "ui://collision/app",
                    "_meta": {"ui": {"prefersBorder": True}},
                }
            ]
        }

    async def read_resource(self, server_id: str, uri: str) -> dict[str, Any]:
        return {
            "contents": [
                {
                    "uri": uri,
                    "mimeType": "text/html;profile=mcp-app",
                    "text": f"<h1>{server_id}</h1>",
                    "_meta": {
                        "ui": {"prefersBorder": False},
                        "server": server_id,
                    },
                }
            ]
        }

    async def subscribe_resource(self, server_id: str, uri: str) -> None:
        return None


def _session(workspace: str, session: str) -> GatewaySessionContext:
    return GatewaySessionContext(
        session,
        "principal",
        workspace,
        f"/workspace/{workspace}",
        "stdio",
    )


@pytest.mark.asyncio
async def test_identical_ui_uri_never_collides_across_server_session_or_workspace() -> None:
    store = McpUiResourceStore(ScopedReader())
    first = await store.read(
        _session("workspace-one", "session-one"),
        "one",
        "ui://collision/app",
    )
    other_server = await store.read(
        _session("workspace-one", "session-one"),
        "two",
        "ui://collision/app",
    )
    other_session = await store.read(
        _session("workspace-one", "session-two"),
        "one",
        "ui://collision/app",
    )
    other_workspace = await store.read(
        _session("workspace-two", "session-three"),
        "one",
        "ui://collision/app",
    )

    assert first.content == "<h1>one</h1>"
    assert other_server.content == "<h1>two</h1>"
    assert len(
        {
            (
                item.workspace_id,
                item.gateway_session_id,
                item.server_connection_id,
                item.upstream_resource_uri,
                item.content_hash,
            )
            for item in (first, other_server, other_session, other_workspace)
        }
    ) == 4
    assert first.metadata.ui["prefersBorder"] is False
    assert first.metadata.upstream["server"] == "one"


@pytest.mark.asyncio
async def test_server_generation_change_creates_new_binding_identity() -> None:
    reader = ScopedReader()
    store = McpUiResourceStore(reader)
    session = _session("workspace-one", "session-one")
    first = await store.read(session, "one", "ui://collision/app")

    reader.connections["one"] = "one:g2"
    restarted = await store.read(session, "one", "ui://collision/app")

    assert restarted.server_connection_id == "one:g2"
    assert restarted is not first
