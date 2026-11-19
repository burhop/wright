"""Definition-only wire declarations used to verify a transferred validation dependency."""

import re
from typing import Annotated, Literal

from pydantic import (
    Field,
    JsonValue,
    StrictBool,
    StringConstraints,
    field_validator,
    model_validator,
)

from .contracts import Contract, Digest, Identifier, canonical_digest, canonical_json

SCHEMA_VERSION = "wright.process-validation/1"
Text = Annotated[str, StringConstraints(min_length=1, max_length=8192)]
Number = Annotated[float, Field(strict=True, allow_inf_nan=False)]
EvidenceMethod = Literal[
    "structured_value",
    "independent_measurement",
    "native_inspection",
    "producer_claim",
    "human_review",
]


def _unique(values, label):
    if len(set(values)) != len(values):
        raise ValueError(f"{label} must be unique")


class VersionReference(Contract):
    id: Identifier
    version: Identifier
    sha256: Digest


class SourceReference(Contract):
    artifact_ref: Text
    sha256: Digest
    locator: Text


class Requirement(Contract):
    id: Identifier
    text: Text
    scope: Literal["content", "design"]
    sources: tuple[SourceReference, ...] = Field(min_length=1, max_length=64)
    mandatory: StrictBool = True
    review_required: StrictBool = False


class Baseline(Contract):
    id: Identifier
    version: Identifier
    requirements: tuple[Requirement, ...] = Field(min_length=1, max_length=1000)
    unresolved_decisions: tuple[Text, ...] = ()
    amendments: tuple[SourceReference, ...] = ()

    @model_validator(mode="after")
    def unique_requirements(self):
        _unique([item.id for item in self.requirements], "Requirement IDs")
        return self

    def reference(self) -> VersionReference:
        return VersionReference(
            id=self.id, version=self.version, sha256=canonical_digest(self)
        )


class Constraint(Contract):
    operator: Literal["exists", "type", "equals", "within", "range", "review"]
    expected: JsonValue = None
    target: Number | None = None
    tolerance: (
        Annotated[float, Field(strict=True, ge=0, allow_inf_nan=False)] | None
    ) = None
    minimum: Number | None = None
    maximum: Number | None = None
    inclusive: StrictBool = True

    @field_validator("expected")
    @classmethod
    def finite_expected(cls, value):
        canonical_json(value)
        return value

    @model_validator(mode="after")
    def valid_limits(self):
        if self.operator == "within" and (
            self.target is None or self.tolerance is None
        ):
            raise ValueError(
                "Within requires a finite target and nonnegative tolerance"
            )
        if self.operator == "range":
            if self.minimum is None and self.maximum is None:
                raise ValueError("Range requires at least one finite bound")
            if (
                self.minimum is not None
                and self.maximum is not None
                and self.minimum > self.maximum
            ):
                raise ValueError("Range minimum exceeds maximum")
        if self.operator == "type" and self.expected not in (
            "object",
            "array",
            "string",
            "number",
            "boolean",
            "null",
        ):
            raise ValueError("Type requires a supported JSON type")
        if self.operator != "within" and (
            self.target is not None or self.tolerance is not None
        ):
            raise ValueError("Target/tolerance only apply to within")
        if self.operator != "range" and (
            self.minimum is not None or self.maximum is not None
        ):
            raise ValueError("Minimum/maximum only apply to range")
        return self


class CheckDefinition(Contract):
    id: Identifier
    version: Identifier = "1"
    requirement_ids: tuple[Identifier, ...] = Field(min_length=1, max_length=100)
    subject_role: Identifier
    reader: Identifier
    selector: Annotated[str, StringConstraints(max_length=2048)] = ""
    constraint: Constraint
    unit: Identifier | None = None
    frame: Identifier | None = None
    evidence_method: EvidenceMethod = "structured_value"
    parameters: dict[str, JsonValue] = Field(default_factory=dict)
    applicability_reason: SourceReference | None = None

    @model_validator(mode="after")
    def valid_check(self):
        _unique(self.requirement_ids, "Check requirement IDs")
        canonical_json(self.parameters)
        if self.constraint.operator in {"within", "range"} and not self.unit:
            raise ValueError(
                "Numeric checks require an explicit unit (use '1' for dimensionless)"
            )
        return self


class ValidationProfile(Contract):
    schema_version: Literal["wright.process-validation/1"] = SCHEMA_VERSION
    id: Identifier
    version: Identifier
    baseline: Baseline
    checks: tuple[CheckDefinition, ...] = Field(min_length=1, max_length=2000)
    excluded_scope: tuple[Text, ...] = ()
    limitations: tuple[Text, ...] = ()
    supported_kinds: tuple[Literal["value", "file", "provider"], ...] = (
        "value",
        "file",
    )

    @model_validator(mode="after")
    def valid_coverage(self):
        _unique([check.id for check in self.checks], "Check IDs")
        required = {item.id for item in self.baseline.requirements if item.mandatory}
        known = {item.id for item in self.baseline.requirements}
        covered = {item for check in self.checks for item in check.requirement_ids}
        if covered - known:
            raise ValueError("Checks reference unknown requirements")
        if required - covered:
            raise ValueError("Mandatory requirement coverage is incomplete")
        review_coverage = {
            rid
            for check in self.checks
            if check.constraint.operator == "review"
            for rid in check.requirement_ids
        }
        if any(
            req.review_required and req.id not in review_coverage
            for req in self.baseline.requirements
        ):
            raise ValueError(
                "Review-required requirements need an explicit review check"
            )
        if not self.supported_kinds:
            raise ValueError("Profile needs a supported subject kind")
        return self

    def reference(self) -> VersionReference:
        return VersionReference(
            id=self.id, version=self.version, sha256=canonical_digest(self)
        )


class ResourceBudget(Contract):
    max_bytes: Annotated[int, Field(strict=True, gt=0, le=256 * 1024 * 1024)] = (
        16 * 1024 * 1024
    )
    max_entities: Annotated[int, Field(strict=True, gt=0, le=2_000_000)] = 100_000
    timeout_seconds: Annotated[int, Field(strict=True, gt=0, le=3600)] = 120
    memory_limit_mb: Annotated[int, Field(strict=True, ge=32, le=4096)] = 512


class ProfileLocation(Contract):
    source: Literal["packaged", "workspace"]
    name: Annotated[str, Field(min_length=1, max_length=256)]
    reference: VersionReference

    @model_validator(mode="after")
    def safe_location(self):
        if self.source == "packaged":
            if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,127}", self.name):
                raise ValueError("Use a packaged profile name")
        else:
            from .bundle import portable_path

            portable_path(self.name)
            if not self.name.endswith(".json"):
                raise ValueError("Workspace profiles must be JSON files")
        return self


class ValidatorConfiguration(Contract):
    profile: ProfileLocation
    baseline: VersionReference
    subjects: Annotated[
        dict[Identifier, Identifier], Field(min_length=1, max_length=32)
    ]
    budget: ResourceBudget = Field(default_factory=ResourceBudget)
    rework_scope: Literal["producer", "verified_segment"] = "producer"
    repair_subjects: tuple[Identifier, ...] = ()

    @model_validator(mode="after")
    def unique_ports(self):
        if self.rework_scope == "verified_segment":
            if not self.repair_subjects or len(set(self.repair_subjects)) != len(
                self.repair_subjects
            ):
                raise ValueError(
                    "Declare distinct repair subject roles for a verified segment"
                )
            if not set(self.repair_subjects) <= set(self.subjects):
                raise ValueError(
                    "Every repair subject must have an explicit input binding"
                )
        elif self.repair_subjects:
            raise ValueError("Repair subject roles require verified-segment rework")
        if len(set(self.subjects.values())) != len(self.subjects):
            raise ValueError("Each subject role needs a distinct input port")
        return self
