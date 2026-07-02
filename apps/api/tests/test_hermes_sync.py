import sqlite3

import yaml

from agent_adapters.openclaw import openclaw_wright_gateway_profile
from api.services import hermes_sync
from api.services import wright_gateway_sync


def _create_workspace_context_db(tmp_path, local_path):
    db_path = str(tmp_path / "workspace-context.db")
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("""
        CREATE TABLE engineering_workspaces (
            workspace_id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL UNIQUE,
            workspace_name TEXT,
            local_path TEXT NOT NULL,
            enabled_tools TEXT,
            workspace_prompt TEXT,
            created_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL
        )
        """)
        conn.execute("""
        CREATE TABLE mcp_servers (
            server_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            is_installed INTEGER NOT NULL DEFAULT 0,
            instructions TEXT,
            created_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL
        )
        """)
        conn.execute(
            """
            INSERT INTO engineering_workspaces (
                workspace_id, session_id, workspace_name, local_path, enabled_tools,
                workspace_prompt, created_at, updated_at
            ) VALUES ('ws1', 'session1', 'Workspace', ?, NULL, 'Use the bench.', 1000, 1000)
            """,
            (str(local_path),),
        )
        conn.execute(
            """
            INSERT INTO mcp_servers (
                server_id, name, type, is_installed, instructions, created_at, updated_at
            ) VALUES ('mcp1', 'Test MCP', 'stdio', 1, 'Follow MCP instructions.', 1000, 1000)
            """
        )
        conn.commit()
    finally:
        conn.close()
    return db_path


def test_static_hermes_config_uses_runtime_repo_dir(tmp_path, monkeypatch):
    hermes_root = tmp_path / ".hermes"

    def fake_expanduser(path: str) -> str:
        return path.replace("~/.hermes", str(hermes_root))

    monkeypatch.setenv("WRIGHT_REPO_DIR", "/workspace")
    monkeypatch.setattr(hermes_sync.os.path, "expanduser", fake_expanduser)

    changed = hermes_sync._write_static_hermes_config()

    assert changed is True

    config_path = hermes_root / "profiles" / "wright" / "config.yaml"
    config = yaml.safe_load(config_path.read_text())
    gateway = config["mcp_servers"]["wrightgateway"]

    assert gateway["args"] == [
        "run",
        "--project",
        "/workspace",
        "python",
        "-m",
        "tool_registry.gateway",
    ]
    assert config["terminal"]["cwd"] == "/workspace"


def test_generic_wright_gateway_config_writer_uses_profile(tmp_path):
    config_path = tmp_path / "config.yaml"
    profile = wright_gateway_sync.default_hermes_gateway_profile("/workspace")

    changed = wright_gateway_sync.write_gateway_profile_config(
        profile, [str(config_path)]
    )

    assert changed is True
    config = yaml.safe_load(config_path.read_text())
    assert config["mcp_servers"]["wrightgateway"] == profile.mcp_server_config()
    assert config["terminal"] == {"cwd": "/workspace"}


def test_workspace_gateway_context_uses_profile_filename(tmp_path):
    workspace_path = tmp_path / "workspace"
    workspace_path.mkdir()
    db_path = _create_workspace_context_db(tmp_path, workspace_path)
    hermes_profile = wright_gateway_sync.default_hermes_gateway_profile("/workspace")

    wright_gateway_sync.write_workspace_gateway_context(
        db_path, str(workspace_path), hermes_profile
    )

    context_path = workspace_path / ".hermes.md"
    assert context_path.exists()
    assert "Follow MCP instructions." in context_path.read_text(encoding="utf-8")

    existing_files = {path.name for path in workspace_path.iterdir()}
    wright_gateway_sync.write_workspace_gateway_context(
        db_path, str(workspace_path), openclaw_wright_gateway_profile("/workspace")
    )

    assert {path.name for path in workspace_path.iterdir()} == existing_files
