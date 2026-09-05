from __future__ import annotations

import sqlite3

import pytest

from data_vault.migrations import (
    LEDGER_TABLE,
    MIGRATIONS,
    database_status,
    upgrade_database,
)
from data_vault.models import DatabaseCompatibilityError, DatabaseIntegrityError

from fixtures import corrupt_database, create_partial_legacy_database


def test_fresh_database_applies_numbered_migrations_in_order(tmp_path):
    path = tmp_path / "fresh.db"

    result = upgrade_database(path)
    status = database_status(path)

    assert result.starting_version == 0
    assert result.ending_version == len(MIGRATIONS)
    assert [item["version"] for item in result.applied] == list(
        range(1, len(MIGRATIONS) + 1)
    )
    assert status.ready is True
    assert status.pending == ()
    with sqlite3.connect(path) as connection:
        entries = connection.execute(
            f"SELECT version, name, checksum FROM {LEDGER_TABLE} ORDER BY version"
        ).fetchall()
    assert entries == [
        (migration.version, migration.name, migration.checksum)
        for migration in MIGRATIONS
    ]


def test_partial_legacy_database_is_adopted_without_losing_records(tmp_path):
    path = create_partial_legacy_database(tmp_path / "legacy.db")

    upgrade_database(path)

    with sqlite3.connect(path) as connection:
        assert connection.execute(
            "SELECT name FROM mcp_servers WHERE server_id='custom-user-server'"
        ).fetchone() == ("Custom User Server",)
        assert connection.execute(
            "SELECT local_path FROM engineering_workspaces WHERE workspace_id='workspace-one'"
        ).fetchone() == ("/workspace/one",)
        assert connection.execute(
            "SELECT session_id FROM workspace_agent_sessions WHERE workspace_id='workspace-one'"
        ).fetchone() == ("session-one",)


def test_upgrade_is_idempotent(tmp_path):
    path = tmp_path / "state.db"
    upgrade_database(path)

    second = upgrade_database(path)

    assert second.applied == ()
    assert second.starting_version == second.ending_version == len(MIGRATIONS)


def test_workflow_review_migration_preserves_prior_workflow_metadata(tmp_path):
    path = tmp_path / "workflow-review.db"
    upgrade_database(path, migrations=MIGRATIONS[:10])
    with sqlite3.connect(path) as connection:
        connection.execute(
            """INSERT INTO engineering_workspaces
            (workspace_id, session_id, local_path, created_at, updated_at)
            VALUES ('workspace', 'session', 'D:/workspace', 1, 1)"""
        )
        connection.execute(
            """INSERT INTO workspace_workflows
            (workspace_id, workflow_id, slug, revision, digest, state, updated_at)
            VALUES ('workspace', 'workflow', 'sample', 1, 'digest', 'active', 1)"""
        )
        connection.commit()

    result = upgrade_database(path)

    assert result.applied == (
        {"version": 11, "name": "workspace_workflow_reviews"},
        {"version": 12, "name": "workspace_workflow_runs"},
        {"version": 13, "name": "capability_library_onboarding"},
        {"version": 14, "name": "rivet_workspace_mcp_gateway"},
        {"version": 15, "name": "rivet_engineering_scenario_reports"},
        {"version": 16, "name": "local_engineering_model_library"},
        {"version": 17, "name": "native_engineering_processes"},
    )
    with sqlite3.connect(path) as connection:
        assert connection.execute(
            "SELECT slug FROM workspace_workflows"
        ).fetchone() == ("sample",)
        assert connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='workspace_workflow_reviews'"
        ).fetchone() == ("workspace_workflow_reviews",)


def test_provider_neutral_mcp_columns_are_added_without_losing_rows(tmp_path):
    path = tmp_path / "pre-provider-neutral.db"
    upgrade_database(path, migrations=MIGRATIONS[:4])
    with sqlite3.connect(path) as connection:
        connection.execute(
            """INSERT INTO mcp_servers
            (server_id, name, type, command, created_at, updated_at)
            VALUES ('existing', 'Existing', 'stdio', '[\"server\"]', 1, 1)"""
        )
        connection.execute(
            """INSERT INTO mcp_tools
            (tool_id, server_id, name, input_schema, created_at)
            VALUES ('existing:tool', 'existing', 'tool', '{}', 1)"""
        )
        connection.commit()

    result = upgrade_database(path, migrations=MIGRATIONS[:5])

    assert result.applied == ({"version": 5, "name": "provider_neutral_mcp_contract"},)
    with sqlite3.connect(path) as connection:
        server = connection.execute(
            "SELECT name, launch_env FROM mcp_servers WHERE server_id='existing'"
        ).fetchone()
        tool = connection.execute(
            """SELECT name, title, output_schema, annotations FROM mcp_tools
            WHERE tool_id='existing:tool'"""
        ).fetchone()
    assert server == ("Existing", None)
    assert tool == ("tool", None, None, None)


def test_capability_library_migration_is_additive_and_complete(tmp_path):
    path = tmp_path / "capability-library.db"
    upgrade_database(path, migrations=MIGRATIONS[:12])
    with sqlite3.connect(path) as connection:
        connection.execute(
            """INSERT INTO mcp_servers
            (server_id, name, type, command, is_active, is_installed, status,
             created_at, updated_at)
            VALUES ('custom', 'Custom', 'stdio', '[\"custom\"]', 0, 1,
                    'inactive', 1, 1)"""
        )
        connection.commit()

    result = upgrade_database(path)

    assert result.applied == (
        {"version": 13, "name": "capability_library_onboarding"},
        {"version": 14, "name": "rivet_workspace_mcp_gateway"},
        {"version": 15, "name": "rivet_engineering_scenario_reports"},
        {"version": 16, "name": "local_engineering_model_library"},
        {"version": 17, "name": "native_engineering_processes"},
    )
    with sqlite3.connect(path) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        columns = {
            row[1] for row in connection.execute("PRAGMA table_info(mcp_servers)")
        }
        assert {
            "catalog_snapshots",
            "catalog_state",
            "catalog_update_previews",
            "catalog_activations",
            "machine_compatibility_observations",
            "mcp_install_plans",
            "mcp_onboarding_runs",
            "mcp_validation_evidence",
            "missing_capability_reports",
        }.issubset(tables)
        assert "transport_variant" in columns
        assert connection.execute(
            "SELECT is_installed, is_active FROM mcp_servers WHERE server_id='custom'"
        ).fetchone() == (1, 0)


def test_capability_library_state_enforces_singleton_and_snapshot_references(tmp_path):
    path = tmp_path / "capability-library-state.db"
    upgrade_database(path)
    with sqlite3.connect(path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """INSERT INTO catalog_state
                (state_id, active_snapshot_id, active_generation, updated_at,
                 updated_by) VALUES (2, 'missing', 1, 1, 'test')"""
            )


def test_complete_unversioned_feature_043_shape_is_adopted(tmp_path):
    path = tmp_path / "feature-043.db"
    upgrade_database(path)
    with sqlite3.connect(path) as connection:
        connection.execute("DROP TABLE wright_schema_migrations")
        connection.execute(
            "INSERT INTO system_settings VALUES ('legacy-marker', 'preserve')"
        )
        connection.commit()

    result = upgrade_database(path)

    assert result.starting_version == 0
    assert result.ending_version == len(MIGRATIONS)
    with sqlite3.connect(path) as connection:
        assert connection.execute(
            "SELECT value FROM system_settings WHERE key='legacy-marker'"
        ).fetchone() == ("preserve",)


def test_checksum_drift_fails_without_mutation(tmp_path):
    path = tmp_path / "state.db"
    upgrade_database(path)
    with sqlite3.connect(path) as connection:
        connection.execute(
            f"UPDATE {LEDGER_TABLE} SET checksum='tampered' WHERE version=1"
        )
        connection.commit()

    with pytest.raises(DatabaseCompatibilityError, match="checksum mismatch"):
        upgrade_database(path)

    with sqlite3.connect(path) as connection:
        assert connection.execute(
            f"SELECT checksum FROM {LEDGER_TABLE} WHERE version=1"
        ).fetchone() == ("tampered",)
        assert connection.execute(
            f"SELECT COUNT(*) FROM {LEDGER_TABLE}"
        ).fetchone() == (len(MIGRATIONS),)


def test_future_version_is_rejected(tmp_path):
    path = tmp_path / "future.db"
    upgrade_database(path)
    with sqlite3.connect(path) as connection:
        connection.execute(
            f"INSERT INTO {LEDGER_TABLE} VALUES (?, ?, ?, ?, ?, ?)",
            (99, "future", "future", "now", 0, "99.0.0"),
        )
        connection.commit()

    with pytest.raises(DatabaseCompatibilityError, match="newer"):
        database_status(path)


def test_corrupt_database_is_rejected(tmp_path):
    path = corrupt_database(tmp_path / "corrupt.db")

    with pytest.raises(DatabaseIntegrityError):
        database_status(path)


def test_foreign_key_corruption_is_rejected(tmp_path):
    path = tmp_path / "foreign-key.db"
    upgrade_database(path)
    with sqlite3.connect(path) as connection:
        connection.execute("PRAGMA foreign_keys = OFF")
        connection.execute(
            """INSERT INTO workspace_agent_sessions
            (workspace_id, session_id, created_at, updated_at)
            VALUES ('missing-workspace', 'orphan-session', 1, 1)"""
        )
        connection.commit()

    with pytest.raises(DatabaseIntegrityError, match="workspace_agent_sessions"):
        database_status(path)
