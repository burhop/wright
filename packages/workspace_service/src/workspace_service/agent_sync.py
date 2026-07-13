from __future__ import annotations

import os
import sqlite3

from core.logging import get_logger

from .adapters.runtime import get_workspace_by_session

logger = get_logger(__name__)


class AgentSyncManager:
    """Persist active agent selection and synchronize explicit workspace context."""

    def __init__(self, db_path: str):
        self.db_path = db_path
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

    def sync_workspace_tools(self, session_id: str) -> None:
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
            return

        logger.info(
            "agent_workspace_sync_recorded",
            agent=self._active_agent,
            session_id=session_id,
            workspace_id=workspace.get("workspace_id"),
        )

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
