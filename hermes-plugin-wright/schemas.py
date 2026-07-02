from pydantic import BaseModel, Field
from typing import List, Optional, Union, Literal


VerificationState = Literal[
    "verified_mcp",
    "verified_docs_mcp",
    "community_mcp",
    "user_reported_url_needed",
    "verified_api_wrapper_candidate",
    "capability_alias",
    "ui_or_web_standard",
    "watchlist",
    "excluded",
]
InstallabilityTier = Literal["tested", "might_work", "blocked", "non_working"]
RiskLevel = Literal["read-only", "low", "medium", "high", "safety-critical"]
PlatformStatus = Literal["yes", "likely", "host-dependent", "unknown", "no"]
ValidationStatus = Literal[
    "passed",
    "dependency_missing",
    "blocked",
    "failed",
    "skipped",
    "not_tested",
]


REQUIRED_PLATFORM_KEYS = (
    "windows_11_x64",
    "linux_x64",
    "linux_arm64",
    "macos_x64",
    "macos_arm64",
)


class EnvVarDefinition(BaseModel):
    """Metadata about an environment variable an MCP server needs.
    Matches tool_registry.models.EnvVarDefinition exactly.
    """

    name: str
    label: str
    description: str = ""
    required: bool = True
    secret: bool = False


class DependencySpec(BaseModel):
    """Dependencies required to run the MCP server."""

    system: List[str] = Field(default_factory=list)
    python: List[str] = Field(default_factory=list)
    node: List[str] = Field(default_factory=list)


class PlatformSupportRecord(BaseModel):
    status: PlatformStatus = "unknown"
    tested: bool = False
    notes: str = ""


class ValidationSummary(BaseModel):
    status: ValidationStatus = "not_tested"
    message: str = "Not yet validated in this environment"
    environment: Optional[str] = None
    missing_dependencies: List[str] = Field(default_factory=list)


def default_platform_support() -> dict[str, PlatformSupportRecord]:
    return {key: PlatformSupportRecord() for key in REQUIRED_PLATFORM_KEYS}


class CatalogEntry(BaseModel):
    """A registered engineering MCP server in the catalog."""

    id: str
    name: str
    vendor: str
    description: str
    domains: List[str]
    tags: List[str] = Field(default_factory=list)
    transport: Literal["stdio", "sse", "webmcp"]
    command: Union[List[str], str]
    source_url: Optional[str] = None
    image_url: Optional[str] = None
    locality: Literal["local", "remote"]
    weight: Literal["light", "medium", "heavy"]
    env_vars: List[EnvVarDefinition] = Field(default_factory=list)
    dependencies: DependencySpec = Field(default_factory=DependencySpec)
    aliases: List[str] = Field(default_factory=list)
    verification_state: VerificationState = "user_reported_url_needed"
    installability_tier: InstallabilityTier = "might_work"
    risk_level: RiskLevel = "low"
    deployment_mode: str = "unknown"
    platform_support: dict[str, PlatformSupportRecord] = Field(
        default_factory=default_platform_support
    )
    host_software_required: List[str] = Field(default_factory=list)
    credentials_required: List[str] = Field(default_factory=list)
    default_enabled: bool = True
    approval_gates: List[str] = Field(default_factory=list)
    validation_result: ValidationSummary = Field(default_factory=ValidationSummary)
    follow_up_url: Optional[str] = None
    install_blocked_reason: Optional[str] = None
