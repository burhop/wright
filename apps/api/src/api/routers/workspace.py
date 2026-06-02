import os
from fastapi import APIRouter, Depends, Query, HTTPException, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from agent_adapters import BaseAgentEngine
from core import WorkspaceManager
from api.routers.agent import get_agent_engine

router = APIRouter()

class WorkspaceNodeResponse(BaseModel):
    name: str
    path: str
    type: str
    size: Optional[int] = None
    last_modified: int
    children: Optional[List[Dict[str, Any]]] = None

class WorkspaceTreeResponse(BaseModel):
    workspace: WorkspaceNodeResponse

async def get_workspace_dir(
    session_id: str,
    engine: BaseAgentEngine = Depends(get_agent_engine)
) -> str:
    """Retrieve the workspace path for the given session ID, with fallback to default."""
    workspace_path = await engine.get_session_workspace(session_id)
    if not workspace_path:
        # Fallback to standard local workspace directory
        workspace_path = "/home/burhop/workspace"
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
