import os
import sqlite3

import pytest

from agent_adapters import AgentSessionInfo, NoOpAgentContextMaterializer
from workspace_service import WorkspaceService


class ExistingSessionEngine:
    def __init__(self, workspace_path: str):
        self.workspace_path = workspace_path

    async def list_sessions(self):
        return [
            AgentSessionInfo(
                session_id="openclaw-session",
                title="OpenClaw Stub",
                created_at=1,
                updated_at=2,
                message_count=0,
                workspace=self.workspace_path,
            )
        ]

    async def create_session(self, workspace: str | None = None):
        raise AssertionError("activation should not create a fallback session")

    async def get_session_workspace(self, session_id: str):
        return self.workspace_path


@pytest.mark.asyncio
async def test_non_hermes_activation_does_not_write_hermes_files(tmp_path):
    db_path = str(tmp_path / "workspace.db")
    workspace_path = str(tmp_path / "workspace")
    os.makedirs(workspace_path)
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("""
        CREATE TABLE engineering_workspaces (
            workspace_id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL UNIQUE,
            workspace_name TEXT,
            local_path TEXT NOT NULL,
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
        conn.execute(
            """
            INSERT INTO engineering_workspaces
                (workspace_id, session_id, workspace_name, local_path, created_at, updated_at)
            VALUES ('ws-openclaw', 'openclaw-session', 'OpenClaw Workspace', ?, 1, 1)
            """,
            (workspace_path,),
        )
        conn.commit()
    finally:
        conn.close()

    service = WorkspaceService(
        db_path,
        materializers={
            "openclaw": NoOpAgentContextMaterializer(
                provider_id="openclaw", support_level="stub"
            )
        },
    )

    activation = await service.activate_workspace(
        "openclaw-session",
        ExistingSessionEngine(workspace_path),
        agent_id="openclaw",
    )

    assert activation.success is True
    assert activation.context.provider_id == "openclaw"
    assert activation.context.files_written == ()
    assert not (tmp_path / "workspace" / ".hermes.md").exists()
