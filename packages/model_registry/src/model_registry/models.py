"""Immutable, bounded contracts for local engineering model packages."""

from __future__ import annotations

import hashlib
import json
import math
import re
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

_DIGEST = re.compile(r"^[a-f0-9]{64}$")
_SECRET = re.compile(
    r"(?i)(?:api[_-]?key|secret|token|password|authorization|cookie|credential)\s*[:=]"
)
MAX_RECORD_BYTES = 64 * 1024


class ModelRegistryError(ValueError):
    """Stable, non-secret model validation failure."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class FailureCategory(StrEnum):
    SOURCE_UNAVAILABLE = "source_unavailable"
    SOURCE_CHANGED = "source_changed"
    SOURCE_GATED = "source_gated"
    CREDENTIAL_MISSING = "credential_missing"
    LICENSE_UNAPPROVED = "license_unapproved"
    LICENSE_CHANGED = "license_changed"
    MANIFEST_INVALID = "manifest_invalid"
    UNSAFE_FORMAT = "unsafe_format"
    REMOTE_CODE_REQUIRED = "remote_code_required"
    PATH_UNSAFE = "path_unsafe"
    UNDECLARED_FILE = "undeclared_file"
    SIZE_EXCEEDED = "size_exceeded"
    DIGEST_MISMATCH = "digest_mismatch"
    INSUFFICIENT_DISK = "insufficient_disk"
    INCOMPATIBLE_PLATFORM = "incompatible_platform"
    INSUFFICIENT_RESOURCES = "insufficient_resources"
    RUNTIME_MISSING = "runtime_missing"
    RUNTIME_UNHEALTHY = "runtime_unhealthy"
    RUNTIME_TIMEOUT = "runtime_timeout"
    INPUT_INVALID = "input_invalid"
    OUTPUT_INVALID = "output_invalid"
    NON_FINITE_OUTPUT = "non_finite_output"
    TEST_FAILED = "test_failed"
    CANCELLED = "cancelled"
    CLEANUP_RESIDUE = "cleanup_residue"
    REFERENCE_BLOCKED = "reference_blocked"
    STALE_BINDING = "stale_binding"
    POLICY_DENIED = "policy_denied"
    EXPORT_FORBIDDEN = "export_forbidden"
    INTERNAL_ERROR = "internal_error"


def _canonical(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return _canonical(value.model_dump(mode="json", exclude_none=True))
    if isinstance(value, dict):
        return {str(key): _canonical(value[key]) for key in sorted(value, key=str)}
    if isinstance(value, (tuple, list)):
        return [_canonical(item) for item in value]
    if isinstance(value, (set, frozenset)):
        return sorted(_canonical(item) for item in value)
    if isinstance(value, StrEnum):
        return str(value)
    if isinstance(value, float) and not math.isfinite(value):
        raise ModelRegistryError("non_finite_output", "Numeric values must be finite")
    return value


def canonical_json(value: Any) -> str:
    return json.dumps(
        _canonical(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )


def canonical_digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _reject_secret_values(value: Any) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if re.search(
                r"(?i)^(?:api[_-]?key|secret|token|password|authorization|cookie|credential)$",
                str(key),
            ):
                raise ModelRegistryError(
                    "secret_forbidden", "Secret material is forbidden"
                )
            _reject_secret_values(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _reject_secret_values(item)
    elif isinstance(value, str) and _SECRET.search(value):
        raise ModelRegistryError("secret_forbidden", "Secret material is forbidden")


class FrozenModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Publisher(FrozenModel):
    name: str = Field(min_length=1, max_length=200)
    source_uri: str = Field(min_length=1, max_length=2048)


class ModelSource(FrozenModel):
    kind: Literal["wright", "hugging_face", "https", "offline"]
    uri: str = Field(min_length=1, max_length=2048)
    immutable_revision: str = Field(min_length=7, max_length=128)
    access: Literal["public", "gated", "private", "offline_only"]
    allowed_hosts: tuple[str, ...] = Field(default=(), max_length=16)


class TaskContract(FrozenModel):
    task_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]{0,95}$")
    description: str = Field(min_length=1, max_length=1000)
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    units: dict[str, Any] = Field(default_factory=dict)
    coordinate_convention: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def validate_schemas(self) -> "TaskContract":
        if self.input_schema.get("type") != "object":
            raise ModelRegistryError("input_schema_invalid", "Input schema is invalid")
        if self.output_schema.get("type") != "object":
            raise ModelRegistryError(
                "output_schema_invalid", "Output schema is invalid"
            )
        if len(self.units) > 64:
            raise ModelRegistryError("units_too_many", "Unit declarations exceed limit")
        return self


class LicenseEvidenceItem(FrozenModel):
    kind: Literal["artifact", "source_page", "publisher_statement"]
    location: str = Field(min_length=1, max_length=2048)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


class LicenseEvidence(FrozenModel):
    expression: str = Field(min_length=1, max_length=256)
    evidence: tuple[LicenseEvidenceItem, ...] = Field(min_length=1, max_length=16)
    attribution: str = Field(min_length=1, max_length=4096)
    redistribution: Literal["allowed", "prohibited", "review_required"]
    acceptance_required: bool = False


class Limitation(FrozenModel):
    limitation_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]{0,95}$")
    description: str = Field(min_length=1, max_length=1000)
    severity: Literal["information", "caution", "critical"] = "caution"


class ArtifactDeclaration(FrozenModel):
    path: str = Field(min_length=1, max_length=512)
    role: Literal[
        "model_data",
        "metadata",
        "license",
        "attribution",
        "test_input",
        "test_expected",
    ]
    media_type: str = Field(min_length=1, max_length=128)
    size: int = Field(ge=0, le=1_099_511_627_776)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_uri: str = Field(min_length=1, max_length=4096)
    redistributable: bool


class RuntimeRequirement(FrozenModel):
    adapter_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]{0,95}$")
    contract_version: str = Field(pattern=r"^[0-9]+\.[0-9]+$")
    version_specifier: str = Field(min_length=1, max_length=128)


class ResourceEnvelope(FrozenModel):
    download_bytes: int = Field(ge=0)
    installed_bytes: int = Field(ge=0)
    ram_bytes: int = Field(ge=0)
    vram_bytes: int = Field(default=0, ge=0)
    load_timeout_ms: int = Field(gt=0, le=3_600_000)
    inference_timeout_ms: int = Field(gt=0, le=3_600_000)
    max_output_bytes: int = Field(gt=0, le=16_777_216)


class ExpectedPredicate(FrozenModel):
    kind: Literal[
        "exact", "absolute_tolerance", "relative_tolerance", "range", "category"
    ]
    value: Any | None = None
    absolute_tolerance: float | None = Field(default=None, ge=0)
    relative_tolerance: float | None = Field(default=None, ge=0)
    minimum: float | None = None
    maximum: float | None = None

    @model_validator(mode="after")
    def validate_kind(self) -> "ExpectedPredicate":
        if self.kind in {"exact", "category"} and self.value is None:
            raise ModelRegistryError("predicate_invalid", "Expected value is required")
        if self.kind == "absolute_tolerance" and (
            self.value is None or self.absolute_tolerance is None
        ):
            raise ModelRegistryError(
                "predicate_invalid", "Absolute tolerance is invalid"
            )
        if self.kind == "relative_tolerance" and (
            self.value is None or self.relative_tolerance is None
        ):
            raise ModelRegistryError(
                "predicate_invalid", "Relative tolerance is invalid"
            )
        if self.kind == "range" and (self.minimum is None or self.maximum is None):
            raise ModelRegistryError("predicate_invalid", "Range is invalid")
        if self.minimum is not None and self.maximum is not None:
            if self.minimum > self.maximum:
                raise ModelRegistryError("predicate_invalid", "Range is invalid")
        _canonical(self.model_dump(mode="json"))
        return self


class VectorLimits(FrozenModel):
    load_timeout_ms: int = Field(gt=0, le=3_600_000)
    inference_timeout_ms: int = Field(gt=0, le=3_600_000)
    max_output_bytes: int = Field(gt=0, le=16_777_216)


class ModelTestVector(FrozenModel):
    schema_version: Literal["1.0"] = "1.0"
    vector_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]{0,95}$")
    version: int = Field(ge=1)
    task_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]{0,95}$")
    input_schema_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    output_schema_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    deterministic_seed: int | str
    units: dict[str, Any] = Field(default_factory=dict)
    coordinate_convention: str | None = Field(default=None, max_length=500)
    input: Any
    expected: ExpectedPredicate
    limitations_exercised: tuple[str, ...] = Field(min_length=1, max_length=64)
    limits: VectorLimits
    mandatory: bool

    @model_validator(mode="after")
    def validate_vector(self) -> "ModelTestVector":
        if isinstance(self.deterministic_seed, str) and not (
            1 <= len(self.deterministic_seed) <= 128
        ):
            raise ModelRegistryError("seed_invalid", "Deterministic seed is invalid")
        if isinstance(self.deterministic_seed, int) and self.deterministic_seed < 0:
            raise ModelRegistryError("seed_invalid", "Deterministic seed is invalid")
        if len(set(self.limitations_exercised)) != len(self.limitations_exercised):
            raise ModelRegistryError(
                "test_limitation_duplicate", "Test limitations must be unique"
            )
        return self


class ModelVariant(FrozenModel):
    variant_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]{0,95}$")
    format: str = Field(min_length=1, max_length=64)
    precision: str = Field(min_length=1, max_length=32)
    platforms: tuple[str, ...] = Field(min_length=1, max_length=32)
    accelerator: Literal["none", "cpu", "cuda", "directml", "coreml"]
    runtime: RuntimeRequirement
    resources: ResourceEnvelope
    artifacts: tuple[ArtifactDeclaration, ...] = Field(min_length=1, max_length=1000)
    test_vectors: tuple[ModelTestVector, ...] = Field(min_length=1, max_length=32)


class ModelPackage(FrozenModel):
    schema_version: Literal["1.0"] = "1.0"
    model_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]{0,95}$")
    package_revision: int = Field(ge=1)
    display_name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=4096)
    publisher: Publisher
    source: ModelSource
    tasks: tuple[TaskContract, ...] = Field(min_length=1, max_length=32)
    license: LicenseEvidence
    limitations: tuple[Limitation, ...] = Field(min_length=1, max_length=64)
    remote_code_policy: Literal["forbidden"]
    review_state: Literal[
        "approved", "needs_review", "blocked", "deprecated", "withdrawn"
    ] = "needs_review"
    variants: tuple[ModelVariant, ...] = Field(min_length=1, max_length=64)

    @classmethod
    def model_validate(cls, obj: Any, *args: Any, **kwargs: Any) -> "ModelPackage":
        try:
            return super().model_validate(obj, *args, **kwargs)
        except ValidationError as exc:
            for error in exc.errors(include_url=False):
                cause = (error.get("ctx") or {}).get("error")
                if isinstance(cause, ModelRegistryError):
                    raise cause from exc
                if error.get("loc") == ("schema_version",):
                    raise ModelRegistryError(
                        "schema_unsupported", "Schema is unsupported"
                    ) from exc
            raise

    @model_validator(mode="after")
    def validate_package(self) -> "ModelPackage":
        if self.schema_version != "1.0":
            raise ModelRegistryError("schema_unsupported", "Schema is unsupported")
        task_ids = [item.task_id for item in self.tasks]
        if len(set(task_ids)) != len(task_ids):
            raise ModelRegistryError("task_duplicate", "Task identities must be unique")
        limitation_ids = [item.limitation_id for item in self.limitations]
        if len(set(limitation_ids)) != len(limitation_ids):
            raise ModelRegistryError(
                "limitation_duplicate", "Limitation identities must be unique"
            )
        variant_ids = [item.variant_id for item in self.variants]
        if len(set(variant_ids)) != len(variant_ids):
            raise ModelRegistryError(
                "variant_duplicate", "Variant identities must be unique"
            )
        for variant in self.variants:
            paths = [item.path for item in variant.artifacts]
            if len(set(paths)) != len(paths):
                raise ModelRegistryError(
                    "artifact_duplicate", "Artifact paths must be unique"
                )
            vector_ids = [item.vector_id for item in variant.test_vectors]
            if len(set(vector_ids)) != len(vector_ids):
                raise ModelRegistryError(
                    "test_vector_duplicate", "Test vector identities must be unique"
                )
            if (
                sum(item.size for item in variant.artifacts)
                > variant.resources.download_bytes
            ):
                raise ModelRegistryError(
                    "resource_download_too_small",
                    "Download resource ceiling is smaller than declared artifacts",
                )
            for vector in variant.test_vectors:
                if vector.task_id not in task_ids:
                    raise ModelRegistryError(
                        "test_task_unknown", "Test vector refers to an unknown task"
                    )
                if not set(vector.limitations_exercised) <= set(limitation_ids):
                    raise ModelRegistryError(
                        "test_limitation_unknown",
                        "Test vector refers to an unknown limitation",
                    )
        if self.review_state == "approved" and self.license.acceptance_required:
            raise ModelRegistryError(
                "license_action_required",
                "Approved packages cannot require license acceptance",
            )
        document = self.canonical()
        _reject_secret_values(document)
        if len(canonical_json(document).encode("utf-8")) > MAX_RECORD_BYTES:
            raise ModelRegistryError(
                "record_too_large", "Package metadata is too large"
            )
        return self

    def canonical(self) -> dict[str, Any]:
        return _canonical(self.model_dump(mode="json", exclude_none=True))

    @property
    def digest(self) -> str:
        return canonical_digest(self.canonical())

    def variant(self, variant_id: str) -> ModelVariant:
        for variant in self.variants:
            if variant.variant_id == variant_id:
                return variant
        raise KeyError(variant_id)


__all__ = [
    "ArtifactDeclaration",
    "FailureCategory",
    "LicenseEvidence",
    "Limitation",
    "ModelPackage",
    "ModelRegistryError",
    "ModelTestVector",
    "ModelVariant",
    "ResourceEnvelope",
    "RuntimeRequirement",
    "TaskContract",
    "canonical_digest",
    "canonical_json",
]
