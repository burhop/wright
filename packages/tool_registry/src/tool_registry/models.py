from collections.abc import Mapping
from typing import Any, List, Literal, Optional, Union

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


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

    name: str  # Variable name (e.g., "ONSHAPE_API_KEY")
    label: str  # Human-readable label (e.g., "Access Key")
    description: str = ""  # Help text
    required: bool = True
    secret: bool = False  # If True, value should be masked in UI


class McpServer(BaseModel):
    server_id: str
    name: str
    type: Literal["stdio", "sse", "webmcp"]
    transport_variant: Literal["stdio", "streamable_http", "sse", "webmcp"] | None = (
        None
    )
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
    launch_env: dict[str, str] = Field(default_factory=dict)
    instructions: Optional[str] = None
    # Dynamic field populated by API  indicates which env vars have saved values
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
    transport_variant: Literal["stdio", "streamable_http", "sse", "webmcp"] | None = (
        None
    )
    command: Optional[Union[List[str], str]] = None
    category: str = "utilities"
    image_url: Optional[str] = None
    description: Optional[str] = None
    source_url: Optional[str] = None
    installed_version: Optional[str] = None
    env_vars: Optional[Union[list[EnvVarDefinition], dict[str, str]]] = None
    launch_env: dict[str, str] = Field(default_factory=dict)
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
    transport_variant: Optional[
        Literal["stdio", "streamable_http", "sse", "webmcp"]
    ] = None
    status: Optional[Literal["active", "inactive", "error"]] = None
    error_message: Optional[str] = None
    env_vars: Optional[Union[list[EnvVarDefinition], dict[str, str]]] = None
    launch_env: Optional[dict[str, str]] = None
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


McpUiVisibility = Literal["model", "app"]


class McpUiToolMetadata(BaseModel):
    """Canonical, security-relevant projection of upstream MCP Apps tool metadata."""

    resource_uri: Optional[str] = None
    visibility: frozenset[McpUiVisibility] = Field(
        default_factory=lambda: frozenset({"model", "app"})
    )
    accepted_deprecated_resource_uri: bool = False
    upstream: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_upstream(cls, metadata: Mapping[str, Any] | None) -> "McpUiToolMetadata":
        upstream = dict(metadata or {})
        raw_ui = upstream.get("ui")
        ui = dict(raw_ui) if isinstance(raw_ui, Mapping) else {}
        canonical = ui.get("resourceUri")
        deprecated = upstream.get("ui/resourceUri")
        selected = canonical if canonical is not None else deprecated
        if selected is not None and (
            not isinstance(selected, str) or not selected.startswith("ui://")
        ):
            raise ValueError("MCP UI resource URI must use ui://")
        raw_visibility = ui.get("visibility", ("model", "app"))
        if not isinstance(raw_visibility, (list, tuple, set, frozenset)):
            raise ValueError("MCP UI visibility must be an array")
        visibility = frozenset(str(item) for item in raw_visibility)
        if not visibility.issubset({"model", "app"}):
            raise ValueError("MCP UI visibility contains an unsupported scope")
        return cls(
            resource_uri=selected,
            visibility=visibility,
            accepted_deprecated_resource_uri=(
                canonical is None and deprecated is not None
            ),
            upstream=upstream,
        )

    @property
    def model_visible(self) -> bool:
        return "model" in self.visibility

    @property
    def app_visible(self) -> bool:
        return "app" in self.visibility


class McpUiResourceMetadata(BaseModel):
    """Merged MCP Apps resource metadata with content-item precedence."""

    ui: dict[str, Any] = Field(default_factory=dict)
    upstream: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def merge(
        cls,
        listing_metadata: Mapping[str, Any] | None,
        content_metadata: Mapping[str, Any] | None,
    ) -> "McpUiResourceMetadata":
        listing = dict(listing_metadata or {})
        content = dict(content_metadata or {})
        listed_ui = listing.get("ui")
        content_ui = content.get("ui")
        merged_ui = dict(listed_ui) if isinstance(listed_ui, Mapping) else {}
        if isinstance(content_ui, Mapping):
            merged_ui.update(content_ui)
        merged = {**listing, **content}
        if merged_ui:
            merged["ui"] = merged_ui
        return cls(ui=merged_ui, upstream=merged)


class McpTool(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    tool_id: str
    server_id: str
    name: str
    title: Optional[str] = None
    description: Optional[str] = None
    input_schema: dict = Field(default_factory=dict)
    output_schema: Optional[dict] = None
    annotations: dict = Field(default_factory=dict)
    meta: dict[str, Any] = Field(
        default_factory=dict,
        validation_alias=AliasChoices("_meta", "meta"),
        serialization_alias="_meta",
    )
    is_enabled: bool
    created_at: int

    @property
    def ui(self) -> McpUiToolMetadata:
        return McpUiToolMetadata.from_upstream(self.meta)
