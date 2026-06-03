import os
import sqlite3
import subprocess
import structlog
from typing import Dict, Any, Optional

logger = structlog.get_logger(__name__)

def _get_db_conn(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.row_factory = sqlite3.Row
    return conn

def get_workspace_by_session(db_path: str, session_id: str) -> Optional[Dict[str, Any]]:
    with _get_db_conn(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM engineering_workspaces WHERE session_id = ?", (session_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def get_workspace(db_path: str, workspace_id: str) -> Optional[Dict[str, Any]]:
    with _get_db_conn(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM engineering_workspaces WHERE workspace_id = ?", (workspace_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def create_workspace(db_path: str, workspace_id: str, session_id: str, local_path: str, git_remote_url: Optional[str] = None, git_username: Optional[str] = None, git_token: Optional[str] = None) -> None:
    import time
    now = int(time.time())
    with _get_db_conn(db_path) as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO engineering_workspaces (
                workspace_id, session_id, local_path, git_remote_url, git_username, git_token, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (workspace_id, session_id, local_path, git_remote_url, git_username, git_token, now, now)
        )
        conn.commit()

def update_workspace_remote(db_path: str, session_id: str, git_remote_url: Optional[str], git_username: Optional[str], git_token: Optional[str]) -> None:
    import time
    now = int(time.time())
    with _get_db_conn(db_path) as conn:
        conn.execute(
            """
            UPDATE engineering_workspaces
            SET git_remote_url = ?, git_username = ?, git_token = ?, updated_at = ?
            WHERE session_id = ?
            """,
            (git_remote_url, git_username, git_token, now, session_id)
        )
        conn.commit()

def get_workspace_enabled_tools(db_path: str, session_id: str) -> Optional[list[str]]:
    import json
    with _get_db_conn(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT enabled_tools FROM engineering_workspaces WHERE session_id = ?", (session_id,))
        row = cursor.fetchone()
        if row and row["enabled_tools"]:
            try:
                return json.loads(row["enabled_tools"])
            except Exception:
                return None
        return None

def update_workspace_enabled_tools(db_path: str, session_id: str, enabled_tools: list[str]) -> None:
    import time
    import json
    now = int(time.time())
    tools_str = json.dumps(enabled_tools)
    with _get_db_conn(db_path) as conn:
        conn.execute(
            """
            UPDATE engineering_workspaces
            SET enabled_tools = ?, updated_at = ?
            WHERE session_id = ?
            """,
            (tools_str, now, session_id)
        )
        conn.commit()

def get_recent_workspaces(db_path: str, limit: int = 5) -> list[Dict[str, Any]]:
    with _get_db_conn(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM engineering_workspaces ORDER BY updated_at DESC LIMIT ?",
            (limit,)
        )
        return [dict(row) for row in cursor.fetchall()]

def get_all_workspaces(db_path: str) -> list[Dict[str, Any]]:
    with _get_db_conn(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM engineering_workspaces ORDER BY local_path ASC")
        return [dict(row) for row in cursor.fetchall()]

def touch_workspace(db_path: str, session_id: str) -> None:
    import time
    now = int(time.time())
    with _get_db_conn(db_path) as conn:
        conn.execute(
            """
            UPDATE engineering_workspaces
            SET updated_at = ?
            WHERE session_id = ?
            """,
            (now, session_id)
        )
        conn.commit()

def create_workspace_from_dashboard(db_path: str, name: str, local_path: str, session_id: Optional[str] = None) -> Dict[str, Any]:
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
            (workspace_id, session_id, name.strip(), local_path, now, now)
        )
        conn.commit()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM engineering_workspaces WHERE workspace_id = ?", (workspace_id,))
        row = cursor.fetchone()
        return dict(row) if row else {}

def get_workspace_by_id(db_path: str, workspace_id: str) -> Optional[Dict[str, Any]]:
    """Fetch a single workspace by its workspace_id."""
    with _get_db_conn(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM engineering_workspaces WHERE workspace_id = ?", (workspace_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

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
            (workspace_id, context_data, now)
        )
        conn.commit()

def load_agent_context(db_path: str, workspace_id: str) -> Optional[Dict[str, Any]]:
    """Load agent conversation context for a workspace."""
    with _get_db_conn(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM agent_contexts WHERE workspace_id = ?", (workspace_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


async def activate_workspace(
    db_path: str,
    session_id: str,
    local_path: str,
    engine,
) -> str:
    """Activate a workspace: verify/create agent session, update session_id if needed.

    Extracted from workspace router to keep route handlers thin.
    Returns the (possibly updated) session_id.
    """
    import time

    try:
        sessions = await engine.list_sessions()
        session_ids = {s.session_id for s in sessions}
        if session_id not in session_ids:
            logger.info("agent_session_missing", session_id=session_id, local_path=local_path)
            session_info = await engine.create_session(local_path)
            conn = sqlite3.connect(db_path)
            try:
                conn.execute(
                    "UPDATE engineering_workspaces SET session_id = ?, updated_at = ? WHERE session_id = ?",
                    (session_info.session_id, int(time.time()), session_id)
                )
                conn.commit()
                logger.info("workspace_session_updated", old_session_id=session_id, new_session_id=session_info.session_id)
                session_id = session_info.session_id
            finally:
                conn.close()
    except Exception as e:
        logger.warning("agent_session_verify_failed", session_id=session_id, error=str(e))

    touch_workspace(db_path, session_id)
    return session_id


async def sync_workspace_runners(db_path: str, session_id: str, mcp_engine) -> None:
    """Synchronize MCP runners based on workspace-scoped tool enablement.

    Starts enabled servers and stops disabled ones. Runs in background.
    Extracted from workspace router to keep route handlers thin.
    """
    import asyncio

    enabled_tools = get_workspace_enabled_tools(db_path, session_id)

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
                    await mcp_engine.start_server(srv_id)
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
                subprocess.run(["git", "init"], cwd=self.base_dir, capture_output=True, check=True)
                logger.info("Initialized local Git repository in workspace %s", self.base_dir)
            except Exception as e:
                logger.error("Failed to initialize Git repository in workspace %s: %s", self.base_dir, e)

        # Auto-generate .gitignore if not present
        gitignore_path = os.path.join(self.base_dir, ".gitignore")
        if not os.path.exists(gitignore_path):
            try:
                with open(gitignore_path, "w") as f:
                    f.write("# Auto-generated .gitignore for Engineering Workspace\n")
                    f.write("*.log\n")
                    f.write("*.tmp\n")
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
                            child_rel = "/" + os.path.relpath(child_abs, self.base_dir).strip("/")
                            child_lock = self._get_lock_path(child_rel)
                            if os.path.exists(child_lock):
                                return True
            except Exception:
                pass
        return False

    def sanitize_path(self, relative_path: str) -> str:
        """Sanitize relative path and resolve to absolute path under base_dir or allow /tmp/ to prevent path traversal."""
        # Support paths inside /tmp/ (e.g. for geometry/exports scratchpads)
        if relative_path.startswith("/tmp/") or relative_path.startswith("tmp/"):
            if relative_path.startswith("tmp/"):
                resolved = os.path.abspath("/" + relative_path)
            else:
                resolved = os.path.abspath(relative_path)
            if resolved.startswith("/tmp/"):
                return resolved
            else:
                raise ValueError("Access denied: path traversal attempt detected.")

        # Clean relative_path of leading/trailing slashes
        clean_rel = relative_path.strip("/")
        # Resolve path
        resolved = os.path.abspath(os.path.join(self.base_dir, clean_rel))
        # Ensure it's under base_dir
        if not resolved.startswith(self.base_dir):
            raise ValueError("Access denied: path traversal attempt detected.")
        return resolved

    def _get_git_statuses(self) -> Dict[str, str]:
        """Run git status --porcelain and return a mapping of workspace-relative paths to status characters."""
        statuses = {}
        try:
            res = subprocess.run(
                ["git", "status", "--porcelain", "-uall"],
                cwd=self.base_dir,
                capture_output=True,
                text=True,
                check=True
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
            rel_path = "/" + os.path.relpath(abs_path, self.base_dir).strip("/")

        stat = os.stat(abs_path)
        last_modified = int(stat.st_mtime)
        
        git_status = statuses.get(rel_path, "Clean")

        if os.path.isdir(abs_path):
            children = []
            try:
                for entry in sorted(os.listdir(abs_path)):
                    # Skip hidden files
                    if entry.startswith("."):
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
                "children": children
            }
        else:
            return {
                "name": name,
                "path": rel_path,
                "type": "file",
                "size": stat.st_size,
                "last_modified": last_modified,
                "git_status": git_status,
                "children": None
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
            raise PermissionError(f"Cannot edit: file '{rel_path}' is locked by an active process.")
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
        clean_rel = "/" + os.path.relpath(abs_path, self.base_dir).strip("/")

        return {
            "name": name,
            "path": clean_rel,
            "type": node_type,
            "size": stat.st_size if node_type == "file" else None,
            "last_modified": last_modified,
            "git_status": statuses.get(clean_rel, "U" if node_type == "file" else "Clean"),
            "children": [] if node_type == "directory" else None
        }

    def delete_file_node(self, rel_path: str) -> None:
        """Safely delete a file or directory from the workspace filesystem."""
        if self.is_file_locked(rel_path):
            raise PermissionError(f"Cannot delete: file or folder '{rel_path}' is locked by an active process.")

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
            raise PermissionError(f"Cannot move/rename: source '{src_rel_path}' is locked by an active process.")

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
                check=True
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
                check=True
            )
            for line in res.stdout.splitlines():
                if len(line) < 4:
                    continue
                xy = line[:2]
                path = line[3:].strip('"')
                rel_path = "/" + path.strip("/")
                
                x, y = xy[0], xy[1]
                staged = x != ' ' and x != '?'
                
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
                    
                changes.append({
                    "path": rel_path,
                    "git_status": status_code,
                    "staged": staged
                })
        except Exception as e:
            logger.error("Failed to run git status: %s", e)

        is_clean = len(changes) == 0
        return {
            "branch_name": branch_name,
            "is_clean": is_clean,
            "changes": changes
        }

    def get_git_diff(self, rel_path: str) -> str:
        """Return the unified git diff of a file (handles untracked files)."""
        abs_path = self.sanitize_path(rel_path)
        is_untracked = False
        try:
            res_status = subprocess.run(
                ["git", "status", "--porcelain", abs_path],
                cwd=self.base_dir,
                capture_output=True,
                text=True
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
                    text=True
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
                    text=True
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
                text=True
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
                subprocess.run(["git", "reset", "HEAD", "--", abs_path], cwd=self.base_dir, capture_output=True)
                subprocess.run(["git", "checkout", "HEAD", "--", abs_path], cwd=self.base_dir, capture_output=True, check=True)
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
            subprocess.run(["git", "add", "-A"], cwd=self.base_dir, capture_output=True, check=True)
            subprocess.run(["git", "commit", "-m", message], cwd=self.base_dir, capture_output=True, check=True)
            res_hash = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.base_dir, capture_output=True, text=True, check=True)
            commit_hash = res_hash.stdout.strip()
            
            return {
                "commit_hash": commit_hash,
                "message": message,
                "timestamp": int(time.time())
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
                check=True
            )
            for line in res.stdout.splitlines():
                parts = line.split("|", 3)
                if len(parts) < 4:
                    continue
                commits.append({
                    "commit_hash": parts[0],
                    "message": parts[1],
                    "author": parts[2],
                    "timestamp": int(parts[3])
                })
        except Exception as e:
            logger.debug("Failed to fetch git history: %s", e)
        return commits

    def _get_authenticated_url(self, remote_url: str, username: Optional[str], token: Optional[str]) -> str:
        if not remote_url:
            return ""
        if remote_url.startswith("/") or remote_url.startswith("file://"):
            return remote_url
        if username and token and remote_url.startswith("https://"):
            stripped = remote_url[8:]
            return f"https://{username}:{token}@{stripped}"
        return remote_url

    def push_remote(self, remote_url: str, username: Optional[str] = None, token: Optional[str] = None) -> None:
        """Push local commits to the configured remote repository."""
        if not remote_url:
            raise ValueError("Git remote URL is not configured.")
        
        branch_name = self.get_git_status()["branch_name"]
        authenticated_url = self._get_authenticated_url(remote_url, username, token)
        
        try:
            subprocess.run(
                ["git", "push", authenticated_url, branch_name],
                cwd=self.base_dir,
                capture_output=True,
                text=True,
                check=True
            )
        except subprocess.CalledProcessError as e:
            logger.error("Failed to push changes: %s\nStderr: %s", e, e.stderr)
            raise RuntimeError(f"Failed to push changes: {e.stderr.strip() or str(e)}")

    def pull_remote(self, remote_url: str, username: Optional[str] = None, token: Optional[str] = None) -> None:
        """Pull commits from the configured remote repository."""
        if not remote_url:
            raise ValueError("Git remote URL is not configured.")
            
        branch_name = self.get_git_status()["branch_name"]
        authenticated_url = self._get_authenticated_url(remote_url, username, token)
        
        try:
            subprocess.run(
                ["git", "pull", "--no-rebase", authenticated_url, branch_name],
                cwd=self.base_dir,
                capture_output=True,
                text=True,
                check=True
            )
        except subprocess.CalledProcessError as e:
            # Check for merge conflicts
            conflicted_files = []
            try:
                res = subprocess.run(
                    ["git", "status", "--porcelain"],
                    cwd=self.base_dir,
                    capture_output=True,
                    text=True
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
                
            logger.error("Failed to pull changes: %s\nStderr: %s", e, e.stderr)
            raise RuntimeError(f"Failed to pull changes: {e.stderr.strip() or str(e)}")
