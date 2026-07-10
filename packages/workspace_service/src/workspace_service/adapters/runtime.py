"""Concrete local workspace runtime adapter implementation."""

import json
import os
import sqlite3
import subprocess
import tempfile
import structlog
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, Any, Optional

from workspace_service.workspace_path import WorkspacePath
from core.secrets import CredentialReference, default_secret_provider

logger = structlog.get_logger(__name__)

ACTIVE_GATEWAY_SESSION_SETTING = "active_gateway_session_id"
SYNTHETIC_SESSION_PREFIXES = ("api_", "wright-local-")


class _ClosingConnection(sqlite3.Connection):
    def __exit__(self, exc_type, exc_value, traceback):
        try:
            return super().__exit__(exc_type, exc_value, traceback)
        finally:
            self.close()


def sanitize_workspace_name(name: str) -> str:
    """Sanitize a workspace name to construct a safe directory name.

    Converts to lowercase, replaces non-alphanumeric (excluding hyphens/underscores)
    with hyphens, merges consecutive hyphens, and strips leading/trailing hyphens.
    """
    import re

    if not name:
        return ""
    # Lowercase
    clean = name.lower()
    # Replace non-alphanumeric and non-underscores/hyphens with a hyphen
    clean = re.sub(r"[^a-z0-9_-]", "-", clean)
    # Replace consecutive hyphens with a single hyphen
    clean = re.sub(r"-+", "-", clean)
    # Strip leading/trailing hyphens/underscores
    clean = clean.strip("-_")
    return clean


def _get_db_conn(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, factory=_ClosingConnection)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.row_factory = sqlite3.Row
    return conn


def _api_rel_path(abs_path: str, base_dir: str) -> str:
    return "/" + os.path.relpath(abs_path, base_dir).replace(os.sep, "/").strip("/")


def _is_within_path(path: str, parent: str) -> bool:
    try:
        return os.path.commonpath(
            [os.path.abspath(path), os.path.abspath(parent)]
        ) == os.path.abspath(parent)
    except ValueError:
        return False


def is_synthetic_session_workspace(row: Dict[str, Any]) -> bool:
    """Return True for fallback rows created from transient agent session IDs."""
    session_id = str(row.get("session_id") or "").strip()
    local_path = str(row.get("local_path") or "").rstrip("/\\")
    basename = os.path.basename(local_path)
    workspace_name = str(row.get("workspace_name") or "").strip()

    synthetic_id = session_id.startswith(
        SYNTHETIC_SESSION_PREFIXES
    ) or basename.startswith(SYNTHETIC_SESSION_PREFIXES)
    if not synthetic_id:
        return False

    display_name = workspace_name or basename
    return display_name in {session_id, basename}


def _visible_workspace_rows(rows: list[sqlite3.Row]) -> list[Dict[str, Any]]:
    return [
        row_dict
        for row in rows
        if not is_synthetic_session_workspace(row_dict := dict(row))
    ]


def _ensure_workspace_agent_sessions_table(conn: sqlite3.Connection) -> None:
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


def associate_workspace_session(
    db_path: str,
    workspace_id: str,
    session_id: str,
    *,
    agent_id: str = "hermes",
    title: Optional[str] = None,
    created_at: Optional[int] = None,
    updated_at: Optional[int] = None,
    reassign_if_owned: bool = False,
) -> None:
    import time

    if not workspace_id or not session_id:
        return
    now = int(time.time())
    created = int(created_at or now)
    updated = int(updated_at or created or now)
    with _get_db_conn(db_path) as conn:
        _ensure_workspace_agent_sessions_table(conn)
        if reassign_if_owned:
            conn.execute(
                "DELETE FROM workspace_agent_sessions WHERE session_id = ?",
                (session_id,),
            )
        else:
            conn.execute(
                """
                DELETE FROM workspace_agent_sessions
                WHERE session_id = ?
                  AND workspace_id NOT IN (
                    SELECT workspace_id FROM engineering_workspaces
                  )
                """,
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
        conn.commit()


def update_workspace_agent_session_title(
    db_path: str, session_id: str, title: str, *, agent_id: str = "hermes"
) -> bool:
    import time

    cleaned = (title or "").strip()
    if not session_id or not cleaned:
        return False

    now = int(time.time())
    with _get_db_conn(db_path) as conn:
        _ensure_workspace_agent_sessions_table(conn)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT workspace_id FROM workspace_agent_sessions WHERE session_id = ? AND is_archived = 0",
            (session_id,),
        )
        row = cursor.fetchone()
        workspace_id = row["workspace_id"] if row else None
        if not workspace_id:
            cursor.execute(
                "SELECT workspace_id FROM engineering_workspaces WHERE session_id = ?",
                (session_id,),
            )
            row = cursor.fetchone()
            workspace_id = row["workspace_id"] if row else None
        if not workspace_id:
            return False

        cursor.execute(
            "SELECT created_at FROM workspace_agent_sessions WHERE workspace_id = ? AND session_id = ?",
            (workspace_id, session_id),
        )
        existing = cursor.fetchone()
        created_at = int(existing["created_at"]) if existing else now
        conn.execute(
            """
            INSERT INTO workspace_agent_sessions (
                workspace_id, session_id, agent_id, title, created_at, updated_at, is_archived
            ) VALUES (?, ?, ?, ?, ?, ?, 0)
            ON CONFLICT(workspace_id, session_id) DO UPDATE SET
                agent_id = excluded.agent_id,
                title = excluded.title,
                updated_at = excluded.updated_at,
                is_archived = 0
            """,
            (workspace_id, session_id, agent_id, cleaned, created_at, now),
        )
        conn.commit()
        return True


def list_workspace_agent_sessions(
    db_path: str, workspace_id: str, *, include_archived: bool = False
) -> list[Dict[str, Any]]:
    with _get_db_conn(db_path) as conn:
        _ensure_workspace_agent_sessions_table(conn)
        cursor = conn.cursor()
        if include_archived:
            cursor.execute(
                """
                SELECT * FROM workspace_agent_sessions
                WHERE workspace_id = ?
                ORDER BY updated_at DESC, created_at DESC
                """,
                (workspace_id,),
            )
        else:
            cursor.execute(
                """
                SELECT * FROM workspace_agent_sessions
                WHERE workspace_id = ? AND is_archived = 0
                ORDER BY updated_at DESC, created_at DESC
                """,
                (workspace_id,),
            )
        return [dict(row) for row in cursor.fetchall()]


def get_workspace_by_session(db_path: str, session_id: str) -> Optional[Dict[str, Any]]:
    with _get_db_conn(db_path) as conn:
        _ensure_workspace_agent_sessions_table(conn)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM engineering_workspaces WHERE session_id = ?", (session_id,)
        )
        row = cursor.fetchone()
        if row:
            return dict(row)
        cursor.execute(
            """
            SELECT ew.*
            FROM engineering_workspaces ew
            JOIN workspace_agent_sessions was ON was.workspace_id = ew.workspace_id
            WHERE was.session_id = ? AND was.is_archived = 0
            """,
            (session_id,),
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def get_workspace(db_path: str, workspace_id: str) -> Optional[Dict[str, Any]]:
    with _get_db_conn(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM engineering_workspaces WHERE workspace_id = ?",
            (workspace_id,),
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def _ensure_system_settings_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS system_settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
        """
    )


def set_active_gateway_session(db_path: str, session_id: str) -> None:
    """Pin the Hermes-facing Wright gateway to the session currently in use."""
    if not session_id:
        return
    with _get_db_conn(db_path) as conn:
        _ensure_system_settings_table(conn)
        conn.execute(
            """
            INSERT OR REPLACE INTO system_settings (key, value)
            VALUES (?, ?)
            """,
            (ACTIVE_GATEWAY_SESSION_SETTING, session_id),
        )
        conn.commit()


def get_active_gateway_session(db_path: str) -> Optional[str]:
    try:
        with _get_db_conn(db_path) as conn:
            _ensure_system_settings_table(conn)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT value FROM system_settings WHERE key = ?",
                (ACTIVE_GATEWAY_SESSION_SETTING,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            session_id = str(row["value"]).strip()
            return session_id or None
    except Exception as e:
        logger.debug("failed_to_read_active_gateway_session", error=str(e))
        return None


def get_gateway_workspace(db_path: str) -> Optional[Dict[str, Any]]:
    """Return the workspace whose MCP tools should be visible through wrightgateway."""
    active_session_id = get_active_gateway_session(db_path)
    if active_session_id:
        workspace = get_workspace_by_session(db_path, active_session_id)
        if workspace:
            return workspace

    with _get_db_conn(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM engineering_workspaces ORDER BY updated_at DESC LIMIT 1"
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def create_workspace(
    db_path: str,
    workspace_id: str,
    session_id: str,
    local_path: str,
    workspace_name: Optional[str] = None,
    git_remote_url: Optional[str] = None,
    git_username: Optional[str] = None,
    git_token: Optional[str] = None,
) -> None:
    import time

    now = int(time.time())
    with _get_db_conn(db_path) as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO engineering_workspaces (
                workspace_id, session_id, workspace_name, local_path, git_remote_url, git_username, git_token, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                workspace_id,
                session_id,
                workspace_name,
                local_path,
                git_remote_url,
                git_username,
                None,
                now,
                now,
            ),
        )
        conn.commit()
    if git_token:
        default_secret_provider().set(
            CredentialReference("workspace", workspace_id, "GIT_TOKEN"), git_token
        )
    associate_workspace_session(
        db_path,
        workspace_id,
        session_id,
        title=workspace_name,
        created_at=now,
        updated_at=now,
        reassign_if_owned=True,
    )


def update_workspace_remote(
    db_path: str,
    session_id: str,
    git_remote_url: Optional[str],
    git_username: Optional[str],
    git_token: Optional[str],
) -> None:
    import time

    now = int(time.time())
    with _get_db_conn(db_path) as conn:
        row = conn.execute(
            "SELECT workspace_id FROM engineering_workspaces WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        conn.execute(
            """
            UPDATE engineering_workspaces
            SET git_remote_url = ?, git_username = ?, git_token = NULL, updated_at = ?
            WHERE session_id = ?
            """,
            (git_remote_url, git_username, now, session_id),
        )
        conn.commit()
    if row and git_token:
        default_secret_provider().set(
            CredentialReference("workspace", row[0], "GIT_TOKEN"), git_token
        )


def get_workspace_enabled_tools_by_workspace(
    db_path: str, workspace_id: str
) -> Optional[list[str]]:
    import json

    with _get_db_conn(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT enabled_tools FROM engineering_workspaces WHERE workspace_id = ?",
            (workspace_id,),
        )
        row = cursor.fetchone()
        if row and row["enabled_tools"] is not None:
            try:
                return json.loads(row["enabled_tools"])
            except Exception:
                pass
    return None


def get_workspace_enabled_tools(db_path: str, session_id: str) -> Optional[list[str]]:
    workspace = get_workspace_by_session(db_path, session_id)
    if workspace:
        enabled_tools = get_workspace_enabled_tools_by_workspace(
            db_path, workspace["workspace_id"]
        )
        if enabled_tools is not None:
            return enabled_tools

    # Fallback/Default behavior when enabled_tools is NULL or invalid JSON
    # Default to enabling all installed MCP servers, EXCEPT those that require
    # credentials which have not yet been configured, or those that are in error state.
    from tool_registry.db import get_servers
    from tool_registry.secrets import has_credentials
    from tool_registry.models import EnvVarDefinition

    try:
        installed = get_servers(db_path)
    except Exception:
        # Fallback if DB structure or tool_registry import fails in some environments
        return []

    enabled = []
    for s in installed:
        if not s.is_installed:
            continue
        if s.status == "error":
            continue

        # Check if the server requires credentials
        requires_creds = False
        if s.env_vars and isinstance(s.env_vars, list):
            required_vars = [
                v.name
                for v in s.env_vars
                if isinstance(v, EnvVarDefinition) and v.required
            ]
            if required_vars:
                requires_creds = True
                cred_status = has_credentials(s.server_id, required_vars)
                # Only enable by default if all required credentials are configured
                if all(cred_status.values()):
                    enabled.append(s.name)

        if not requires_creds:
            enabled.append(s.name)

    return enabled


def update_workspace_enabled_tools_by_workspace(
    db_path: str, workspace_id: str, enabled_tools: list[str]
) -> None:
    import time
    import json

    now = int(time.time())
    tools_str = json.dumps(enabled_tools)
    with _get_db_conn(db_path) as conn:
        conn.execute(
            """
            UPDATE engineering_workspaces
            SET enabled_tools = ?, updated_at = ?
            WHERE workspace_id = ?
            """,
            (tools_str, now, workspace_id),
        )
        conn.commit()


def update_workspace_enabled_tools(
    db_path: str, session_id: str, enabled_tools: list[str]
) -> None:
    workspace = get_workspace_by_session(db_path, session_id)
    if workspace:
        update_workspace_enabled_tools_by_workspace(
            db_path, workspace["workspace_id"], enabled_tools
        )
        return


def get_recent_workspaces(db_path: str, limit: int = 5) -> list[Dict[str, Any]]:
    with _get_db_conn(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM engineering_workspaces ORDER BY updated_at DESC LIMIT ?",
            (max(limit * 4, limit),),
        )
        return _visible_workspace_rows(cursor.fetchall())[:limit]


def get_all_workspaces(db_path: str) -> list[Dict[str, Any]]:
    with _get_db_conn(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM engineering_workspaces ORDER BY local_path ASC")
        return _visible_workspace_rows(cursor.fetchall())


def touch_workspace(db_path: str, session_id: str) -> None:
    import time

    now = int(time.time())
    workspace = get_workspace_by_session(db_path, session_id)
    with _get_db_conn(db_path) as conn:
        if workspace:
            conn.execute(
                """
                UPDATE engineering_workspaces
                SET updated_at = ?
                WHERE workspace_id = ?
                """,
                (now, workspace["workspace_id"]),
            )
            _ensure_workspace_agent_sessions_table(conn)
            conn.execute(
                """
                UPDATE workspace_agent_sessions
                SET updated_at = ?
                WHERE workspace_id = ? AND session_id = ?
                """,
                (now, workspace["workspace_id"], session_id),
            )
        else:
            conn.execute(
                """
                UPDATE engineering_workspaces
                SET updated_at = ?
                WHERE session_id = ?
                """,
                (now, session_id),
            )
        conn.commit()


def create_workspace_from_dashboard(
    db_path: str, name: str, local_path: str, session_id: Optional[str] = None
) -> Dict[str, Any]:
    """Create a workspace from the dashboard with a user-provided name and path.

    Validates that local_path exists on disk and is an absolute path.
    Returns the full workspace dict.
    """
    import time
    import uuid

    # Validate path is absolute
    if not os.path.isabs(local_path):
        raise ValueError("local_path must be an absolute path")
    # Validate path exists on disk
    if not os.path.isdir(local_path):
        raise ValueError(f"Directory does not exist: {local_path}")
    # Validate name length
    if not name or len(name.strip()) == 0:
        raise ValueError("Workspace name must not be empty")
    if len(name) > 100:
        raise ValueError("Workspace name must be 100 characters or fewer")

    workspace_id = str(uuid.uuid4())
    if not session_id:
        session_id = str(uuid.uuid4())
    now = int(time.time())

    with _get_db_conn(db_path) as conn:
        conn.execute(
            """
            INSERT INTO engineering_workspaces (
                workspace_id, session_id, workspace_name, local_path, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (workspace_id, session_id, name.strip(), local_path, now, now),
        )
        conn.commit()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM engineering_workspaces WHERE workspace_id = ?",
            (workspace_id,),
        )
        row = cursor.fetchone()
        result = dict(row) if row else {}
    if result:
        associate_workspace_session(
            db_path,
            workspace_id,
            session_id,
            title=name.strip(),
            created_at=now,
            updated_at=now,
            reassign_if_owned=True,
        )
    return result


def get_workspace_by_id(db_path: str, workspace_id: str) -> Optional[Dict[str, Any]]:
    """Fetch a single workspace by its workspace_id."""
    with _get_db_conn(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM engineering_workspaces WHERE workspace_id = ?",
            (workspace_id,),
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def get_workspace_by_path(db_path: str, local_path: str) -> Optional[Dict[str, Any]]:
    """Fetch a single workspace by its local_path."""
    with _get_db_conn(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM engineering_workspaces WHERE local_path = ?",
            (local_path,),
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def update_workspace_remote_by_id(
    db_path: str,
    workspace_id: str,
    git_remote_url: Optional[str],
    git_username: Optional[str],
    git_token: Optional[str],
    workspace_prompt: Optional[str] = None,
    git_large_file_threshold: Optional[int] = None,
) -> None:
    """Update workspace Git remote credentials using workspace_id."""
    import time

    now = int(time.time())
    with _get_db_conn(db_path) as conn:
        conn.execute(
            """
            UPDATE engineering_workspaces
            SET git_remote_url = ?, git_username = ?, git_token = NULL, workspace_prompt = ?, git_large_file_threshold = ?, updated_at = ?
            WHERE workspace_id = ?
            """,
            (
                git_remote_url,
                git_username,
                workspace_prompt,
                git_large_file_threshold,
                now,
                workspace_id,
            ),
        )
        conn.commit()
    if git_token:
        default_secret_provider().set(
            CredentialReference("workspace", workspace_id, "GIT_TOKEN"), git_token
        )


def get_workspace_git_token(workspace_id: str) -> Optional[str]:
    return default_secret_provider().get(
        CredentialReference("workspace", workspace_id, "GIT_TOKEN")
    )


def has_workspace_git_token(workspace_id: str) -> bool:
    return (
        default_secret_provider()
        .status(CredentialReference("workspace", workspace_id, "GIT_TOKEN"))
        .configured
    )


def update_workspace_session(db_path: str, workspace_id: str, session_id: str) -> None:
    """Set the default session pointer and associate the session with a workspace."""
    import time

    now = int(time.time())
    with _get_db_conn(db_path) as conn:
        conn.execute(
            """
            UPDATE engineering_workspaces
            SET session_id = ?, updated_at = ?
            WHERE workspace_id = ?
            """,
            (session_id, now, workspace_id),
        )
        conn.commit()
    associate_workspace_session(
        db_path, workspace_id, session_id, created_at=now, updated_at=now
    )


def save_agent_context(db_path: str, workspace_id: str, context_data: str) -> None:
    """Save agent conversation context for a workspace."""
    import time

    now = int(time.time())
    with _get_db_conn(db_path) as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO agent_contexts (workspace_id, context_data, updated_at)
            VALUES (?, ?, ?)
            """,
            (workspace_id, context_data, now),
        )
        conn.commit()


def load_agent_context(db_path: str, workspace_id: str) -> Optional[Dict[str, Any]]:
    """Load agent conversation context for a workspace."""
    with _get_db_conn(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM agent_contexts WHERE workspace_id = ?", (workspace_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None


async def sync_workspace_runners(db_path: str, session_id: str, mcp_engine) -> None:
    """Synchronize MCP runners based on workspace-scoped tool enablement.

    Starts enabled servers and stops disabled ones. Runs in background.
    Extracted from workspace router to keep route handlers thin.
    """
    import asyncio

    enabled_tools = get_workspace_enabled_tools(db_path, session_id)
    workspace = get_workspace_by_session(db_path, session_id)
    workspace_dir = workspace["local_path"] if workspace else None
    workspace_id = workspace["workspace_id"] if workspace else None

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM mcp_servers WHERE is_installed = 1")
        installed_servers = [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()

    async def sync_runners_background():
        for srv in installed_servers:
            srv_id = srv["server_id"]
            srv_name = srv["name"]

            is_enabled = True
            if enabled_tools is not None:
                is_enabled = (srv_name in enabled_tools) or (srv_id in enabled_tools)

            try:
                if is_enabled:
                    from tool_registry import ApprovalContext

                    approval_gates = srv.get("approval_gates") or []
                    if isinstance(approval_gates, str):
                        try:
                            approval_gates = json.loads(approval_gates)
                        except json.JSONDecodeError:
                            approval_gates = []
                    await mcp_engine.start_server(
                        srv_id,
                        workspace_dir=workspace_dir,
                        approval_context=ApprovalContext(
                            workspace_id=workspace_id,
                            workspace_approvals=set(approval_gates or []),
                        ),
                    )
                else:
                    await mcp_engine.stop_server(srv_id)
            except Exception as err:
                logger.error("mcp_runner_sync_failed", server=srv_name, error=str(err))

    asyncio.create_task(sync_runners_background())


class MergeConflictError(Exception):
    """Exception raised when a git pull results in merge conflicts."""

    def __init__(self, conflicted_files: list[str]):
        super().__init__("Pull resulted in merge conflicts")
        self.conflicted_files = conflicted_files


class WorkspaceManager:
    """Manages workspace file browser directory tree construction and raw file reads."""

    def __init__(self, base_dir: str):
        self.base_dir = os.path.abspath(base_dir)
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir, exist_ok=True)

        # Initialize Git repository if not already present
        git_dir = os.path.join(self.base_dir, ".git")
        if not os.path.exists(git_dir):
            try:
                subprocess.run(
                    ["git", "init"], cwd=self.base_dir, capture_output=True, check=True
                )
                logger.info(
                    "Initialized local Git repository in workspace %s", self.base_dir
                )
            except Exception as e:
                logger.error(
                    "Failed to initialize Git repository in workspace %s: %s",
                    self.base_dir,
                    e,
                )

        # Auto-generate .gitignore if not present
        gitignore_path = os.path.join(self.base_dir, ".gitignore")
        if not os.path.exists(gitignore_path):
            try:
                with open(gitignore_path, "w") as f:
                    f.write("# Auto-generated .gitignore for Engineering Workspace\n")
                    f.write("*.log\n")
                    f.write("*.tmp\n")
                    f.write("tmp/\n")
                    f.write("/tmp/\n")
                logger.info("Created default .gitignore in %s", gitignore_path)
            except Exception as e:
                logger.error("Failed to create .gitignore in %s: %s", gitignore_path, e)

    def _get_lock_path(self, rel_path: str) -> str:
        import hashlib

        rel_clean = rel_path.strip("/")
        hash_val = hashlib.sha256(rel_clean.encode()).hexdigest()
        locks_dir = os.path.join(self.base_dir, ".git", "workspace_locks")
        os.makedirs(locks_dir, exist_ok=True)
        return os.path.join(locks_dir, hash_val)

    def lock_file(self, rel_path: str) -> None:
        """Lock a file to prevent renaming or deletion."""
        lock_file_path = self._get_lock_path(rel_path)
        with open(lock_file_path, "w") as f:
            f.write("locked")

    def unlock_file(self, rel_path: str) -> None:
        """Unlock a file."""
        lock_file_path = self._get_lock_path(rel_path)
        if os.path.exists(lock_file_path):
            try:
                os.remove(lock_file_path)
            except Exception:
                pass

    def is_file_locked(self, rel_path: str) -> bool:
        """Check if a file or directory (or any file inside it) is locked."""
        lock_file_path = self._get_lock_path(rel_path)
        if os.path.exists(lock_file_path):
            return True

        locks_dir = os.path.join(self.base_dir, ".git", "workspace_locks")
        if os.path.exists(locks_dir):
            try:
                abs_path = self.sanitize_path(rel_path)
                if os.path.isdir(abs_path):
                    for root, _, files in os.walk(abs_path):
                        for file in files:
                            child_abs = os.path.join(root, file)
                            child_rel = _api_rel_path(child_abs, self.base_dir)
                            child_lock = self._get_lock_path(child_rel)
                            if os.path.exists(child_lock):
                                return True
            except Exception:
                pass
        return False

    def sanitize_path(self, relative_path: str) -> str:
        """Resolve a user path inside this workspace without following links."""
        capability = WorkspacePath(self.base_dir)
        normalized = relative_path.replace("\\", "/")
        if normalized == "/tmp" or normalized.startswith("/tmp/"):
            raise ValueError("Access denied: global temporary paths are not allowed")
        # The legacy HTTP contract represents workspace-relative paths with one
        # leading slash. Strip only that marker; UNC/double-slash stays invalid.
        if normalized.startswith("/") and not normalized.startswith("//"):
            normalized = normalized[1:]
        if normalized.startswith("tmp/"):
            return str(capability.scratch(normalized.removeprefix("tmp/")))
        return str(capability.resolve(normalized))

    def write_backup(self, rel_path: str, content: bytes) -> str:
        """Write temporary backup file for unsaved edits under .git/backups/."""
        import hashlib

        hash_val = hashlib.sha256(rel_path.encode()).hexdigest()
        backups_dir = os.path.join(self.base_dir, ".git", "backups")
        os.makedirs(backups_dir, exist_ok=True)
        backup_path = os.path.join(backups_dir, hash_val)
        with open(backup_path, "wb") as f:
            f.write(content)
        return hash_val

    def delete_backup(self, backup_id: str) -> None:
        """Delete temporary backup file."""
        backup_path = str(WorkspacePath(self.base_dir).backup(backup_id))
        if os.path.exists(backup_path):
            try:
                os.remove(backup_path)
            except Exception:
                pass

    def _get_git_statuses(self) -> Dict[str, str]:
        """Run git status --porcelain and return a mapping of workspace-relative paths to status characters."""
        statuses = {}
        try:
            res = subprocess.run(
                ["git", "status", "--porcelain", "-uall"],
                cwd=self.base_dir,
                capture_output=True,
                text=True,
                check=True,
            )
            for line in res.stdout.splitlines():
                if len(line) < 4:
                    continue
                xy = line[:2]
                path = line[3:].strip('"')
                rel_path = "/" + path.strip("/")

                if xy == "??":
                    status = "U"
                elif "A" in xy:
                    status = "A"
                elif "D" in xy:
                    status = "D"
                elif "M" in xy:
                    status = "M"
                else:
                    status = "Clean"

                statuses[rel_path] = status
        except Exception as e:
            logger.debug("Failed to fetch git status: %s", e)
        return statuses

    def get_workspace_tree(self) -> Dict[str, Any]:
        """Build the complete hierarchical file tree for the base_dir decorated with git status."""
        if not os.path.exists(self.base_dir):
            # Create if it doesn't exist (e.g. initial start)
            os.makedirs(self.base_dir, exist_ok=True)
        statuses = self._get_git_statuses()
        return self._build_node(self.base_dir, statuses)

    def _build_node(self, abs_path: str, statuses: Dict[str, str]) -> Dict[str, Any]:
        name = os.path.basename(abs_path)
        if not name:
            name = os.path.basename(self.base_dir)

        # Build clean project-relative slash prefix paths (e.g., /designs/gearbox.stl)
        if abs_path == self.base_dir:
            rel_path = "/"
        else:
            rel_path = _api_rel_path(abs_path, self.base_dir)

        path_stat = os.lstat(abs_path)
        if os.path.islink(abs_path) or bool(
            getattr(path_stat, "st_file_attributes", 0) & 0x400
        ):
            raise ValueError("Workspace tree contains a symbolic link or reparse point")
        last_modified = int(path_stat.st_mtime)

        git_status = statuses.get(rel_path, "Clean")

        if os.path.isdir(abs_path):
            children = []
            try:
                for entry in sorted(os.listdir(abs_path)):
                    # Skip hidden files and special ignored directories
                    if entry.startswith(".") or entry == "freecad_mcp_work":
                        continue
                    child_abs = os.path.join(abs_path, entry)
                    children.append(self._build_node(child_abs, statuses))
            except Exception:
                pass
            return {
                "name": name,
                "path": rel_path,
                "type": "directory",
                "size": None,
                "last_modified": last_modified,
                "git_status": git_status,
                "children": children,
            }
        else:
            return {
                "name": name,
                "path": rel_path,
                "type": "file",
                "size": path_stat.st_size,
                "last_modified": last_modified,
                "git_status": git_status,
                "children": None,
            }

    def read_file_content(self, rel_path: str) -> bytes:
        """Read and return binary content of a file."""
        abs_path = self.sanitize_path(rel_path)
        if not os.path.isfile(abs_path):
            raise FileNotFoundError(f"File not found: {rel_path}")
        with open(abs_path, "rb") as f:
            return f.read()

    def write_file_content(self, rel_path: str, content: bytes) -> None:
        """Write content back to a file, validating paths for safety."""
        if self.is_file_locked(rel_path):
            raise PermissionError(
                f"Cannot edit: file '{rel_path}' is locked by an active process."
            )
        abs_path = self.sanitize_path(rel_path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "wb") as f:
            f.write(content)

    def create_file_node(self, rel_path: str, node_type: str) -> Dict[str, Any]:
        """Create a new file or directory on disk and return its node metadata."""
        abs_path = self.sanitize_path(rel_path)
        if os.path.exists(abs_path):
            raise FileExistsError(f"Path already exists: {rel_path}")

        if node_type == "directory":
            os.makedirs(abs_path, exist_ok=True)
        elif node_type == "file":
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            with open(abs_path, "w") as f:
                f.write("")
        else:
            raise ValueError(f"Invalid node type: {node_type}")

        stat = os.stat(abs_path)
        last_modified = int(stat.st_mtime)
        name = os.path.basename(abs_path)
        statuses = self._get_git_statuses()
        clean_rel = _api_rel_path(abs_path, self.base_dir)

        return {
            "name": name,
            "path": clean_rel,
            "type": node_type,
            "size": stat.st_size if node_type == "file" else None,
            "last_modified": last_modified,
            "git_status": statuses.get(
                clean_rel, "U" if node_type == "file" else "Clean"
            ),
            "children": [] if node_type == "directory" else None,
        }

    def delete_file_node(self, rel_path: str) -> None:
        """Safely delete a file or directory from the workspace filesystem."""
        if self.is_file_locked(rel_path):
            raise PermissionError(
                f"Cannot delete: file or folder '{rel_path}' is locked by an active process."
            )

        abs_path = self.sanitize_path(rel_path)
        if not os.path.exists(abs_path):
            raise FileNotFoundError(f"Path not found: {rel_path}")

        if os.path.isdir(abs_path):
            import shutil

            shutil.rmtree(abs_path)
        else:
            os.remove(abs_path)

    def move_file_node(self, src_rel_path: str, dest_rel_path: str) -> None:
        """Move or rename a file/folder in the workspace filesystem."""
        if self.is_file_locked(src_rel_path):
            raise PermissionError(
                f"Cannot move/rename: source '{src_rel_path}' is locked by an active process."
            )

        src_abs = self.sanitize_path(src_rel_path)
        dest_abs = self.sanitize_path(dest_rel_path)

        if not os.path.exists(src_abs):
            raise FileNotFoundError(f"Source path not found: {src_rel_path}")
        if os.path.exists(dest_abs):
            raise FileExistsError(f"Destination path already exists: {dest_rel_path}")

        os.makedirs(os.path.dirname(dest_abs), exist_ok=True)
        import shutil

        shutil.move(src_abs, dest_abs)

    def get_git_status(self) -> Dict[str, Any]:
        """Retrieve branch name, clean status, and changed items array from the local Git repo."""
        branch_name = "main"
        try:
            res_branch = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=self.base_dir,
                capture_output=True,
                text=True,
                check=True,
            )
            branch_name = res_branch.stdout.strip() or "main"
        except Exception:
            pass

        changes = []
        try:
            res = subprocess.run(
                ["git", "status", "--porcelain", "-uall"],
                cwd=self.base_dir,
                capture_output=True,
                text=True,
                check=True,
            )
            for line in res.stdout.splitlines():
                if len(line) < 4:
                    continue
                xy = line[:2]
                path = line[3:].strip('"')
                rel_path = "/" + path.strip("/")

                x, y = xy[0], xy[1]
                staged = x != " " and x != "?"

                if xy == "??":
                    status_code = "U"
                elif x == "A" or y == "A":
                    status_code = "A"
                elif x == "D" or y == "D":
                    status_code = "D"
                elif x == "M" or y == "M":
                    status_code = "M"
                else:
                    status_code = "M"

                changes.append(
                    {"path": rel_path, "git_status": status_code, "staged": staged}
                )
        except Exception as e:
            logger.error("Failed to run git status: %s", e)

        is_clean = len(changes) == 0
        return {"branch_name": branch_name, "is_clean": is_clean, "changes": changes}

    def get_git_diff(self, rel_path: str) -> str:
        """Return the unified git diff of a file (handles untracked files)."""
        abs_path = self.sanitize_path(rel_path)
        is_untracked = False
        try:
            res_status = subprocess.run(
                ["git", "status", "--porcelain", abs_path],
                cwd=self.base_dir,
                capture_output=True,
                text=True,
            )
            if res_status.stdout.startswith("??"):
                is_untracked = True
        except Exception:
            pass

        if is_untracked:
            try:
                res = subprocess.run(
                    ["git", "diff", "--no-color", "--no-index", "/dev/null", abs_path],
                    cwd=self.base_dir,
                    capture_output=True,
                    text=True,
                )
                return res.stdout
            except Exception as e:
                return f"Error diffing untracked file: {e}"
        else:
            try:
                res = subprocess.run(
                    ["git", "diff", "HEAD", "--no-color", "--", abs_path],
                    cwd=self.base_dir,
                    capture_output=True,
                    text=True,
                )
                return res.stdout
            except Exception as e:
                return f"Error diffing file: {e}"

    def revert_file(self, rel_path: str) -> None:
        """Revert a file back to HEAD state or delete if untracked."""
        abs_path = self.sanitize_path(rel_path)
        is_untracked = False
        try:
            res_status = subprocess.run(
                ["git", "status", "--porcelain", abs_path],
                cwd=self.base_dir,
                capture_output=True,
                text=True,
            )
            if res_status.stdout.startswith("??"):
                is_untracked = True
        except Exception:
            pass

        if is_untracked:
            if os.path.isdir(abs_path):
                import shutil

                shutil.rmtree(abs_path)
            elif os.path.exists(abs_path):
                os.remove(abs_path)
        else:
            try:
                subprocess.run(
                    ["git", "reset", "HEAD", "--", abs_path],
                    cwd=self.base_dir,
                    capture_output=True,
                )
                subprocess.run(
                    ["git", "checkout", "HEAD", "--", abs_path],
                    cwd=self.base_dir,
                    capture_output=True,
                    check=True,
                )
            except Exception as e:
                logger.error("Failed to revert file %s: %s", rel_path, e)
                raise RuntimeError(f"Failed to revert file: {e}")

    def commit_changes(self, message: str) -> Dict[str, Any]:
        """Stage all workspace changes and commit locally."""
        import time

        status_info = self.get_git_status()
        if status_info["is_clean"]:
            raise ValueError("No changes to commit.")

        try:
            subprocess.run(
                ["git", "add", "-A"], cwd=self.base_dir, capture_output=True, check=True
            )
            subprocess.run(
                ["git", "commit", "-m", message],
                cwd=self.base_dir,
                capture_output=True,
                check=True,
            )
            res_hash = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.base_dir,
                capture_output=True,
                text=True,
                check=True,
            )
            commit_hash = res_hash.stdout.strip()

            return {
                "commit_hash": commit_hash,
                "message": message,
                "timestamp": int(time.time()),
            }
        except Exception as e:
            logger.error("Failed to commit changes: %s", e)
            raise RuntimeError(f"Failed to commit changes: {e}")

    def get_git_history(self, limit: int = 50) -> list[Dict[str, Any]]:
        """Return the linear commit history log."""
        commits = []
        try:
            res = subprocess.run(
                ["git", "log", f"-n{limit}", "--pretty=format:%H|%s|%an|%ct"],
                cwd=self.base_dir,
                capture_output=True,
                text=True,
                check=True,
            )
            for line in res.stdout.splitlines():
                parts = line.split("|", 3)
                if len(parts) < 4:
                    continue
                commits.append(
                    {
                        "commit_hash": parts[0],
                        "message": parts[1],
                        "author": parts[2],
                        "timestamp": int(parts[3]),
                    }
                )
        except Exception as e:
            logger.debug("Failed to fetch git history: %s", e)
        return commits

    @contextmanager
    def _git_credential_environment(
        self, username: Optional[str], token: Optional[str]
    ):
        environment = os.environ.copy()
        if not username or not token:
            yield environment
            return

        with tempfile.TemporaryDirectory(prefix="wright-git-askpass-") as directory:
            if os.name == "nt":
                helper = Path(directory) / "askpass.cmd"
                helper.write_text(
                    "@echo off\r\n"
                    'echo %~1 | findstr /I "username" >nul\r\n'
                    "if %errorlevel%==0 (echo %WRIGHT_GIT_USERNAME%) else (echo %WRIGHT_GIT_TOKEN%)\r\n",
                    encoding="utf-8",
                )
            else:
                helper = Path(directory) / "askpass.sh"
                helper.write_text(
                    "#!/bin/sh\n"
                    'case "$1" in *[Uu]sername*) printf "%s\\n" "$WRIGHT_GIT_USERNAME" ;; '
                    '*) printf "%s\\n" "$WRIGHT_GIT_TOKEN" ;; esac\n',
                    encoding="utf-8",
                )
                helper.chmod(0o700)
            environment.update(
                {
                    "GIT_ASKPASS": str(helper),
                    "GIT_TERMINAL_PROMPT": "0",
                    "WRIGHT_GIT_USERNAME": username,
                    "WRIGHT_GIT_TOKEN": token,
                }
            )
            yield environment

    def push_remote(
        self,
        remote_url: str,
        username: Optional[str] = None,
        token: Optional[str] = None,
    ) -> None:
        """Push local commits to the configured remote repository."""
        if not remote_url:
            raise ValueError("Git remote URL is not configured.")

        branch_name = self.get_git_status()["branch_name"]
        try:
            with self._git_credential_environment(username, token) as environment:
                subprocess.run(
                    ["git", "push", remote_url, branch_name],
                    cwd=self.base_dir,
                    capture_output=True,
                    text=True,
                    check=True,
                    env=environment,
                )
        except subprocess.CalledProcessError as e:
            from core.redaction import redact_text

            detail = redact_text(e.stderr.strip() or str(e), [token] if token else [])
            logger.error("git_push_failed", error=detail)
            raise RuntimeError(f"Failed to push changes: {detail}")

    def pull_remote(
        self,
        remote_url: str,
        username: Optional[str] = None,
        token: Optional[str] = None,
    ) -> None:
        """Pull commits from the configured remote repository."""
        if not remote_url:
            raise ValueError("Git remote URL is not configured.")

        branch_name = self.get_git_status()["branch_name"]
        try:
            with self._git_credential_environment(username, token) as environment:
                subprocess.run(
                    ["git", "pull", "--no-rebase", remote_url, branch_name],
                    cwd=self.base_dir,
                    capture_output=True,
                    text=True,
                    check=True,
                    env=environment,
                )
        except subprocess.CalledProcessError as e:
            # Check for merge conflicts
            conflicted_files = []
            try:
                res = subprocess.run(
                    ["git", "status", "--porcelain"],
                    cwd=self.base_dir,
                    capture_output=True,
                    text=True,
                )
                for line in res.stdout.splitlines():
                    if len(line) >= 4:
                        xy = line[:2]
                        if "U" in xy or xy in ("DD", "AA"):
                            path = line[3:].strip('"')
                            conflicted_files.append("/" + path.strip("/"))
            except Exception:
                pass

            if conflicted_files:
                raise MergeConflictError(conflicted_files)

            from core.redaction import redact_text

            detail = redact_text(e.stderr.strip() or str(e), [token] if token else [])
            logger.error("git_pull_failed", error=detail)
            raise RuntimeError(f"Failed to pull changes: {detail}")


def compile_workspace_mcp_instructions(db_path: str, local_path: str) -> Optional[str]:
    """Compile instructions of enabled MCP servers for a given workspace path."""
    import os
    import json
    import sqlite3

    if not os.path.exists(db_path):
        return None

    enabled_tools = None
    workspace_exists = False
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT enabled_tools FROM engineering_workspaces WHERE local_path = ?",
            (local_path,),
        )
        row = cursor.fetchone()
        if row:
            workspace_exists = True
            if row["enabled_tools"]:
                try:
                    enabled_tools = json.loads(row["enabled_tools"])
                except Exception:
                    pass
    except Exception:
        pass
    finally:
        conn.close()

    if not workspace_exists:
        return None

    installed_servers = []
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.cursor()
        # Ensure we have instructions column
        cursor.execute("PRAGMA table_info(mcp_servers)")
        columns = [col[1] for col in cursor.fetchall()]
        if "instructions" in columns:
            cursor.execute(
                "SELECT name, server_id, instructions FROM mcp_servers WHERE is_installed = 1"
            )
            installed_servers = [dict(row) for row in cursor.fetchall()]
    except Exception:
        pass
    finally:
        conn.close()

    active_instructions = []
    for srv in installed_servers:
        is_enabled = True
        if enabled_tools is not None:
            is_enabled = (srv["name"] in enabled_tools) or (
                srv["server_id"] in enabled_tools
            )
        if is_enabled and srv.get("instructions"):
            active_instructions.append(
                f"## {srv['name']} Instructions\n{srv['instructions']}"
            )

    global_rules = (
        "## Global Workspace Rules\n"
        f"1. **Workspace Path**: The absolute path to the current project workspace is `{local_path}`. All files and assets generated or modified during this session must reside directly within this folder or its subdirectories.\n"
        "2. **Excluding System Temp/Hidden Paths**: Never write or export final requested outputs to system temporary directories (such as `/tmp/`, `/var/tmp/`, etc.).\n"
        "3. **Explicit MCP Target Arguments**: When calling MCP tools (such as OpenSCAD, FreeCAD, CalculiX, etc.) to create models, save files, run simulations, or export files (e.g., STL, 3MF, PNG, etc.), you must explicitly specify target directory and output path parameters (e.g. `workspace`, `output_path`, `path`, `directory`, `cwd`) pointing to this active workspace or a subfolder inside it (e.g. `./`), instead of relying on the tools' default parameters which often fall back to temporary system directories.\n\n"
    )

    return (
        "Here are the instructions on how to use the loaded MCP tools within the Wright platform:\n\n"
        + global_rules
        + ("\n\n".join(active_instructions) if active_instructions else "")
    )


def write_workspace_agent_context(
    db_path: str, local_path: str, context_filename: str
) -> None:
    """Compile workspace MCP instructions and write them to an agent context file.

    If the context file already exists, preserves user's custom instructions outside of
    the Wright MCP instructions and Workspace Context blocks.
    """
    import os
    import re

    if not os.path.exists(local_path) or not context_filename:
        return

    instructions = compile_workspace_mcp_instructions(db_path, local_path)
    context_path = os.path.join(local_path, context_filename)

    start_marker = "<!-- WRIGHT MCP INSTRUCTIONS START -->"
    end_marker = "<!-- WRIGHT MCP INSTRUCTIONS END -->"

    generated_block = ""
    if instructions:
        generated_block = f"{start_marker}\n{instructions}\n{end_marker}"
    else:
        # If there are no instructions, clear the block
        generated_block = f"{start_marker}\n{end_marker}"

    # Retrieve workspace context prompt
    workspace = get_workspace_by_path(db_path, local_path)
    workspace_prompt = workspace.get("workspace_prompt") if workspace else None

    start_prompt_marker = "<!-- WRIGHT WORKSPACE PROMPT START -->"
    end_prompt_marker = "<!-- WRIGHT WORKSPACE PROMPT END -->"

    generated_prompt_block = ""
    if workspace_prompt:
        generated_prompt_block = f"{start_prompt_marker}\n## Workspace Context Prompt\n\n{workspace_prompt}\n{end_prompt_marker}"
    else:
        generated_prompt_block = f"{start_prompt_marker}\n{end_prompt_marker}"

    existing_content = ""
    if os.path.exists(context_path):
        try:
            with open(context_path, "r", encoding="utf-8") as f:
                existing_content = f.read()
        except Exception:
            pass

    # 1. Update MCP instructions block
    if start_marker in existing_content and end_marker in existing_content:
        # Replace the existing block
        pattern = re.compile(
            rf"{re.escape(start_marker)}.*?{re.escape(end_marker)}", re.DOTALL
        )
        new_content = pattern.sub(lambda _: generated_block, existing_content)
    elif start_marker in existing_content or end_marker in existing_content:
        # Markers are mismatched or incomplete, append to the end
        new_content = existing_content.rstrip() + "\n\n" + generated_block
    else:
        # Markers not found
        if existing_content.strip():
            new_content = existing_content.rstrip() + "\n\n" + generated_block
        else:
            new_content = generated_block

    # 2. Update Workspace Context Prompt block
    if start_prompt_marker in new_content and end_prompt_marker in new_content:
        # Replace the existing block
        pattern = re.compile(
            rf"{re.escape(start_prompt_marker)}.*?{re.escape(end_prompt_marker)}",
            re.DOTALL,
        )
        new_content = pattern.sub(lambda _: generated_prompt_block, new_content)
    elif start_prompt_marker in new_content or end_prompt_marker in new_content:
        new_content = new_content.rstrip() + "\n\n" + generated_prompt_block
    else:
        if new_content.strip():
            new_content = new_content.rstrip() + "\n\n" + generated_prompt_block
        else:
            new_content = generated_prompt_block

    try:
        with open(context_path, "w", encoding="utf-8") as f:
            f.write(new_content.strip() + "\n")
    except Exception as e:
        logger.error(
            "Failed to write workspace agent context %s: %s", context_filename, e
        )


def read_application_logs(
    workspace_id: Optional[str] = None,
    level: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> dict:
    """Read and parse application logs from apps/api/wright.log."""
    import os
    import json

    _lib_dir = os.path.dirname(os.path.abspath(__file__))
    _repo_root = os.path.abspath(os.path.join(_lib_dir, "..", "..", "..", ".."))
    log_path = os.path.join(_repo_root, "apps", "api", "wright.log")

    if not os.path.exists(log_path):
        return {"logs": [], "total": 0}

    parsed_logs = []

    try:
        with open(log_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)

                    # Filter by level (case insensitive)
                    if level:
                        entry_level = entry.get("level", "").lower()
                        if entry_level != level.lower():
                            continue

                    # Filter by workspace_id
                    if workspace_id:
                        ws_id_val = (
                            entry.get("workspace_id")
                            or entry.get("extra", {}).get("workspaceId")
                            or entry.get("workspaceId")
                        )
                        if ws_id_val != workspace_id:
                            continue

                    # Filter by search string
                    if search:
                        search_lower = search.lower()
                        message = entry.get("message", "").lower()
                        event = entry.get("event", "").lower()
                        if search_lower not in message and search_lower not in event:
                            # Check keys and values in entry
                            found = False
                            for k, v in entry.items():
                                if k != "timestamp" and search_lower in str(v).lower():
                                    found = True
                                    break
                            if not found:
                                continue

                    # Normalize structlog keys to expected schema
                    if "message" not in entry and "event" in entry:
                        entry["message"] = entry["event"]
                    if "logger" not in entry and "logger_name" in entry:
                        entry["logger"] = entry["logger_name"]
                    elif "logger" not in entry:
                        entry["logger"] = "unknown"
                    if "timestamp" not in entry and "time" in entry:
                        entry["timestamp"] = entry["time"]

                    parsed_logs.append(entry)
                except Exception:
                    continue
    except Exception as e:
        logger.error("Failed to read log file: %s", e)
        return {"logs": [], "total": 0}

    # Reverse logs to get newest first
    parsed_logs.reverse()

    total = len(parsed_logs)
    paginated = parsed_logs[offset : offset + limit]

    return {"logs": paginated, "total": total}
