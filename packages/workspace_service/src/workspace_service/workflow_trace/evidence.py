"""Strict producer-envelope ingestion; no engineering interpretation occurs here."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from core.workflow_trace import TraceEvidenceRecord, TraceEvidenceSubject


SUPPORTED_SCHEMA_VERSION = 1


def ingest_external_evidence(value: Mapping[str, Any]) -> TraceEvidenceRecord:
    if value.get("schema_version") != SUPPORTED_SCHEMA_VERSION:
        raise ValueError("unsupported workflow trace evidence schema")
    subjects = tuple(
        TraceEvidenceSubject.model_validate(item)
        for item in value.get("subjects") or ()
    )
    return TraceEvidenceRecord(
        evidence_id=str(value["evidence_id"]),
        run_id=str(value["run_id"]),
        producer=str(value["producer"]),
        producer_version=str(value["producer_version"]),
        producer_record_id=str(value["producer_record_id"]),
        kind=value["kind"],
        recorded_at=int(value["recorded_at"]),
        subjects=subjects,
        statement=str(value["statement"]),
        recorded_outcome=(
            str(value["recorded_outcome"])
            if value.get("recorded_outcome") is not None
            else None
        ),
        supporting_refs=tuple(str(item) for item in value.get("supporting_refs") or ()),
        supersedes_id=(
            str(value["supersedes_id"]) if value.get("supersedes_id") else None
        ),
    )
