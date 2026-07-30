from __future__ import annotations

import sqlite3
import json

from data_vault import upgrade_database
from tool_registry.catalog_reconcile import (
    reconcile_engineering_catalog,
    reconcile_installed_bundle,
)
from tool_registry import catalog_reconcile


def test_schema_upgrade_does_not_seed_or_mutate_catalog_rows(tmp_path):
    database = tmp_path / "state.db"

    upgrade_database(database)

    with sqlite3.connect(database) as connection:
        assert connection.execute("SELECT COUNT(*) FROM mcp_servers").fetchone() == (0,)


def test_reconcile_seeds_catalog_and_preserves_unknown_server(tmp_path):
    database = tmp_path / "state.db"
    upgrade_database(database)
    with sqlite3.connect(database) as connection:
        connection.execute(
            """INSERT INTO mcp_servers (
                server_id, name, type, command, created_at, updated_at
            ) VALUES ('user-owned', 'User Owned', 'stdio', 'custom', 1, 1)"""
        )
        connection.commit()

    count = reconcile_engineering_catalog(str(database))

    with sqlite3.connect(database) as connection:
        assert connection.execute(
            "SELECT name FROM mcp_servers WHERE server_id='user-owned'"
        ).fetchone() == ("User Owned",)
        assert connection.execute("SELECT COUNT(*) FROM mcp_servers").fetchone()[0] == (
            count + 1
        )


def test_reconcile_resets_only_failed_wright_catalog_install(tmp_path):
    database = tmp_path / "state.db"
    upgrade_database(database)
    reconcile_engineering_catalog(str(database))
    with sqlite3.connect(database) as connection:
        connection.execute(
            """UPDATE mcp_servers SET is_installed=1, is_active=1, status='error',
                error_message='missing' WHERE server_id='openscad-mcp-server'"""
        )
        connection.commit()

    reconcile_engineering_catalog(str(database))

    with sqlite3.connect(database) as connection:
        assert connection.execute(
            """SELECT is_installed, is_active, status, error_message
            FROM mcp_servers WHERE server_id='openscad-mcp-server'"""
        ).fetchone() == (0, 0, "inactive", None)


def test_reconcile_persists_trusted_launch_environment(tmp_path, monkeypatch):
    database = tmp_path / "state.db"
    upgrade_database(database)
    entry = {
        "server_id": "workspace-aware",
        "name": "Workspace Aware",
        "type": "stdio",
        "command": json.dumps(["server"]),
        "category": "cad",
        "description": "Synthetic server",
        "launch_env": json.dumps({"SERVER_WORKSPACE": "{workspace.path}"}),
        "verification_state": "verified_mcp",
        "installability_tier": "tested",
        "risk_level": "low",
        "deployment_mode": "local-only",
        "platform_support": {},
        "host_software_required": [],
        "credentials_required": [],
        "default_enabled": True,
        "approval_gates": [],
        "validation_result": {},
    }
    monkeypatch.setattr(catalog_reconcile, "ENGINEERING_CATALOG", [entry])

    reconcile_engineering_catalog(str(database))

    with sqlite3.connect(database) as connection:
        launch_env = connection.execute(
            "SELECT launch_env FROM mcp_servers WHERE server_id='workspace-aware'"
        ).fetchone()[0]
    assert json.loads(launch_env) == {"SERVER_WORKSPACE": "{workspace.path}"}


def test_installed_bundle_reconcile_noops_without_status_file(tmp_path):
    database = tmp_path / "state.db"
    upgrade_database(database)

    assert (
        reconcile_installed_bundle(str(database), status_path=tmp_path / "missing.json")
        == 0
    )

    with sqlite3.connect(database) as connection:
        assert connection.execute("SELECT COUNT(*) FROM mcp_servers").fetchone() == (0,)


def test_installed_bundle_reconcile_marks_local_servers_installed(tmp_path):
    database = tmp_path / "state.db"
    upgrade_database(database)
    bundle = tmp_path / "mcp-bundle.yaml"
    status = tmp_path / "mcp-bundle-status.json"
    config = tmp_path / "hermes-mcp.generated.yaml"
    bundle.write_text(
        """
bundle_id: wright-mcp-appliance-linux-arm64
applications:
  - id: openscad
    display_name: OpenSCAD
    category: code-cad
mcp_servers:
  - id: openscad-mcp
    display_name: OpenSCAD MCP
    application_id: openscad
    docs_summary: OpenSCAD server bundled for tests.
    mcp_source:
      type: git
      url: https://example.test/openscad-mcp.git
      ref: abc123
    workspace_binding:
      env:
        OPENSCAD_WORKSPACE: "{workspace.path}"
  - id: remote-only-mcp
    display_name: Remote MCP
""",
        encoding="utf-8",
    )
    status.write_text(
        json.dumps(
            {
                "bundle_id": "wright-mcp-appliance-linux-arm64",
                "mcp_servers": [
                    {
                        "id": "openscad-mcp",
                        "display_name": "OpenSCAD MCP",
                        "application_id": "openscad",
                        "availability": "local_enabled",
                        "status": "accepted",
                    },
                    {
                        "id": "remote-only-mcp",
                        "display_name": "Remote MCP",
                        "application_id": None,
                        "availability": "remote_only",
                        "status": "remote_only",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    config.write_text(
        """
mcp_servers:
  openscad-mcp:
    command: /opt/wright/mcp/bin/openscad-mcp
    args:
      - --stdio
    env:
      OPENSCAD_PATH: /usr/bin/openscad
""",
        encoding="utf-8",
    )

    count = reconcile_installed_bundle(
        str(database), bundle_path=bundle, status_path=status, config_path=config
    )

    assert count == 1
    with sqlite3.connect(database) as connection:
        row = connection.execute(
            """SELECT name, command, is_installed, is_active, status, category,
                      source_url, installed_version, env_vars, launch_env,
                      verification_state, installability_tier, deployment_mode,
                      platform_support
               FROM mcp_servers WHERE server_id='openscad-mcp'"""
        ).fetchone()
    assert row is not None
    assert row[0] == "OpenSCAD MCP"
    assert json.loads(row[1]) == ["/opt/wright/mcp/bin/openscad-mcp", "--stdio"]
    assert row[2:6] == (1, 0, "inactive", "cad")
    assert row[6] == "https://example.test/openscad-mcp.git"
    assert row[7] == "abc123"
    assert json.loads(row[8]) == {"OPENSCAD_PATH": "/usr/bin/openscad"}
    assert json.loads(row[9]) == {"OPENSCAD_WORKSPACE": "{workspace.path}"}
    assert row[10:13] == ("verified_mcp", "tested", "local-bundled")
    assert json.loads(row[13])["linux_arm64"]["status"] == "yes"
