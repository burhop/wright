"""Versioned process validation contracts; no storage, transport or tool imports."""

from __future__ import annotations

import hashlib
import json
from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    JsonValue,
    StrictBool,
    StringConstraints,
    field_validator,
    model_validator,
)

SCHEMA_VERSION = "wright.process-validation/1"
Identifier = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)
]
Digest = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
Text = Annotated[str, StringConstraints(min_length=1, max_length=8192)]
Number = Annotated[float, Field(strict=True, allow_inf_nan=False)]
CheckState = Literal[
    "pass", "fail", "blocked", "inconclusive", "error", "not_applicable"
]
Lifecycle = Literal["queued", "running", "completed", "blocked", "error", "cancelled"]
EvidenceMethod = Literal[
    "structured_value",
    "independent_measurement",
    "native_inspection",
    "producer_claim",
    "human_review",
]


def canonical_json(value: object) -> str:
    """wright-json-v1: sorted keys, compact UTF-8 JSON, finite numbers only."""
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="python")

    def model_value(item):
        if isinstance(item, BaseModel):
            return item.model_dump(mode="python")
        raise TypeError("Unsupported JSON value")

    try:
        encoded = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
            default=model_value,
        )
        encoded.encode("utf-8")
        return encoded
    except (TypeError, UnicodeError, RecursionError) as exc:
        raise ValueError("Value must be finite, serializable UTF-8 JSON") from exc


def canonical_digest(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


class Contract(BaseModel):
    model_config = ConfigDict(
        extra="forbid", frozen=True, validate_default=True, allow_inf_nan=False
    )


def _unique(values, label):
    if len(set(values)) != len(values):
        raise ValueError(f"{label} must be unique")


def relative_locator(value: str) -> str:
    if any(c in value for c in ("\\", ":", "\x00")) or any(
        part in {"", ".", ".."} for part in value.split("/")
    ):
        raise ValueError("File locator must be a confined workspace-relative path")
    return value


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


class ProducerIdentity(Contract):
    run_id: Identifier
    step_id: Identifier
    attempt: Annotated[int, Field(strict=True, ge=1)]
    output_port: Identifier


class SubjectBinding(Contract):
    id: Identifier
    role: Identifier
    result_id: Identifier
    producer: ProducerIdentity
    kind: Literal["value", "file", "provider"]
    sha256: Digest
    value: JsonValue = None
    locator: Text | None = None
    format: Identifier = "json"
    provider_id: Identifier | None = None
    resource_id: Identifier | None = None
    revision: Identifier | None = None
    input_digests: tuple[Digest, ...] = ()
    encoding: Literal["wright-json-v1", "raw-bytes"] = "wright-json-v1"

    @model_validator(mode="after")
    def exact_identity(self):
        if self.kind == "value":
            if self.encoding == "raw-bytes":
                if not isinstance(self.value, str):
                    raise ValueError("Raw inline output must contain UTF-8 text")
                digest = hashlib.sha256(self.value.encode("utf-8")).hexdigest()
            else:
                digest = canonical_digest(self.value)
            if digest != self.sha256:
                raise ValueError(
                    "Inline value digest does not match its canonical content"
                )
            if self.locator or self.provider_id or self.resource_id or self.revision:
                raise ValueError(
                    "Inline value cannot reference another storage representation"
                )
        elif self.kind == "file":
            if not self.locator:
                raise ValueError("File subject requires a locator")
            relative_locator(self.locator)
            if self.encoding != "raw-bytes":
                raise ValueError("File digests must identify raw bytes")
            if self.value is not None or self.provider_id or self.resource_id:
                raise ValueError("File subject cannot also contain a value/provider")
        elif not (self.provider_id and self.resource_id and self.revision):
            raise ValueError(
                "Provider subject requires a pinned provider/resource/revision"
            )
        return self


class ResourceBudget(Contract):
    max_bytes: Annotated[int, Field(strict=True, gt=0, le=256 * 1024 * 1024)] = (
        16 * 1024 * 1024
    )
    max_entities: Annotated[int, Field(strict=True, gt=0, le=2_000_000)] = 100_000
    timeout_seconds: Annotated[int, Field(strict=True, gt=0, le=3600)] = 120
    memory_limit_mb: Annotated[int, Field(strict=True, ge=32, le=4096)] = 512


class ValidationRequest(Contract):
    schema_version: Literal["wright.process-validation/1"] = SCHEMA_VERSION
    trace_id: Identifier
    workspace_id: Identifier
    invocation_id: Identifier
    run_id: Identifier | None = None
    check_step_id: Identifier | None = None
    subjects: tuple[SubjectBinding, ...] = Field(max_length=100)
    profile_ref: VersionReference
    baseline_ref: VersionReference
    idempotency_key: Identifier
    budget: ResourceBudget = Field(default_factory=ResourceBudget)

    @model_validator(mode="after")
    def unique_subjects(self):
        _unique([subject.id for subject in self.subjects], "Subject IDs")
        _unique([subject.role for subject in self.subjects], "Subject roles")
        if bool(self.run_id) != bool(self.check_step_id):
            raise ValueError(
                "Canonical run and check-step identity must be supplied together"
            )
        if self.run_id and any(s.producer.run_id != self.run_id for s in self.subjects):
            raise ValueError("Canonical subjects must belong to the bound run")
        return self


class ReaderIdentity(Contract):
    id: Identifier
    version: Identifier
    config_digest: Digest
    method: EvidenceMethod
    tool_identity: Text | None = None
    formats: tuple[Identifier, ...] = ()


class Measurement(Contract):
    id: Identifier
    subject_id: Identifier
    subject_sha256: Digest
    selector: Annotated[str, StringConstraints(max_length=2048)] = ""
    value: JsonValue
    unit: Identifier | None = None
    frame: Identifier | None = None
    uncertainty: Annotated[float, Field(strict=True, ge=0, allow_inf_nan=False)] = 0.0
    reader: ReaderIdentity
    evidence_refs: tuple[Text, ...] = Field(min_length=1, max_length=100)

    @field_validator("value")
    @classmethod
    def finite_value(cls, value):
        canonical_json(value)
        return value


class Correction(Contract):
    action: Literal[
        "revise_output",
        "supply_input",
        "restore_capability",
        "request_review",
        "retry_validation",
        "refresh_subject",
    ]
    target_step_id: Identifier | None = None
    target: Text
    preserve_requirement_ids: tuple[Identifier, ...] = ()
    recheck_ids: tuple[Identifier, ...] = ()


class Finding(Contract):
    id: Identifier
    code: Identifier
    check_id: Identifier
    requirement_ids: tuple[Identifier, ...] = Field(min_length=1)
    state: Literal["fail", "blocked", "inconclusive", "error"]
    severity: Literal["error", "warning", "info"] = "error"
    category: Literal[
        "output_defect",
        "missing_evidence",
        "source_conflict",
        "capability_unavailable",
        "review_required",
        "validator_error",
        "stale_subject",
    ]
    subject_id: Identifier | None = None
    owner: ProducerIdentity | None = None
    selector: Annotated[str, StringConstraints(max_length=2048)] = ""
    expected: Constraint
    observed: JsonValue = None
    unit: Identifier | None = None
    frame: Identifier | None = None
    observed_unit: Identifier | None = None
    observed_frame: Identifier | None = None
    evidence_refs: tuple[Text, ...] = ()
    source_refs: tuple[SourceReference, ...] = Field(min_length=1)
    summary: Text
    explanation: Text
    suggested_cause: Text | None = None
    correction: Correction

    @field_validator("observed")
    @classmethod
    def finite_observation(cls, value):
        canonical_json(value)
        return value

    @model_validator(mode="after")
    def repair_requires_failure(self):
        if self.correction.action == "revise_output" and not (
            self.state == "fail"
            and self.category == "output_defect"
            and self.owner
            and self.evidence_refs
        ):
            raise ValueError(
                "Artifact repair requires an evidenced defect and producer ownership"
            )
        if self.correction.target_step_id and (
            not self.owner or self.correction.target_step_id != self.owner.step_id
        ):
            raise ValueError("Correction target must match finding owner")
        return self


class CheckResult(Contract):
    check_id: Identifier
    requirement_ids: tuple[Identifier, ...] = Field(min_length=1)
    state: CheckState
    measurement_ids: tuple[Identifier, ...] = ()
    evidence_refs: tuple[Text, ...] = ()
    finding_ids: tuple[Identifier, ...] = ()
    applicability_reason: SourceReference | None = None

    @model_validator(mode="after")
    def evidenced_state(self):
        if self.state in {"pass", "fail"} and not self.evidence_refs:
            raise ValueError("A conclusive check requires evidence")
        if self.state == "not_applicable" and self.applicability_reason is None:
            raise ValueError(
                "Not applicable requires a source-backed applicability reason"
            )
        if self.state not in {"pass", "not_applicable"} and not self.finding_ids:
            raise ValueError("Non-passing check requires actionable findings")
        return self


class Summary(Contract):
    content_verified: StrictBool | None
    requirements_compliant: StrictBool | None
    evaluation_complete: StrictBool
    release_eligible: StrictBool
    physical_validation: Literal["not_assessed"] = "not_assessed"
    counts: dict[CheckState, int]


def summarize(
    profile: ValidationProfile,
    results: tuple[CheckResult, ...],
    *,
    subject_current: bool = True,
) -> Summary:
    definitions = {check.id: check for check in profile.checks}
    _unique([result.check_id for result in results], "Result check IDs")
    indexed = {result.check_id: result for result in results}
    for result in results:
        if result.check_id not in definitions or set(result.requirement_ids) != set(
            definitions[result.check_id].requirement_ids
        ):
            raise ValueError("Result requirements must match the profile check")
        if (
            result.state == "not_applicable"
            and result.applicability_reason
            != definitions[result.check_id].applicability_reason
        ):
            raise ValueError("Result applicability must match the frozen profile")
    required = {item.id for item in profile.baseline.requirements if item.mandatory}
    mandatory = [
        check
        for check in profile.checks
        if required.intersection(check.requirement_ids)
    ]
    conclusive = {"pass", "fail", "not_applicable"}
    complete = (
        bool(mandatory)
        and not profile.baseline.unresolved_decisions
        and all(
            check.id in indexed and indexed[check.id].state in conclusive
            for check in mandatory
        )
    )

    def dimension(scope):
        ids = {
            item.id
            for item in profile.baseline.requirements
            if item.mandatory and item.scope == scope
        }
        checks = [
            check for check in mandatory if ids.intersection(check.requirement_ids)
        ]
        states = [
            indexed[check.id].state if check.id in indexed else "blocked"
            for check in checks
        ]
        if "fail" in states:
            return False
        if (
            not states
            or profile.baseline.unresolved_decisions
            or any(s not in {"pass", "not_applicable"} for s in states)
        ):
            return None
        return True

    counts = {
        state: 0
        for state in (
            "pass",
            "fail",
            "blocked",
            "inconclusive",
            "error",
            "not_applicable",
        )
    }
    for check in profile.checks:
        counts[indexed[check.id].state if check.id in indexed else "blocked"] += 1
    eligible = (
        complete
        and subject_current
        and any(indexed[c.id].state == "pass" for c in mandatory)
        and all(
            indexed[check.id].state in {"pass", "not_applicable"} for check in mandatory
        )
    )
    return Summary(
        content_verified=dimension("content"),
        requirements_compliant=dimension("design"),
        evaluation_complete=complete,
        release_eligible=eligible,
        counts=counts,
    )


class Assessment(Contract):
    schema_version: Literal["wright.process-validation/1"] = SCHEMA_VERSION
    id: Identifier
    attempt_id: Identifier
    request: ValidationRequest
    profile: ValidationProfile
    created_at: Text
    measurements: tuple[Measurement, ...] = ()
    checks: tuple[CheckResult, ...] = ()
    findings: tuple[Finding, ...] = ()
    summary: Summary
    subject_current: StrictBool = True
    review_ids: tuple[Identifier, ...] = ()
    supersedes: Identifier | None = None

    @model_validator(mode="after")
    def consistent_evidence(self):
        if (
            self.profile.reference() != self.request.profile_ref
            or self.profile.baseline.reference() != self.request.baseline_ref
        ):
            raise ValueError(
                "Assessment profile/baseline identity does not match request"
            )
        if self.summary != summarize(
            self.profile, self.checks, subject_current=self.subject_current
        ):
            raise ValueError("Assessment summary differs from check evidence")
        for label, items in (
            ("Measurement", self.measurements),
            ("Finding", self.findings),
        ):
            _unique([item.id for item in items], f"{label} IDs")
        measurements = {m.id: m for m in self.measurements}
        findings = {f.id: f for f in self.findings}
        subjects = {s.id: s for s in self.request.subjects}
        for measurement in self.measurements:
            subject = subjects.get(measurement.subject_id)
            if subject is None or subject.sha256 != measurement.subject_sha256:
                raise ValueError("Measurement subject identity differs from request")
        for check in self.checks:
            if any(m not in measurements for m in check.measurement_ids):
                raise ValueError("Check references missing measurements")
            for finding_id in check.finding_ids:
                finding = findings.get(finding_id)
                if (
                    finding is None
                    or finding.check_id != check.check_id
                    or finding.state != check.state
                ):
                    raise ValueError("Check references inconsistent findings")
                if set(finding.requirement_ids) != set(check.requirement_ids):
                    raise ValueError(
                        "Finding requirements differ from the checked requirements"
                    )
                if finding.subject_id is not None:
                    subject = subjects.get(finding.subject_id)
                    if subject is None or finding.owner != subject.producer:
                        raise ValueError("Finding owner differs from its bound subject")
            definition = next(
                item for item in self.profile.checks if item.id == check.check_id
            )
            if check.state == "pass" and definition.constraint.operator == "review":
                if not set(check.evidence_refs).intersection(self.review_ids):
                    raise ValueError(
                        "Passing human review requires a recorded review identity"
                    )
        return self


class RepairFeedback(Contract):
    schema_version: Literal["wright.process-validation/1"] = SCHEMA_VERSION
    assessment_id: Identifier
    assessment_digest: Digest
    subject_digests: tuple[Digest, ...]
    profile_ref: VersionReference
    target_step_id: Identifier
    findings: tuple[Finding, ...] = Field(max_length=20)
    preserve_requirement_ids: tuple[Identifier, ...]
    remaining_revisions: Annotated[int, Field(strict=True, ge=0, le=3)]
    total_findings: Annotated[int, Field(strict=True, ge=0)]
    omitted_findings: Annotated[int, Field(strict=True, ge=0)]
    complete_result_ref: Text

    @model_validator(mode="after")
    def valid_delivery(self):
        if self.total_findings != len(self.findings) + self.omitted_findings:
            raise ValueError("Feedback omitted-finding count is inconsistent")
        if any(
            f.correction.action == "revise_output"
            and f.correction.target_step_id != self.target_step_id
            for f in self.findings
        ):
            raise ValueError("Feedback contains a correction for another producer")
        return self


class AssessmentReference(Contract):
    schema_version: Literal["wright.process-validation/1"] = SCHEMA_VERSION
    assessment_id: Identifier
    assessment_digest: Digest
    attempt_id: Identifier
    workspace_id: Identifier
    is_current: bool
    release_eligible: bool
    summary: Summary
    finding_count: Annotated[int, Field(strict=True, ge=0)]


class FindingPage(AssessmentReference):
    findings: tuple[Finding, ...] = Field(max_length=20)
    next_cursor: Annotated[int, Field(strict=True, ge=0)] | None = None


class AssessmentCurrentness(Contract):
    as_of: Text
    selected_assessment_id: Identifier
    selected_attempt_id: Identifier
    selected_subject_ids: tuple[Identifier, ...]
    latest_attempt_id: Identifier
    latest_assessment_id: Identifier | None = None
    superseded_by: tuple[Identifier, ...] = ()
    is_current: StrictBool
    stale_reason: Literal[
        "newer_validation_attempt",
        "superseded_by_review",
        "subject_revision_changed",
        "subject_changed_during_validation",
        "subject_unavailable",
    ] | None = None

    @model_validator(mode="after")
    def explains_staleness(self):
        if self.is_current == (self.stale_reason is not None):
            raise ValueError("Currentness and stale reason are inconsistent")
        return self


class RequirementTraceRow(Contract):
    requirement_id: Identifier
    requirement_text: Text
    requirement_scope: Literal["content", "design"]
    mandatory: StrictBool
    review_required: StrictBool
    source_refs: tuple[SourceReference, ...] = Field(min_length=1)
    check_id: Identifier
    check_version: Identifier
    check_state: CheckState
    reader: Identifier
    evidence_method: EvidenceMethod
    selector: Annotated[str, StringConstraints(max_length=2048)] = ""
    expected: Constraint
    expected_unit: Identifier | None = None
    expected_frame: Identifier | None = None
    observed: tuple[JsonValue, ...] = ()
    observed_units: tuple[Identifier | None, ...] = ()
    observed_frames: tuple[Identifier | None, ...] = ()
    evidence_refs: tuple[Text, ...] = ()
    subject_id: Identifier | None = None
    subject_sha256: Digest | None = None
    producer: ProducerIdentity | None = None
    finding_ids: tuple[Identifier, ...] = ()
    action: Literal[
        "revise_output",
        "supply_input",
        "restore_capability",
        "request_review",
        "retry_validation",
        "refresh_subject",
    ] | None = None

    @model_validator(mode="after")
    def aligned_observations(self):
        if not (
            len(self.observed)
            == len(self.observed_units)
            == len(self.observed_frames)
        ):
            raise ValueError("Observed values, units and frames must align")
        if self.subject_id is None and (
            self.subject_sha256 is not None or self.producer is not None
        ):
            raise ValueError("Subject provenance requires a subject identity")
        return self


class ReportScope(Contract):
    requirement_ids: tuple[Identifier, ...] = Field(min_length=1)
    excluded_scope: tuple[Text, ...] = ()
    limitations: tuple[Text, ...] = ()
    physical_validation: Literal["not_assessed"] = "not_assessed"


class ValidationReport(Contract):
    schema_version: Literal["wright.process-validation-report/1"] = (
        "wright.process-validation-report/1"
    )
    assessment_digest: Digest
    currentness: AssessmentCurrentness
    scope: ReportScope
    reader_identities: tuple[ReaderIdentity, ...]
    traceability: tuple[RequirementTraceRow, ...] = Field(min_length=1)
    assessment: Assessment

    @model_validator(mode="after")
    def matches_assessment(self):
        assessment = self.assessment
        if self.assessment_digest != canonical_digest(assessment):
            raise ValueError("Report assessment digest does not match its payload")
        if (
            self.currentness.selected_assessment_id != assessment.id
            or self.currentness.selected_attempt_id != assessment.attempt_id
            or self.currentness.selected_subject_ids
            != tuple(subject.id for subject in assessment.request.subjects)
        ):
            raise ValueError("Report currentness does not identify its assessment")
        required = tuple(item.id for item in assessment.profile.baseline.requirements)
        if self.scope.requirement_ids != required:
            raise ValueError("Report scope differs from the assessment baseline")
        expected_rows = {
            (requirement_id, check.id)
            for check in assessment.profile.checks
            for requirement_id in check.requirement_ids
        }
        actual_rows = {
            (row.requirement_id, row.check_id) for row in self.traceability
        }
        if actual_rows != expected_rows or len(actual_rows) != len(self.traceability):
            raise ValueError("Report traceability differs from profile coverage")
        return self


class ReviewDecision(Contract):
    id: Identifier
    workspace_id: Identifier
    assessment_id: Identifier
    assessment_digest: Digest
    requirement_id: Identifier
    actor_id: Identifier
    actor_type: Literal["authenticated_human"]
    authority_ref: Identifier
    decision: Literal["approved", "changes_requested"]
    rationale: Text
    evidence_refs: tuple[Text, ...] = Field(min_length=1)
    created_at: Text
