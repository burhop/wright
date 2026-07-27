from __future__ import annotations

from dataclasses import dataclass, field

from typing import Any


@dataclass(frozen=True)
class WorkspaceRecord:
    workspace_id: str
    session_id: str
    workspace_name: str | None
    local_path: str
    updated_at: int
    git_remote_url: str | None = None
    git_username: str | None = None
    enabled_tools: list[str] | None = None


@dataclass(frozen=True)
class WorkspaceSessionRecord:
    workspace_id: str
    session_id: str
    title: str | None
    created_at: int
    updated_at: int
    message_count: int = 0
    agent_id: str = "hermes"


@dataclass(frozen=True)
class WorkspaceActivation:
    success: bool
    session_id: str
    workspace_path: str
    context: Any


@dataclass(frozen=True)
class WorkspaceToolState:
    session_id: str
    enabled_tools: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class FileExecutionPolicy:
    timeout_seconds: float = 10.0


@dataclass(frozen=True)
class FileExecutionResult:
    success: bool
    stdout: str
    stderr: str
    exit_code: int


@dataclass(frozen=True, slots=True)
class ProcessResult:
    exit_code: int
    stdout: str
    stderr: str
