"""
Workspace request/response Pydantic models.

Extracted from apps/api/src/api/routers/workspace.py to keep the router thin.
All models used by workspace endpoints are defined here.
"""

import json
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Literal, Optional


#  File Operations
class WorkspaceNodeResponse(BaseModel):
    name: str
    path: str
    type: str
    size: Optional[int] = None
    last_modified: int
    git_status: str = "Clean"
    children: Optional[List[Dict[str, Any]]] = None


class WorkspaceTreeResponse(BaseModel):
    workspace: WorkspaceNodeResponse


class FileCreateRequest(BaseModel):
    session_id: str
    path: str
    type: str  # 'file' | 'directory'


class FileMoveRequest(BaseModel):
    session_id: str
    source_path: str
    destination_path: str


class FileMoveResponse(BaseModel):
    success: bool
    source_path: str
    destination_path: str


class FileContentSaveRequest(BaseModel):
    session_id: str
    path: str
    content: str


class FileContentSaveResponse(BaseModel):
    success: bool


class WorkflowCreateRequest(BaseModel):
    session_id: str
    slug: str
    project: str
    datasets: Dict[str, str] = Field(default_factory=dict)


class WorkflowSaveRequest(BaseModel):
    session_id: str
    expected_revision: int
    project: str
    datasets: Dict[str, str] = Field(default_factory=dict)


class WorkflowResponse(BaseModel):
    workflow_id: str
    slug: str
    revision: int
    etag: str


class WorkflowDocumentResponse(WorkflowResponse):
    project: str
    datasets: Dict[str, str]


class WorkflowTemplateResponse(BaseModel):
    template_id: str
    title: str
    description: str
    kind: Literal["starter", "advanced", "example"]
    requirements: List[str] = Field(default_factory=list)


class WorkflowTemplateListResponse(BaseModel):
    templates: List[WorkflowTemplateResponse]


class WorkflowTemplateInstantiateRequest(BaseModel):
    session_id: str
    slug: str


class WorkflowGraphNodeResponse(BaseModel):
    node_id: str
    node_type: str | None = None
    title: str | None = None
    data: Dict[str, Any] = Field(default_factory=dict)
    outgoing_connections: List[str] = Field(default_factory=list)


class WorkflowGraphSummaryResponse(BaseModel):
    graph_id: str
    name: str | None = None
    main: bool
    node_count: int
    nodes: List[WorkflowGraphNodeResponse] = Field(default_factory=list)


class WorkflowGraphResponse(WorkflowResponse):
    graph: WorkflowGraphSummaryResponse
    issues: List[Dict[str, Any]] = Field(default_factory=list)


class WorkflowGraphActionRequest(BaseModel):
    session_id: str
    action: Literal[
        "add_node",
        "edit_node",
        "delete_node",
        "connect_ports",
        "disconnect_ports",
        "save_revision",
    ]
    expected_revision: int = Field(ge=1)
    graph_id: str | None = None
    node_id: str | None = None
    source_node_id: str | None = None
    source_port: str | None = None
    target_node_ref: str | None = None
    target_port: str | None = None
    connection: str | None = None
    visual_data: str | None = None
    node: Dict[str, Any] | None = None
    node_patch: Dict[str, Any] | None = None
    data: Dict[str, Any] | None = None
    project: str | None = None
    datasets: Dict[str, str] | None = None


class WorkflowRunnerStatusResponse(BaseModel):
    availability: str
    generation: int
    detail: str | None = None


class WorkflowRunStartRequest(BaseModel):
    session_id: str
    expected_generation: int | None = Field(default=None, ge=1)
    expected_revision: int = Field(ge=1)
    expected_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    expected_review_digest: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    binding_set_digest: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    graph: str | None = Field(default=None, max_length=256)
    inputs: Dict[str, Any] = Field(default_factory=dict)
    context: Dict[str, Any] = Field(default_factory=dict)
    timeout_seconds: float | None = Field(default=None, ge=1, le=300)


class WorkflowRunCancelRequest(BaseModel):
    session_id: str
    generation: int = Field(ge=1)


class WorkflowRunResponse(BaseModel):
    run_id: str
    workspace_id: str
    session_id: str
    workflow_id: str
    revision: int
    digest: str | None = None
    graph: str | None = None
    generation: int
    state: str
    reason: str | None = None
    outputs: Dict[str, Any] | None = None
    duration_ms: int | None = None
    output_truncated: bool = False
    manifest: Dict[str, Any] | None = None


class RivetCallApprovalResponse(BaseModel):
    approval_id: str
    run_id: str
    node_id: str
    qualified_tool_name: str
    binding_digest: str
    argument_digest: str
    argument_summary: Dict[str, Any]
    required_gates: list[str]
    state: str
    expires_at: str
    approval_digest: str
    decided_by: str | None = None
    decision_reason: str | None = None


class RivetCallApprovalListResponse(BaseModel):
    approvals: list[RivetCallApprovalResponse]


class RivetCallApprovalDecisionRequest(BaseModel):
    session_id: str
    expected_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    decision: Literal["approved", "denied"]
    actor: str = Field(min_length=1, max_length=200)
    reason: str | None = Field(default=None, max_length=512)


class WorkflowReviewRequest(BaseModel):
    session_id: str
    state: Literal["approved", "rejected"]
    reviewer: str = Field(min_length=1, max_length=200)
    expected_digest: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    graph: str | None = Field(default=None, max_length=256)
    binding_set_digest: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")


class WorkflowReviewResponse(BaseModel):
    workflow_id: str
    slug: str
    revision: int
    etag: str
    review_state: str | None = None
    reviewer: str | None = None
    reviewed_at: int | None = None
    workflow_digest: str | None = None
    graph_id: str | None = None
    binding_set_id: str | None = None
    binding_set_digest: str | None = None
    policy_snapshot_digest: str | None = None
    review_digest: str | None = None
    stale_reasons: list[str] = Field(default_factory=list)


class RivetMcpRequirementResponse(BaseModel):
    graph_id: str
    node_id: str
    node_type: str
    static_tool_name: str | None = None


class RivetMcpCapabilityResponse(BaseModel):
    qualified_tool_name: str
    server_id: str
    tool_name: str
    title: str
    description: str
    server_revision: str
    capability_digest: str
    validation_evidence_id: str
    workspace_grant_digest: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any] | None = None
    schema_digest: str
    annotations: Dict[str, Any]
    required_approvals: list[str]
    compatibility: str
    binding_eligible: bool
    blocking_reasons: list[str]


class RivetMcpCapabilitiesResponse(BaseModel):
    workflow_id: str
    slug: str
    revision: int
    etag: str
    graph_id: str
    snapshot_digest: str
    policy_snapshot_digest: str
    requirements: list[RivetMcpRequirementResponse]
    issues: list[dict]
    capabilities: list[RivetMcpCapabilityResponse]
    next_after: int | None = None


class RivetMcpBindingSelectionRequest(BaseModel):
    node_id: str = Field(min_length=1, max_length=256)
    qualified_tool_name: str = Field(
        min_length=3,
        max_length=257,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}__[A-Za-z0-9][A-Za-z0-9._-]{0,127}$",
    )
    units_policy: Dict[str, Any] = Field(default_factory=dict)
    material_defaults: Dict[str, Any] = Field(default_factory=dict)


class RivetMcpBindingPreviewRequest(BaseModel):
    session_id: str
    expected_revision: int = Field(ge=1)
    expected_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    graph: str | None = Field(default=None, max_length=256)
    selections: list[RivetMcpBindingSelectionRequest] = Field(
        default_factory=list, max_length=1000
    )


class RivetMcpBindingResponse(BaseModel):
    node_id: str
    node_handle: str | None = None
    selected_tool: str | None = None
    binding_digest: str | None = None
    server_id: str | None = None
    server_revision: str | None = None
    schema_digest: str | None = None
    validation_evidence_id: str | None = None
    workspace_grant_digest: str | None = None
    risk: Dict[str, Any] | None = None
    units_policy: Dict[str, Any] | None = None
    material_defaults: Dict[str, Any] | None = None
    blockers: list[str] = Field(default_factory=list)


class RivetMcpBindingPreviewResponse(BaseModel):
    workflow_id: str
    slug: str
    revision: int
    etag: str
    graph_id: str
    snapshot_digest: str
    policy_snapshot_digest: str
    binding_set_id: str | None = None
    binding_set_digest: str | None = None
    expires_at: str
    ready: bool
    bindings: list[RivetMcpBindingResponse]


class WorkflowOperationsListResponse(BaseModel):
    workflows: list[WorkflowReviewResponse]


class WorkflowRunHistoryResponse(BaseModel):
    run_id: str
    events: list[dict]


class WorkflowRunEvidenceResponse(BaseModel):
    schema_version: Literal[1]
    run_id: str
    manifest: Dict[str, Any]
    bindings: list[dict]
    child_calls: list[dict]
    approvals: list[dict]
    artifacts: list[dict]
    timeline: list[dict]
    reproducibility: Dict[str, Any]
    accounting: Dict[str, Any]


class EngineeringScenarioCatalogEntryResponse(BaseModel):
    scenario_id: str
    revision: int
    title: str
    summary: str
    domains: list[str]
    tier: str
    resource_class: str
    expected_duration_seconds: int
    manifest_digest: str


class EngineeringScenarioListResponse(BaseModel):
    scenarios: list[EngineeringScenarioCatalogEntryResponse]


class EngineeringScenarioDetailResponse(BaseModel):
    manifest: Dict[str, Any]
    manifest_digest: str


class EngineeringScenarioPreflightRequest(BaseModel):
    session_id: str
    allow_tier2: bool = False
    platform: str | None = Field(default=None, max_length=40)


class EngineeringScenarioBlockerResponse(BaseModel):
    code: str
    message: str
    recovery: str


class EngineeringScenarioPreflightResponse(BaseModel):
    preflight_id: str
    scenario_id: str
    scenario_revision: int
    manifest_digest: str
    workflow_slug: str
    workflow_revision: int | None = None
    workflow_digest: str | None = None
    graph_id: str
    binding_set_digest: str | None = None
    state: Literal["ready", "blocked", "skipped"]
    capabilities: list[Dict[str, Any]]
    environment: Dict[str, Any]
    blockers: list[EngineeringScenarioBlockerResponse]
    expires_at: str


class EngineeringScenarioStartRequest(BaseModel):
    session_id: str
    manifest_digest: str = Field(pattern="^[a-f0-9]{64}$")
    workflow_revision: int = Field(ge=1)
    workflow_digest: str = Field(pattern="^[a-f0-9]{64}$")
    review_digest: str = Field(pattern="^[a-f0-9]{64}$")
    binding_set_digest: str = Field(pattern="^[a-f0-9]{64}$")
    seed: int = Field(default=0, ge=0, le=2147483647)


class EngineeringScenarioStartResponse(BaseModel):
    scenario_run_id: str
    workflow_run: WorkflowRunResponse
    state: Literal["running"]


class EngineeringScenarioReportResponse(BaseModel):
    scenario_run_id: str
    workflow_run_id: str
    workspace_id: str
    session_id: str
    scenario_id: str
    scenario_revision: int
    manifest_digest: str
    workflow_digest: str
    binding_set_digest: str | None = None
    state: str
    identity: Dict[str, Any]
    artifacts: list[Dict[str, Any]]
    environment: Dict[str, Any]
    cleanup_state: str
    residue: Dict[str, Any]
    assertions: list[Dict[str, Any]]
    report_digest: str | None = None


class EngineeringScenarioCancelRequest(BaseModel):
    session_id: str


class EngineeringScenarioCompareResponse(BaseModel):
    strictly_reproducible: bool
    differences: list[Dict[str, Any]]
    assertion_changes: list[Dict[str, Any]]


class WorkflowEditorAvailabilityResponse(BaseModel):
    availability: str
    detail: str | None = None


class WorkflowEditorSurfaceRequest(BaseModel):
    session_id: str


class WorkflowEditorSurfaceResponse(WorkflowEditorAvailabilityResponse):
    manifest: Dict[str, Any] | None = None


class BrepPanelRequest(BaseModel):
    session_id: str


class BrepPanelResponse(BaseModel):
    server_id: str
    control_url: str
    module_url: str
    connected: bool


class BrepToolRequest(BaseModel):
    session_id: str
    tool_name: str = Field(min_length=1, max_length=256)
    arguments: Dict[str, Any] = Field(default_factory=dict)


class WorkflowEditorBootstrapRequest(BaseModel):
    session_id: str


class WorkflowEditorBootstrapResponse(WorkflowEditorAvailabilityResponse):
    grant_id: str | None = None
    workflow_id: str | None = None
    revision: int | None = None
    etag: str | None = None
    expires_at: str | None = None


class WorkflowEditorReadRequest(BaseModel):
    session_id: str
    grant_id: str


class WorkflowEditorSaveRequest(WorkflowEditorReadRequest):
    expected_revision: int = Field(ge=1)
    project: str
    datasets: Dict[str, str] = Field(default_factory=dict)


class WorkflowDeleteRequest(BaseModel):
    session_id: str
    expected_revision: int


class WorkflowRecoveryRequest(BaseModel):
    session_id: str
    slug: str


class WorkflowRenameRequest(BaseModel):
    session_id: str
    expected_revision: int
    slug: str


#  Git Operations
class GitStatusItem(BaseModel):
    path: str
    git_status: str
    staged: bool
    file_size: Optional[int] = None


class GitStatusResponse(BaseModel):
    branch_name: str
    is_clean: bool
    changes: List[GitStatusItem]


class GitDiffResponse(BaseModel):
    path: str
    diff: str


class GitRevertRequest(BaseModel):
    session_id: str
    path: str


class GitRevertResponse(BaseModel):
    success: bool
    path: str


class GitCommitRequest(BaseModel):
    session_id: str
    message: str


class GitCommitResponse(BaseModel):
    success: bool
    commit_hash: str
    message: str
    timestamp: int


class GitCommitInfo(BaseModel):
    commit_hash: str
    message: str
    author: str
    timestamp: int


class GitHistoryResponse(BaseModel):
    commits: List[GitCommitInfo]


class GitPushPullRequest(BaseModel):
    session_id: str


class GitPushPullResponse(BaseModel):
    success: bool
    message: str


#  Workspace Config
class WorkspaceConfigRequest(BaseModel):
    session_id: str
    git_remote_url: Optional[str] = None
    git_username: Optional[str] = None
    git_token: Optional[str] = None
    workspace_prompt: Optional[str] = None
    git_large_file_threshold: Optional[int] = None


class WorkspaceConfigResponse(BaseModel):
    success: bool
    workspace_id: str


class WorkspaceConfigGetResponse(BaseModel):
    workspace_id: str
    git_remote_url: Optional[str] = None
    git_username: Optional[str] = None
    has_token: bool
    workspace_path: Optional[str] = None
    workspace_prompt: Optional[str] = None
    git_large_file_threshold: Optional[int] = None


#  Workspace Tools
class WorkspaceToolsGetResponse(BaseModel):
    session_id: str
    enabled_tools: List[str]


class WorkspaceToolToggleRequest(BaseModel):
    session_id: str
    server_id: str
    is_enabled: bool


class WorkspaceToolToggleResponse(BaseModel):
    success: bool
    session_id: str
    server_id: str
    is_enabled: bool


#  Workspace CRUD & Listing
class WorkspaceListEntry(BaseModel):
    workspace_id: str
    session_id: str
    workspace_name: Optional[str] = None
    local_path: str
    git_remote_url: Optional[str] = None
    git_username: Optional[str] = None
    enabled_tools: Optional[List[str]] = None
    updated_at: int


class WorkspaceListResponse(BaseModel):
    workspaces: List[WorkspaceListEntry]


class WorkspaceCreateRequest(BaseModel):
    name: str
    local_path: Optional[str] = None


class WorkspaceActivateRequest(BaseModel):
    session_id: str


class WorkspaceActivateResponse(BaseModel):
    success: bool
    session_id: str
    workspace_path: str


class WorkspaceSessionInfo(BaseModel):
    session_id: str
    title: Optional[str] = None
    created_at: int
    updated_at: int
    message_count: int = 0


class WorkspaceSessionsResponse(BaseModel):
    workspace_id: str
    sessions: List[WorkspaceSessionInfo]


class WorkspaceSessionCreateResponse(BaseModel):
    workspace_id: str
    session_id: str
    title: Optional[str] = None
    created_at: int


class WorkspaceSessionSelectRequest(BaseModel):
    session_id: str


class WorkspaceSessionSelectResponse(BaseModel):
    success: bool
    workspace_id: str
    session_id: str


class WorkspaceToolsByIdResponse(BaseModel):
    workspace_id: str
    enabled_tools: List[str]


class WorkspaceToolToggleByIdRequest(BaseModel):
    server_id: str
    is_enabled: bool


class WorkspaceToolToggleByIdResponse(BaseModel):
    success: bool
    workspace_id: str
    server_id: str
    is_enabled: bool


class ContextSaveRequest(BaseModel):
    context_data: dict


class DefaultWorkspaceDirResponse(BaseModel):
    default_dir: str


class WorkspaceSessionUpdateRequest(BaseModel):
    session_id: str


class GitBranchRequest(BaseModel):
    session_id: str
    branch_name: str
    create: bool = False


class GitMergeRequest(BaseModel):
    session_id: str
    branch_name: str


#  Utility functions
def parse_enabled_tools(tools_str: Optional[str]) -> Optional[List[str]]:
    """Parse a JSON-encoded list of enabled tool names/IDs from the database."""
    if not tools_str:
        return None
    try:
        return json.loads(tools_str)
    except Exception:
        return None


def serialize_workspace(w: dict) -> WorkspaceListEntry:
    """Convert a raw workspace database row dict to a WorkspaceListEntry."""
    return WorkspaceListEntry(
        workspace_id=w["workspace_id"],
        session_id=w["session_id"],
        workspace_name=w.get("workspace_name"),
        local_path=w["local_path"],
        git_remote_url=w.get("git_remote_url"),
        git_username=w.get("git_username"),
        enabled_tools=parse_enabled_tools(w.get("enabled_tools")),
        updated_at=w["updated_at"],
    )


class RunningMcpInfo(BaseModel):
    name: str
    status: str
    error_message: Optional[str] = None


class WorkspaceMcpStatusResponse(BaseModel):
    status: str
    message: str
    running_mcps: Optional[List[RunningMcpInfo]] = None
    workspace_id: Optional[str] = None


class FileBackupRequest(BaseModel):
    session_id: str
    path: str
    content: str


class FileBackupResponse(BaseModel):
    success: bool
    backup_id: str


class FileBackupDeleteRequest(BaseModel):
    session_id: str
    backup_id: str


class FileRunRequest(BaseModel):
    session_id: str
    path: str


class FileRunResponse(BaseModel):
    success: bool
    stdout: str
    stderr: str
    exit_code: int
