from __future__ import annotations

from types import SimpleNamespace

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from api.routers.workflow_drafts import router
from core.workflow_drafts import canonical_sha256
from workspace_service import WorkflowDraftService


def make_client(tmp_path, *, enabled: bool) -> tuple[TestClient, WorkflowDraftService]:
    app = FastAPI()
    app.state.security_settings = SimpleNamespace(enforced=False)
    app.state.workflow_composer_enabled = enabled
    service = WorkflowDraftService(tmp_path / "wright.sqlite3")
    app.state.workflow_draft_service = service

    @app.middleware("http")
    async def test_trace(request: Request, call_next):  # type: ignore[no-untyped-def]
        request.state.trace_id = request.headers.get("X-Trace-Id", "test-trace")
        return await call_next(request)

    app.include_router(router, prefix="/api/workflow-drafts")
    return TestClient(app), service


def test_disabled_composer_is_inert_and_support_safe(tmp_path) -> None:
    client, service = make_client(tmp_path, enabled=False)

    response = client.post(
        "/api/workflow-drafts",
        json={"title": "Hidden", "purpose": "Must not persist."},
    )

    assert response.status_code == 404
    assert response.json()["error_code"] == "WORKFLOW_COMPOSER_UNAVAILABLE"
    assert response.json()["recovery_class"] == "enable_feature"
    assert not service.repository.db_path.exists()


def test_enabled_create_read_validate_and_save_round_trip(tmp_path) -> None:
    client, _ = make_client(tmp_path, enabled=True)

    created_response = client.post(
        "/api/workflow-drafts",
        json={"title": "New workflow", "purpose": "Compose safely."},
        headers={"X-Trace-Id": "trace-draft-1"},
    )
    assert created_response.status_code == 201
    created = created_response.json()
    etag = created_response.headers["etag"]
    assert created["revision"] == 1
    assert created_response.headers["x-trace-id"] == "trace-draft-1"

    read_response = client.get(f"/api/workflow-drafts/{created['draft_id']}")
    assert read_response.status_code == 200
    assert read_response.json() == created
    assert read_response.headers["etag"] == etag

    validation = client.post(
        f"/api/workflow-drafts/{created['draft_id']}/validate", json=created
    )
    assert validation.status_code == 200
    assert validation.json()["valid"] is True

    candidate = dict(created)
    candidate["semantic"] = dict(created["semantic"])
    candidate["semantic"]["title"] = "Updated workflow"
    candidate["semantic_sha256"] = canonical_sha256(candidate["semantic"])
    saved_response = client.put(
        f"/api/workflow-drafts/{created['draft_id']}",
        json=candidate,
        headers={"If-Match": etag},
    )

    assert saved_response.status_code == 200
    assert saved_response.json()["revision"] == 2
    assert saved_response.json()["semantic"]["title"] == "Updated workflow"
    assert saved_response.headers["etag"] != etag


def test_invalid_transport_returns_closed_error_without_echoing_body(tmp_path) -> None:
    client, _ = make_client(tmp_path, enabled=True)
    created = client.post("/api/workflow-drafts", json={}).json()
    created["release_target"] = "private-customer-name"

    response = client.post(
        f"/api/workflow-drafts/{created['draft_id']}/validate", json=created
    )

    assert response.status_code == 422
    assert response.json()["error_code"] == "WORKFLOW_DRAFT_INVALID"
    assert "private-customer-name" not in response.text
