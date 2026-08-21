from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .windows_qualification_models import WindowsQualificationSummary

Digest = str
EvidenceClass = Literal[
    "official_production",
    "official_preview",
    "verified_community",
    "community_candidate",
    "user_reported_source_needed",
    "api_wrapper_candidate",
    "documentation_only",
    "blocked_validation",
    "excluded_or_stale",
]
TransportVariant = Literal["stdio", "streamable_http", "sse", "webmcp"]
EMPTY_BINDING_DIGEST = (
    "44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a"
)


def _is_digest(value: str) -> bool:
    return len(value) == 64 and all(
        character in "0123456789abcdef" for character in value
    )


def _require_digest(value: str, field: str) -> None:
    if not _is_digest(value):
        raise ValueError(f"{field} must be a lowercase SHA-256 digest")


def _require_ordered_times(start: datetime, end: datetime, end_field: str) -> None:
    if start.tzinfo is None or end.tzinfo is None:
        raise ValueError("timestamps must be timezone-aware")
    if end <= start:
        raise ValueError(f"{end_field} must be later than the start time")


def _reject_secret_keys(values: Any) -> Any:
    if not isinstance(values, dict):
        return values
    allowed = {
        "credentials",
        "credential_required",
        "environment_requirements",
        "header_requirements",
        "signer_key_id",
        "key_id",
        "signature",
    }
    markers = ("secret", "password", "api_key", "api_token", "authorization", "bearer")
    for key in values:
        normalized = str(key).lower()
        if normalized not in allowed and any(
            marker in normalized for marker in markers
        ):
            raise ValueError(f"raw secret-like field is forbidden: {key}")
    return values


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CapabilityDiagnostic(StrictModel):
    code: str = Field(pattern=r"^[a-z0-9_]+$")
    message: str
    recovery: str = ""
    path: str = ""


class CredentialRequirement(StrictModel):
    name: str = Field(min_length=1)
    credential_required: bool = True
    value_supplied: bool = False


class CatalogSnapshot(StrictModel):
    snapshot_id: str = Field(min_length=1)
    channel: str = Field(min_length=1, max_length=100)
    sequence: int = Field(ge=1)
    schema_version: int = Field(ge=1)
    issued_at: datetime
    expires_at: datetime
    payload_sha256: Digest
    payload_json: dict[str, Any]
    envelope_json: dict[str, Any] | None
    signer_key_id: str | None
    signature: str | None
    verification_state: Literal[
        "bundled",
        "candidate",
        "verified",
        "rejected",
        "active",
        "previous",
        "superseded",
    ]
    verified_at: datetime | None = None
    rejection_code: str | None = None

    @model_validator(mode="after")
    def validate_snapshot(self) -> "CatalogSnapshot":
        _require_digest(self.payload_sha256, "payload_sha256")
        _require_ordered_times(self.issued_at, self.expires_at, "expires_at")
        if (
            self.channel != "bundled"
            and self.verification_state not in {"bundled", "rejected"}
            and (not self.envelope_json or not self.signer_key_id or not self.signature)
        ):
            raise ValueError(
                "verified network snapshots require signed envelope metadata"
            )
        return self


class ImportedMcpDraft(StrictModel):
    draft_id: str = Field(min_length=1)
    name: str = Field(min_length=1, max_length=200)
    source_format: Literal["claude_mcp_servers", "vscode_servers", "plain_server"]
    transport: TransportVariant
    command: str | None = None
    arguments: list[str] = Field(default_factory=list)
    endpoint: str | None = None
    environment_requirements: list[CredentialRequirement] = Field(default_factory=list)
    header_requirements: list[CredentialRequirement] = Field(default_factory=list)
    warnings: list[CapabilityDiagnostic] = Field(default_factory=list)
    errors: list[CapabilityDiagnostic] = Field(default_factory=list)
    redacted_preview: dict[str, Any] = Field(default_factory=dict)
    draft_digest: Digest

    @model_validator(mode="before")
    @classmethod
    def reject_secret_fields(cls, values: Any) -> Any:
        return _reject_secret_keys(values)

    @model_validator(mode="after")
    def validate_draft(self) -> "ImportedMcpDraft":
        _require_digest(self.draft_digest, "draft_digest")
        if self.transport == "stdio" and not self.command:
            raise ValueError("stdio drafts require a command")
        if self.transport != "stdio" and not self.endpoint:
            raise ValueError("network drafts require an endpoint")
        return self


class MachineCompatibilityObservation(StrictModel):
    observation_id: str = Field(min_length=1)
    observed_at: datetime
    expires_at: datetime
    platform_key: str = Field(min_length=1)
    os_name: str
    os_version: str
    architecture: str
    distribution_mode: str
    runtimes: dict[str, dict[str, Any]] = Field(default_factory=dict)
    package_managers: dict[str, dict[str, Any]] = Field(default_factory=dict)
    container_runtime: dict[str, Any] | None = None
    network_policy: Literal["offline", "allowed", "unknown"] = "unknown"
    host_observations: dict[str, dict[str, Any]] = Field(default_factory=dict)
    digest: Digest

    @model_validator(mode="after")
    def validate_observation(self) -> "MachineCompatibilityObservation":
        _require_digest(self.digest, "digest")
        _require_ordered_times(self.observed_at, self.expires_at, "expires_at")
        return self


class CompatibilityReason(StrictModel):
    code: str = Field(pattern=r"^[a-z0-9_]+$")
    message: str
    recovery: str
    source: str


class CapabilityCompatibility(StrictModel):
    status: Literal["compatible", "incompatible", "uncertain", "blocked"]
    platform_key: str
    reasons: list[CompatibilityReason] = Field(default_factory=list)
    observation_id: str | None = None
    observed_at: datetime | None = None

    @model_validator(mode="after")
    def require_explanation(self) -> "CapabilityCompatibility":
        if self.status != "compatible" and not self.reasons:
            raise ValueError("non-compatible results require at least one reason")
        return self


class CapabilityUserState(StrictModel):
    server_id: str | None = None
    installed: bool = False
    active: bool = False
    process_status: str = "not_registered"
    explicit_disabled: bool = False
    installed_version: str | None = None
    credentials_configured: dict[str, bool] = Field(default_factory=dict)
    enabled_workspaces: list[dict[str, str]] = Field(default_factory=list)


class CapabilityView(StrictModel):
    capability_id: str
    canonical_id: str
    name: str
    vendor: str
    description: str
    domains: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    aliases: list[str] = Field(default_factory=list)
    capability_summary: list[str] = Field(default_factory=list)
    field_provenance: dict[str, str] = Field(default_factory=dict)
    data_touched: list[str] = Field(default_factory=list)
    examples: list[str] = Field(default_factory=list)
    validation_history: list[dict[str, Any]] = Field(default_factory=list)
    lifecycle_stage: str
    maturity: str
    evidence_class: EvidenceClass
    transport: TransportVariant
    locality: Literal["local", "remote"]
    risk_level: str
    installability_tier: str
    compatibility: CapabilityCompatibility
    source_records: list[dict[str, Any]] = Field(default_factory=list)
    requirements: dict[str, Any] = Field(default_factory=dict)
    validation_result: dict[str, Any] = Field(default_factory=dict)
    local_validation: dict[str, Any] | None = None
    windows_qualification: WindowsQualificationSummary | None = None
    user_state: CapabilityUserState = Field(default_factory=CapabilityUserState)
    custom: bool = False
    available_actions: list[str] = Field(default_factory=list)
    alternatives: list[str] = Field(default_factory=list)


class CapabilitySnapshotSummary(StrictModel):
    snapshot_id: str
    channel: str
    sequence: int = Field(ge=1)
    offline: bool
    updated_at: datetime


class CapabilityList(StrictModel):
    snapshot: CapabilitySnapshotSummary
    capabilities: list[CapabilityView]
    next_cursor: str | None = None
    total: int = Field(ge=0)


class LicenseRequirement(StrictModel):
    state: Literal[
        "known", "unknown", "not_applicable", "external_acceptance_required"
    ] = "unknown"
    reference: str | None = None
    independent_completion_required: bool = False
    independent_completion_recorded_at: datetime | None = None

    @model_validator(mode="after")
    def validate_license(self) -> "LicenseRequirement":
        if (
            self.state == "external_acceptance_required"
            and not self.independent_completion_required
        ):
            raise ValueError("external acceptance must require independent completion")
        return self


class InstallPlanRequirements(StrictModel):
    platform: list[str] = Field(default_factory=list)
    runtimes: list[str] = Field(default_factory=list)
    license: LicenseRequirement = Field(default_factory=LicenseRequirement)
    credentials: list[str] = Field(default_factory=list)
    network: list[str] = Field(default_factory=list)
    storage: list[str] = Field(default_factory=list)
    host: list[str] = Field(default_factory=list)


class InstallPlanStep(StrictModel):
    step_id: str = Field(min_length=1)
    kind: str = Field(min_length=1)
    description: str = Field(min_length=1)
    target: str | None = None
    reversible: bool
    rollback_step_id: str | None = None


class InstallPlan(StrictModel):
    plan_id: str = Field(min_length=1)
    plan_version: Literal[1] = 1
    state: Literal[
        "draft",
        "reviewable",
        "blocked",
        "approved",
        "applying",
        "validating",
        "completed",
        "failed",
        "rolling_back",
        "rolled_back",
        "rollback_failed",
        "invalidated",
        "expired",
    ]
    capability_id: str = Field(min_length=1)
    snapshot_id: str = Field(min_length=1)
    capability_digest: Digest
    import_draft_id: str | None = None
    import_draft_digest: Digest | None = None
    machine_observation_id: str = Field(min_length=1)
    machine_observation_digest: Digest
    backend_kind: Literal[
        "local_package", "remote_endpoint", "host_bridge", "local_command"
    ]
    requested_scope: Literal["global_registered", "workspace"]
    workspace_id: str | None = None
    source: dict[str, Any] = Field(default_factory=dict)
    requirements: InstallPlanRequirements
    effects: list[InstallPlanStep] = Field(default_factory=list)
    steps: list[InstallPlanStep] = Field(default_factory=list)
    validation_steps: list[InstallPlanStep] = Field(default_factory=list)
    rollback_steps: list[InstallPlanStep] = Field(default_factory=list)
    approval_gates: list[str] = Field(default_factory=list)
    blocking_reasons: list[CapabilityDiagnostic] = Field(default_factory=list)
    created_by: str
    created_at: datetime
    expires_at: datetime
    approved_by: str | None = None
    approved_at: datetime | None = None
    plan_digest: Digest

    @model_validator(mode="before")
    @classmethod
    def reject_secret_fields(cls, values: Any) -> Any:
        return _reject_secret_keys(values)

    @model_validator(mode="after")
    def validate_plan(self) -> "InstallPlan":
        for field, value in (
            ("capability_digest", self.capability_digest),
            ("machine_observation_digest", self.machine_observation_digest),
            ("plan_digest", self.plan_digest),
        ):
            _require_digest(value, field)
        if self.import_draft_digest:
            _require_digest(self.import_draft_digest, "import_draft_digest")
        _require_ordered_times(self.created_at, self.expires_at, "expires_at")
        license_requirement = self.requirements.license
        if (
            license_requirement.state == "external_acceptance_required"
            and license_requirement.independent_completion_recorded_at is None
            and self.state not in {"draft", "blocked", "expired", "invalidated"}
        ):
            raise ValueError("external license acceptance keeps the plan blocked")
        if self.state == "blocked" and not self.blocking_reasons:
            raise ValueError("blocked plans require blocking reasons")
        return self


class ValidationEvidence(StrictModel):
    evidence_id: str
    capability_id: str
    server_id: str
    snapshot_id: str
    capability_digest: Digest
    observation_id: str
    platform_key: str
    architecture: str
    server_revision: str = "unknown"
    credential_binding_digest: Digest = EMPTY_BINDING_DIGEST
    state: Literal[
        "not_checked",
        "queued",
        "running",
        "passed",
        "partially_passed",
        "failed",
        "blocked",
        "stale",
        "unavailable",
    ]
    protocol_steps: dict[str, Literal["pending", "passed", "failed", "skipped"]] = (
        Field(default_factory=dict)
    )
    schema_digest: Digest | None = None
    tool_count: int | None = Field(default=None, ge=0)
    read_only_probe: dict[str, Any] | None = None
    observed_at: datetime
    trace_id: str | None = None
    reason_codes: list[str] = Field(default_factory=list)
    missing_requirements: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_evidence(self) -> "ValidationEvidence":
        _require_digest(self.capability_digest, "capability_digest")
        _require_digest(self.credential_binding_digest, "credential_binding_digest")
        if self.schema_digest:
            _require_digest(self.schema_digest, "schema_digest")
        required = {"initialize", "notifications/initialized", "tools/list"}
        if self.state == "passed" and not all(
            self.protocol_steps.get(step) == "passed" for step in required
        ):
            raise ValueError("passed evidence requires required protocol steps")
        if self.state == "passed" and (
            self.schema_digest is None or self.tool_count is None
        ):
            raise ValueError("passed evidence requires discovered tool schema evidence")
        if self.state in {"failed", "blocked", "stale", "unavailable"} and not (
            self.reason_codes or self.missing_requirements
        ):
            raise ValueError(f"{self.state} evidence requires an explicit reason")
        return self


class MissingCapabilityReport(StrictModel):
    """User-owned discovery evidence, never trusted catalog metadata."""

    report_id: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=200)
    vendor: str = Field(min_length=1, max_length=200)
    source_url: str | None = Field(default=None, max_length=2048)
    domains: list[str] = Field(min_length=1, max_length=20)
    expected_task: str = Field(min_length=1, max_length=2000)
    platform: str | None = Field(default=None, max_length=200)
    host_application: str | None = Field(default=None, max_length=200)
    notes: str | None = Field(default=None, max_length=4000)
    search_context: dict[str, Any] = Field(default_factory=dict)
    reporter: str = Field(min_length=1, max_length=200)
    created_at: datetime
    updated_at: datetime
    state: Literal["submitted", "exported", "under_review", "matched", "closed"]
    matched_capability_id: str | None = None

    @model_validator(mode="before")
    @classmethod
    def reject_secret_fields(cls, values: Any) -> Any:
        _reject_secret_keys(values)
        if isinstance(values, dict):
            _reject_secret_keys(values.get("search_context"))
        return values

    @model_validator(mode="after")
    def validate_report(self) -> "MissingCapabilityReport":
        if self.created_at.tzinfo is None or self.updated_at.tzinfo is None:
            raise ValueError("timestamps must be timezone-aware")
        if self.updated_at < self.created_at:
            raise ValueError("updated_at cannot precede created_at")
        normalized_domains = [domain.strip().lower() for domain in self.domains]
        if any(not domain for domain in normalized_domains):
            raise ValueError("domains cannot contain empty values")
        self.domains = list(dict.fromkeys(normalized_domains))
        if self.state == "matched" and not self.matched_capability_id:
            raise ValueError("matched reports require a capability id")
        if self.state != "matched" and self.matched_capability_id:
            raise ValueError("only matched reports may identify a capability")
        return self
