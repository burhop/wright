"""Versioned, producer-neutral records for workflow review traces."""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from .rivet_mcp import reject_secret_material


TraceId = Annotated[
    str,
    StringConstraints(
        min_length=1, max_length=240, pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]*$"
    ),
]
Sha256 = Annotated[str, StringConstraints(pattern=r"^[a-f0-9]{64}$")]
Reference = Annotated[str, StringConstraints(min_length=1, max_length=2000)]
Availability = Literal[
    "retained", "external", "session_only", "missing", "omitted_from_export"
]


class _TraceModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    @model_validator(mode="after")
    def reject_credentials(self):
        reject_secret_material(self.model_dump(mode="python"))
        return self


class TraceRunRecord(_TraceModel):
    schema_version: Literal[1] = 1
    workspace_id: TraceId
    run_id: TraceId
    source_kind: Literal["rivet", "canonical", "source-json", "legacy"]
    source_record_ref: Reference
    source_record_digest: Sha256
    workflow_id: TraceId
    definition_digest: Sha256 | None = None
    definition_ref: Reference | None = None
    layout_ref: Reference | None = None
    original_status: Annotated[str, StringConstraints(min_length=1, max_length=80)]
    outcome: Literal[
        "completed", "failed", "blocked", "cancelled", "interrupted", "checkpoint"
    ]
    capture_state: Literal["complete", "partial", "legacy"]
    started_at: int | None = Field(default=None, ge=0)
    ended_at: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_times(self) -> "TraceRunRecord":
        if self.ended_at is not None and self.started_at is not None:
            if self.ended_at < self.started_at:
                raise ValueError("trace run completion precedes its start")
        return self


class TraceCaptureEvent(_TraceModel):
    schema_version: Literal[1] = 1
    event_id: TraceId
    run_id: TraceId
    sequence: int = Field(ge=1)
    producer: TraceId
    producer_event_id: TraceId
    occurred_at: int = Field(ge=0)
    kind: TraceId
    payload_digest: Sha256
    payload: dict[str, Any] = Field(default_factory=dict)


class TraceOccurrence(_TraceModel):
    schema_version: Literal[1] = 1
    occurrence_id: TraceId
    run_id: TraceId
    block_id: TraceId
    attempt: int = Field(ge=1)
    parent_occurrence_id: TraceId | None = None
    iteration_path: tuple[str, ...] = Field(default_factory=tuple, max_length=32)
    state: Annotated[str, StringConstraints(min_length=1, max_length=80)]
    started_at: int | None = Field(default=None, ge=0)
    ended_at: int | None = Field(default=None, ge=0)
    input_version_ids: tuple[TraceId, ...] = Field(
        default_factory=tuple, max_length=1000
    )
    output_version_ids: tuple[TraceId, ...] = Field(
        default_factory=tuple, max_length=1000
    )
    prompt_refs: tuple[Reference, ...] = Field(default_factory=tuple, max_length=100)

    @model_validator(mode="after")
    def validate_identity(self) -> "TraceOccurrence":
        if len(set(self.input_version_ids)) != len(self.input_version_ids):
            raise ValueError("duplicate occurrence input version")
        if len(set(self.output_version_ids)) != len(self.output_version_ids):
            raise ValueError("duplicate occurrence output version")
        if self.parent_occurrence_id == self.occurrence_id:
            raise ValueError("occurrence cannot parent itself")
        return self


class TraceTraversal(_TraceModel):
    schema_version: Literal[1] = 1
    traversal_id: TraceId
    run_id: TraceId
    relationship_id: TraceId
    sequence: int = Field(ge=1)
    source_occurrence_id: TraceId
    target_occurrence_id: TraceId
    transferred_version_ids: tuple[TraceId, ...] = Field(
        default_factory=tuple, max_length=1000
    )
    outcome: Annotated[str, StringConstraints(min_length=1, max_length=80)]
    source_event_ref: Reference


class TraceRepresentation(_TraceModel):
    representation_id: TraceId
    kind: Literal["original", "preview", "display", "report", "data"]
    media_type: Annotated[str, StringConstraints(min_length=1, max_length=200)]
    format: Annotated[str, StringConstraints(min_length=1, max_length=80)]
    original_name: Annotated[str, StringConstraints(min_length=1, max_length=512)]
    availability: Availability
    digest: Sha256 | None = None
    byte_size: int | None = Field(default=None, ge=0)
    storage_ref: Reference | None = None
    external_ref: Reference | None = None

    @model_validator(mode="after")
    def validate_location(self) -> "TraceRepresentation":
        if self.availability == "retained" and (
            self.digest is None or self.byte_size is None or self.storage_ref is None
        ):
            raise ValueError(
                "retained representation requires digest, size, and storage ref"
            )
        if self.availability == "external" and self.external_ref is None:
            raise ValueError("external representation requires external ref")
        return self


class TraceArtifactVersion(_TraceModel):
    schema_version: Literal[1] = 1
    version_id: TraceId
    run_id: TraceId
    occurrence_id: TraceId
    role: Annotated[str, StringConstraints(min_length=1, max_length=120)]
    display_name: Annotated[str, StringConstraints(min_length=1, max_length=512)]
    representations: tuple[TraceRepresentation, ...] = Field(
        min_length=1, max_length=1000
    )
    upstream_version_ids: tuple[TraceId, ...] = Field(
        default_factory=tuple, max_length=1000
    )
    supersedes_version_ids: tuple[TraceId, ...] = Field(
        default_factory=tuple, max_length=1000
    )

    @model_validator(mode="after")
    def validate_versions(self) -> "TraceArtifactVersion":
        ids = [item.representation_id for item in self.representations]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate artifact representation")
        if self.version_id in self.upstream_version_ids + self.supersedes_version_ids:
            raise ValueError("artifact version cannot reference itself")
        return self


class TraceEvidenceSubject(_TraceModel):
    subject_kind: Literal[
        "run", "occurrence", "artifact_version", "requirement", "input", "approval"
    ]
    subject_id: TraceId
    revision: Annotated[str, StringConstraints(min_length=1, max_length=200)] | None = (
        None
    )
    digest: Sha256 | None = None


class TraceEvidenceRecord(_TraceModel):
    schema_version: Literal[1] = 1
    evidence_id: TraceId
    run_id: TraceId
    producer: TraceId
    producer_version: Annotated[str, StringConstraints(min_length=1, max_length=120)]
    producer_record_id: TraceId
    kind: Literal["requirement", "approval", "assumption", "decision", "validation"]
    recorded_at: int = Field(ge=0)
    subjects: tuple[TraceEvidenceSubject, ...] = Field(min_length=1, max_length=1000)
    statement: Annotated[str, StringConstraints(min_length=1, max_length=20000)]
    recorded_outcome: (
        Annotated[str, StringConstraints(min_length=1, max_length=200)] | None
    ) = None
    supporting_refs: tuple[Reference, ...] = Field(
        default_factory=tuple, max_length=1000
    )
    supersedes_id: TraceId | None = None


class TraceEvidenceLink(_TraceModel):
    schema_version: Literal[1] = 1
    link_id: TraceId
    run_id: TraceId
    relation: Literal[
        "derived_from",
        "approved_by",
        "justified_by",
        "verifies",
        "used_by",
        "produced_by",
        "display_of",
        "supersedes",
    ]
    from_ref: Reference
    to_ref: Reference
    producer: TraceId
    source_event_ref: Reference


class TraceReportRevision(_TraceModel):
    schema_version: Literal[1] = 1
    report_id: TraceId
    revision: int = Field(ge=1)
    run_id: TraceId
    capture_cursor: int = Field(ge=0)
    evidence_set_digest: Sha256
    renderer_version: Annotated[str, StringConstraints(min_length=1, max_length=120)]
    built_at: int = Field(ge=0)
    outcome: Annotated[str, StringConstraints(min_length=1, max_length=80)]
    primary_version_ids: tuple[TraceId, ...] = Field(
        default_factory=tuple, max_length=1000
    )


def trace_anchor(
    report: TraceReportRevision, subject_kind: str, subject_id: str
) -> str:
    """Return a stable future-comment anchor without embedding display text."""

    if not subject_kind or not subject_id or "/" in subject_kind or "/" in subject_id:
        raise ValueError("invalid trace anchor subject")
    return f"trace:{report.run_id}:{report.report_id}:{report.revision}:{subject_kind}:{subject_id}"


__all__ = [
    "TraceArtifactVersion",
    "TraceCaptureEvent",
    "TraceEvidenceLink",
    "TraceEvidenceRecord",
    "TraceEvidenceSubject",
    "TraceOccurrence",
    "TraceReportRevision",
    "TraceRepresentation",
    "TraceRunRecord",
    "TraceTraversal",
    "trace_anchor",
]
