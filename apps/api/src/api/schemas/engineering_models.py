"""Bounded HTTP projections for the Engineering Models control plane."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Literal

from core.rivet_mcp import reject_secret_material
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

_FORBIDDEN_PUBLIC_KEYS = {
    "adapter_command",
    "credential",
    "credential_reference",
    "host_path",
    "process_handle",
    "runtime_command",
    "runtime_endpoint",
    "secret",
    "token",
}


def _validate_public(value: Any, *, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key).lower() in _FORBIDDEN_PUBLIC_KEYS:
                raise ValueError(f"Private model field is forbidden at {path}.{key}")
            _validate_public(item, path=f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _validate_public(item, path=f"{path}[{index}]")


class CatalogSnapshotResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    snapshot_id: str = Field(min_length=1, max_length=128)
    catalog_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    freshness: str = Field(min_length=1, max_length=32)
    offline: bool
    channel: str | None = Field(default=None, max_length=128)
    sequence: int | None = Field(default=None, ge=0)
    schema_version: str | None = Field(default=None, max_length=32)
    source_kind: str | None = Field(default=None, max_length=32)
    trust_state: str | None = Field(default=None, max_length=32)


class EngineeringModelResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]{0,95}$")
    display_name: str = Field(min_length=1, max_length=120)
    description: str = Field(max_length=4096)
    tasks: list[str] = Field(min_length=1, max_length=32)
    source: dict[str, Any]
    license: dict[str, Any]
    readiness: str = Field(min_length=1, max_length=64)
    compatibility: dict[str, Any]
    evidence: dict[str, str]
    limitations: list[dict[str, Any]] = Field(max_length=64)
    variants: list[dict[str, Any]] = Field(max_length=64)
    blockers: list[dict[str, Any]] = Field(max_length=128)
    generator: dict[str, Any] | None = None
    qualification: dict[str, Any] | None = None
    manifest_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    entry_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    snapshot: CatalogSnapshotResponse

    @model_validator(mode="after")
    def validate_boundary(self) -> "EngineeringModelResponse":
        document = self.model_dump(mode="json", exclude_none=True)
        reject_secret_material(document)
        _validate_public(document)
        if len(json.dumps(document, separators=(",", ":")).encode("utf-8")) > 64 * 1024:
            raise ValueError("Engineering model response exceeds 64 KiB")
        return self


class EngineeringModelListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    snapshot: CatalogSnapshotResponse
    models: list[EngineeringModelResponse] = Field(max_length=100)
    next_cursor: str | None = Field(default=None, max_length=4096)
    total: int = Field(ge=0, le=1000)


class ModelInstallationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    installation_id: str = Field(min_length=1, max_length=128)
    model_id: str = Field(min_length=1, max_length=128)
    package_revision: int = Field(ge=1)
    variant_id: str = Field(min_length=1, max_length=128)
    manifest_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    state: Literal[
        "installed",
        "testing",
        "ready",
        "unhealthy",
        "disabled",
        "uninstalled",
        "missing",
    ]
    active_revision: bool
    runtime_adapter_id: str = Field(min_length=1, max_length=128)
    runtime_adapter_version: str = Field(min_length=1, max_length=128)
    standard_test_evidence_id: str | None = Field(
        default=None, min_length=1, max_length=128
    )
    installed_at: datetime
    last_verified_at: datetime | None = None


class ModelInstallationListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    installations: list[ModelInstallationResponse] = Field(max_length=1000)


class ModelPlanRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    operation_kind: Literal[
        "install",
        "import",
        "update",
        "rollback",
        "export",
        "disable",
        "uninstall",
        "purge",
    ]
    model_id: str | None = Field(default=None, pattern=r"^[a-z0-9][a-z0-9._-]{0,95}$")
    variant_id: str | None = Field(default=None, pattern=r"^[a-z0-9][a-z0-9._-]{0,95}$")
    installation_id: str | None = Field(default=None, min_length=1, max_length=128)
    target_installation_id: str | None = Field(
        default=None, min_length=1, max_length=128
    )

    @model_validator(mode="after")
    def validate_operation_identity(self) -> "ModelPlanRequest":
        install = self.operation_kind in {"install", "import"}
        target_required = self.operation_kind in {"update", "rollback"}
        if install:
            if not self.model_id or not self.variant_id or self.installation_id:
                raise ValueError("Install plans require model_id and variant_id only")
            if self.target_installation_id:
                raise ValueError("Install plans cannot identify a maintenance target")
        elif (
            not self.installation_id
            or self.model_id
            or self.variant_id
            or target_required != bool(self.target_installation_id)
        ):
            raise ValueError(
                "Maintenance plans require the exact installation and only update or rollback require a target"
            )
        return self


class ModelPlanConfirmationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    plan_digest: str = Field(pattern=r"^[a-f0-9]{64}$")


class ModelEffectResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: Literal[
        "network",
        "read",
        "write",
        "cache_reuse",
        "activate",
        "deactivate",
        "export",
        "retain",
        "delete",
    ]
    description: str = Field(min_length=1, max_length=1000)
    source: str | None = Field(default=None, max_length=2048)
    safe_location: str | None = Field(default=None, max_length=256)
    exact_bytes: int | None = Field(default=None, ge=0)
    maximum_bytes: int = Field(ge=0)
    reversible: bool


class ModelBlockerResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: str = Field(min_length=1, max_length=128)
    message: str = Field(min_length=1, max_length=1000)
    recovery: str = Field(min_length=1, max_length=1000)


class ModelPlanResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"]
    plan_id: str = Field(min_length=1, max_length=128)
    plan_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    principal_id: str = Field(min_length=1, max_length=128)
    operation_kind: Literal[
        "install",
        "import",
        "update",
        "rollback",
        "export",
        "disable",
        "uninstall",
        "purge",
    ]
    model_id: str = Field(min_length=1, max_length=128)
    package_revision: int = Field(ge=1)
    variant_id: str = Field(min_length=1, max_length=128)
    snapshot_id: str = Field(min_length=1, max_length=128)
    manifest_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    effects: list[ModelEffectResponse] = Field(max_length=256)
    blockers: list[ModelBlockerResponse] = Field(max_length=128)
    requirements: dict[str, Any]
    compatibility: dict[str, Any]
    prompts: list[dict[str, Any]] = Field(max_length=32)
    runtime_requirement: dict[str, Any]
    credential_reference_present: bool = False
    references: list[dict[str, Any]] = Field(default_factory=list, max_length=1000)
    rollback: str = Field(min_length=1, max_length=2000)
    cleanup: str = Field(min_length=1, max_length=2000)
    created_at: datetime
    expires_at: datetime
    state: Literal[
        "preview", "confirmable", "blocked", "confirmed", "expired", "invalidated"
    ]

    @model_validator(mode="after")
    def validate_plan_boundary(self) -> "ModelPlanResponse":
        document = self.model_dump(mode="json", exclude_none=True)
        if len(json.dumps(document, separators=(",", ":")).encode("utf-8")) > 64 * 1024:
            raise ValueError("Engineering model plan exceeds 64 KiB")
        return self


class ModelProgressResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    completed_items: int = Field(ge=0)
    total_items: int = Field(ge=0)
    completed_bytes: int = Field(ge=0)
    maximum_bytes: int = Field(ge=0)
    message: str | None = Field(default=None, max_length=1000)


class ModelOperationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"]
    operation_id: str = Field(min_length=1, max_length=128)
    plan_id: str = Field(min_length=1, max_length=128)
    plan_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    kind: Literal[
        "acquire",
        "import",
        "verify",
        "install",
        "test",
        "enable",
        "update",
        "rollback",
        "export",
        "disable",
        "uninstall",
        "purge",
        "cleanup",
    ]
    state: Literal[
        "prepared",
        "running",
        "verifying",
        "testing",
        "activating",
        "cancelling",
        "cleaning",
        "blocked",
        "succeeded",
        "failed",
        "cancelled",
    ]
    phase: str = Field(min_length=1, max_length=128)
    progress: ModelProgressResponse
    result: dict[str, Any] | None = None
    failure: ModelBlockerResponse | None = None
    trace_id: str = Field(min_length=1, max_length=128)
    cancellation_requested_at: datetime | None = None
    cleanup_state: Literal["not_needed", "pending", "clean", "residue", "unknown"]
    created_at: datetime
    updated_at: datetime


class ModelOperationEventResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sequence: int = Field(ge=1, le=1000)
    operation: ModelOperationResponse


class ModelRuntimeEvidenceResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    evidence_id: str = Field(min_length=1, max_length=128)
    state: Literal["passed", "failed", "blocked", "error"]
    material_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    observation_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    material: dict[str, Any] = Field(default_factory=dict)
    observation: dict[str, Any] = Field(default_factory=dict)
    evidence: dict[str, Any] | None = None


class ModelRuntimeTestResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    installation_id: str = Field(min_length=1, max_length=128)
    installation_state: Literal["installed", "testing", "ready", "unhealthy"]
    adapter_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]{0,95}$")
    adapter_version: str = Field(min_length=1, max_length=128)
    evidence: list[ModelRuntimeEvidenceResponse] = Field(max_length=32)

    @model_validator(mode="after")
    def validate_boundary(self) -> "ModelRuntimeTestResponse":
        document = self.model_dump(mode="json", exclude_none=True)
        reject_secret_material(document)
        _validate_public(document)
        if len(json.dumps(document, separators=(",", ":")).encode()) > 1024 * 1024:
            raise ValueError("Engineering model evidence exceeds 1 MiB")
        return self


class ModelWorkspaceBindingRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    installation_id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
    task_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]{0,95}$")

    @field_validator("task_id")
    @classmethod
    def reject_physical_actuation(cls, value: str) -> str:
        normalized = value.replace("-", "_").replace(".", "_")
        if "physical" in normalized and "actuation" in normalized:
            raise ValueError("Physical actuation is outside the model capability gate")
        return value


class ModelWorkspaceBindingStateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    state: Literal["enabled", "disabled"]


class ModelWorkspaceBindingResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    binding_id: str = Field(min_length=1, max_length=128)
    binding_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    workspace_id: str = Field(min_length=1, max_length=128)
    installation_id: str = Field(min_length=1, max_length=128)
    task_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]{0,95}$")
    tool_name: str = Field(pattern=r"^wright_model__[a-z0-9_]+__[a-z0-9_]+$")
    policy_snapshot_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    state: Literal["enabled", "disabled", "stale", "blocked"]


class ModelUpdateCompareRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]{0,95}$")
    variant_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]{0,95}$")


class ModelUpdateComparisonResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    current_manifest_digest: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    candidate_manifest_digest: str | None = Field(
        default=None, pattern=r"^[a-f0-9]{64}$"
    )
    changed_facets: list[str] = Field(max_length=16)
    diff_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    requires_retest: bool
    requires_license_review: bool = False


class ModelMaintenanceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: Literal["disable", "uninstall", "purge", "update", "rollback"]
    target_installation_id: str | None = Field(
        default=None, pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$"
    )

    @model_validator(mode="after")
    def require_target(self) -> "ModelMaintenanceRequest":
        if self.action in {"update", "rollback"} and not self.target_installation_id:
            raise ValueError("Update and rollback require an exact target installation")
        if self.action not in {"update", "rollback"} and self.target_installation_id:
            raise ValueError("This maintenance action does not accept a target")
        return self


class ModelMaintenanceResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    installation_id: str | None = Field(default=None, max_length=128)
    state: str = Field(min_length=1, max_length=64)
    active: bool | None = None
    reclaimable_bytes: int | None = Field(default=None, ge=0)
    reclaimed_bytes: int | None = Field(default=None, ge=0)
    blockers: list[dict[str, Any]] = Field(default_factory=list, max_length=1000)
    references: list[dict[str, Any]] = Field(default_factory=list, max_length=1000)
    target_installation_id: str | None = Field(default=None, max_length=128)
    current_installation_id: str | None = Field(default=None, max_length=128)
    active_installation_id: str | None = Field(default=None, max_length=128)
    predecessor_id: str | None = Field(default=None, max_length=128)
    cached_content_reused: bool | None = None
    cleanup_state: str | None = Field(default=None, max_length=32)
    category: str | None = Field(default=None, max_length=128)
    message: str | None = Field(default=None, max_length=1000)


class ModelReferenceStateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    state: Literal["detached", "archived"]


class ModelReferenceResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    reference_id: str = Field(min_length=1, max_length=128)
    state: Literal["active", "detached", "archived"]
    kind: str | None = Field(default=None, max_length=128)
    owner_id: str | None = Field(default=None, max_length=128)


class ModelOfflineExportResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    artifact_id: str = Field(pattern=r"^export-[a-f0-9]{1,120}$")
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    size: int = Field(ge=0, le=512 * 1024 * 1024)
    filename: str | None = Field(default=None, max_length=256)


__all__ = [
    "CatalogSnapshotResponse",
    "EngineeringModelListResponse",
    "EngineeringModelResponse",
    "ModelEffectResponse",
    "ModelOperationEventResponse",
    "ModelOperationResponse",
    "ModelInstallationListResponse",
    "ModelPlanConfirmationRequest",
    "ModelPlanRequest",
    "ModelPlanResponse",
    "ModelRuntimeTestResponse",
    "ModelMaintenanceRequest",
    "ModelMaintenanceResponse",
    "ModelOfflineExportResponse",
    "ModelReferenceResponse",
    "ModelReferenceStateRequest",
    "ModelUpdateCompareRequest",
    "ModelUpdateComparisonResponse",
    "ModelWorkspaceBindingRequest",
    "ModelWorkspaceBindingResponse",
    "ModelWorkspaceBindingStateRequest",
]
