import sqlite3
from pathlib import Path

import yaml

from agent_adapters.openclaw import openclaw_wright_gateway_profile
from api.services import hermes_sync
from api.services import wright_gateway_sync
from workspace_service.adapters.runtime import associate_workspace_session


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


def test_static_hermes_config_uses_installed_native_gateway(tmp_path, monkeypatch):
    hermes_root = tmp_path / ".hermes"
    workspace_root = tmp_path / "workspaces"
    monkeypatch.setenv("WRIGHT_NATIVE_RUNTIME", "1")
    monkeypatch.setenv("WRIGHT_WORKSPACE_ROOT", str(workspace_root))
    monkeypatch.setenv("HERMES_HOME", str(hermes_root))
    monkeypatch.delenv("LOCALAPPDATA", raising=False)
    monkeypatch.delenv("HERMES_CONFIG_PATH", raising=False)
    monkeypatch.delenv("HERMES_PROFILE", raising=False)

    changed = hermes_sync._write_static_hermes_config()

    assert changed is True

    config_path = hermes_root / "profiles" / "wright" / "config.yaml"
    config = yaml.safe_load(config_path.read_text())
    gateway = config["mcp_servers"]["wrightgateway"]

    assert gateway["args"] == [
        "-m",
        "wright_engineering.cli",
        "mcp",
        "serve",
        "--stdio",
        "--workspace",
        str(workspace_root),
        "--session-id",
        "wright-native",
        "--workspace-id",
        "wright-native",
    ]
    assert gateway["command"] != "uv"
    assert config["terminal"]["cwd"] == str(workspace_root)


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


def test_gateway_config_writer_preserves_operator_runtime_fields(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        yaml.safe_dump(
            {
                "mcp_servers": {
                    "wrightgateway": {
                        "command": "stale-command",
                        "args": ["stale-argument"],
                        "env": {
                            "WRIGHT_MCP_TIMEOUT": "130",
                            "WRIGHT_MCP_MAX_TIMEOUT": "180",
                        },
                        "enabled": True,
                        "tools": {"include": ["wright__workspace_status"]},
                        "timeout": 180,
                        "connect_timeout": 30,
                        "url": "https://stale.invalid/mcp",
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    profile = wright_gateway_sync.default_hermes_gateway_profile("/workspace")

    changed = wright_gateway_sync.write_gateway_profile_config(
        profile, [str(config_path)]
    )

    assert changed is True
    gateway = yaml.safe_load(config_path.read_text())["mcp_servers"]["wrightgateway"]
    assert gateway == {
        "command": "uv",
        "args": profile.args,
        "env": {
            "WRIGHT_MCP_TIMEOUT": "130",
            "WRIGHT_MCP_MAX_TIMEOUT": "180",
        },
        "enabled": True,
        "tools": {"include": ["wright__workspace_status"]},
        "timeout": 180,
        "connect_timeout": 30,
    }


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


def test_workspace_sync_writes_exact_gateway_binding(tmp_path):
    workspace_path = tmp_path / "workspace"
    workspace_path.mkdir()
    db_path = _create_workspace_context_db(tmp_path, workspace_path)
    config_path = tmp_path / "config.yaml"

    changed = wright_gateway_sync.sync_workspace_tools_to_wright_gateway(
        "session1",
        db_path,
        profile=wright_gateway_sync.default_hermes_gateway_profile("/wright"),
        config_paths=[str(config_path)],
    )

    assert changed is True
    gateway = yaml.safe_load(config_path.read_text())["mcp_servers"]["wrightgateway"]
    assert gateway["args"][-7:] == [
        "api.gateway_stdio",
        "--session-id",
        "session1",
        "--workspace-id",
        "ws1",
        "--principal-id",
        "local-admin",
    ]
    config = yaml.safe_load(config_path.read_text())
    assert config["terminal"]["cwd"] == str(workspace_path)
    assert gateway["args"][2] == "/wright"


def test_workspace_sync_rejects_wright_application_source(tmp_path):
    application_root = Path(__file__).resolve().parents[3]
    db_path = _create_workspace_context_db(tmp_path, application_root)
    config_path = tmp_path / "config.yaml"

    changed = wright_gateway_sync.sync_workspace_tools_to_wright_gateway(
        "session1",
        db_path,
        profile=wright_gateway_sync.default_hermes_gateway_profile("/wright"),
        config_paths=[str(config_path)],
    )

    assert changed is False
    assert not config_path.exists()


def test_workspace_sync_reuses_binding_for_another_session_in_same_workspace(tmp_path):
    workspace_path = tmp_path / "workspace"
    workspace_path.mkdir()
    db_path = _create_workspace_context_db(tmp_path, workspace_path)
    config_path = tmp_path / "config.yaml"
    profile = wright_gateway_sync.default_hermes_gateway_profile("/wright")

    assert (
        wright_gateway_sync.sync_workspace_tools_to_wright_gateway(
            "session1",
            db_path,
            profile=profile,
            config_paths=[str(config_path)],
        )
        is True
    )
    associate_workspace_session(db_path, "ws1", "session2")

    changed = wright_gateway_sync.sync_workspace_tools_to_wright_gateway(
        "session2",
        db_path,
        profile=profile,
        config_paths=[str(config_path)],
    )

    assert changed is False
    gateway = yaml.safe_load(config_path.read_text())["mcp_servers"]["wrightgateway"]
    assert gateway["args"][-7:] == [
        "api.gateway_stdio",
        "--session-id",
        "session1",
        "--workspace-id",
        "ws1",
        "--principal-id",
        "local-admin",
    ]
    config = yaml.safe_load(config_path.read_text())
    assert config["terminal"]["cwd"] == str(workspace_path)
    assert gateway["args"][2] == "/wright"
