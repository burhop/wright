from __future__ import annotations

from datetime import UTC, datetime

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

import api.routers.surface_mcp_apps as routes
from api.routers.surface_mcp_apps import get_gateway_service, router
from api.routers.surfaces import get_surface_service
from core.surfaces.models import (
    McpAppSurfaceSource,
    SurfaceDescriptor,
    SurfaceId,
    SurfaceLifecycle,
    SurfaceRevision,
)
from tool_registry.gateway_models import GatewayToolResult
from tool_registry.models import McpUiResourceMetadata
from tool_registry.ui.resources import McpUiBinding
from workspace_service.config import (
    SurfaceFeatureFlags,
    SurfacePolicySettings,
    SurfacePreviewSettings,
    WorkspaceSurfaceSettings,
)


NOW = datetime(2026, 7, 31, tzinfo=UTC)


def _source() -> McpAppSurfaceSource:
    return McpAppSurfaceSource(
        gateway_session_id="gateway-session",
        server_id="cad",
        server_connection_id="cad:4",
        resource_uri="ui://cad/designer",
        content_hash="a" * 64,
        protocol_version="2026-01-26",
        initial_tool_input={"part": "bracket"},
        fallback_result={
            "content": [{"type": "text", "text": "Bracket created"}],
            "structuredContent": {"partId": "part-1"},
        },
        declared_host_capabilities=frozenset({"user.message"}),
    )


def _descriptor(source: McpAppSurfaceSource | None = None) -> SurfaceDescriptor:
    return SurfaceDescriptor(
        schema_version=1,
        surface_id=SurfaceId("mcp-surface"),
        workspace_id="workspace-1",
        source=source or _source(),
        title="CAD designer",
        lifecycle=SurfaceLifecycle.READY,
        revision=SurfaceRevision(3),
        created_at=NOW,
        updated_at=NOW,
    )


class _Surfaces:
    descriptor = _descriptor()

    async def get(self, *, actor, surface_id):
        assert actor.workspace_id == "workspace-1"
        assert str(surface_id) == "mcp-surface"
        return self.descriptor


class _Gateway:
    def __init__(self) -> None:
        self.calls: list[tuple] = []
        self.binding = McpUiBinding(
            gateway_session_id="gateway-session",
            workspace_id="workspace-1",
            server_id="cad",
            server_connection_id="cad:4",
            upstream_resource_uri="ui://cad/designer",
            content_hash="a" * 64,
            source_version="a" * 64,
            media_type="text/html;profile=mcp-app",
            content="<main>Designer</main>",
            metadata=McpUiResourceMetadata.merge(
                {},
                {
                    "ui": {
                        "csp": {
                            "connectDomains": ["https://api.example.test"]
                        },
                        "permissions": {"camera": {}},
                    }
                },
            ),
            subscribed=True,
        )

    async def read_app_resource(self, *args):
        self.calls.append(("read", *args))
        if args[-1] == "ui://cad/other":
            return McpUiBinding(
                **{
                    **{
                        field: getattr(self.binding, field)
                        for field in self.binding.__dataclass_fields__
                    },
                    "upstream_resource_uri": "ui://cad/other",
                    "content": "other",
                }
            )
        return self.binding

    async def call_app_tool(self, *args):
        self.calls.append(("tool", *args))
        return GatewayToolResult(
            content=({"type": "text", "text": "done"},),
            structured_content={"ok": True},
        )

    async def list_app_resources(self, *args):
        self.calls.append(("list", *args))
        return {"resources": [{"uri": "ui://cad/designer"}]}

    async def list_app_resource_templates(self, *args):
        self.calls.append(("templates", *args))
        return {"resourceTemplates": []}

    def cancel(self, *args):
        self.calls.append(("cancel", *args))
        return True


def _settings(enabled: bool = True) -> WorkspaceSurfaceSettings:
    return WorkspaceSurfaceSettings(
        flags=SurfaceFeatureFlags(model=True, mcp_apps=enabled),
        preview=SurfacePreviewSettings(
            scheme="https",
            domain="preview.example.test",
            public_port=443,
        ),
        policy=SurfacePolicySettings(),
    )


def _client(monkeypatch, *, enabled: bool = True):
    app = FastAPI()
    surfaces = _Surfaces()
    gateway = _Gateway()

    @app.middleware("http")
    async def actor(request: Request, call_next):
        request.state.principal_id = "user-1"
        request.state.principal_role = "engineer"
        return await call_next(request)

    app.include_router(router, prefix="/api/workspace")
    app.dependency_overrides[get_surface_service] = lambda: surfaces
    app.dependency_overrides[get_gateway_service] = lambda: gateway
    monkeypatch.setattr(
        routes, "get_workspace_surface_settings", lambda: _settings(enabled)
    )
    return TestClient(app), surfaces, gateway


def _headers() -> dict[str, str]:
    return {
        "X-Wright-Workspace-ID": "workspace-1",
        "X-Wright-Session-ID": "surface-session",
    }


def test_projection_revalidates_exact_resource_and_denies_requested_permissions(
    monkeypatch,
) -> None:
    client, _surfaces, gateway = _client(monkeypatch)
    response = client.get(
        "/api/workspace/surfaces/mcp-surface/mcp-app/presentation",
        headers=_headers(),
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["capability"] == "supported"
    assert payload["protocolVersion"] == "2026-01-26"
    assert payload["sandboxOrigin"] == "https://mcp-sandbox.preview.example.test"
    assert payload["resource"] == {
        "html": "<main>Designer</main>",
        "mediaType": "text/html;profile=mcp-app",
        "csp": {"connectDomains": ["https://api.example.test"]},
        "grantedPermissions": {},
    }
    assert payload["hostCapabilities"] == []
    assert payload["fallbackResult"]["structuredContent"] == {"partId": "part-1"}
    assert gateway.calls[0] == (
        "read",
        "gateway-session",
        "projection:mcp-surface",
        "cad",
        "cad",
        "ui://cad/designer",
    )


def test_projection_falls_back_when_disabled_or_content_binding_changes(
    monkeypatch,
) -> None:
    client, _surfaces, gateway = _client(monkeypatch, enabled=False)
    disabled = client.get(
        "/api/workspace/surfaces/mcp-surface/mcp-app/presentation",
        headers=_headers(),
    )
    assert disabled.json()["capability"] == "absent"
    assert gateway.calls == []

    client, _surfaces, gateway = _client(monkeypatch)
    gateway.binding = McpUiBinding(
        **{
            **{
                field: getattr(gateway.binding, field)
                for field in gateway.binding.__dataclass_fields__
            },
            "content_hash": "b" * 64,
        }
    )
    changed = client.get(
        "/api/workspace/surfaces/mcp-surface/mcp-app/presentation",
        headers=_headers(),
    ).json()
    assert changed["resource"] is None
    assert "changed" in changed["reason"]
    assert changed["fallbackResult"] is not None


def test_bridge_operations_are_scoped_to_persisted_gateway_and_server(monkeypatch) -> None:
    client, _surfaces, gateway = _client(monkeypatch)
    root = "/api/workspace/surfaces/mcp-surface/mcp-app"

    tool = client.post(
        f"{root}/tools/call",
        headers=_headers(),
        json={"requestId": "r1", "name": "cad__update", "arguments": {"x": 1}},
    )
    resources = client.post(
        f"{root}/resources/list",
        headers=_headers(),
        json={"requestId": "r2"},
    )
    templates = client.post(
        f"{root}/resource-templates/list",
        headers=_headers(),
        json={"requestId": "r3"},
    )
    read = client.post(
        f"{root}/resources/read",
        headers=_headers(),
        json={"requestId": "r4", "uri": "ui://cad/other"},
    )
    cancel = client.delete(
        f"{root}/operations/r4", headers=_headers()
    )

    assert tool.json() == {
        "content": [{"type": "text", "text": "done"}],
        "structuredContent": {"ok": True},
    }
    assert resources.json()["resources"][0]["uri"] == "ui://cad/designer"
    assert templates.json() == {"resourceTemplates": []}
    assert read.json()["contents"][0]["text"] == "other"
    assert cancel.status_code == 204
    assert ("tool", "gateway-session", "r1", "cad", "cad__update", {"x": 1}) in gateway.calls
    assert ("cancel", "gateway-session", "r4", "MCP App request aborted") in gateway.calls


def test_projection_requires_workspace_headers(monkeypatch) -> None:
    client, _surfaces, gateway = _client(monkeypatch)
    response = client.get(
        "/api/workspace/surfaces/mcp-surface/mcp-app/presentation"
    )
    assert response.status_code == 422
    assert gateway.calls == []
