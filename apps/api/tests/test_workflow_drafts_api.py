from __future__ import annotations

from types import SimpleNamespace

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from api.routers.workflow_drafts import router
from core.workflow_drafts import canonical_sha256
from data_vault import WorkflowDraftStorageError
from workspace_service import WorkflowDraftService


def make_client(
    tmp_path,
    *,
    enabled: bool,
    enforced: bool = False,
    principal_role: str | None = None,
) -> tuple[TestClient, WorkflowDraftService]:
    app = FastAPI()
    app.state.security_settings = SimpleNamespace(enforced=enforced)
    app.state.workflow_composer_enabled = enabled
    service = WorkflowDraftService(tmp_path / "wright.sqlite3")
    app.state.workflow_draft_service = service

    @app.middleware("http")
    async def test_trace(request: Request, call_next):  # type: ignore[no-untyped-def]
        request.state.trace_id = request.headers.get("X-Trace-Id", "test-trace")
        if principal_role is not None:
            request.state.principal_role = principal_role
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


def test_exact_etag_supports_bodyless_conditional_reopen(tmp_path) -> None:
    client, _ = make_client(tmp_path, enabled=True)
    created_response = client.post("/api/workflow-drafts", json={})
    draft_id = created_response.json()["draft_id"]
    etag = created_response.headers["etag"]

    response = client.get(
        f"/api/workflow-drafts/{draft_id}", headers={"If-None-Match": etag}
    )

    assert response.status_code == 304
    assert response.content == b""
    assert response.headers["etag"] == etag


def test_stale_save_is_closed_and_does_not_replace_current_revision(tmp_path) -> None:
    client, _ = make_client(tmp_path, enabled=True)
    created_response = client.post("/api/workflow-drafts", json={})
    first = created_response.json()
    stale_etag = created_response.headers["etag"]
    candidate = {**first, "semantic": {**first["semantic"], "title": "Revision 2"}}
    candidate["semantic_sha256"] = canonical_sha256(candidate["semantic"])
    saved = client.put(
        f"/api/workflow-drafts/{first['draft_id']}",
        json=candidate,
        headers={"If-Match": stale_etag},
    )
    assert saved.status_code == 200

    stale = client.put(
        f"/api/workflow-drafts/{first['draft_id']}",
        json=candidate,
        headers={"If-Match": stale_etag},
    )

    assert stale.status_code == 412
    assert set(stale.json()) == {
        "error_code",
        "message",
        "recovery_class",
        "trace_id",
    }
    assert stale.json()["error_code"] == "WORKFLOW_DRAFT_STALE_REVISION"
    current = client.get(f"/api/workflow-drafts/{first['draft_id']}").json()
    assert current["revision"] == 2
    assert current["semantic"]["title"] == "Revision 2"


def test_invalid_graph_validate_and_save_preserve_prior_revision(tmp_path) -> None:
    client, _ = make_client(tmp_path, enabled=True)
    created_response = client.post("/api/workflow-drafts", json={})
    candidate = created_response.json()
    candidate["semantic"]["blocks"].append(
        {
            "id": "block.orphan",
            "title": "Orphan",
            "purpose": "Exercise complete graph validation.",
            "role": "work",
            "phase_id": "phase.draft",
            "input_port_ids": [],
            "output_port_ids": [],
            "gate_ids": [],
            "intended_artifact_ids": [],
        }
    )
    candidate["layout"]["positions"].append(
        {"semantic_id": "block.orphan", "x": 0, "y": 0}
    )
    candidate["semantic_sha256"] = canonical_sha256(candidate["semantic"])
    candidate["layout_sha256"] = canonical_sha256(candidate["layout"])
    path = f"/api/workflow-drafts/{candidate['draft_id']}"

    validation = client.post(f"{path}/validate", json=candidate)
    rejected = client.put(
        path,
        json=candidate,
        headers={"If-Match": created_response.headers["etag"]},
    )

    assert validation.status_code == 200
    assert validation.json()["valid"] is False
    assert validation.json()["diagnostics"][0]["code"] == "BLOCK_PHASE_RECIPROCITY"
    assert rejected.status_code == 422
    assert rejected.json()["error_code"] == "WORKFLOW_DRAFT_INVALID"
    assert client.get(path).json()["revision"] == 1


def test_request_body_limit_is_enforced_before_persistence(tmp_path) -> None:
    client, service = make_client(tmp_path, enabled=True)

    response = client.post(
        "/api/workflow-drafts",
        content=b'{"title":"x","purpose":"' + b"x" * (1024 * 1024) + b'"}',
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 413
    assert response.json()["error_code"] == "WORKFLOW_DRAFT_INVALID"
    assert not service.repository.db_path.exists()


def test_only_engineer_and_admin_roles_reach_authoring_routes(tmp_path) -> None:
    for role in ("engineer", "admin"):
        client, _ = make_client(
            tmp_path / role,
            enabled=True,
            enforced=True,
            principal_role=role,
        )
        assert client.post("/api/workflow-drafts", json={}).status_code == 201

    denied, service = make_client(
        tmp_path / "viewer",
        enabled=True,
        enforced=True,
        principal_role="viewer",
    )
    assert denied.post("/api/workflow-drafts", json={}).status_code == 403
    assert not service.repository.db_path.exists()


def test_router_exposes_no_release_execution_or_rivet_authority() -> None:
    route_shapes = {
        (route.path, method)
        for route in router.routes
        for method in getattr(route, "methods", set())
    }

    assert route_shapes == {
        ("", "POST"),
        ("/{draft_id}", "GET"),
        ("/{draft_id}", "PUT"),
        ("/{draft_id}/validate", "POST"),
    }


def test_unsupported_schema_has_specific_closed_recovery(tmp_path) -> None:
    client, _ = make_client(tmp_path, enabled=True)
    created = client.post("/api/workflow-drafts", json={}).json()
    created["schema_version"] = "2.0.0"

    response = client.post(
        f"/api/workflow-drafts/{created['draft_id']}/validate", json=created
    )

    assert response.status_code == 422
    assert response.json() == {
        "error_code": "WORKFLOW_DRAFT_INCOMPATIBLE_SCHEMA",
        "message": "Workflow draft schema is not supported.",
        "recovery_class": "install_compatible_wright",
        "trace_id": "test-trace",
    }


def test_path_body_identity_mismatch_and_missing_precondition_are_closed(tmp_path) -> None:
    client, _ = make_client(tmp_path, enabled=True)
    created_response = client.post("/api/workflow-drafts", json={})
    created = created_response.json()
    path = f"/api/workflow-drafts/{created['draft_id']}"
    mismatch = {**created, "draft_id": "draft.other"}

    validate = client.post(f"{path}/validate", json=mismatch)
    save = client.put(
        path,
        json=mismatch,
        headers={"If-Match": created_response.headers["etag"]},
    )
    missing_precondition = client.put(path, json=created)

    assert validate.status_code == 409
    assert save.status_code == 409
    assert validate.json()["error_code"] == "WORKFLOW_DRAFT_IDENTITY_MISMATCH"
    assert save.json()["error_code"] == "WORKFLOW_DRAFT_IDENTITY_MISMATCH"
    assert missing_precondition.status_code == 412
    assert missing_precondition.json()["error_code"] == (
        "WORKFLOW_DRAFT_STALE_REVISION"
    )
    assert client.get(path).json()["revision"] == 1


def test_not_found_and_storage_failures_are_support_safe(tmp_path, monkeypatch) -> None:
    client, service = make_client(tmp_path, enabled=True)

    missing = client.get("/api/workflow-drafts/draft.missing")
    assert missing.status_code == 404
    assert missing.json()["error_code"] == "WORKFLOW_DRAFT_NOT_FOUND"

    def fail_read(_draft_id):
        raise WorkflowDraftStorageError("D:/private/customer/workflow-drafts.sqlite3")

    monkeypatch.setattr(service.repository, "read", fail_read)
    failed = client.get("/api/workflow-drafts/draft.any")

    assert failed.status_code == 503
    assert failed.json() == {
        "error_code": "WORKFLOW_DRAFT_STORAGE_FAILED",
        "message": "Workflow draft storage is unavailable.",
        "recovery_class": "retry_or_inspect_local_store",
        "trace_id": "test-trace",
    }
    assert "private" not in failed.text
    assert failed.headers["cache-control"] == "no-store"
