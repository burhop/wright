from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Protocol

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from httpx import Response
from tool_registry.process_definition import (
    PROCESS_ID,
    ProcessDefinitionDocument,
    ProcessDefinitionErrorCode,
    ProcessDefinitionReadError,
    ProcessDefinitionReader,
)

from api.routers.process_definition import router
from api.schemas.process_definition import ProcessDefinitionEnvelopeResponse
from api.security import ControlPlaneSecurityMiddleware, SecuritySettings


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
PACKAGED_ROOT = (
    REPOSITORY_ROOT / "src" / "wright_engineering" / "static" / "process-definitions"
)
CONTRACT_ROOT = REPOSITORY_ROOT / "specs" / "078-process-definition-view" / "contracts"
RECOVERY_FIXTURES = json.loads(
    (CONTRACT_ROOT / "recovery-fixtures.json").read_text(encoding="utf-8")
)
SAMPLE_DEFINITION = PACKAGED_ROOT / "product-definition-v1.json"


class Reader(Protocol):
    def read(self, process_id: str) -> ProcessDefinitionDocument: ...


def _document() -> ProcessDefinitionDocument:
    return ProcessDefinitionReader(
        REPOSITORY_ROOT / ".absent-process-definitions",
        PACKAGED_ROOT,
    ).read(PROCESS_ID)


class FakeReader:
    def __init__(self) -> None:
        self.document = _document()
        self.error: ProcessDefinitionReadError | None = None
        self.unexpected_error: Exception | None = None
        self.calls: list[str] = []

    def read(self, process_id: str) -> ProcessDefinitionDocument:
        self.calls.append(process_id)
        if self.unexpected_error is not None:
            raise self.unexpected_error
        if self.error is not None:
            raise self.error
        return self.document


class TrackingReader:
    def __init__(self, delegate: ProcessDefinitionReader) -> None:
        self.delegate = delegate
        self.calls: list[str] = []

    def read(self, process_id: str) -> ProcessDefinitionDocument:
        self.calls.append(process_id)
        return self.delegate.read(process_id)


def make_client(
    reader: Reader,
    *,
    enforced: bool = False,
    principal_role: str | None = None,
) -> TestClient:
    app = FastAPI()
    app.state.security_settings = SimpleNamespace(enforced=enforced)
    app.state.process_definition_reader = reader

    @app.middleware("http")
    async def test_identity(request: Request, call_next):  # type: ignore[no-untyped-def]
        request.state.trace_id = request.headers.get("X-Trace-Id", "test-trace")
        if principal_role is not None:
            request.state.principal_role = principal_role
        return await call_next(request)

    app.include_router(router, prefix="/api/process-definitions")
    return TestClient(app)


def make_authenticated_client(reader: Reader) -> TestClient:
    app = FastAPI()
    app.state.security_settings = SecuritySettings(
        "enforced",
        "process-definition-test-token",
        ("http://localhost:5173",),
        "127.0.0.1",
    )
    app.state.process_definition_reader = reader
    app.include_router(router, prefix="/api/process-definitions")
    app.add_middleware(ControlPlaneSecurityMiddleware)
    return TestClient(app)


def _fixture(fixture_id: str) -> dict[str, object]:
    return next(row for row in RECOVERY_FIXTURES["fixtures"] if row["id"] == fixture_id)


def _write(path: Path, content: bytes) -> None:
    path.mkdir(parents=True, exist_ok=True)
    (path / "product-definition-v1.json").write_bytes(content)


def _temporary_reader(
    tmp_path: Path,
    *,
    installed_content: bytes | None = None,
    packaged_content: bytes | None = None,
) -> tuple[ProcessDefinitionReader, tuple[Path, Path, Path]]:
    installed = tmp_path / "installed"
    packaged = tmp_path / "packaged"
    schema = tmp_path / "schema"
    installed.mkdir()
    packaged.mkdir()
    schema.mkdir()
    (schema / "process-definition.schema.json").write_bytes(
        (CONTRACT_ROOT / "process-definition.schema.json").read_bytes()
    )
    if installed_content is not None:
        _write(installed, installed_content)
    if packaged_content is not None:
        _write(packaged, packaged_content)
    return (
        ProcessDefinitionReader(installed, packaged, schema_root=schema),
        (installed, packaged, schema),
    )


def _source_snapshot(roots: tuple[Path, ...]) -> dict[str, tuple[bytes, int]]:
    return {
        str(path.relative_to(root.parent)): (path.read_bytes(), path.stat().st_mtime_ns)
        for root in roots
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _assert_safe_failure(
    response: Response,
    *,
    expected_status: int,
    expected_code: str,
    expected_recovery: str,
    roots: tuple[Path, ...] = (),
) -> None:
    assert response.status_code == expected_status
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-trace-id"] == "test-trace"
    body = response.json()
    expected_keys = {"error_code", "message", "recovery_class", "trace_id"}
    if expected_code == "PROCESS_DEFINITION_UNSUPPORTED_VERSION":
        expected_keys.add("supported_schema_versions")
        assert body["supported_schema_versions"] == ["1.0.0"]
    assert set(body) == expected_keys
    assert body["error_code"] == expected_code
    assert body["recovery_class"] == expected_recovery
    assert body["message"] == (
        "Process definition is not available from validated local evidence."
    )
    assert body["trace_id"] == "test-trace"
    for forbidden in [
        "customer-needs",
        "Traceback",
        "secret-token",
        "attacker-controlled",
        *(str(root) for root in roots),
    ]:
        assert forbidden not in response.text


def test_success_returns_exact_envelope_safe_source_and_trace() -> None:
    reader = FakeReader()
    client = make_client(reader)

    response = client.get(
        f"/api/process-definitions/{PROCESS_ID}",
        headers={"X-Trace-Id": "trace-process-001"},
    )

    assert response.status_code == 200
    assert response.content == reader.document.canonical_bytes
    assert response.json() == reader.document.as_dict()
    assert (
        response.json()["source_id"] == "process-definitions/product-definition-v1.json"
    )
    assert response.json()["etag"] == reader.document.etag
    assert response.headers["etag"] == f'"{reader.document.etag}"'
    assert response.headers["cache-control"] == "no-cache, private"
    assert response.headers["x-trace-id"] == "trace-process-001"
    assert reader.calls == [PROCESS_ID]


def test_exact_envelope_is_accepted_by_the_closed_response_schema() -> None:
    body = _document().as_dict()

    validated = ProcessDefinitionEnvelopeResponse.model_validate(body)

    assert validated.model_dump(mode="json", by_alias=True) == body
    with pytest.raises(ValueError):
        ProcessDefinitionEnvelopeResponse.model_validate({**body, "unexpected": True})


def test_exact_matching_etag_returns_bodyless_304() -> None:
    reader = FakeReader()
    client = make_client(reader)

    response = client.get(
        f"/api/process-definitions/{PROCESS_ID}",
        headers={"If-None-Match": f'"{reader.document.etag}"'},
    )

    assert response.status_code == 304
    assert response.content == b""
    assert response.headers["etag"] == f'"{reader.document.etag}"'
    assert response.headers["x-trace-id"] == "test-trace"


@pytest.mark.parametrize("role", ["engineer", "admin"])
def test_engineer_and_admin_roles_can_read(role: str) -> None:
    reader = FakeReader()
    response = make_client(reader, enforced=True, principal_role=role).get(
        f"/api/process-definitions/{PROCESS_ID}"
    )

    assert response.status_code == 200
    assert reader.calls == [PROCESS_ID]


def test_real_security_middleware_authenticates_before_the_reader() -> None:
    reader = FakeReader()
    client = make_authenticated_client(reader)
    path = f"/api/process-definitions/{PROCESS_ID}"

    allowed = client.get(
        path,
        headers={"Authorization": "Bearer process-definition-test-token"},
    )
    assert allowed.status_code == 200
    assert reader.calls == [PROCESS_ID]

    reader.calls.clear()
    assert client.get(path).status_code == 401
    assert (
        client.get(path, headers={"Authorization": "Bearer wrong"}).status_code == 401
    )
    assert reader.calls == []


@pytest.mark.parametrize("role", [None, "viewer"])
def test_unauthorized_roles_are_rejected_before_read_without_leak(
    role: str | None,
) -> None:
    reader = FakeReader()
    response = make_client(reader, enforced=True, principal_role=role).get(
        f"/api/process-definitions/{PROCESS_ID}"
    )

    assert response.status_code == 403
    assert reader.calls == []
    assert "process-definitions/product-definition-v1.json" not in response.text
    assert "customer-needs" not in response.text
    assert str(REPOSITORY_ROOT) not in response.text


@pytest.mark.parametrize(
    ("code", "recovery", "expected_status", "includes_versions"),
    [
        (
            ProcessDefinitionErrorCode.UNAVAILABLE,
            "enable_or_reinstall",
            404,
            False,
        ),
        (
            ProcessDefinitionErrorCode.IDENTITY_MISMATCH,
            "reinstall_exact_artifact",
            409,
            False,
        ),
        (
            ProcessDefinitionErrorCode.INVALID,
            "replace_validated_definition",
            422,
            False,
        ),
        (
            ProcessDefinitionErrorCode.UNSUPPORTED_VERSION,
            "install_compatible_wright",
            422,
            True,
        ),
        (
            ProcessDefinitionErrorCode.READ_FAILED,
            "inspect_local_data_root",
            503,
            False,
        ),
    ],
)
def test_reader_failures_have_closed_status_and_support_safe_body(
    code: ProcessDefinitionErrorCode,
    recovery: str,
    expected_status: int,
    includes_versions: bool,
) -> None:
    reader = FakeReader()
    reader.error = ProcessDefinitionReadError(code, recovery)
    response = make_client(reader).get(f"/api/process-definitions/{PROCESS_ID}")

    assert response.status_code == expected_status
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-trace-id"] == "test-trace"
    assert response.json() == {
        "error_code": code.value,
        "message": "Process definition is not available from validated local evidence.",
        "recovery_class": recovery,
        "trace_id": "test-trace",
        **({"supported_schema_versions": ["1.0.0"]} if includes_versions else {}),
    }
    assert str(REPOSITORY_ROOT) not in response.text
    assert "customer-needs" not in response.text
    assert "Traceback" not in response.text


def test_error_recovery_is_mapped_from_code_instead_of_forwarded() -> None:
    reader = FakeReader()
    reader.error = ProcessDefinitionReadError(
        ProcessDefinitionErrorCode.INVALID,
        "attacker-controlled-recovery",
    )

    response = make_client(reader).get(f"/api/process-definitions/{PROCESS_ID}")

    assert response.status_code == 422
    assert response.json()["recovery_class"] == "replace_validated_definition"
    assert "attacker-controlled-recovery" not in response.text


def test_frozen_recovery_fixture_bytes_and_digests_are_exact() -> None:
    assert RECOVERY_FIXTURES["schema_version"] == "1.0.0"
    assert RECOVERY_FIXTURES["encoding"] == "UTF-8 without BOM"
    assert [row["id"] for row in RECOVERY_FIXTURES["fixtures"]] == [
        "missing-unavailable",
        "invalid-truncated-json",
        "unsupported-version",
    ]
    for fixture in RECOVERY_FIXTURES["fixtures"]:
        exact_bytes = fixture["exact_text"].encode("utf-8")
        assert not exact_bytes.startswith(b"\xef\xbb\xbf")
        assert hashlib.sha256(exact_bytes).hexdigest() == fixture["sha256"]


@pytest.mark.parametrize(
    "fixture_id",
    ["missing-unavailable", "invalid-truncated-json", "unsupported-version"],
)
def test_frozen_recovery_fixtures_drive_real_reader_api_failures_without_mutation(
    tmp_path: Path,
    fixture_id: str,
) -> None:
    fixture = _fixture(fixture_id)
    installed_content = (
        None
        if fixture_id == "missing-unavailable"
        else str(fixture["exact_text"]).encode("utf-8")
    )
    packaged_content = (
        None if fixture_id == "missing-unavailable" else SAMPLE_DEFINITION.read_bytes()
    )
    reader, roots = _temporary_reader(
        tmp_path,
        installed_content=installed_content,
        packaged_content=packaged_content,
    )
    before = _source_snapshot(roots)

    response = make_client(reader).get(f"/api/process-definitions/{PROCESS_ID}")

    _assert_safe_failure(
        response,
        expected_status=int(fixture["expected_http_status"]),
        expected_code=str(fixture["expected_code"]),
        expected_recovery=str(fixture["expected_recovery"]),
        roots=roots,
    )
    assert str(fixture["exact_text"]) not in response.text
    assert _source_snapshot(roots) == before


def test_identity_mismatch_is_closed_and_does_not_fall_back_or_mutate(
    tmp_path: Path,
) -> None:
    stale = json.loads(SAMPLE_DEFINITION.read_text(encoding="utf-8"))
    stale["title"] = "Changed without a matching content identity"
    reader, roots = _temporary_reader(
        tmp_path,
        installed_content=json.dumps(stale, separators=(",", ":")).encode(),
        packaged_content=SAMPLE_DEFINITION.read_bytes(),
    )
    before = _source_snapshot(roots)

    response = make_client(reader).get(f"/api/process-definitions/{PROCESS_ID}")

    _assert_safe_failure(
        response,
        expected_status=409,
        expected_code="PROCESS_DEFINITION_IDENTITY_MISMATCH",
        expected_recovery="reinstall_exact_artifact",
        roots=roots,
    )
    assert "Changed without a matching content identity" not in response.text
    assert _source_snapshot(roots) == before


def test_unexpected_reader_failure_is_closed_without_exception_details() -> None:
    reader = FakeReader()
    reader.unexpected_error = RuntimeError(
        r"C:\private\definition.json https://bad.example secret-token"
    )

    response = make_client(reader).get(f"/api/process-definitions/{PROCESS_ID}")

    _assert_safe_failure(
        response,
        expected_status=503,
        expected_code="PROCESS_DEFINITION_READ_FAILED",
        expected_recovery="inspect_local_data_root",
    )
    assert "private" not in response.text
    assert "bad.example" not in response.text


def test_unknown_process_is_rejected_before_reader_without_path_construction() -> None:
    reader = FakeReader()
    client = make_client(reader)

    response = client.get("/api/process-definitions/not-the-bundled-process")

    assert response.status_code == 404
    assert reader.calls == []
    assert "not-the-bundled-process" not in response.text


@pytest.mark.parametrize(
    "unsafe_path",
    [
        "..%5Csecret",
        "C:%5Cprivate%5Cdefinition.json",
        "file:%5C%5Cprivate%5Cdefinition.json",
        "https:%2F%2Fevil.example%2Fdefinition.json",
        "%2E%2E%2Fsecret",
        "%2Fetc%2Fpasswd",
    ],
)
def test_traversal_absolute_and_url_identifiers_are_rejected_without_source_access(
    tmp_path: Path,
    unsafe_path: str,
) -> None:
    delegate, roots = _temporary_reader(
        tmp_path,
        packaged_content=SAMPLE_DEFINITION.read_bytes(),
    )
    reader = TrackingReader(delegate)
    before = _source_snapshot(roots)

    response = make_client(reader).get(f"/api/process-definitions/{unsafe_path}")

    assert response.status_code == 404
    assert reader.calls == []
    assert "customer-needs" not in response.text
    assert "private" not in response.text
    assert "evil.example" not in response.text
    assert str(tmp_path) not in response.text
    assert _source_snapshot(roots) == before


def test_authentication_precedes_unsafe_identifier_classification() -> None:
    reader = FakeReader()
    response = make_authenticated_client(reader).get(
        "/api/process-definitions/C:%5Cprivate%5Cdefinition.json"
    )

    assert response.status_code == 401
    assert reader.calls == []
    assert "private" not in response.text


def test_composition_uses_installed_and_packaged_process_definition_roots(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from api import composition

    database = tmp_path / "wright.db"
    monkeypatch.setattr(composition, "DATABASE_PATH", str(database))
    composition.process_definition_reader.cache_clear()
    try:
        reader = composition.process_definition_reader()
        assert reader.installed_root == tmp_path / "process-definitions"
        assert reader.packaged_root.name == "process-definitions"
        assert reader.packaged_root.parent.name == "static"
        assert reader.read(PROCESS_ID).source_kind == "packaged_fallback"
    finally:
        composition.process_definition_reader.cache_clear()


def test_router_contains_no_filesystem_or_execution_construction() -> None:
    source = (
        REPOSITORY_ROOT
        / "apps"
        / "api"
        / "src"
        / "api"
        / "routers"
        / "process_definition.py"
    ).read_text(encoding="utf-8")

    assert "Path(" not in source
    assert ".open(" not in source
    assert "subprocess" not in source
    assert "Mcp" not in source


@pytest.mark.parametrize("method", ["post", "put", "patch", "delete"])
def test_no_mutating_process_definition_endpoint(method: str) -> None:
    reader = FakeReader()
    client = make_client(reader)

    response = getattr(client, method)(f"/api/process-definitions/{PROCESS_ID}")

    assert response.status_code == 405
    assert reader.calls == []
