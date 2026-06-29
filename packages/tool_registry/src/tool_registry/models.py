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


class PlatformSupportRecord(BaseModel):
    status: PlatformStatus = "unknown"
    tested: bool = False
    notes: str = ""


class ValidationSummary(BaseModel):
    status: ValidationStatus = "not_tested"
    message: str = "Not yet validated in this environment"
    environment: Optional[str] = None
    missing_dependencies: List[str] = Field(default_factory=list)


class EnvVarDefinition(BaseModel):
    """Metadata about an environment variable an MCP server needs."""
    name: str           # Variable name (e.g., "ONSHAPE_API_KEY")
    label: str          # Human-readable label (e.g., "Access Key")
    description: str = ""  # Help text
    required: bool = True
    secret: bool = False   # If True, value should be masked in UI


class McpServer(BaseModel):
    server_id: str
    name: str
    type: Literal["stdio", "sse", "webmcp"]
    command: Optional[Union[List[str], str]] = None
    is_active: bool
    is_installed: bool = False
    status: Literal["active", "inactive", "error"]
    error_message: Optional[str] = None
    category: str = "utilities"
    created_at: int
    updated_at: int
    image_url: Optional[str] = None
    description: Optional[str] = None
    source_url: Optional[str] = None
    installed_version: Optional[str] = None
    env_vars: Optional[Union[list[EnvVarDefinition], dict[str, str]]] = None
    instructions: Optional[str] = None
    # Dynamic field populated by API — indicates which env vars have saved values
    credentials_configured: Optional[dict[str, bool]] = None
    verification_state: VerificationState = "user_reported_url_needed"
    installability_tier: InstallabilityTier = "might_work"
    risk_level: RiskLevel = "low"
    deployment_mode: str = "unknown"
    platform_support: dict[str, PlatformSupportRecord] = Field(default_factory=dict)
    host_software_required: List[str] = Field(default_factory=list)
    credentials_required: List[str] = Field(default_factory=list)
    default_enabled: bool = True
    approval_gates: List[str] = Field(default_factory=list)
    validation_result: ValidationSummary = Field(default_factory=ValidationSummary)
    follow_up_url: Optional[str] = None
    install_blocked_reason: Optional[str] = None


class McpServerCreate(BaseModel):
    name: str
    type: Literal["stdio", "sse", "webmcp"]
    command: Optional[Union[List[str], str]] = None
    category: str = "utilities"
    image_url: Optional[str] = None
    description: Optional[str] = None
    source_url: Optional[str] = None
    installed_version: Optional[str] = None
    env_vars: Optional[Union[list[EnvVarDefinition], dict[str, str]]] = None
    instructions: Optional[str] = None
    verification_state: VerificationState = "user_reported_url_needed"
    installability_tier: InstallabilityTier = "might_work"
    risk_level: RiskLevel = "low"
    deployment_mode: str = "unknown"
    platform_support: dict[str, PlatformSupportRecord] = Field(default_factory=dict)
    host_software_required: List[str] = Field(default_factory=list)
    credentials_required: List[str] = Field(default_factory=list)
    default_enabled: bool = True
    approval_gates: List[str] = Field(default_factory=list)
    validation_result: ValidationSummary = Field(default_factory=ValidationSummary)
    follow_up_url: Optional[str] = None
    install_blocked_reason: Optional[str] = None


class McpServerUpdate(BaseModel):
    is_active: Optional[bool] = None
    status: Optional[Literal["active", "inactive", "error"]] = None
    error_message: Optional[str] = None
    env_vars: Optional[Union[list[EnvVarDefinition], dict[str, str]]] = None
    instructions: Optional[str] = None
    verification_state: Optional[VerificationState] = None
    installability_tier: Optional[InstallabilityTier] = None
    risk_level: Optional[RiskLevel] = None
    deployment_mode: Optional[str] = None
    platform_support: Optional[dict[str, PlatformSupportRecord]] = None
    host_software_required: Optional[List[str]] = None
    credentials_required: Optional[List[str]] = None
    default_enabled: Optional[bool] = None
    approval_gates: Optional[List[str]] = None
    validation_result: Optional[ValidationSummary] = None
    follow_up_url: Optional[str] = None
    install_blocked_reason: Optional[str] = None


class McpTool(BaseModel):
    tool_id: str
    server_id: str
    name: str
    description: Optional[str] = None
    input_schema: dict = Field(default_factory=dict)
    is_enabled: bool
    created_at: int

