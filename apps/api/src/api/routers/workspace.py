"""
Workspace router — thin HTTP handlers only.

All Pydantic models are in api.schemas.workspace.
All business logic is owned by workspace_service application operations.
All handlers are decorated with @traced for OTel span creation.
"""

import structlog
from fastapi import APIRouter, Depends, Query, HTTPException, status, Response, Request
from fastapi.responses import FileResponse, JSONResponse
from typing import Optional

from agent_adapters import BaseAgentEngine
from agent_adapters.hermes_gateway import hermes_config_paths
from core.tracing import traced
from api.routers.agent import get_agent_engine
from api.composition import workspace_service
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
)

logger = structlog.get_logger(__name__)
router = APIRouter()


def get_default_workspace_parent_dir() -> str:
    """Return the per-user parent directory for Wright-created workspaces."""
    return default_workspace_parent_dir()


def get_workspace_service() -> WorkspaceService:
    return workspace_service()


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
    engine: BaseAgentEngine = Depends(get_agent_engine),
    service: WorkspaceService = Depends(get_workspace_service),
):
    try:
        res = await service.execute_workspace_file(body.session_id, body.path, engine)
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
    workspace_dir: str = Depends(get_workspace_dir),
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
    mcp_engine = getattr(request.app.state, "mcp_engine", None) if request else None
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
            mcp_engine=getattr(request.app.state, "mcp_engine", None),
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
                mcp_engine=getattr(request.app.state, "mcp_engine", None),
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
