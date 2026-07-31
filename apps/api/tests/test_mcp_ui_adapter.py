from __future__ import annotations

from datetime import UTC, datetime

import pytest

from api.mcp_ui_adapter import ApiMcpUiPublisher, McpUiPublishingDisabled
from core.surfaces.models import (
    McpAppSurfaceSource,
    SurfaceDescriptor,
    SurfaceId,
    SurfaceLifecycle,
    SurfaceRevision,
)
from workspace_service.surfaces import McpUiPublication


NOW = datetime(2026, 7, 30, tzinfo=UTC)


class Surfaces:
    def __init__(self) -> None:
        self.declarations = []
        self.transitions = []

    async def declare(self, **values) -> SurfaceDescriptor:
        self.declarations.append(values)
        return SurfaceDescriptor(
            schema_version=1,
            surface_id=SurfaceId("mcp-app-surface"),
            workspace_id=values["actor"].workspace_id,
            source=values["source"],
            title=values["title"],
            lifecycle=SurfaceLifecycle.DECLARED,
            revision=SurfaceRevision(1),
            created_at=NOW,
            updated_at=NOW,
        )

    async def transition(self, **values) -> SurfaceDescriptor:
        self.transitions.append(values)
        previous = (
            self.declarations[0]["source"]
            if len(self.transitions) == 1
            else self.transitions[-2]["descriptor"].source
            if "descriptor" in self.transitions[-2]
            else self.declarations[0]["source"]
        )
        revision = SurfaceRevision(len(self.transitions) + 1)
        descriptor = SurfaceDescriptor(
            schema_version=1,
            surface_id=values["surface_id"],
            workspace_id=self.declarations[0]["actor"].workspace_id,
            source=previous,
            title=self.declarations[0]["title"],
            lifecycle=values["target"],
            revision=revision,
            created_at=NOW,
            updated_at=NOW,
        )
        self.transitions[-1]["descriptor"] = descriptor
        return descriptor


def _publication() -> McpUiPublication:
    return McpUiPublication(
        user_id="user-one",
        workspace_id="workspace-one",
        session_id="session-one",
        gateway_session_id="gateway-one",
        server_id="server-one",
        server_connection_id="server-one:7",
        resource_uri="ui://server-one/app",
        content_hash="a" * 64,
        protocol_version="2025-11-25",
        title="Reference MCP App",
        idempotency_key="tool-call-one",
    )


@pytest.mark.asyncio
async def test_api_adapter_publishes_ready_mcp_app_surface_with_exact_binding() -> None:
    surfaces = Surfaces()
    descriptor = await ApiMcpUiPublisher(surfaces, enabled=True).publish(
        _publication()
    )

    assert descriptor.lifecycle is SurfaceLifecycle.READY
    assert isinstance(descriptor.source, McpAppSurfaceSource)
    assert descriptor.source.gateway_session_id == "gateway-one"
    assert descriptor.source.server_id == "server-one"
    assert descriptor.source.server_connection_id == "server-one:7"
    assert descriptor.source.resource_uri == "ui://server-one/app"
    assert descriptor.source.content_hash == "a" * 64
    assert [item["target"] for item in surfaces.transitions] == [
        SurfaceLifecycle.STARTING,
        SurfaceLifecycle.READY,
    ]


@pytest.mark.asyncio
async def test_disabled_mcp_apps_host_preserves_non_ui_fallback() -> None:
    surfaces = Surfaces()
    with pytest.raises(McpUiPublishingDisabled, match="fallback"):
        await ApiMcpUiPublisher(surfaces, enabled=False).publish(_publication())
    assert surfaces.declarations == []
