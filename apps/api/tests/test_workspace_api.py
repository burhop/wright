import os
import tempfile
import pytest
from fastapi.testclient import TestClient
from api.main import app
from agent_adapters import (
    BaseAgentEngine,
    AgentSessionInfo,
    AgentChatRequest,
    AgentChatStartResponse,
    AgentStreamEvent,
)
from typing import AsyncIterator


# Mock Agent Engine to return a temporary workspace path
class MockAgentEngine(BaseAgentEngine):
    def __init__(self, workspace_path: str):
        self.workspace_path = workspace_path

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
                title="Test Session",
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

    async def start_chat(self, request: AgentChatRequest) -> AgentChatStartResponse:
        return AgentChatStartResponse(
            stream_id="stream-1", session_id=request.session_id
        )

    async def stream_response(self, stream_id: str) -> AsyncIterator[AgentStreamEvent]:
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
            "DELETE FROM engineering_workspaces WHERE session_id = 'test-session'"
        )
        conn.commit()
        conn.close()
    except Exception:
        pass

    mock_engine = MockAgentEngine(workspace_setup)
    app.state.agent_engine = mock_engine
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
            shutil.rmtree(clone_dir)

    finally:
        shutil.rmtree(remote_dir)


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

    # Verify the updated session ID in config
    response_config = client.get("/api/workspace/by-id/" + workspace_id)
    assert response_config.json()["session_id"] == "new-test-session"


def test_agent_sessions_filtering_by_workspace(client):
    # Ensure test-session exists
    client.get("/api/workspace/files", params={"session_id": "test-session"})

    # Get the workspace config to get workspace_id
    response = client.get(
        "/api/workspace/config", params={"session_id": "test-session"}
    )
    workspace_id = response.json()["workspace_id"]

    # Retrieve sessions with workspace_id query parameter
    response_sessions = client.get("/api/agent/sessions", params={"workspace_id": workspace_id})
    assert response_sessions.status_code == 200
    sessions = response_sessions.json()["sessions"]
    # Our MockAgentEngine lists test-session and mock-session under workspace_setup, so both should match
    assert len(sessions) == 2
    assert {s["session_id"] for s in sessions} == {"test-session", "mock-session"}

    # Query with a non-existent workspace_id, should return empty sessions
    response_empty = client.get("/api/agent/sessions", params={"workspace_id": "non-existent-workspace-uuid"})
    assert response_empty.status_code == 200
    assert len(response_empty.json()["sessions"]) == 0


def test_workspace_activate_session_fallback(client):
    from api.config import DATABASE_PATH
    from core.workspace import create_workspace
    import os
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
    manager = WorkspaceManager(workspace_dir)
    
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
    import json

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
    assert compile_workspace_mcp_instructions(db_path, "/my/workspace") is None


def test_workspace_sanitize_path_local_vs_system_tmp(tmp_path):
    from core.workspace import WorkspaceManager
    import os
    import tempfile

    # Set up local workspace directory
    workspace_dir = str(tmp_path / "local_workspace")
    os.makedirs(workspace_dir, exist_ok=True)
    manager = WorkspaceManager(workspace_dir)

    # 1. Create a file in local workspace's tmp folder
    local_tmp_dir = os.path.join(workspace_dir, "tmp", "openscad-mcp")
    os.makedirs(local_tmp_dir, exist_ok=True)
    local_file_path = os.path.join(local_tmp_dir, "test.scad")
    with open(local_file_path, "w") as f:
        f.write("local content")

    # Verify that requesting "tmp/openscad-mcp/test.scad" resolves to the local path
    resolved_local = manager.sanitize_path("tmp/openscad-mcp/test.scad")
    assert resolved_local == local_file_path

    # Verify that requesting "/tmp/openscad-mcp/test.scad" resolves to the local path
    resolved_local_slash = manager.sanitize_path("/tmp/openscad-mcp/test.scad")
    assert resolved_local_slash == local_file_path

    # 2. Check system-wide fallback. We will use a tempfile in the real /tmp directory.
    with tempfile.NamedTemporaryFile(dir="/tmp", prefix="global_test_", suffix=".scad", delete=False) as temp_global:
        temp_global.write(b"global content")
        global_path = temp_global.name

    try:
        # Requesting the global absolute path should resolve to the global path
        resolved_global = manager.sanitize_path(global_path)
        assert resolved_global == global_path
    finally:
        os.unlink(global_path)

    # 3. For a file that does not exist anywhere, requesting it should default to local
    nonexistent_path = "tmp/openscad-mcp/nonexistent.scad"
    resolved_nonexistent = manager.sanitize_path(nonexistent_path)
    expected_local = os.path.abspath(os.path.join(workspace_dir, nonexistent_path))
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
    
    # Activate workspace - this should trigger creating a fallback session and writing .hermes.md
    session_id = asyncio.run(
        activate_workspace(db_path, "missing-session", local_path, engine)
    )

    assert session_id == "new-fallback-session"
    assert len(engine.created_sessions) == 1
    workspace_path, instructions = engine.created_sessions[0]
    assert workspace_path == local_path
    assert instructions is None  # Handled via file instead

    # Verify .hermes.md was written
    hermes_md_path = os.path.join(local_path, ".hermes.md")
    assert os.path.exists(hermes_md_path)
    with open(hermes_md_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "<!-- WRIGHT MCP INSTRUCTIONS START -->" in content
    assert "My test instructions" in content
    assert "<!-- WRIGHT MCP INSTRUCTIONS END -->" in content


def test_write_workspace_hermes_md(tmp_path):
    from core.workspace import write_workspace_hermes_md, create_workspace
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
        conn.execute("UPDATE mcp_servers SET instructions = 'Updated instructions' WHERE server_id = 'mcp1'")
        conn.commit()
    finally:
        conn.close()

    write_workspace_hermes_md(db_path, local_path)
    with open(hermes_md_path, "r", encoding="utf-8") as f:
        new_content = f.read()

    assert "Rule 1: Always do X." in new_content
    assert "Updated instructions" in new_content
    assert "My test instructions" not in new_content





