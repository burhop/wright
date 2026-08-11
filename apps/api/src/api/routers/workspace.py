"""
Workspace router — thin HTTP handlers only.

All Pydantic models are in api.schemas.workspace.
All business logic is owned by workspace_service application operations.
All handlers are decorated with @traced for OTel span creation.
"""

import asyncio
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
    WorkflowReviewRequest,
    WorkflowReviewResponse,
    WorkflowOperationsListResponse,
    WorkflowRunHistoryResponse,
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
from workspace_service.workflow_graph import WorkflowGraphError
from workspace_service.workflow_catalog import WorkflowTemplateError
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


def _run_response(run, record=None) -> WorkflowRunResponse:
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
    return WorkflowReviewResponse(
        workflow_id=record.workflow_id,
        slug=record.slug,
        revision=record.revision,
        etag=record.digest,
        review_state=record.review.state if record.review else None,
        reviewer=record.review.reviewer if record.review else None,
        reviewed_at=record.review.updated_at if record.review else None,
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
            graph=body.graph,
            inputs=body.inputs,
            context=body.context,
            timeout_seconds=body.timeout_seconds,
        )
        return _run_response(run, service.workflow_runner.result(run.run_id))
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
        return _run_response(run, service.workflow_runner.result(run.run_id))
    except (WorkflowRunnerError, WorkflowOperationsError) as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(error)
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
        return _run_response(run, service.workflow_runner.result(run.run_id))
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
            )
        )
    except (WorkflowOperationsError, WorkflowPersistenceError) as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)
        ) from error


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
    return await service.resolve_workspace_dir(session_id, engine)


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
    state = service.list_workspace_tools(session_id)
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
    await service.resolve_workspace_dir(body.session_id, engine)
    service.set_workspace_tool_enabled(body.session_id, body.server_id, body.is_enabled)

    return WorkspaceToolToggleResponse(
        success=True,
        session_id=body.session_id,
        server_id=body.server_id,
        is_enabled=body.is_enabled,
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
    ws = service.lifecycle.get_by_id(workspace_id)
    if not ws:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found"
        )
    return serialize_workspace(ws)


@router.get("/by-id/{workspace_id}/sessions", response_model=WorkspaceSessionsResponse)
@traced("workspace.sessions.list")
async def list_workspace_sessions_endpoint(
    workspace_id: str,
    request: Request,
    engine: BaseAgentEngine = Depends(get_agent_engine),
    service: WorkspaceService = Depends(get_workspace_service),
):
    records = await service.list_workspace_sessions(
        workspace_id, engine, agent_id=_active_agent_id(request)
    )
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
    state = service.list_workspace_tools_by_workspace(workspace_id)
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
    service.set_workspace_tool_enabled_by_workspace(
        workspace_id, body.server_id, body.is_enabled
    )
    return WorkspaceToolToggleByIdResponse(
        success=True,
        workspace_id=workspace_id,
        server_id=body.server_id,
        is_enabled=body.is_enabled,
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
    workspace = service.lifecycle.get_by_id(workspace_id)
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found"
        )
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
    service.context.save(workspace_id, body.context_data)
    return {"success": True}


@router.get("/by-id/{workspace_id}/context/load")
@traced("workspace.context.load")
async def load_workspace_context_endpoint(
    workspace_id: str, service: WorkspaceService = Depends(get_workspace_service)
):
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
    workspaces = service.lifecycle.list_recent(limit=5)
    return WorkspaceListResponse(
        workspaces=[serialize_workspace(w) for w in workspaces]
    )


@router.get("/list", response_model=WorkspaceListResponse)
@traced("workspace.list")
async def list_all_workspaces_endpoint(
    service: WorkspaceService = Depends(get_workspace_service),
):
    workspaces = service.lifecycle.list_all()
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

    activation = await service.activate_workspace(
        session_id,
        engine,
        local_path=local_path,
        agent_id=_active_agent_id(request),
    )
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
