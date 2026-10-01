"""Authenticated native authoring API with controlled model/compiler/runtime.

Actual repositories, revision verification and presentation/grant owners are
used. The loaded observation below is synthetic; managed browser proof is a
separate acceptance task.
"""

import asyncio
from contextlib import asynccontextmanager
from types import SimpleNamespace
import time

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
import pytest

from api.routers.process_interfaces import router
from api.routers.process_ui_authoring import get_process_ui_surfaces
from api.routers.workspace import get_workspace_service
from workspace_service.process_interfaces.artifacts import ProcessUIPreviewObservation
from workspace_service.process_interfaces.toolchain import UnavailableBuildToolchain
from packages.workspace_service.tests.test_process_ui_presentations import native_case

PREFIX = "/api/workspace/process-interfaces"


@pytest.fixture
def case(tmp_path, monkeypatch):
    prepared = native_case(tmp_path, monkeypatch)
    application = prepared.application
    workspace = application.workspace
    workspace.process_interfaces = application
    workspace.lifecycle = SimpleNamespace(
        get_by_session=lambda key: (
            {"workspace_id": "workspace", "local_path": str(tmp_path)}
            if key == "owned-session"
            else None
        )
    )
    application.__dict__["_authoring"] = prepared.author

    @asynccontextmanager
    async def lifespan(_):
        yield
        await application.close()

    app = FastAPI(lifespan=lifespan)
    app.state.security_settings = SimpleNamespace(enforced=True)
    state = {"principal": "user", "role": "engineer"}

    @app.middleware("http")
    async def identity(request: Request, call_next):
        request.state.principal_id = state["principal"]
        request.state.principal_role = state["role"]
        return await call_next(request)

    app.include_router(router, prefix=PREFIX)
    app.dependency_overrides[get_workspace_service] = lambda: workspace
    app.dependency_overrides[get_process_ui_surfaces] = lambda: prepared.surfaces
    query = {
        "session_id": "owned-session",
        "path": prepared.process.source_path,
        "expected_storage_digest": prepared.process.source_digest,
    }
    with TestClient(app) as client:
        yield SimpleNamespace(
            **vars(prepared), client=client, query=query, app=app, state=state
        )


def generate(case, request_id="author-one", **changes):
    response = case.client.post(
        PREFIX + "/authoring-jobs",
        json=case.query
        | {
            "request_id": request_id,
            "instruction": "Compare these exact outputs",
            "title": "Results comparison",
            **changes,
        },
    )
    assert response.status_code == 202, response.text
    job = response.json()
    deadline = time.monotonic() + 8
    while time.monotonic() < deadline:
        status = case.client.get(
            PREFIX + "/authoring-jobs/" + job["job_id"], params=case.query
        )
        assert status.status_code == 200, status.text
        value = status.json()
        if value["job"]["state"] in {"preview_ready", "saved", "failed", "cancelled"}:
            assert value["job"]["state"] == "preview_ready", value
            return value
        time.sleep(0.01)
    pytest.fail("Controlled authoring did not finish within its test deadline")


def preview(case, value, request_id="preview-one"):
    response = case.client.post(
        PREFIX + "/authoring-jobs/" + value["job"]["job_id"] + "/preview",
        json=case.query | {"request_id": request_id},
    )
    assert response.status_code == 200, response.text
    return response.json()


def save(case, value, view, expected_active=None):
    manifest = value["preview"]["manifest"]
    report = value["preview"]["build"]
    case.application.ui_revisions.observe_preview(
        case.scope,
        case.process,
        value["job"]["job_id"],
        ProcessUIPreviewObservation(
            view["binding"]["presentation_id"],
            manifest["ui_id"],
            manifest["revision_id"],
            report["bundle_digest"],
        ),
    )
    response = case.client.post(
        PREFIX + f"/uis/{manifest['ui_id']}/revisions/{manifest['revision_id']}/save",
        json=case.query
        | {
            "job_id": value["job"]["job_id"],
            "source_digest": report["source_digest"],
            "manifest_digest": report["manifest_digest"],
            "bundle_digest": report["bundle_digest"],
            "expected_active_revision": expected_active,
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_generation_status_events_idempotency_and_preview_are_native_scoped(case):
    capabilities = case.client.get(
        PREFIX + "/authoring-capabilities", params=case.query
    )
    assert capabilities.status_code == 200 and capabilities.json()["available"]
    value = generate(case)
    events = case.client.get(
        PREFIX + "/authoring-jobs/" + value["job"]["job_id"] + "/events",
        params=case.query,
    )
    assert events.status_code == 200 and "event: authoring" in events.text
    assert '"state":"preview_ready"' in events.text
    again = case.client.post(
        PREFIX + "/authoring-jobs",
        json=case.query
        | {
            "request_id": "author-one",
            "instruction": "Compare these exact outputs",
            "title": "Results comparison",
        },
    )
    assert again.status_code == 202 and again.json()["job_id"] == value["job"]["job_id"]
    assert len(case.author.engine.calls) == 1
    view = preview(case, value)
    assert view["binding"]["read_only"] is True
    assert view["launch"]["kind"] == "panel"
    assert view["descriptor"]["workspaceId"] == "workspace"
    assert "absoluteBootstrapUrl" in view["launch"]
    assert not (case.root / "first.txt").exists()


def test_save_update_rollback_saved_open_and_close_use_exact_revisions(case):
    first = generate(case)
    first_view = preview(case, first)
    save(case, first, first_view)
    manifest = first["preview"]["manifest"]
    second = generate(
        case,
        "update-one",
        ui_id=manifest["ui_id"],
        base_revision=manifest["revision_id"],
        instruction="Emphasize findings",
    )
    second_view = preview(case, second, "preview-two")
    save(case, second, second_view, manifest["revision_id"])
    second_revision = second["preview"]["manifest"]["revision_id"]
    rollback = case.client.post(
        PREFIX + f"/uis/{manifest['ui_id']}/activate",
        json=case.query
        | {
            "revision_id": manifest["revision_id"],
            "expected_active_revision": second_revision,
        },
    )
    assert rollback.status_code == 200
    listed = case.client.get(PREFIX + "/uis", params=case.query)
    assert listed.status_code == 200 and len(listed.json()["interfaces"]) == 1
    assert listed.json()["interfaces"][0]["active_revision"] == manifest["revision_id"]
    revisions = case.client.get(
        PREFIX + f"/uis/{manifest['ui_id']}/revisions", params=case.query
    )
    assert revisions.status_code == 200 and len(revisions.json()["revisions"]) == 2
    compatible = case.client.get(
        PREFIX + f"/uis/{manifest['ui_id']}/compatibility", params=case.query
    )
    assert compatible.status_code == 200 and compatible.json()["state"] == "compatible"
    calls = len(case.author.engine.calls)
    case.author.toolchain = UnavailableBuildToolchain()
    case.app.state.agent_engine = None
    view_response = case.client.post(
        PREFIX + f"/uis/{manifest['ui_id']}/present",
        json=case.query | {"request_id": "saved-open"},
    )
    assert view_response.status_code == 200, view_response.text
    view = view_response.json()
    assert (
        view["binding"]["revision_id"] == manifest["revision_id"]
        and not view["binding"]["read_only"]
    )
    close = case.client.post(
        PREFIX + "/presentations/close",
        json=case.query
        | {
            "surface_id": view["descriptor"]["surfaceId"],
            "presentation_id": view["binding"]["presentation_id"],
        },
    )
    assert close.status_code == 204
    assert len(case.author.engine.calls) == calls
    case.application.runs.cancel.assert_not_called()


def test_save_requires_preview_and_hash_cas_authority(case):
    value = generate(case)
    manifest, report = value["preview"]["manifest"], value["preview"]["build"]
    url = PREFIX + f"/uis/{manifest['ui_id']}/revisions/{manifest['revision_id']}/save"
    body = case.query | {
        "job_id": value["job"]["job_id"],
        "source_digest": report["source_digest"],
        "manifest_digest": report["manifest_digest"],
        "bundle_digest": report["bundle_digest"],
        "expected_active_revision": None,
    }
    assert case.client.post(url, json=body).status_code == 403
    view = preview(case, value)
    case.application.ui_revisions.observe_preview(
        case.scope,
        case.process,
        value["job"]["job_id"],
        ProcessUIPreviewObservation(
            view["binding"]["presentation_id"],
            manifest["ui_id"],
            manifest["revision_id"],
            report["bundle_digest"],
        ),
    )
    assert (
        case.client.post(url, json=body | {"bundle_digest": "0" * 64}).status_code
        == 409
    )
    assert (
        case.client.post(
            url, json=body | {"expected_active_revision": "foreign-revision"}
        ).status_code
        == 409
    )
    assert (
        case.client.post(url, json=body | {"job_id": "foreign-job"}).status_code == 403
    )
    assert (
        case.client.post(url, json=body | {"administrator_approved": True}).status_code
        == 422
    )
    assert case.client.post(url, json=body).status_code == 200


def test_role_source_and_presentation_principal_authority(case):
    value = generate(case)
    view = preview(case, value)
    url = PREFIX + "/authoring-jobs/" + value["job"]["job_id"]
    case.state["role"] = "viewer"
    assert case.client.get(url, params=case.query).status_code == 403
    case.state["role"] = "engineer"
    case.state["principal"] = "foreign-user"
    # Native collaborators authorized for this workspace can inspect its job.
    # They cannot borrow another principal's issued presentation.
    assert case.client.get(url, params=case.query).status_code == 200
    assert (
        case.client.post(
            PREFIX + "/presentations/close",
            json=case.query
            | {
                "surface_id": view["descriptor"]["surfaceId"],
                "presentation_id": view["binding"]["presentation_id"],
            },
        ).status_code
        == 403
    )
    case.state["principal"] = "user"
    assert case.client.get(
        url, params=case.query | {"path": "workflows/another.workflow.wflow"}
    ).status_code in {403, 409}
    assert (
        case.client.get(
            url, params=case.query | {"expected_storage_digest": "f" * 64}
        ).status_code
        == 403
    )
    assert (
        case.client.post(
            PREFIX + "/authoring-jobs",
            json=case.query
            | {
                "request_id": "author-one",
                "instruction": "Change the existing request",
            },
        ).status_code
        == 409
    )


def test_unavailable_model_can_read_saved_status_but_cannot_generate(case):
    value = generate(case)
    del case.application.__dict__["_authoring"]
    response = case.client.get(PREFIX + "/authoring-capabilities", params=case.query)
    assert response.status_code == 200 and not response.json()["available"]
    status = case.client.get(
        PREFIX + "/authoring-jobs/" + value["job"]["job_id"], params=case.query
    )
    assert (
        status.status_code == 200 and status.json()["job"]["state"] == "preview_ready"
    )
    denied = case.client.post(
        PREFIX + "/authoring-jobs",
        json=case.query | {"request_id": "unavailable", "instruction": "Create a view"},
    )
    assert denied.status_code == 503
    assert "qualified" in denied.json()["detail"]["correction"].lower()


def test_cancel_and_bounded_event_observer_do_not_replay_generation(case, monkeypatch):
    async def blocked():
        case.author.engine.release = asyncio.Event()

    case.client.portal.call(blocked)
    response = case.client.post(
        PREFIX + "/authoring-jobs",
        json=case.query
        | {"request_id": "blocked", "instruction": "Wait in the controlled model"},
    )
    assert response.status_code == 202
    job_id = response.json()["job_id"]
    monkeypatch.setattr(
        "api.routers.process_ui_authoring.AUTHORING_OBSERVER_SECONDS", 0
    )
    events = case.client.get(
        PREFIX + f"/authoring-jobs/{job_id}/events", params=case.query
    )
    assert events.status_code == 200 and "observer_expired" in events.text
    status = case.client.get(PREFIX + f"/authoring-jobs/{job_id}", params=case.query)
    assert status.json()["job"]["state"] not in {"cancelled", "failed"}
    cancelled = case.client.post(
        PREFIX + f"/authoring-jobs/{job_id}/cancel", json=case.query
    )
    assert cancelled.status_code == 200 and cancelled.json()["state"] == "cancelled"
    again = case.client.post(
        PREFIX + f"/authoring-jobs/{job_id}/cancel", json=case.query
    )
    assert again.status_code == 200 and again.json()["state"] == "cancelled"
    assert len(case.author.engine.calls) <= 1
