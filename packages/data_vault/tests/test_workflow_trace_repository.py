import pytest

from core.workflow_trace import (
    TraceArtifactVersion,
    TraceCaptureEvent,
    TraceEvidenceRecord,
    TraceEvidenceSubject,
    TraceOccurrence,
    TraceReportRevision,
    TraceRepresentation,
    TraceRunRecord,
)
from data_vault.workflow_trace_repository import (
    WorkflowTraceRepository,
    WorkflowTraceStorageError,
)


DIGEST = "a" * 64


def run_record() -> TraceRunRecord:
    return TraceRunRecord(
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


def test_idempotent_ingest_and_restart_recovery(tmp_path) -> None:
    path = tmp_path / "state.db"
    repository = WorkflowTraceRepository(path)
    assert repository.put_run(run_record()) is True
    assert repository.put_run(run_record()) is False
    event = TraceCaptureEvent(
        event_id="event-1",
        run_id="run-1",
        sequence=1,
        producer="runner",
        producer_event_id="source-1",
        occurred_at=1,
        kind="step-started",
        payload_digest=DIGEST,
    )
    assert repository.append_event(event) is True
    restarted = WorkflowTraceRepository(path)
    assert restarted.get_run("run-1") == run_record()
    assert restarted.append_event(event) is False


def test_distinct_attempt_artifacts_and_pagination(tmp_path) -> None:
    repository = WorkflowTraceRepository(tmp_path / "state.db")
    repository.put_run(run_record())
    for attempt in (1, 2):
        occurrence = TraceOccurrence(
            occurrence_id=f"occurrence-{attempt}",
            run_id="run-1",
            block_id="block-1",
            attempt=attempt,
            state="succeeded" if attempt == 2 else "failed",
            output_version_ids=(f"version-{attempt}",),
        )
        repository.put_occurrence(occurrence)
        repository.put_artifact_version(
            TraceArtifactVersion(
                version_id=f"version-{attempt}",
                run_id="run-1",
                occurrence_id=occurrence.occurrence_id,
                role="output",
                display_name="same.step",
                representations=(
                    TraceRepresentation(
                        representation_id=f"representation-{attempt}",
                        kind="original",
                        media_type="model/step",
                        format="step",
                        original_name="same.step",
                        availability="retained",
                        digest=("a" if attempt == 1 else "b") * 64,
                        byte_size=attempt,
                        storage_ref=f"vault:{attempt}",
                    ),
                ),
            )
        )
    assert [item.attempt for item in repository.occurrences("run-1", limit=1)] == [1]
    assert [item.attempt for item in repository.occurrences("run-1", after=1)] == [2]


def test_immutable_report_and_evidence_subject(tmp_path) -> None:
    repository = WorkflowTraceRepository(tmp_path / "state.db")
    repository.put_run(run_record())
    evidence = TraceEvidenceRecord(
        evidence_id="evidence-1",
        run_id="run-1",
        producer="validator",
        producer_version="1",
        producer_record_id="record-1",
        kind="validation",
        recorded_at=1,
        subjects=(
            TraceEvidenceSubject(
                subject_kind="artifact_version", subject_id="version-1", digest=DIGEST
            ),
        ),
        statement="Checked exact version.",
        recorded_outcome="pass",
    )
    assert repository.put_evidence(evidence)
    assert repository.evidence("run-1") == (evidence,)
    report = TraceReportRevision(
        report_id="report-1",
        revision=1,
        run_id="run-1",
        capture_cursor=1,
        evidence_set_digest=DIGEST,
        renderer_version="1",
        built_at=2,
        outcome="completed",
    )
    assert repository.put_report(report)
    assert repository.put_report(report) is False
    with pytest.raises(WorkflowTraceStorageError, match="immutable"):
        repository.put_report(report.model_copy(update={"outcome": "failed"}))


def test_event_sequence_is_transactional(tmp_path) -> None:
    repository = WorkflowTraceRepository(tmp_path / "state.db")
    repository.put_run(run_record())
    with pytest.raises(WorkflowTraceStorageError, match="contiguous"):
        repository.append_event(
            TraceCaptureEvent(
                event_id="event-2",
                run_id="run-1",
                sequence=2,
                producer="runner",
                producer_event_id="source-2",
                occurred_at=2,
                kind="step-finished",
                payload_digest=DIGEST,
            )
        )
