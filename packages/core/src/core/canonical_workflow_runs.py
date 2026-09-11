"""Stable workflow execution records bound to exact canonical definitions."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    ValidationError,
    model_validator,
)

from .rivet_mcp import reject_secret_material
from .workflow_definitions import WorkflowDefinition


WORKFLOW_RUN_KIND = "workflow-run"
WORKFLOW_RUN_VERSION = "1.0.0"
RECOVERY_WORKFLOW_RUN_VERSION = "1.0.0-recovery.1"

Identifier = Annotated[
    str,
    StringConstraints(
        min_length=3,
        max_length=200,
        pattern=r"^[a-z0-9][a-z0-9._-]*$",
    ),
]
Sha256 = Annotated[str, StringConstraints(pattern=r"^[a-f0-9]{64}$")]
BoundedText = Annotated[str, StringConstraints(min_length=1, max_length=2000)]
Reference = Annotated[str, StringConstraints(min_length=3, max_length=1000)]
RunState = Literal[
    "idle",
    "queued",
    "running",
    "needs_input",
    "cancelling",
    "cancelled",
    "succeeded",
    "failed",
    "blocked",
    "stale",
]
StepState = Literal[
    "idle",
    "queued",
    "running",
    "needs_input",
    "cancelled",
    "succeeded",
    "failed",
    "blocked",
    "stale",
]
ActivityKind = Literal[
    "registered",
    "connected",
    "first_event",
    "first_output",
    "progress",
    "needs_input",
    "resumed",
    "cancel_requested",
    "terminal",
    "cleanup",
]
AllowedAction = Literal["inspect", "preview", "open", "download", "replace"]


class _ClosedModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class _RecoveryRunIdentity(BaseModel):
    model_config = ConfigDict(extra="allow", frozen=True)

    document_kind: Literal["workflow-run"]
    schema_version: Literal["1.0.0-recovery.1"]
    run_id: Identifier
    workflow_id: Identifier
    workflow_revision: Annotated[int, Field(ge=1)]
    semantic_sha256: Sha256


@dataclass(frozen=True, slots=True)
class RecoveryWorkflowRunEnvelope:
    run_id: str
    workflow_id: str
    workflow_revision: int
    semantic_sha256: str
    original: bytes
    envelope_sha256: str


def _unique(value: tuple[str, ...]) -> tuple[str, ...]:
    if len(value) != len(set(value)):
        raise ValueError("record identity list contains duplicates")
    return value


class CanonicalWorkflowRun(_ClosedModel):
    document_kind: Literal["workflow-run"]
    schema_version: Literal["1.0.0"]
    run_id: Identifier
    workflow_id: Identifier
    workflow_revision: Annotated[int, Field(ge=1)]
    semantic_sha256: Sha256
    created_at: Annotated[int, Field(ge=0)]
    completed_at: Annotated[int | None, Field(ge=0)]
    mode: Literal["simulated", "live"]
    state: RunState
    active_block_id: Identifier | None
    active_relationship_id: Identifier | None
    material_supplied: bool
    outputs_ready: bool
    cleanup_state: Literal["retained", "cleaned"]

    @model_validator(mode="after")
    def validate_lifecycle(self) -> "CanonicalWorkflowRun":
        reject_secret_material(self.model_dump(mode="python"))
        terminal = self.state in {
            "cancelled",
            "succeeded",
            "failed",
            "blocked",
            "stale",
        }
        if terminal != (self.completed_at is not None):
            raise ValueError("Terminal workflow run state and completion time disagree")
        if self.completed_at is not None and self.completed_at < self.created_at:
            raise ValueError("Workflow run completion precedes creation")
        if self.cleanup_state == "cleaned" and not terminal:
            raise ValueError("Only a terminal workflow run may be cleaned")
        return self


class WorkflowComponentScope(_ClosedModel):
    component_instance_id: Identifier
    component_id: Identifier
    component_version: Annotated[str, StringConstraints(min_length=1, max_length=80)]
    internal_semantic_id: Identifier


class WorkflowRunStepRecord(_ClosedModel):
    run_id: Identifier
    step_id: Identifier
    block_id: Identifier
    attempt: Annotated[int, Field(ge=1)]
    state: StepState
    started_at: Annotated[int | None, Field(ge=0)]
    completed_at: Annotated[int | None, Field(ge=0)]
    input_artifact_ids: Annotated[tuple[Identifier, ...], Field(max_length=1000)]
    output_artifact_ids: Annotated[tuple[Identifier, ...], Field(max_length=1000)]
    diagnosis_codes: Annotated[tuple[BoundedText, ...], Field(max_length=1000)]
    component_scope: WorkflowComponentScope | None

    @model_validator(mode="after")
    def validate_step(self) -> "WorkflowRunStepRecord":
        reject_secret_material(self.model_dump(mode="python"))
        _unique(self.input_artifact_ids)
        _unique(self.output_artifact_ids)
        _unique(self.diagnosis_codes)
        if self.completed_at is not None and self.started_at is None:
            raise ValueError("Completed workflow step lacks a start time")
        if (
            self.completed_at is not None
            and self.started_at is not None
            and self.completed_at < self.started_at
        ):
            raise ValueError("Workflow step completion precedes its start")
        return self


class WorkflowRunActivity(_ClosedModel):
    run_id: Identifier
    sequence: Annotated[int, Field(ge=1)]
    occurred_at: Annotated[int, Field(ge=0)]
    kind: ActivityKind
    summary: BoundedText
    evidence_reference: Reference | None

    @model_validator(mode="after")
    def validate_activity(self) -> "WorkflowRunActivity":
        reject_secret_material(self.model_dump(mode="python"))
        return self


class WorkflowArtifactRecord(_ClosedModel):
    artifact_id: Identifier
    run_id: Identifier
    step_id: Identifier
    contract_id: Identifier
    type_id: Identifier
    media_type: Annotated[str, StringConstraints(min_length=1, max_length=160)]
    digest_sha256: Sha256
    size_bytes: Annotated[int, Field(ge=0)]
    producer_block_id: Identifier
    upstream_artifact_ids: Annotated[tuple[Identifier, ...], Field(max_length=1000)]
    storage_reference: Reference
    preview_state: Literal["ready", "unavailable"]
    allowed_actions: Annotated[tuple[AllowedAction, ...], Field(max_length=5)]
    lifetime: Literal["retained", "ephemeral"]
    expires_at: Annotated[int | None, Field(ge=0)]
    cleanup_state: Literal["retained", "cleaned"]

    @model_validator(mode="after")
    def validate_artifact(self) -> "WorkflowArtifactRecord":
        reject_secret_material(self.model_dump(mode="python"))
        _unique(self.upstream_artifact_ids)
        _unique(self.allowed_actions)
        if self.artifact_id in self.upstream_artifact_ids:
            raise ValueError("Artifact cannot depend on itself")
        if self.lifetime == "ephemeral" and self.expires_at is None:
            raise ValueError("Ephemeral artifact requires an expiry")
        return self


def validate_run_subject(
    definition: WorkflowDefinition, run: CanonicalWorkflowRun
) -> None:
    if (
        run.workflow_id != definition.workflow_id
        or run.workflow_revision != definition.revision
        or run.semantic_sha256 != definition.semantic_sha256
    ):
        raise ValueError(
            "WFR-RUN-SUBJECT-MISMATCH: run does not reference the exact accepted definition"
        )
    block_ids = {block.id for block in definition.blocks}
    relationship_ids = {item.id for item in definition.relationships}
    if run.active_block_id is not None and run.active_block_id not in block_ids:
        raise ValueError("WFR-RUN-BLOCK-UNKNOWN: active block does not exist")
    if (
        run.active_relationship_id is not None
        and run.active_relationship_id not in relationship_ids
    ):
        raise ValueError(
            "WFR-RUN-RELATIONSHIP-UNKNOWN: active relationship does not exist"
        )


def validate_step_subject(
    definition: WorkflowDefinition, step: WorkflowRunStepRecord
) -> None:
    blocks = {block.id: block for block in definition.blocks}
    block = blocks.get(step.block_id)
    if block is None:
        raise ValueError("WFR-RUN-STEP-BLOCK: step block does not exist")
    scope = step.component_scope
    if scope is None:
        return
    if scope.component_instance_id != step.block_id or block.component_ref is None:
        raise ValueError(
            "WFR-RUN-COMPONENT-INSTANCE: component scope does not match the step block"
        )
    components = {component.id: component for component in definition.components}
    component = components.get(scope.component_id)
    if (
        component is None
        or block.component_ref.component_id != scope.component_id
        or component.version != scope.component_version
    ):
        raise ValueError(
            "WFR-RUN-COMPONENT-VERSION: component scope does not match the definition"
        )
    addresses = {address.semantic_id for address in component.internal_addresses}
    if scope.internal_semantic_id not in addresses:
        raise ValueError(
            "WFR-RUN-COMPONENT-ADDRESS: internal semantic address does not exist"
        )


def validate_artifact_subject(
    definition: WorkflowDefinition, artifact: WorkflowArtifactRecord
) -> None:
    contracts = {contract.id: contract for contract in definition.artifact_contracts}
    contract = contracts.get(artifact.contract_id)
    if contract is None:
        raise ValueError("WFR-RUN-ARTIFACT-CONTRACT: artifact contract does not exist")
    if artifact.producer_block_id != contract.producer_block_id:
        raise ValueError(
            "WFR-RUN-ARTIFACT-PRODUCER: artifact producer does not match its contract"
        )
    if (
        artifact.type_id != contract.type_id
        or artifact.media_type != contract.media_type
    ):
        raise ValueError(
            "WFR-RUN-ARTIFACT-TYPE: artifact type does not match its contract"
        )
    if not set(artifact.allowed_actions).issubset(contract.allowed_actions):
        raise ValueError(
            "WFR-RUN-ARTIFACT-ACTION: artifact grants an action outside its contract"
        )


def _strict_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate key {key}")
        value[key] = item
    return value


def capture_recovery_workflow_run(original: bytes) -> RecoveryWorkflowRunEnvelope:
    """Capture a recovery run opaquely without rewriting its historical subject."""

    try:
        value = json.loads(
            original,
            object_pairs_hook=_strict_object,
            parse_constant=lambda item: (_ for _ in ()).throw(
                ValueError(f"non-finite number {item}")
            ),
        )
        reject_secret_material(value)
        identity = _RecoveryRunIdentity.model_validate(value)
    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
        ValidationError,
        ValueError,
    ) as error:
        raise ValueError(
            "Recovery workflow run identity is unsupported or invalid"
        ) from error
    return RecoveryWorkflowRunEnvelope(
        run_id=identity.run_id,
        workflow_id=identity.workflow_id,
        workflow_revision=identity.workflow_revision,
        semantic_sha256=identity.semantic_sha256,
        original=original,
        envelope_sha256=hashlib.sha256(original).hexdigest(),
    )


__all__ = [
    "WORKFLOW_RUN_KIND",
    "WORKFLOW_RUN_VERSION",
    "RECOVERY_WORKFLOW_RUN_VERSION",
    "CanonicalWorkflowRun",
    "RecoveryWorkflowRunEnvelope",
    "WorkflowArtifactRecord",
    "WorkflowComponentScope",
    "WorkflowRunActivity",
    "WorkflowRunStepRecord",
    "capture_recovery_workflow_run",
    "validate_artifact_subject",
    "validate_run_subject",
    "validate_step_subject",
]
