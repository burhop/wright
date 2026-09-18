"""Authenticated HTTP boundary for process-validation report operations."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from core.process_validation import Assessment, AssessmentCurrentness
from workspace_service.process_validation.reporting import (
    ReportExport,
    build_report,
)

import api.routers.workspace as workspace_router


REPOSITORY = Path(__file__).parents[3]
ASSESSMENT_PATH = (
    REPOSITORY
    / "artifacts/process-validation/structured-loop/20260916T202647Z/workspace/validation/assessment-a867edfeee654ea9a2e196ea3ff740a2.json"
)


class FakeValidationApplication:
    def __init__(self):
        assessment = Assessment.model_validate_json(ASSESSMENT_PATH.read_bytes())
        self.report = build_report(
            assessment,
            AssessmentCurrentness(
                as_of="2026-09-16T21:00:00Z",
                selected_assessment_id=assessment.id,
                selected_attempt_id=assessment.attempt_id,
                selected_subject_ids=tuple(
                    item.id for item in assessment.request.subjects
                ),
                latest_attempt_id=assessment.attempt_id,
                latest_assessment_id=assessment.id,
                is_current=True,
            ),
        )
        self.review_calls = []

    def get_result(self, assessment_id):
        if assessment_id not in {self.report.assessment.id, "reviewed"}:
            raise KeyError(assessment_id)
        return self.report

    def list_findings(self, assessment_id, *, cursor, limit):
        self.get_result(assessment_id)
        return {"assessment_id": assessment_id, "findings": [], "next_cursor": None}

    def export_result(self, assessment_id, format):
        self.get_result(assessment_id)
        if format == "csv":
            return ReportExport(
                "csv", "text/csv; charset=utf-8", "report.csv", b"status\r\npass\r\n"
            )
        raise ValueError("unsupported test format")

    def record_review(self, assessment_id, **kwargs):
        self.get_result(assessment_id)
        self.review_calls.append(kwargs)
        return self.report.assessment.model_copy(update={"id": "reviewed"})


def _client(monkeypatch, application, *, role="engineer", enforced=True):
    app = FastAPI()
    app.state.security_settings = SimpleNamespace(enforced=enforced)

    @app.middleware("http")
    async def identity(request: Request, call_next):  # type: ignore[no-untyped-def]
        request.state.principal_role = role
        request.state.principal_id = "authenticated-engineer"
        request.state.trace_id = "trace-api-review"
        return await call_next(request)

    app.dependency_overrides[workspace_router.get_workspace_service] = lambda: object()

    def application_for(session_id, _service):
        if session_id != "owned-session":
            raise KeyError("Workspace not found")
        return application

    monkeypatch.setattr(
        workspace_router, "_process_validation_application", application_for
    )
    app.include_router(workspace_router.router, prefix="/api/workspace")
    return TestClient(app)


def test_get_findings_and_export_are_workspace_scoped(monkeypatch):
    application = FakeValidationApplication()
    client = _client(monkeypatch, application)
    assessment_id = application.report.assessment.id

    response = client.get(
        f"/api/workspace/process-validations/{assessment_id}",
        params={"session_id": "owned-session"},
    )
    assert response.status_code == 200
    assert response.json()["assessment_digest"] == application.report.assessment_digest
    assert response.json()["currentness"]["is_current"] is True

    findings = client.get(
        f"/api/workspace/process-validations/{assessment_id}/findings",
        params={"session_id": "owned-session", "limit": 1},
    )
    assert findings.status_code == 200 and findings.json()["findings"] == []

    exported = client.get(
        f"/api/workspace/process-validations/{assessment_id}/export",
        params={"session_id": "owned-session", "format": "csv"},
    )
    assert exported.status_code == 200
    assert exported.headers["cache-control"] == "no-store"
    assert exported.headers["x-content-type-options"] == "nosniff"
    assert exported.text == "status\r\npass\r\n"

    foreign = client.get(
        f"/api/workspace/process-validations/{assessment_id}",
        params={"session_id": "foreign-session"},
    )
    assert foreign.status_code == 404
    assert assessment_id not in json.dumps(foreign.json())


def test_review_uses_authenticated_actor_and_rejects_client_actor(monkeypatch):
    application = FakeValidationApplication()
    client = _client(monkeypatch, application)
    assessment_id = application.report.assessment.id
    body = {
        "session_id": "owned-session",
        "requirement_id": "DEMO-001",
        "decision": "approved",
        "rationale": "Reviewed against the source requirement.",
        "evidence_refs": ["wright://workspace/evidence/review-note"],
    }
    response = client.post(
        f"/api/workspace/process-validations/{assessment_id}/reviews", json=body
    )
    assert response.status_code == 200
    assert application.review_calls[0]["actor_id"] == "authenticated-engineer"
    assert (
        application.review_calls[0]["authority_ref"] == "control-plane:trace-api-review"
    )

    forged = client.post(
        f"/api/workspace/process-validations/{assessment_id}/reviews",
        json={**body, "actor_id": "forged"},
    )
    assert forged.status_code == 422


def test_validation_routes_require_engineer_or_admin_when_auth_is_enforced(
    monkeypatch,
):
    application = FakeValidationApplication()
    client = _client(monkeypatch, application, role="viewer", enforced=True)
    response = client.get(
        f"/api/workspace/process-validations/{application.report.assessment.id}",
        params={"session_id": "owned-session"},
    )
    assert response.status_code == 403
