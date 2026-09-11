from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from api.schemas.workflow_drafts import (
    WorkflowDraftCreateRequest,
    WorkflowDraftDiagnosticResponse,
    WorkflowDraftEnvelope,
    WorkflowDraftErrorCode,
    WorkflowDraftErrorResponse,
    WorkflowDraftValidationResponse,
)


FIXTURE = (
    Path(__file__).parents[3]
    / "packages"
    / "core"
    / "tests"
    / "fixtures"
    / "workflow_drafts"
    / "representative-workflow.json"
)


def test_create_and_envelope_models_are_closed() -> None:
    request = WorkflowDraftCreateRequest(title="New workflow", purpose="Draft safely.")
    envelope = WorkflowDraftEnvelope.model_validate_json(FIXTURE.read_bytes())

    assert request.title == "New workflow"
    assert envelope.revision == 1
    with pytest.raises(ValidationError):
        WorkflowDraftCreateRequest(
            title="New workflow", purpose="Draft safely.", release=True
        )
    payload = envelope.model_dump(mode="json")
    payload["execution_target"] = "local"
    with pytest.raises(ValidationError):
        WorkflowDraftEnvelope.model_validate(payload)


def test_validation_response_contains_only_bounded_safe_diagnostics() -> None:
    diagnostic = WorkflowDraftDiagnosticResponse(
        code="CONNECTION_VALUE_TYPE_MISMATCH",
        path="semantic.connections[0]",
        affected_semantic_ids=("connection.a",),
        explanation="Connected port types must match.",
        correction="Choose ports with the same value type.",
    )
    response = WorkflowDraftValidationResponse(
        valid=False,
        semantic_sha256="a" * 64,
        layout_sha256="b" * 64,
        diagnostics=(diagnostic,),
    )

    assert response.model_dump(mode="json")["diagnostics"][0]["code"] == (
        "CONNECTION_VALUE_TYPE_MISMATCH"
    )
    with pytest.raises(ValidationError):
        WorkflowDraftDiagnosticResponse(
            code="INVALID",
            path="semantic",
            affected_semantic_ids=(),
            explanation="x" * 501,
            correction="Correct the candidate.",
        )


def test_error_transport_cannot_include_paths_or_draft_content() -> None:
    error = WorkflowDraftErrorResponse(
        error_code=WorkflowDraftErrorCode.STORAGE_FAILED,
        message="Workflow draft storage is unavailable.",
        recovery_class="retry_or_inspect_local_store",
        trace_id="trace-1",
    )

    assert set(error.model_dump(mode="json")) == {
        "error_code",
        "message",
        "recovery_class",
        "trace_id",
        "diagnostics",
    }
    with pytest.raises(ValidationError):
        WorkflowDraftErrorResponse(
            error_code=WorkflowDraftErrorCode.STORAGE_FAILED,
            message="Workflow draft storage is unavailable.",
            recovery_class="retry_or_inspect_local_store",
            trace_id="trace-1",
            local_path="D:/private/wright.sqlite3",
        )
