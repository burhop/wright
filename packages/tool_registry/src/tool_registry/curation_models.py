"""Reviewed catalog recommendations, independent of local installation state."""

from datetime import date
import hashlib
import json
from typing import Any
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

CurationDisposition = Literal["curated", "follow_up", "removed"]
EngineeringStage = Literal[
    "requirements",
    "concept",
    "design",
    "simulation",
    "sourcing",
    "manufacturing",
    "test_quality",
    "release",
    "operations",
]
ENGINEERING_STAGES: dict[str, str] = {
    "requirements": "Requirements",
    "concept": "Concept and architecture",
    "design": "Detailed design",
    "simulation": "Analysis and simulation",
    "sourcing": "BOM and sourcing",
    "manufacturing": "Manufacturing and assembly",
    "test_quality": "Test and quality",
    "release": "Release and change management",
    "operations": "Operations and service",
}
IntegrationKind = Literal[
    "mcp_server",
    "webmcp_application",
    "protocol_reference",
    "api_candidate",
    "capability_alias",
    "agent_skills",
]
HardwareStandard = Literal["none", "hardware_mcp", "mhs_preview"]


class QualificationScope(BaseModel):
    model_config = ConfigDict(extra="forbid")

    platform: Literal[
        "windows_11_x64", "linux_x64", "linux_arm64", "macos_x64", "macos_arm64"
    ]
    environment: str = Field(min_length=1, max_length=200)
    distribution_mode: Literal["native", "docker"]
    configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    workflow: str = Field(min_length=1, max_length=500)
    source_revision: str = Field(min_length=1, max_length=200)
    wright_revision: str = Field(min_length=1, max_length=200)
    verified_at: date
    expires_at: date
    evidence_path: str = Field(min_length=1, max_length=500)
    evidence_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    protocol: Literal["passed"]
    backend: Literal["passed"]
    gateway: Literal["passed"]
    outcome: Literal["passed"]

    @model_validator(mode="after")
    def check_interval(self) -> "QualificationScope":
        if self.expires_at <= self.verified_at:
            raise ValueError("qualification expiry must follow verification")
        if (self.expires_at - self.verified_at).days > 60:
            raise ValueError("software qualification cannot exceed 60 days")
        return self


class CurationDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    disposition: CurationDisposition = "follow_up"
    reason: str = Field(
        default="Wright qualification has not been reviewed.", max_length=2000
    )
    owner: str = Field(
        default="Wright catalog maintainers", min_length=1, max_length=200
    )
    reviewed_at: date | None = None
    review_due: date | None = None
    next_action: str = Field(
        default="Review sources and qualify a useful workflow through Wright.",
        max_length=2000,
    )
    replacement_ids: list[str] = Field(default_factory=list, max_length=20)
    adoption: Literal[
        "unknown", "publisher_reported", "independent_reports", "wright_repeat_use"
    ] = "unknown"
    adoption_evidence: list[str] = Field(default_factory=list, max_length=20)
    qualifications: list[QualificationScope] = Field(
        default_factory=list, max_length=30
    )

    @model_validator(mode="after")
    def check_decision(self) -> "CurationDecision":
        if self.disposition != "follow_up" and not self.reviewed_at:
            raise ValueError("curated and removed decisions require a review date")
        if self.review_due and self.reviewed_at and self.review_due <= self.reviewed_at:
            raise ValueError("review due date must follow review date")
        if self.disposition == "curated" and (
            not self.qualifications or not self.review_due
        ):
            raise ValueError(
                "curated decisions require scoped qualification and a review due date"
            )
        if self.adoption != "unknown" and not self.adoption_evidence:
            raise ValueError("adoption claims require evidence")
        return self


class CurationView(CurationDecision):
    effective_disposition: CurationDisposition = "follow_up"
    review_overdue: bool = False
    limitations: list[str] = Field(default_factory=list)


def evaluate_curation(
    decision: CurationDecision,
    *,
    today: date,
    platform: str | None = None,
    distribution_mode: str | None = None,
    configuration_sha256: str | None = None,
) -> CurationView:
    """Expiry affects recommendations only; never mutate the reviewed decision."""
    effective = decision.disposition
    limitations: list[str] = []
    overdue = bool(decision.review_due and today >= decision.review_due)
    if decision.reviewed_at and decision.reviewed_at > today:
        limitations.append("The review is dated in the future.")
        if effective == "curated":
            effective = "follow_up"
    if effective == "curated":
        scopes = [
            scope
            for scope in decision.qualifications
            if scope.verified_at <= today < scope.expires_at
            and (platform is None or scope.platform == platform)
            and (
                distribution_mode is None
                or scope.distribution_mode == distribution_mode
            )
            and (
                configuration_sha256 is None
                or scope.configuration_sha256 == configuration_sha256
            )
        ]
        if overdue or not scopes:
            effective = "follow_up"
            limitations.append(
                "Recommendation needs renewal."
                if overdue
                else "No current qualification for this platform, deployment, and configuration."
            )
    if decision.adoption == "unknown":
        limitations.append("Repeat user adoption has not been measured.")
    return CurationView(
        **decision.model_dump(),
        effective_disposition=effective,
        review_overdue=overdue,
        limitations=limitations,
    )


def qualification_configuration(entry: Any) -> str:
    """Invalidate a recommendation when its reviewed launch or prerequisites change."""
    values = entry.model_dump(mode="json")
    fields = (
        "id",
        "transport",
        "command",
        "source_url",
        "repository_url",
        "package_url",
        "container_url",
        "launch_env",
        "env_vars",
        "dependencies",
        "auth_model",
        "host_software_required",
        "credentials_required",
        "runtime_requirements",
        "risk_level",
        "approval_gates",
        "integration_kind",
        "hardware_standard",
    )
    payload = {key: values.get(key) for key in fields}
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
