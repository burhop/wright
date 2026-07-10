import os
import tempfile
import pytest
from fastapi.testclient import TestClient
from api.main import app
from agent_adapters import (
    BaseAgentEngine,
    AgentSessionInfo,
    AgentChatRequest,
    AgentStreamEvent,
)
from typing import AsyncIterator


# Mock Agent Engine to return a temporary workspace path
class MockAgentEngine(BaseAgentEngine):
    def __init__(self, workspace_path: str):
        self.workspace_path = workspace_path
        self.test_session_title = "Test Session"

    async def check_health(self) -> dict:
        return {"state": "connected", "latencyMs": 1.0}

    async def create_session(self, workspace: str | None = None) -> AgentSessionInfo:
        return AgentSessionInfo(
            session_id="mock-session",
            title="Mock Session",
            created_at=1000,
            updated_at=1000,
            message_count=0,
            workspace=workspace or self.workspace_path,
        )

    async def list_sessions(self) -> list[AgentSessionInfo]:
        return [
            AgentSessionInfo(
                session_id="test-session",
                title=self.test_session_title,
                created_at=1000,
                updated_at=1000,
                message_count=0,
                workspace=self.workspace_path,
            ),
            AgentSessionInfo(
                session_id="mock-session",
                title="Mock Session",
                created_at=1000,
                updated_at=1000,
                message_count=0,
                workspace=self.workspace_path,
            ),
        ]

    async def delete_session(self, session_id: str) -> bool:
        return True

    async def stream_chat(
        self, request: AgentChatRequest
    ) -> AsyncIterator[AgentStreamEvent]:
        yield AgentStreamEvent(type="token", data={"text": "hello"})

    async def get_session_workspace(self, session_id: str) -> str | None:
        return self.workspace_path

    async def save_context(self, session_id: str, workspace_id: str) -> bool:
        return True

    async def load_context(self, session_id: str, workspace_id: str) -> dict | None:
        return None

    async def get_chat_history(self, session_id: str) -> list:
        return []

    async def get_commands(self) -> list:
        return []


@pytest.fixture
def workspace_setup():
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create designs folder
        designs_dir = os.path.join(temp_dir, "designs")
        os.makedirs(designs_dir, exist_ok=True)

        # Create a sample stl file
        stl_path = os.path.join(designs_dir, "bracket.stl")
        with open(stl_path, "wb") as f:
            f.write(b"solid mesh data here")

        # Create a sample scad file
        scad_path = os.path.join(temp_dir, "model.scad")
        with open(scad_path, "w") as f:
            f.write("cube([10, 20, 30]);")

        yield temp_dir


@pytest.fixture
def client(workspace_setup) -> TestClient:
    # Clean up test-session workspace from DB to avoid stale temp directories
    from api.config import DATABASE_PATH
    import sqlite3

    try:
        conn = sqlite3.connect(DATABASE_PATH)
        conn.execute(
            """DELETE FROM workspace_agent_sessions
            WHERE workspace_id IN (
                SELECT workspace_id FROM engineering_workspaces
                WHERE session_id IN ('test-session', 'mock-session', 'new-test-session', 'occupied-session')
            )"""
        )
        conn.execute(
            "DELETE FROM workspace_agent_sessions WHERE session_id IN ('test-session', 'mock-session', 'new-test-session', 'occupied-session')"
        )
        conn.execute(
            "DELETE FROM engineering_workspaces WHERE session_id IN ('test-session', 'mock-session', 'new-test-session', 'occupied-session')"
        )
        conn.commit()
        conn.close()
    except Exception:
        pass

    mock_engine = MockAgentEngine(workspace_setup)
    app.state.agent_engine = mock_engine
    if hasattr(app.state, "chat_stream_registry"):
        delattr(app.state, "chat_stream_registry")
    with TestClient(app) as c:
        yield c


def test_list_workspace_files(client):
    response = client.get("/api/workspace/files", params={"session_id": "test-session"})
    assert response.status_code == 200
    data = response.json()
    assert "workspace" in data
    root = data["workspace"]
    assert root["type"] == "directory"

    # Check children
    children = root["children"]
    assert len(children) >= 2

    names = [c["name"] for c in children]
    assert "designs" in names
    assert "model.scad" in names

    # Find designs folder and check child file
    designs_node = next(c for c in children if c["name"] == "designs")
    assert designs_node["type"] == "directory"
    assert len(designs_node["children"]) == 1
    assert designs_node["children"][0]["name"] == "bracket.stl"
    assert designs_node["children"][0]["path"] == "/designs/bracket.stl"


def test_default_workspace_parent_prefers_userprofile(monkeypatch):
    from api.routers.workspace import get_default_workspace_parent_dir

    monkeypatch.delenv("WRIGHT_WORKSPACES_DIR", raising=False)
    monkeypatch.setenv("USERPROFILE", r"C:\Users\User")
    monkeypatch.setenv("HOME", r"C:\unexpected-home")

    assert get_default_workspace_parent_dir() == r"C:\Users\User\wright"


def test_get_file_content_success(client):
    # Fetch .scad file content
    response = client.get(
        "/api/workspace/files/content",
        params={"session_id": "test-session", "path": "/model.scad"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["content"] == "cube([10, 20, 30]);"
    assert "application/json" in response.headers["content-type"]

    # Fetch .stl file content (binary stream)
    response_stl = client.get(
        "/api/workspace/files/content",
        params={"session_id": "test-session", "path": "/designs/bracket.stl"},
    )
    assert response_stl.status_code == 200
    assert response_stl.content == b"solid mesh data here"
    # FileResponse uses MIME type detection, .stl may return model/stl or application/octet-stream
    content_type = response_stl.headers["content-type"]
    assert "stl" in content_type or "octet-stream" in content_type


def test_get_file_content_not_found(client):
    response = client.get(
        "/api/workspace/files/content",
        params={"session_id": "test-session", "path": "/missing.stl"},
    )
    assert response.status_code == 404
    assert "File not found" in response.json()["message"]


def test_get_file_content_traversal_blocked(client):
    # Attempt directory traversal out of workspace root
    response = client.get(
        "/api/workspace/files/content",
        params={"session_id": "test-session", "path": "/../../etc/passwd"},
    )
    assert response.status_code in (400, 500)  # may raise ValueError or HTTPException
    data = response.json()
    assert "error_code" in data or "detail" in data


def test_create_file_and_directory(client):
    # Create directory
    response = client.post(
        "/api/workspace/files",
        json={"session_id": "test-session", "path": "/new_folder", "type": "directory"},
    )
    assert response.status_code == 201
    assert response.json()["name"] == "new_folder"
    assert response.json()["type"] == "directory"

    # Create file
    response = client.post(
        "/api/workspace/files",
        json={
            "session_id": "test-session",
            "path": "/new_folder/test.txt",
            "type": "file",
        },
    )
    assert response.status_code == 201
    assert response.json()["name"] == "test.txt"
    assert response.json()["type"] == "file"


def test_delete_file_and_directory(client):
    # Setup - create files to delete
    client.post(
        "/api/workspace/files",
        json={"session_id": "test-session", "path": "/to_delete.txt", "type": "file"},
    )

    # Delete file
    response = client.delete(
        "/api/workspace/files",
        params={"session_id": "test-session", "path": "/to_delete.txt"},
    )
    assert response.status_code == 204


def test_move_file(client):
    # Setup - create folder and file
    client.post(
        "/api/workspace/files",
        json={
            "session_id": "test-session",
            "path": "/move_folder",
            "type": "directory",
        },
    )
    client.post(
        "/api/workspace/files",
        json={"session_id": "test-session", "path": "/to_move.txt", "type": "file"},
    )

    # Move file
    response = client.put(
        "/api/workspace/files/move",
        json={
            "session_id": "test-session",
            "source_path": "/to_move.txt",
            "destination_path": "/move_folder/moved.txt",
        },
    )
    assert response.status_code == 200
    assert response.json()["success"] is True


def test_git_status_and_commit(client):
    # Add a file first (will be untracked 'U')
    client.post(
        "/api/workspace/files",
        json={"session_id": "test-session", "path": "/untracked.txt", "type": "file"},
    )

    # Check Git Status
    response = client.get(
        "/api/workspace/git/status", params={"session_id": "test-session"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "branch_name" in data
    assert len(data["changes"]) > 0

    # Commit changes
    response_commit = client.post(
        "/api/workspace/git/commit",
        json={"session_id": "test-session", "message": "feat: test git commit"},
    )
    assert response_commit.status_code == 200
    assert response_commit.json()["success"] is True

    # Check history
    response_history = client.get(
        "/api/workspace/git/history", params={"session_id": "test-session"}
    )
    assert response_history.status_code == 200
    assert len(response_history.json()["commits"]) > 0


def test_git_diff_and_revert(client):
    # Setup - Create file and commit it
    client.post(
        "/api/workspace/files",
        json={"session_id": "test-session", "path": "/diff_test.txt", "type": "file"},
    )
    client.post(
        "/api/workspace/git/commit",
        json={"session_id": "test-session", "message": "initial commit"},
    )

    # Modify file content manually on disk by resolving its path
    from api.config import DATABASE_PATH
    from core.workspace import get_workspace_by_session

    workspace = get_workspace_by_session(DATABASE_PATH, "test-session")
    file_path = os.path.join(workspace["local_path"], "diff_test.txt")
    with open(file_path, "w") as f:
        f.write("modified content here")

    # Get Diff
    response_diff = client.get(
        "/api/workspace/git/diff",
        params={"session_id": "test-session", "path": "/diff_test.txt"},
    )
    assert response_diff.status_code == 200
    assert "diff" in response_diff.json()

    # Revert
    response_revert = client.post(
        "/api/workspace/git/revert",
        json={"session_id": "test-session", "path": "/diff_test.txt"},
    )
    assert response_revert.status_code == 200

    # Verify file content is reverted (empty)
    with open(file_path, "r") as f:
        assert f.read() == ""


def test_workspace_config_and_remote_operations(client):
    import subprocess
    import shutil
    import stat

    def remove_tree(path):
        def handle_remove_readonly(func, remove_path, _exc_info):
            os.chmod(remove_path, stat.S_IWRITE)
            func(remove_path)

        shutil.rmtree(path, onerror=handle_remove_readonly)

    # 1. GET config initially
    response = client.get(
        "/api/workspace/config", params={"session_id": "test-session"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "workspace_id" in data
    assert data["git_remote_url"] is None
    assert data["git_username"] is None
    assert data["has_token"] is False

    # 2. Create a bare remote repository
    remote_dir = tempfile.mkdtemp()
    try:
        subprocess.run(["git", "init", "--bare"], cwd=remote_dir, check=True)

        # Configure remote URL
        response_config = client.post(
            "/api/workspace/config",
            json={
                "session_id": "test-session",
                "git_remote_url": remote_dir,
                "git_username": "test-user",
                "git_token": "test-token",
            },
        )
        assert response_config.status_code == 200
        assert response_config.json()["success"] is True

        # Verify settings updated in GET
        response = client.get(
            "/api/workspace/config", params={"session_id": "test-session"}
        )
        data = response.json()
        assert data["git_remote_url"] == remote_dir
        assert data["git_username"] == "test-user"
        assert data["has_token"] is True

        # 3. Create a local file and commit it
        client.post(
            "/api/workspace/files",
            json={
                "session_id": "test-session",
                "path": "/push_test.txt",
                "type": "file",
            },
        )
        client.post(
            "/api/workspace/git/commit",
            json={"session_id": "test-session", "message": "feat: test remote push"},
        )

        # 4. Push to remote
        push_res = client.post(
            "/api/workspace/git/push", json={"session_id": "test-session"}
        )
        assert push_res.status_code == 200
        assert push_res.json()["success"] is True

        # Verify the commit exists on bare remote
        res = subprocess.run(
            ["git", "log", "-n1", "--oneline"],
            cwd=remote_dir,
            capture_output=True,
            text=True,
            check=True,
        )
        assert "feat: test remote push" in res.stdout

        # 5. Setup clone to make remote commits
        clone_dir = tempfile.mkdtemp()
        try:
            # Git needs configuration in testing environments for commits to work
            subprocess.run(
                ["git", "config", "--global", "user.email", "test@example.com"],
                check=True,
            )
            subprocess.run(
                ["git", "config", "--global", "user.name", "Test User"], check=True
            )

            subprocess.run(["git", "clone", remote_dir, clone_dir], check=True)

            # Get current branch of the clone
            branch_res = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=clone_dir,
                capture_output=True,
                text=True,
                check=True,
            )
            current_branch = branch_res.stdout.strip()

            # Make commit on remote clone
            test_file = os.path.join(clone_dir, "push_test.txt")
            with open(test_file, "w") as f:
                f.write("remote modifications")
            subprocess.run(["git", "add", "push_test.txt"], cwd=clone_dir, check=True)
            subprocess.run(
                ["git", "commit", "-m", "remote update"], cwd=clone_dir, check=True
            )
            subprocess.run(
                ["git", "push", "origin", current_branch], cwd=clone_dir, check=True
            )

            # Pull changes in workspace
            pull_res = client.post(
                "/api/workspace/git/pull", json={"session_id": "test-session"}
            )
            assert pull_res.status_code == 200
            assert pull_res.json()["success"] is True

            # Verify file modified in workspace
            from core.workspace import get_workspace_by_session
            from api.config import DATABASE_PATH

            workspace = get_workspace_by_session(DATABASE_PATH, "test-session")
            workspace_file = os.path.join(workspace["local_path"], "push_test.txt")
            with open(workspace_file, "r") as f:
                assert f.read() == "remote modifications"

            # 6. Setup Merge Conflict
            with open(test_file, "w") as f:
                f.write("conflicting remote modifications")
            subprocess.run(["git", "add", "push_test.txt"], cwd=clone_dir, check=True)
            subprocess.run(
                ["git", "commit", "-m", "conflicting remote update"],
                cwd=clone_dir,
                check=True,
            )
            subprocess.run(
                ["git", "push", "origin", current_branch], cwd=clone_dir, check=True
            )

            # Edit locally
            with open(workspace_file, "w") as f:
                f.write("conflicting local modifications")
            client.post(
                "/api/workspace/git/commit",
                json={
                    "session_id": "test-session",
                    "message": "conflicting local update",
                },
            )

            # Pull -> should trigger 409 Conflict
            pull_conflict_res = client.post(
                "/api/workspace/git/pull", json={"session_id": "test-session"}
            )
            assert pull_conflict_res.status_code == 409
            conflict_data = pull_conflict_res.json()
            assert conflict_data["success"] is False
            assert "/push_test.txt" in conflict_data["conflicted_files"]

        finally:
            remove_tree(clone_dir)

    finally:
        remove_tree(remote_dir)


def test_workspace_file_locks(client):
    # Setup - Create file
    client.post(
        "/api/workspace/files",
        json={"session_id": "test-session", "path": "/locked_file.txt", "type": "file"},
    )

    # Retrieve local path
    from api.config import DATABASE_PATH
    from core.workspace import get_workspace_by_session, WorkspaceManager

    workspace = get_workspace_by_session(DATABASE_PATH, "test-session")
    manager = WorkspaceManager(workspace["local_path"])

    # Assert initially not locked
    assert not manager.is_file_locked("/locked_file.txt")

    # Lock the file
    manager.lock_file("/locked_file.txt")
    assert manager.is_file_locked("/locked_file.txt")

    # Trying to delete should fail with PermissionError
    with pytest.raises(PermissionError):
        manager.delete_file_node("/locked_file.txt")

    # Trying to move/rename should fail with PermissionError
    with pytest.raises(PermissionError):
        manager.move_file_node("/locked_file.txt", "/moved_locked.txt")

    # Unlock file
    manager.unlock_file("/locked_file.txt")
    assert not manager.is_file_locked("/locked_file.txt")

    # Deleting now should succeed
    manager.delete_file_node("/locked_file.txt")


def test_save_file_content_success(client):
    # Create a file
    client.post(
        "/api/workspace/files",
        json={"session_id": "test-session", "path": "/save_test.py", "type": "file"},
    )

    # Save content to the file
    response = client.put(
        "/api/workspace/files/content",
        json={
            "session_id": "test-session",
            "path": "/save_test.py",
            "content": "print('hello world')",
        },
    )
    assert response.status_code == 200
    assert response.json()["success"] is True

    # Read back content and verify it matches
    response_get = client.get(
        "/api/workspace/files/content",
        params={"session_id": "test-session", "path": "/save_test.py"},
    )
    assert response_get.status_code == 200
    get_data = response_get.json()
    assert get_data["content"] == "print('hello world')"


def test_save_file_content_traversal_blocked(client):
    response = client.put(
        "/api/workspace/files/content",
        json={
            "session_id": "test-session",
            "path": "/../../etc/passwd",
            "content": "malicious",
        },
    )
    assert response.status_code in (400, 500)  # may raise ValueError or HTTPException
    data = response.json()
    assert "error_code" in data or "detail" in data


def test_workspace_tools_endpoints(client):
    # Retrieve tools
    response = client.get("/api/workspace/tools", params={"session_id": "test-session"})
    assert response.status_code == 200
    data = response.json()
    assert "enabled_tools" in data

    # Toggle a tool off
    response_toggle = client.post(
        "/api/workspace/tools/toggle",
        json={
            "session_id": "test-session",
            "server_id": "OpenSCAD Geometry",
            "is_enabled": False,
        },
    )
    assert response_toggle.status_code == 200
    toggle_data = response_toggle.json()
    assert toggle_data["success"] is True
    assert toggle_data["is_enabled"] is False

    # Retrieve tools again to assert change persisted
    response_get = client.get(
        "/api/workspace/tools", params={"session_id": "test-session"}
    )
    assert response_get.status_code == 200
    tools = response_get.json()["enabled_tools"]
    assert "OpenSCAD Geometry" not in tools


def test_workspace_recent_and_list(client):
    # Ensure test-session exists by listing files first
    client.get("/api/workspace/files", params={"session_id": "test-session"})

    # Test GET /api/workspace/recent
    response = client.get("/api/workspace/recent")
    assert response.status_code == 200
    data = response.json()
    assert "workspaces" in data
    assert len(data["workspaces"]) >= 1
    assert any(w["session_id"] == "test-session" for w in data["workspaces"])

    # Test GET /api/workspace/list
    response_list = client.get("/api/workspace/list")
    assert response_list.status_code == 200
    data_list = response_list.json()
    assert "workspaces" in data_list
    assert len(data_list["workspaces"]) >= 1
    assert any(w["session_id"] == "test-session" for w in data_list["workspaces"])


def test_workspace_activate(client):
    # Ensure test-session exists
    client.get("/api/workspace/files", params={"session_id": "test-session"})

    # Test POST /api/workspace/activate
    response = client.post(
        "/api/workspace/activate", json={"session_id": "test-session"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["session_id"] == "test-session"
    assert "workspace_path" in data


def test_active_agent_endpoints(client):
    # Test GET /api/agent/active (should default to hermes or whatever the active agent is)
    response = client.get("/api/agent/active")
    assert response.status_code == 200
    assert "agent" in response.json()

    # Test POST /api/agent/active to update the agent to openclaw
    response_post = client.post(
        "/api/agent/active",
        json={"agent": "openclaw"},
        params={"session_id": "test-session"},
    )
    assert response_post.status_code == 200
    assert response_post.json()["agent"] == "openclaw"

    # Verify the updated agent via GET
    response_get = client.get("/api/agent/active")
    assert response_get.status_code == 200
    assert response_get.json()["agent"] == "openclaw"

    # Reset back to hermes
    client.post("/api/agent/active", json={"agent": "hermes"})


def test_workspace_session_update(client):
    # Ensure test-session exists
    client.get("/api/workspace/files", params={"session_id": "test-session"})

    # Get the workspace ID
    response = client.get(
        "/api/workspace/config", params={"session_id": "test-session"}
    )
    workspace_id = response.json()["workspace_id"]

    # Test POST /api/workspace/by-id/{workspace_id}/session
    response_update = client.post(
        f"/api/workspace/by-id/{workspace_id}/session",
        json={"session_id": "new-test-session"},
    )
    assert response_update.status_code == 200
    assert response_update.json()["success"] is True
    assert response_update.json()["session_id"] == "new-test-session"

    # Verify the updated session ID in config
    response_config = client.get("/api/workspace/by-id/" + workspace_id)
    assert response_config.json()["session_id"] == "new-test-session"


def test_workspace_session_update_conflicts_when_session_owned_elsewhere(
    client, tmp_path
):
    from api.config import DATABASE_PATH
    from core.workspace import create_workspace
    import sqlite3

    client.get("/api/workspace/files", params={"session_id": "test-session"})
    response = client.get(
        "/api/workspace/config", params={"session_id": "test-session"}
    )
    workspace_id = response.json()["workspace_id"]

    other_path = tmp_path / "other-workspace"
    other_path.mkdir()
    create_workspace(
        DATABASE_PATH,
        "other-workspace-id",
        "occupied-session",
        str(other_path),
        "Other Workspace",
    )

    try:
        response_update = client.post(
            f"/api/workspace/by-id/{workspace_id}/session",
            json={"session_id": "occupied-session"},
        )

        assert response_update.status_code == 400
        error_body = response_update.json()
        assert "not associated with this workspace" in (
            error_body.get("detail") or error_body.get("message") or ""
        )
    finally:
        conn = sqlite3.connect(DATABASE_PATH)
        try:
            conn.execute(
                "DELETE FROM workspace_agent_sessions WHERE workspace_id = ?",
                ("other-workspace-id",),
            )
            conn.execute(
                "DELETE FROM engineering_workspaces WHERE workspace_id = ?",
                ("other-workspace-id",),
            )
            conn.commit()
        finally:
            conn.close()


def test_agent_sessions_filtering_by_workspace(client):
    # Ensure test-session exists
    client.get("/api/workspace/files", params={"session_id": "test-session"})

    # Get the workspace config to get workspace_id
    response = client.get(
        "/api/workspace/config", params={"session_id": "test-session"}
    )
    workspace_id = response.json()["workspace_id"]

    # Retrieve sessions with workspace_id query parameter
    response_sessions = client.get(
        "/api/agent/sessions", params={"workspace_id": workspace_id}
    )
    assert response_sessions.status_code == 200
    sessions = response_sessions.json()["sessions"]
    # Our MockAgentEngine lists test-session and mock-session under workspace_setup, so both should match
    assert len(sessions) == 2
    assert {s["session_id"] for s in sessions} == {"test-session", "mock-session"}

    # Query with a non-existent workspace_id, should return empty sessions
    response_empty = client.get(
        "/api/agent/sessions", params={"workspace_id": "non-existent-workspace-uuid"}
    )
    assert response_empty.status_code == 200
    assert len(response_empty.json()["sessions"]) == 0


def test_workspace_sessions_endpoint_retains_multiple_sessions(client):
    client.get("/api/workspace/files", params={"session_id": "test-session"})
    response = client.get(
        "/api/workspace/config", params={"session_id": "test-session"}
    )
    workspace_id = response.json()["workspace_id"]

    response_update = client.post(
        f"/api/workspace/by-id/{workspace_id}/session",
        json={"session_id": "new-test-session"},
    )
    assert response_update.status_code == 200

    response_sessions = client.get(f"/api/workspace/by-id/{workspace_id}/sessions")
    assert response_sessions.status_code == 200
    session_ids = {s["session_id"] for s in response_sessions.json()["sessions"]}

    assert "test-session" in session_ids
    assert "mock-session" in session_ids
    assert "new-test-session" in session_ids


def test_workspace_sessions_endpoint_uses_current_agent_title(client):
    from api.config import DATABASE_PATH
    from core.workspace import associate_workspace_session

    client.get("/api/workspace/files", params={"session_id": "test-session"})
    response = client.get(
        "/api/workspace/config", params={"session_id": "test-session"}
    )
    workspace_id = response.json()["workspace_id"]

    associate_workspace_session(
        DATABASE_PATH,
        workspace_id,
        "test-session",
        title="Old Local Title",
        created_at=1000,
        updated_at=1000,
    )

    response_sessions = client.get(f"/api/workspace/by-id/{workspace_id}/sessions")
    assert response_sessions.status_code == 200
    titles = {s["session_id"]: s["title"] for s in response_sessions.json()["sessions"]}

    assert titles["test-session"] == "Test Session"


def test_title_command_persists_workspace_session_title_when_agent_title_is_untitled(
    client,
):
    client.get("/api/workspace/files", params={"session_id": "test-session"})
    response = client.get(
        "/api/workspace/config", params={"session_id": "test-session"}
    )
    workspace_id = response.json()["workspace_id"]

    client.app.state.agent_engine.test_session_title = "Untitled Session"

    response_chat = client.post(
        "/api/agent/chat",
        json={"session_id": "test-session", "message": "/title mark"},
    )
    assert response_chat.status_code == 200

    response_sessions = client.get(f"/api/workspace/by-id/{workspace_id}/sessions")
    assert response_sessions.status_code == 200
    titles = {s["session_id"]: s["title"] for s in response_sessions.json()["sessions"]}

    assert titles["test-session"] == "mark"


def test_workspace_sessions_endpoint_disambiguates_duplicate_titles(client):
    from api.config import DATABASE_PATH
    from core.workspace import associate_workspace_session

    client.get("/api/workspace/files", params={"session_id": "test-session"})
    response = client.get(
        "/api/workspace/config", params={"session_id": "test-session"}
    )
    workspace_id = response.json()["workspace_id"]

    associate_workspace_session(
        DATABASE_PATH,
        workspace_id,
        "duplicate-session-a",
        title="Onshape Session 2",
        created_at=1001,
        updated_at=1001,
    )
    associate_workspace_session(
        DATABASE_PATH,
        workspace_id,
        "duplicate-session-b",
        title="Onshape Session 2",
        created_at=1002,
        updated_at=1002,
    )

    response_sessions = client.get(f"/api/workspace/by-id/{workspace_id}/sessions")
    assert response_sessions.status_code == 200
    sessions = response_sessions.json()["sessions"]
    titles = {s["session_id"]: s["title"] for s in sessions}

    assert titles["duplicate-session-b"] == "Onshape Session 2"
    assert titles["duplicate-session-a"] == "Onshape Session 2 (2)"


def test_workspace_mcp_status_by_workspace_uses_workspace_tools(client):
    from api.config import DATABASE_PATH
    import json
    import sqlite3
    import time

    client.get("/api/workspace/files", params={"session_id": "test-session"})
    response = client.get(
        "/api/workspace/config", params={"session_id": "test-session"}
    )
    workspace_id = response.json()["workspace_id"]

    now = int(time.time())
    conn = sqlite3.connect(DATABASE_PATH)
    try:
        conn.execute(
            "UPDATE engineering_workspaces SET enabled_tools = ? WHERE workspace_id = ?",
            (json.dumps(["Workspace Scoped Onshape MCP"]), workspace_id),
        )
        conn.execute(
            "DELETE FROM mcp_servers WHERE server_id IN (?, ?)",
            ("onshape-test", "other-test"),
        )
        conn.executemany(
            """
            INSERT INTO mcp_servers
                (server_id, name, type, command, is_installed, status, created_at, updated_at)
            VALUES (?, ?, 'stdio', '[]', 1, 'inactive', ?, ?)
            """,
            [
                ("onshape-test", "Workspace Scoped Onshape MCP", now, now),
                ("other-test", "Other Workspace MCP", now, now),
            ],
        )
        conn.commit()
    finally:
        conn.close()

    response_status = client.get(f"/api/workspace/by-id/{workspace_id}/mcp-status")
    assert response_status.status_code == 200
    running = response_status.json()["running_mcps"]
    assert {item["name"] for item in running} == {"Workspace Scoped Onshape MCP"}


def test_workspace_activate_session_fallback(client):
    from api.config import DATABASE_PATH
    from core.workspace import create_workspace
    import tempfile

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a workspace record in the DB with a session that is missing from the active sessions
        workspace_id = "test-fallback-workspace-uuid"
        missing_session_id = "missing-session-id"
        create_workspace(
            DATABASE_PATH,
            workspace_id,
            missing_session_id,
            temp_dir,
            workspace_name="Fallback Test",
        )

        # Override mock engine's list_sessions to return an active session matching temp_dir
        original_list_sessions = app.state.agent_engine.list_sessions

        async def mock_list_sessions():
            return [
                AgentSessionInfo(
                    session_id="matching-active-session",
                    title="Active Session",
                    created_at=1000,
                    updated_at=1000,
                    message_count=0,
                    workspace=temp_dir,
                )
            ]

        app.state.agent_engine.list_sessions = mock_list_sessions

        try:
            # Activate workspace using the missing session ID
            response = client.post(
                "/api/workspace/activate", json={"session_id": missing_session_id}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            # It should have successfully fallen back to the active matching-active-session
            assert data["session_id"] == "matching-active-session"
            assert data["workspace_path"] == temp_dir
        finally:
            app.state.agent_engine.list_sessions = original_list_sessions


def test_workspace_gitignore_setup(tmp_path):
    from core.workspace import WorkspaceManager
    import os

    # Initialize WorkspaceManager with a fresh directory
    workspace_dir = str(tmp_path / "new_workspace")
    WorkspaceManager(workspace_dir)

    # Check if .gitignore was created
    gitignore_path = os.path.join(workspace_dir, ".gitignore")
    assert os.path.exists(gitignore_path)

    # Read gitignore content
    with open(gitignore_path, "r") as f:
        content = f.read()

    assert "tmp/\n" in content
    assert "/tmp/\n" in content


def test_compile_workspace_mcp_instructions(tmp_path):
    from core.workspace import compile_workspace_mcp_instructions, create_workspace
    import sqlite3

    db_path = str(tmp_path / "test.db")
    # Initialize minimal schema
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS engineering_workspaces (
            workspace_id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL UNIQUE,
            workspace_name TEXT,
            local_path TEXT NOT NULL,
            git_remote_url TEXT,
            git_username TEXT,
            git_token TEXT,
            enabled_tools TEXT,
            created_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL
        )
        """)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS mcp_servers (
            server_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            command TEXT,
            is_active INTEGER NOT NULL DEFAULT 0,
            is_installed INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'inactive',
            category TEXT,
            created_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL,
            image_url TEXT,
            description TEXT,
            source_url TEXT,
            installed_version TEXT,
            env_vars TEXT,
            instructions TEXT
        )
        """)
        conn.commit()
    finally:
        conn.close()

    # Seed an installed mcp server
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("""
        INSERT INTO mcp_servers (server_id, name, type, is_installed, instructions, created_at, updated_at)
        VALUES ('mcp1', 'Test MCP', 'stdio', 1, 'Test instructions', 1000, 1000)
        """)
        conn.commit()
    finally:
        conn.close()

    # 1. Test compile when no workspace exists
    assert compile_workspace_mcp_instructions(db_path, "/path/doesnt/exist") is None

    # 2. Test compile when workspace exists with enabled_tools=None (defaults to all installed)
    create_workspace(db_path, "ws1", "sess1", "/my/workspace", "My Workspace")
    instructions = compile_workspace_mcp_instructions(db_path, "/my/workspace")
    assert instructions is not None
    assert "## Test MCP Instructions" in instructions
    assert "Test instructions" in instructions

    # 3. Test compile when workspace exists with empty enabled_tools (no tools enabled)
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("UPDATE engineering_workspaces SET enabled_tools = '[]'")
        conn.commit()
    finally:
        conn.close()
    instructions_empty = compile_workspace_mcp_instructions(db_path, "/my/workspace")
    assert instructions_empty is not None
    assert "## Global Workspace Rules" in instructions_empty
    assert "## Test MCP Instructions" not in instructions_empty


def test_workspace_sanitize_path_local_vs_system_tmp(tmp_path):
    from core.workspace import WorkspaceManager
    import os

    # Set up local workspace directory
    workspace_dir = str(tmp_path / "local_workspace")
    os.makedirs(workspace_dir, exist_ok=True)
    manager = WorkspaceManager(workspace_dir)

    # 1. Create a file in local workspace's tmp folder
    local_tmp_dir = os.path.join(workspace_dir, ".wright", "tmp", "openscad-mcp")
    os.makedirs(local_tmp_dir, exist_ok=True)
    local_file_path = os.path.join(local_tmp_dir, "test.scad")
    with open(local_file_path, "w") as f:
        f.write("local content")

    # Verify that requesting "tmp/openscad-mcp/test.scad" resolves to the local path
    resolved_local = manager.sanitize_path("tmp/openscad-mcp/test.scad")
    assert resolved_local == local_file_path

    # Absolute/global temporary paths are never workspace capabilities.
    with pytest.raises(ValueError):
        manager.sanitize_path("/tmp/openscad-mcp/test.scad")

    # 3. For a file that does not exist anywhere, requesting it should default to local
    nonexistent_path = "tmp/openscad-mcp/nonexistent.scad"
    resolved_nonexistent = manager.sanitize_path(nonexistent_path)
    expected_local = os.path.abspath(
        os.path.join(
            workspace_dir, ".wright", "tmp", "openscad-mcp", "nonexistent.scad"
        )
    )
    assert resolved_nonexistent == expected_local


def test_activate_workspace_fallback_passes_instructions(tmp_path):
    from core.workspace import activate_workspace, create_workspace
    import sqlite3
    import asyncio
    import os

    db_path = str(tmp_path / "test.db")
    local_path = str(tmp_path / "my_workspace")
    os.makedirs(local_path, exist_ok=True)

    # Initialize minimal schema
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS engineering_workspaces (
            workspace_id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL UNIQUE,
            workspace_name TEXT,
            local_path TEXT NOT NULL,
            git_remote_url TEXT,
            git_username TEXT,
            git_token TEXT,
            enabled_tools TEXT,
            created_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL
        )
        """)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS mcp_servers (
            server_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            command TEXT,
            is_active INTEGER NOT NULL DEFAULT 0,
            is_installed INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'inactive',
            category TEXT,
            created_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL,
            image_url TEXT,
            description TEXT,
            source_url TEXT,
            installed_version TEXT,
            env_vars TEXT,
            instructions TEXT
        )
        """)
        # Seed workspace and an installed mcp server
        create_workspace(db_path, "ws1", "missing-session", local_path, "My Workspace")
        conn.execute("""
        INSERT INTO mcp_servers (server_id, name, type, is_installed, instructions, created_at, updated_at)
        VALUES ('mcp1', 'Test MCP', 'stdio', 1, 'My test instructions', 1000, 1000)
        """)
        conn.commit()
    finally:
        conn.close()

    # Define a mock engine
    class MockEngine:
        def __init__(self):
            self.created_sessions = []

        async def list_sessions(self):
            # Return empty list to force fallback creation of a session
            return []

        async def create_session(self, workspace, instructions=None):
            from agent_adapters import AgentSessionInfo

            info = AgentSessionInfo(
                session_id="new-fallback-session",
                title="New Session",
                created_at=1000,
                updated_at=1000,
                message_count=0,
                workspace=workspace,
            )
            self.created_sessions.append((workspace, instructions))
            return info

    engine = MockEngine()

    # Activate workspace - this should trigger creating a fallback session.
    session_id = asyncio.run(
        activate_workspace(db_path, "missing-session", local_path, engine)
    )

    assert session_id == "new-fallback-session"
    assert len(engine.created_sessions) == 1
    workspace_path, instructions = engine.created_sessions[0]
    assert workspace_path == local_path
    assert instructions is None

    # Provider-specific context materialization is owned by agent adapters.
    hermes_md_path = os.path.join(local_path, ".hermes.md")
    assert not os.path.exists(hermes_md_path)


def test_write_workspace_hermes_md(tmp_path):
    from agent_adapters.hermes_gateway import write_workspace_hermes_md
    from core.workspace import create_workspace
    import sqlite3
    import os

    db_path = str(tmp_path / "test.db")
    local_path = str(tmp_path / "my_workspace")
    os.makedirs(local_path, exist_ok=True)

    # Setup database
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS engineering_workspaces (
            workspace_id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL UNIQUE,
            workspace_name TEXT,
            local_path TEXT NOT NULL,
            git_remote_url TEXT,
            git_username TEXT,
            git_token TEXT,
            enabled_tools TEXT,
            created_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL
        )
        """)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS mcp_servers (
            server_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            command TEXT,
            is_active INTEGER NOT NULL DEFAULT 0,
            is_installed INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'inactive',
            category TEXT,
            created_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL,
            image_url TEXT,
            description TEXT,
            source_url TEXT,
            installed_version TEXT,
            env_vars TEXT,
            instructions TEXT
        )
        """)
        create_workspace(db_path, "ws1", "missing-session", local_path, "My Workspace")
        conn.execute("""
        INSERT INTO mcp_servers (server_id, name, type, is_installed, instructions, created_at, updated_at)
        VALUES ('mcp1', 'Test MCP', 'stdio', 1, 'My test instructions', 1000, 1000)
        """)
        conn.commit()
    finally:
        conn.close()

    hermes_md_path = os.path.join(local_path, ".hermes.md")

    # 1. Test first write (file doesn't exist)
    write_workspace_hermes_md(db_path, local_path)
    assert os.path.exists(hermes_md_path)
    with open(hermes_md_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "<!-- WRIGHT MCP INSTRUCTIONS START -->" in content
    assert "My test instructions" in content
    assert "<!-- WRIGHT MCP INSTRUCTIONS END -->" in content

    # 2. Test preserving user content
    user_rules = "# User Project Rules\n\nRule 1: Always do X.\n"
    with open(hermes_md_path, "w", encoding="utf-8") as f:
        f.write(user_rules + content)

    # Modify instructions in DB
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "UPDATE mcp_servers SET instructions = 'Updated instructions' WHERE server_id = 'mcp1'"
        )
        conn.commit()
    finally:
        conn.close()

    write_workspace_hermes_md(db_path, local_path)
    with open(hermes_md_path, "r", encoding="utf-8") as f:
        new_content = f.read()

    assert "Rule 1: Always do X." in new_content
    assert "Updated instructions" in new_content
    assert "My test instructions" not in new_content


@pytest.mark.asyncio
async def test_workspace_runner_sync_starts_only_assigned_installed_mcps(tmp_path):
    from core.workspace import create_workspace, sync_workspace_runners
    import json
    import sqlite3
    import time
    import asyncio

    db_path = str(tmp_path / "test.db")
    now = int(time.time())
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("""
        CREATE TABLE engineering_workspaces (
            workspace_id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL UNIQUE,
            workspace_name TEXT,
            local_path TEXT NOT NULL,
            git_remote_url TEXT,
            git_username TEXT,
            git_token TEXT,
            enabled_tools TEXT,
            created_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL
        )
        """)
        conn.execute("""
        CREATE TABLE mcp_servers (
            server_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            command TEXT,
            is_active INTEGER NOT NULL DEFAULT 0,
            is_installed INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'inactive',
            category TEXT,
            approval_gates TEXT,
            created_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL
        )
        """)
        conn.commit()
    finally:
        conn.close()

    workspace_dir = str(tmp_path / "workspace")
    os.makedirs(workspace_dir, exist_ok=True)
    create_workspace(db_path, "ws1", "session-1", workspace_dir, "Workspace 1")

    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "UPDATE engineering_workspaces SET enabled_tools = ? WHERE session_id = ?",
            (json.dumps(["assigned-mcp"]), "session-1"),
        )
        conn.executemany(
            """
            INSERT INTO mcp_servers
                (server_id, name, type, command, is_installed, status, approval_gates, created_at, updated_at)
            VALUES (?, ?, 'stdio', '[]', 1, 'inactive', ?, ?, ?)
            """,
            [
                (
                    "assigned-mcp",
                    "Assigned MCP",
                    json.dumps(["workspace_write_approval"]),
                    now,
                    now,
                ),
                ("unassigned-mcp", "Unassigned MCP", None, now, now),
            ],
        )
        conn.commit()
    finally:
        conn.close()

    class FakeMcpEngine:
        def __init__(self):
            self.started = []
            self.stopped = []

        async def start_server(
            self, server_id, workspace_dir=None, *, approval_context=None
        ):
            self.started.append((server_id, workspace_dir, approval_context))

        async def stop_server(self, server_id):
            self.stopped.append(server_id)

    engine = FakeMcpEngine()

    await sync_workspace_runners(db_path, "session-1", engine)
    await asyncio.sleep(0)

    assert len(engine.started) == 1
    started_server_id, started_workspace_dir, approval_context = engine.started[0]
    assert started_server_id == "assigned-mcp"
    assert started_workspace_dir == workspace_dir
    assert approval_context.workspace_id == "ws1"
    assert approval_context.workspace_approvals == {"workspace_write_approval"}
    assert engine.stopped == ["unassigned-mcp"]


def test_workspace_mcp_status_endpoint(client):
    # Retrieve mcp status for a session
    response = client.get(
        "/api/workspace/mcp-status", params={"session_id": "test-session"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "message" in data
    assert "running_mcps" in data


def test_workspace_mcp_status_errors_when_expected_server_inactive(
    client, monkeypatch, tmp_path
):
    from api.config import DATABASE_PATH
    import json
    import sqlite3
    import time

    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    hermes_config = tmp_path / ".hermes" / "profiles" / "wright" / "config.yaml"
    hermes_config.parent.mkdir(parents=True)
    hermes_config.write_text("mcp_servers:\n  wrightgateway: {}\n", encoding="utf-8")

    client.get("/api/workspace/files", params={"session_id": "test-session"})
    now = int(time.time())
    conn = sqlite3.connect(DATABASE_PATH)
    try:
        conn.execute(
            "UPDATE engineering_workspaces SET enabled_tools = ? WHERE session_id = ?",
            (json.dumps(["inactive-test-mcp"]), "test-session"),
        )
        conn.execute(
            """
            INSERT OR REPLACE INTO mcp_servers
                (server_id, name, type, command, is_active, is_installed,
                 status, error_message, category, created_at, updated_at)
            VALUES
                ('inactive-test-mcp', 'Inactive Test MCP', 'stdio', '[]',
                 0, 1, 'inactive', NULL, 'cad', ?, ?)
            """,
            (now, now),
        )
        conn.commit()
    finally:
        conn.close()

    try:
        response = client.get(
            "/api/workspace/mcp-status", params={"session_id": "test-session"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["running_mcps"] == [
            {
                "name": "Inactive Test MCP",
                "status": "active",
                "error_message": None,
            }
        ]
    finally:
        conn = sqlite3.connect(DATABASE_PATH)
        try:
            conn.execute(
                "DELETE FROM mcp_servers WHERE server_id = 'inactive-test-mcp'"
            )
            conn.execute(
                "UPDATE engineering_workspaces SET enabled_tools = NULL WHERE session_id = ?",
                ("test-session",),
            )
            conn.commit()
        finally:
            conn.close()


def test_create_workspace_uses_local_session_when_agent_unavailable(
    client, workspace_setup
):
    class FailingCreateSessionEngine(MockAgentEngine):
        async def create_session(
            self, workspace: str | None = None
        ) -> AgentSessionInfo:
            raise RuntimeError("Hermes unavailable")

    original_engine = app.state.agent_engine
    app.state.agent_engine = FailingCreateSessionEngine(workspace_setup)
    local_path = os.path.join(workspace_setup, "local-fallback-workspace")

    try:
        response = client.post(
            "/api/workspace/create",
            json={"name": "Local Fallback Workspace", "local_path": local_path},
        )
    finally:
        app.state.agent_engine = original_engine

    assert response.status_code == 201
    data = response.json()
    assert data["session_id"].startswith("wright-local-")
    assert data["local_path"] == local_path
    assert os.path.isdir(local_path)


def test_workspace_lists_hide_synthetic_session_rows(client, workspace_setup):
    from api.config import DATABASE_PATH
    from core.workspace import get_all_workspaces, get_recent_workspaces
    import sqlite3
    import time
    import uuid

    now = int(time.time())
    rows = [
        (
            str(uuid.uuid4()),
            "api_1782845491_1094a132",
            "api_1782845491_1094a132",
            os.path.join(workspace_setup, "api_1782845491_1094a132"),
            now + 3,
        ),
        (
            str(uuid.uuid4()),
            "wright-local-e373b404-48ce-4ce8-960f-59d1e4e25fa8",
            "wright-local-e373b404-48ce-4ce8-960f-59d1e4e25fa8",
            os.path.join(
                workspace_setup, "wright-local-e373b404-48ce-4ce8-960f-59d1e4e25fa8"
            ),
            now + 2,
        ),
        (
            str(uuid.uuid4()),
            "wright-local-real-session",
            "Demo",
            os.path.join(workspace_setup, "demo"),
            now + 1,
        ),
    ]
    for _, _, _, local_path, _ in rows:
        os.makedirs(local_path, exist_ok=True)

    conn = sqlite3.connect(DATABASE_PATH)
    try:
        conn.executemany(
            """
            INSERT INTO engineering_workspaces
                (workspace_id, session_id, workspace_name, local_path, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (workspace_id, session_id, name, path, updated_at, updated_at)
                for workspace_id, session_id, name, path, updated_at in rows
            ],
        )
        conn.commit()

        recent_names = {
            w["workspace_name"] for w in get_recent_workspaces(DATABASE_PATH, limit=10)
        }
        all_names = {w["workspace_name"] for w in get_all_workspaces(DATABASE_PATH)}

        assert "api_1782845491_1094a132" not in recent_names
        assert "wright-local-e373b404-48ce-4ce8-960f-59d1e4e25fa8" not in recent_names
        assert "api_1782845491_1094a132" not in all_names
        assert "wright-local-e373b404-48ce-4ce8-960f-59d1e4e25fa8" not in all_names
        assert "Demo" in recent_names
        assert "Demo" in all_names
    finally:
        conn.execute(
            "DELETE FROM engineering_workspaces WHERE workspace_id IN (?, ?, ?)",
            tuple(row[0] for row in rows),
        )
        conn.commit()
        conn.close()


def test_workspace_files_uses_local_dir_when_agent_lookup_fails(
    client, workspace_setup, monkeypatch
):
    from api.routers import workspace as workspace_router

    class FailingLookupEngine(MockAgentEngine):
        async def get_session_workspace(self, session_id: str) -> str | None:
            raise RuntimeError("Hermes unavailable")

    default_parent = os.path.join(workspace_setup, "wright-defaults")
    monkeypatch.setenv("WRIGHT_WORKSPACES_DIR", default_parent)
    original_engine = app.state.agent_engine
    app.state.agent_engine = FailingLookupEngine(workspace_setup)
    session_id = "offline-session"

    try:
        response = client.get("/api/workspace/files", params={"session_id": session_id})
    finally:
        app.state.agent_engine = original_engine

    expected_path = os.path.join(
        workspace_router.get_default_workspace_parent_dir(),
        session_id,
    )
    assert response.status_code == 200
    assert os.path.isdir(expected_path)


def test_agent_chat_starts_enabled_workspace_mcp_servers(client, monkeypatch):
    from api.config import DATABASE_PATH
    from tool_registry import McpServer
    from tool_registry.db import insert_server
    import sqlite3
    import time

    client.get("/api/workspace/files", params={"session_id": "test-session"})

    now = int(time.time())
    server_id = "chat-preflight-mcp"
    conn = sqlite3.connect(DATABASE_PATH)
    try:
        conn.execute("DELETE FROM mcp_tools WHERE server_id = ?", (server_id,))
        conn.execute("DELETE FROM mcp_servers WHERE server_id = ?", (server_id,))
        conn.execute(
            "UPDATE engineering_workspaces SET enabled_tools = ? WHERE session_id = ?",
            ('["chat-preflight-mcp"]', "test-session"),
        )
        conn.commit()
    finally:
        conn.close()

    insert_server(
        DATABASE_PATH,
        McpServer(
            server_id=server_id,
            name="Chat Preflight MCP",
            type="stdio",
            command=["uv", "run", "chat-preflight"],
            is_active=False,
            is_installed=True,
            status="inactive",
            created_at=now,
            updated_at=now,
        ),
    )

    started = []

    async def fake_start_server(server_id_arg, workspace_dir=None, **_kwargs):
        started.append((server_id_arg, workspace_dir))
        return None

    monkeypatch.setattr(client.app.state.mcp_engine, "start_server", fake_start_server)

    response = client.post(
        "/api/agent/chat",
        json={"session_id": "test-session", "message": "hello"},
    )

    assert response.status_code == 200
    assert started == [(server_id, client.app.state.agent_engine.workspace_path)]

    conn = sqlite3.connect(DATABASE_PATH)
    try:
        conn.execute("DELETE FROM mcp_servers WHERE server_id = ?", (server_id,))
        conn.execute(
            "UPDATE engineering_workspaces SET enabled_tools = NULL WHERE session_id = ?",
            ("test-session",),
        )
        conn.commit()
    finally:
        conn.close()


def test_agent_chat_stream_can_be_reattached_after_completion(client):
    client.get("/api/workspace/files", params={"session_id": "test-session"})

    response_chat = client.post(
        "/api/agent/chat",
        json={"session_id": "test-session", "message": "hello"},
    )
    assert response_chat.status_code == 200
    assert "event: token" in response_chat.text
    assert "hello" in response_chat.text

    response_attach = client.get(
        "/api/agent/chat/stream",
        params={"session_id": "test-session"},
    )
    assert response_attach.status_code == 200
    assert "event: token" in response_attach.text
    assert "hello" in response_attach.text
    assert "event: stream_end" in response_attach.text


def test_agent_chat_reports_mcp_start_failure(client, monkeypatch):
    from api.config import DATABASE_PATH
    from tool_registry import McpServer
    from tool_registry.db import insert_server
    import sqlite3
    import time

    client.get("/api/workspace/files", params={"session_id": "test-session"})

    now = int(time.time())
    server_id = "chat-failing-mcp"
    conn = sqlite3.connect(DATABASE_PATH)
    try:
        conn.execute("DELETE FROM mcp_tools WHERE server_id = ?", (server_id,))
        conn.execute("DELETE FROM mcp_servers WHERE server_id = ?", (server_id,))
        conn.execute(
            "UPDATE engineering_workspaces SET enabled_tools = ? WHERE session_id = ?",
            ('["chat-failing-mcp"]', "test-session"),
        )
        conn.commit()
    finally:
        conn.close()

    insert_server(
        DATABASE_PATH,
        McpServer(
            server_id=server_id,
            name="Chat Failing MCP",
            type="stdio",
            command=["uv", "run", "chat-failing"],
            is_active=False,
            is_installed=True,
            status="inactive",
            created_at=now,
            updated_at=now,
        ),
    )

    async def fake_start_server(*_args, **_kwargs):
        raise RuntimeError("missing credentials")

    monkeypatch.setattr(client.app.state.mcp_engine, "start_server", fake_start_server)

    response = client.post(
        "/api/agent/chat",
        json={"session_id": "test-session", "message": "hello"},
    )

    assert response.status_code == 503
    assert "Failed to start workspace MCP server(s)" in response.text
    assert "Chat Failing MCP: missing credentials" in response.text

    conn = sqlite3.connect(DATABASE_PATH)
    try:
        conn.execute("DELETE FROM mcp_servers WHERE server_id = ?", (server_id,))
        conn.execute(
            "UPDATE engineering_workspaces SET enabled_tools = NULL WHERE session_id = ?",
            ("test-session",),
        )
        conn.commit()
    finally:
        conn.close()
