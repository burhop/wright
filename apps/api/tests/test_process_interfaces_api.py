"""Native process APIs derive scope and compose real preparation/readiness."""

from types import SimpleNamespace

import pytest

from api.main import app
from api.routers.workspace import get_workspace_service
from api.security import SecuritySettings
from packages.workspace_service.tests.test_process_preparation_service import owner
from packages.workspace_service.tests.test_process_input_readiness import (
    source,
    process,
)


@pytest.fixture
def case(tmp_path):
    text = source(default="Accepted default")
    application = owner(tmp_path, text)
    workspace = application.workspace
    workspace.ensure_workspace_path_safe = lambda path: path
    workspace.lifecycle = SimpleNamespace(
        get_by_session=lambda key: (
            {
                "workspace_id": "workspace",
                "local_path": str(tmp_path),
            }
            if key == "owned-session"
            else None
        )
    )
    workspace.process_interfaces = application
    app.dependency_overrides[get_workspace_service] = lambda: workspace
    yield SimpleNamespace(
        owner=application,
        text=text,
        root=tmp_path,
        query={
            "session_id": "owned-session",
            "path": process(text).source_path,
            "expected_storage_digest": process(text).source_digest,
        },
    )
    app.dependency_overrides.pop(get_workspace_service, None)


def test_preparation_inputs_and_readiness_use_the_existing_owner(sync_client, case):
    response = sync_client.get(
        "/api/workspace/process-interfaces/interaction", params=case.query
    )
    assert response.status_code == 200
    assert response.json()["context"]["process"]["workspace_id"] == "workspace"
    assert response.headers["cache-control"] == "no-store"
    assert not (case.root / "state.db").exists()
    prepared = sync_client.post(
        "/api/workspace/process-interfaces/inputs",
        json={
            **case.query,
            "bindings": [
                {"kind": "value", "input_id": "brief", "value": "Run requirements"}
            ],
        },
    )
    assert prepared.status_code == 200
    frozen = prepared.json()
    assert frozen["bindings"][0]["value"] == "Run requirements"
    assert frozen["process"]["workspace_id"] == "workspace"
    assert prepared.headers["cache-control"] == "no-store"
    readiness = sync_client.post(
        "/api/workspace/process-interfaces/readiness",
        json={
            **case.query,
            "input_snapshot_id": frozen["snapshot_id"],
        },
    )
    assert readiness.status_code == 200
    assert readiness.json()["state"] == "ready"
    assert readiness.json()["input_digest"] == frozen["digest"]
    assert not (case.root / "first.txt").exists()


def test_foreign_session_and_changed_source_do_not_receive_other_context(
    sync_client, case
):
    foreign = sync_client.get(
        "/api/workspace/process-interfaces/interaction",
        params={**case.query, "session_id": "other"},
    )
    assert foreign.status_code == 404
    changed = sync_client.get(
        "/api/workspace/process-interfaces/interaction",
        params={**case.query, "expected_storage_digest": "0" * 64},
    )
    assert changed.status_code == 409
    assert changed.json()["error_code"] == "SOURCE_CHANGED"
    assert changed.json()["details"]["correction"]
    assert changed.headers["cache-control"] == "no-store"


def test_client_cannot_supply_identity_or_permissions_and_errors_do_not_echo(
    sync_client, case
):
    for field in ("principal_id", "workspace_id", "capabilities"):
        response = sync_client.post(
            "/api/workspace/process-interfaces/inputs",
            json={**case.query, field: "private-value-must-not-echo"},
        )
        assert response.status_code == 422
        assert "private-value-must-not-echo" not in response.text
        assert response.headers["cache-control"] == "no-store"


def test_malformed_binding_is_rejected_without_unbounded_input_echo(sync_client, case):
    response = sync_client.post(
        "/api/workspace/process-interfaces/inputs",
        json={
            **case.query,
            "bindings": [
                {
                    "kind": "not-supported",
                    "input_id": "brief",
                    "value": "private-value-must-not-echo",
                }
            ],
        },
    )
    assert response.status_code == 422
    assert "private-value-must-not-echo" not in response.text


def test_invalid_discriminator_and_field_name_are_not_echoed(sync_client, case):
    for extra in (
        {
            "bindings": [
                {
                    "kind": "private-value-must-not-echo",
                    "input_id": "brief",
                    "value": "anything",
                }
            ]
        },
        {"private-value-must-not-echo": "anything"},
    ):
        response = sync_client.post(
            "/api/workspace/process-interfaces/inputs", json={**case.query, **extra}
        )
        assert response.status_code == 422
        assert "private-value-must-not-echo" not in response.text


def test_authentication_and_origin_policy_still_cover_new_routes(
    sync_client, case, monkeypatch
):
    settings = SecuritySettings(
        "enforced", "test-only-token", ("http://allowed.local",), "127.0.0.1"
    )
    monkeypatch.setattr(app.state, "security_settings", settings)
    unauthenticated = sync_client.get(
        "/api/workspace/process-interfaces/interaction", params=case.query
    )
    assert unauthenticated.status_code == 401
    denied = sync_client.get(
        "/api/workspace/process-interfaces/interaction",
        params=case.query,
        headers={
            "Authorization": "Bearer test-only-token",
            "Origin": "http://other.local",
        },
    )
    assert denied.status_code == 403
    allowed = sync_client.get(
        "/api/workspace/process-interfaces/interaction",
        params=case.query,
        headers={
            "Authorization": "Bearer test-only-token",
            "Origin": "http://allowed.local",
        },
    )
    assert allowed.status_code == 200


def test_declared_body_size_is_bounded_before_materialization(sync_client, case):
    response = sync_client.post(
        "/api/workspace/process-interfaces/inputs",
        headers={"Content-Length": str(67_108_865)},
        content=b"{}",
    )
    assert response.status_code == 413
    assert response.json()["error_code"] == "process_interface_request_too_large"


def test_frozen_preparation_attachment_does_not_execute(sync_client, case):
    frozen = sync_client.post(
        "/api/workspace/process-interfaces/inputs", json=case.query
    ).json()
    response = sync_client.get(
        "/api/workspace/process-interfaces/interaction",
        params={**case.query, "input_snapshot_id": frozen["snapshot_id"]},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["context"]["input_snapshot_id"] == frozen["snapshot_id"]
    assert body["inputs"][0]["current_value"]["value"] == "Accepted default"
    assert body["readiness"]["input_digest"] == frozen["digest"]
    assert not (case.root / "first.txt").exists()


def test_role_gate_matches_existing_validation_reads(monkeypatch):
    from fastapi import FastAPI, Request
    from fastapi.testclient import TestClient
    from api.routers.process_interfaces import router

    probe = FastAPI()
    probe.state.security_settings = SimpleNamespace(enforced=True)

    @probe.middleware("http")
    async def identity(request: Request, call_next):
        request.state.principal_role = "viewer"
        return await call_next(request)

    probe.dependency_overrides[get_workspace_service] = lambda: (_ for _ in ()).throw(
        AssertionError("The denied caller must not resolve workspace services")
    )
    probe.include_router(router, prefix="/api/workspace/process-interfaces")
    with TestClient(probe) as client:
        response = client.get(
            "/api/workspace/process-interfaces/interaction",
            params={
                "session_id": "owned",
                "path": "workflows/test.wflow",
                "expected_storage_digest": "a" * 64,
            },
        )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_chunked_body_bound_rejects_before_route_invocation():
    from api.main import ProcessInterfaceBodyLimitMiddleware

    calls, sent = [], []
    messages = iter(
        (
            {"type": "http.request", "body": b"abcd", "more_body": True},
            {"type": "http.request", "body": b"e", "more_body": False},
        )
    )

    async def receive():
        return next(messages)

    async def send(message):
        sent.append(message)

    async def downstream(*args):
        calls.append(args)

    middleware = ProcessInterfaceBodyLimitMiddleware(downstream, max_body_bytes=4)
    await middleware(
        {
            "type": "http",
            "path": "/api/workspace/process-interfaces/inputs",
            "method": "POST",
            "state": {"trace_id": "trace-bounded"},
        },
        receive,
        send,
    )
    assert calls == []
    assert sent[0]["status"] == 413
    assert b"trace-bounded" in sent[1]["body"]


@pytest.mark.asyncio
async def test_recorded_run_attachment_preserves_checkpoint_and_does_not_replay(
    sync_client, tmp_path
):
    from packages.workspace_service.tests.test_workflow_approval_execution import (
        setup_case,
    )
    from packages.workspace_service.tests.test_process_interaction_owners import (
        application,
        reference,
    )

    existing = await setup_case(tmp_path)
    interfaces = application(existing.services, tmp_path)
    workspace = existing.services
    workspace.process_interfaces = interfaces
    workspace.ensure_workspace_path_safe = lambda path: path
    workspace.lifecycle = SimpleNamespace(
        get_by_session=lambda key: (
            {"workspace_id": "ws", "local_path": str(tmp_path)}
            if key == "owned-session"
            else None
        )
    )
    process_ref = reference(tmp_path, existing.checkpoint.workflow_id)
    params = {
        "session_id": "owned-session",
        "path": process_ref.source_path,
        "expected_storage_digest": process_ref.source_digest,
        "run_id": existing.result["run_id"],
    }
    log = tmp_path / existing.result["run_log_path"]
    before, calls = log.read_bytes(), list(existing.calls)
    app.dependency_overrides[get_workspace_service] = lambda: workspace
    try:
        response = sync_client.get(
            "/api/workspace/process-interfaces/interaction", params=params
        )
        assert response.status_code == 200
        snapshot = response.json()
        assert snapshot["state"] == "waiting_human"
        assert (
            snapshot["interactions"][0]["checkpoint_id"]
            == existing.checkpoint.checkpoint_id
        )
        assert (
            snapshot["interactions"][0]["subject_digest"]
            == existing.checkpoint.subject_digest
        )
        override = sync_client.get(
            "/api/workspace/process-interfaces/interaction",
            params={**params, "input_snapshot_id": "different-inputs"},
        )
        assert override.status_code == 422
        assert override.json()["error_code"] == "RESPONSE_INVALID"
        assert log.read_bytes() == before
        assert existing.calls == calls
    finally:
        app.dependency_overrides.pop(get_workspace_service, None)
