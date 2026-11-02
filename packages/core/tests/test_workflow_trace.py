import pytest
from pydantic import ValidationError

from core.workflow_trace import (
    TraceArtifactVersion,
    TraceEvidenceRecord,
    TraceEvidenceSubject,
    TraceOccurrence,
    TraceReportRevision,
    TraceRepresentation,
    TraceRunRecord,
    trace_anchor,
)


DIGEST = "a" * 64


def test_trace_records_are_strict_and_stable() -> None:
    run = TraceRunRecord(
        workspace_id="workspace-1",
        run_id="run-1",
        source_kind="rivet",
        source_record_ref="workflow-run:run-1",
        source_record_digest=DIGEST,
        workflow_id="workflow-1",
        original_status="succeeded",
        outcome="completed",
        capture_state="complete",
    )
    report = TraceReportRevision(
        report_id="report-1",
        revision=2,
        run_id=run.run_id,
        capture_cursor=12,
        evidence_set_digest=DIGEST,
        renderer_version="1.0.0",
        built_at=10,
        outcome="completed",
    )
    assert trace_anchor(report, "artifact", "version-1") == (
        "trace:run-1:report-1:2:artifact:version-1"
    )
    with pytest.raises(ValidationError):
        TraceRunRecord.model_validate({**run.model_dump(), "unknown": True})


def test_occurrence_and_artifact_versions_preserve_attempt_identity() -> None:
    first = TraceOccurrence(
        occurrence_id="occurrence-1",
        run_id="run-1",
        block_id="block-1",
        attempt=1,
        state="failed",
        output_version_ids=("version-1",),
    )
    second = first.model_copy(
        update={
            "occurrence_id": "occurrence-2",
            "attempt": 2,
            "state": "succeeded",
            "output_version_ids": ("version-2",),
        }
    )
    assert first.output_version_ids != second.output_version_ids
    artifact = TraceArtifactVersion(
        version_id="version-2",
        run_id="run-1",
        occurrence_id="occurrence-2",
        role="final",
        display_name="part.step",
        supersedes_version_ids=("version-1",),
        representations=(
            TraceRepresentation(
                representation_id="representation-2",
                kind="original",
                media_type="model/step",
                format="step",
                original_name="part.step",
                availability="retained",
                digest=DIGEST,
                byte_size=42,
                storage_ref="vault:part-v2",
            ),
        ),
    )
    assert artifact.supersedes_version_ids == ("version-1",)


def test_external_evidence_keeps_exact_subject_and_rejects_secrets() -> None:
    evidence = TraceEvidenceRecord(
        evidence_id="evidence-1",
        run_id="run-1",
        producer="validator-082",
        producer_version="2.1",
        producer_record_id="producer-record-8",
        kind="validation",
        recorded_at=12,
        subjects=(
            TraceEvidenceSubject(
                subject_kind="artifact_version",
                subject_id="version-2",
                revision="2",
                digest=DIGEST,
            ),
        ),
        statement="Producer checked the named artifact revision.",
        recorded_outcome="pass",
    )
    assert evidence.subjects[0].digest == DIGEST
    with pytest.raises(ValidationError, match="secret"):
        TraceEvidenceRecord.model_validate(
            {**evidence.model_dump(), "statement": "api_key=abc123456789"}
        )


def test_retained_representation_requires_immutable_byte_identity() -> None:
    with pytest.raises(ValidationError, match="digest, size, and storage"):
        TraceRepresentation(
            representation_id="representation-1",
            kind="original",
            media_type="model/stl",
            format="stl",
            original_name="part.stl",
            availability="retained",
        )
