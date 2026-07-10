"""Typed repository for existing Wright workspace and session state."""

from __future__ import annotations

import json
import os
import time
import uuid
from collections.abc import Mapping
from typing import Any

from core.secrets import CredentialReference, SecretProvider

from .state_store import connect_state_db

ACTIVE_GATEWAY_SESSION_SETTING = "active_gateway_session_id"
SYNTHETIC_SESSION_PREFIXES = ("local-", "local-session-")


def sanitize_workspace_name(name: str) -> str:
    import re

    clean = re.sub(r"[^a-z0-9_-]", "-", (name or "").lower())
    return re.sub(r"-+", "-", clean).strip("-_")


def is_synthetic_session_workspace(row: Mapping[str, Any]) -> bool:
    session_id = str(row.get("session_id") or "").strip()
    local_path = str(row.get("local_path") or "").rstrip("/\\")
    basename = os.path.basename(local_path)
    display_name = str(row.get("workspace_name") or "").strip() or basename
    synthetic = session_id.startswith(
        SYNTHETIC_SESSION_PREFIXES
    ) or basename.startswith(SYNTHETIC_SESSION_PREFIXES)
    return synthetic and display_name in {session_id, basename}


class WorkspaceRepository:
    def __init__(self, db_path: str, *, secrets: SecretProvider) -> None:
        self.db_path = db_path
        self.secrets = secrets

    def _ensure_sessions(self, conn) -> None:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS workspace_agent_sessions (
                workspace_id TEXT NOT NULL,
                session_id TEXT NOT NULL UNIQUE,
                agent_id TEXT NOT NULL DEFAULT 'hermes',
                title TEXT,
                created_at INTEGER NOT NULL,
                updated_at INTEGER NOT NULL,
                is_archived INTEGER NOT NULL DEFAULT 0 CHECK(is_archived IN (0, 1)),
                PRIMARY KEY (workspace_id, session_id),
                FOREIGN KEY (workspace_id) REFERENCES engineering_workspaces(workspace_id) ON DELETE CASCADE
            )
            """
        )
        conn.execute(
            """
            INSERT OR IGNORE INTO workspace_agent_sessions (
                workspace_id, session_id, agent_id, title, created_at, updated_at, is_archived
            )
            SELECT workspace_id, session_id, 'hermes', workspace_name, created_at, updated_at, 0
            FROM engineering_workspaces
            WHERE session_id IS NOT NULL AND session_id != ''
            """
        )

    def get_by_session(self, session_id: str) -> dict[str, Any] | None:
        with connect_state_db(self.db_path) as conn:
            self._ensure_sessions(conn)
            row = conn.execute(
                "SELECT * FROM engineering_workspaces WHERE session_id = ?",
                (session_id,),
            ).fetchone()
            if not row:
                row = conn.execute(
                    """
                    SELECT ew.* FROM engineering_workspaces ew
                    JOIN workspace_agent_sessions was ON was.workspace_id = ew.workspace_id
                    WHERE was.session_id = ? AND was.is_archived = 0
                    """,
                    (session_id,),
                ).fetchone()
            return dict(row) if row else None

    def get_by_id(self, workspace_id: str) -> dict[str, Any] | None:
        with connect_state_db(self.db_path) as conn:
            row = conn.execute(
                "SELECT * FROM engineering_workspaces WHERE workspace_id = ?",
                (workspace_id,),
            ).fetchone()
            return dict(row) if row else None

    def get_by_path(self, local_path: str) -> dict[str, Any] | None:
        with connect_state_db(self.db_path) as conn:
            row = conn.execute(
                "SELECT * FROM engineering_workspaces WHERE local_path = ?",
                (local_path,),
            ).fetchone()
            return dict(row) if row else None

    def get_by_name(self, workspace_name: str) -> dict[str, Any] | None:
        with connect_state_db(self.db_path) as conn:
            row = conn.execute(
                "SELECT * FROM engineering_workspaces WHERE workspace_name = ?",
                (workspace_name,),
            ).fetchone()
            return dict(row) if row else None

    def list_recent(self, limit: int = 5) -> list[dict[str, Any]]:
        with connect_state_db(self.db_path) as conn:
            rows = conn.execute(
                "SELECT * FROM engineering_workspaces ORDER BY updated_at DESC LIMIT ?",
                (max(limit * 4, limit),),
            ).fetchall()
        return [
            row
            for item in rows
            if not is_synthetic_session_workspace(row := dict(item))
        ][:limit]

    def list_all(self) -> list[dict[str, Any]]:
        with connect_state_db(self.db_path) as conn:
            rows = conn.execute(
                "SELECT * FROM engineering_workspaces ORDER BY local_path ASC"
            ).fetchall()
        return [
            dict(row) for row in rows if not is_synthetic_session_workspace(dict(row))
        ]

    def associate_session(
        self,
        workspace_id: str,
        session_id: str,
        *,
        agent_id: str = "hermes",
        title: str | None = None,
        created_at: int | None = None,
        updated_at: int | None = None,
        reassign_if_owned: bool = False,
    ) -> None:
        if not workspace_id or not session_id:
            return
        now = int(time.time())
        created = int(created_at or now)
        updated = int(updated_at or created)
        with connect_state_db(self.db_path) as conn:
            self._ensure_sessions(conn)
            if reassign_if_owned:
                conn.execute(
                    "DELETE FROM workspace_agent_sessions WHERE session_id = ?",
                    (session_id,),
                )
            conn.execute(
                """
                INSERT INTO workspace_agent_sessions (
                    workspace_id, session_id, agent_id, title, created_at, updated_at, is_archived
                ) VALUES (?, ?, ?, ?, ?, ?, 0)
                ON CONFLICT(workspace_id, session_id) DO UPDATE SET
                    agent_id = excluded.agent_id,
                    title = COALESCE(excluded.title, workspace_agent_sessions.title),
                    updated_at = MAX(workspace_agent_sessions.updated_at, excluded.updated_at),
                    is_archived = 0
                """,
                (workspace_id, session_id, agent_id, title, created, updated),
            )

    def list_sessions(
        self, workspace_id: str, *, include_archived: bool = False
    ) -> list[dict[str, Any]]:
        with connect_state_db(self.db_path) as conn:
            self._ensure_sessions(conn)
            archived = "" if include_archived else " AND is_archived = 0"
            rows = conn.execute(
                f"""SELECT * FROM workspace_agent_sessions
                WHERE workspace_id = ?{archived}
                ORDER BY updated_at DESC, created_at DESC""",  # noqa: S608 - fixed clause
                (workspace_id,),
            ).fetchall()
            return [dict(row) for row in rows]

    def create(
        self,
        workspace_id: str,
        session_id: str,
        local_path: str,
        *,
        workspace_name: str | None = None,
        git_remote_url: str | None = None,
        git_username: str | None = None,
        git_token: str | None = None,
    ) -> None:
        now = int(time.time())
        with connect_state_db(self.db_path) as conn:
            conn.execute(
                """INSERT OR REPLACE INTO engineering_workspaces (
                    workspace_id, session_id, workspace_name, local_path,
                    git_remote_url, git_username, git_token, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, NULL, ?, ?)""",
                (
                    workspace_id,
                    session_id,
                    workspace_name,
                    local_path,
                    git_remote_url,
                    git_username,
                    now,
                    now,
                ),
            )
        if git_token:
            self.secrets.set(
                CredentialReference("workspace", workspace_id, "GIT_TOKEN"), git_token
            )
        self.associate_session(
            workspace_id,
            session_id,
            title=workspace_name,
            created_at=now,
            updated_at=now,
            reassign_if_owned=True,
        )

    def create_dashboard(
        self, name: str, local_path: str, session_id: str | None = None
    ) -> dict[str, Any]:
        if not os.path.isabs(local_path):
            raise ValueError("local_path must be an absolute path")
        if not os.path.isdir(local_path):
            raise ValueError(f"Directory does not exist: {local_path}")
        cleaned = name.strip()
        if not cleaned:
            raise ValueError("Workspace name must not be empty")
        if len(name) > 100:
            raise ValueError("Workspace name must be 100 characters or fewer")
        workspace_id = str(uuid.uuid4())
        active_session = session_id or str(uuid.uuid4())
        self.create(
            workspace_id,
            active_session,
            local_path,
            workspace_name=cleaned,
        )
        return self.get_by_id(workspace_id) or {}

    def touch(self, session_id: str) -> None:
        now = int(time.time())
        workspace = self.get_by_session(session_id)
        with connect_state_db(self.db_path) as conn:
            if workspace:
                conn.execute(
                    "UPDATE engineering_workspaces SET updated_at = ? WHERE workspace_id = ?",
                    (now, workspace["workspace_id"]),
                )
                self._ensure_sessions(conn)
                conn.execute(
                    """UPDATE workspace_agent_sessions SET updated_at = ?
                    WHERE workspace_id = ? AND session_id = ?""",
                    (now, workspace["workspace_id"], session_id),
                )

    def set_active_gateway_session(self, session_id: str) -> None:
        if not session_id:
            return
        with connect_state_db(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO system_settings (key, value) VALUES (?, ?)",
                (ACTIVE_GATEWAY_SESSION_SETTING, session_id),
            )

    def update_session(self, workspace_id: str, session_id: str) -> None:
        now = int(time.time())
        with connect_state_db(self.db_path) as conn:
            conn.execute(
                """UPDATE engineering_workspaces SET session_id = ?, updated_at = ?
                WHERE workspace_id = ?""",
                (session_id, now, workspace_id),
            )
        self.associate_session(workspace_id, session_id, created_at=now, updated_at=now)

    def enabled_tools(self, workspace_id: str) -> list[str] | None:
        with connect_state_db(self.db_path) as conn:
            row = conn.execute(
                "SELECT enabled_tools FROM engineering_workspaces WHERE workspace_id = ?",
                (workspace_id,),
            ).fetchone()
        if not row or row["enabled_tools"] is None:
            return None
        try:
            value = json.loads(row["enabled_tools"])
            return value if isinstance(value, list) else None
        except (TypeError, json.JSONDecodeError):
            return None

    def set_enabled_tools(self, workspace_id: str, tools: list[str]) -> None:
        with connect_state_db(self.db_path) as conn:
            conn.execute(
                """UPDATE engineering_workspaces SET enabled_tools = ?, updated_at = ?
                WHERE workspace_id = ?""",
                (json.dumps(tools), int(time.time()), workspace_id),
            )

    def update_remote(
        self,
        workspace_id: str,
        git_remote_url: str | None,
        git_username: str | None,
        git_token: str | None,
        workspace_prompt: str | None = None,
        git_large_file_threshold: int | None = None,
    ) -> None:
        with connect_state_db(self.db_path) as conn:
            conn.execute(
                """UPDATE engineering_workspaces
                SET git_remote_url = ?, git_username = ?, git_token = NULL,
                    workspace_prompt = ?, git_large_file_threshold = ?, updated_at = ?
                WHERE workspace_id = ?""",
                (
                    git_remote_url,
                    git_username,
                    workspace_prompt,
                    git_large_file_threshold,
                    int(time.time()),
                    workspace_id,
                ),
            )
        if git_token:
            self.secrets.set(
                CredentialReference("workspace", workspace_id, "GIT_TOKEN"), git_token
            )

    def git_token(self, workspace_id: str) -> str | None:
        return self.secrets.get(
            CredentialReference("workspace", workspace_id, "GIT_TOKEN")
        )

    def has_git_token(self, workspace_id: str) -> bool:
        return self.secrets.status(
            CredentialReference("workspace", workspace_id, "GIT_TOKEN")
        ).configured

    def save_context(self, workspace_id: str, context_data: str) -> None:
        with connect_state_db(self.db_path) as conn:
            conn.execute(
                """INSERT OR REPLACE INTO agent_contexts
                (workspace_id, context_data, updated_at) VALUES (?, ?, ?)""",
                (workspace_id, context_data, int(time.time())),
            )

    def load_context(self, workspace_id: str) -> dict[str, Any] | None:
        with connect_state_db(self.db_path) as conn:
            row = conn.execute(
                "SELECT * FROM agent_contexts WHERE workspace_id = ?", (workspace_id,)
            ).fetchone()
            return dict(row) if row else None
