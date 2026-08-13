from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime

import pytest
from core.secrets import configure_default_secret_provider
from data_vault import upgrade_database
from data_vault.secret_provider import (
    FileSecretProvider,
    create_default_secret_provider,
)
from tool_registry.catalog_reconcile import reconcile_engineering_catalog_document
from tool_registry.catalog_signing import CatalogTrustRoot
from tool_registry.catalog_snapshots import (
    bootstrap_bundled_snapshot,
    get_catalog_state,
    load_active_catalog,
)
from tool_registry.catalog_updates import (
    activate_catalog_update,
    preview_catalog_update,
    rollback_catalog,
)
from tool_registry.secrets import read_secrets, write_secrets
from catalog_update_fixtures import (
    TEST_KEY_ID,
    TEST_PUBLIC_KEY,
    candidate_70_catalog,
    prior_69_catalog,
    signed_catalog,
)

NOW = datetime(2026, 8, 12, 12, 0, tzinfo=UTC)
ROOT = CatalogTrustRoot("test", TEST_KEY_ID, TEST_PUBLIC_KEY)


def _prepare(database, secret_path) -> dict:
    upgrade_database(database)
    prior = prior_69_catalog()
    bundled = bootstrap_bundled_snapshot(database, payload=prior)
    reconcile_engineering_catalog_document(str(database), prior)
    configure_default_secret_provider(lambda: FileSecretProvider(secret_path))
    write_secrets("jarvis-onshape-mcp", {"ONSHAPE_ACCESS_KEY": "sentinel"})
    with sqlite3.connect(database) as connection:
        connection.execute(
            """UPDATE mcp_servers SET is_installed=1, is_active=0,
                      status='inactive', installed_version='1.2.0'
               WHERE server_id='jarvis-onshape-mcp'"""
        )
        connection.execute(
            """INSERT INTO mcp_servers (
                server_id, name, type, command, is_active, is_installed,
                status, category, created_at, updated_at
            ) VALUES ('custom-sentinel', 'Custom Sentinel', 'stdio',
                      '["custom-command"]', 0, 0, 'inactive', 'cad', 1, 1)"""
        )
        connection.execute(
            """INSERT INTO engineering_workspaces (
                workspace_id, session_id, local_path, enabled_tools,
                created_at, updated_at, workspace_name
            ) VALUES ('workspace-sentinel', 'session-sentinel', 'D:/safe/workspace',
                      ?, 1, 1, 'Sentinel Workspace')""",
            (json.dumps(["jarvis-onshape-mcp"]),),
        )
    return {"bundled": bundled, "prior": prior}


def _preview(database) -> dict:
    return preview_catalog_update(
        database,
        signed_catalog(candidate_70_catalog(), issued_at=NOW),
        trust_root=ROOT,
        actor="admin-a",
        now=NOW,
        trace_id="trace-preview",
    )


def test_prior_69_activates_signed_onshape_70_survives_restart_and_rolls_back(
    tmp_path,
) -> None:
    database = tmp_path / "state.db"
    secret_path = tmp_path / "secrets.json"
    prepared = _prepare(database, secret_path)
    try:
        preview = _preview(database)
        result = activate_catalog_update(
            database,
            preview["preview_id"],
            preview["preview_digest"],
            actor="admin-a",
            now=NOW,
            trace_id="trace-activate",
        )

        assert result["reconciled"] == 70
        assert result["preserved_user_state"] is True
        state = get_catalog_state(database)
        assert state["active_snapshot_id"] == preview["candidate_snapshot_id"]
        assert state["previous_snapshot_id"] == prepared["bundled"].snapshot_id
        active, diagnostic = load_active_catalog(database)
        assert diagnostic is None
        assert len(active["servers"]) == 70
        assert any(
            entry["id"] == "onshape-labs-featurescript-mcp"
            for entry in active["servers"]
        )

        with sqlite3.connect(database) as connection:
            custom = connection.execute(
                """SELECT name, command FROM mcp_servers
                   WHERE server_id='custom-sentinel'"""
            ).fetchone()
            installed = connection.execute(
                """SELECT is_installed, is_active, status, installed_version
                   FROM mcp_servers WHERE server_id='jarvis-onshape-mcp'"""
            ).fetchone()
            workspace = connection.execute(
                """SELECT enabled_tools FROM engineering_workspaces
                   WHERE workspace_id='workspace-sentinel'"""
            ).fetchone()
        assert custom == ("Custom Sentinel", '["custom-command"]')
        assert installed == (1, 0, "inactive", "1.2.0")
        assert json.loads(workspace[0]) == ["jarvis-onshape-mcp"]
        assert read_secrets("jarvis-onshape-mcp") == {"ONSHAPE_ACCESS_KEY": "sentinel"}

        rolled_back = rollback_catalog(
            database,
            expected_active_snapshot_id=state["active_snapshot_id"],
            expected_previous_snapshot_id=state["previous_snapshot_id"],
            actor="admin-a",
            now=NOW,
            trace_id="trace-rollback",
        )
        assert rolled_back["preserved_user_state"] is True
        restored, diagnostic = load_active_catalog(database)
        assert diagnostic is None
        assert len(restored["servers"]) == 69
        assert not any(
            entry["id"] == "onshape-labs-featurescript-mcp"
            for entry in restored["servers"]
        )
        assert read_secrets("jarvis-onshape-mcp")["ONSHAPE_ACCESS_KEY"] == "sentinel"
    finally:
        configure_default_secret_provider(create_default_secret_provider)


def test_interrupted_activation_rolls_back_reconcile_pointer_and_audit(
    tmp_path,
) -> None:
    database = tmp_path / "state.db"
    secret_path = tmp_path / "secrets.json"
    prepared = _prepare(database, secret_path)
    preview = _preview(database)

    def interrupt(stage: str) -> None:
        if stage == "after_reconcile":
            raise RuntimeError("simulated interruption")

    try:
        with pytest.raises(RuntimeError, match="simulated interruption"):
            activate_catalog_update(
                database,
                preview["preview_id"],
                preview["preview_digest"],
                actor="admin-a",
                now=NOW,
                trace_id="trace-interrupt",
                fault=interrupt,
            )

        state = get_catalog_state(database)
        assert state["active_snapshot_id"] == prepared["bundled"].snapshot_id
        with sqlite3.connect(database) as connection:
            assert connection.execute(
                """SELECT COUNT(*) FROM mcp_servers
                   WHERE server_id='onshape-labs-featurescript-mcp'"""
            ).fetchone() == (0,)
            assert connection.execute(
                """SELECT COUNT(*) FROM catalog_activations
                   WHERE trace_id='trace-interrupt'"""
            ).fetchone() == (0,)
    finally:
        configure_default_secret_provider(create_default_secret_provider)
