from __future__ import annotations

import os
import ntpath
import subprocess
import uuid
from dataclasses import replace
from collections.abc import Callable, Mapping
from typing import Any

from agent_adapters import (
    AgentContextMaterializationRequest,
    AgentContextMaterializer,
)
from agent_adapters.context import NoOpAgentContextMaterializer
from agent_adapters.hermes_gateway import hermes_context_materializer
from agent_adapters.openclaw import openclaw_context_materializer
from core.logging import get_logger
from core.redaction import redact_command, redact_text
from core.tracing import traced
from .adapters.runtime import (
    WorkspaceManager,
    get_workspace_enabled_tools,
    write_workspace_agent_context,
    sync_workspace_runners,
)
from data_vault import WorkspaceRepository, create_default_secret_provider
from data_vault.workspace_repository import (
    is_synthetic_session_workspace,
    sanitize_workspace_name,
)
from tool_registry.db import get_servers

from .errors import (
    WorkspaceConflictError,
    WorkspaceInvalidRequestError,
    WorkspaceNotFoundError,
)
from .adapters import LocalProcessRunner, LocalWorkspaceFiles, LocalWorkspaceGit
from .models import (
    FileExecutionPolicy,
    FileExecutionResult,
    WorkspaceActivation,
    WorkspaceRecord,
    WorkspaceSessionRecord,
    WorkspaceToolState,
)
from .executor import BoundedExecutor
from .use_cases import (
    WorkspaceContextUseCases,
    WorkspaceFileUseCases,
    WorkspaceGitUseCases,
    WorkspaceLifecycleUseCases,
    WorkspaceToolUseCases,
)
from .ports import WorkspaceNotifier

logger = get_logger(__name__)


class _NoopNotifier:
    def publish(
        self,
        event: str,
        *,
        workspace_id: str | None = None,
        session_id: str | None = None,
    ) -> None:
        return None


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


def _clean_session_title(title: str | None) -> str:
    cleaned = (title or "").strip()
    if not cleaned or cleaned in {"Untitled", "Undefined"}:
        return "Untitled Session"
    return cleaned


def _unique_session_title(title: str | None, existing_titles: list[str | None]) -> str:
    base = _clean_session_title(title)
    existing = {_clean_session_title(item).casefold() for item in existing_titles}
    if base.casefold() not in existing:
        return base

    index = 2
    while f"{base} ({index})".casefold() in existing:
        index += 1
    return f"{base} ({index})"


def _with_unique_session_titles(
    records: list[WorkspaceSessionRecord],
) -> list[WorkspaceSessionRecord]:
    counts: dict[str, int] = {}
    result: list[WorkspaceSessionRecord] = []
    for record in records:
        base = _clean_session_title(record.title)
        key = base.casefold()
        counts[key] = counts.get(key, 0) + 1
        title = base if counts[key] == 1 else f"{base} ({counts[key]})"
        result.append(replace(record, title=title))
    return result


class WorkspaceService:
    def __init__(
        self,
        db_path: str,
        *,
        parent_dir_provider: Callable[[], str] = default_workspace_parent_dir,
        materializers: Mapping[str, AgentContextMaterializer] | None = None,
        executor: BoundedExecutor | None = None,
        repository: WorkspaceRepository | None = None,
        notifier: WorkspaceNotifier | None = None,
    ) -> None:
        self.db_path = db_path
        self.parent_dir_provider = parent_dir_provider
        self.executor = executor or BoundedExecutor()
        self.repository = repository or WorkspaceRepository(
            db_path, secrets=create_default_secret_provider()
        )
        self.files = WorkspaceFileUseCases(
            db_path,
            self.executor,
            LocalWorkspaceFiles,
            repository=self.repository,
        )
        process = LocalProcessRunner()
        self.git = WorkspaceGitUseCases(
            self.executor,
            self.repository,
            lambda path: LocalWorkspaceGit(path, process=process, timeout_seconds=30.0),
        )
        self.notifier = notifier or _NoopNotifier()
        self.lifecycle = WorkspaceLifecycleUseCases(self.repository)
        self.context = WorkspaceContextUseCases(self.repository)
        self.tools = WorkspaceToolUseCases(
            self.repository,
            lambda: [
                server.name
                for server in get_servers(self.db_path)
                if server.is_installed
            ],
            lambda session_id: get_workspace_enabled_tools(self.db_path, session_id),
            lambda: get_servers(self.db_path),
        )
        self.materializers: dict[str, AgentContextMaterializer] = {
            "hermes": hermes_context_materializer(write_workspace_agent_context),
            "openclaw": openclaw_context_materializer(),
        }
        if materializers:
            self.materializers.update(
                {key.lower(): value for key, value in materializers.items()}
            )

    async def resolve_workspace_dir(self, session_id: str, engine) -> str:
        workspace = self.repository.get_by_session(session_id)
        if workspace:
            try:
                actual_workspace_path = await engine.get_session_workspace(session_id)
            except Exception:
                actual_workspace_path = None
            if (
                actual_workspace_path
                and actual_workspace_path != workspace["local_path"]
            ):
                existing = self.repository.get_by_path(actual_workspace_path)
                if existing:
                    self.repository.update_session(existing["workspace_id"], session_id)
                else:
                    self.repository.create(
                        str(uuid.uuid4()),
                        session_id,
                        actual_workspace_path,
                        workspace_name=os.path.basename(actual_workspace_path),
                    )
                return actual_workspace_path
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
        existing = self.repository.get_by_path(workspace_path)
        if existing:
            self.repository.update_session(existing["workspace_id"], session_id)
        elif not synthetic_fallback:
            self.repository.create(
                str(uuid.uuid4()),
                session_id,
                workspace_path,
                workspace_name=os.path.basename(workspace_path),
            )
        return workspace_path

    async def close(self) -> None:
        await self.executor.close()

    async def reconcile_runtime(
        self, session_id: str, *, mcp_engine: Any | None, sync_manager: Any | None
    ) -> None:
        if mcp_engine is not None:
            await sync_workspace_runners(self.db_path, session_id, mcp_engine)
        if sync_manager is not None:
            sync_manager.sync_workspace_tools(session_id)

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

        row = self.repository.create_dashboard(name, workspace_path, session_id)
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
        workspace = self.repository.get_by_session(session_id)
        workspace_path = local_path or (workspace["local_path"] if workspace else None)
        if not workspace_path:
            workspace_path = await self.resolve_workspace_dir(session_id, engine)

        active_session_id = await self._verify_agent_session(
            session_id,
            workspace_path,
            engine,
            allow_fallback=allow_fallback,
        )
        if workspace:
            self.repository.update_session(workspace["workspace_id"], active_session_id)
        else:
            workspace = self.repository.get_by_path(workspace_path)
            if workspace:
                self.repository.update_session(
                    workspace["workspace_id"], active_session_id
                )
        self.repository.touch(active_session_id)
        refreshed = self.refresh_agent_context_for_path(
            workspace_path,
            agent_id=agent_id,
            workspace_id=(workspace or {}).get("workspace_id"),
            session_id=active_session_id,
        )
        self.notifier.publish(
            "workspace.activated",
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
        workspace = self.repository.get_by_path(workspace_path)
        if not workspace:
            raise WorkspaceNotFoundError("Workspace not found")
        self.repository.update_remote(
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

    async def list_workspace_sessions(
        self, workspace_id: str, engine, *, agent_id: str = "hermes"
    ) -> list[WorkspaceSessionRecord]:
        workspace = self.repository.get_by_id(workspace_id)
        if not workspace:
            raise WorkspaceNotFoundError("Workspace not found")

        local_records = {
            row["session_id"]: row
            for row in self.repository.list_sessions(workspace_id)
        }
        try:
            agent_sessions = await engine.list_sessions()
        except Exception as exc:
            logger.warning(
                "workspace_session_agent_list_failed",
                workspace_id=workspace_id,
                error=redact_text(exc),
            )
            agent_sessions = []

        by_id: dict[str, WorkspaceSessionRecord] = {}
        for session in agent_sessions:
            if getattr(session, "workspace", None) != workspace["local_path"]:
                continue
            local_title = local_records.get(session.session_id, {}).get("title")
            agent_title = _clean_session_title(session.title)
            title = agent_title if agent_title != "Untitled Session" else local_title
            self.repository.associate_session(
                workspace_id,
                session.session_id,
                agent_id=agent_id,
                title=title,
                created_at=session.created_at,
                updated_at=session.updated_at,
            )
            by_id[session.session_id] = WorkspaceSessionRecord(
                workspace_id=workspace_id,
                session_id=session.session_id,
                title=title,
                created_at=session.created_at,
                updated_at=session.updated_at,
                message_count=session.message_count,
                agent_id=agent_id,
            )

        for session_id, row in local_records.items():
            if session_id in by_id:
                continue
            by_id[session_id] = WorkspaceSessionRecord(
                workspace_id=workspace_id,
                session_id=session_id,
                title=row.get("title"),
                created_at=int(row.get("created_at") or 0),
                updated_at=int(row.get("updated_at") or 0),
                message_count=0,
                agent_id=row.get("agent_id") or agent_id,
            )

        return _with_unique_session_titles(
            sorted(by_id.values(), key=lambda item: item.updated_at, reverse=True)
        )

    async def create_workspace_session(
        self, workspace_id: str, engine, *, agent_id: str = "hermes"
    ) -> WorkspaceSessionRecord:
        workspace = self.repository.get_by_id(workspace_id)
        if not workspace:
            raise WorkspaceNotFoundError("Workspace not found")
        session_info = await engine.create_session(workspace["local_path"])
        existing_titles = [
            row.get("title") for row in self.repository.list_sessions(workspace_id)
        ]
        title = _unique_session_title(session_info.title, existing_titles)
        self.repository.update_session(workspace_id, session_info.session_id)
        self.repository.associate_session(
            workspace_id,
            session_info.session_id,
            agent_id=agent_id,
            title=title,
            created_at=session_info.created_at,
            updated_at=session_info.updated_at,
        )
        self.refresh_agent_context_for_path(
            workspace["local_path"],
            agent_id=agent_id,
            workspace_id=workspace_id,
            session_id=session_info.session_id,
        )
        return WorkspaceSessionRecord(
            workspace_id=workspace_id,
            session_id=session_info.session_id,
            title=title,
            created_at=session_info.created_at,
            updated_at=session_info.updated_at,
            message_count=session_info.message_count,
            agent_id=agent_id,
        )

    async def select_workspace_session(
        self, workspace_id: str, session_id: str, engine, *, agent_id: str = "hermes"
    ) -> WorkspaceActivation:
        workspace = self.repository.get_by_id(workspace_id)
        if not workspace:
            raise WorkspaceNotFoundError("Workspace not found")

        owner = self.repository.get_by_session(session_id)
        if owner and owner["workspace_id"] != workspace_id:
            raise WorkspaceInvalidRequestError(
                "Session is not associated with this workspace"
            )

        known = {
            row["session_id"] for row in self.repository.list_sessions(workspace_id)
        }
        if session_id not in known:
            try:
                workspace_path = await engine.get_session_workspace(session_id)
            except Exception:
                workspace_path = None
            if workspace_path != workspace["local_path"]:
                raise WorkspaceInvalidRequestError(
                    "Session is not associated with this workspace"
                )

        self.repository.update_session(workspace_id, session_id)
        active_session_id = await self._verify_agent_session(
            session_id,
            workspace["local_path"],
            engine,
            allow_fallback=False,
        )
        refreshed = self.refresh_agent_context_for_path(
            workspace["local_path"],
            agent_id=agent_id,
            workspace_id=workspace_id,
            session_id=active_session_id,
        )
        self.notifier.publish(
            "workspace.session.selected",
            workspace_id=workspace_id,
            session_id=active_session_id,
        )
        return WorkspaceActivation(
            success=True,
            session_id=active_session_id,
            workspace_path=workspace["local_path"],
            context=refreshed,
        )

    def list_workspace_tools_by_workspace(
        self, workspace_id: str
    ) -> WorkspaceToolState:
        return self.tools.list_by_workspace(workspace_id)

    def set_workspace_tool_enabled_by_workspace(
        self, workspace_id: str, server_id: str, is_enabled: bool
    ) -> WorkspaceToolState:
        state = self.tools.set_by_workspace(workspace_id, server_id, is_enabled)
        self.notifier.publish("workspace.tools.changed", workspace_id=workspace_id)
        return state

    def list_workspace_tools(self, session_id: str) -> WorkspaceToolState:
        return self.tools.list_by_session(session_id)

    def set_workspace_tool_enabled(
        self, session_id: str, server_id: str, is_enabled: bool
    ) -> WorkspaceToolState:
        state = self.tools.set_by_session(session_id, server_id, is_enabled)
        workspace = self.repository.get_by_session(session_id)
        self.notifier.publish(
            "workspace.tools.changed",
            workspace_id=(workspace or {}).get("workspace_id"),
            session_id=session_id,
        )
        return state

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
            stdout = (
                exc.stdout.decode("utf-8", errors="replace")
                if isinstance(exc.stdout, bytes)
                else (exc.stdout or "")
            )
            stderr = (
                exc.stderr.decode("utf-8", errors="replace")
                if isinstance(exc.stderr, bytes)
                else (exc.stderr or f"Process timed out after {timeout} seconds.")
            )
            return FileExecutionResult(
                success=False,
                stdout=stdout,
                stderr=stderr,
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
        if self.repository.get_by_path(local_path):
            raise WorkspaceConflictError(
                f"Workspace directory path already exists: {local_path}"
            )
        if self.repository.get_by_name(name.strip()):
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
            row = self.repository.get_by_path(workspace_path)
            if row:
                self.repository.update_session(
                    row["workspace_id"], session_info.session_id
                )
            return session_info.session_id
        except Exception as exc:
            logger.warning(
                "agent_session_verify_failed",
                session_id=session_id,
                error=redact_text(exc),
            )
            return session_id
