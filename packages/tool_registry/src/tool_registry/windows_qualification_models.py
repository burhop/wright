from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any, Literal
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

WINDOWS_MCP_ALLOWLIST = (
    "brep-mcp",
    "solid-edge-mcp-burhop",
    "aps-mcp-server-nodejs",
    "autodesk-product-help-mcp",
    "autodesk-fusion-desktop-mcp",
    "autodesk-fusion-data-mcp",
    "onshape-labs-featurescript-mcp",
)
QUALIFICATION_STAGES = (
    "source_current",
    "windows_install_passed",
    "mcp_started",
    "protocol_passed",
    "safe_probe_passed",
    "wright_install_passed",
    "wright_gateway_passed",
    "cleanup_passed",
)
QUALIFICATION_RESULTS = (
    "passed",
    "partial",
    "failed",
    "safety_blocked",
    "obsolete_or_unavailable",
    "not_applicable",
    "not_tested",
)
QUALIFICATION_MAX_AGE = timedelta(hours=24)
MAX_EVIDENCE_BYTES = 1024 * 1024
EMPTY_DIGEST = "0" * 64

ServerId = Literal[
    "brep-mcp",
    "solid-edge-mcp-burhop",
    "aps-mcp-server-nodejs",
    "autodesk-product-help-mcp",
    "autodesk-fusion-desktop-mcp",
    "autodesk-fusion-data-mcp",
    "onshape-labs-featurescript-mcp",
]
QualificationStage = Literal[
    "source_current",
    "windows_install_passed",
    "mcp_started",
    "protocol_passed",
    "safe_probe_passed",
    "wright_install_passed",
    "wright_gateway_passed",
    "cleanup_passed",
]
QualificationResult = Literal[
    "passed",
    "partial",
    "failed",
    "safety_blocked",
    "obsolete_or_unavailable",
    "not_applicable",
    "not_tested",
]


class QualificationModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


def _require_digest(value: str | None, field_name: str) -> str | None:
    if value is not None and (
        len(value) != 64 or any(char not in "0123456789abcdef" for char in value)
    ):
        raise ValueError(f"{field_name} must be a lowercase SHA-256 digest")
    return value


def _require_uri(value: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme not in {"https", "http"} or not parsed.netloc:
        raise ValueError("network destinations must be absolute HTTP(S) URIs")
    if parsed.scheme == "http" and parsed.hostname not in {"127.0.0.1", "localhost"}:
        raise ValueError("cleartext network destinations are limited to loopback")
    return value.rstrip("/")


def _reject_forbidden_parameter_keys(value: Any) -> None:
    forbidden = {
        "command",
        "cmd",
        "shell",
        "powershell",
        "script",
        "env",
        "environment",
    }
    if isinstance(value, dict):
        for key, nested in value.items():
            if str(key).lower() in forbidden:
                raise ValueError(f"forbidden operation parameter: {key}")
            _reject_forbidden_parameter_keys(nested)
    elif isinstance(value, list):
        for nested in value:
            _reject_forbidden_parameter_keys(nested)


class QualificationSource(QualificationModel):
    kind: Literal["git", "npm", "vendor_docs", "built_in_host", "remote_endpoint"]
    url: str = Field(min_length=1, max_length=2048)
    immutable_revision: str | None = Field(default=None, max_length=256)
    package_name: str | None = Field(default=None, max_length=200)
    package_version: str | None = Field(default=None, max_length=100)
    artifact_integrity: str | None = Field(default=None, max_length=512)
    maintenance_expectation: Literal[
        "active", "preview", "built_in", "archived", "missing", "unknown"
    ]

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        return _require_uri(value)

    @model_validator(mode="after")
    def require_pins_for_downloadable_sources(self) -> "QualificationSource":
        if self.kind in {"git", "npm"} and not self.immutable_revision:
            raise ValueError("downloadable sources require an immutable revision")
        if self.kind == "npm" and not (
            self.package_name and self.package_version and self.artifact_integrity
        ):
            raise ValueError(
                "npm sources require pinned package identity and integrity"
            )
        return self


class RiskFinding(QualificationModel):
    capability: str = Field(min_length=1, max_length=200)
    severity: Literal["low", "medium", "high", "critical"]
    boundary: str = Field(min_length=1, max_length=1000)
    rationale: str = Field(min_length=1, max_length=2000)


class QualificationOperation(QualificationModel):
    operation_id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{0,127}$")
    stage: QualificationStage
    kind: Literal[
        "source_metadata",
        "npm_local_install",
        "git_checkout",
        "dotnet_local_build",
        "stdio_mcp",
        "remote_mcp",
        "loopback_mcp",
        "wright_onboarding",
        "wright_gateway",
        "residue_snapshot",
        "stop_owned_processes",
        "remove_isolated_root",
    ]
    timeout_seconds: int = Field(default=60, ge=1, le=900)
    output_limit_bytes: int = Field(default=65536, ge=1024, le=65536)
    parameters: dict[str, Any] = Field(default_factory=dict, max_length=32)

    @field_validator("parameters")
    @classmethod
    def reject_arbitrary_execution_authority(
        cls, value: dict[str, Any]
    ) -> dict[str, Any]:
        _reject_forbidden_parameter_keys(value)
        return value


class SafeProbe(QualificationModel):
    tool_name: str = Field(min_length=1, max_length=200)
    arguments: dict[str, Any] = Field(default_factory=dict, max_length=32)
    mode: Literal["read_only", "disposable_brep_geometry"]
    safety_rationale: str = Field(min_length=1, max_length=2000)
    write_scope: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def validate_write_scope(self) -> "SafeProbe":
        if self.mode == "read_only" and self.write_scope is not None:
            raise ValueError("read-only probes cannot declare a write scope")
        if self.mode == "disposable_brep_geometry" and (
            self.write_scope != "disposable_work_root"
        ):
            raise ValueError("BREP geometry probes must use the disposable work root")
        return self


class WindowsQualificationRecipe(QualificationModel):
    schema_version: Literal["1.0"] = "1.0"
    recipe_id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{0,127}$")
    server_id: ServerId
    publisher: str = Field(min_length=1, max_length=200)
    source: QualificationSource
    license: str = Field(min_length=1, max_length=500)
    locality: Literal["local_package", "built_in_host", "remote"]
    transport: Literal["stdio", "streamable_http", "sse"]
    allowed_network_destinations: list[str] = Field(default_factory=list, max_length=32)
    credential_requirements: list[str] = Field(default_factory=list, max_length=32)
    host_requirements: list[str] = Field(default_factory=list, max_length=16)
    risk_findings: list[RiskFinding] = Field(default_factory=list, max_length=64)
    operations: list[QualificationOperation] = Field(
        default_factory=list, max_length=32
    )
    safe_probe: SafeProbe | None = None
    expected_residue: list[str] = Field(default_factory=list, max_length=128)
    cleanup: list[QualificationOperation] = Field(default_factory=list, max_length=32)

    @field_validator("allowed_network_destinations")
    @classmethod
    def validate_destinations(cls, values: list[str]) -> list[str]:
        normalized = [_require_uri(value) for value in values]
        if len(normalized) != len(set(normalized)):
            raise ValueError("allowed network destinations must be unique")
        return normalized

    @model_validator(mode="after")
    def validate_recipe_semantics(self) -> "WindowsQualificationRecipe":
        operation_ids = [operation.operation_id for operation in self.operations]
        operation_ids += [operation.operation_id for operation in self.cleanup]
        if len(operation_ids) != len(set(operation_ids)):
            raise ValueError("qualification operation IDs must be unique")
        if any(operation.stage != "cleanup_passed" for operation in self.cleanup):
            raise ValueError("cleanup operations must use cleanup_passed stage")
        if self.safe_probe and self.safe_probe.mode == "disposable_brep_geometry":
            if self.server_id != "brep-mcp":
                raise ValueError("only brep-mcp may use a disposable geometry probe")
            program_digest = self.safe_probe.arguments.get("program_sha256")
            _require_digest(str(program_digest), "safe_probe program_sha256")
        return self


class SafetyPreflight(QualificationModel):
    decision: Literal["approved", "safety_blocked", "obsolete_or_unavailable"]
    reason_code: str = Field(min_length=1, max_length=200)
    reviewed_at: datetime
    material_concerns: list[str] = Field(default_factory=list, max_length=64)
    residual_risks: list[str] = Field(default_factory=list, max_length=64)


class StageEvidence(QualificationModel):
    stage: QualificationStage
    result: QualificationResult
    reason_code: str = Field(min_length=1, max_length=200)
    summary: str = Field(default="", max_length=4000)
    recovery: str = Field(default="", max_length=4000)
    started_at: datetime | None = None
    finished_at: datetime | None = None
    duration_ms: int | None = Field(default=None, ge=0)
    operation_digest: str | None = None
    output_digest: str | None = None
    artifact_digests: list[str] = Field(default_factory=list, max_length=64)
    observations: dict[str, str | int | float | bool | None] = Field(
        default_factory=dict, max_length=64
    )
    missing_requirements: list[str] = Field(default_factory=list, max_length=32)
    network_destinations_contacted: list[str] = Field(
        default_factory=list, max_length=32
    )

    @field_validator("operation_digest", "output_digest")
    @classmethod
    def validate_optional_digests(cls, value: str | None, info):
        return _require_digest(value, info.field_name)

    @field_validator("artifact_digests")
    @classmethod
    def validate_artifact_digests(cls, values: list[str]) -> list[str]:
        return [_require_digest(value, "artifact_digest") or "" for value in values]

    @field_validator("network_destinations_contacted")
    @classmethod
    def validate_contacted_destinations(cls, values: list[str]) -> list[str]:
        return [_require_uri(value) for value in values]


class ServerQualificationEvidence(QualificationModel):
    schema_version: Literal["1.0"] = "1.0"
    evidence_id: str = Field(min_length=1, max_length=200)
    server_id: ServerId
    policy_version: str = Field(min_length=1, max_length=100)
    recipe_digest: str
    source_revision: str | None = Field(default=None, max_length=256)
    package_version: str | None = Field(default=None, max_length=100)
    package_digest: str | None = None
    tool_schema_digest: str | None = None
    machine_digest: str
    credential_binding_digest: str
    observed_at: datetime
    maximum_age_hours: int = Field(default=24, ge=1, le=8760)
    stale_reasons: list[str] = Field(default_factory=list, max_length=32)
    safety_preflight: SafetyPreflight
    stages: list[StageEvidence]
    server_identity: str | None = Field(default=None, max_length=200)
    server_version: str | None = Field(default=None, max_length=100)
    protocol_version: str | None = Field(default=None, max_length=100)
    tool_count: int | None = Field(default=None, ge=0, le=10000)
    installed_items: list[str] = Field(default_factory=list, max_length=256)
    cleanup_events: list[str] = Field(default_factory=list, max_length=256)
    attempted_server_ids: list[ServerId] = Field(default_factory=list, max_length=7)
    non_allowlist_actions: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list, max_length=64)
    residual_risks: list[str] = Field(default_factory=list, max_length=64)
    follow_ups: list[str] = Field(default_factory=list, max_length=64)
    terminal_classification: QualificationResult

    @field_validator(
        "recipe_digest",
        "package_digest",
        "tool_schema_digest",
        "machine_digest",
        "credential_binding_digest",
    )
    @classmethod
    def validate_digests(cls, value: str | None, info):
        return _require_digest(value, info.field_name)

    @model_validator(mode="after")
    def validate_complete_evidence(self) -> "ServerQualificationEvidence":
        if [stage.stage for stage in self.stages] != list(QUALIFICATION_STAGES):
            raise ValueError(
                "qualification stages must contain all eight stages exactly once in order"
            )
        if self.non_allowlist_actions:
            raise ValueError("non-allowlisted qualification actions are forbidden")
        if any(server_id != self.server_id for server_id in self.attempted_server_ids):
            raise ValueError(
                "server evidence may record attempts only for its own identity"
            )
        if len(self.model_dump_json().encode("utf-8")) > MAX_EVIDENCE_BYTES:
            raise ValueError("qualification evidence exceeds the 1 MiB limit")
        return self


class WindowsQualificationStatus(QualificationModel):
    result: QualificationResult
    label: str = Field(min_length=1, max_length=100)
    reason_code: str = Field(min_length=1, max_length=200)


class WindowsQualificationSummary(QualificationModel):
    observed_at: datetime
    evidence_path: str = Field(min_length=1, max_length=500)
    evidence_digest: str
    current: bool = True
    stale_reasons: list[str] = Field(default_factory=list, max_length=32)
    source: WindowsQualificationStatus
    package_or_registration: WindowsQualificationStatus
    startup: WindowsQualificationStatus
    protocol: WindowsQualificationStatus
    host_or_backend: WindowsQualificationStatus
    wright_setup: WindowsQualificationStatus
    gateway: WindowsQualificationStatus
    cleanup: WindowsQualificationStatus
    claim: str | None = Field(default=None, max_length=200)

    @field_validator("evidence_digest")
    @classmethod
    def validate_evidence_digest(cls, value: str) -> str:
        return _require_digest(value, "evidence_digest") or value

    @model_validator(mode="after")
    def validate_claim(self) -> "WindowsQualificationSummary":
        if self.current and self.stale_reasons:
            raise ValueError(
                "current qualification summaries cannot have stale reasons"
            )
        if self.claim == "Installs on Windows with no problems":
            required = (
                self.package_or_registration,
                self.startup,
                self.protocol,
                self.wright_setup,
                self.cleanup,
            )
            if not self.current or any(item.result != "passed" for item in required):
                raise ValueError(
                    "no-problems claim requires current passed install, startup, "
                    "protocol, Wright setup, and cleanup evidence"
                )
        return self


class QualificationRun(QualificationModel):
    run_id: str = Field(min_length=1, max_length=200)
    policy_version: str = Field(min_length=1, max_length=100)
    started_at: datetime
    finished_at: datetime | None = None
    next_server_id: ServerId | None = None
    server_evidence: list[str] = Field(default_factory=list, max_length=7)
    installed_items: list[str] = Field(default_factory=list, max_length=256)
    cleanup_events: list[str] = Field(default_factory=list, max_length=256)
    attempted_server_ids: list[ServerId] = Field(default_factory=list, max_length=7)
    non_allowlist_actions: list[str] = Field(default_factory=list)
    status: Literal["running", "completed", "failed_infrastructure"] = "running"

    @model_validator(mode="after")
    def reject_non_allowlisted_actions(self) -> "QualificationRun":
        if self.non_allowlist_actions:
            raise ValueError("non-allowlisted qualification actions are forbidden")
        return self


def qualification_staleness_reasons(
    evidence: ServerQualificationEvidence,
    *,
    recipe_digest: str,
    source_revision: str | None,
    package_version: str | None,
    tool_schema_digest: str | None,
    machine_digest: str,
    credential_binding_digest: str,
    now: datetime | None = None,
) -> list[str]:
    comparisons = (
        (evidence.recipe_digest, recipe_digest, "qualification_recipe_changed"),
        (evidence.source_revision, source_revision, "qualification_source_changed"),
        (evidence.package_version, package_version, "qualification_package_changed"),
        (
            evidence.tool_schema_digest,
            tool_schema_digest,
            "qualification_schema_changed",
        ),
        (evidence.machine_digest, machine_digest, "qualification_machine_changed"),
        (
            evidence.credential_binding_digest,
            credential_binding_digest,
            "qualification_credential_binding_changed",
        ),
    )
    reasons = [code for before, after, code in comparisons if before != after]
    current_time = now or datetime.now(UTC)
    if current_time - evidence.observed_at > timedelta(
        hours=evidence.maximum_age_hours
    ):
        reasons.append("qualification_evidence_expired")
    return reasons


def empty_stage_evidence(
    *,
    result: QualificationResult = "not_tested",
    reason_code: str = "not_attempted",
    summary: str = "This stage was not attempted.",
    recovery: str = "Review prerequisites and rerun qualification.",
) -> list[StageEvidence]:
    return [
        StageEvidence(
            stage=stage,
            result=result,
            reason_code=reason_code,
            summary=summary,
            recovery=recovery,
        )
        for stage in QUALIFICATION_STAGES
    ]
