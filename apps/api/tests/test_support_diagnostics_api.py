from __future__ import annotations

from datetime import UTC, datetime

import pytest
from data_vault import upgrade_database
from fastapi import FastAPI
from fastapi.testclient import TestClient
from workspace_service.adapters.runtime import create_workspace
from workspace_service.support_diagnostic_service import SupportDiagnosticService

from api.routers.support_diagnostics import (
    get_support_diagnostic_application,
    router,
)
from api.security import ControlPlaneSecurityMiddleware, SecuritySettings


@pytest.fixture
def client(tmp_path):
    database = tmp_path / "state.db"
    upgrade_database(database)
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    create_workspace(str(database), "ws-1", "session-1", str(workspace), "Fixture")
    values = iter(["snapshot_12345678", "confirmation-token"])
    service = SupportDiagnosticService(
        database,
        clock=lambda: datetime(2026, 8, 13, 12, tzinfo=UTC),
        token_factory=lambda _bytes: next(values),
        principal_digest_key=b"test-principal-digest-key",
    )
    application = FastAPI()
    application.state.security_settings = SecuritySettings(
        mode="compat",
        api_token=None,
        allowed_origins=("http://127.0.0.1:5173",),
        bind_host="127.0.0.1",
    )
    application.add_middleware(ControlPlaneSecurityMiddleware)
    application.include_router(router, prefix="/api/workspace/support-diagnostics")
    application.dependency_overrides[get_support_diagnostic_application] = lambda: (
        service
    )
    with TestClient(application) as test_client:
        yield test_client, application


def test_preview_then_exact_attachment_export_and_replay_denial(client) -> None:
    test_client, _ = client
    preview = test_client.post(
        "/api/workspace/support-diagnostics/preview",
        json={"workspace_id": "ws-1", "scope": {"session_id": "session-1"}},
    )

    assert preview.status_code == 200
    body = preview.json()
    assert body["snapshot"]["workspace_id"] == "ws-1"
    assert body["snapshot_digest"] == body["snapshot"]["snapshot_digest"]
    assert body["confirmation_token"] == "confirmation-token"
    assert "local_path" not in preview.text
    assert "command" not in preview.text

    request = {
        "workspace_id": "ws-1",
        "snapshot_digest": body["snapshot_digest"],
        "confirmation_token": body["confirmation_token"],
    }
    exported = test_client.post(
        "/api/workspace/support-diagnostics/export", json=request
    )
    replay = test_client.post("/api/workspace/support-diagnostics/export", json=request)

    assert exported.status_code == 200
    assert exported.headers["content-type"] == "application/json"
    assert exported.headers["cache-control"] == "no-store"
    assert exported.headers["x-content-type-options"] == "nosniff"
    assert "attachment;" in exported.headers["content-disposition"]
    assert exported.json() == body["snapshot"]
    assert replay.status_code == 403
    assert replay.json()["detail"]["code"] == "DIAGNOSTIC_EXPORT_DENIED"


def test_preview_requires_authentication_when_control_plane_is_enforced(client) -> None:
    test_client, application = client
    application.state.security_settings = SecuritySettings(
        mode="enforced",
        api_token="synthetic-test-token",
        allowed_origins=("http://127.0.0.1:5173",),
        bind_host="127.0.0.1",
    )

    denied = test_client.post(
        "/api/workspace/support-diagnostics/preview",
        json={"workspace_id": "ws-1", "scope": {}},
    )
    allowed = test_client.post(
        "/api/workspace/support-diagnostics/preview",
        headers={"Authorization": "Bearer synthetic-test-token"},
        json={"workspace_id": "ws-1", "scope": {}},
    )

    assert denied.status_code == 401
    assert allowed.status_code == 200


def test_cross_workspace_scope_returns_safe_stable_error(client) -> None:
    test_client, _ = client
    response = test_client.post(
        "/api/workspace/support-diagnostics/preview",
        json={"workspace_id": "ws-1", "scope": {"session_id": "other-session"}},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == {
        "code": "DIAGNOSTIC_SCOPE_FORBIDDEN",
        "message": "Support diagnostic request was denied.",
    }
