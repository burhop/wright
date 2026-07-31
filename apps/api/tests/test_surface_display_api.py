from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routers.surface_displays import (
    get_display_service,
    get_display_token_service,
    router,
)
from core.surfaces.models import (
    DisplaySurfaceSource,
    SurfaceDescriptor,
    SurfaceId,
    SurfaceLifecycle,
    SurfaceRevision,
)
from workspace_service.surfaces.display_service import (
    DisplayIngestResult,
    DisplayRevisionConflict,
)
from workspace_service.surfaces.display_tokens import (
    DisplayExecutionClaims,
    DisplayExecutionTokenService,
)


pytestmark = pytest.mark.workspace_surfaces
NOW = datetime(2026, 7, 30, 12, 0, tzinfo=UTC)


def _body(revision: int = 1) -> dict:
    return {
        "schemaVersion": 1,
        "displayId": "loads",
        "revision": revision,
        "idempotencyKey": f"display-request-{revision:04d}",
        "title": "Loads",
        "durability": "durable",
        "accessibility": {"description": "Load by time."},
        "representations": [
            {"mediaType": "text/plain", "encoding": "utf-8", "data": "10 N"}
        ],
    }


def _descriptor(revision: int = 1) -> SurfaceDescriptor:
    return SurfaceDescriptor(
        schema_version=1,
        surface_id=SurfaceId("surface-1"),
        workspace_id="workspace-1",
        source=DisplaySurfaceSource(
            execution_id="execution-1",
            display_id="loads",
            artifact_revision=revision,
            durability="durable",
            media_types=("text/plain",),
        ),
        title="Loads",
        lifecycle=SurfaceLifecycle.READY,
        revision=SurfaceRevision(revision),
        created_at=NOW,
        updated_at=NOW,
    )


class FakeDisplayService:
    def __init__(self) -> None:
        self.calls = []
        self.created = True
        self.error: Exception | None = None

    def ingest(self, body, *, context):
        self.calls.append((body, context))
        if self.error:
            raise self.error
        return DisplayIngestResult(
            descriptor=_descriptor(body["revision"]), created=self.created
        )


def _client() -> tuple[TestClient, FakeDisplayService, DisplayExecutionTokenService]:
    app = FastAPI()
    service = FakeDisplayService()
    tokens = DisplayExecutionTokenService(secret=b"test-secret" * 4, clock=lambda: NOW)
    app.include_router(router, prefix="/api/workspace")
    app.dependency_overrides[get_display_service] = lambda: service
    app.dependency_overrides[get_display_token_service] = lambda: tokens
    return TestClient(app), service, tokens


def _claims(**changes) -> DisplayExecutionClaims:
    values = {
        "audience": "wright-display-ingest-v1",
        "user_id": "user-1",
        "workspace_id": "workspace-1",
        "session_id": "session-1",
        "task_id": "task-1",
        "execution_id": "execution-1",
        "expires_at": NOW + timedelta(minutes=5),
        "prompt": "Plot load by time.",
        "effective_constraints": {"offline": True},
        "script": "import wright; wright.line(...)\n",
        "script_revision": 1,
        "trace_id": "a" * 32,
    }
    values.update(changes)
    return DisplayExecutionClaims(**values)


def _headers(token: str, workspace_id: str = "workspace-1") -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "X-Wright-Workspace-ID": workspace_id,
        "Idempotency-Key": "display-request-0001",
        "Content-Type": "application/vnd.wright.display+json",
    }


def test_valid_execution_token_binds_workspace_and_producer_context() -> None:
    client, service, tokens = _client()
    response = client.post(
        "/api/workspace/surfaces/displays",
        headers=_headers(tokens.issue(_claims())),
        json=_body(),
    )
    assert response.status_code == 201, response.text
    assert service.calls[0][1].workspace_id == "workspace-1"
    assert service.calls[0][1].execution_id == "execution-1"
    assert service.calls[0][1].prompt == "Plot load by time."


def test_duplicate_returns_original_revision_with_200() -> None:
    client, service, tokens = _client()
    service.created = False
    response = client.post(
        "/api/workspace/surfaces/displays",
        headers=_headers(tokens.issue(_claims())),
        json=_body(),
    )
    assert response.status_code == 200
    assert response.json()["revision"] == 1


@pytest.mark.parametrize(
    "claims,workspace",
    [
        (_claims(audience="another-audience"), "workspace-1"),
        (_claims(expires_at=NOW - timedelta(seconds=1)), "workspace-1"),
        (_claims(workspace_id="workspace-2"), "workspace-1"),
    ],
)
def test_wrong_audience_expired_and_cross_workspace_tokens_are_rejected(
    claims: DisplayExecutionClaims, workspace: str
) -> None:
    client, service, tokens = _client()
    response = client.post(
        "/api/workspace/surfaces/displays",
        headers=_headers(tokens.issue(claims), workspace),
        json=_body(),
    )
    assert response.status_code == 401
    assert service.calls == []


def test_revoked_execution_and_stale_revision_are_rejected() -> None:
    client, service, tokens = _client()
    token = tokens.issue(_claims())
    tokens.revoke_execution("execution-1")
    response = client.post(
        "/api/workspace/surfaces/displays", headers=_headers(token), json=_body()
    )
    assert response.status_code == 401
    service.error = DisplayRevisionConflict("loads", expected=2, received=1)
    fresh = tokens.issue(_claims(execution_id="execution-2"))
    response = client.post(
        "/api/workspace/surfaces/displays", headers=_headers(fresh), json=_body()
    )
    assert response.status_code == 409


def test_missing_or_malformed_bearer_never_reaches_service() -> None:
    client, service, _tokens = _client()
    for authorization in (None, "Basic nope", "Bearer malformed"):
        headers = {
            "X-Wright-Workspace-ID": "workspace-1",
            "Idempotency-Key": "display-request-0001",
            "Content-Type": "application/vnd.wright.display+json",
        }
        if authorization:
            headers["Authorization"] = authorization
        response = client.post(
            "/api/workspace/surfaces/displays", headers=headers, json=_body()
        )
        assert response.status_code == 401
    assert service.calls == []
