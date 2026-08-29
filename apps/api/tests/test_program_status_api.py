from __future__ import annotations

from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient
from tool_registry.program_status import (
    ProgramStatusDocument,
    ProgramStatusErrorCode,
    ProgramStatusPublisherState,
    ProgramStatusReadError,
)

from api.routers.program_status import router


class FakeReader:
    def __init__(self) -> None:
        self.bundle_error: ProgramStatusReadError | None = None
        self.publisher_error: ProgramStatusReadError | None = None
        self.document = ProgramStatusDocument(
            bundle_id="a" * 64,
            source_commit="b" * 40,
            generated_at="2026-08-29T02:02:46Z",
            canonical_bytes=b'{"bundle_id":"' + b"a" * 64 + b'"}',
            source_kind="installed",
        )
        self.publisher = ProgramStatusPublisherState(
            state="active",
            mode="manual",
            observed_commit="b" * 40,
            last_attempt_at="2026-08-29T02:02:46Z",
            last_success_at="2026-08-29T02:02:46Z",
            failure_code=None,
            recovery=None,
        )

    def read_bundle(self) -> ProgramStatusDocument:
        if self.bundle_error is not None:
            raise self.bundle_error
        return self.document

    def read_publisher(self) -> ProgramStatusPublisherState:
        if self.publisher_error is not None:
            raise self.publisher_error
        return self.publisher


def make_client(reader: FakeReader, *, enforced: bool = False) -> TestClient:
    app = FastAPI()
    app.state.security_settings = SimpleNamespace(enforced=enforced)
    app.state.program_status_reader = reader
    app.include_router(router, prefix="/api/program-status")
    return TestClient(app)


def test_bundle_returns_private_etag_and_exact_bytes() -> None:
    client = make_client(FakeReader())

    response = client.get("/api/program-status")

    assert response.status_code == 200
    assert response.content.startswith(b'{"bundle_id":')
    assert response.headers["etag"] == f'"{"a" * 64}"'
    assert response.headers["cache-control"] == "no-cache, private"
    assert response.headers["x-program-status-observed-at"] == "2026-08-29T02:02:46Z"


def test_matching_etag_returns_bodyless_304() -> None:
    client = make_client(FakeReader())

    response = client.get(
        "/api/program-status", headers={"If-None-Match": f'"{"a" * 64}"'}
    )

    assert response.status_code == 304
    assert response.content == b""
    assert response.headers["etag"] == f'"{"a" * 64}"'


def test_publisher_is_separate_and_no_store() -> None:
    client = make_client(FakeReader())

    response = client.get("/api/program-status/publisher")

    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert response.json()["state"] == "active"
    assert response.json()["observed_commit"] == "b" * 40


def test_typed_reader_failure_is_bounded() -> None:
    reader = FakeReader()
    reader.bundle_error = ProgramStatusReadError(
        ProgramStatusErrorCode.IDENTITY_MISMATCH,
        "republish_exact_committed_subject",
    )
    client = make_client(reader)

    response = client.get("/api/program-status")

    assert response.status_code == 409
    assert response.json() == {
        "error_code": "PROGRAM_STATUS_IDENTITY_MISMATCH",
        "message": "Program status is not available from validated local evidence.",
        "recovery_class": "republish_exact_committed_subject",
        "trace_id": "no-active-span",
    }
    assert response.headers["cache-control"] == "no-store"


def test_engineer_or_admin_policy_rejects_missing_principal_when_enforced() -> None:
    client = make_client(FakeReader(), enforced=True)

    response = client.get("/api/program-status")

    assert response.status_code == 403
