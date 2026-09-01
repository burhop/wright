from __future__ import annotations

import hashlib
import json
from types import SimpleNamespace

import pytest

from api.main import WorkflowSourceBodyLimitMiddleware, app
from api.routers.workspace import get_workspace_service
from workspace_service.workflow_sources import (
    WORKFLOW_SOURCE_MAX_BYTES,
    WorkflowSourceConflictError,
    WorkflowSourceStorageError,
)


SOURCE_PATH = "workflows/mounting-bracket.workflow.wflow"


def _document(source: str, storage_revision: int, definition_revision: int = 2):
    encoded = source.encode("utf-8")
    return SimpleNamespace(
        path=SOURCE_PATH,
        storage_revision=storage_revision,
        storage_digest=hashlib.sha256(encoded).hexdigest(),
        definition_revision=definition_revision,
        size_bytes=len(encoded),
        source=source,
    )


class _WorkflowSources:
    def __init__(self):
        self.current = None

    async def create(
        self,
        workspace_dir: str,
        path: str,
        source: str,
    ):
        assert workspace_dir == "/tmp/workspace-1"
        assert path == SOURCE_PATH
        self.current = _document(source, 1, 1)
        return self.current

    async def read(self, workspace_dir: str, path: str):
        assert (workspace_dir, path) == ("/tmp/workspace-1", SOURCE_PATH)
        if self.current is None:
            raise FileNotFoundError(path)
        return self.current

    async def update(
        self,
        workspace_dir: str,
        path: str,
        *,
        expected_storage_revision: int,
        expected_storage_digest: str,
        semantic_change_validated: bool,
        source: str,
    ):
        assert (workspace_dir, path) == ("/tmp/workspace-1", SOURCE_PATH)
        if (
            self.current is None
            or expected_storage_revision != self.current.storage_revision
            or expected_storage_digest != self.current.storage_digest
        ):
            current = self.current or _document("missing", 1)
            raise WorkflowSourceConflictError(
                current.storage_revision, current.storage_digest
            )
        self.current = _document(
            source,
            self.current.storage_revision + 1,
            self.current.definition_revision + int(semantic_change_validated),
        )
        return self.current


class _Service:
    def __init__(self):
        self.workflow_sources = _WorkflowSources()
        self.session_lookups = 0

        def get_by_session(session_id):
            self.session_lookups += 1
            return (
                {
                    "workspace_id": "workspace-1",
                    "session_id": session_id,
                    "local_path": "/tmp/workspace-1",
                }
                if session_id == "session-1"
                else None
            )

        self.lifecycle = SimpleNamespace(
            get_by_session=get_by_session
        )

    async def resolve_workspace_dir(self, session_id: str, engine) -> str:
        raise AssertionError("workflow-source routes must not perform fallback lookup")

    def ensure_workspace_path_safe(self, local_path: str) -> str:
        assert local_path == "/tmp/workspace-1"
        return local_path


def test_workflow_source_create_read_and_cas_update_api(sync_client):
    service = _Service()
    app.dependency_overrides[get_workspace_service] = lambda: service
    try:
        created = sync_client.post(
            "/api/workspace/workflow-sources",
            json={
                "session_id": "session-1",
                "path": SOURCE_PATH,
                "source": "workflow bracket\nend\n",
            },
        )
        read = sync_client.get(
            "/api/workspace/workflow-sources",
            params={"session_id": "session-1", "path": SOURCE_PATH},
        )
        current = created.json()
        updated = sync_client.put(
            "/api/workspace/workflow-sources",
            json={
                "session_id": "session-1",
                "path": SOURCE_PATH,
                "source": "workflow bracket\n  name: revised\nend\n",
                "expected_storage_revision": current["storage_revision"],
                "expected_storage_digest": current["storage_digest"],
                "semantic_change_validated": True,
            },
        )
    finally:
        app.dependency_overrides.pop(get_workspace_service, None)

    assert created.status_code == 201
    assert created.headers["cache-control"] == "no-store"
    assert read.status_code == 200
    assert read.headers["cache-control"] == "no-store"
    assert read.json() == created.json()
    assert updated.status_code == 200
    assert updated.headers["cache-control"] == "no-store"
    assert updated.json()["workspace_id"] == "workspace-1"
    assert updated.json()["path"] == SOURCE_PATH
    assert updated.json()["storage_revision"] == 2
    assert created.json()["definition_revision"] == 1
    assert updated.json()["definition_revision"] == 2
    assert updated.json()["metadata_authority"] == "wright_host"
    assert updated.json()["source"].startswith("workflow bracket")
    assert updated.json()["size_bytes"] == len(updated.json()["source"].encode("utf-8"))
    assert service.session_lookups == 3


def test_workflow_source_scope_snapshots_one_exact_binding_without_fallback(
    sync_client,
):
    service = _Service()
    app.dependency_overrides[get_workspace_service] = lambda: service
    try:
        response = sync_client.post(
            "/api/workspace/workflow-sources",
            json={
                "session_id": "session-1",
                "path": SOURCE_PATH,
                "source": "source",
            },
        )
    finally:
        app.dependency_overrides.pop(get_workspace_service, None)

    assert response.status_code == 201
    assert service.session_lookups == 1


def test_workflow_source_scope_maps_path_resolution_oserror_to_safe_503(sync_client):
    service = _Service()

    def fail_path_resolution(_local_path: str) -> str:
        raise OSError(r"access denied C:\sensitive\workspace")

    service.ensure_workspace_path_safe = fail_path_resolution
    app.dependency_overrides[get_workspace_service] = lambda: service
    try:
        response = sync_client.post(
            "/api/workspace/workflow-sources",
            json={
                "session_id": "session-1",
                "path": SOURCE_PATH,
                "source": "source",
            },
        )
    finally:
        app.dependency_overrides.pop(get_workspace_service, None)

    assert response.status_code == 503
    assert response.headers["cache-control"] == "no-store"
    assert response.json()["error_code"] == "workflow_source_unavailable"
    assert "sensitive" not in response.text


def test_workflow_source_api_returns_current_cas_identity_on_conflict(sync_client):
    service = _Service()
    service.workflow_sources.current = _document("accepted", 4)
    app.dependency_overrides[get_workspace_service] = lambda: service
    try:
        response = sync_client.put(
            "/api/workspace/workflow-sources",
            json={
                "session_id": "session-1",
                "path": SOURCE_PATH,
                "source": "stale",
                "expected_storage_revision": 3,
                "expected_storage_digest": "0" * 64,
                "semantic_change_validated": True,
            },
        )
    finally:
        app.dependency_overrides.pop(get_workspace_service, None)

    assert response.status_code == 409
    assert response.headers["cache-control"] == "no-store"
    assert response.json()["error_code"] == "workflow_source_conflict"
    assert response.json()["message"] == (
        "The workflow source changed after it was read"
    )
    assert response.json()["details"] == {
        "current_storage_revision": 4,
        "current_storage_digest": service.workflow_sources.current.storage_digest,
    }


def test_workflow_source_api_requires_a_registered_workspace_session(sync_client):
    service = _Service()
    app.dependency_overrides[get_workspace_service] = lambda: service
    try:
        response = sync_client.get(
            "/api/workspace/workflow-sources",
            params={"session_id": "foreign-session", "path": SOURCE_PATH},
        )
    finally:
        app.dependency_overrides.pop(get_workspace_service, None)

    assert response.status_code == 404
    assert response.headers["cache-control"] == "no-store"
    assert response.json()["message"] == "Workspace not found"


class _InvalidWorkflowSources(_WorkflowSources):
    async def create(
        self,
        workspace_dir: str,
        path: str,
        source: str,
    ):
        raise WorkflowSourceStorageError(
            "workflow_source_path_invalid",
            "Workflow source path must be workflows/<safe-slug>.workflow.wflow",
        )


def test_workflow_source_api_projects_storage_validation_without_parsing(sync_client):
    service = _Service()
    service.workflow_sources = _InvalidWorkflowSources()
    app.dependency_overrides[get_workspace_service] = lambda: service
    try:
        response = sync_client.post(
            "/api/workspace/workflow-sources",
            json={
                "session_id": "session-1",
                "path": "workflows/bracket.workflow.json",
                "source": "this syntax is opaque to storage",
            },
        )
    finally:
        app.dependency_overrides.pop(get_workspace_service, None)

    assert response.status_code == 400
    assert response.headers["cache-control"] == "no-store"
    assert response.json()["error_code"] == "workflow_source_path_invalid"


def test_workflow_source_api_rejects_client_assigned_definition_revision(sync_client):
    service = _Service()
    app.dependency_overrides[get_workspace_service] = lambda: service
    try:
        response = sync_client.post(
            "/api/workspace/workflow-sources",
            json={
                "session_id": "session-1",
                "path": SOURCE_PATH,
                "source": "opaque source",
                "definition_revision": 9,
            },
        )
    finally:
        app.dependency_overrides.pop(get_workspace_service, None)

    assert response.status_code == 422
    assert response.headers["cache-control"] == "no-store"
    assert response.json()["error_code"] == "VALIDATION_ERROR"


def test_workflow_source_api_requires_semantic_change_validation(sync_client):
    service = _Service()
    service.workflow_sources.current = _document("accepted", 1, 1)
    app.dependency_overrides[get_workspace_service] = lambda: service
    try:
        response = sync_client.put(
            "/api/workspace/workflow-sources",
            json={
                "session_id": "session-1",
                "path": SOURCE_PATH,
                "source": "changed",
                "expected_storage_revision": 1,
                "expected_storage_digest": service.workflow_sources.current.storage_digest,
            },
        )
    finally:
        app.dependency_overrides.pop(get_workspace_service, None)

    assert response.status_code == 422
    assert response.headers["cache-control"] == "no-store"
    assert response.json()["error_code"] == "VALIDATION_ERROR"


def test_workflow_source_api_rejects_coerced_semantic_change_indication(sync_client):
    service = _Service()
    service.workflow_sources.current = _document("accepted", 1, 1)
    app.dependency_overrides[get_workspace_service] = lambda: service
    try:
        response = sync_client.put(
            "/api/workspace/workflow-sources",
            json={
                "session_id": "session-1",
                "path": SOURCE_PATH,
                "source": "changed",
                "expected_storage_revision": 1,
                "expected_storage_digest": service.workflow_sources.current.storage_digest,
                "semantic_change_validated": 1,
            },
        )
    finally:
        app.dependency_overrides.pop(get_workspace_service, None)

    assert response.status_code == 422
    assert response.headers["cache-control"] == "no-store"


def test_workflow_source_api_bounds_utf8_source_before_storage(sync_client):
    service = _Service()
    app.dependency_overrides[get_workspace_service] = lambda: service
    try:
        response = sync_client.post(
            "/api/workspace/workflow-sources",
            json={
                "session_id": "session-1",
                "path": SOURCE_PATH,
                "source": "😀" * (WORKFLOW_SOURCE_MAX_BYTES // 4 + 1),
            },
        )
    finally:
        app.dependency_overrides.pop(get_workspace_service, None)

    assert response.status_code == 422
    assert response.headers["cache-control"] == "no-store"
    assert response.json()["error_code"] == "VALIDATION_ERROR"
    assert len(response.content) < 4096
    assert service.workflow_sources.current is None


def test_workflow_source_format_only_save_keeps_definition_revision(sync_client):
    service = _Service()
    service.workflow_sources.current = _document("accepted", 1, 4)
    app.dependency_overrides[get_workspace_service] = lambda: service
    try:
        response = sync_client.put(
            "/api/workspace/workflow-sources",
            json={
                "session_id": "session-1",
                "path": SOURCE_PATH,
                "source": "accepted\n",
                "expected_storage_revision": 1,
                "expected_storage_digest": service.workflow_sources.current.storage_digest,
                "semantic_change_validated": False,
            },
        )
    finally:
        app.dependency_overrides.pop(get_workspace_service, None)

    assert response.status_code == 200
    assert response.json()["storage_revision"] == 2
    assert response.json()["definition_revision"] == 4


@pytest.mark.asyncio
async def test_workflow_source_transport_caps_chunked_body_before_downstream():
    downstream_called = False

    async def downstream(scope, receive, send):
        nonlocal downstream_called
        downstream_called = True

    middleware = WorkflowSourceBodyLimitMiddleware(downstream, max_body_bytes=8)
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/api/workspace/workflow-sources",
        "headers": [],
        "state": {"trace_id": "trace-body-limit"},
    }
    incoming = iter(
        [
            {"type": "http.request", "body": b"12345", "more_body": True},
            {"type": "http.request", "body": b"6789", "more_body": False},
        ]
    )
    sent = []

    async def receive():
        return next(incoming)

    async def send(message):
        sent.append(message)

    await middleware(scope, receive, send)

    assert not downstream_called
    start = next(message for message in sent if message["type"] == "http.response.start")
    assert start["status"] == 413
    headers = dict(start["headers"])
    assert headers[b"cache-control"] == b"no-store"
    body = next(message["body"] for message in sent if message["type"] == "http.response.body")
    assert json.loads(body)["error_code"] == "workflow_source_request_too_large"


def test_workflow_source_transport_rejects_oversized_declared_body(sync_client):
    response = sync_client.post(
        "/api/workspace/workflow-sources",
        content=b"{}",
        headers={
            "content-type": "application/json",
            "content-length": "999999999",
        },
    )

    assert response.status_code == 413
    assert response.headers["cache-control"] == "no-store"
    assert response.json()["error_code"] == "workflow_source_request_too_large"
    assert response.json()["trace_id"] != "unknown"


def test_workflow_source_api_bounds_session_identifier(sync_client):
    service = _Service()
    app.dependency_overrides[get_workspace_service] = lambda: service
    try:
        response = sync_client.post(
            "/api/workspace/workflow-sources",
            json={
                "session_id": "s" * 257,
                "path": SOURCE_PATH,
                "source": "source",
            },
        )
    finally:
        app.dependency_overrides.pop(get_workspace_service, None)

    assert response.status_code == 422
    assert response.headers["cache-control"] == "no-store"
    assert service.workflow_sources.current is None


def test_workflow_source_validation_details_are_count_and_size_bounded(sync_client):
    service = _Service()
    payload = {
        "session_id": "session-1",
        "path": SOURCE_PATH,
        "source": "source",
        **{f"unexpected_{index}": f"secret-value-{index}" for index in range(40)},
    }
    app.dependency_overrides[get_workspace_service] = lambda: service
    try:
        response = sync_client.post(
            "/api/workspace/workflow-sources",
            json=payload,
        )
    finally:
        app.dependency_overrides.pop(get_workspace_service, None)

    assert response.status_code == 422
    assert response.headers["cache-control"] == "no-store"
    errors = response.json()["details"]["errors"]
    assert len(errors) == 17
    assert errors[-1]["type"] == "additional_validation_errors"
    assert "secret-value" not in response.text
    assert len(response.content) < 8192


class _FailingWorkflowSources(_WorkflowSources):
    def __init__(self, failure: BaseException):
        super().__init__()
        self.failure = failure

    async def create(self, workspace_dir: str, path: str, source: str):
        raise self.failure


@pytest.mark.parametrize(
    ("failure", "error_code"),
    [
        (
            WorkflowSourceStorageError(
                "workflow_source_integrity", "sensitive journal detail"
            ),
            "workflow_source_integrity",
        ),
        (OSError(r"access denied C:\sensitive\workflow"), "workflow_source_unavailable"),
    ],
)
def test_workflow_source_storage_failures_use_safe_typed_503_envelope(
    sync_client, failure, error_code
):
    service = _Service()
    service.workflow_sources = _FailingWorkflowSources(failure)
    app.dependency_overrides[get_workspace_service] = lambda: service
    try:
        response = sync_client.post(
            "/api/workspace/workflow-sources",
            json={
                "session_id": "session-1",
                "path": SOURCE_PATH,
                "source": "source",
            },
        )
    finally:
        app.dependency_overrides.pop(get_workspace_service, None)

    assert response.status_code == 503
    assert response.headers["cache-control"] == "no-store"
    assert response.json()["error_code"] == error_code
    assert response.json()["message"] == (
        "Workflow source storage is temporarily unavailable"
    )
    assert "sensitive" not in response.text
