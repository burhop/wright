import os
import uuid
from fastapi import APIRouter, Depends, Query, HTTPException, status, Response
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from agent_adapters import BaseAgentEngine
from core import WorkspaceManager
from core.workspace import get_workspace_by_session, create_workspace
from api.routers.agent import get_agent_engine
from api.config import DATABASE_PATH

router = APIRouter()

class WorkspaceNodeResponse(BaseModel):
    name: str
    path: str
    type: str
    size: Optional[int] = None
    last_modified: int
    git_status: str = "Clean"
    children: Optional[List[Dict[str, Any]]] = None

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

class GitStatusItem(BaseModel):
    path: str
    git_status: str
    staged: bool

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

class WorkspaceTreeResponse(BaseModel):
    workspace: WorkspaceNodeResponse

class FileContentSaveRequest(BaseModel):
    session_id: str
    path: str
    content: str

class FileContentSaveResponse(BaseModel):
    success: bool

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

async def get_workspace_dir(
    session_id: str,
    engine: BaseAgentEngine = Depends(get_agent_engine)
) -> str:
    """Retrieve the workspace path for the given session ID, with fallback to default, backed by SQLite."""
    # 1. Query database first
    workspace = get_workspace_by_session(DATABASE_PATH, session_id)
    if workspace:
        return workspace["local_path"]

    # 2. If not found, retrieve from the engine
    workspace_path = await engine.get_session_workspace(session_id)
    if not workspace_path:
        # Fallback to isolated session directory
        workspace_path = f"/home/burhop/workspace/{session_id}"
        
    # 3. Create directory
    os.makedirs(workspace_path, exist_ok=True)
    
    # 4. Save to database
    workspace_id = str(uuid.uuid4())
    create_workspace(DATABASE_PATH, workspace_id, session_id, workspace_path)
    
    return workspace_path

@router.get("/files", response_model=WorkspaceTreeResponse)
async def list_workspace_files(
    session_id: str = Query(..., description="The session ID representing the active workspace context"),
    workspace_dir: str = Depends(get_workspace_dir)
):
    try:
        manager = WorkspaceManager(workspace_dir)
        tree = manager.get_workspace_tree()
        return WorkspaceTreeResponse(workspace=tree)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list workspace files: {e}"
        )

@router.get("/files/content")
async def get_file_content(
    session_id: str = Query(..., description="The session ID representing the active workspace context"),
    path: str = Query(..., description="Workspace-relative path to the file"),
    workspace_dir: str = Depends(get_workspace_dir)
):
    try:
        manager = WorkspaceManager(workspace_dir)
        abs_path = manager.sanitize_path(path)
        
        # Verify file existence
        if not os.path.exists(abs_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File not found: {path}"
            )
            
        if not os.path.isfile(abs_path):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Path is not a file: {path}"
            )
            
        # Determine media type based on extension
        media_type = "application/octet-stream"
        if path.endswith(".scad"):
            media_type = "text/plain"
        elif path.endswith(".stl"):
            media_type = "application/octet-stream"
        elif path.endswith(".json"):
            media_type = "application/json"
            
        return FileResponse(abs_path, media_type=media_type, filename=os.path.basename(abs_path))
    except HTTPException:
        raise
    except ValueError as e:
        # Prevent traversal
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read file content: {e}"
        )

@router.post("/files", response_model=WorkspaceNodeResponse, status_code=status.HTTP_201_CREATED)
async def create_file_endpoint(
    body: FileCreateRequest,
    engine: BaseAgentEngine = Depends(get_agent_engine)
):
    try:
        workspace_dir = await get_workspace_dir(body.session_id, engine)
        manager = WorkspaceManager(workspace_dir)
        node = manager.create_file_node(body.path, body.type)
        return node
    except FileExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create file/folder: {e}"
        )

@router.delete("/files", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file_endpoint(
    path: str = Query(..., description="Workspace-relative path to the file/folder"),
    workspace_dir: str = Depends(get_workspace_dir)
):
    try:
        manager = WorkspaceManager(workspace_dir)
        manager.delete_file_node(path)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete file/folder: {e}"
        )

@router.put("/files/move", response_model=FileMoveResponse)
async def move_file_endpoint(
    body: FileMoveRequest,
    engine: BaseAgentEngine = Depends(get_agent_engine)
):
    try:
        workspace_dir = await get_workspace_dir(body.session_id, engine)
        manager = WorkspaceManager(workspace_dir)
        manager.move_file_node(body.source_path, body.destination_path)
        return FileMoveResponse(
            success=True,
            source_path=body.source_path,
            destination_path=body.destination_path
        )
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except FileExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to move file/folder: {e}"
        )

@router.get("/git/status", response_model=GitStatusResponse)
async def git_status_endpoint(
    session_id: str = Query(..., description="The session ID representing the active workspace"),
    engine: BaseAgentEngine = Depends(get_agent_engine)
):
    try:
        workspace_dir = await get_workspace_dir(session_id, engine)
        manager = WorkspaceManager(workspace_dir)
        status_info = manager.get_git_status()
        return GitStatusResponse(**status_info)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get git status: {e}"
        )

@router.get("/git/diff", response_model=GitDiffResponse)
async def git_diff_endpoint(
    session_id: str = Query(..., description="The session ID"),
    path: str = Query(..., description="Workspace-relative path to diff"),
    engine: BaseAgentEngine = Depends(get_agent_engine)
):
    try:
        workspace_dir = await get_workspace_dir(session_id, engine)
        manager = WorkspaceManager(workspace_dir)
        diff_text = manager.get_git_diff(path)
        return GitDiffResponse(path=path, diff=diff_text)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch git diff: {e}"
        )

@router.post("/git/revert", response_model=GitRevertResponse)
async def git_revert_endpoint(
    body: GitRevertRequest,
    engine: BaseAgentEngine = Depends(get_agent_engine)
):
    try:
        workspace_dir = await get_workspace_dir(body.session_id, engine)
        manager = WorkspaceManager(workspace_dir)
        manager.revert_file(body.path)
        return GitRevertResponse(success=True, path=body.path)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to revert file changes: {e}"
        )

@router.post("/git/commit", response_model=GitCommitResponse)
async def git_commit_endpoint(
    body: GitCommitRequest,
    engine: BaseAgentEngine = Depends(get_agent_engine)
):
    try:
        workspace_dir = await get_workspace_dir(body.session_id, engine)
        manager = WorkspaceManager(workspace_dir)
        commit_info = manager.commit_changes(body.message)
        return GitCommitResponse(success=True, **commit_info)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to commit changes: {e}"
        )

@router.get("/git/history", response_model=GitHistoryResponse)
async def git_history_endpoint(
    session_id: str = Query(..., description="The session ID"),
    limit: int = Query(50, description="Max commits to fetch"),
    engine: BaseAgentEngine = Depends(get_agent_engine)
):
    try:
        workspace_dir = await get_workspace_dir(session_id, engine)
        manager = WorkspaceManager(workspace_dir)
        history = manager.get_git_history(limit)
        return GitHistoryResponse(commits=history)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch git commit logs: {e}"
        )

# Remote Syncing & Options Models
class WorkspaceConfigRequest(BaseModel):
    session_id: str
    git_remote_url: Optional[str] = None
    git_username: Optional[str] = None
    git_token: Optional[str] = None

class WorkspaceConfigResponse(BaseModel):
    success: bool
    workspace_id: str

class WorkspaceConfigGetResponse(BaseModel):
    workspace_id: str
    git_remote_url: Optional[str] = None
    git_username: Optional[str] = None
    has_token: bool
    workspace_path: Optional[str] = None

class GitPushPullRequest(BaseModel):
    session_id: str

class GitPushPullResponse(BaseModel):
    success: bool
    message: str

@router.get("/config", response_model=WorkspaceConfigGetResponse)
async def get_workspace_config(
    session_id: str = Query(..., description="The session ID representing the active workspace"),
    workspace_dir: str = Depends(get_workspace_dir)
):
    try:
        workspace = get_workspace_by_session(DATABASE_PATH, session_id)
        if not workspace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workspace configuration not found for session: {session_id}"
            )
        return WorkspaceConfigGetResponse(
            workspace_id=workspace["workspace_id"],
            git_remote_url=workspace.get("git_remote_url"),
            git_username=workspace.get("git_username"),
            has_token=bool(workspace.get("git_token")),
            workspace_path=workspace.get("local_path")
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve workspace configuration: {e}"
        )

@router.post("/config", response_model=WorkspaceConfigResponse)
async def update_workspace_config(
    body: WorkspaceConfigRequest,
    engine: BaseAgentEngine = Depends(get_agent_engine)
):
    try:
        _ = await get_workspace_dir(body.session_id, engine)
        workspace = get_workspace_by_session(DATABASE_PATH, body.session_id)
        if not workspace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workspace not found for session: {body.session_id}"
            )
        
        git_token = body.git_token
        # If token not provided but we have it, retain it
        if git_token is None and workspace.get("git_token"):
            git_token = workspace.get("git_token")
            
        from core.workspace import update_workspace_remote
        update_workspace_remote(
            DATABASE_PATH,
            body.session_id,
            body.git_remote_url,
            body.git_username,
            git_token
        )
        return WorkspaceConfigResponse(success=True, workspace_id=workspace["workspace_id"])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update workspace configuration: {e}"
        )

@router.post("/git/push", response_model=GitPushPullResponse)
async def git_push_endpoint(
    body: GitPushPullRequest,
    engine: BaseAgentEngine = Depends(get_agent_engine)
):
    try:
        workspace_dir = await get_workspace_dir(body.session_id, engine)
        workspace = get_workspace_by_session(DATABASE_PATH, body.session_id)
        if not workspace or not workspace.get("git_remote_url"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Git remote URL is not configured."
            )
            
        manager = WorkspaceManager(workspace_dir)
        manager.push_remote(
            remote_url=workspace["git_remote_url"],
            username=workspace.get("git_username"),
            token=workspace.get("git_token")
        )
        return GitPushPullResponse(success=True, message="Push completed successfully")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Push failed: {e}"
        )

@router.post("/git/pull")
async def git_pull_endpoint(
    body: GitPushPullRequest,
    engine: BaseAgentEngine = Depends(get_agent_engine)
):
    try:
        workspace_dir = await get_workspace_dir(body.session_id, engine)
        workspace = get_workspace_by_session(DATABASE_PATH, body.session_id)
        if not workspace or not workspace.get("git_remote_url"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Git remote URL is not configured."
            )
            
        manager = WorkspaceManager(workspace_dir)
        from core.workspace import MergeConflictError
        try:
            manager.pull_remote(
                remote_url=workspace["git_remote_url"],
                username=workspace.get("git_username"),
                token=workspace.get("git_token")
            )
        except MergeConflictError as mce:
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content={
                    "error": "MergeConflict",
                    "message": "Pull resulted in merge conflicts",
                    "conflicted_files": mce.conflicted_files
                }
            )
        return GitPushPullResponse(success=True, message="Pull completed successfully")
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pull failed: {e}"
        )

@router.put("/files/content", response_model=FileContentSaveResponse)
async def save_file_content_endpoint(
    body: FileContentSaveRequest,
    engine: BaseAgentEngine = Depends(get_agent_engine)
):
    try:
        workspace_dir = await get_workspace_dir(body.session_id, engine)
        manager = WorkspaceManager(workspace_dir)
        manager.write_file_content(body.path, body.content.encode("utf-8"))
        return FileContentSaveResponse(success=True)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file content: {e}"
        )

@router.get("/tools", response_model=WorkspaceToolsGetResponse)
async def get_workspace_tools_endpoint(
    session_id: str = Query(..., description="The session ID representing the active workspace")
):
    try:
        from core.workspace import get_workspace_enabled_tools
        enabled = get_workspace_enabled_tools(DATABASE_PATH, session_id)
        if enabled is None:
            from tool_registry.db import get_servers
            servers = get_servers(DATABASE_PATH)
            enabled = [s.name for s in servers if s.is_active]
        return WorkspaceToolsGetResponse(session_id=session_id, enabled_tools=enabled)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get workspace tools: {e}"
        )

@router.post("/tools/toggle", response_model=WorkspaceToolToggleResponse)
async def toggle_workspace_tool_endpoint(
    body: WorkspaceToolToggleRequest
):
    try:
        from core.workspace import get_workspace_enabled_tools, update_workspace_enabled_tools
        enabled = get_workspace_enabled_tools(DATABASE_PATH, body.session_id)
        if enabled is None:
            from tool_registry.db import get_servers
            servers = get_servers(DATABASE_PATH)
            enabled = [s.name for s in servers if s.is_active]
            
        if body.is_enabled:
            if body.server_id not in enabled:
                enabled.append(body.server_id)
        else:
            if body.server_id in enabled:
                enabled.remove(body.server_id)
                
        update_workspace_enabled_tools(DATABASE_PATH, body.session_id, enabled)
        
        # Sync the new tool selection list to Hermes config.yaml
        sync_workspace_tools_to_hermes(body.session_id)
        
        return WorkspaceToolToggleResponse(
            success=True,
            session_id=body.session_id,
            server_id=body.server_id,
            is_enabled=body.is_enabled
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to toggle workspace tool: {e}"
        )

def sync_workspace_tools_to_hermes(session_id: str):
    """Sync the workspace's enabled tools to Hermes config.yaml (filtering out disabled ones)."""
    import sys
    import yaml
    import subprocess
    if "pytest" in sys.modules:
        return

    workspace = get_workspace_by_session(DATABASE_PATH, session_id)
    if not workspace:
        return

    from core.workspace import get_workspace_enabled_tools
    enabled_tools = get_workspace_enabled_tools(DATABASE_PATH, session_id)
    
    from tool_registry.db import get_servers
    all_servers = get_servers(DATABASE_PATH)
    
    paths = [
        os.path.expanduser("~/.hermes/profiles/wright/config.yaml"),
        os.path.expanduser("~/.hermes/config.yaml")
    ]
    
    for path in paths:
        if not os.path.exists(path):
            continue
        try:
            with open(path, "r") as f:
                config = yaml.safe_load(f) or {}
                
            if "mcp_servers" not in config:
                config["mcp_servers"] = {}
            
            # Rebuild the mcp_servers section
            new_mcp_servers = {}
            for server in all_servers:
                key_name = "".join(c.lower() for c in server.name if c.isalnum())
                if not key_name:
                    key_name = server.server_id
                
                # Check if this server is globally active
                if not server.is_active:
                    continue
                
                # Check if this server is enabled in the workspace session
                is_enabled = True
                if enabled_tools is not None:
                    is_enabled = (server.name in enabled_tools) or (server.server_id in enabled_tools)
                
                if is_enabled:
                    # Construct stdio or sse settings
                    if server.type == "stdio":
                        if not server.command:
                            continue
                        import shlex
                        args = []
                        if isinstance(server.command, list):
                            cmd = server.command[0]
                            if len(server.command) > 1:
                                args = server.command[1:]
                        else:
                            parsed = shlex.split(server.command)
                            cmd = parsed[0] if parsed else "echo"
                            args = parsed[1:] if len(parsed) > 1 else []
                            
                        srv_config = {
                            "command": cmd,
                            "args": args
                        }
                        if key_name == "openscadgeometry" or "openscad" in key_name:
                            srv_config["env"] = {
                                "OPENSCAD_PATH": "/home/burhop/repos/wright/scripts/openscad-headless.sh"
                            }
                        new_mcp_servers[key_name] = srv_config
                    elif server.type == "sse":
                        if not server.command or not isinstance(server.command, str):
                            continue
                        new_mcp_servers[key_name] = {
                            "url": server.command,
                            "transport": "sse"
                        }
            
            config["mcp_servers"] = new_mcp_servers
            with open(path, "w") as f:
                yaml.safe_dump(config, f, default_flow_style=False)
                
        except Exception as e:
            # Log error or pass
            pass
            
    # Restart Hermes WebUI in background to reload config
    try:
        subprocess.Popen(
            "export HERMES_HOME=\"$HOME/.hermes/profiles/wright\" && /home/burhop/hermes-webui/ctl.sh stop && /home/burhop/hermes-webui/ctl.sh start 8788",
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except Exception:
        pass
