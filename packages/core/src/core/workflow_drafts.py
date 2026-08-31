"""Closed immutable contracts for provisional visual workflow drafts.

These types intentionally contain no execution, release, MCP, LLM, or renderer
state. Semantic content and replaceable layout are independently digest-bound.
"""

from __future__ import annotations

import hashlib
import json
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator


Identifier = Annotated[
    str,
    StringConstraints(
        min_length=1,
        max_length=96,
        pattern=r"^[a-z0-9][a-z0-9._-]*$",
    ),
]
BoundedText = Annotated[str, StringConstraints(min_length=1, max_length=500)]
Sha256Digest = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
IdentifierTuple = Annotated[tuple[Identifier, ...], Field(max_length=64)]


class _ClosedModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Phase(_ClosedModel):
    id: Identifier
    name: BoundedText
    purpose: BoundedText
    order: Annotated[int, Field(ge=0, le=15)]
    block_ids: IdentifierTuple


class WorkflowBlock(_ClosedModel):
    id: Identifier
    title: BoundedText
    purpose: BoundedText
    role: Literal["input", "work", "review", "release"]
    phase_id: Identifier
    input_port_ids: IdentifierTuple
    output_port_ids: IdentifierTuple
    gate_ids: IdentifierTuple
    intended_artifact_ids: IdentifierTuple


class TypedPort(_ClosedModel):
    id: Identifier
    owner_block_id: Identifier
    direction: Literal["input", "output"]
    name: BoundedText
    value_type_id: Identifier
    required: bool
    cardinality: Literal["one", "many"]


class Connection(_ClosedModel):
    id: Identifier
    source_port_id: Identifier
    target_port_id: Identifier


class Gate(_ClosedModel):
    id: Identifier
    owner_block_id: Identifier
    condition: BoundedText
    proceed_target_block_id: Identifier
    revise_target_block_id: Identifier
    feedback_path_id: Identifier


class FeedbackPath(_ClosedModel):
    id: Identifier
    from_gate_id: Identifier
    to_block_id: Identifier
    reason: BoundedText


class IntendedArtifact(_ClosedModel):
    id: Identifier
    title: BoundedText
    artifact_type_id: Identifier
    description: BoundedText
    produced_by_block_id: Identifier


class WorkflowSemantic(_ClosedModel):
    title: BoundedText
    purpose: BoundedText
    phases: Annotated[tuple[Phase, ...], Field(min_length=1, max_length=16)]
    blocks: Annotated[tuple[WorkflowBlock, ...], Field(max_length=100)]
    ports: Annotated[tuple[TypedPort, ...], Field(max_length=400)]
    connections: Annotated[tuple[Connection, ...], Field(max_length=400)]
    gates: Annotated[tuple[Gate, ...], Field(max_length=100)]
    feedback_paths: Annotated[tuple[FeedbackPath, ...], Field(max_length=100)]
    intended_artifacts: Annotated[
        tuple[IntendedArtifact, ...], Field(max_length=200)
    ]


class BlockPosition(_ClosedModel):
    semantic_id: Identifier
    x: Annotated[int, Field(ge=-10_000, le=10_000)]
    y: Annotated[int, Field(ge=-10_000, le=10_000)]


class WorkflowLayout(_ClosedModel):
    schema_version: Literal["1.0.0"]
    positions: Annotated[tuple[BlockPosition, ...], Field(max_length=100)]


def canonical_json_bytes(value: BaseModel | Any) -> bytes:
    """Return the provisional contract's deterministic UTF-8 JSON bytes."""

    material = value.model_dump(mode="json") if isinstance(value, BaseModel) else value
    return json.dumps(
        material,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def canonical_sha256(value: BaseModel | Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


class WorkflowDraft(_ClosedModel):
    document_kind: Literal["workflow-draft"]
    schema_version: Literal["1.0.0-draft.1"]
    draft_id: Identifier
    revision: Annotated[int, Field(ge=1)]
    semantic_sha256: Sha256Digest
    layout_sha256: Sha256Digest
    semantic: WorkflowSemantic
    layout: WorkflowLayout

    @model_validator(mode="after")
    def verify_canonical_digests(self) -> "WorkflowDraft":
        if canonical_sha256(self.semantic) != self.semantic_sha256:
            raise ValueError("semantic_sha256 does not match canonical semantic content")
        if canonical_sha256(self.layout) != self.layout_sha256:
            raise ValueError("layout_sha256 does not match canonical layout content")
        return self


__all__ = [
    "BlockPosition",
    "Connection",
    "FeedbackPath",
    "Gate",
    "IntendedArtifact",
    "Phase",
    "TypedPort",
    "WorkflowBlock",
    "WorkflowDraft",
    "WorkflowLayout",
    "WorkflowSemantic",
    "canonical_json_bytes",
    "canonical_sha256",
]
