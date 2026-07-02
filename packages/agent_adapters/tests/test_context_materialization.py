import os
import sqlite3

from agent_adapters import AgentContextMaterializationRequest
from agent_adapters.context import NoOpAgentContextMaterializer
from agent_adapters.hermes_gateway import hermes_context_materializer


def _init_workspace_db(db_path: str, workspace_path: str) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("""
        CREATE TABLE engineering_workspaces (
            workspace_id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL UNIQUE,
            workspace_name TEXT,
            local_path TEXT NOT NULL,
            workspace_prompt TEXT,
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
            instructions TEXT,
            created_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL
        )
        """)
        conn.execute(
            """
            INSERT INTO engineering_workspaces
                (workspace_id, session_id, workspace_name, local_path, workspace_prompt, created_at, updated_at)
            VALUES ('ws1', 'session-1', 'Workspace', ?, 'Use metric units.', 1, 1)
            """,
            (workspace_path,),
        )
        conn.commit()
    finally:
        conn.close()


def test_hermes_materializer_writes_hermes_context_file(tmp_path):
    workspace_path = str(tmp_path / "workspace")
    os.makedirs(workspace_path)
    db_path = str(tmp_path / "workspace.db")
    _init_workspace_db(db_path, workspace_path)

    result = hermes_context_materializer().materialize(
        AgentContextMaterializationRequest(
            db_path=db_path,
            workspace_path=workspace_path,
            workspace_id="ws1",
            session_id="session-1",
        )
    )

    hermes_file = tmp_path / "workspace" / ".hermes.md"
    assert result.provider_id == "hermes"
    assert str(hermes_file) in result.files_written
    assert hermes_file.exists()
    assert "Use metric units." in hermes_file.read_text(encoding="utf-8")


def test_noop_materializer_does_not_write_hermes_files(tmp_path):
    workspace_path = str(tmp_path / "workspace")
    os.makedirs(workspace_path)

    result = NoOpAgentContextMaterializer("openclaw").materialize(
        AgentContextMaterializationRequest(
            db_path=str(tmp_path / "missing.db"),
            workspace_path=workspace_path,
        )
    )

    assert result.provider_id == "openclaw"
    assert result.files_written == ()
    assert not (tmp_path / "workspace" / ".hermes.md").exists()
