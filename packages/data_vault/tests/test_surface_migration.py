from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from data_vault.migrations import (
    LEDGER_TABLE,
    MIGRATIONS,
    database_status,
    upgrade_database,
)
from data_vault.models import DatabaseCompatibilityError


pytestmark = pytest.mark.workspace_surfaces

SURFACE_TABLES = {
    "workspace_surfaces",
    "surface_presentations",
    "surface_display_artifacts",
    "surface_generation_provenance",
    "surface_runtimes",
    "surface_preferences",
    "surface_capability_grants",
    "surface_mcp_bindings",
    "surface_diagnostic_events",
    "surface_outbox",
}


def test_migration_six_is_contiguous_checksummed_and_creates_all_surface_tables(
    tmp_path: Path,
) -> None:
    assert [migration.version for migration in MIGRATIONS] == [1, 2, 3, 4, 5, 6, 7]
    migration = MIGRATIONS[5]
    assert migration.name == "workspace_surfaces"
    assert len(migration.checksum) == 64

    path = tmp_path / "surface.db"
    upgrade_database(path)
    with sqlite3.connect(path) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        ledger = connection.execute(
            f"SELECT name, checksum FROM {LEDGER_TABLE} WHERE version=6"
        ).fetchone()
    assert SURFACE_TABLES <= tables
    assert ledger == (migration.name, migration.checksum)


def test_upgrade_from_five_creates_verified_backup_and_preserves_workspace(
    tmp_path: Path,
) -> None:
    path = tmp_path / "upgrade.db"
    upgrade_database(path, migrations=MIGRATIONS[:5])
    with sqlite3.connect(path) as connection:
        connection.execute(
            """INSERT INTO engineering_workspaces
            (workspace_id, session_id, local_path, created_at, updated_at)
            VALUES ('workspace-1', 'session-1', '/workspace/one', 1, 1)"""
        )
        connection.commit()

    result = upgrade_database(path, backup_dir=tmp_path / "backups")

    assert result.starting_version == 5
    assert result.ending_version == 7
    assert result.backup_manifest is not None
    assert Path(result.backup_manifest).is_file()
    with sqlite3.connect(path) as connection:
        assert connection.execute(
            "SELECT local_path FROM engineering_workspaces WHERE workspace_id='workspace-1'"
        ).fetchone() == ("/workspace/one",)


def test_future_surface_schema_is_rejected_before_mutation(tmp_path: Path) -> None:
    path = tmp_path / "future.db"
    upgrade_database(path)
    with sqlite3.connect(path) as connection:
        connection.execute(
            f"INSERT INTO {LEDGER_TABLE} VALUES (?, ?, ?, ?, ?, ?)",
            (8, "future_surface_contract", "future", "now", 0, "99.0.0"),
        )
        connection.commit()

    with pytest.raises(DatabaseCompatibilityError, match="newer"):
        database_status(path)
    with sqlite3.connect(path) as connection:
        assert connection.execute(
            f"SELECT COUNT(*) FROM {LEDGER_TABLE} WHERE version=8"
        ).fetchone() == (1,)


def test_upgrade_from_six_revokes_legacy_presentation_authority(
    tmp_path: Path,
) -> None:
    path = tmp_path / "legacy-presentation.db"
    upgrade_database(path, migrations=MIGRATIONS[:6])
    with sqlite3.connect(path) as connection:
        connection.execute(
            """INSERT INTO engineering_workspaces
            (workspace_id, session_id, local_path, created_at, updated_at)
            VALUES ('workspace-1', 'session-1', '/workspace/one', 1, 1)"""
        )
        connection.execute(
            """INSERT INTO workspace_surfaces (
                surface_id, workspace_id, user_id, session_id, schema_version,
                source_kind, source_id, source_version, source_json, title,
                lifecycle, instance_json, presentations_json, capabilities_json,
                revision, created_at, updated_at
            ) VALUES (
                'surface-app', 'workspace-1', 'user-1', 'session-1', 1,
                'live_app', 'app', 'source-v1', '{}', 'App', 'ready',
                '{"instanceId":"instance-1","generation":3}', '[]', '[]',
                1, '2026-07-30T12:00:00+00:00', '2026-07-30T12:00:00+00:00'
            )"""
        )
        connection.execute(
            """INSERT INTO surface_presentations (
                presentation_id, instance_id, surface_id, workspace_id,
                user_id, kind, state, effective_origin, bootstrap_nonce_hash,
                cookie_audience, created_at, expires_at
            ) VALUES (
                'legacy-presentation', 'instance-1', 'surface-app',
                'workspace-1', 'user-1', 'panel', 'active',
                'https://legacy.preview.test', 'secret-hash', 'legacy-audience',
                '2026-07-30T12:00:00+00:00', '2026-07-30T12:01:00+00:00'
            )"""
        )
        connection.commit()

    result = upgrade_database(path)
    assert result.starting_version == 6
    assert result.ending_version == 7
    with sqlite3.connect(path) as connection:
        migrated = connection.execute(
            """SELECT session_id, state, generation, source_id, source_version,
                      bootstrap_nonce_hash, idempotency_key, closed_at
               FROM surface_presentations
               WHERE presentation_id='legacy-presentation'"""
        ).fetchone()
    assert migrated == (
        "session-1",
        "expired",
        1,
        "app",
        "source-v1",
        None,
        "migration-7:legacy-presentation",
        "2026-07-30T12:00:00+00:00",
    )
