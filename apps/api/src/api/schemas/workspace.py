"""
Workspace request/response Pydantic models.

Extracted from apps/api/src/api/routers/workspace.py to keep the router thin.
All models used by workspace endpoints are defined here.
"""

import json
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    StrictInt,
    field_validator,
    model_validator,
)
from typing import Any, Dict, List, Literal, Optional

from workspace_service.workflow_sources import (
    WORKFLOW_SOURCE_MAX_BYTES,
    WorkflowSourceStorageError,
    validate_source_layout,
)


class WorkflowSourceExecutionSnapshot(BaseModel):
    """Compact recovery projection; full native evidence remains in the run file."""

    active_task_id: str | None = None
    completed_task_ids: list[str]
    event_count: int
    model_call_count: int
    tool_call_count: int
    tool_completed_count: int
    revision_count: int
    outputs: list[dict[str, Any]]
    last_progress: dict[str, Any] | None = None
    truncated: bool


class WorkflowSourceRecentRun(BaseModel):
    path: str
    status: str
    started_at: str | None = None
    completed_at: str | None = None
    source_digest: str | None = None
    error: str | None = None
    results: list[dict[str, Any]]
    last_event: dict[str, Any] | None = None
    review: dict[str, Any] | None = None
    approval: dict[str, Any] | None = None
    verification: dict[str, Any] | None = None
    capture_rights: dict[str, Any] | None = None
    run_id: str | None = None
    execution_ended_at: str | None = None
    source_matches_current: bool | None = None
    execution: WorkflowSourceExecutionSnapshot | None = None


class WorkflowSourceRecentRunsResponse(BaseModel):
    workspace_id: str
    workflow_path: str
    runs: list[WorkflowSourceRecentRun]


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


class _WorkflowSourceContentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: str = Field(max_length=WORKFLOW_SOURCE_MAX_BYTES)

    @field_validator("source")
    @classmethod
    def validate_source_utf8_bytes(cls, source: str) -> str:
        try:
            size_bytes = len(source.encode("utf-8"))
        except UnicodeEncodeError as error:
            raise ValueError("Workflow source must be valid UTF-8 text") from error
        if size_bytes > WORKFLOW_SOURCE_MAX_BYTES:
            raise ValueError(
                f"Workflow source exceeds the {WORKFLOW_SOURCE_MAX_BYTES}-byte limit"
            )
        return source


class WorkflowSourceCreateRequest(_WorkflowSourceContentRequest):
    session_id: str = Field(min_length=1, max_length=256)
    path: str = Field(min_length=1, max_length=256)


class WorkflowSourceUpdateRequest(_WorkflowSourceContentRequest):
    session_id: str = Field(min_length=1, max_length=256)
    path: str = Field(min_length=1, max_length=256)
    expected_storage_revision: int = Field(ge=1)
    expected_storage_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    semantic_change_validated: StrictBool
    layout: dict[str, Any] | None = None
    expected_layout_revision: StrictInt | None = Field(default=None, ge=0, lt=100_000)

    @field_validator("layout")
    @classmethod
    def validate_layout(cls, layout):
        if layout is None:
            return None
        try:
            return validate_source_layout(layout)
        except WorkflowSourceStorageError as error:
            raise ValueError(str(error)) from error

    @model_validator(mode="after")
    def require_layout_base(self):
        if self.layout is not None and self.expected_layout_revision is None:
            raise ValueError("A layout base revision is required when saving layout")
        return self


class WorkflowSourceResponse(BaseModel):
    workspace_id: str
    path: str
    storage_revision: int
    storage_digest: str
    definition_revision: int
    metadata_authority: Literal["wright_host"] = "wright_host"
    size_bytes: int
    source: str
    layout: dict[str, Any] | None = None
    layout_revision: int = 0
    layout_status: Literal["missing", "current", "stale"] = "missing"


class WorkflowSourceReadinessResponse(BaseModel):
    """Authoritative readiness for a stored workflow's template provenance."""

    state: Literal[
        "not_template",
        "reference",
        "setup_required",
        "ready",
        "verified",
        "unavailable",
    ]
    template_id: str | None = None
    template_version: str | None = None
    source_digest: str | None = None
    layout_digest: str | None = None
    definition_valid: bool | None = None
    configured: bool | None = None
    qualified: bool | None = None
    available: bool | None = None
    verified_run: bool | None = None
    facts: list[Dict[str, Any]] = Field(default_factory=list)
    blocking_reasons: list[str] = Field(default_factory=list)
    message: str | None = None


class EngineeringWorkflowTemplateListResponse(BaseModel):
    catalog_version: str
    templates: list[Dict[str, Any]]


class EngineeringWorkflowTemplateDetailResponse(BaseModel):
    template: Dict[str, Any]


class EngineeringWorkflowTemplateReadinessRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: str = Field(min_length=1, max_length=256)
    template_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")


class EngineeringWorkflowTemplateInstanceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: str = Field(min_length=1, max_length=256)
    template_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    expected_source_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    workflow_path: str = Field(
        pattern=r"^workflows/[a-z0-9][a-z0-9-]{0,62}\.workflow\.wflow$",
        max_length=96,
    )
    request_id: str = Field(
        pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]{7,127}$", max_length=128
    )


class EngineeringWorkflowTemplateInstanceResponse(WorkflowSourceResponse):
    workflow_id: str
    template: Dict[str, str]


class WorkflowApprovalDecisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: str = Field(min_length=1, max_length=256)
    subject_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    decision: Literal["approved", "changes_requested"]
    auto: bool = False
    reason: str | None = Field(default=None, max_length=2000)
    request_id: str = Field(
        pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]{7,127}$", max_length=128
    )


class WorkflowApprovalResumeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: str = Field(min_length=1, max_length=256)
    checkpoint_id: str = Field(min_length=1, max_length=128)
    subject_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    request_id: str = Field(
        pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]{7,127}$", max_length=128
    )


class WorkflowExternalActionReconcileRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: str = Field(min_length=1, max_length=256)
    subject_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    outcome: Literal["dispatched", "not_dispatched", "outcome_unknown"]
    evidence: Dict[str, Any] = Field(default_factory=dict)


class WorkflowApprovalCheckpointResponse(BaseModel):
    checkpoint_id: str
    workspace_id: str
    workflow_id: str
    run_id: str
    step_id: str
    action_kind: str
    subject: Dict[str, Any]
    subject_digest: str
    state: Literal[
        "pending", "approved", "changes_requested", "expired", "stale", "consumed"
    ]
    continuation: Dict[str, Any]
    actor: str | None = None
    reason: str | None = None
    created_at: int
    updated_at: int
    expires_at: int | None = None
    external_action: Dict[str, Any] | None = None
    execution_result: Dict[str, Any] | None = None


class WorkflowDemoCaptureRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: str = Field(min_length=1, max_length=256)
    run_log_path: str = Field(pattern=r"^runs/[A-Za-z0-9._/-]+\.json$", max_length=256)
    artifact_ids: list[str] = Field(min_length=1, max_length=12)
    caption: str = Field(min_length=1, max_length=8000)


class WorkflowDemoCaptureResponse(BaseModel):
    path: str
    size_bytes: int = Field(gt=0, le=80 * 1024 * 1024)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    manifest_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    artifact_count: int = Field(ge=1, le=12)
    published: Literal[False]


class WorkflowSourceRunRequest(BaseModel):
    """Run a saved workspace workflow without accepting a client execution plan."""

    model_config = ConfigDict(extra="forbid")

    session_id: str = Field(min_length=1, max_length=256)
    path: str = Field(min_length=1, max_length=256)
    expected_storage_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    integration_policy_digest: str | None = Field(
        default=None, pattern=r"^[0-9a-f]{64}$"
    )


class WorkflowSourceRunResponse(BaseModel):
    status: Literal["completed", "pending_review", "awaiting_approval"] = "completed"
    review: dict | None = None
    approval: WorkflowApprovalCheckpointResponse | None = None
    verification: dict | None = None
    capture_rights: dict | None = None
    run_id: str | None = None
    results: list[dict] = Field(default_factory=list)
    run_log_path: str | None = None
    workspace_id: str
    workflow_path: str
    workflow_title: str
    task_id: str
    task_title: str
    output_path: str
    output_bytes: int = Field(ge=0, le=100 * 1024 * 1024)
    outputs: list[dict] = Field(default_factory=list)
    steps: list[dict] = Field(default_factory=list)


class WorkflowArtifactReviewDecisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    session_id: str = Field(min_length=1, max_length=256)
    expected_package_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    decision: Literal["approved", "changes_requested"]
    actor: str | None = Field(
        default=None, max_length=200
    )  # Compatibility label, never reviewer authority.
    reason: str = Field(default="", max_length=2000)


class WorkflowInputFileResponse(BaseModel):
    path: str
    name: str


class WorkflowInputFilesResponse(BaseModel):
    workspace_id: str
    files: list[WorkflowInputFileResponse]


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


class RivetRunSummaryResponse(BaseModel):
    run_id: str
    workspace_id: str
    session_id: str
    workflow_id: str
    revision: int
    digest: str
    graph: str
    generation: int
    state: str
    started_at: str | None = None
    completed_at: str | None = None
    duration_ms: int | None = None
    reason_code: str | None = None
    trace_id: str | None = None
    latest_sequence: int = 0
    has_outputs: bool = False
    has_diagnostic: bool = False
    output_truncated: bool = False
    output_redaction_count: int = 0


class RivetRunProgressResponse(BaseModel):
    phase: str
    current_step_id: str | None = None
    completed_steps: int = 0
    total_steps: int = 0
    last_sequence: int = 0
    updated_at: str | None = None


class RivetRunResultResponse(BaseModel):
    result_id: str
    name: str
    origin: str
    kind: str
    data_type: str = "unknown"
    evidence_state: str = "unavailable"
    value: Any = None
    preview: str
    complete: bool
    truncation_reason: str | None = None
    original_bytes: int
    retained_bytes: int
    digest: str
    redaction_count: int = 0
    artifact: Dict[str, Any] | None = None


class RivetRunStepResponse(BaseModel):
    step_id: str
    sequence: int
    node_id: str | None = None
    node_type: str | None = None
    label: str
    kind: str
    qualified_tool_name: str | None = None
    request_id: str | None = None
    trace_id: str | None = None
    state: str
    started_at: str | None = None
    completed_at: str | None = None
    duration_ms: int | None = None
    reason_code: str | None = None
    inputs: List[RivetRunResultResponse] = Field(default_factory=list)
    outputs: List[RivetRunResultResponse] = Field(default_factory=list)
    input_state: str = "unavailable"
    output_state: str = "unavailable"
    result: Dict[str, Any] | None = None
    artifacts: List[Dict[str, Any]] = Field(default_factory=list)
    redaction_count: int = 0
    complete: bool = True


class RivetRunDiagnosticResponse(BaseModel):
    code: str
    summary: str
    recovery_action: str
    failed_step_id: str | None = None
    failed_node_id: str | None = None
    failed_node_label: str | None = None
    qualified_tool_name: str | None = None
    trace_id: str | None = None
    full_rerun_available: bool
    partial_retry_available: bool = False
    residue_possible: bool = False


class RivetRunCompletenessResponse(BaseModel):
    inputs_complete: bool = False
    outputs_complete: bool
    steps_complete: bool
    events_complete: bool
    evidence_available: bool
    reasons: List[str] = Field(default_factory=list)


class RivetRunInspectionResponse(BaseModel):
    schema_version: Literal[1]
    run: RivetRunSummaryResponse
    progress: RivetRunProgressResponse
    events: List[Dict[str, Any]] = Field(default_factory=list)
    run_inputs: List[RivetRunResultResponse] = Field(default_factory=list)
    inputs_state: str = "not-retained"
    steps: List[RivetRunStepResponse] = Field(default_factory=list)
    final_outputs: List[RivetRunResultResponse] = Field(default_factory=list)
    diagnostic: RivetRunDiagnosticResponse | None = None
    completeness: RivetRunCompletenessResponse


class RivetRecentRunsResponse(BaseModel):
    workflow_id: str
    current_revision: int
    runs: List[RivetRunSummaryResponse] = Field(default_factory=list)


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
    artifact_producer: Dict[str, Any] | None = None
    artifact_producer_digest: str | None = Field(
        default=None, pattern=r"^[a-f0-9]{64}$"
    )


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
    artifact_producer: Dict[str, Any] | None = None
    artifact_producer_digest: str | None = Field(
        default=None, pattern=r"^[a-f0-9]{64}$"
    )
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


class EngineeringProviderEvidenceResponse(BaseModel):
    schema_version: Literal["1.0"]
    provider_kind: Literal["mcp", "engineering_model"]
    provider_id: str
    capability_id: str
    resource_class: Literal["small", "medium", "large", "external"]
    evidence: Dict[str, Any]


class EngineeringScenarioCapabilityResponse(BaseModel):
    node_id: str
    requested_tool: str | None = None
    selected_tool: str | None = None
    binding_digest: str | None = None
    blockers: list[str]
    provider: EngineeringProviderEvidenceResponse | None = None
    provider_evidence_digest: str | None = Field(default=None, pattern="^[a-f0-9]{64}$")


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
    capabilities: list[EngineeringScenarioCapabilityResponse]
    environment: Dict[str, Any]
    blockers: list[EngineeringScenarioBlockerResponse]
    expires_at: str


class EngineeringScenarioStartRequest(BaseModel):
    session_id: str
    manifest_digest: str = Field(pattern="^[a-f0-9]{64}$")
    workflow_revision: int = Field(ge=1)
    workflow_digest: str = Field(pattern="^[a-f0-9]{64}$")
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
    advisory: Dict[str, Any] | None = None
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
