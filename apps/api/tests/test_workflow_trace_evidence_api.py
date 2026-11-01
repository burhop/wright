from types import SimpleNamespace

import pytest
from api.routers import workspace as workspace_router
from api.schemas.workflow_trace import WorkflowTraceEvidenceIngestRequest
from core.workflow_trace import TraceRunRecord
from data_vault import WorkflowTraceRepository
from fastapi import HTTPException
from workspace_service.workflow_trace import WorkflowTraceProjection


DIGEST = "a" * 64


def service(tmp_path):
    repository = WorkflowTraceRepository(tmp_path / "state.db")
    repository.put_run(
        TraceRunRecord(
            workspace_id="workspace-1",
            run_id="run-1",
            source_kind="rivet",
            source_record_ref="run:1",
            source_record_digest=DIGEST,
            workflow_id="workflow-1",
            original_status="succeeded",
            outcome="completed",
            capture_state="complete",
        )
    )
    return SimpleNamespace(
        lifecycle=SimpleNamespace(
            get_by_session=lambda session: (
                {"workspace_id": "workspace-1"} if session == "session-1" else None
            )
        ),
        workflow_traces=WorkflowTraceProjection(repository),
    )


def envelope(evidence_id="evidence-1", producer_record_id="producer-1"):
    return {
        "schema_version": 1,
        "evidence_id": evidence_id,
        "run_id": "run-1",
        "producer": "feature-082-validator",
        "producer_version": "1.0",
        "producer_record_id": producer_record_id,
        "kind": "validation",
        "recorded_at": 10,
        "subjects": [
            {
                "subject_kind": "artifact_version",
                "subject_id": "artifact-version-2",
                "revision": "2",
                "digest": DIGEST,
            }
        ],
        "statement": "Checked the exact retained artifact revision.",
        "recorded_outcome": "pass",
    }


@pytest.mark.asyncio
async def test_ingests_exact_subject_and_lists_paginated_records(tmp_path) -> None:
    app = service(tmp_path)
    first = await workspace_router.workflow_run_trace_evidence_ingest_endpoint(
        "run-1",
        WorkflowTraceEvidenceIngestRequest(session_id="session-1", evidence=envelope()),
        app,
    )
    corrected = envelope("evidence-2", "producer-2")
    corrected["supersedes_id"] = "evidence-1"
    corrected["recorded_outcome"] = "fail"
    await workspace_router.workflow_run_trace_evidence_ingest_endpoint(
        "run-1",
        WorkflowTraceEvidenceIngestRequest(session_id="session-1", evidence=corrected),
        app,
    )
    page = await workspace_router.workflow_run_trace_evidence_list_endpoint(
        "run-1", "session-1", "", 1, app
    )
    assert first["subjects"][0]["subject_id"] == "artifact-version-2"
    assert page["records"][0]["evidence_id"] == "evidence-1"
    assert page["next_after"] == "evidence-1"


@pytest.mark.asyncio
async def test_rejects_unsupported_schema_mismatched_run_and_scope(tmp_path) -> None:
    app = service(tmp_path)
    unsupported = envelope()
    unsupported["schema_version"] = 2
    with pytest.raises(HTTPException) as invalid:
        await workspace_router.workflow_run_trace_evidence_ingest_endpoint(
            "run-1",
            WorkflowTraceEvidenceIngestRequest(
                session_id="session-1", evidence=unsupported
            ),
            app,
        )
    assert invalid.value.status_code == 422

    wrong = envelope()
    wrong["run_id"] = "run-2"
    with pytest.raises(HTTPException) as mismatch:
        await workspace_router.workflow_run_trace_evidence_ingest_endpoint(
            "run-1",
            WorkflowTraceEvidenceIngestRequest(session_id="session-1", evidence=wrong),
            app,
        )
    assert mismatch.value.status_code == 422

    with pytest.raises(HTTPException) as hidden:
        await workspace_router.workflow_run_trace_evidence_list_endpoint(
            "run-1", "other", "", 10, app
        )
    assert hidden.value.status_code == 404
