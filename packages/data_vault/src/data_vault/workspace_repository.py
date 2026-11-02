"""Typed repository for existing Wright workspace and session state."""

from __future__ import annotations

import json
import hashlib
import os
import re
import time
import uuid
from collections.abc import Mapping
from typing import Any

from core.secrets import CredentialReference, SecretProvider

from .state_store import connect_state_db

ACTIVE_GATEWAY_SESSION_SETTING = "active_gateway_session_id"
SYNTHETIC_SESSION_PREFIXES = ("api_", "wright-local-", "local-", "local-session-")
UUID_SESSION_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)
HERMES_NATIVE_SESSION_PATTERN = re.compile(r"^\d{8}_\d{6}_[0-9a-f]+$", re.IGNORECASE)
GENERIC_SESSION_PATTERN = re.compile(r"^session(?:[-_]?.*)?$", re.IGNORECASE)
WORKSPACE_CONFIGURATION_FIELDS = (
    "git_remote_url",
    "git_username",
    "workspace_prompt",
    "git_large_file_threshold",
)


class WorkspaceConfigurationConflict(ValueError):
    """The observed nonsecret configuration is no longer current."""


def _configuration_record(row) -> dict[str, Any]:
    value = {key: row[key] for key in ("workspace_id", *WORKSPACE_CONFIGURATION_FIELDS)}
    revision = hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    return {**value, "revision": revision}


def sanitize_workspace_name(name: str) -> str:
    import re

    clean = re.sub(r"[^a-z0-9_-]", "-", (name or "").lower())
    return re.sub(r"-+", "-", clean).strip("-_")


def is_synthetic_session_workspace(row: Mapping[str, Any]) -> bool:
    """Return True only for rows whose display name is a transient session id."""
    session_id = str(row.get("session_id") or "").strip()
    local_path = str(row.get("local_path") or "").rstrip("/\\")
    basename = os.path.basename(local_path)
    workspace_name = str(row.get("workspace_name") or "").strip()

    def is_synthetic_token(token: str) -> bool:
        return (
            token.startswith(SYNTHETIC_SESSION_PREFIXES)
            or bool(UUID_SESSION_PATTERN.fullmatch(token))
            or bool(HERMES_NATIVE_SESSION_PATTERN.fullmatch(token))
            or bool(GENERIC_SESSION_PATTERN.fullmatch(token))
        )

    display_name = workspace_name or basename
    if not display_name or not is_synthetic_token(display_name):
        return False

    return display_name in {session_id, basename}


class WorkspaceRepository:
    def __init__(self, db_path: str, *, secrets: SecretProvider) -> None:
        self.db_path = db_path
        self.secrets = secrets

    def _ensure_sessions(self, conn, exclude_session_id="") -> None:
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
            WHERE session_id IS NOT NULL AND session_id != '' AND session_id != ?
            """,
            (exclude_session_id,),
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
        agent_id: str | None = None,
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
            self._ensure_sessions(conn, session_id)
            prior = conn.execute(
                "SELECT agent_id FROM workspace_agent_sessions WHERE session_id=?",
                (session_id,),
            ).fetchone()
            if prior and agent_id is not None and prior["agent_id"] != agent_id:
                raise ValueError("Session platform identity is immutable")
            agent_id = prior["agent_id"] if prior else (agent_id or "hermes")
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
                    agent_id = workspace_agent_sessions.agent_id,
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
        agent_id: str = "hermes",
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
            agent_id=agent_id,
        )

    def create_dashboard(
        self,
        name: str,
        local_path: str,
        session_id: str | None = None,
        *,
        agent_id: str = "hermes",
    ) -> dict[str, Any]:
        if not os.path.isabs(local_path):
            raise ValueError("local_path must be an absolute path")
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
            agent_id=agent_id,
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

    def update_session(
        self, workspace_id: str, session_id: str, *, agent_id: str | None = None
    ) -> None:
        now = int(time.time())
        with connect_state_db(self.db_path) as conn:
            conn.execute(
                """UPDATE engineering_workspaces SET session_id = ?, updated_at = ?
                WHERE workspace_id = ?""",
                (session_id, now, workspace_id),
            )
        self.associate_session(
            workspace_id, session_id, agent_id=agent_id, created_at=now, updated_at=now
        )

    def session_platform(self, session_id: str) -> str | None:
        with connect_state_db(self.db_path) as conn:
            self._ensure_sessions(conn)
            row = conn.execute(
                "SELECT agent_id FROM workspace_agent_sessions WHERE session_id=?",
                (session_id,),
            ).fetchone()
        return row["agent_id"] if row else None

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

    def configuration(self, workspace_id: str) -> dict[str, Any]:
        """Read configuration without requesting or copying credential values."""
        with connect_state_db(self.db_path) as conn:
            row = conn.execute(
                "SELECT workspace_id, git_remote_url, git_username, workspace_prompt, "
                "git_large_file_threshold FROM engineering_workspaces WHERE workspace_id = ?",
                (workspace_id,),
            ).fetchone()
        if row is None:
            raise LookupError("Workspace not found")
        return _configuration_record(row)

    def patch_configuration(
        self,
        workspace_id: str,
        *,
        expected_revision: str,
        changes: dict[str, Any],
    ) -> dict[str, Any]:
        """CAS only named preferences; preserve credentials, sessions and tools."""
        if not changes or set(changes) - set(WORKSPACE_CONFIGURATION_FIELDS):
            raise ValueError("Unknown or empty workspace configuration update")
        with connect_state_db(self.db_path) as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                "SELECT workspace_id, git_remote_url, git_username, workspace_prompt, "
                "git_large_file_threshold FROM engineering_workspaces WHERE workspace_id = ?",
                (workspace_id,),
            ).fetchone()
            if row is None:
                raise LookupError("Workspace not found")
            before = _configuration_record(row)
            if before["revision"] != expected_revision:
                raise WorkspaceConfigurationConflict(
                    "Workspace settings changed; read them before saving"
                )
            # Column names come exclusively from the fixed allowlist above.
            assignments = ", ".join(f"{key} = ?" for key in changes)
            conn.execute(
                f"UPDATE engineering_workspaces SET {assignments}, updated_at = ? WHERE workspace_id = ?",
                (*changes.values(), int(time.time()), workspace_id),
            )
            result = _configuration_record({**dict(row), **changes})
        return result

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
