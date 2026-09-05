from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.trace import StatusCode

from api.middleware import tracing as request_tracing
from api.middleware.tracing import TracingMiddleware
from api.routers.native_process import router
from api.security import ControlPlaneSecurityMiddleware, SecuritySettings
from core import native_tracing, tracing
from core.native_process import language_contract
from data_vault.migrations import upgrade_database
from data_vault.native_process_repository import NativeProcessRepository
from data_vault.state_store import connect_state_db
from workspace_service.native_process_service import NativeProcessService
from workspace_service.service import WorkspaceService

ROOT = Path(__file__).resolve().parents[3]
EXAMPLES = ROOT / "src/wright_engineering/static/native-processes"
BASE = "/api/native-processes"


def definition():
    return json.loads((EXAMPLES / "concept-brief.json").read_text(encoding="utf-8"))


@pytest.fixture
def service(tmp_path):
    path = tmp_path / "state.db"
    upgrade_database(path)
    with connect_state_db(path) as connection:
        for identity in ("one", "two"):
            workspace = tmp_path / identity
            workspace.mkdir()
            connection.execute(
                """INSERT INTO engineering_workspaces
                (workspace_id,session_id,local_path,created_at,updated_at) VALUES (?,?,?,1,1)""",
                (identity, "session-" + identity, str(workspace)),
            )
    workspaces = WorkspaceService(
        str(path),
        parent_dir_provider=lambda: str(tmp_path),
        protected_roots_provider=lambda: (str(tmp_path / "application"),),
    )
    return NativeProcessService(
        NativeProcessRepository(str(path)),
        workspaces.require_safe_session_workspace,
        EXAMPLES,
    )


def client_for(service, *, role="engineer", authenticated=False):
    app = FastAPI()
    app.state.native_process_service = service
    app.state.security_settings = SimpleNamespace(enforced=True)
    if authenticated:
        app.state.security_settings = SecuritySettings(
            "enforced", "native-test-token", ("http://localhost:5173",), "127.0.0.1"
        )
        app.add_middleware(ControlPlaneSecurityMiddleware)
    else:

        @app.middleware("http")
        async def identity(request: Request, call_next):
            request.state.principal_role = role
            return await call_next(request)

    app.add_middleware(TracingMiddleware)
    app.include_router(router, prefix=BASE)
    return TestClient(app)


def payload():
    return {
        "definition": definition(),
        "presentation": {},
        "request_id": "create-request",
    }


def test_real_repository_api_authoring_and_programmatic_parity(service):
    with client_for(service) as client:
        contract = client.get(BASE + "/contract", params={"session_id": "session-one"})
        assert contract.status_code == 200 and contract.json() == language_contract()
        examples = client.get(BASE + "/examples").json()["examples"]
        assert len(examples) == 3
        created = client.post(
            BASE + "?session_id=session-one",
            json=payload(),
            headers={"X-Trace-Id": "native-save-trace"},
        )
        assert created.status_code == 201, created.text
        original = created.json()
        process_id = original["definition"]["id"]
        assert service.get_document("session-one", process_id) == original
        updated_definition = definition()
        updated_definition["title"] = "Programmatic update"
        saved = service.save_document(
            "session-one",
            updated_definition,
            {"need-source": {"x": 30, "y": 60}},
            request_id="programmatic-save",
            expected_token=original["token"],
            trace_id="programmatic-trace",
        )
        received = client.get(f"{BASE}/{process_id}?session_id=session-one")
        assert received.json() == saved
        assert saved["semantic_digest"] != original["semantic_digest"]
        assert (
            client.post(BASE + "?session_id=session-one", json=payload()).json()
            == original
        )
        conflict = client.put(
            f"{BASE}/{process_id}?session_id=session-one",
            json={
                **payload(),
                "request_id": "stale-save",
                "expected_token": original["token"],
            },
        )
        assert (
            conflict.status_code == 409 and conflict.json()["code"] == "NATIVE_CONFLICT"
        )
        assert conflict.json()["trace_id"] == conflict.headers["X-Trace-Id"]
        listed = client.get(BASE + "?session_id=session-one").json()
        assert listed["documents"][0]["revision"] == 2
        assert (
            client.get(f"{BASE}/{process_id}?session_id=session-two").status_code == 404
        )
        with connect_state_db(service.repository.db_path) as connection:
            assert (
                connection.execute(
                    "SELECT trace_id FROM native_process_requests WHERE request_id='create-request'"
                ).fetchone()[0]
                == created.headers["X-Trace-Id"]
            )


@pytest.mark.parametrize(
    "mutation", ["extra", "missing", "float", "duplicate", "oversized"]
)
def test_closed_strict_request_fails_before_mutation(service, mutation):
    data = payload()
    if mutation == "extra":
        data["surprise"] = True
    elif mutation == "missing":
        del data["presentation"]
    elif mutation == "float":
        data["presentation"] = {"need-source": {"x": 1.0, "y": 0}}
    raw = json.dumps(data)
    if mutation == "duplicate":
        raw = '{"request_id":"hidden",' + raw[1:]
    elif mutation == "oversized":
        raw = " " * (1100 * 1024 + 1)
    with client_for(service) as client:
        response = client.post(
            BASE + "?session_id=session-one",
            content=raw,
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == (413 if mutation == "oversized" else 400), (
            response.text
        )
        assert response.json()["trace_id"]
    assert service.list_documents("session-one")["documents"] == []


def test_shared_validator_check_and_identity_mismatch(service):
    with client_for(service) as client:
        check = client.post(
            BASE + "/check?session_id=session-one",
            json={"definition": definition(), "bindings": {}},
        )
        assert check.status_code == 200 and check.json() == service.check(
            "session-one", definition(), {}
        )
        assert check.json()["ready"]
        bad = definition()
        bad["connections"][0]["source_port_id"] = "absent-port"
        check = client.post(
            BASE + "/check?session_id=session-one", json={"definition": bad}
        )
        assert not check.json()["structurally_valid"] and not check.json()["ready"]
        response = client.post(
            BASE + "?session_id=session-one", json={**payload(), "definition": bad}
        )
        assert response.status_code == 422
        created = client.post(BASE + "?session_id=session-one", json=payload()).json()
        response = client.put(
            BASE + "/wrong-process?session_id=session-one",
            json={
                **payload(),
                "request_id": "wrong-id",
                "expected_token": created["token"],
            },
        )
        assert response.status_code == 400


def test_permission_session_and_scope_checks(service):
    with client_for(service, role="viewer") as client:
        for path in (
            "/contract?session_id=session-one",
            "/examples",
            "?session_id=session-one",
        ):
            denied = client.get(BASE + path)
            assert (
                denied.status_code == 403 and denied.json()["code"] == "NATIVE_DENIED"
            )
    with client_for(service) as client:
        assert client.get(BASE + "/contract").status_code == 400
        assert client.get(BASE + "/contract?session_id=missing").status_code == 404
        assert client.get(BASE + "?session_id=session-one&limit=101").status_code == 400
    with client_for(service, authenticated=True) as client:
        assert client.get(BASE + "/contract?session_id=session-one").status_code == 401
        authorized = client.get(
            BASE + "/contract?session_id=session-one",
            headers={"Authorization": "Bearer native-test-token"},
        )
        assert authorized.status_code == 200


def test_internal_error_does_not_disclose_path_or_payload(service, monkeypatch):
    provider = TracerProvider()
    exporter = InMemorySpanExporter()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    tracer = provider.get_tracer("native-api-test")
    for module in (native_tracing, tracing, request_tracing):
        monkeypatch.setattr(module, "_tracer", tracer)
    sentinel = "NATIVE_API_TEST_PRIVATE_PAYLOAD"

    def fail(*args, **kwargs):
        try:
            raise ValueError("api_key=" + sentinel)
        except ValueError as cause:
            raise RuntimeError("C:/private/" + sentinel) from cause

    # Fail inside the real transaction so both repository and service wrappers
    # see the exception before the HTTP transport sanitizes its response.
    monkeypatch.setattr(service.repository, "_remember", fail)
    try:
        with client_for(service) as client:
            failed = client.post(BASE + "?session_id=session-one", json=payload())
        finished = exporter.get_finished_spans()
    finally:
        provider.shutdown()
    assert failed.status_code == 500
    assert failed.json()["code"] == "NATIVE_INTERNAL"
    assert "private" not in failed.text and sentinel not in failed.text
    native_spans = [s for s in finished if s.name == "native.document.save"]
    assert len(native_spans) == 2
    for span in native_spans:
        assert span.status.status_code == StatusCode.ERROR
        assert span.attributes["error.type"] == "RuntimeError"
        assert span.status.description is None
        assert not span.events
    assert all(sentinel not in span.to_json() for span in finished)
    request_span = next(s for s in finished if "http.method" in s.attributes)
    assert all(
        s.context.trace_id == request_span.context.trace_id for s in native_spans
    )
    assert service.list_documents("session-one")["documents"] == []


@pytest.mark.parametrize("error_kind", ["service", "repository"])
def test_domain_error_response_uses_public_message_not_exception_text(
    service, monkeypatch, error_kind
):
    from data_vault.native_process_repository import NativeRepositoryError
    from workspace_service.native_process_service import NativeServiceError

    public_message = "Reopen the current process."
    error = (
        NativeServiceError("NATIVE_CONFLICT", public_message, "Reload and retry.")
        if error_kind == "service"
        else NativeRepositoryError("NATIVE_CONFLICT", public_message)
    )
    # Internal exception diagnostics may evolve without becoming an HTTP field.
    error.args = ("C:/private/internal-diagnostic",)

    def fail(*args, **kwargs):
        raise error

    monkeypatch.setattr(service, "list_documents", fail)
    with client_for(service) as client:
        response = client.get(BASE + "?session_id=session-one")
    assert response.status_code == 409
    assert response.json()["message"] == public_message
    assert "private" not in response.text
    assert response.json()["code"] == "NATIVE_CONFLICT"
    assert response.json()["findings"] == []
    assert response.json()["recovery"]


def test_file_preflight_never_accepts_unavailable_input_or_caller_asserted_tool_binding(
    service,
):
    data = definition()
    data.update(
        steps=[
            {
                "id": "read-file",
                "title": "Read input",
                "operation": "artifact.input@1",
                "config": {"path": "missing.txt"},
            }
        ],
        ports=[],
        connections=[],
        outputs=[],
    )
    check = service.check("session-one", data, {})
    assert any(f["code"] == "ARTIFACT_UNAVAILABLE" for f in check["findings"])
    data["steps"][0].update(operation="mcp.call@1", config={})
    assert not service.check(
        "session-one", data, {"read-file": {"server_id": "caller-asserted"}}
    )["ready"]
