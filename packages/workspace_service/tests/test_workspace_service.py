import os
import sqlite3

import pytest

from agent_adapters import AgentSessionInfo
from workspace_service import (
    WorkspaceConflictError,
    WorkspaceInvalidRequestError,
    WorkspaceService,
    default_workspace_parent_dir,
)


class FakeEngine:
    def __init__(self):
        self.sessions: list[AgentSessionInfo] = []

    async def create_session(self, workspace: str | None = None) -> AgentSessionInfo:
        info = AgentSessionInfo(
            session_id=f"session-{len(self.sessions) + 1}",
            title="Fake",
            created_at=1,
            updated_at=1,
            message_count=0,
            workspace=workspace,
        )
        self.sessions.append(info)
        return info

    async def list_sessions(self) -> list[AgentSessionInfo]:
        return list(self.sessions)

    async def get_session_workspace(self, session_id: str) -> str | None:
        for session in self.sessions:
            if session.session_id == session_id:
                return session.workspace
        return None


@pytest.fixture
def db_path(tmp_path):
    path = tmp_path / "workspace.db"
    conn = sqlite3.connect(path)
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
            workspace_prompt TEXT,
            git_large_file_threshold INTEGER,
            enabled_tools TEXT,
            created_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL
        )
        """)
        conn.execute("""
        CREATE TABLE system_settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
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
            instructions TEXT,
            created_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL
        )
        """)
        conn.commit()
    finally:
        conn.close()
    return str(path)


def test_default_workspace_parent_prefers_userprofile():
    assert (
        default_workspace_parent_dir(
            {"USERPROFILE": r"C:\Users\Engineer", "HOME": "/unexpected"}
        )
        == r"C:\Users\Engineer\wright"
    )


@pytest.mark.asyncio
async def test_create_workspace_uses_facade_and_materializes_hermes_context(
    tmp_path, db_path
):
    service = WorkspaceService(db_path, parent_dir_provider=lambda: str(tmp_path))
    workspace_path = str(tmp_path / "phase-two-workspace")

    record = await service.create_workspace(
        "Phase Two Workspace", workspace_path, FakeEngine()
    )

    assert record.workspace_name == "Phase Two Workspace"
    assert record.local_path == workspace_path
    assert os.path.isdir(workspace_path)
    assert os.path.exists(os.path.join(workspace_path, ".hermes.md"))


@pytest.mark.asyncio
async def test_create_workspace_rejects_existing_path(tmp_path, db_path):
    workspace_path = tmp_path / "existing"
    workspace_path.mkdir()
    service = WorkspaceService(db_path)

    with pytest.raises(WorkspaceConflictError):
        await service.create_workspace("Existing", str(workspace_path), FakeEngine())


@pytest.mark.asyncio
async def test_update_config_refreshes_context(tmp_path, db_path):
    service = WorkspaceService(db_path, parent_dir_provider=lambda: str(tmp_path))
    engine = FakeEngine()
    workspace_path = str(tmp_path / "config-workspace")
    record = await service.create_workspace("Config Workspace", workspace_path, engine)

    workspace_id = await service.update_workspace_config(
        record.session_id,
        engine,
        git_remote_url="https://example.invalid/repo.git",
        git_username="engineer",
        workspace_prompt="Always explain assumptions.",
    )

    assert workspace_id == record.workspace_id
    hermes_text = (tmp_path / "config-workspace" / ".hermes.md").read_text(
        encoding="utf-8"
    )
    assert "Always explain assumptions." in hermes_text


@pytest.mark.asyncio
async def test_execute_workspace_file_uses_policy_and_returns_output(tmp_path, db_path):
    service = WorkspaceService(db_path, parent_dir_provider=lambda: str(tmp_path))
    engine = FakeEngine()
    record = await service.create_workspace(
        "Run Workspace", str(tmp_path / "run"), engine
    )
    script = tmp_path / "run" / "hello.py"
    script.write_text("print('hello from service')\n", encoding="utf-8")

    result = await service.execute_workspace_file(
        record.session_id, "/hello.py", engine
    )

    assert result.success is True
    assert result.stdout.strip() == "hello from service"


@pytest.mark.asyncio
async def test_execute_workspace_file_rejects_non_python(tmp_path, db_path):
    service = WorkspaceService(db_path, parent_dir_provider=lambda: str(tmp_path))
    engine = FakeEngine()
    record = await service.create_workspace(
        "Run Workspace", str(tmp_path / "run"), engine
    )
    (tmp_path / "run" / "notes.txt").write_text("hello", encoding="utf-8")

    with pytest.raises(WorkspaceInvalidRequestError):
        await service.execute_workspace_file(record.session_id, "/notes.txt", engine)
