"""Closed transport models for the read-only process-definition API."""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field


ProcessId = Literal["product-definition-v1"]
SchemaVersion = Literal["1.0.0"]
RecoveryClass = Literal[
    "enable_or_reinstall",
    "reinstall_exact_artifact",
    "replace_validated_definition",
    "install_compatible_wright",
    "inspect_local_data_root",
]
ProcessElementId = Annotated[
    str,
    Field(pattern=r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$", min_length=3, max_length=80),
]


class ClosedProcessDefinitionModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class ProcessDefinitionPhaseResponse(ClosedProcessDefinitionModel):
    id: ProcessElementId
    title: str = Field(min_length=1, max_length=1000)
    purpose: str = Field(min_length=1, max_length=1000)
    action_ids: list[ProcessElementId] = Field(min_length=1, max_length=100)


class ProcessDefinitionActionResponse(ClosedProcessDefinitionModel):
    id: ProcessElementId
    title: str = Field(min_length=1, max_length=1000)
    purpose: str = Field(min_length=1, max_length=1000)
    input_port_ids: list[ProcessElementId] = Field(max_length=100)
    output_port_ids: list[ProcessElementId] = Field(max_length=100)
    gate_ids: list[ProcessElementId] = Field(max_length=100)
    feedback_path_ids: list[ProcessElementId] = Field(max_length=100)
    expected_artifact_ids: list[ProcessElementId] = Field(max_length=100)


class ProcessDefinitionPortResponse(ClosedProcessDefinitionModel):
    id: ProcessElementId
    name: str = Field(min_length=1, max_length=1000)
    direction: Literal["input", "output"]
    value_type: Literal[
        "customer-need",
        "requirement-set",
        "product-model",
        "review-decision",
        "release-package",
    ]
    description: str = Field(min_length=1, max_length=1000)
    owner_action_id: ProcessElementId
    source_port_id: ProcessElementId | None


class ProcessDefinitionGateResponse(ClosedProcessDefinitionModel):
    id: ProcessElementId
    title: str = Field(min_length=1, max_length=1000)
    condition: str = Field(min_length=1, max_length=1000)
    owner_action_id: ProcessElementId
    pass_target_id: ProcessElementId
    fail_target_id: ProcessElementId


class ProcessDefinitionFeedbackPathResponse(ClosedProcessDefinitionModel):
    id: ProcessElementId
    from_id: ProcessElementId
    to_id: ProcessElementId
    reason: str = Field(min_length=1, max_length=1000)


class ProcessDefinitionArtifactResponse(ClosedProcessDefinitionModel):
    id: ProcessElementId
    name: str = Field(min_length=1, max_length=1000)
    artifact_type: Literal[
        "requirements-baseline",
        "product-definition",
        "review-record",
        "released-definition-package",
    ]
    purpose: str = Field(min_length=1, max_length=1000)
    produced_by_action_id: ProcessElementId


class ProcessDefinitionResponse(ClosedProcessDefinitionModel):
    schema_ref: Literal["./process-definition.schema.json"] | None = Field(
        default=None, alias="$schema"
    )
    schema_version: SchemaVersion
    process_id: ProcessId
    revision: int = Field(ge=1)
    title: str = Field(min_length=1, max_length=1000)
    purpose: str = Field(min_length=1, max_length=1000)
    content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    phases: list[ProcessDefinitionPhaseResponse] = Field(min_length=1, max_length=20)
    actions: list[ProcessDefinitionActionResponse] = Field(min_length=1, max_length=100)
    ports: list[ProcessDefinitionPortResponse] = Field(max_length=300)
    gates: list[ProcessDefinitionGateResponse] = Field(max_length=100)
    feedback_paths: list[ProcessDefinitionFeedbackPathResponse] = Field(max_length=100)
    artifacts: list[ProcessDefinitionArtifactResponse] = Field(max_length=200)


class ProcessDefinitionEnvelopeResponse(ClosedProcessDefinitionModel):
    definition: ProcessDefinitionResponse
    source_kind: Literal["installed", "packaged_fallback"]
    source_id: Literal["process-definitions/product-definition-v1.json"]
    source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_available: Literal[True]
    etag: str = Field(pattern=r"^[0-9a-f]{64}$")
    supported_schema_versions: tuple[SchemaVersion, ...] = Field(
        min_length=1, max_length=1
    )


class ProcessDefinitionErrorCode(StrEnum):
    UNAVAILABLE = "PROCESS_DEFINITION_UNAVAILABLE"
    IDENTITY_MISMATCH = "PROCESS_DEFINITION_IDENTITY_MISMATCH"
    INVALID = "PROCESS_DEFINITION_INVALID"
    UNSUPPORTED_VERSION = "PROCESS_DEFINITION_UNSUPPORTED_VERSION"
    READ_FAILED = "PROCESS_DEFINITION_READ_FAILED"


class ProcessDefinitionErrorResponse(ClosedProcessDefinitionModel):
    error_code: ProcessDefinitionErrorCode
    message: str = Field(min_length=1, max_length=500)
    recovery_class: RecoveryClass
    trace_id: str = Field(min_length=1, max_length=200)
    supported_schema_versions: tuple[SchemaVersion, ...] | None = Field(
        default=None, min_length=1, max_length=1
    )


__all__ = [
    "ProcessDefinitionEnvelopeResponse",
    "ProcessDefinitionErrorCode",
    "ProcessDefinitionErrorResponse",
]
