"""
Workspace router — thin HTTP handlers only.

All Pydantic models are in api.schemas.workspace.
All business logic is in core.workspace and api.services.hermes_sync.
All handlers are decorated with @traced for OTel span creation.
"""

import os
import uuid
import structlog
from fastapi import APIRouter, Depends, Query, HTTPException, status, Response, Request
from fastapi.responses import FileResponse, JSONResponse

from agent_adapters import BaseAgentEngine
from core import WorkspaceManager
from core.workspace import (
    get_workspace_by_session,
    create_workspace,
    get_workspace_enabled_tools,
    update_workspace_enabled_tools,
    get_recent_workspaces,
    get_all_workspaces,
    create_workspace_from_dashboard,
    get_workspace_by_id,
    save_agent_context,
    load_agent_context,
    update_workspace_remote,
    activate_workspace,
    sync_workspace_runners,
    update_workspace_session,
)
from core.tracing import traced
from api.routers.agent import get_agent_engine
from api.config import DATABASE_PATH
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
    WorkspaceToolsGetResponse,
    WorkspaceToolToggleRequest,
    WorkspaceToolToggleResponse,
    WorkspaceListEntry,
    WorkspaceListResponse,
    WorkspaceCreateRequest,
    WorkspaceActivateRequest,
    WorkspaceActivateResponse,
    ContextSaveRequest,
    DefaultWorkspaceDirResponse,
    serialize_workspace,
    WorkspaceSessionUpdateRequest,
)

logger = structlog.get_logger(__name__)
router = APIRouter()


async def get_workspace_dir(
    session_id: str, engine: BaseAgentEngine = Depends(get_agent_engine)
) -> str:
    """Retrieve the workspace path for the given session ID, with fallback."""
    workspace = get_workspace_by_session(DATABASE_PATH, session_id)
    if workspace:
        return workspace["local_path"]
    workspace_path = await engine.get_session_workspace(session_id)
    if not workspace_path:
        workspace_path = f"/home/burhop/workspace/{session_id}"
    os.makedirs(workspace_path, exist_ok=True)
    workspace_id = str(uuid.uuid4())
    create_workspace(
        DATABASE_PATH,
        workspace_id,
        session_id,
        workspace_path,
        workspace_name=os.path.basename(workspace_path),
    )
    return workspace_path


# ── File Operations ──────────────────────────────────────────────────────


@router.get("/files", response_model=WorkspaceTreeResponse)
@traced("workspace.files.list")
async def list_workspace_files(
    session_id: str = Query(...), workspace_dir: str = Depends(get_workspace_dir)
):
    mgr = WorkspaceManager(workspace_dir)
    tree = mgr.get_workspace_tree()
    # Override root node name with the human-readable workspace name
    workspace = get_workspace_by_session(DATABASE_PATH, session_id)
    if workspace:
        display_name = workspace.get("workspace_name") or os.path.basename(
            workspace["local_path"]
        )
        tree["name"] = display_name
    return WorkspaceTreeResponse(workspace=WorkspaceNodeResponse(**tree))


@router.get("/files/content")
@traced("workspace.files.read")
async def get_file_content(
    session_id: str = Query(...),
    path: str = Query(...),
    workspace_dir: str = Depends(get_workspace_dir),
):
    mgr = WorkspaceManager(workspace_dir)
    try:
        abs_path = mgr.sanitize_path(path)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    if not os.path.isfile(abs_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"File not found: {path}"
        )
    ext = os.path.splitext(abs_path)[1].lower()
    binary_extensions = {
        ".stl",
        ".obj",
        ".step",
        ".stp",
        ".iges",
        ".igs",
        ".3mf",
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".bmp",
        ".pdf",
    }
    if ext in binary_extensions:
        return FileResponse(abs_path, filename=os.path.basename(abs_path))
    try:
        content = mgr.read_file_content(path)
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            return FileResponse(abs_path, filename=os.path.basename(abs_path))
        return JSONResponse(
            content={"content": text, "path": path, "encoding": "utf-8"}
        )
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"File not found: {path}"
        )


@router.post(
    "/files", response_model=WorkspaceNodeResponse, status_code=status.HTTP_201_CREATED
)
@traced("workspace.files.create")
async def create_file_endpoint(
    body: FileCreateRequest, engine: BaseAgentEngine = Depends(get_agent_engine)
):
    workspace_dir = await get_workspace_dir(body.session_id, engine)
    mgr = WorkspaceManager(workspace_dir)
    try:
        node = mgr.create_file_node(body.path, body.type)
        return WorkspaceNodeResponse(**node)
    except (FileExistsError, ValueError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/files", status_code=status.HTTP_204_NO_CONTENT)
@traced("workspace.files.delete")
async def delete_file_endpoint(
    session_id: str = Query(...),
    path: str = Query(...),
    workspace_dir: str = Depends(get_workspace_dir),
):
    mgr = WorkspaceManager(workspace_dir)
    try:
        mgr.delete_file_node(path)
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
    body: FileMoveRequest, engine: BaseAgentEngine = Depends(get_agent_engine)
):
    workspace_dir = await get_workspace_dir(body.session_id, engine)
    mgr = WorkspaceManager(workspace_dir)
    try:
        mgr.move_file_node(body.source_path, body.destination_path)
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
    body: FileContentSaveRequest, engine: BaseAgentEngine = Depends(get_agent_engine)
):
    workspace_dir = await get_workspace_dir(body.session_id, engine)
    mgr = WorkspaceManager(workspace_dir)
    try:
        mgr.write_file_content(body.path, body.content.encode("utf-8"))
        return FileContentSaveResponse(success=True)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


# ── Git Operations ───────────────────────────────────────────────────────


@router.get("/git/status", response_model=GitStatusResponse)
@traced("workspace.git.status")
async def git_status_endpoint(
    session_id: str = Query(...), workspace_dir: str = Depends(get_workspace_dir)
):
    mgr = WorkspaceManager(workspace_dir)
    s = mgr.get_git_status()
    return GitStatusResponse(
        branch_name=s["branch_name"],
        is_clean=s["is_clean"],
        changes=[GitStatusItem(**c) for c in s["changes"]],
    )


@router.get("/git/diff", response_model=GitDiffResponse)
@traced("workspace.git.diff")
async def git_diff_endpoint(
    session_id: str = Query(...),
    path: str = Query(...),
    workspace_dir: str = Depends(get_workspace_dir),
):
    mgr = WorkspaceManager(workspace_dir)
    return GitDiffResponse(path=path, diff=mgr.get_git_diff(path))


@router.post("/git/revert", response_model=GitRevertResponse)
@traced("workspace.git.revert")
async def git_revert_endpoint(
    body: GitRevertRequest, engine: BaseAgentEngine = Depends(get_agent_engine)
):
    workspace_dir = await get_workspace_dir(body.session_id, engine)
    mgr = WorkspaceManager(workspace_dir)
    mgr.revert_file(body.path)
    return GitRevertResponse(success=True, path=body.path)


@router.post("/git/commit", response_model=GitCommitResponse)
@traced("workspace.git.commit")
async def git_commit_endpoint(
    body: GitCommitRequest, engine: BaseAgentEngine = Depends(get_agent_engine)
):
    workspace_dir = await get_workspace_dir(body.session_id, engine)
    mgr = WorkspaceManager(workspace_dir)
    try:
        result = mgr.commit_changes(body.message)
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
    session_id: str = Query(...), workspace_dir: str = Depends(get_workspace_dir)
):
    mgr = WorkspaceManager(workspace_dir)
    commits = mgr.get_git_history()
    return GitHistoryResponse(commits=[GitCommitInfo(**c) for c in commits])


@router.post("/git/push", response_model=GitPushPullResponse)
@traced("workspace.git.push")
async def git_push_endpoint(
    body: GitPushPullRequest, engine: BaseAgentEngine = Depends(get_agent_engine)
):
    workspace_dir = await get_workspace_dir(body.session_id, engine)
    workspace = get_workspace_by_session(DATABASE_PATH, body.session_id)
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found"
        )
    remote_url = workspace.get("git_remote_url")
    if not remote_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Git remote URL not configured",
        )
    mgr = WorkspaceManager(workspace_dir)
    try:
        mgr.push_remote(
            remote_url, workspace.get("git_username"), workspace.get("git_token")
        )
        return GitPushPullResponse(success=True, message="Push successful")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post("/git/pull")
@traced("workspace.git.pull")
async def git_pull_endpoint(
    body: GitPushPullRequest, engine: BaseAgentEngine = Depends(get_agent_engine)
):
    workspace_dir = await get_workspace_dir(body.session_id, engine)
    from core.workspace import MergeConflictError

    workspace = get_workspace_by_session(DATABASE_PATH, body.session_id)
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found"
        )
    remote_url = workspace.get("git_remote_url")
    if not remote_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Git remote URL not configured",
        )
    mgr = WorkspaceManager(workspace_dir)
    try:
        mgr.pull_remote(
            remote_url, workspace.get("git_username"), workspace.get("git_token")
        )
        return JSONResponse(content={"success": True, "message": "Pull successful"})
    except MergeConflictError as e:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "success": False,
                "message": "Merge conflicts detected",
                "conflicted_files": e.conflicted_files,
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


# ── Workspace Config ─────────────────────────────────────────────────────


@router.get("/config", response_model=WorkspaceConfigGetResponse)
@traced("workspace.config.get")
async def get_workspace_config(
    session_id: str = Query(...), workspace_dir: str = Depends(get_workspace_dir)
):
    workspace = get_workspace_by_session(DATABASE_PATH, session_id)
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found"
        )
    return WorkspaceConfigGetResponse(
        workspace_id=workspace["workspace_id"],
        git_remote_url=workspace.get("git_remote_url"),
        git_username=workspace.get("git_username"),
        has_token=bool(workspace.get("git_token")),
        workspace_path=workspace.get("local_path"),
    )


@router.post("/config", response_model=WorkspaceConfigResponse)
@traced("workspace.config.update")
async def update_workspace_config(
    body: WorkspaceConfigRequest, engine: BaseAgentEngine = Depends(get_agent_engine)
):
    await get_workspace_dir(body.session_id, engine)
    workspace = get_workspace_by_session(DATABASE_PATH, body.session_id)
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found"
        )
    update_workspace_remote(
        DATABASE_PATH,
        body.session_id,
        body.git_remote_url,
        body.git_username,
        body.git_token,
    )
    return WorkspaceConfigResponse(success=True, workspace_id=workspace["workspace_id"])


# ── Workspace Tools ──────────────────────────────────────────────────────


@router.get("/tools", response_model=WorkspaceToolsGetResponse)
@traced("workspace.tools.list")
async def get_workspace_tools_endpoint(
    session_id: str = Query(...), workspace_dir: str = Depends(get_workspace_dir)
):
    enabled = get_workspace_enabled_tools(DATABASE_PATH, session_id) or []
    return WorkspaceToolsGetResponse(session_id=session_id, enabled_tools=enabled)


@router.post("/tools/toggle", response_model=WorkspaceToolToggleResponse)
@traced("workspace.tools.toggle")
async def toggle_workspace_tool_endpoint(
    body: WorkspaceToolToggleRequest,
    request: Request,
    engine: BaseAgentEngine = Depends(get_agent_engine),
):
    await get_workspace_dir(body.session_id, engine)
    current = get_workspace_enabled_tools(DATABASE_PATH, body.session_id) or []
    if body.is_enabled and body.server_id not in current:
        current.append(body.server_id)
    elif not body.is_enabled and body.server_id in current:
        current.remove(body.server_id)
    update_workspace_enabled_tools(DATABASE_PATH, body.session_id, current)

    from api.services.hermes_sync import (
        sync_workspace_tools_to_hermes,
        restart_hermes_background,
    )

    sync_workspace_tools_to_hermes(body.session_id, DATABASE_PATH)
    restart_hermes_background()

    sync_manager = getattr(request.app.state, "agent_sync_manager", None)
    if sync_manager:
        sync_manager.sync_workspace_tools(body.session_id)

    return WorkspaceToolToggleResponse(
        success=True,
        session_id=body.session_id,
        server_id=body.server_id,
        is_enabled=body.is_enabled,
    )


# ── Workspace CRUD ───────────────────────────────────────────────────────


@router.post(
    "/create", response_model=WorkspaceListEntry, status_code=status.HTTP_201_CREATED
)
@traced("workspace.create")
async def create_workspace_endpoint(
    body: WorkspaceCreateRequest, engine: BaseAgentEngine = Depends(get_agent_engine)
):
    logger.info("workspace_create", name=body.name, local_path=body.local_path)
    try:
        session_info = await engine.create_session(body.local_path)
        ws = create_workspace_from_dashboard(
            DATABASE_PATH, body.name, body.local_path, session_info.session_id
        )
        return serialize_workspace(ws)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.exception("workspace_create_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/by-id/{workspace_id}", response_model=WorkspaceListEntry)
@traced("workspace.get")
async def get_workspace_by_id_endpoint(workspace_id: str):
    ws = get_workspace_by_id(DATABASE_PATH, workspace_id)
    if not ws:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found"
        )
    return serialize_workspace(ws)


@router.post("/by-id/{workspace_id}/context/save")
@traced("workspace.context.save")
async def save_workspace_context_endpoint(workspace_id: str, body: ContextSaveRequest):
    import json

    save_agent_context(DATABASE_PATH, workspace_id, json.dumps(body.context_data))
    return {"success": True}


@router.get("/by-id/{workspace_id}/context/load")
@traced("workspace.context.load")
async def load_workspace_context_endpoint(workspace_id: str):
    import json

    ctx = load_agent_context(DATABASE_PATH, workspace_id)
    if not ctx:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No saved context found"
        )
    try:
        parsed = json.loads(ctx["context_data"])
    except Exception:
        parsed = ctx["context_data"]
    return {
        "workspace_id": workspace_id,
        "context_data": parsed,
        "updated_at": ctx.get("updated_at"),
    }


@router.get("/recent", response_model=WorkspaceListResponse)
@traced("workspace.list")
async def list_recent_workspaces_endpoint():
    workspaces = get_recent_workspaces(DATABASE_PATH, limit=5)
    return WorkspaceListResponse(
        workspaces=[serialize_workspace(w) for w in workspaces]
    )


@router.get("/list", response_model=WorkspaceListResponse)
@traced("workspace.list")
async def list_all_workspaces_endpoint():
    workspaces = get_all_workspaces(DATABASE_PATH)
    return WorkspaceListResponse(
        workspaces=[serialize_workspace(w) for w in workspaces]
    )


@router.post("/activate", response_model=WorkspaceActivateResponse)
@traced("workspace.activate")
async def activate_workspace_endpoint(
    body: WorkspaceActivateRequest,
    request: Request,
    engine: BaseAgentEngine = Depends(get_agent_engine),
):
    session_id = body.session_id
    logger.info("workspace_activate", session_id=session_id)

    workspace = get_workspace_by_session(DATABASE_PATH, session_id)
    if not workspace:
        local_path = await get_workspace_dir(session_id, engine)
    else:
        local_path = workspace["local_path"]

    session_id = await activate_workspace(DATABASE_PATH, session_id, local_path, engine)

    mcp_engine = getattr(request.app.state, "mcp_engine", None)
    if mcp_engine:
        try:
            await sync_workspace_runners(DATABASE_PATH, session_id, mcp_engine)
        except Exception as e:
            logger.error("mcp_runner_sync_failed_on_activate", error=str(e))

    sync_manager = getattr(request.app.state, "agent_sync_manager", None)
    if sync_manager:
        try:
            sync_manager.sync_workspace_tools(session_id)
        except Exception as e:
            logger.error("agent_tool_sync_failed_on_activate", error=str(e))

    return WorkspaceActivateResponse(
        success=True, session_id=session_id, workspace_path=local_path
    )


@router.get("/default-dir", response_model=DefaultWorkspaceDirResponse)
@traced("workspace.get")
async def get_default_workspace_dir_endpoint():
    default_path = os.path.join(os.path.expanduser("~"), "wright")
    return DefaultWorkspaceDirResponse(default_dir=default_path)


@router.post("/by-id/{workspace_id}/session")
@traced("workspace.session.update")
async def update_workspace_session_endpoint(
    workspace_id: str, body: WorkspaceSessionUpdateRequest
):
    update_workspace_session(DATABASE_PATH, workspace_id, body.session_id)
    return {"success": True}
