from __future__ import annotations

from copy import deepcopy
from typing import Any, Literal, Optional, Union

from pydantic import BaseModel, Field, field_validator, model_validator

from .models import (
    EnvVarDefinition,
    InstallabilityTier,
    PlatformStatus,
    RiskLevel,
    ValidationStatus,
    VerificationState,
)

REQUIRED_PLATFORM_KEYS = (
    "windows_11_x64",
    "linux_x64",
    "linux_arm64",
    "macos_x64",
    "macos_arm64",
)

TIER_ORDER = {
    "tested": 0,
    "might_work": 1,
    "blocked": 2,
    "non_working": 3,
}

DEFAULT_PLATFORM_SUPPORT = {
    "windows_11_x64": {
        "status": "unknown",
        "tested": False,
        "notes": "not tested",
    },
    "linux_x64": {
        "status": "unknown",
        "tested": False,
        "notes": "first container target; not yet tested",
    },
    "linux_arm64": {
        "status": "unknown",
        "tested": False,
        "notes": "not tested; Linux x64 support does not imply ARM64 support",
    },
    "macos_x64": {
        "status": "unknown",
        "tested": False,
        "notes": "not tested",
    },
    "macos_arm64": {
        "status": "unknown",
        "tested": False,
        "notes": "not tested",
    },
}


class DependencySpec(BaseModel):
    system: list[str] = Field(default_factory=list)
    python: list[str] = Field(default_factory=list)
    node: list[str] = Field(default_factory=list)


class PlatformSupportRecord(BaseModel):
    status: PlatformStatus = "unknown"
    tested: bool = False
    notes: str = ""

    @field_validator("status", mode="before")
    @classmethod
    def normalize_yaml_boolean_status(cls, value):
        if value is True:
            return "yes"
        if value is False:
            return "no"
        return value


class ValidationSummary(BaseModel):
    status: ValidationStatus = "not_tested"
    message: str = "Not yet validated in this environment"
    environment: Optional[str] = None
    missing_dependencies: list[str] = Field(default_factory=list)


def default_platform_support_dict() -> dict[str, dict[str, Any]]:
    return deepcopy(DEFAULT_PLATFORM_SUPPORT)


def default_platform_support() -> dict[str, PlatformSupportRecord]:
    return {
        key: PlatformSupportRecord.model_validate(value)
        for key, value in DEFAULT_PLATFORM_SUPPORT.items()
    }


def validation_summary_dict(
    status: str = "not_tested",
    message: str = "Not yet validated in this environment",
    environment: str | None = None,
    missing_dependencies: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "status": status,
        "message": message,
        "environment": environment,
        "missing_dependencies": missing_dependencies or [],
    }


class CatalogEntry(BaseModel):
    id: str
    name: str
    vendor: str
    description: str
    domains: list[str]
    tags: list[str] = Field(default_factory=list)
    transport: Literal["stdio", "sse", "webmcp"]
    command: Union[list[str], str]
    source_url: Optional[str] = None
    image_url: Optional[str] = None
    locality: Literal["local", "remote"]
    weight: Literal["light", "medium", "heavy"]
    env_vars: list[EnvVarDefinition] = Field(default_factory=list)
    dependencies: DependencySpec = Field(default_factory=DependencySpec)
    aliases: list[str] = Field(default_factory=list)
    verification_state: VerificationState = "user_reported_url_needed"
    installability_tier: InstallabilityTier = "might_work"
    risk_level: RiskLevel = "low"
    deployment_mode: str = "unknown"
    platform_support: dict[str, PlatformSupportRecord] = Field(
        default_factory=default_platform_support
    )
    host_software_required: list[str] = Field(default_factory=list)
    credentials_required: list[str] = Field(default_factory=list)
    default_enabled: bool = True
    approval_gates: list[str] = Field(default_factory=list)
    validation_result: ValidationSummary = Field(default_factory=ValidationSummary)
    follow_up_url: Optional[str] = None
    install_blocked_reason: Optional[str] = None

    @model_validator(mode="after")
    def normalize_defaults(self) -> "CatalogEntry":
        support = default_platform_support()
        support.update(self.platform_support)
        self.platform_support = support

        if self.risk_level in {"medium", "high", "safety-critical"}:
            self.default_enabled = False

        return self
