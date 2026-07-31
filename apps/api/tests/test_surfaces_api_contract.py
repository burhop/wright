from __future__ import annotations

import ast
from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from pydantic import TypeAdapter, ValidationError

from api.routers.surfaces import get_surface_service, router
from api.schemas.surfaces import (
    DeclareSurfaceRequest,
    SurfaceDescriptorResponse,
)
from core.surfaces.models import (
    ExternalUrlSurfaceSource,
    SurfaceDescriptor,
    SurfaceId,
    SurfaceLifecycle,
    SurfaceRevision,
)
from workspace_service.surfaces.service import ActorRole


pytestmark = pytest.mark.workspace_surfaces
ROOT = Path(__file__).resolve().parents[3]


def _descriptor() -> SurfaceDescriptor:
    now = datetime(2026, 7, 30, 12, 0, tzinfo=UTC)
    return SurfaceDescriptor(
        schema_version=1,
        surface_id=SurfaceId("surface-1"),
        workspace_id="workspace-1",
        source=ExternalUrlSurfaceSource(
            normalized_url="https://docs.example.test/guide",
            approval_id="approval-1",
            view_only=True,
        ),
        title="Guide",
        lifecycle=SurfaceLifecycle.DECLARED,
        revision=SurfaceRevision(1),
        created_at=now,
        updated_at=now,
    )


class FakeSurfaceService:
    def __init__(self) -> None:
        self.calls = []

    async def list(self, *, actor):
        self.calls.append(("list", actor))
        return [_descriptor()]

    async def get(self, *, actor, surface_id):
        self.calls.append(("get", actor, str(surface_id)))
        return _descriptor()

    async def declare(self, *, actor, source, title, idempotency_key):
        self.calls.append(("declare", actor, source, title, idempotency_key))
        return _descriptor()


def _client(role: str = "engineer") -> tuple[TestClient, FakeSurfaceService]:
    app = FastAPI()
    service = FakeSurfaceService()

    @app.middleware("http")
    async def actor(request: Request, call_next):
        request.state.principal_id = "user-1"
        request.state.principal_role = role
        return await call_next(request)

    app.include_router(router, prefix="/api/workspace")
    app.dependency_overrides[get_surface_service] = lambda: service
    return TestClient(app), service


def _headers() -> dict[str, str]:
    return {
        "X-Wright-Workspace-ID": "workspace-1",
        "X-Wright-Session-ID": "session-1",
        "Idempotency-Key": "declare-request-0001",
    }


def test_declare_request_is_discriminated_strict_and_versioned() -> None:
    adapter = TypeAdapter(DeclareSurfaceRequest)
    external = adapter.validate_python(
        {
            "schemaVersion": 1,
            "kind": "external_url",
            "url": "https://docs.example.test/guide",
            "approval": "explicit_view_only_instance",
        }
    )
    assert external.kind == "external_url"
    live = adapter.validate_python(
        {
            "schemaVersion": 1,
            "kind": "live_app",
            "manifest": {
                "schemaVersion": 1,
                "id": "brep",
                "title": "BREP",
                "version": "1.0.0",
                "launch": {"mode": "command", "argv": ["brep"]},
            },
        }
    )
    assert live.kind == "live_app"
    with pytest.raises(ValidationError):
        adapter.validate_python(
            {
                "schemaVersion": 2,
                "kind": "external_url",
                "url": "https://docs.example.test",
                "approval": "explicit_view_only_instance",
            }
        )
    with pytest.raises(ValidationError):
        adapter.validate_python(
            {
                "schemaVersion": 1,
                "kind": "external_url",
                "url": "https://docs.example.test",
                "approval": "explicit_view_only_instance",
                "targetUrl": "http://127.0.0.1:22",
            }
        )


def test_response_projection_uses_contract_aliases_and_hides_authority() -> None:
    payload = SurfaceDescriptorResponse.from_domain(_descriptor()).model_dump(
        mode="json", by_alias=True, exclude_none=True
    )
    assert payload == {
        "schemaVersion": 1,
        "surfaceId": "surface-1",
        "workspaceId": "workspace-1",
        "source": {
            "kind": "external_url",
            "sourceId": "approval-1",
            "sourceVersion": _descriptor().source.source_version,
            "displayUrl": "https://docs.example.test/guide",
            "viewOnly": True,
        },
        "title": "Guide",
        "lifecycle": "declared",
        "presentations": [],
        "capabilities": [],
        "revision": 1,
        "createdAt": "2026-07-30T12:00:00Z",
        "updatedAt": "2026-07-30T12:00:00Z",
    }
    serialized = repr(payload).lower()
    assert "target_pin" not in serialized
    assert "bootstrap" not in serialized
    assert "token" not in serialized
    assert "pid" not in serialized


@pytest.mark.parametrize("role", ["engineer", "admin"])
def test_engineer_and_admin_routes_pass_explicit_actor_scope(role: str) -> None:
    client, service = _client(role)
    response = client.post(
        "/api/workspace/surfaces",
        headers=_headers(),
        json={
            "schemaVersion": 1,
            "kind": "external_url",
            "url": "https://docs.example.test/guide",
            "approval": "explicit_view_only_instance",
        },
    )
    assert response.status_code == 201, response.text
    call = service.calls[-1]
    assert call[0] == "declare"
    assert call[1].user_id == "user-1"
    assert call[1].workspace_id == "workspace-1"
    assert call[1].session_id == "session-1"
    assert call[1].role is ActorRole(role)
    assert call[-1] == "declare-request-0001"


def test_forbidden_role_is_rejected_before_service_call() -> None:
    client, service = _client("viewer")
    response = client.get(
        "/api/workspace/surfaces",
        headers={
            key: value for key, value in _headers().items() if key != "Idempotency-Key"
        },
    )
    assert response.status_code == 403
    assert service.calls == []


def test_missing_scope_headers_are_rejected_before_service_call() -> None:
    client, service = _client()
    response = client.get("/api/workspace/surfaces")
    assert response.status_code == 422
    assert service.calls == []


def test_surface_router_contains_transport_translation_only() -> None:
    path = ROOT / "apps/api/src/api/routers/surfaces.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    forbidden = {"sqlite3", "subprocess", "socket", "httpx", "urllib"}
    imported = {
        alias.name.split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imported.update(
        (node.module or "").split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    )
    assert imported.isdisjoint(forbidden)
    assert not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "open"
        for node in ast.walk(tree)
    )
