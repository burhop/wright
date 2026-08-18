"""
Workspace router — thin HTTP handlers only.

All Pydantic models are in api.schemas.workspace.
All business logic is owned by workspace_service application operations.
All handlers are decorated with @traced for OTel span creation.
"""

import asyncio
import json
import time

import structlog
from fastapi import APIRouter, Depends, Query, HTTPException, status, Response, Request
from fastapi.responses import FileResponse, JSONResponse
from typing import Optional

from agent_adapters import BaseAgentEngine
from agent_adapters.hermes_gateway import hermes_config_paths
from core.tracing import traced
from api.config import (
    DATABASE_PATH,
    api_mcp_autostart_enabled,
    get_workspace_surface_settings,
    rivet_editor_enabled,
    rivet_runner_enabled,
    rivet_workflow_operations_enabled,
    rivet_workflows_enabled,
)
from api.routers.agent import get_agent_engine
from api.composition import surface_application, workspace_service
from workspace_service import (
    WorkspaceConflictError,
    WorkspaceInvalidRequestError,
    WorkspaceNotFoundError,
    WorkspaceProtectedPathError,
    WorkspaceService,
    WorkspaceServiceError,
    default_workspace_parent_dir,
)
from api.schemas.workspace import (
    WorkspaceNodeResponse,
    WorkspaceTreeResponse,
    FileCreateRequest,
    FileMoveRequest,
    FileMoveResponse,
    FileContentSaveRequest,
    FileContentSaveResponse,
    GitStatusItem,
    GitStatusResponse,
    GitDiffResponse,
    GitRevertRequest,
    GitRevertResponse,
    GitCommitRequest,
    GitCommitResponse,
    GitCommitInfo,
    GitHistoryResponse,
    WorkspaceConfigRequest,
    WorkspaceConfigResponse,
    WorkspaceConfigGetResponse,
    GitPushPullRequest,
    GitPushPullResponse,
    GitBranchRequest,
    GitMergeRequest,
    WorkspaceToolsGetResponse,
    WorkspaceToolToggleRequest,
    WorkspaceToolToggleResponse,
    WorkspaceMcpStatusResponse,
    RunningMcpInfo,
    WorkspaceListEntry,
    WorkspaceListResponse,
    WorkspaceCreateRequest,
    WorkspaceActivateRequest,
    WorkspaceActivateResponse,
    ContextSaveRequest,
    FileBackupRequest,
    FileBackupResponse,
    FileBackupDeleteRequest,
    DefaultWorkspaceDirResponse,
    serialize_workspace,
    WorkspaceSessionUpdateRequest,
    WorkspaceSessionInfo,
    WorkspaceSessionsResponse,
    WorkspaceSessionCreateResponse,
    WorkspaceSessionSelectRequest,
    WorkspaceSessionSelectResponse,
    WorkspaceToolsByIdResponse,
    WorkspaceToolToggleByIdRequest,
    WorkspaceToolToggleByIdResponse,
    FileRunRequest,
    FileRunResponse,
    WorkflowCreateRequest,
    WorkflowResponse,
    WorkflowDocumentResponse,
    WorkflowTemplateInstantiateRequest,
    WorkflowTemplateListResponse,
    WorkflowTemplateResponse,
    WorkflowGraphActionRequest,
    WorkflowGraphResponse,
    WorkflowGraphSummaryResponse,
    WorkflowSaveRequest,
    WorkflowDeleteRequest,
    WorkflowRecoveryRequest,
    WorkflowRenameRequest,
    WorkflowRunnerStatusResponse,
    WorkflowRunCancelRequest,
    WorkflowRunResponse,
    WorkflowRunStartRequest,
    RivetCallApprovalDecisionRequest,
    RivetCallApprovalListResponse,
    RivetCallApprovalResponse,
    WorkflowReviewRequest,
    WorkflowReviewResponse,
    RivetMcpCapabilitiesResponse,
    RivetMcpCapabilityResponse,
    RivetMcpRequirementResponse,
    RivetMcpBindingPreviewRequest,
    RivetMcpBindingPreviewResponse,
    RivetMcpBindingResponse,
    WorkflowOperationsListResponse,
    WorkflowRunHistoryResponse,
    WorkflowRunEvidenceResponse,
    EngineeringScenarioCatalogEntryResponse,
    EngineeringScenarioListResponse,
    EngineeringScenarioDetailResponse,
    EngineeringScenarioPreflightRequest,
    EngineeringScenarioPreflightResponse,
    EngineeringScenarioBlockerResponse,
    EngineeringScenarioStartRequest,
    EngineeringScenarioStartResponse,
    EngineeringScenarioReportResponse,
    EngineeringScenarioCancelRequest,
    EngineeringScenarioCompareResponse,
    WorkflowEditorAvailabilityResponse,
    WorkflowEditorSurfaceRequest,
    WorkflowEditorSurfaceResponse,
    BrepPanelRequest,
    BrepPanelResponse,
    BrepToolRequest,
    WorkflowEditorBootstrapRequest,
    WorkflowEditorBootstrapResponse,
    WorkflowEditorReadRequest,
    WorkflowEditorSaveRequest,
)
from workspace_service.workflows import (
    WorkflowPersistenceError,
    WorkflowRevisionConflict,
)
from core.workflow_runs import WorkflowRunnerError, WorkflowRunnerUnavailable
from core.workflow_editor import WorkflowEditorError
from workspace_service.workflow_operations import WorkflowOperationsError
from workspace_service.rivet_approvals import RivetApprovalError
from workspace_service.workflow_graph import WorkflowGraphError
from workspace_service.workflow_catalog import WorkflowTemplateError
from core.engineering_scenarios import EngineeringScenarioError
from workspace_service.brep_panel import (
    BREP_APPLICATION_STATUS_TOOL,
    BrepPanelError,
    panel_environment,
    parse_brep_status_result,
    select_brep_application_server,
    wait_for_brep_module,
)
from tool_registry.db import get_servers, update_server
from tool_registry.safety import ApprovalContext

logger = structlog.get_logger(__name__)
router = APIRouter()
_brep_panel_start_lock = asyncio.Lock()


def get_default_workspace_parent_dir() -> str:
    """Return the per-user parent directory for Wright-created workspaces."""
    return default_workspace_parent_dir()


def get_workspace_service() -> WorkspaceService:
    return workspace_service()


def _workflow_feature_enabled() -> None:
    if not rivet_workflows_enabled():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Rivet workflows are disabled"
        )


def _runner_feature_enabled() -> None:
    if not rivet_runner_enabled():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Rivet runner is disabled"
        )


def _editor_feature_enabled() -> None:
    if not rivet_editor_enabled():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Rivet editor is disabled"
        )
    surface_flags = get_workspace_surface_settings().flags
    if not surface_flags.model or not surface_flags.live_apps:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rivet editor requires workspace live app surfaces",
        )


def _operations_feature_enabled() -> None:
    if not rivet_workflow_operations_enabled():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rivet workflow operations are disabled",
        )


def _workflow_response(document) -> WorkflowResponse:
    return WorkflowResponse(
        workflow_id=document.workflow_id,
        slug=document.slug,
        revision=document.revision,
        etag=document.digest,
    )


def _workflow_template_response(template) -> WorkflowTemplateResponse:
    return WorkflowTemplateResponse(
        template_id=template.template_id,
        title=template.title,
        description=template.description,
        kind=template.kind,
        requirements=list(template.requirements),
    )


def _run_response(run, record=None, manifest=None) -> WorkflowRunResponse:
    output = record.output_summary if record is not None else None
    return WorkflowRunResponse(
        run_id=run.run_id,
        workspace_id=run.workspace_id,
        session_id=run.session_id,
        workflow_id=run.workflow_id,
        revision=run.revision,
        digest=record.digest if record is not None else None,
        graph=record.graph if record is not None else None,
        generation=run.generation,
        state=run.state,
        reason=run.reason,
        outputs=output.get("outputs") if output else None,
        duration_ms=output.get("durationMs") if output else None,
        output_truncated=record.output_truncated if record is not None else False,
        manifest=manifest,
    )


def _run_manifest(service, run_id: str):
    getter = getattr(service.workflow_runner, "manifest", None)
    return getter(run_id) if callable(getter) else None


def _call_approval_response(approval) -> RivetCallApprovalResponse:
    return RivetCallApprovalResponse(
        approval_id=approval.approval_id,
        run_id=approval.run_id,
        node_id=approval.node_id,
        qualified_tool_name=approval.qualified_tool_name,
        binding_digest=approval.binding_digest,
        argument_digest=approval.argument_digest,
        argument_summary=dict(approval.argument_summary),
        required_gates=list(approval.required_gates),
        state=approval.state,
        expires_at=approval.expires_at.isoformat(),
        approval_digest=approval.approval_digest,
        decided_by=approval.decided_by,
        decision_reason=approval.decision_reason,
    )


def _editor_bootstrap_response(bootstrap) -> WorkflowEditorBootstrapResponse:
    return WorkflowEditorBootstrapResponse(
        availability=bootstrap.availability,
        grant_id=bootstrap.grant_id,
        workflow_id=bootstrap.workflow_id,
        revision=bootstrap.revision,
        etag=bootstrap.etag,
        expires_at=(bootstrap.expires_at.isoformat() if bootstrap.expires_at else None),
        detail=bootstrap.detail,
    )


def _review_response(record) -> WorkflowReviewResponse:
    review = record.review
    return WorkflowReviewResponse(
        workflow_id=record.workflow_id,
        slug=record.slug,
        revision=record.revision,
        etag=record.digest,
        review_state=review.state if review else None,
        reviewer=review.reviewer if review else None,
        reviewed_at=review.updated_at if review else None,
        workflow_digest=review.workflow_digest if review else None,
        graph_id=review.graph_id if review else None,
        binding_set_id=review.binding_set_id if review else None,
        binding_set_digest=review.binding_set_digest if review else None,
        policy_snapshot_digest=review.policy_snapshot_digest if review else None,
        review_digest=review.review_digest if review else None,
        stale_reasons=list(record.stale_reasons),
    )


def _mcp_error(error: WorkflowOperationsError) -> HTTPException:
    conflict_codes = {
        "RIVET_WORKFLOW_REVISION_CONFLICT",
        "RIVET_REVIEW_STALE",
        "RIVET_BINDING_EXTRA",
    }
    return HTTPException(
        status_code=(
            status.HTTP_409_CONFLICT
            if error.code in conflict_codes
            else status.HTTP_400_BAD_REQUEST
        ),
        detail={"code": error.code, "message": str(error)},
    )


def _scenario_error(error: EngineeringScenarioError) -> HTTPException:
    conflict_codes = {
        "scenario_preflight_stale",
        "scenario_workflow_modified",
        "scenario_binding_stale",
    }
    return HTTPException(
        status_code=(
            status.HTTP_404_NOT_FOUND
            if error.code in {"scenario_not_found", "scenario_report_unavailable"}
            else status.HTTP_409_CONFLICT
            if error.code in conflict_codes
            else status.HTTP_400_BAD_REQUEST
        ),
        detail={"code": error.code, "message": str(error)},
    )


def _graph_response(result) -> WorkflowGraphResponse:
    return WorkflowGraphResponse(
        **_workflow_response(result.document).model_dump(),
        graph=WorkflowGraphSummaryResponse(
            graph_id=result.graph.graph_id,
            name=result.graph.name,
            main=result.graph.main,
            node_count=len(result.graph.nodes),
            nodes=[
                {
                    "node_id": node.node_id,
                    "node_type": node.node_type,
                    "title": node.title,
                    "data": dict(node.data),
                    "outgoing_connections": list(node.outgoing_connections),
                }
                for node in result.graph.nodes
            ],
        ),
        issues=[dict(issue) for issue in result.issues],
    )


async def _editor_scope(
    session_id: str, engine: BaseAgentEngine, service: WorkspaceService
):
    workspace = service.lifecycle.get_by_session(session_id)
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found"
        )
    return workspace["workspace_id"], await service.resolve_workspace_dir(
        session_id, engine
    )


async def _workflow_scope(
    session_id: str, engine: BaseAgentEngine, service: WorkspaceService
):
    workspace = service.lifecycle.get_by_session(session_id)
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found"
        )
    return workspace["workspace_id"], await service.resolve_workspace_dir(
        session_id, engine
    )


def _scenario_entry_response(entry) -> EngineeringScenarioCatalogEntryResponse:
    return EngineeringScenarioCatalogEntryResponse(
        scenario_id=entry.scenario_id,
        revision=entry.revision,
        title=entry.title,
        summary=entry.summary,
        domains=list(entry.domains),
        tier=str(entry.tier),
        resource_class=str(entry.resource_class),
        expected_duration_seconds=entry.expected_duration_seconds,
        manifest_digest=entry.manifest_digest,
    )


def _scenario_report_response(report: dict) -> EngineeringScenarioReportResponse:
    return EngineeringScenarioReportResponse(
        scenario_run_id=report["scenario_run_id"],
        workflow_run_id=report["workflow_run_id"],
        workspace_id=report["workspace_id"],
        session_id=report["session_id"],
        scenario_id=report["scenario_id"],
        scenario_revision=report["scenario_revision"],
        manifest_digest=report["manifest_digest"],
        workflow_digest=report["workflow_digest"],
        binding_set_digest=report.get("binding_set_digest"),
        state=report["state"],
        identity=dict(report["identity"]),
        artifacts=list(report["artifacts"]),
        environment=dict(report["environment"]),
        cleanup_state=report["cleanup_state"],
        residue=dict(report["residue"]),
        assertions=list(report["assertions"]),
        report_digest=report.get("report_digest"),
    )


def _assert_scenario_scope(report: dict, *, workspace_id: str, session_id: str) -> None:
    if report["workspace_id"] != workspace_id or report["session_id"] != session_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "scenario_report_unavailable",
                "message": "Scenario report was not found",
            },
        )


@router.get("/engineering-scenarios", response_model=EngineeringScenarioListResponse)
@traced("workspace.engineering_scenarios.list")
async def list_engineering_scenarios_endpoint(
    domain: list[str] = Query(default=[]),
    tier: str | None = Query(default=None, pattern="^tier[123]$"),
    service: WorkspaceService = Depends(get_workspace_service),
):
    _workflow_feature_enabled()
    return EngineeringScenarioListResponse(
        scenarios=[
            _scenario_entry_response(entry)
            for entry in service.engineering_scenarios.list(domains=domain, tier=tier)
        ]
    )


@router.get(
    "/engineering-scenarios/{scenario_id}",
    response_model=EngineeringScenarioDetailResponse,
)
@traced("workspace.engineering_scenarios.detail")
async def engineering_scenario_detail_endpoint(
    scenario_id: str,
    service: WorkspaceService = Depends(get_workspace_service),
):
    _workflow_feature_enabled()
    try:
        manifest = service.engineering_scenarios.detail(scenario_id)
        return EngineeringScenarioDetailResponse(
            manifest=dict(manifest.document), manifest_digest=manifest.digest
        )
    except EngineeringScenarioError as error:
        raise _scenario_error(error) from error


@router.post(
    "/engineering-scenarios/{scenario_id}/preflight",
    response_model=EngineeringScenarioPreflightResponse,
)
@traced("workspace.engineering_scenarios.preflight")
async def engineering_scenario_preflight_endpoint(
    scenario_id: str,
    body: EngineeringScenarioPreflightRequest,
    engine: BaseAgentEngine = Depends(get_agent_engine),
    service: WorkspaceService = Depends(get_workspace_service),
):
    _workflow_feature_enabled()
    _operations_feature_enabled()
    workspace_id, workspace_dir = await _workflow_scope(
        body.session_id, engine, service
    )
    try:
        preflight = await service.engineering_scenarios.preflight(
            workspace_id=workspace_id,
            session_id=body.session_id,
            workspace_dir=workspace_dir,
            scenario_id=scenario_id,
            allow_tier2=body.allow_tier2,
            platform_tag=body.platform,
        )
        return EngineeringScenarioPreflightResponse(
            preflight_id=preflight.preflight_id,
            scenario_id=preflight.scenario_id,
            scenario_revision=preflight.scenario_revision,
            manifest_digest=preflight.manifest_digest,
            workflow_slug=preflight.workflow_slug,
            workflow_revision=preflight.workflow_revision,
            workflow_digest=preflight.workflow_digest,
            graph_id=preflight.graph_id,
            binding_set_digest=preflight.binding_set_digest,
            state=preflight.state,
            capabilities=[dict(value) for value in preflight.capabilities],
            environment=dict(preflight.environment),
            blockers=[
                EngineeringScenarioBlockerResponse(
                    code=value.code,
                    message=value.message,
                    recovery=value.recovery,
                )
                for value in preflight.blockers
            ],
            expires_at=preflight.expires_at.isoformat(),
        )
    except EngineeringScenarioError as error:
        raise _scenario_error(error) from error


@router.post(
    "/engineering-scenarios/{scenario_id}/runs",
    response_model=EngineeringScenarioStartResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
@traced("workspace.engineering_scenarios.start")
async def start_engineering_scenario_endpoint(
    scenario_id: str,
    body: EngineeringScenarioStartRequest,
    engine: BaseAgentEngine = Depends(get_agent_engine),
    service: WorkspaceService = Depends(get_workspace_service),
):
    _workflow_feature_enabled()
    _runner_feature_enabled()
    _operations_feature_enabled()
    workspace_id, workspace_dir = await _workflow_scope(
        body.session_id, engine, service
    )
    try:
        scenario_run_id, run = await service.engineering_scenarios.start(
            workspace_id=workspace_id,
            session_id=body.session_id,
            workspace_dir=workspace_dir,
            scenario_id=scenario_id,
            manifest_digest=body.manifest_digest,
            workflow_revision=body.workflow_revision,
            workflow_digest=body.workflow_digest,
            review_digest=body.review_digest,
            binding_set_digest=body.binding_set_digest,
            seed=body.seed,
        )
        return EngineeringScenarioStartResponse(
            scenario_run_id=scenario_run_id,
            workflow_run=_run_response(
                run,
                service.workflow_runner.result(run.run_id),
                _run_manifest(service, run.run_id),
            ),
            state="running",
        )
    except EngineeringScenarioError as error:
        raise _scenario_error(error) from error
    except (WorkflowOperationsError, WorkflowRunnerError) as error:
        raise _mcp_error(error) from error


@router.get(
    "/engineering-scenarios/runs/{scenario_run_id}",
    response_model=EngineeringScenarioReportResponse,
)
@traced("workspace.engineering_scenarios.report")
async def engineering_scenario_report_endpoint(
    scenario_run_id: str,
    session_id: str = Query(...),
    service: WorkspaceService = Depends(get_workspace_service),
):
    _operations_feature_enabled()
    workspace = service.lifecycle.get_by_session(session_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    try:
        report = service.engineering_scenarios.report(scenario_run_id)
        if report is None:
            raise EngineeringScenarioError(
                "scenario_report_unavailable", "Scenario report was not found"
            )
        _assert_scenario_scope(
            report, workspace_id=workspace["workspace_id"], session_id=session_id
        )
        return _scenario_report_response(report)
    except EngineeringScenarioError as error:
        raise _scenario_error(error) from error


@router.get("/engineering-scenarios/runs/{scenario_run_id}/export")
@traced("workspace.engineering_scenarios.export")
async def engineering_scenario_export_endpoint(
    scenario_run_id: str,
    session_id: str = Query(...),
    service: WorkspaceService = Depends(get_workspace_service),
):
    report = await engineering_scenario_report_endpoint(
        scenario_run_id, session_id, service
    )
    document = report.model_dump(mode="json")
    encoded = json.dumps(document, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    return Response(
        content=encoded,
        media_type="application/json",
        headers={
            "Cache-Control": "no-store",
            "Content-Disposition": (
                f'attachment; filename="wright-engineering-scenario-{scenario_run_id}.json"'
            ),
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.post(
    "/engineering-scenarios/runs/{scenario_run_id}/cancel",
    response_model=WorkflowRunResponse,
)
@traced("workspace.engineering_scenarios.cancel")
async def cancel_engineering_scenario_endpoint(
    scenario_run_id: str,
    body: EngineeringScenarioCancelRequest,
    service: WorkspaceService = Depends(get_workspace_service),
):
    _runner_feature_enabled()
    _operations_feature_enabled()
    workspace = service.lifecycle.get_by_session(body.session_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    try:
        run = await service.engineering_scenarios.cancel(
            workspace_id=workspace["workspace_id"],
            session_id=body.session_id,
            scenario_run_id=scenario_run_id,
        )
        return _run_response(
            run,
            service.workflow_runner.result(run.run_id),
            _run_manifest(service, run.run_id),
        )
    except EngineeringScenarioError as error:
        raise _scenario_error(error) from error


@router.get(
    "/engineering-scenarios/runs/{left}/compare/{right}",
    response_model=EngineeringScenarioCompareResponse,
)
@traced("workspace.engineering_scenarios.compare")
async def compare_engineering_scenario_runs_endpoint(
    left: str,
    right: str,
    session_id: str = Query(...),
    service: WorkspaceService = Depends(get_workspace_service),
):
    _operations_feature_enabled()
    workspace = service.lifecycle.get_by_session(session_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    try:
        first = service.engineering_scenarios.report(left)
        second = service.engineering_scenarios.report(right)
        if first is None or second is None:
            raise EngineeringScenarioError(
                "scenario_report_unavailable", "Scenario report was not found"
            )
        _assert_scenario_scope(
            first, workspace_id=workspace["workspace_id"], session_id=session_id
        )
        _assert_scenario_scope(
            second, workspace_id=workspace["workspace_id"], session_id=session_id
        )
        result = service.engineering_scenarios.compare(left, right)
        return EngineeringScenarioCompareResponse(
            strictly_reproducible=result["strictly_reproducible"],
            differences=list(result["differences"]),
            assertion_changes=list(result["assertion_changes"]),
        )
    except EngineeringScenarioError as error:
        raise _scenario_error(error) from error


@router.get("/workflow-templates", response_model=WorkflowTemplateListResponse)
@traced("workspace.workflow_templates.list")
async def list_workflow_templates_endpoint(
    service: WorkspaceService = Depends(get_workspace_service),
):
    _workflow_feature_enabled()
    return WorkflowTemplateListResponse(
        templates=[
            _workflow_template_response(template)
            for template in service.workflow_templates.list()
        ]
    )


@router.post(
    "/workflow-templates/{template_id}/instantiate",
    response_model=WorkflowResponse,
    status_code=status.HTTP_201_CREATED,
)
@traced("workspace.workflow_templates.instantiate")
async def instantiate_workflow_template_endpoint(
    template_id: str,
    body: WorkflowTemplateInstantiateRequest,
    engine: BaseAgentEngine = Depends(get_agent_engine),
    service: WorkspaceService = Depends(get_workspace_service),
):
    _workflow_feature_enabled()
    workspace_id, workspace_dir = await _workflow_scope(
        body.session_id, engine, service
    )
    try:
        project = service.workflow_templates.instantiate(template_id)
        document = await service.workflows.create(
            workspace_id,
            workspace_dir,
            body.slug,
            project,
            {},
        )
        return _workflow_response(document)
    except WorkflowTemplateError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(error)
        ) from error
    except WorkflowPersistenceError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)
        ) from error


@router.get(
    "/workflows/editor/status", response_model=WorkflowEditorAvailabilityResponse
)
@traced("workspace.workflows.editor.status")
async def workflow_editor_status_endpoint(
    service: WorkspaceService = Depends(get_workspace_service),
):
    _editor_feature_enabled()
    availability, detail = service.workflow_editor.availability()
    return WorkflowEditorAvailabilityResponse(availability=availability, detail=detail)


@router.post("/workflows/editor/surface", response_model=WorkflowEditorSurfaceResponse)
@traced("workspace.workflows.editor.surface")
async def workflow_editor_surface_endpoint(
    body: WorkflowEditorSurfaceRequest,
    engine: BaseAgentEngine = Depends(get_agent_engine),
    service: WorkspaceService = Depends(get_workspace_service),
):
    _editor_feature_enabled()
    _workspace_id, workspace_dir = await _editor_scope(body.session_id, engine, service)
    availability, detail = service.workflow_editor.availability()
    if availability.value != "available":
        return WorkflowEditorSurfaceResponse(availability=availability, detail=detail)
    try:
        manifest = service.workflow_editor.manual_surface_manifest(workspace_dir)
    except WorkflowEditorError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(error)
        ) from error
    return WorkflowEditorSurfaceResponse(
        availability=availability,
        detail=detail,
        manifest=manifest,
    )


@router.post("/brep/panel", response_model=BrepPanelResponse)
@traced("workspace.brep.panel")
async def brep_panel_endpoint(
    body: BrepPanelRequest,
    request: Request,
    response: Response,
    engine: BaseAgentEngine = Depends(get_agent_engine),
    service: WorkspaceService = Depends(get_workspace_service),
):
    """Start the visible BREP MCP and return its bounded loopback panel URL."""

    workspace_id, workspace_dir = await _workflow_scope(
        body.session_id, engine, service
    )
    mcp_engine = getattr(request.app.state, "mcp_engine", None)
    if mcp_engine is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The Wright MCP runtime is unavailable.",
        )
    try:
        # Workspace restoration can mount the retained BREP surface more than
        # once before the first MCP process has published its runner. Keep the
        # environment reconciliation, process start, and readiness probe in one
        # single-flight section so every waiter reuses the first healthy host.
        async with _brep_panel_start_lock:
            server = select_brep_application_server(get_servers(DATABASE_PATH))
            configured_environment = panel_environment(
                server.env_vars if isinstance(server.env_vars, dict) else {}
            )
            environment_changed = configured_environment != server.env_vars
            if environment_changed:
                server = update_server(
                    DATABASE_PATH,
                    server.server_id,
                    {
                        "env_vars": configured_environment,
                        "updated_at": int(time.time()),
                    },
                )
                if server is None:
                    raise BrepPanelError("The BREP MCP registration disappeared.")

            approval = ApprovalContext(
                workspace_id=workspace_id,
                session_id=body.session_id,
                workspace_approvals=set(server.approval_gates or []),
            )
            runner = mcp_engine.lifecycle.runner_for(server.server_id)
            if environment_changed or runner is None or not runner.is_running():
                started = await mcp_engine.start_server(
                    server.server_id,
                    workspace_dir=workspace_dir,
                    approval_context=approval,
                )
                if started is None or started.status == "error":
                    raise BrepPanelError(
                        (started.error_message if started else None)
                        or "The BREP MCP process did not start."
                    )

            result = await mcp_engine.call_tool(
                server.server_id,
                BREP_APPLICATION_STATUS_TOOL,
                {},
                approval_context=approval,
            )
            panel = parse_brep_status_result(result)
            await asyncio.to_thread(wait_for_brep_module, panel.module_url)
    except BrepPanelError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(error)
        ) from error
    except Exception as error:
        logger.exception("brep_panel_start_failed", error=str(error))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="BREP could not be started for the Wright panel.",
        ) from error

    response.headers["Cache-Control"] = "no-store"
    return BrepPanelResponse(
        server_id=server.server_id,
        control_url=panel.control_url,
        module_url=panel.module_url,
        connected=panel.connected,
    )


@router.post("/brep/tool")
@traced("workspace.brep.tool")
async def brep_tool_endpoint(
    body: BrepToolRequest,
    request: Request,
    engine: BaseAgentEngine = Depends(get_agent_engine),
    service: WorkspaceService = Depends(get_workspace_service),
):
    """Call the panel-owned BREP process for the Wright STDIO gateway."""

    workspace_id, workspace_dir = await _workflow_scope(
        body.session_id, engine, service
    )
    mcp_engine = getattr(request.app.state, "mcp_engine", None)
    if mcp_engine is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The Wright MCP runtime is unavailable.",
        )
    try:
        server = select_brep_application_server(get_servers(DATABASE_PATH))
        configured_environment = panel_environment(
            server.env_vars if isinstance(server.env_vars, dict) else {}
        )
        if configured_environment != server.env_vars:
            server = update_server(
                DATABASE_PATH,
                server.server_id,
                {
                    "env_vars": configured_environment,
                    "updated_at": int(time.time()),
                },
            )
            if server is None:
                raise BrepPanelError("The BREP MCP registration disappeared.")
        approval = ApprovalContext(
            workspace_id=workspace_id,
            session_id=body.session_id,
            workspace_approvals=set(server.approval_gates or []),
        )
        runner = mcp_engine.lifecycle.runner_for(server.server_id)
        if runner is None or not runner.is_running():
            started = await mcp_engine.start_server(
                server.server_id,
                workspace_dir=workspace_dir,
                approval_context=approval,
            )
            if started is None or started.status == "error":
                raise BrepPanelError(
                    (started.error_message if started else None)
                    or "The BREP MCP process did not start."
                )
        return await mcp_engine.call_tool(
            server.server_id,
            body.tool_name,
            body.arguments,
            approval_context=approval,
        )
    except BrepPanelError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(error)
        ) from error
    except Exception as error:
        logger.exception(
            "brep_panel_tool_failed",
            tool_name=body.tool_name,
            error=str(error),
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="BREP could not execute the requested tool.",
        ) from error


@router.post(
    "/workflows/{slug}/editor/bootstrap", response_model=WorkflowEditorBootstrapResponse
)
@traced("workspace.workflows.editor.bootstrap")
async def workflow_editor_bootstrap_endpoint(
    slug: str,
    body: WorkflowEditorBootstrapRequest,
    engine: BaseAgentEngine = Depends(get_agent_engine),
    service: WorkspaceService = Depends(get_workspace_service),
):
    _editor_feature_enabled()
    workspace_id, workspace_dir = await _editor_scope(body.session_id, engine, service)
    try:
        return _editor_bootstrap_response(
            await service.workflow_editor.bootstrap(
                workspace_id=workspace_id,
                session_id=body.session_id,
                workspace_dir=workspace_dir,
                slug=slug,
            )
        )
    except WorkflowPersistenceError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found"
        ) from error


@router.post("/workflows/editor/read", response_model=WorkflowDocumentResponse)
@traced("workspace.workflows.editor.read")
async def workflow_editor_read_endpoint(
    body: WorkflowEditorReadRequest,
    engine: BaseAgentEngine = Depends(get_agent_engine),
    service: WorkspaceService = Depends(get_workspace_service),
):
    _editor_feature_enabled()
    workspace_id, workspace_dir = await _editor_scope(body.session_id, engine, service)
    try:
        document = await service.workflow_editor.read(
            body.grant_id,
            workspace_id=workspace_id,
            session_id=body.session_id,
            workspace_dir=workspace_dir,
        )
        return WorkflowDocumentResponse(
            **_workflow_response(document).model_dump(),
            project=document.project,
            datasets=document.datasets,
        )
    except WorkflowEditorError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Editor grant is unavailable"
        ) from error


@router.post("/workflows/editor/save", response_model=WorkflowResponse)
@traced("workspace.workflows.editor.save")
async def workflow_editor_save_endpoint(
    body: WorkflowEditorSaveRequest,
    engine: BaseAgentEngine = Depends(get_agent_engine),
    service: WorkspaceService = Depends(get_workspace_service),
):
    _editor_feature_enabled()
    workspace_id, workspace_dir = await _editor_scope(body.session_id, engine, service)
    try:
        document = await service.workflow_editor.save(
            body.grant_id,
            workspace_id=workspace_id,
            session_id=body.session_id,
            workspace_dir=workspace_dir,
            expected_revision=body.expected_revision,
            project=body.project,
            datasets=body.datasets,
        )
        return _workflow_response(document)
    except WorkflowEditorError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Editor grant is unavailable"
        ) from error
    except WorkflowRevisionConflict as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "revision_conflict",
                "revision": error.revision,
                "etag": error.digest,
            },
        ) from error


@router.get("/workflows/runner/status", response_model=WorkflowRunnerStatusResponse)
@traced("workspace.workflows.runner.status")
async def workflow_runner_status_endpoint(
    service: WorkspaceService = Depends(get_workspace_service),
):
    _runner_feature_enabled()
    runner = service.workflow_runner.status()
    return WorkflowRunnerStatusResponse(
        availability=runner.availability,
        generation=runner.generation,
        detail=runner.detail,
    )


@router.post(
    "/workflows/{slug}/runs",
    response_model=WorkflowRunResponse,
    status_code=status.HTTP_201_CREATED,
)
@traced("workspace.workflows.runner.start")
async def start_workflow_run_endpoint(
    slug: str,
    body: WorkflowRunStartRequest,
    engine: BaseAgentEngine = Depends(get_agent_engine),
    service: WorkspaceService = Depends(get_workspace_service),
):
    _runner_feature_enabled()
    _operations_feature_enabled()
    workspace = service.lifecycle.get_by_session(body.session_id)
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found"
        )
    workspace_dir = await service.resolve_workspace_dir(body.session_id, engine)
    try:
        run = await service.workflow_operations.start(
            workspace_id=workspace["workspace_id"],
            session_id=body.session_id,
            workspace_dir=workspace_dir,
            slug=slug,
            expected_generation=body.expected_generation,
            expected_revision=body.expected_revision,
            expected_digest=body.expected_digest,
            expected_review_digest=body.expected_review_digest,
            binding_set_digest=body.binding_set_digest,
            graph=body.graph,
            inputs=body.inputs,
            context=body.context,
            timeout_seconds=body.timeout_seconds,
        )
        return _run_response(
            run,
            service.workflow_runner.result(run.run_id),
            _run_manifest(service, run.run_id),
        )
    except WorkflowRunnerUnavailable as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": error.code, "availability": error.availability},
        ) from error
    except (
        WorkflowRunnerError,
        WorkflowPersistenceError,
        WorkflowOperationsError,
    ) as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": getattr(error, "code", "invalid_workflow_run"),
                "message": str(error),
            },
        ) from error


@router.get("/workflows/runs/{run_id}", response_model=WorkflowRunResponse)
@traced("workspace.workflows.runner.status")
async def workflow_run_status_endpoint(
    run_id: str,
    session_id: str = Query(...),
    service: WorkspaceService = Depends(get_workspace_service),
):
    _runner_feature_enabled()
    _operations_feature_enabled()
    workspace = service.lifecycle.get_by_session(session_id)
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found"
        )
    try:
        run = service.workflow_operations.run(
            workspace_id=workspace["workspace_id"], session_id=session_id, run_id=run_id
        )
        return _run_response(
            run,
            service.workflow_runner.result(run.run_id),
            _run_manifest(service, run_id),
        )
    except (WorkflowRunnerError, WorkflowOperationsError) as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(error)
        ) from error


@router.get(
    "/workflows/runs/{run_id}/approvals",
    response_model=RivetCallApprovalListResponse,
)
@traced("workspace.workflows.runner.approvals")
async def workflow_run_approvals_endpoint(
    run_id: str,
    session_id: str = Query(...),
    service: WorkspaceService = Depends(get_workspace_service),
):
    _runner_feature_enabled()
    _operations_feature_enabled()
    workspace = service.lifecycle.get_by_session(session_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    try:
        approvals = service.workflow_operations.call_approvals(
            workspace_id=workspace["workspace_id"],
            session_id=session_id,
            run_id=run_id,
        )
        return RivetCallApprovalListResponse(
            approvals=[_call_approval_response(item) for item in approvals]
        )
    except (WorkflowRunnerError, WorkflowOperationsError) as error:
        raise HTTPException(
            status_code=404, detail="Workflow run was not found"
        ) from error


@router.post(
    "/workflows/runs/{run_id}/approvals/{approval_id}",
    response_model=RivetCallApprovalResponse,
)
@traced("workspace.workflows.runner.approval_decision")
async def decide_workflow_run_approval_endpoint(
    run_id: str,
    approval_id: str,
    body: RivetCallApprovalDecisionRequest,
    service: WorkspaceService = Depends(get_workspace_service),
):
    _runner_feature_enabled()
    _operations_feature_enabled()
    workspace = service.lifecycle.get_by_session(body.session_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    try:
        approval = service.workflow_operations.decide_call_approval(
            workspace_id=workspace["workspace_id"],
            session_id=body.session_id,
            run_id=run_id,
            approval_id=approval_id,
            expected_digest=body.expected_digest,
            actor=body.actor,
            approved=body.decision == "approved",
            reason=body.reason,
        )
        return _call_approval_response(approval)
    except WorkflowOperationsError as error:
        raise HTTPException(
            status_code=404, detail="Call approval was not found"
        ) from error
    except RivetApprovalError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": error.code, "message": str(error)},
        ) from error


@router.post("/workflows/runs/{run_id}/cancel", response_model=WorkflowRunResponse)
@traced("workspace.workflows.runner.cancel")
async def cancel_workflow_run_endpoint(
    run_id: str,
    body: WorkflowRunCancelRequest,
    service: WorkspaceService = Depends(get_workspace_service),
):
    _runner_feature_enabled()
    _operations_feature_enabled()
    workspace = service.lifecycle.get_by_session(body.session_id)
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found"
        )
    try:
        run = await service.workflow_operations.cancel(
            workspace_id=workspace["workspace_id"],
            session_id=body.session_id,
            run_id=run_id,
            generation=body.generation,
        )
        return _run_response(
            run,
            service.workflow_runner.result(run.run_id),
            _run_manifest(service, run_id),
        )
    except (WorkflowRunnerError, WorkflowOperationsError) as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": error.code, "message": str(error)},
        ) from error


@router.post("/workflows/{slug}/review", response_model=WorkflowReviewResponse)
@traced("workspace.workflows.review")
async def review_workflow_endpoint(
    slug: str,
    body: WorkflowReviewRequest,
    engine: BaseAgentEngine = Depends(get_agent_engine),
    service: WorkspaceService = Depends(get_workspace_service),
):
    _operations_feature_enabled()
    workspace = service.lifecycle.get_by_session(body.session_id)
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found"
        )
    try:
        return _review_response(
            await service.workflow_operations.review(
                workspace_id=workspace["workspace_id"],
                workspace_dir=await service.resolve_workspace_dir(
                    body.session_id, engine
                ),
                slug=slug,
                state=body.state,
                reviewer=body.reviewer,
                session_id=body.session_id,
                expected_digest=body.expected_digest,
                graph=body.graph,
                binding_set_digest=body.binding_set_digest,
            )
        )
    except (WorkflowOperationsError, WorkflowPersistenceError) as error:
        if isinstance(error, WorkflowOperationsError):
            raise _mcp_error(error) from error
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)
        ) from error


@router.get(
    "/workflows/{slug}/mcp-capabilities",
    response_model=RivetMcpCapabilitiesResponse,
)
@traced("workspace.workflows.mcp.capabilities")
async def workflow_mcp_capabilities_endpoint(
    slug: str,
    session_id: str = Query(...),
    graph: str | None = Query(default=None, max_length=256),
    after: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=200),
    engine: BaseAgentEngine = Depends(get_agent_engine),
    service: WorkspaceService = Depends(get_workspace_service),
):
    _operations_feature_enabled()
    workspace_id, workspace_dir = await _workflow_scope(session_id, engine, service)
    try:
        record = await service.workflow_operations.mcp_capabilities(
            workspace_id=workspace_id,
            session_id=session_id,
            workspace_dir=workspace_dir,
            slug=slug,
            graph=graph,
        )
    except (WorkflowOperationsError, WorkflowPersistenceError) as error:
        if isinstance(error, WorkflowOperationsError):
            raise _mcp_error(error) from error
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(error)
        ) from error
    page = record.snapshot.tools[after : after + limit]
    next_after = (
        after + len(page) if after + len(page) < len(record.snapshot.tools) else None
    )
    return RivetMcpCapabilitiesResponse(
        workflow_id=record.workflow_id,
        slug=record.slug,
        revision=record.revision,
        etag=record.digest,
        graph_id=record.graph_id,
        snapshot_digest=record.snapshot.snapshot_digest,
        policy_snapshot_digest=record.snapshot.policy_snapshot_digest,
        requirements=[
            RivetMcpRequirementResponse(
                graph_id=item.graph_id,
                node_id=item.node_id,
                node_type=item.node_type,
                static_tool_name=item.static_tool_name,
            )
            for item in record.requirements
        ],
        issues=[
            {
                "code": item.code,
                "message": item.message,
                "graph_id": item.graph_id,
                "node_id": item.node_id,
            }
            for item in record.issues
        ],
        capabilities=[
            RivetMcpCapabilityResponse(
                qualified_tool_name=item.qualified_tool_name,
                server_id=item.server_id,
                tool_name=item.tool_name,
                title=item.title,
                description=item.description,
                server_revision=item.server_revision,
                capability_digest=item.capability_digest,
                validation_evidence_id=item.validation_evidence_id,
                workspace_grant_digest=item.workspace_grant_digest,
                input_schema=dict(item.input_schema),
                output_schema=(
                    dict(item.output_schema) if item.output_schema else None
                ),
                schema_digest=item.schema_digest,
                annotations=dict(item.annotations),
                required_approvals=list(item.required_approvals),
                compatibility=item.compatibility,
                binding_eligible=item.binding_eligible,
                blocking_reasons=list(item.blocking_reasons),
            )
            for item in page
        ],
        next_after=next_after,
    )


@router.post(
    "/workflows/{slug}/mcp-bindings/preview",
    response_model=RivetMcpBindingPreviewResponse,
)
@traced("workspace.workflows.mcp.bindings.preview")
async def workflow_mcp_binding_preview_endpoint(
    slug: str,
    body: RivetMcpBindingPreviewRequest,
    engine: BaseAgentEngine = Depends(get_agent_engine),
    service: WorkspaceService = Depends(get_workspace_service),
):
    _operations_feature_enabled()
    workspace_id, workspace_dir = await _workflow_scope(
        body.session_id, engine, service
    )
    selections = {item.node_id: item.qualified_tool_name for item in body.selections}
    if len(selections) != len(body.selections):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "RIVET_MCP_DUPLICATE_NODE",
                "message": "A binding node was selected more than once",
            },
        )
    try:
        preview = await service.workflow_operations.preview_mcp_bindings(
            workspace_id=workspace_id,
            session_id=body.session_id,
            workspace_dir=workspace_dir,
            slug=slug,
            expected_revision=body.expected_revision,
            expected_digest=body.expected_digest,
            graph=body.graph,
            selections=selections,
            units_policy={item.node_id: item.units_policy for item in body.selections},
            material_defaults={
                item.node_id: item.material_defaults for item in body.selections
            },
        )
    except (WorkflowOperationsError, WorkflowPersistenceError) as error:
        if isinstance(error, WorkflowOperationsError):
            raise _mcp_error(error) from error
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(error)
        ) from error
    return RivetMcpBindingPreviewResponse(
        workflow_id=preview.workflow_id,
        slug=preview.slug,
        revision=preview.revision,
        etag=preview.digest,
        graph_id=preview.graph_id,
        snapshot_digest=preview.snapshot_digest,
        policy_snapshot_digest=preview.policy_snapshot_digest,
        binding_set_id=(
            preview.binding_set.binding_set_id if preview.binding_set else None
        ),
        binding_set_digest=(
            preview.binding_set.binding_set_digest if preview.binding_set else None
        ),
        expires_at=preview.expires_at.isoformat(),
        ready=preview.binding_set is not None,
        bindings=[
            RivetMcpBindingResponse(
                node_id=item.requirement.node_id,
                node_handle=item.binding.node_handle if item.binding else None,
                selected_tool=item.selected_tool,
                binding_digest=item.binding.binding_digest if item.binding else None,
                server_id=item.binding.server_id if item.binding else None,
                server_revision=item.binding.server_revision if item.binding else None,
                schema_digest=item.binding.schema_digest if item.binding else None,
                validation_evidence_id=(
                    item.binding.validation_evidence_id if item.binding else None
                ),
                workspace_grant_digest=(
                    item.binding.workspace_grant_digest if item.binding else None
                ),
                risk=dict(item.binding.risk) if item.binding else None,
                units_policy=dict(item.binding.units_policy) if item.binding else None,
                material_defaults=(
                    dict(item.binding.material_defaults) if item.binding else None
                ),
                blockers=list(item.blockers),
            )
            for item in preview.nodes
        ],
    )


@router.get("/workflows", response_model=WorkflowOperationsListResponse)
@traced("workspace.workflows.operations.list")
async def list_workflow_operations_endpoint(
    session_id: str = Query(...),
    engine: BaseAgentEngine = Depends(get_agent_engine),
    service: WorkspaceService = Depends(get_workspace_service),
):
    _operations_feature_enabled()
    workspace = service.lifecycle.get_by_session(session_id)
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found"
        )
    records = await service.workflow_operations.list(
        workspace_id=workspace["workspace_id"],
        workspace_dir=await service.resolve_workspace_dir(session_id, engine),
        session_id=session_id,
    )
    return WorkflowOperationsListResponse(
        workflows=[_review_response(record) for record in records]
    )


@router.get("/workflows/{slug}/operation", response_model=WorkflowReviewResponse)
@traced("workspace.workflows.operation")
async def workflow_operation_detail_endpoint(
    slug: str,
    session_id: str = Query(...),
    engine: BaseAgentEngine = Depends(get_agent_engine),
    service: WorkspaceService = Depends(get_workspace_service),
):
    _operations_feature_enabled()
    workspace = service.lifecycle.get_by_session(session_id)
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found"
        )
    try:
        return _review_response(
            await service.workflow_operations.detail(
                workspace_id=workspace["workspace_id"],
                workspace_dir=await service.resolve_workspace_dir(session_id, engine),
                slug=slug,
                session_id=session_id,
            )
        )
    except (WorkflowOperationsError, FileNotFoundError) as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(error)
        ) from error


@router.get(
    "/workflows/runs/{run_id}/history", response_model=WorkflowRunHistoryResponse
)
@traced("workspace.workflows.history")
async def workflow_run_history_endpoint(
    run_id: str,
    session_id: str = Query(...),
    after_sequence: int = Query(default=0, ge=0),
    service: WorkspaceService = Depends(get_workspace_service),
):
    _operations_feature_enabled()
    workspace = service.lifecycle.get_by_session(session_id)
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found"
        )
    try:
        events = service.workflow_operations.history(
            workspace_id=workspace["workspace_id"],
            session_id=session_id,
            run_id=run_id,
            after_sequence=after_sequence,
        )
        return WorkflowRunHistoryResponse(
            run_id=run_id,
            events=[
                {
                    "sequence": event.sequence,
                    "kind": event.kind,
                    "payload": dict(event.payload),
                }
                for event in events
            ],
        )
    except (WorkflowOperationsError, WorkflowRunnerError) as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(error)
        ) from error


@router.get(
    "/workflows/runs/{run_id}/manifest", response_model=WorkflowRunEvidenceResponse
)
@traced("workspace.workflows.manifest")
async def workflow_run_manifest_endpoint(
    run_id: str,
    session_id: str = Query(...),
    service: WorkspaceService = Depends(get_workspace_service),
):
    _operations_feature_enabled()
    workspace = service.lifecycle.get_by_session(session_id)
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found"
        )
    try:
        return service.workflow_operations.run_evidence(
            workspace_id=workspace["workspace_id"],
            session_id=session_id,
            run_id=run_id,
        )
    except (WorkflowOperationsError, WorkflowRunnerError) as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(error)
        ) from error


@router.get(
    "/workflows/runs/{run_id}/evidence", response_model=WorkflowRunEvidenceResponse
)
@traced("workspace.workflows.evidence")
async def workflow_run_evidence_endpoint(
    run_id: str,
    session_id: str = Query(...),
    service: WorkspaceService = Depends(get_workspace_service),
):
    return await workflow_run_manifest_endpoint(run_id, session_id, service)


@router.get("/workflows/runs/{run_id}/evidence/export")
@traced("workspace.workflows.evidence.export")
async def workflow_run_evidence_export_endpoint(
    run_id: str,
    session_id: str = Query(...),
    service: WorkspaceService = Depends(get_workspace_service),
):
    evidence = await workflow_run_manifest_endpoint(run_id, session_id, service)
    document = (
        evidence.model_dump(mode="json")
        if isinstance(evidence, WorkflowRunEvidenceResponse)
        else evidence
    )
    encoded = json.dumps(document, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    return Response(
        content=encoded,
        media_type="application/json",
        headers={
            "Cache-Control": "no-store",
            "Content-Disposition": (
                f'attachment; filename="wright-rivet-run-{run_id}-evidence.json"'
            ),
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.get("/workflows/{slug}/graph", response_model=WorkflowGraphResponse)
@traced("workspace.workflows.graph.inspect")
async def inspect_workflow_graph_endpoint(
    slug: str,
    session_id: str = Query(...),
    graph_id: str | None = Query(default=None),
    engine: BaseAgentEngine = Depends(get_agent_engine),
    service: WorkspaceService = Depends(get_workspace_service),
):
    _workflow_feature_enabled()
    try:
        _workspace_id, workspace_dir = await _workflow_scope(
            session_id, engine, service
        )
        return _graph_response(
            await service.workflow_graph.inspect(
                workspace_dir=workspace_dir,
                slug=slug,
                graph_id=graph_id,
            )
        )
    except FileNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found"
        ) from error
    except WorkflowGraphError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)
        ) from error


@router.get("/workflows/{slug}/graph/lint", response_model=WorkflowGraphResponse)
@traced("workspace.workflows.graph.lint")
async def lint_workflow_graph_endpoint(
    slug: str,
    session_id: str = Query(...),
    graph_id: str | None = Query(default=None),
    engine: BaseAgentEngine = Depends(get_agent_engine),
    service: WorkspaceService = Depends(get_workspace_service),
):
    _workflow_feature_enabled()
    try:
        _workspace_id, workspace_dir = await _workflow_scope(
            session_id, engine, service
        )
        return _graph_response(
            await service.workflow_graph.lint(
                workspace_dir=workspace_dir,
                slug=slug,
                graph_id=graph_id,
            )
        )
    except FileNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found"
        ) from error
    except WorkflowGraphError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)
        ) from error


@router.post("/workflows/{slug}/graph/actions", response_model=WorkflowGraphResponse)
@traced("workspace.workflows.graph.action")
async def apply_workflow_graph_action_endpoint(
    slug: str,
    body: WorkflowGraphActionRequest,
    engine: BaseAgentEngine = Depends(get_agent_engine),
    service: WorkspaceService = Depends(get_workspace_service),
):
    _workflow_feature_enabled()
    try:
        workspace_id, workspace_dir = await _workflow_scope(
            body.session_id, engine, service
        )
        return _graph_response(
            await service.workflow_graph.apply(
                workspace_id=workspace_id,
                workspace_dir=workspace_dir,
                slug=slug,
                expected_revision=body.expected_revision,
                action=body.action,
                arguments=body.model_dump(exclude={"session_id", "action"}),
            )
        )
    except FileNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found"
        ) from error
    except WorkflowRevisionConflict as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "revision_conflict",
                "revision": error.revision,
                "etag": error.digest,
            },
        ) from error
    except WorkflowGraphError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)
        ) from error


@router.get("/workflows/{slug}", response_model=WorkflowDocumentResponse)
@traced("workspace.workflows.read")
async def read_workflow_endpoint(
    slug: str,
    session_id: str = Query(...),
    engine: BaseAgentEngine = Depends(get_agent_engine),
    service: WorkspaceService = Depends(get_workspace_service),
):
    _workflow_feature_enabled()
    workspace_dir = await service.resolve_workspace_dir(session_id, engine)
    try:
        document = await service.workflows.read(workspace_dir, slug)
        return WorkflowDocumentResponse(
            **_workflow_response(document).model_dump(),
            project=document.project,
            datasets=document.datasets,
        )
    except FileNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found"
        ) from error
    except WorkflowPersistenceError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)
        ) from error


@router.post(
    "/workflows", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED
)
@traced("workspace.workflows.create")
async def create_workflow_endpoint(
    body: WorkflowCreateRequest,
    engine: BaseAgentEngine = Depends(get_agent_engine),
    service: WorkspaceService = Depends(get_workspace_service),
):
    _workflow_feature_enabled()
    workspace_dir = await service.resolve_workspace_dir(body.session_id, engine)
    workspace = service.lifecycle.get_by_session(body.session_id)
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found"
        )
    try:
        document = await service.workflows.create(
            workspace["workspace_id"],
            workspace_dir,
            body.slug,
            body.project,
            body.datasets,
        )
        return _workflow_response(document)
    except WorkflowPersistenceError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)
        ) from error


@router.put("/workflows/{slug}", response_model=WorkflowResponse)
@traced("workspace.workflows.save")
async def save_workflow_endpoint(
    slug: str,
    body: WorkflowSaveRequest,
    engine: BaseAgentEngine = Depends(get_agent_engine),
    service: WorkspaceService = Depends(get_workspace_service),
):
    _workflow_feature_enabled()
    workspace_dir = await service.resolve_workspace_dir(body.session_id, engine)
    workspace = service.lifecycle.get_by_session(body.session_id)
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found"
        )
    try:
        document = await service.workflows.save(
            workspace["workspace_id"],
            workspace_dir,
            slug,
            body.expected_revision,
            body.project,
            body.datasets,
        )
        return _workflow_response(document)
    except WorkflowRevisionConflict as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "revision_conflict",
                "revision": error.revision,
                "etag": error.digest,
            },
        ) from error
    except WorkflowPersistenceError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)
        ) from error


@router.post("/workflows/{slug}/rename", response_model=WorkflowResponse)
@traced("workspace.workflows.rename")
async def rename_workflow_endpoint(
    slug: str,
    body: WorkflowRenameRequest,
    engine: BaseAgentEngine = Depends(get_agent_engine),
    service: WorkspaceService = Depends(get_workspace_service),
):
    _workflow_feature_enabled()
    workspace_dir = await service.resolve_workspace_dir(body.session_id, engine)
    workspace = service.lifecycle.get_by_session(body.session_id)
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found"
        )
    try:
        document = await service.workflows.rename(
            workspace["workspace_id"],
            workspace_dir,
            slug,
            body.expected_revision,
            body.slug,
        )
        return _workflow_response(document)
    except WorkflowRevisionConflict as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "revision_conflict",
                "revision": error.revision,
                "etag": error.digest,
            },
        ) from error
    except WorkflowPersistenceError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)
        ) from error


@router.delete("/workflows/{slug}")
@traced("workspace.workflows.delete")
async def delete_workflow_endpoint(
    slug: str,
    body: WorkflowDeleteRequest,
    engine: BaseAgentEngine = Depends(get_agent_engine),
    service: WorkspaceService = Depends(get_workspace_service),
):
    _workflow_feature_enabled()
    workspace_dir = await service.resolve_workspace_dir(body.session_id, engine)
    workspace = service.lifecycle.get_by_session(body.session_id)
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found"
        )
    try:
        recovery_id = await service.workflows.delete(
            workspace["workspace_id"], workspace_dir, slug, body.expected_revision
        )
        return {"recovery_id": recovery_id}
    except WorkflowRevisionConflict as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "revision_conflict",
                "revision": error.revision,
                "etag": error.digest,
            },
        ) from error
    except WorkflowPersistenceError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)
        ) from error


@router.post("/workflows/recover/{recovery_id}", response_model=WorkflowResponse)
@traced("workspace.workflows.recover")
async def recover_workflow_endpoint(
    recovery_id: str,
    body: WorkflowRecoveryRequest,
    engine: BaseAgentEngine = Depends(get_agent_engine),
    service: WorkspaceService = Depends(get_workspace_service),
):
    _workflow_feature_enabled()
    workspace_dir = await service.resolve_workspace_dir(body.session_id, engine)
    workspace = service.lifecycle.get_by_session(body.session_id)
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found"
        )
    try:
        document = await service.workflows.recover(
            workspace["workspace_id"], workspace_dir, recovery_id, body.slug
        )
        return _workflow_response(document)
    except WorkflowPersistenceError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)
        ) from error


def _active_agent_id(request: Request | None = None) -> str:
    if request is not None:
        sync_manager = getattr(request.app.state, "agent_sync_manager", None)
        if sync_manager and getattr(sync_manager, "active_agent", None):
            return sync_manager.active_agent
    return "hermes"


def _workspace_service_http_exception(error: WorkspaceServiceError) -> HTTPException:
    if isinstance(error, WorkspaceNotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error))
    if isinstance(error, WorkspaceProtectedPathError):
        return HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": error.detail.code, "message": str(error)},
        )
    if isinstance(error, (WorkspaceConflictError, WorkspaceInvalidRequestError)):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(error)
    )


async def get_workspace_dir(
    session_id: str,
    engine: BaseAgentEngine = Depends(get_agent_engine),
    service: WorkspaceService = Depends(get_workspace_service),
) -> str:
    """Retrieve the workspace path for the given session ID, with fallback."""
    try:
        return await service.resolve_workspace_dir(session_id, engine)
    except WorkspaceServiceError as error:
        raise _workspace_service_http_exception(error)


# ── File Operations ──────────────────────────────────────────────────────


@router.get("/files", response_model=WorkspaceTreeResponse)
@traced("workspace.files.list")
async def list_workspace_files(
    session_id: str = Query(...),
    workspace_dir: str = Depends(get_workspace_dir),
    service: WorkspaceService = Depends(get_workspace_service),
):
    tree = await service.files.tree(workspace_dir)
    return WorkspaceTreeResponse(workspace=WorkspaceNodeResponse(**tree))


@router.get("/files/content")
@traced("workspace.files.read")
async def get_file_content(
    session_id: str = Query(...),
    path: str = Query(...),
    backup_id: Optional[str] = Query(None),
    workspace_dir: str = Depends(get_workspace_dir),
    service: WorkspaceService = Depends(get_workspace_service),
):
    try:
        result = await service.files.read(workspace_dir, path, backup_id)
        if result.binary:
            return FileResponse(result.path, filename=result.path.name)
        assert result.content is not None
        return JSONResponse(
            content={
                "content": result.content.decode("utf-8"),
                "path": path,
                "encoding": "utf-8",
            }
        )
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))
    except FileNotFoundError:
        label = (
            f"Backup not found: {backup_id}" if backup_id else f"File not found: {path}"
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=label)


@router.post(
    "/files", response_model=WorkspaceNodeResponse, status_code=status.HTTP_201_CREATED
)
@traced("workspace.files.create")
async def create_file_endpoint(
    body: FileCreateRequest,
    engine: BaseAgentEngine = Depends(get_agent_engine),
    service: WorkspaceService = Depends(get_workspace_service),
):
    workspace_dir = await service.resolve_workspace_dir(body.session_id, engine)
    try:
        node = await service.files.create(workspace_dir, body.path, body.type)
        return WorkspaceNodeResponse(**node)
    except (FileExistsError, ValueError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/files", status_code=status.HTTP_204_NO_CONTENT)
@traced("workspace.files.delete")
async def delete_file_endpoint(
    session_id: str = Query(...),
    path: str = Query(...),
    workspace_dir: str = Depends(get_workspace_dir),
    service: WorkspaceService = Depends(get_workspace_service),
):
    try:
        await service.files.delete(workspace_dir, path)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"File not found: {path}"
        )
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.put("/files/move", response_model=FileMoveResponse)
@traced("workspace.files.move")
async def move_file_endpoint(
    body: FileMoveRequest,
    engine: BaseAgentEngine = Depends(get_agent_engine),
    service: WorkspaceService = Depends(get_workspace_service),
):
    workspace_dir = await service.resolve_workspace_dir(body.session_id, engine)
    try:
        await service.files.move(workspace_dir, body.source_path, body.destination_path)
        return FileMoveResponse(
            success=True,
            source_path=body.source_path,
            destination_path=body.destination_path,
        )
    except (FileNotFoundError, FileExistsError, PermissionError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/files/content", response_model=FileContentSaveResponse)
@traced("workspace.files.save")
async def save_file_content_endpoint(
    body: FileContentSaveRequest,
    engine: BaseAgentEngine = Depends(get_agent_engine),
    service: WorkspaceService = Depends(get_workspace_service),
):
    workspace_dir = await service.resolve_workspace_dir(body.session_id, engine)
    try:
        await service.files.write(workspace_dir, body.path, body.content)
        return FileContentSaveResponse(success=True)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.post("/files/run", response_model=FileRunResponse)
@traced("workspace.files.run")
async def run_file_endpoint(
    body: FileRunRequest,
    request: Request,
    engine: BaseAgentEngine = Depends(get_agent_engine),
    service: WorkspaceService = Depends(get_workspace_service),
):
    try:
        surface_settings = getattr(
            request.app.state, "workspace_surface_settings", None
        )
        safe_display = bool(
            surface_settings
            and surface_settings.flags.model
            and surface_settings.flags.safe_display
        )
        res = await service.execute_workspace_file(
            body.session_id,
            body.path,
            engine,
            display_tokens=(
                surface_application().display_tokens if safe_display else None
            ),
            display_endpoint=(
                str(request.url_for("ingest_display")) if safe_display else None
            ),
            principal_id=getattr(request.state, "principal_id", "local-user"),
            trace_id=getattr(request.state, "trace_id", "no-active-trace"),
        )
        return FileRunResponse(
            success=res.success,
            stdout=res.stdout,
            stderr=res.stderr,
            exit_code=res.exit_code,
        )
    except WorkspaceServiceError as e:
        raise _workspace_service_http_exception(e)


# ── Git Operations ───────────────────────────────────────────────────────


@router.get("/git/status", response_model=GitStatusResponse)
@traced("workspace.git.status")
async def git_status_endpoint(
    session_id: str = Query(...),
    workspace_dir: str = Depends(get_workspace_dir),
    service: WorkspaceService = Depends(get_workspace_service),
):
    result = await service.git.status(workspace_dir)
    changes = [
        GitStatusItem(
            path=c["path"],
            git_status=c["git_status"],
            staged=c["staged"],
            file_size=c.get("file_size"),
        )
        for c in result["changes"]
    ]
    return GitStatusResponse(
        branch_name=result["branch_name"],
        is_clean=result["is_clean"],
        changes=changes,
    )


@router.get("/git/diff", response_model=GitDiffResponse)
@traced("workspace.git.diff")
async def git_diff_endpoint(
    session_id: str = Query(...),
    path: str = Query(...),
    workspace_dir: str = Depends(get_workspace_dir),
    service: WorkspaceService = Depends(get_workspace_service),
):
    return GitDiffResponse(path=path, diff=await service.git.diff(workspace_dir, path))


@router.post("/git/revert", response_model=GitRevertResponse)
@traced("workspace.git.revert")
async def git_revert_endpoint(
    body: GitRevertRequest,
    engine: BaseAgentEngine = Depends(get_agent_engine),
    service: WorkspaceService = Depends(get_workspace_service),
):
    workspace_dir = await service.resolve_workspace_dir(body.session_id, engine)
    await service.git.revert(workspace_dir, body.path)
    return GitRevertResponse(success=True, path=body.path)


@router.post("/git/commit", response_model=GitCommitResponse)
@traced("workspace.git.commit")
async def git_commit_endpoint(
    body: GitCommitRequest,
    engine: BaseAgentEngine = Depends(get_agent_engine),
    service: WorkspaceService = Depends(get_workspace_service),
):
    workspace_dir = await service.resolve_workspace_dir(body.session_id, engine)
    try:
        result = await service.git.commit(workspace_dir, body.message)
        return GitCommitResponse(success=True, **result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/git/history", response_model=GitHistoryResponse)
@traced("workspace.git.history")
async def git_history_endpoint(
    session_id: str = Query(...),
    workspace_dir: str = Depends(get_workspace_dir),
    service: WorkspaceService = Depends(get_workspace_service),
):
    commits = await service.git.history(workspace_dir)
    return GitHistoryResponse(commits=[GitCommitInfo(**c) for c in commits])


@router.post("/git/push", response_model=GitPushPullResponse)
@traced("workspace.git.push")
async def git_push_endpoint(
    body: GitPushPullRequest,
    engine: BaseAgentEngine = Depends(get_agent_engine),
    service: WorkspaceService = Depends(get_workspace_service),
):
    workspace_dir = await service.resolve_workspace_dir(body.session_id, engine)
    try:
        await service.git.push(workspace_dir)
        return GitPushPullResponse(success=True, message="Push successful")
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post("/git/pull")
@traced("workspace.git.pull")
async def git_pull_endpoint(
    body: GitPushPullRequest,
    engine: BaseAgentEngine = Depends(get_agent_engine),
    service: WorkspaceService = Depends(get_workspace_service),
):
    from workspace_service.use_cases import GitMergeConflict

    workspace_dir = await service.resolve_workspace_dir(body.session_id, engine)
    try:
        await service.git.pull(workspace_dir)
        return JSONResponse(content={"success": True, "message": "Pull successful"})
    except GitMergeConflict as e:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "success": False,
                "message": "Merge conflicts detected",
                "conflicted_files": list(e.files),
            },
        )
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post("/git/branch")
@traced("workspace.git.branch")
async def git_branch_endpoint(
    body: GitBranchRequest,
    engine: BaseAgentEngine = Depends(get_agent_engine),
    service: WorkspaceService = Depends(get_workspace_service),
):
    workspace_dir = await service.resolve_workspace_dir(body.session_id, engine)
    try:
        message = await service.git.branch(
            workspace_dir, body.branch_name, create=body.create
        )
        return {
            "success": True,
            "message": message,
        }
    except (ValueError, RuntimeError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Git operation failed: {e}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post("/git/merge")
@traced("workspace.git.merge")
async def git_merge_endpoint(
    body: GitMergeRequest,
    engine: BaseAgentEngine = Depends(get_agent_engine),
    service: WorkspaceService = Depends(get_workspace_service),
):
    from workspace_service.use_cases import GitMergeConflict

    workspace_dir = await service.resolve_workspace_dir(body.session_id, engine)
    try:
        message = await service.git.merge(workspace_dir, body.branch_name)
        return {
            "success": True,
            "message": message,
        }
    except GitMergeConflict as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Merge conflicts detected: {e.message}",
        )
    except (ValueError, RuntimeError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


# ── Workspace Config ─────────────────────────────────────────────────────


@router.get("/config", response_model=WorkspaceConfigGetResponse)
@traced("workspace.config.get")
async def get_workspace_config(
    session_id: str = Query(...),
    workspace_dir: str = Depends(get_workspace_dir),
    service: WorkspaceService = Depends(get_workspace_service),
):
    workspace = service.context.config(workspace_dir)
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found"
        )
    return WorkspaceConfigGetResponse(
        workspace_id=workspace["workspace_id"],
        git_remote_url=workspace.get("git_remote_url"),
        git_username=workspace.get("git_username"),
        has_token=workspace["has_token"],
        workspace_path=workspace.get("local_path"),
        workspace_prompt=workspace.get("workspace_prompt"),
        git_large_file_threshold=workspace.get("git_large_file_threshold"),
    )


@router.post("/config", response_model=WorkspaceConfigResponse)
@traced("workspace.config.update")
async def update_workspace_config(
    body: WorkspaceConfigRequest,
    request: Request,
    engine: BaseAgentEngine = Depends(get_agent_engine),
    service: WorkspaceService = Depends(get_workspace_service),
):
    try:
        workspace_id = await service.update_workspace_config(
            body.session_id,
            engine,
            git_remote_url=body.git_remote_url,
            git_username=body.git_username,
            git_token=body.git_token,
            workspace_prompt=body.workspace_prompt,
            git_large_file_threshold=body.git_large_file_threshold,
            agent_id=_active_agent_id(request),
        )
        return WorkspaceConfigResponse(success=True, workspace_id=workspace_id)
    except WorkspaceServiceError as e:
        raise _workspace_service_http_exception(e)


# ── Workspace Tools ──────────────────────────────────────────────────────


@router.get("/tools", response_model=WorkspaceToolsGetResponse)
@traced("workspace.tools.list")
async def get_workspace_tools_endpoint(
    session_id: str = Query(...),
    service: WorkspaceService = Depends(get_workspace_service),
):
    try:
        state = service.list_workspace_tools(session_id)
    except WorkspaceServiceError as error:
        raise _workspace_service_http_exception(error)
    return WorkspaceToolsGetResponse(
        session_id=state.session_id, enabled_tools=state.enabled_tools
    )


@router.post("/tools/toggle", response_model=WorkspaceToolToggleResponse)
@traced("workspace.tools.toggle")
async def toggle_workspace_tool_endpoint(
    body: WorkspaceToolToggleRequest,
    request: Request,
    engine: BaseAgentEngine = Depends(get_agent_engine),
    service: WorkspaceService = Depends(get_workspace_service),
):
    try:
        await service.resolve_workspace_dir(body.session_id, engine)
        state = service.set_workspace_tool_enabled(
            body.session_id, body.server_id, body.is_enabled
        )
    except WorkspaceServiceError as error:
        raise _workspace_service_http_exception(error)

    return WorkspaceToolToggleResponse(
        success=True,
        session_id=body.session_id,
        server_id=body.server_id,
        is_enabled=body.server_id in state.enabled_tools,
    )


async def _workspace_mcp_status_response(
    *,
    workspace: dict,
    service: WorkspaceService,
    request: Request | None = None,
) -> WorkspaceMcpStatusResponse:
    workspace_id = workspace["workspace_id"]
    mcp_engine = (
        getattr(request.app.state, "mcp_engine", None)
        if request and api_mcp_autostart_enabled()
        else None
    )
    result = await service.tools.status(
        workspace,
        mcp_engine=mcp_engine,
        config_paths=hermes_config_paths(),
    )
    return WorkspaceMcpStatusResponse(
        workspace_id=workspace_id,
        status=result["status"],
        message=result["message"],
        running_mcps=[RunningMcpInfo(**item) for item in result["running_mcps"]],
    )


@router.get("/mcp-status", response_model=WorkspaceMcpStatusResponse)
@traced("workspace.mcp-status")
async def get_workspace_mcp_status_endpoint(
    request: Request,
    session_id: str = Query(...),
    workspace_dir: str = Depends(get_workspace_dir),
    service: WorkspaceService = Depends(get_workspace_service),
):
    workspace = service.lifecycle.get_by_session(session_id)
    if not workspace:
        return WorkspaceMcpStatusResponse(
            status="ok", message="No active workspace.", running_mcps=[]
        )
    return await _workspace_mcp_status_response(
        workspace=workspace, service=service, request=request
    )


# ── Workspace CRUD ───────────────────────────────────────────────────────


@router.post(
    "/create", response_model=WorkspaceListEntry, status_code=status.HTTP_201_CREATED
)
@traced("workspace.create")
async def create_workspace_endpoint(
    body: WorkspaceCreateRequest,
    request: Request,
    engine: BaseAgentEngine = Depends(get_agent_engine),
    service: WorkspaceService = Depends(get_workspace_service),
):
    logger.info("workspace_create", name=body.name, local_path=body.local_path)
    try:
        ws = await service.create_workspace(
            body.name,
            body.local_path,
            engine,
            agent_id=_active_agent_id(request),
        )
        return WorkspaceListEntry(
            workspace_id=ws.workspace_id,
            session_id=ws.session_id,
            workspace_name=ws.workspace_name,
            local_path=ws.local_path,
            git_remote_url=ws.git_remote_url,
            git_username=ws.git_username,
            enabled_tools=ws.enabled_tools,
            updated_at=ws.updated_at,
        )
    except WorkspaceServiceError as e:
        raise _workspace_service_http_exception(e)
    except Exception as e:
        logger.exception("workspace_create_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/by-id/{workspace_id}", response_model=WorkspaceListEntry)
@traced("workspace.get")
async def get_workspace_by_id_endpoint(
    workspace_id: str, service: WorkspaceService = Depends(get_workspace_service)
):
    try:
        ws = service.require_safe_workspace(workspace_id)
    except WorkspaceServiceError as error:
        raise _workspace_service_http_exception(error)
    return serialize_workspace(ws)


@router.get("/by-id/{workspace_id}/sessions", response_model=WorkspaceSessionsResponse)
@traced("workspace.sessions.list")
async def list_workspace_sessions_endpoint(
    workspace_id: str,
    request: Request,
    engine: BaseAgentEngine = Depends(get_agent_engine),
    service: WorkspaceService = Depends(get_workspace_service),
):
    try:
        records = await service.list_workspace_sessions(
            workspace_id, engine, agent_id=_active_agent_id(request)
        )
    except WorkspaceServiceError as error:
        raise _workspace_service_http_exception(error)
    return WorkspaceSessionsResponse(
        workspace_id=workspace_id,
        sessions=[
            WorkspaceSessionInfo(
                session_id=record.session_id,
                title=record.title,
                created_at=record.created_at,
                updated_at=record.updated_at,
                message_count=record.message_count,
            )
            for record in records
        ],
    )


@router.post(
    "/by-id/{workspace_id}/sessions", response_model=WorkspaceSessionCreateResponse
)
@traced("workspace.sessions.create")
async def create_workspace_session_endpoint(
    workspace_id: str,
    request: Request,
    engine: BaseAgentEngine = Depends(get_agent_engine),
    service: WorkspaceService = Depends(get_workspace_service),
):
    try:
        record = await service.create_workspace_session(
            workspace_id, engine, agent_id=_active_agent_id(request)
        )
        return WorkspaceSessionCreateResponse(
            workspace_id=workspace_id,
            session_id=record.session_id,
            title=record.title,
            created_at=record.created_at,
        )
    except WorkspaceServiceError as e:
        raise _workspace_service_http_exception(e)


@router.post(
    "/by-id/{workspace_id}/session/select",
    response_model=WorkspaceSessionSelectResponse,
)
@traced("workspace.sessions.select")
async def select_workspace_session_endpoint(
    workspace_id: str,
    body: WorkspaceSessionSelectRequest,
    request: Request,
    engine: BaseAgentEngine = Depends(get_agent_engine),
    service: WorkspaceService = Depends(get_workspace_service),
):
    try:
        activation = await service.select_workspace_session(
            workspace_id, body.session_id, engine, agent_id=_active_agent_id(request)
        )
    except WorkspaceServiceError as e:
        raise _workspace_service_http_exception(e)

    return WorkspaceSessionSelectResponse(
        success=True, workspace_id=workspace_id, session_id=activation.session_id
    )


@router.get("/by-id/{workspace_id}/tools", response_model=WorkspaceToolsByIdResponse)
@traced("workspace.tools.list_by_workspace")
async def get_workspace_tools_by_id_endpoint(
    workspace_id: str, service: WorkspaceService = Depends(get_workspace_service)
):
    try:
        state = service.list_workspace_tools_by_workspace(workspace_id)
    except WorkspaceServiceError as error:
        raise _workspace_service_http_exception(error)
    return WorkspaceToolsByIdResponse(
        workspace_id=workspace_id, enabled_tools=state.enabled_tools
    )


@router.post(
    "/by-id/{workspace_id}/tools/toggle",
    response_model=WorkspaceToolToggleByIdResponse,
)
@traced("workspace.tools.toggle_by_workspace")
async def toggle_workspace_tool_by_id_endpoint(
    workspace_id: str,
    body: WorkspaceToolToggleByIdRequest,
    service: WorkspaceService = Depends(get_workspace_service),
):
    try:
        state = service.set_workspace_tool_enabled_by_workspace(
            workspace_id, body.server_id, body.is_enabled
        )
    except WorkspaceServiceError as error:
        raise _workspace_service_http_exception(error)
    return WorkspaceToolToggleByIdResponse(
        success=True,
        workspace_id=workspace_id,
        server_id=body.server_id,
        is_enabled=body.server_id in state.enabled_tools,
    )


@router.get(
    "/by-id/{workspace_id}/mcp-status", response_model=WorkspaceMcpStatusResponse
)
@traced("workspace.mcp-status-by-id")
async def get_workspace_mcp_status_by_id_endpoint(
    workspace_id: str,
    request: Request,
    service: WorkspaceService = Depends(get_workspace_service),
):
    try:
        workspace = service.require_safe_workspace(workspace_id)
    except WorkspaceServiceError as error:
        raise _workspace_service_http_exception(error)
    return await _workspace_mcp_status_response(
        workspace=workspace, service=service, request=request
    )


@router.post("/by-id/{workspace_id}/context/save")
@traced("workspace.context.save")
async def save_workspace_context_endpoint(
    workspace_id: str,
    body: ContextSaveRequest,
    service: WorkspaceService = Depends(get_workspace_service),
):
    try:
        service.require_safe_workspace(workspace_id)
    except WorkspaceServiceError as error:
        raise _workspace_service_http_exception(error)
    service.context.save(workspace_id, body.context_data)
    return {"success": True}


@router.get("/by-id/{workspace_id}/context/load")
@traced("workspace.context.load")
async def load_workspace_context_endpoint(
    workspace_id: str, service: WorkspaceService = Depends(get_workspace_service)
):
    try:
        service.require_safe_workspace(workspace_id)
    except WorkspaceServiceError as error:
        raise _workspace_service_http_exception(error)
    ctx = service.context.load(workspace_id)
    if not ctx:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No saved context found"
        )
    return ctx


@router.get("/recent", response_model=WorkspaceListResponse)
@traced("workspace.list")
async def list_recent_workspaces_endpoint(
    service: WorkspaceService = Depends(get_workspace_service),
):
    workspaces = [
        workspace
        for workspace in service.lifecycle.list_recent(limit=50)
        if service.workspace_path_is_safe(workspace["local_path"])
    ][:5]
    return WorkspaceListResponse(
        workspaces=[serialize_workspace(w) for w in workspaces]
    )


@router.get("/list", response_model=WorkspaceListResponse)
@traced("workspace.list")
async def list_all_workspaces_endpoint(
    service: WorkspaceService = Depends(get_workspace_service),
):
    workspaces = [
        workspace
        for workspace in service.lifecycle.list_all()
        if service.workspace_path_is_safe(workspace["local_path"])
    ]
    return WorkspaceListResponse(
        workspaces=[serialize_workspace(w) for w in workspaces]
    )


@router.post("/activate", response_model=WorkspaceActivateResponse)
@traced("workspace.activate")
async def activate_workspace_endpoint(
    body: WorkspaceActivateRequest,
    request: Request,
    engine: BaseAgentEngine = Depends(get_agent_engine),
    service: WorkspaceService = Depends(get_workspace_service),
):
    session_id = body.session_id
    logger.info("workspace_activate", session_id=session_id)

    workspace = service.lifecycle.get_by_session(session_id)
    if not workspace:
        local_path = await service.resolve_workspace_dir(session_id, engine)
    else:
        local_path = workspace["local_path"]

    try:
        activation = await service.activate_workspace(
            session_id,
            engine,
            local_path=local_path,
            agent_id=_active_agent_id(request),
        )
    except WorkspaceServiceError as error:
        raise _workspace_service_http_exception(error)
    session_id = activation.session_id
    local_path = activation.workspace_path

    try:
        await service.reconcile_runtime(
            session_id,
            mcp_engine=(
                getattr(request.app.state, "mcp_engine", None)
                if api_mcp_autostart_enabled()
                else None
            ),
            sync_manager=getattr(request.app.state, "agent_sync_manager", None),
        )
    except Exception as e:
        logger.error("workspace_runtime_sync_failed_on_activate", error=str(e))

    return WorkspaceActivateResponse(
        success=True, session_id=session_id, workspace_path=local_path
    )


@router.get("/default-dir", response_model=DefaultWorkspaceDirResponse)
@traced("workspace.get")
async def get_default_workspace_dir_endpoint():
    default_path = get_default_workspace_parent_dir()
    return DefaultWorkspaceDirResponse(default_dir=default_path)


@router.post("/by-id/{workspace_id}/session")
@traced("workspace.session.update")
async def update_workspace_session_endpoint(
    workspace_id: str,
    body: WorkspaceSessionUpdateRequest,
    request: Request,
    engine: BaseAgentEngine = Depends(get_agent_engine),
    service: WorkspaceService = Depends(get_workspace_service),
):
    session_id = body.session_id
    workspace = service.lifecycle.get_by_id(workspace_id)
    if workspace:
        try:
            activation = await service.select_workspace_session(
                workspace_id,
                body.session_id,
                engine,
                agent_id=_active_agent_id(request),
            )
        except WorkspaceServiceError as e:
            raise _workspace_service_http_exception(e)
        session_id = activation.session_id

        try:
            await service.reconcile_runtime(
                session_id,
                mcp_engine=(
                    getattr(request.app.state, "mcp_engine", None)
                    if api_mcp_autostart_enabled()
                    else None
                ),
                sync_manager=getattr(request.app.state, "agent_sync_manager", None),
            )
        except Exception as e:
            logger.error(
                "workspace_runtime_sync_failed_on_session_update", error=str(e)
            )

    return {"success": True, "session_id": session_id}


@router.post("/files/backup", response_model=FileBackupResponse)
@traced("workspace.files.backup")
async def backup_file_content_endpoint(
    body: FileBackupRequest,
    engine: BaseAgentEngine = Depends(get_agent_engine),
    service: WorkspaceService = Depends(get_workspace_service),
):
    workspace_dir = await service.resolve_workspace_dir(body.session_id, engine)
    try:
        backup_id = await service.files.backup(workspace_dir, body.path, body.content)
        return FileBackupResponse(success=True, backup_id=backup_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.delete("/files/backup", response_model=FileContentSaveResponse)
@traced("workspace.files.backup.delete")
async def delete_file_backup_endpoint(
    body: FileBackupDeleteRequest,
    engine: BaseAgentEngine = Depends(get_agent_engine),
    service: WorkspaceService = Depends(get_workspace_service),
):
    workspace_dir = await service.resolve_workspace_dir(body.session_id, engine)
    try:
        await service.files.delete_backup(workspace_dir, body.backup_id)
        return FileContentSaveResponse(success=True)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
