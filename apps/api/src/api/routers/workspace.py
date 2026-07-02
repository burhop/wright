"""
Workspace router — thin HTTP handlers only.

All Pydantic models are in api.schemas.workspace.
All business logic is in core.workspace and api.services.wright_gateway_sync.
All handlers are decorated with @traced for OTel span creation.
"""

import os
import sqlite3
import structlog
from fastapi import APIRouter, Depends, Query, HTTPException, status, Response, Request
from fastapi.responses import FileResponse, JSONResponse
from typing import Optional

from agent_adapters import BaseAgentEngine
from agent_adapters.hermes_gateway import hermes_config_paths
from core import WorkspaceManager
from core.workspace import (
    get_workspace_by_session,
    get_workspace_enabled_tools,
    get_recent_workspaces,
    get_all_workspaces,
    get_workspace_by_id,
    get_workspace_by_path,
    save_agent_context,
    load_agent_context,
    sync_workspace_runners,
    update_workspace_session,
)
from core.tracing import traced
from api.routers.agent import get_agent_engine
from api.config import DATABASE_PATH
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
    FileRunRequest,
    FileRunResponse,
)

logger = structlog.get_logger(__name__)
router = APIRouter()


def get_default_workspace_parent_dir() -> str:
    """Return the per-user parent directory for Wright-created workspaces."""
    return default_workspace_parent_dir()


def get_workspace_service() -> WorkspaceService:
    return WorkspaceService(DATABASE_PATH)


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
    if not hasattr(service, "resolve_workspace_dir"):
        service = get_workspace_service()
    return await service.resolve_workspace_dir(session_id, engine)


# ── File Operations ──────────────────────────────────────────────────────


@router.get("/files", response_model=WorkspaceTreeResponse)
@traced("workspace.files.list")
async def list_workspace_files(
    session_id: str = Query(...), workspace_dir: str = Depends(get_workspace_dir)
):
    mgr = WorkspaceManager(workspace_dir)
    tree = mgr.get_workspace_tree()
    # Override root node name with the human-readable workspace name
    workspace = get_workspace_by_path(DATABASE_PATH, workspace_dir)
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
    backup_id: Optional[str] = Query(None),
    workspace_dir: str = Depends(get_workspace_dir),
):
    mgr = WorkspaceManager(workspace_dir)
    if backup_id:
        backups_dir = os.path.join(workspace_dir, ".git", "backups")
        abs_path = os.path.join(backups_dir, backup_id)
        if not os.path.exists(abs_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Backup not found: {backup_id}",
            )
    else:
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
        ".svg",
        ".webp",
    }
    if ext in binary_extensions:
        return FileResponse(abs_path, filename=os.path.basename(abs_path))
    try:
        if backup_id:
            try:
                with open(abs_path, "rb") as f:
                    content = f.read()
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to read backup: {e}",
                )
        else:
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
    session_id: str = Query(...), workspace_dir: str = Depends(get_workspace_dir)
):
    mgr = WorkspaceManager(workspace_dir)
    s = mgr.get_git_status()
    changes = []
    for c in s["changes"]:
        file_path = os.path.join(workspace_dir, c["path"])
        file_size = None
        if os.path.exists(file_path) and os.path.isfile(file_path):
            try:
                file_size = os.path.getsize(file_path)
            except Exception:
                pass
        changes.append(
            GitStatusItem(
                path=c["path"],
                git_status=c["git_status"],
                staged=c["staged"],
                file_size=file_size,
            )
        )
    return GitStatusResponse(
        branch_name=s["branch_name"],
        is_clean=s["is_clean"],
        changes=changes,
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
    workspace = get_workspace_by_path(DATABASE_PATH, workspace_dir)
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

    workspace = get_workspace_by_path(DATABASE_PATH, workspace_dir)
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


@router.post("/git/branch")
@traced("workspace.git.branch")
async def git_branch_endpoint(
    body: GitBranchRequest, engine: BaseAgentEngine = Depends(get_agent_engine)
):
    workspace_dir = await get_workspace_dir(body.session_id, engine)
    import subprocess

    cmd = ["git", "checkout"]
    if body.create:
        cmd.extend(["-b", body.branch_name])
    else:
        cmd.append(body.branch_name)

    try:
        res = subprocess.run(
            cmd, cwd=workspace_dir, capture_output=True, text=True, check=True
        )
        return {
            "success": True,
            "message": res.stdout or res.stderr or "Branch checked out successfully",
        }
    except subprocess.CalledProcessError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Git operation failed: {e.stderr or str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post("/git/merge")
@traced("workspace.git.merge")
async def git_merge_endpoint(
    body: GitMergeRequest, engine: BaseAgentEngine = Depends(get_agent_engine)
):
    workspace_dir = await get_workspace_dir(body.session_id, engine)
    import subprocess

    try:
        res = subprocess.run(
            ["git", "merge", body.branch_name],
            cwd=workspace_dir,
            capture_output=True,
            text=True,
            check=True,
        )
        return {
            "success": True,
            "message": res.stdout or res.stderr or "Branch merged successfully",
        }
    except subprocess.CalledProcessError as e:
        if "CONFLICT" in e.stdout or "CONFLICT" in e.stderr:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Merge conflicts detected: {e.stdout or e.stderr}",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Git merge failed: {e.stderr or str(e)}",
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
    workspace = get_workspace_by_path(DATABASE_PATH, workspace_dir)
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
    await get_workspace_dir(body.session_id, engine)
    service.set_workspace_tool_enabled(body.session_id, body.server_id, body.is_enabled)

    # Notify gateway of tool list change so Hermes updates dynamically
    try:
        from api.routers.gateway import notify_gateway_tool_change

        notify_gateway_tool_change()
    except Exception as e:
        logger.warning("failed_to_notify_gateway_tool_change", error=str(e))

    return WorkspaceToolToggleResponse(
        success=True,
        session_id=body.session_id,
        server_id=body.server_id,
        is_enabled=body.is_enabled,
    )


@router.get("/mcp-status", response_model=WorkspaceMcpStatusResponse)
@traced("workspace.mcp-status")
async def get_workspace_mcp_status_endpoint(
    session_id: str = Query(...), workspace_dir: str = Depends(get_workspace_dir)
):
    import yaml

    # 1. Get current workspace by session_id
    workspace = get_workspace_by_session(DATABASE_PATH, session_id)
    if not workspace:
        return WorkspaceMcpStatusResponse(
            status="ok", message="No active workspace.", running_mcps=[]
        )

    # 2. Get currently enabled tools in the database
    enabled_tools = get_workspace_enabled_tools(DATABASE_PATH, session_id)
    from tool_registry.db import get_servers

    all_servers = get_servers(DATABASE_PATH)

    # Active servers expected to be configured
    expected_servers = []
    for s in all_servers:
        if s.is_installed:
            is_enabled = True
            if enabled_tools is not None:
                is_enabled = (s.name in enabled_tools) or (s.server_id in enabled_tools)
            if is_enabled:
                expected_servers.append(s)

    running_mcps = [
        RunningMcpInfo(name=s.name, status=s.status, error_message=s.error_message)
        for s in expected_servers
    ]

    # Sanitize expected server names to match config.yaml keys
    expected_keys = set()
    for s in expected_servers:
        key_name = "".join(c.lower() for c in s.name if c.isalnum())
        if not key_name:
            key_name = s.server_id
        expected_keys.add(key_name)

    # 3. Read current configured mcp_servers from config.yaml
    configured_keys = set()
    paths = hermes_config_paths()
    config_loaded = False
    for path in paths:
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    config = yaml.safe_load(f) or {}
                mcp_servers = config.get("mcp_servers", {})
                configured_keys = set(mcp_servers.keys())
                config_loaded = True
                break
            except Exception:
                pass

    if not config_loaded:
        # If no config file exists, but we expect tools, it's a mismatch
        if expected_keys:
            return WorkspaceMcpStatusResponse(
                status="mismatch",
                message="Tool change during session. Start a new session to apply changes.",
                running_mcps=running_mcps,
            )
        return WorkspaceMcpStatusResponse(
            status="ok",
            message="MCP configuration is active and healthy.",
            running_mcps=running_mcps,
        )

    # 4. Check for mismatches
    if expected_keys and "wrightgateway" not in configured_keys:
        return WorkspaceMcpStatusResponse(
            status="mismatch",
            message="Tool change during session. Start a new session to apply changes.",
            running_mcps=running_mcps,
        )

    # 5. Check for broken servers
    for s in expected_servers:
        if s.status == "error":
            err_msg = s.error_message or "Unknown error"
            return WorkspaceMcpStatusResponse(
                status="error",
                message=f"Cannot connect to MCP Server: {s.name} ({err_msg})",
                running_mcps=running_mcps,
            )
    inactive_servers = [s.name for s in expected_servers if s.status != "active"]
    if inactive_servers:
        names = ", ".join(inactive_servers)
        return WorkspaceMcpStatusResponse(
            status="warning",
            message=f"MCP server installed but not active: {names}",
            running_mcps=running_mcps,
        )

    return WorkspaceMcpStatusResponse(
        status="ok",
        message="MCP configuration is active and healthy.",
        running_mcps=running_mcps,
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

    service = get_workspace_service()
    activation = await service.activate_workspace(
        session_id,
        engine,
        local_path=local_path,
        agent_id=_active_agent_id(request),
    )
    session_id = activation.session_id
    local_path = activation.workspace_path

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

    # Notify gateway that workspace tools have changed
    try:
        from api.routers.gateway import notify_gateway_tool_change

        notify_gateway_tool_change()
    except Exception as e:
        logger.warning("failed_to_notify_gateway_workspace_activation", error=str(e))

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
):
    session_id = body.session_id
    try:
        update_workspace_session(DATABASE_PATH, workspace_id, body.session_id)
    except sqlite3.IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Session is already associated with another workspace",
        ) from exc

    workspace = get_workspace_by_id(DATABASE_PATH, workspace_id)
    if workspace:
        local_path = workspace["local_path"]
        service = get_workspace_service()
        activation = await service.activate_workspace(
            body.session_id,
            engine,
            local_path=local_path,
            agent_id=_active_agent_id(request),
            allow_fallback=False,
        )
        session_id = activation.session_id

        mcp_engine = getattr(request.app.state, "mcp_engine", None)
        if mcp_engine:
            try:
                await sync_workspace_runners(DATABASE_PATH, session_id, mcp_engine)
            except Exception as e:
                logger.error("mcp_runner_sync_failed_on_session_update", error=str(e))

        sync_manager = getattr(request.app.state, "agent_sync_manager", None)
        if sync_manager:
            try:
                sync_manager.sync_workspace_tools(session_id)
            except Exception as e:
                logger.error("agent_tool_sync_failed_on_session_update", error=str(e))

        try:
            from api.routers.gateway import notify_gateway_tool_change

            notify_gateway_tool_change()
        except Exception as e:
            logger.warning("failed_to_notify_gateway_on_session_update", error=str(e))

    return {"success": True, "session_id": session_id}


@router.post("/files/backup", response_model=FileBackupResponse)
@traced("workspace.files.backup")
async def backup_file_content_endpoint(
    body: FileBackupRequest, engine: BaseAgentEngine = Depends(get_agent_engine)
):
    workspace_dir = await get_workspace_dir(body.session_id, engine)
    mgr = WorkspaceManager(workspace_dir)
    try:
        backup_id = mgr.write_backup(body.path, body.content.encode("utf-8"))
        return FileBackupResponse(success=True, backup_id=backup_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.delete("/files/backup", response_model=FileContentSaveResponse)
@traced("workspace.files.backup.delete")
async def delete_file_backup_endpoint(
    body: FileBackupDeleteRequest, engine: BaseAgentEngine = Depends(get_agent_engine)
):
    workspace_dir = await get_workspace_dir(body.session_id, engine)
    mgr = WorkspaceManager(workspace_dir)
    try:
        mgr.delete_backup(body.backup_id)
        return FileContentSaveResponse(success=True)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
