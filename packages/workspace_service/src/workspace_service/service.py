from __future__ import annotations

import hashlib
import ntpath
import os
from pathlib import Path
import subprocess
import sys
import uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace
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
from data_vault import (
    WorkflowRepository,
    WorkflowReviewRepository,
    WorkflowRunRepository,
    WorkspaceRepository,
    create_default_secret_provider,
)
from data_vault.workspace_repository import sanitize_workspace_name
from tool_registry.db import get_servers

from .adapters import LocalProcessRunner, LocalWorkspaceFiles, LocalWorkspaceGit
from .adapters.runtime import (
    WorkspaceManager,
    get_workspace_enabled_tools,
    sync_workspace_runners,
    write_workspace_agent_context,
)
from .errors import (
    WorkspaceConflictError,
    WorkspaceInvalidRequestError,
    WorkspaceNotFoundError,
    WorkspaceProtectedPathError,
)
from .executor import BoundedExecutor
from .models import (
    FileExecutionPolicy,
    FileExecutionResult,
    WorkspaceActivation,
    WorkspaceRecord,
    WorkspaceSessionRecord,
    WorkspaceToolState,
)
from .ports import WorkspaceNotifier
from .use_cases import (
    WorkspaceContextUseCases,
    WorkspaceFileUseCases,
    WorkspaceGitUseCases,
    WorkspaceLifecycleUseCases,
    WorkspaceToolUseCases,
    WorkspaceWorkflowUseCases,
)
from .use_cases.run import issue_display_execution_lease
from .surfaces.display_tokens import DisplayExecutionTokenService
from .surfaces.process_supervisor import ProcessAdapter, ProcessSupervisor
from .workflow_runner import RunnerSettings, WorkspaceWorkflowRunner
from .rivet_runtime_host import RivetRuntimeHost
from .workflow_editor import WorkspaceWorkflowEditor
from .workflow_graph import WorkspaceWorkflowGraphOperations
from .workflow_operations import WorkspaceWorkflowOperations
from .workflow_catalog import WorkflowTemplateCatalog
from .engineering_scenario_service import EngineeringScenarioService
from .workspace_path import WorkspacePath

logger = get_logger(__name__)


@dataclass(frozen=True)
class SessionWorkspaceAuthorization:
    path: str
    workspace_id: str | None
    created: bool


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
    configured_root = source.get("WRIGHT_WORKSPACES_DIR")
    if configured_root:
        return configured_root
    home_dir = (
        source.get("USERPROFILE") or source.get("HOME") or os.path.expanduser("~")
    )
    if ":" in home_dir or "\\" in home_dir:
        return ntpath.join(home_dir, "wright")
    return os.path.join(home_dir, "wright")


def default_protected_application_roots() -> tuple[str, ...]:
    """Return Wright source/install roots that must never become workspaces."""

    module_dir = Path(__file__).resolve().parent
    roots = {module_dir}
    for candidate in module_dir.parents:
        if (
            (candidate / "pyproject.toml").is_file()
            and (candidate / "apps" / "api").is_dir()
            and (candidate / "packages" / "workspace_service").is_dir()
        ):
            roots.add(candidate)
            break
    return tuple(str(root) for root in roots)


def _paths_overlap(left: Path, right: Path) -> bool:
    try:
        common = os.path.commonpath((str(left), str(right)))
    except ValueError:
        return False
    common_identity = os.path.normcase(os.path.normpath(common))
    return common_identity in {
        os.path.normcase(os.path.normpath(str(left))),
        os.path.normcase(os.path.normpath(str(right))),
    }


def workspace_path_overlaps_application(
    local_path: str,
    protected_roots: tuple[str, ...] | None = None,
) -> bool:
    if not str(local_path or "").strip():
        return False
    candidate = Path(local_path).expanduser().resolve(strict=False)
    roots = (
        default_protected_application_roots()
        if protected_roots is None
        else protected_roots
    )
    return any(
        _paths_overlap(
            candidate,
            Path(root).expanduser().resolve(strict=False),
        )
        for root in roots
        if str(root or "").strip()
    )


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
        protected_roots_provider: Callable[
            [], tuple[str, ...]
        ] = default_protected_application_roots,
        materializers: Mapping[str, AgentContextMaterializer] | None = None,
        executor: BoundedExecutor | None = None,
        repository: WorkspaceRepository | None = None,
        notifier: WorkspaceNotifier | None = None,
    ) -> None:
        self.db_path = db_path
        self.parent_dir_provider = parent_dir_provider
        self.protected_roots_provider = protected_roots_provider
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
        self.workflows = WorkspaceWorkflowUseCases(
            self.executor, WorkflowRepository(db_path)
        )
        self.workflow_templates = WorkflowTemplateCatalog()
        self.workflow_graph = WorkspaceWorkflowGraphOperations(self.workflows)
        self.workflow_editor = WorkspaceWorkflowEditor(self.workflows)
        runner_adapter: ProcessAdapter
        if os.name == "nt":
            from .surfaces.process_windows import WindowsProcessAdapter

            runner_adapter = WindowsProcessAdapter()
        else:
            from .surfaces.process_posix import PosixProcessAdapter

            runner_adapter = PosixProcessAdapter()
        runner_settings = RunnerSettings.from_env()
        runner_supervisor = ProcessSupervisor(adapter=runner_adapter)
        self.workflow_runner = WorkspaceWorkflowRunner(
            supervisor=runner_supervisor,
            settings=runner_settings,
            runtime_host=RivetRuntimeHost(
                supervisor=runner_supervisor, settings=runner_settings
            ),
            run_repository=WorkflowRunRepository(
                db_path,
                maximum_output_bytes=runner_settings.captured_output_bytes,
                maximum_event_bytes=runner_settings.maximum_event_bytes,
            ),
        )
        self.workflow_operations = WorkspaceWorkflowOperations(
            WorkflowReviewRepository(db_path), self.workflow_runner
        )
        self.engineering_scenarios = EngineeringScenarioService(
            db_path, operations=self.workflow_operations
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
            self.ensure_workspace_path_safe(workspace["local_path"])
            try:
                actual_workspace_path = await engine.get_session_workspace(session_id)
            except Exception:
                actual_workspace_path = None
            if (
                actual_workspace_path
                and actual_workspace_path != workspace["local_path"]
            ):
                logger.warning(
                    "workspace_agent_path_mismatch_ignored",
                    session_id=session_id,
                    persisted_path=workspace["local_path"],
                    agent_path=actual_workspace_path,
                )
            return workspace["local_path"]

        try:
            reported_workspace_path = await engine.get_session_workspace(session_id)
        except Exception as exc:
            logger.warning(
                "workspace_session_lookup_failed_using_local_workspace",
                session_id=session_id,
                error=redact_text(exc),
            )
            reported_workspace_path = None
        if reported_workspace_path:
            logger.warning(
                "unbound_agent_workspace_ignored",
                session_id=session_id,
                agent_path=reported_workspace_path,
            )

        fallback_slug = uuid.uuid5(
            uuid.NAMESPACE_URL, f"wright-session:{session_id}"
        ).hex
        workspace_path = self._managed_workspace_path(
            f"session-{fallback_slug}", create=True
        )
        return workspace_path

    def authorize_session_workspace(
        self, requested_path: str | None
    ) -> SessionWorkspaceAuthorization:
        """Resolve a request to registered storage or create a generated managed path."""

        if requested_path:
            if "\x00" in requested_path:
                raise WorkspaceInvalidRequestError(
                    "Session workspace must reference a registered workspace."
                )
            workspace = self.repository.get_by_path(requested_path)
            if not workspace:
                raise WorkspaceInvalidRequestError(
                    "Session workspace must reference a registered workspace."
                )
            registered = Path(str(workspace["local_path"])).expanduser()
            if not registered.is_absolute():
                raise WorkspaceInvalidRequestError(
                    "Registered workspace path must be absolute."
                )
            try:
                canonical = registered.resolve(strict=True)
            except (FileNotFoundError, OSError) as exc:
                raise WorkspaceInvalidRequestError(
                    "Session workspace must reference an existing directory."
                ) from exc
            if not canonical.is_dir():
                raise WorkspaceInvalidRequestError(
                    "Session workspace must reference an existing directory."
                )
            lexical = registered.absolute()
            if os.path.normcase(str(lexical)) != os.path.normcase(str(canonical)):
                raise WorkspaceInvalidRequestError(
                    "Session workspace aliases are not permitted."
                )
            self.ensure_workspace_path_safe(str(canonical))
            return SessionWorkspaceAuthorization(
                path=str(canonical),
                workspace_id=str(workspace["workspace_id"]),
                created=False,
            )

        workspace_name = f"session-{uuid.uuid4().hex}"
        managed = self._managed_workspace_path(workspace_name, create=True)
        return SessionWorkspaceAuthorization(
            path=managed,
            workspace_id=None,
            created=True,
        )

    def _managed_workspace_path(
        self,
        workspace_name: str,
        requested_path: str | None = None,
        *,
        create: bool = False,
    ) -> str:
        sanitized = sanitize_workspace_name(workspace_name)
        if not sanitized:
            raise WorkspaceInvalidRequestError(
                "Workspace name cannot be empty or invalid."
            )
        root = Path(self.parent_dir_provider()).expanduser().resolve(strict=False)
        managed = (root / sanitized).resolve(strict=False)
        if managed.parent != root:
            raise WorkspaceInvalidRequestError(
                "Workspace path must remain inside the configured Wright workspace root."
            )
        self.ensure_workspace_path_safe(str(managed))
        if requested_path is not None:
            requested_identity = requested_path.rstrip("/\\")
            managed_identity = str(managed).rstrip("/\\")
            if os.name == "nt":
                requested_identity = requested_identity.replace("/", "\\").casefold()
                managed_identity = managed_identity.replace("/", "\\").casefold()
            if requested_identity != managed_identity:
                raise WorkspaceInvalidRequestError(
                    "Explicit workspace path must match the managed path derived from its name."
                )
        if create:
            managed.mkdir(parents=True, exist_ok=True)
        return str(managed)

    def ensure_workspace_path_safe(self, local_path: str) -> str:
        """Reject workspaces that overlap Wright's own source or install files."""

        if not str(local_path or "").strip():
            raise WorkspaceInvalidRequestError("Workspace path cannot be empty.")
        candidate = Path(local_path).expanduser().resolve(strict=False)
        protected_roots = self.protected_roots_provider()
        if workspace_path_overlaps_application(str(candidate), protected_roots):
            logger.error(
                "workspace_protected_path_rejected",
                workspace_path=str(candidate),
            )
            raise WorkspaceProtectedPathError(
                "Workspace access blocked because its path overlaps Wright "
                "application files. Create or select a dedicated engineering "
                f"workspace under {self.parent_dir_provider()} instead."
            )
        return str(candidate)

    def workspace_path_is_safe(self, local_path: str) -> bool:
        try:
            self.ensure_workspace_path_safe(local_path)
        except WorkspaceProtectedPathError:
            return False
        return True

    def require_safe_workspace(self, workspace_id: str) -> Mapping[str, Any]:
        workspace = self.repository.get_by_id(workspace_id)
        if not workspace:
            raise WorkspaceNotFoundError("Workspace not found")
        self.ensure_workspace_path_safe(workspace["local_path"])
        return workspace

    def require_safe_session_workspace(self, session_id: str) -> Mapping[str, Any]:
        workspace = self.repository.get_by_session(session_id)
        if not workspace:
            raise WorkspaceNotFoundError("Workspace not found")
        self.ensure_workspace_path_safe(workspace["local_path"])
        return workspace

    def _workspace_file(self, workspace_path: str, requested_path: str) -> Path:
        normalized = requested_path.replace("\\", "/")
        if normalized.startswith("/") and not normalized.startswith("//"):
            normalized = normalized[1:]
        try:
            candidate = WorkspacePath(workspace_path).resolve(
                normalized, must_exist=True
            )
        except (FileNotFoundError, ValueError) as exc:
            raise WorkspaceInvalidRequestError(
                "Requested file must be a regular file inside the workspace."
            ) from exc
        if not candidate.is_file():
            raise WorkspaceInvalidRequestError(
                "Requested file must be a regular file inside the workspace."
            )
        return candidate

    async def close(self) -> None:
        await self.workflow_runner.shutdown()
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
        workspace_path = self._managed_workspace_path(name, local_path)

        self._ensure_workspace_available(name, workspace_path)
        workspace_path = self._managed_workspace_path(name, local_path, create=True)
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
        self.ensure_workspace_path_safe(workspace_path)

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
        self.ensure_workspace_path_safe(workspace["local_path"])

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
        self.ensure_workspace_path_safe(workspace["local_path"])
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
        self.ensure_workspace_path_safe(workspace["local_path"])

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
        self.require_safe_workspace(workspace_id)
        return self.tools.list_by_workspace(workspace_id)

    def set_workspace_tool_enabled_by_workspace(
        self, workspace_id: str, server_id: str, is_enabled: bool
    ) -> WorkspaceToolState:
        self.require_safe_workspace(workspace_id)
        state = self.tools.set_by_workspace(workspace_id, server_id, is_enabled)
        self.notifier.publish("workspace.tools.changed", workspace_id=workspace_id)
        return state

    def list_workspace_tools(self, session_id: str) -> WorkspaceToolState:
        self.require_safe_session_workspace(session_id)
        return self.tools.list_by_session(session_id)

    def set_workspace_tool_enabled(
        self, session_id: str, server_id: str, is_enabled: bool
    ) -> WorkspaceToolState:
        self.require_safe_session_workspace(session_id)
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
        display_tokens: DisplayExecutionTokenService | None = None,
        display_endpoint: str | None = None,
        principal_id: str = "local-user",
        trace_id: str = "no-active-trace",
    ) -> FileExecutionResult:
        workspace_path = await self.resolve_workspace_dir(session_id, engine)
        full_path = self._workspace_file(workspace_path, path)
        if full_path.suffix.casefold() != ".py":
            raise WorkspaceInvalidRequestError(
                "Only Python files (.py) are supported for running."
            )

        timeout = (policy or FileExecutionPolicy()).timeout_seconds
        display_lease = None
        if display_tokens is not None and display_endpoint:
            workspace = self.repository.get_by_session(session_id)
            if workspace is None:
                raise WorkspaceNotFoundError("Workspace session not found.")
            script = full_path.read_text(encoding="utf-8")
            execution_id = str(uuid.uuid4())
            display_lease = issue_display_execution_lease(
                token_service=display_tokens,
                endpoint=display_endpoint,
                user_id=principal_id,
                workspace_id=workspace["workspace_id"],
                session_id=session_id,
                task_id=(
                    "file-run-"
                    + hashlib.sha256(
                        str(full_path.relative_to(workspace_path)).encode("utf-8")
                    ).hexdigest()[:32]
                ),
                execution_id=execution_id,
                prompt=None,
                effective_constraints={
                    "contract_version": 1,
                    "execution_kind": "workspace_file",
                },
                script=script,
                script_revision=max(1, full_path.stat().st_mtime_ns),
                trace_id=trace_id,
                lifetime_seconds=timeout + 30,
            )
        command = [
            sys.executable,
            "-c",
            "import runpy,sys; runpy.run_path(sys.stdin.readline().rstrip('\\n'), run_name='__main__')",
        ]
        logger.info(
            "workspace_file_execute",
            command=redact_command(command),
            timeout_seconds=timeout,
        )
        try:
            environment = None
            if display_lease is not None:
                environment = os.environ.copy()
                environment.update(display_lease.environment())
            result = subprocess.run(
                command,
                cwd=workspace_path,
                capture_output=True,
                text=True,
                input=f"{full_path}\n",
                timeout=timeout,
                env=environment,
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
        finally:
            if display_lease is not None:
                display_lease.revoke()

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
