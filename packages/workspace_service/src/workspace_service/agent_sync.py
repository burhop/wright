from __future__ import annotations

import asyncio
import os
import sqlite3
from collections.abc import Awaitable, Callable

from core.logging import get_logger

from .adapters.runtime import get_workspace_by_session

logger = get_logger(__name__)


class GatewayRefreshNotObserved(RuntimeError):
    """A successful lifecycle command did not establish a new agent process."""


class AgentSyncManager:
    """Persist active agent selection and synchronize explicit workspace context."""

    def __init__(
        self,
        db_path: str,
        workspace_sync: Callable[[str, str], bool] | None = None,
    ):
        self.db_path = db_path
        self._workspace_sync = workspace_sync
        self._gateway_restart_required = False
        self._gateway_refresh_in_progress = False
        self._gateway_refresh_error: str | None = None
        self._gateway_refresh_lock = asyncio.Lock()
        self._gateway_binding_revision = 0
        self._gateway_refresh_workspace_id: str | None = None
        self._gateway_restarted_revision: int | None = None
        self._gateway_runtime_before_refresh: tuple[int, str] | None = None
        self._active_agent = "hermes"
        self._load_active_agent()

    @property
    def active_agent(self) -> str:
        return self._active_agent

    @active_agent.setter
    def active_agent(self, agent_name: str) -> None:
        self._active_agent = agent_name.lower().strip()
        logger.info("agent_active_runtime_selected", agent=self._active_agent)
        self._save_active_agent()

    def sync_workspace_tools(self, session_id: str) -> bool:
        """Record the active workspace for agent-neutral gateway/catalog sync.

        Provider-specific profile files are materialized by agent adapter/profile
        services, not by core.
        """
        workspace = get_workspace_by_session(self.db_path, session_id)
        if not workspace:
            logger.warning(
                "agent_workspace_sync_skipped_missing_workspace",
                agent=self._active_agent,
                session_id=session_id,
            )
            return self._gateway_restart_required

        if self._active_agent == "hermes" and self._workspace_sync is not None:
            restart_required = bool(self._workspace_sync(session_id, self.db_path))
            self._gateway_refresh_workspace_id = str(workspace["workspace_id"])
            if restart_required:
                self._gateway_refresh_error = None
                self._gateway_binding_revision += 1
                self._gateway_runtime_before_refresh = None
            self._gateway_restart_required = (
                restart_required or self._gateway_restart_required
            )

        logger.info(
            "agent_workspace_sync_recorded",
            agent=self._active_agent,
            session_id=session_id,
            workspace_id=workspace.get("workspace_id"),
        )
        return self._gateway_restart_required

    def mark_gateway_refreshed(self) -> None:
        self._gateway_restart_required = False
        self._gateway_refresh_error = None
        self._gateway_restarted_revision = None
        self._gateway_runtime_before_refresh = None

    @property
    def gateway_refresh_workspace_id(self) -> str | None:
        return self._gateway_refresh_workspace_id

    @property
    def gateway_refresh_in_progress(self) -> bool:
        return self._gateway_refresh_in_progress

    @property
    def gateway_refresh_pending(self) -> bool:
        return self._gateway_restart_required and self._gateway_refresh_error is None

    @property
    def gateway_refresh_error(self) -> str | None:
        return self._gateway_refresh_error

    async def observe_gateway_before_refresh(
        self,
        workspace_id: str,
        runtime_identity: Callable[[], Awaitable[str]],
    ) -> bool:
        """Retain the pending revision's baseline before offering manual recovery."""
        async with self._gateway_refresh_lock:
            if (
                not self._gateway_restart_required
                or self._gateway_refresh_workspace_id != workspace_id
            ):
                return False
            revision = self._gateway_binding_revision
            before = self._gateway_runtime_before_refresh
            if before is not None and before[0] == revision:
                return True
            observed = await runtime_identity()
            if (
                revision != self._gateway_binding_revision
                or self._gateway_refresh_workspace_id != workspace_id
            ):
                return False
            self._gateway_runtime_before_refresh = (revision, observed)
            return True

    async def refresh_gateway_if_needed(
        self,
        refresh: Callable[[], Awaitable[None]],
        *,
        wait_ready: Callable[[], Awaitable[None]] | None = None,
        runtime_identity: Callable[[], Awaitable[str]] | None = None,
    ) -> bool:
        """Serialize refresh; a readiness timeout must not repeat a proven restart."""
        async with self._gateway_refresh_lock:
            if not self._gateway_restart_required:
                return False
            revision = self._gateway_binding_revision
            self._gateway_refresh_in_progress = True
            try:
                replacement_observed = False
                if runtime_identity is not None:
                    before = self._gateway_runtime_before_refresh
                    current = await runtime_identity()
                    if before is None or before[0] != revision:
                        before = (revision, current)
                        self._gateway_runtime_before_refresh = before
                    else:
                        replacement_observed = current != before[1]
                if replacement_observed:
                    self._gateway_restarted_revision = revision
                if self._gateway_restarted_revision != revision:
                    await refresh()
                    self._gateway_restarted_revision = revision
                if wait_ready is not None:
                    await wait_ready()
                if runtime_identity is not None:
                    # A detached native launch can briefly leave the old healthy
                    # process serving. Observe the same issued replacement; do
                    # not issue another restart during its startup window.
                    deadline = asyncio.get_running_loop().time() + 120.0
                    while True:
                        try:
                            observed = await asyncio.wait_for(
                                runtime_identity(), timeout=5.0
                            )
                        except Exception:
                            observed = before[1]
                        if observed != before[1]:
                            break
                        remaining = deadline - asyncio.get_running_loop().time()
                        if remaining <= 0:
                            raise GatewayRefreshNotObserved(
                                "Agent gateway process replacement was not observed"
                            )
                        await asyncio.sleep(min(0.25, remaining))
                if revision != self._gateway_binding_revision:
                    raise RuntimeError(
                        "Workspace binding changed during gateway refresh"
                    )
            except Exception as exc:
                self._gateway_refresh_error = str(exc)
                raise
            finally:
                self._gateway_refresh_in_progress = False
            self.mark_gateway_refreshed()
            return True

    def _load_active_agent(self) -> None:
        if not os.path.exists(self.db_path):
            return
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT value FROM system_settings WHERE key = 'active_agent'"
                )
                row = cursor.fetchone()
                if row:
                    self._active_agent = str(row[0]).lower().strip() or "hermes"
        except Exception as exc:
            logger.warning("agent_active_runtime_load_failed", error=str(exc))

    def _save_active_agent(self) -> None:
        if not os.path.exists(self.db_path):
            return
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO system_settings (key, value) VALUES ('active_agent', ?)",
                    (self._active_agent,),
                )
                conn.commit()
        except Exception as exc:
            logger.error("agent_active_runtime_save_failed", error=str(exc))
