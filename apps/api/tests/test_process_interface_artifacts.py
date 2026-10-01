"""Authenticated transport composes real bounded file and preparation owners."""

import asyncio
from dataclasses import replace
import hashlib
from types import SimpleNamespace

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from api.main import app
from api.routers.workspace import get_workspace_service
from api.security import SecuritySettings
from workspace_service.adapters.filesystem import LocalWorkspaceFiles
from workspace_service.executor import BoundedExecutor
from workspace_service.use_cases.files import WorkspaceFileUseCases
from packages.workspace_service.tests.test_process_preparation_service import owner
from packages.workspace_service.tests.test_process_input_readiness import (
    source,
    process,
)


PREFIX = "/api/workspace/process-interfaces"


@pytest.fixture
def artifact_case(tmp_path):
    text = source(file="original.txt")
    application = owner(tmp_path, text)
    workspace = application.workspace
    executor = BoundedExecutor()
    workspace.files = WorkspaceFileUseCases(
        application.db_path, executor, LocalWorkspaceFiles
    )
    workspace.ensure_workspace_path_safe = lambda path: path
    workspace.lifecycle = SimpleNamespace(
        get_by_session=lambda key: (
            {"workspace_id": "workspace", "local_path": str(tmp_path)}
            if key == "owned-session"
            else None
        )
    )
    workspace.process_interfaces = application
    app.dependency_overrides[get_workspace_service] = lambda: workspace
    try:
        yield SimpleNamespace(
            owner=application,
            root=tmp_path,
            query={
                "session_id": "owned-session",
                "path": process(text).source_path,
                "expected_storage_digest": process(text).source_digest,
            },
        )
    finally:
        app.dependency_overrides.pop(get_workspace_service, None)
        asyncio.run(application.close())
        asyncio.run(executor.close())


def upload(
    client, case, *, content=b"Engineering requirement", name="brief.txt", **extra
):
    return client.post(
        f"{PREFIX}/inputs/upload",
        data={**case.query, "input_id": "brief", **extra},
        files={"file": (name, content, "text/html")},
    )


def prepare(client, case, reference):
    response = client.post(
        f"{PREFIX}/inputs",
        json={
            **case.query,
            "bindings": [{"kind": "file", "input_id": "brief", "reference": reference}],
        },
    )
    assert response.status_code == 200, response.text
    return response.json()["snapshot_id"]


def read(client, case, reference, snapshot_id, **extra):
    return client.post(
        f"{PREFIX}/representations/read",
        json={
            **case.query,
            "reference": reference,
            "input_snapshot_id": snapshot_id,
            **extra,
        },
    )


def test_upload_prepare_and_read_exact_bytes_without_execution(
    sync_client, artifact_case
):
    c = artifact_case
    content = b"Exact input" * 10_000
    response = upload(sync_client, c, content=content)
    assert response.status_code == 200, response.text
    assert response.headers["cache-control"] == "no-store"
    reference = response.json()
    assert reference["media_type"] == "text/plain"
    assert reference["sha256"] == hashlib.sha256(content).hexdigest()
    assert not (c.root / "state.db").exists()
    snapshot_id = prepare(sync_client, c, reference)
    downloaded = read(sync_client, c, reference, snapshot_id)
    assert downloaded.status_code == 200, downloaded.text
    assert downloaded.content == content
    assert downloaded.headers["content-type"].startswith("text/plain")
    assert downloaded.headers["content-disposition"].startswith("attachment;")
    assert downloaded.headers["content-length"] == str(len(content))
    assert downloaded.headers["x-content-type-options"] == "nosniff"
    assert downloaded.headers["cache-control"] == "no-store"
    assert downloaded.headers["x-wright-artifact-sha256"] == reference["sha256"]
    assert not (c.root / "first.txt").exists()
    assert not (c.root / "runs").exists()


def test_uploaded_html_is_inert_download_even_with_caller_mime(
    sync_client, artifact_case
):
    response = upload(
        sync_client, artifact_case, name="brief.html", content=b"<script>1</script>"
    )
    assert response.status_code == 200
    reference = response.json()
    assert reference["media_type"] == "application/octet-stream"
    snapshot_id = prepare(sync_client, artifact_case, reference)
    downloaded = read(sync_client, artifact_case, reference, snapshot_id)
    assert downloaded.headers["content-type"] == "application/octet-stream"
    assert downloaded.headers["content-disposition"].startswith("attachment;")


@pytest.mark.parametrize("field", ["workspace_id", "principal_id", "capabilities"])
def test_upload_rejects_caller_authority_without_echo_or_publication(
    sync_client, artifact_case, field
):
    response = upload(sync_client, artifact_case, **{field: "private-must-not-echo"})
    assert response.status_code == 422
    assert "private-must-not-echo" not in response.text
    assert not (artifact_case.root / ".wright" / "process-inputs").exists()


def test_duplicate_input_field_rejects_before_publication(sync_client, artifact_case):
    body = [(key, (None, value)) for key, value in artifact_case.query.items()]
    body += [("input_id", (None, "brief")), ("input_id", (None, "other"))]
    body += [("file", ("brief.txt", b"data", "text/plain"))]
    response = sync_client.post(f"{PREFIX}/inputs/upload", files=body)
    assert response.status_code == 422
    assert not (artifact_case.root / ".wright" / "process-inputs").exists()


def test_upload_scope_and_size_are_checked_before_saving(sync_client, artifact_case):
    c = artifact_case
    assert upload(sync_client, c, session_id="foreign").status_code == 404
    assert upload(sync_client, c, expected_storage_digest="0" * 64).status_code == 409
    assert upload(sync_client, c, input_id="unknown").status_code == 403
    c.owner.limits = replace(c.owner.limits, maximum_upload_bytes=4)
    assert upload(sync_client, c, content=b"12345").status_code == 422
    assert not (c.root / ".wright" / "process-inputs").exists()


def test_representation_needs_exact_preparation_and_immutable_bytes(
    sync_client, artifact_case
):
    c = artifact_case
    reference = upload(sync_client, c).json()
    snapshot_id = prepare(sync_client, c, reference)
    for changed in (
        {**reference, "artifact_ref": "private.txt"},
        {**reference, "sha256": "0" * 64},
        {**reference, "result_id": "foreign"},
    ):
        assert read(sync_client, c, changed, snapshot_id).status_code == 403
    assert (
        read(sync_client, c, reference, snapshot_id, session_id="foreign").status_code
        == 404
    )
    assert (
        read(sync_client, c, reference, snapshot_id, run_id="other").status_code == 422
    )
    assert read(sync_client, c, reference, None).status_code == 422
    assert (
        read(
            sync_client, c, reference, snapshot_id, principal_id="private-must-not-echo"
        ).status_code
        == 422
    )
    (c.root / reference["artifact_ref"]).write_bytes(b"Changed input")
    stale = read(sync_client, c, reference, snapshot_id)
    assert stale.status_code == 409
    assert stale.json()["error_code"] == "SUBJECT_STALE"
    assert stale.headers["cache-control"] == "no-store"


def test_auth_and_origin_cover_upload_and_download(
    sync_client, artifact_case, monkeypatch
):
    monkeypatch.setattr(
        app.state,
        "security_settings",
        SecuritySettings(
            "enforced", "test-only-token", ("http://allowed.local",), "127.0.0.1"
        ),
    )
    for route in ("inputs/upload", "representations/read"):
        denied = sync_client.post(f"{PREFIX}/{route}")
        assert denied.status_code == 401
        origin = sync_client.post(
            f"{PREFIX}/{route}",
            headers={
                "Authorization": "Bearer test-only-token",
                "Origin": "http://other.local",
            },
        )
        assert origin.status_code == 403
    allowed = sync_client.post(
        f"{PREFIX}/inputs/upload",
        data={**artifact_case.query, "input_id": "brief"},
        files={"file": ("brief.txt", b"data", "text/plain")},
        headers={
            "Authorization": "Bearer test-only-token",
            "Origin": "http://allowed.local",
        },
    )
    assert allowed.status_code == 200


def test_artifact_routes_deny_viewer_before_resolving_workspace():
    from api.routers.process_interfaces import router

    probe = FastAPI()
    probe.state.security_settings = SimpleNamespace(enforced=True)

    @probe.middleware("http")
    async def identity(request: Request, call_next):
        request.state.principal_role = "viewer"
        return await call_next(request)

    def must_not_resolve():
        raise AssertionError("Denied callers cannot resolve a workspace")

    probe.dependency_overrides[get_workspace_service] = must_not_resolve
    probe.include_router(router, prefix=PREFIX)
    with TestClient(probe) as client:
        for route in ("inputs/upload", "representations/read"):
            response = client.post(f"{PREFIX}/{route}")
            assert response.status_code == 403


@pytest.mark.asyncio
async def test_bounded_request_replay_retains_the_actual_connection_lifetime():
    from api.main import ProcessInterfaceBodyLimitMiddleware

    disconnected = asyncio.Event()
    body_received = False

    async def receive():
        nonlocal body_received
        if not body_received:
            body_received = True
            return {"type": "http.request", "body": b"{}", "more_body": False}
        await disconnected.wait()
        return {"type": "http.disconnect"}

    async def downstream(scope, replay, send):
        assert await replay() == {
            "type": "http.request",
            "body": b"{}",
            "more_body": False,
        }
        waiting = asyncio.create_task(replay())
        await asyncio.sleep(0)
        assert not waiting.done(), (
            "Request-body completion must not invent a disconnect"
        )
        disconnected.set()
        assert await waiting == {"type": "http.disconnect"}

    async def send(message):
        raise AssertionError("This bounded request must not be rejected")

    await ProcessInterfaceBodyLimitMiddleware(downstream, max_body_bytes=4)(
        {"type": "http", "path": f"{PREFIX}/representations/read", "method": "POST"},
        receive,
        send,
    )
