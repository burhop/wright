from __future__ import annotations

import os
import ntpath
import subprocess
import uuid
from collections.abc import Callable, Mapping
from typing import Any

from agent_adapters import (
    AgentContextMaterializationRequest,
    AgentContextMaterializer,
)
from agent_adapters.context import NoOpAgentContextMaterializer
from agent_adapters.hermes_gateway import hermes_context_materializer
from agent_adapters.openclaw import openclaw_context_materializer
from core import WorkspaceManager
from core.logging import get_logger
from core.redaction import redact_command, redact_text
from core.tracing import traced
from core.workspace import (
    create_workspace,
    create_workspace_from_dashboard,
    get_workspace_by_path,
    get_workspace_by_session,
    get_workspace_enabled_tools,
    is_synthetic_session_workspace,
    sanitize_workspace_name,
    set_active_gateway_session,
    touch_workspace,
    update_workspace_enabled_tools,
    update_workspace_remote_by_id,
    update_workspace_session,
)
from data_vault import connect_state_db
from tool_registry.db import get_servers

from .models import (
    FileExecutionPolicy,
    FileExecutionResult,
    WorkspaceActivation,
    WorkspaceConflictError,
    WorkspaceInvalidRequestError,
    WorkspaceNotFoundError,
    WorkspaceRecord,
    WorkspaceToolState,
)

logger = get_logger(__name__)


def default_workspace_parent_dir(env: Mapping[str, str] | None = None) -> str:
    source = env or os.environ
    home_dir = (
        source.get("WRIGHT_WORKSPACES_DIR")
        or source.get("USERPROFILE")
        or source.get("HOME")
        or os.path.expanduser("~")
    )
    if ":" in home_dir or "\\" in home_dir:
        return ntpath.join(home_dir, "wright")
    return os.path.join(home_dir, "wright")


def _record_from_row(row: Mapping[str, Any]) -> WorkspaceRecord:
    return WorkspaceRecord(
        workspace_id=str(row["workspace_id"]),
        session_id=str(row["session_id"]),
        workspace_name=row.get("workspace_name"),
        local_path=str(row["local_path"]),
        git_remote_url=row.get("git_remote_url"),
        git_username=row.get("git_username"),
        updated_at=int(row["updated_at"]),
    )


class WorkspaceService:
    def __init__(
        self,
        db_path: str,
        *,
        parent_dir_provider: Callable[[], str] = default_workspace_parent_dir,
        materializers: Mapping[str, AgentContextMaterializer] | None = None,
    ) -> None:
        self.db_path = db_path
        self.parent_dir_provider = parent_dir_provider
        self.materializers = {
            "hermes": hermes_context_materializer(),
            "openclaw": openclaw_context_materializer(),
        }
        if materializers:
            self.materializers.update(
                {key.lower(): value for key, value in materializers.items()}
            )

    async def resolve_workspace_dir(self, session_id: str, engine) -> str:
        workspace = get_workspace_by_session(self.db_path, session_id)
        if workspace:
            return workspace["local_path"]

        try:
            workspace_path = await engine.get_session_workspace(session_id)
        except Exception as exc:
            logger.warning(
                "workspace_session_lookup_failed_using_local_workspace",
                session_id=session_id,
                error=redact_text(exc),
            )
            workspace_path = None

        if not workspace_path:
            workspace_path = os.path.join(self.parent_dir_provider(), session_id)
        os.makedirs(workspace_path, exist_ok=True)

        synthetic_fallback = is_synthetic_session_workspace(
            {
                "session_id": session_id,
                "local_path": workspace_path,
                "workspace_name": os.path.basename(workspace_path),
            }
        )
        existing = get_workspace_by_path(self.db_path, workspace_path)
        if existing:
            update_workspace_session(self.db_path, existing["workspace_id"], session_id)
        elif not synthetic_fallback:
            create_workspace(
                self.db_path,
                str(uuid.uuid4()),
                session_id,
                workspace_path,
                workspace_name=os.path.basename(workspace_path),
            )
        return workspace_path

    @traced("workspace.create")
    async def create_workspace(
        self, name: str, local_path: str | None, engine, *, agent_id: str = "hermes"
    ) -> WorkspaceRecord:
        workspace_path = local_path
        if not workspace_path:
            sanitized = sanitize_workspace_name(name)
            if not sanitized:
                raise WorkspaceInvalidRequestError(
                    "Workspace name cannot be empty or invalid."
                )
            workspace_path = os.path.join(self.parent_dir_provider(), sanitized)

        self._ensure_workspace_available(name, workspace_path)
        os.makedirs(workspace_path, exist_ok=True)
        WorkspaceManager(workspace_path)

        try:
            session_info = await engine.create_session(workspace_path)
            session_id = session_info.session_id
        except Exception as exc:
            session_id = f"wright-local-{uuid.uuid4()}"
            logger.warning(
                "workspace_create_agent_session_failed_using_local_session",
                local_path=workspace_path,
                session_id=session_id,
                error=redact_text(exc),
            )

        row = create_workspace_from_dashboard(
            self.db_path, name, workspace_path, session_id
        )
        self.refresh_agent_context_for_path(
            workspace_path,
            agent_id=agent_id,
            workspace_id=row.get("workspace_id"),
            session_id=session_id,
        )
        return _record_from_row(row)

    @traced("workspace.activate")
    async def activate_workspace(
        self,
        session_id: str,
        engine,
        *,
        local_path: str | None = None,
        agent_id: str = "hermes",
        allow_fallback: bool = True,
    ) -> WorkspaceActivation:
        workspace = get_workspace_by_session(self.db_path, session_id)
        workspace_path = local_path or (workspace["local_path"] if workspace else None)
        if not workspace_path:
            workspace_path = await self.resolve_workspace_dir(session_id, engine)

        active_session_id = await self._verify_agent_session(
            session_id,
            workspace_path,
            engine,
            allow_fallback=allow_fallback,
        )
        touch_workspace(self.db_path, active_session_id)
        set_active_gateway_session(self.db_path, active_session_id)
        refreshed = self.refresh_agent_context_for_path(
            workspace_path,
            agent_id=agent_id,
            workspace_id=(workspace or {}).get("workspace_id"),
            session_id=active_session_id,
        )
        return WorkspaceActivation(
            success=True,
            session_id=active_session_id,
            workspace_path=workspace_path,
            context=refreshed,
        )

    @traced("workspace.config.update")
    async def update_workspace_config(
        self,
        session_id: str,
        engine,
        *,
        git_remote_url: str | None = None,
        git_username: str | None = None,
        git_token: str | None = None,
        workspace_prompt: str | None = None,
        git_large_file_threshold: int | None = None,
        agent_id: str = "hermes",
    ) -> str:
        workspace_path = await self.resolve_workspace_dir(session_id, engine)
        workspace = get_workspace_by_path(self.db_path, workspace_path)
        if not workspace:
            raise WorkspaceNotFoundError("Workspace not found")
        update_workspace_remote_by_id(
            self.db_path,
            workspace["workspace_id"],
            git_remote_url,
            git_username,
            git_token,
            workspace_prompt,
            git_large_file_threshold,
        )
        self.refresh_agent_context_for_path(
            workspace_path,
            agent_id=agent_id,
            workspace_id=workspace["workspace_id"],
            session_id=session_id,
        )
        return workspace["workspace_id"]

    def list_workspace_tools(self, session_id: str) -> WorkspaceToolState:
        enabled = get_workspace_enabled_tools(self.db_path, session_id)
        if enabled is None:
            enabled = [
                server.name
                for server in get_servers(self.db_path)
                if server.is_installed
            ]
        return WorkspaceToolState(session_id=session_id, enabled_tools=enabled)

    def set_workspace_tool_enabled(
        self, session_id: str, server_id: str, is_enabled: bool
    ) -> WorkspaceToolState:
        current = get_workspace_enabled_tools(self.db_path, session_id)
        if current is None:
            current = [
                server.name
                for server in get_servers(self.db_path)
                if server.is_installed
            ]
        if is_enabled and server_id not in current:
            current.append(server_id)
        elif not is_enabled and server_id in current:
            current.remove(server_id)
        update_workspace_enabled_tools(self.db_path, session_id, current)
        return WorkspaceToolState(session_id=session_id, enabled_tools=current)

    @traced("workspace.file.execute")
    async def execute_workspace_file(
        self,
        session_id: str,
        path: str,
        engine,
        *,
        policy: FileExecutionPolicy | None = None,
    ) -> FileExecutionResult:
        workspace_path = await self.resolve_workspace_dir(session_id, engine)
        safe_path = os.path.normpath(path)
        if (
            safe_path.startswith("..")
            or os.path.isabs(safe_path)
            or safe_path.startswith("/")
            or safe_path.startswith("\\")
        ):
            safe_path = safe_path.lstrip("/\\").replace("../", "").replace("..\\", "")
        full_path = os.path.normpath(os.path.join(workspace_path, safe_path))
        if not os.path.exists(full_path) or not os.path.isfile(full_path):
            raise WorkspaceNotFoundError(f"File not found: {path}")
        if not full_path.endswith(".py"):
            raise WorkspaceInvalidRequestError(
                "Only Python files (.py) are supported for running."
            )

        timeout = (policy or FileExecutionPolicy()).timeout_seconds
        command = ["python", full_path]
        logger.info(
            "workspace_file_execute",
            command=redact_command(command),
            timeout_seconds=timeout,
        )
        try:
            result = subprocess.run(
                command,
                cwd=workspace_path,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return FileExecutionResult(
                success=result.returncode == 0,
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.returncode,
            )
        except subprocess.TimeoutExpired as exc:
            return FileExecutionResult(
                success=False,
                stdout=exc.stdout or "",
                stderr=exc.stderr or f"Process timed out after {timeout} seconds.",
                exit_code=-9,
            )

    @traced("agent.context.materialize")
    def refresh_agent_context_for_path(
        self,
        workspace_path: str,
        *,
        agent_id: str = "hermes",
        workspace_id: str | None = None,
        session_id: str | None = None,
        correlation_id: str | None = None,
    ):
        materializer = self.materializers.get(
            agent_id.strip().lower(),
            NoOpAgentContextMaterializer(agent_id.strip().lower() or "unknown", "stub"),
        )
        return materializer.materialize(
            AgentContextMaterializationRequest(
                db_path=self.db_path,
                workspace_path=workspace_path,
                workspace_id=workspace_id,
                session_id=session_id,
                correlation_id=correlation_id,
            )
        )

    def _ensure_workspace_available(self, name: str, local_path: str) -> None:
        if get_workspace_by_path(self.db_path, local_path):
            raise WorkspaceConflictError(
                f"Workspace directory path already exists: {local_path}"
            )
        with connect_state_db(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT workspace_id FROM engineering_workspaces WHERE workspace_name = ?",
                (name.strip(),),
            )
            if cursor.fetchone():
                raise WorkspaceConflictError(
                    f"Workspace with name '{name}' already exists."
                )
        if os.path.exists(local_path):
            raise WorkspaceConflictError(
                f"Workspace directory already exists on disk: {local_path}"
            )

    async def _verify_agent_session(
        self,
        session_id: str,
        workspace_path: str,
        engine,
        *,
        allow_fallback: bool,
    ) -> str:
        try:
            sessions = await engine.list_sessions()
            session_ids = {session.session_id for session in sessions}
            if session_id in session_ids:
                return session_id
            if not allow_fallback:
                return session_id

            workspace_sessions = sorted(
                [
                    session
                    for session in sessions
                    if session.workspace == workspace_path
                ],
                key=lambda session: session.updated_at,
                reverse=True,
            )
            session_info = (
                workspace_sessions[0]
                if workspace_sessions
                else await engine.create_session(workspace_path)
            )
            row = get_workspace_by_path(self.db_path, workspace_path)
            if row:
                update_workspace_session(
                    self.db_path,
                    row["workspace_id"],
                    session_info.session_id,
                )
            return session_info.session_id
        except Exception as exc:
            logger.warning(
                "agent_session_verify_failed",
                session_id=session_id,
                error=redact_text(exc),
            )
            return session_id
