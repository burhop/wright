"""Real authenticated routes own runs independently from request observers."""

import asyncio
import json
import threading
from contextlib import asynccontextmanager
from types import SimpleNamespace
from urllib.parse import urlencode

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.routers import process_interfaces as routes
from api.routers.workspace import get_workspace_service
from packages.workspace_service.tests.test_process_preparation_service import owner
from packages.workspace_service.tests.test_process_input_readiness import (
    source,
    process,
)

PREFIX = "/api/workspace/process-interfaces"


@pytest.fixture
def lifecycle_case(tmp_path, monkeypatch):
    text = source(default="Frozen requirements")
    reference = process(text)
    path = tmp_path / reference.source_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    application = owner(tmp_path, text)
    workspace = application.workspace
    workspace.process_interfaces = application
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
    entered, release = threading.Event(), threading.Event()
    calls = []

    async def generate(prompt, fmt):
        calls.append(prompt)
        entered.set()
        while not release.is_set():
            await asyncio.sleep(0.01)
        return "Actual controlled API artifact"

    @asynccontextmanager
    async def lifespan(_):
        yield
        await application.close()

    monkeypatch.setattr(app.router, "lifespan_context", lifespan)
    monkeypatch.setattr(routes, "generate_workflow_response", generate, raising=False)
    app.dependency_overrides[get_workspace_service] = lambda: workspace
    try:
        with TestClient(app) as client:
            query = {
                "session_id": "owned-session",
                "path": reference.source_path,
                "expected_storage_digest": reference.source_digest,
            }
            prepared = client.post(f"{PREFIX}/inputs", json=query)
            assert prepared.status_code == 200
            frozen = prepared.json()
            yield SimpleNamespace(
                client=client,
                owner=application,
                root=tmp_path,
                query=query,
                frozen=frozen,
                calls=calls,
                entered=entered,
                release=release,
                reference=reference,
            )
    finally:
        release.set()
        app.dependency_overrides.pop(get_workspace_service, None)


def begin(case, request_id="start-one"):
    return case.client.post(
        f"{PREFIX}/runs",
        json={
            **case.query,
            "input_snapshot_id": case.frozen["snapshot_id"],
            "expected_input_digest": case.frozen["digest"],
            "request_id": request_id,
        },
    )


def wait(case, run_id):
    from workspace_service.process_interfaces.service import ProcessScope

    return case.client.portal.call(
        case.owner.runs.wait,
        ProcessScope("local-control-plane", "workspace", frozenset({"process.read"})),
        case.reference,
        run_id,
    )


def test_start_returns_before_work_finishes_and_retry_reattaches(lifecycle_case):
    case = lifecycle_case
    response = begin(case)
    assert response.status_code == 202
    receipt = response.json()
    assert receipt["principal_id"] == "local-control-plane"
    assert response.headers["cache-control"] == "no-store"
    assert case.entered.wait(2)
    assert begin(case).json() == receipt
    active = case.client.get(f"{PREFIX}/runs/{receipt['run_id']}", params=case.query)
    assert active.status_code == 200
    assert active.json()["state"] == "running"
    case.release.set()
    assert wait(case, receipt["run_id"])["status"] == "completed"
    attached = case.client.get(f"{PREFIX}/runs/{receipt['run_id']}", params=case.query)
    assert attached.json()["state"] == "completed"
    assert len(case.calls) == 1


def test_actual_sse_disconnect_leaves_backend_running(lifecycle_case):
    case = lifecycle_case
    response = begin(case)
    assert response.status_code == 202
    run_id = response.json()["run_id"]
    assert case.entered.wait(2)

    async def disconnected_request():
        disconnect = asyncio.Event()
        request_sent = False
        bodies = []

        async def receive():
            nonlocal request_sent
            if not request_sent:
                request_sent = True
                return {"type": "http.request", "body": b"", "more_body": False}
            await disconnect.wait()
            return {"type": "http.disconnect"}

        async def send(message):
            if message["type"] == "http.response.body" and message.get("body"):
                bodies.append(message["body"])
                disconnect.set()

        path = f"{PREFIX}/runs/{run_id}/events"
        scope = {
            "type": "http",
            "asgi": {"version": "3.0", "spec_version": "2.0"},
            "http_version": "1.1",
            "method": "GET",
            "scheme": "http",
            "path": path,
            "raw_path": path.encode(),
            "root_path": "",
            "query_string": urlencode(case.query).encode(),
            "headers": [],
            "client": ("127.0.0.1", 50001),
            "server": ("127.0.0.1", 5190),
        }
        await asyncio.wait_for(app(scope, receive, send), 3)
        assert bodies and b'"cursor"' in bodies[0]
        assert case.owner.runs.is_live(run_id)

    case.client.portal.call(disconnected_request)
    case.release.set()
    assert wait(case, run_id)["status"] == "completed"
    assert len(case.calls) == 1


def test_explicit_cancel_and_terminal_event_replay_are_durable(lifecycle_case):
    case = lifecycle_case
    response = begin(case)
    assert response.status_code == 202
    run_id = response.json()["run_id"]
    assert case.entered.wait(2)
    body = {**case.query, "request_id": "cancel-one"}
    cancelled = case.client.post(f"{PREFIX}/runs/{run_id}/cancel", json=body)
    assert cancelled.status_code == 200
    assert cancelled.json()["state"] == "cancellation_requested"
    assert wait(case, run_id)["status"] == "cancelled"
    assert (
        case.client.post(f"{PREFIX}/runs/{run_id}/cancel", json=body).json()
        == cancelled.json()
    )
    stream = case.client.get(f"{PREFIX}/runs/{run_id}/events", params=case.query)
    assert stream.status_code == 200
    frame = json.loads(
        next(line[6:] for line in stream.text.splitlines() if line.startswith("data: "))
    )
    assert frame["state"] == "cancelled"
    resumed = case.client.get(
        f"{PREFIX}/runs/{run_id}/events",
        params={**case.query, "cursor": frame["cursor"]},
    )
    final = json.loads(
        next(
            line[6:] for line in resumed.text.splitlines() if line.startswith("data: ")
        )
    )
    assert final["events"] == []
    assert len(case.calls) == 1


def test_run_scope_input_identity_and_request_conflicts(lifecycle_case):
    case = lifecycle_case
    response = begin(case)
    assert response.status_code == 202
    run_id = response.json()["run_id"]
    assert case.entered.wait(2)
    foreign = case.client.get(f"{PREFIX}/runs/not-this-run", params=case.query)
    assert foreign.status_code == 403
    changed = case.client.post(
        f"{PREFIX}/runs",
        json={
            **case.query,
            "input_snapshot_id": case.frozen["snapshot_id"],
            "expected_input_digest": "0" * 64,
            "request_id": "start-one",
        },
    )
    assert changed.status_code == 409
    assert changed.json()["error_code"] == "REQUEST_CONFLICT"
    for field in ("principal_id", "capabilities", "workspace_id"):
        invalid = case.client.post(
            f"{PREFIX}/runs/{run_id}/cancel",
            json={
                **case.query,
                "request_id": "cancel-injected",
                field: "private-not-echoed",
            },
        )
        assert invalid.status_code == 422
        assert "private-not-echoed" not in invalid.text
    case.release.set()
    wait(case, run_id)


def test_reopened_api_reconciles_interruption_without_restarting(lifecycle_case):
    from workspace_service.process_interfaces.runs import ProcessRunSupervisor

    case = lifecycle_case
    response = begin(case)
    assert response.status_code == 202
    receipt = response.json()
    assert case.entered.wait(2)
    case.client.portal.call(case.owner.close)
    case.owner.__dict__["runs"] = ProcessRunSupervisor(case.owner)
    assert begin(case).json() == receipt
    attached = case.client.get(f"{PREFIX}/runs/{receipt['run_id']}", params=case.query)
    assert attached.status_code == 200
    assert attached.json()["state"] == "reconciliation_required"
    assert not case.owner.runs.is_live(receipt["run_id"])
    assert len(case.calls) == 1


def test_missing_log_returns_unknown_without_repeating_work(lifecycle_case):
    case = lifecycle_case
    response = begin(case)
    assert response.status_code == 202
    receipt = response.json()
    case.release.set()
    wait(case, receipt["run_id"])
    (case.root / receipt["run_log_path"]).unlink()
    retry = begin(case)
    assert retry.status_code == 202
    assert retry.json() == receipt
    read = case.client.get(
        f"{PREFIX}/runs/{receipt['run_id']}/events", params=case.query
    )
    assert read.status_code == 503
    assert read.json()["error_code"] == "OUTCOME_UNKNOWN"
    assert len(case.calls) == 1
