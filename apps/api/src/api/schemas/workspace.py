"""
Workspace request/response Pydantic models.

Extracted from apps/api/src/api/routers/workspace.py to keep the router thin.
All models used by workspace endpoints are defined here.
"""

import json
from pydantic import BaseModel
from typing import Any, Dict, List, Optional


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
