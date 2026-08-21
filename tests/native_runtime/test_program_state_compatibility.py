from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from data_vault import database_status, upgrade_database
from data_vault.migrations import MIGRATIONS
from wright_engineering.runtime.migrations import (
    MigrationPreflightError,
    NativeMigrationManager,
)


def test_packaged_ceiling_tracks_the_complete_program_schema() -> None:
    from wright_engineering.runtime.compatibility import CompatibilityPolicy

    contract = CompatibilityPolicy.load(
        Path(__file__).parents[2] / "src" / "wright_engineering" / "compatibility.json"
    )
    assert contract.data_schema_max == MIGRATIONS[-1].version == 16


def test_native_activation_upgrades_predecessor_state_and_creates_backup(
    tmp_path: Path,
) -> None:
    data_root = tmp_path / "data"
    database = NativeMigrationManager.database_path(data_root)
    upgrade_database(database, migrations=MIGRATIONS[:14])

    backup = NativeMigrationManager().prepare_activation(
        data_root=data_root,
        data_schema_min=0,
        data_schema_max=len(MIGRATIONS),
        operation_id="upgrade-program-state",
    )

    assert backup is not None
    assert Path(backup).exists()
    assert database_status(database).current_version == len(MIGRATIONS)


def test_native_activation_refuses_state_newer_than_candidate(tmp_path: Path) -> None:
    data_root = tmp_path / "data"
    database = NativeMigrationManager.database_path(data_root)
    upgrade_database(database)

    with pytest.raises(
        MigrationPreflightError, match="data_schema_newer_than_candidate"
    ):
        NativeMigrationManager().prepare_activation(
            data_root=data_root,
            data_schema_min=0,
            data_schema_max=len(MIGRATIONS) - 1,
            operation_id="rollback-program-state",
        )


def test_program_state_inventory_survives_upgrade_and_same_plan_is_idempotent(
    tmp_path: Path,
) -> None:
    data_root = tmp_path / "data"
    database = NativeMigrationManager.database_path(data_root)
    upgrade_database(database, migrations=MIGRATIONS[:14])
    with sqlite3.connect(database) as connection:
        connection.execute(
            """INSERT INTO catalog_snapshots(
                   snapshot_id, channel, sequence, schema_version, issued_at,
                   expires_at, payload_sha256, payload_json, verification_state)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                "catalog-fixture",
                "stable",
                1,
                1,
                1,
                2,
                "a" * 64,
                "{}",
                "active",
            ),
        )
        connection.execute(
            """INSERT INTO catalog_state(
                   state_id, active_snapshot_id, active_generation, updated_at,
                   updated_by)
               VALUES (1, 'catalog-fixture', 1, 1, 'program-test')"""
        )

    manager = NativeMigrationManager()
    before = manager.capture_state_inventory(data_root)
    first_backup = manager.prepare_activation(
        data_root=data_root,
        data_schema_min=0,
        data_schema_max=len(MIGRATIONS),
        operation_id="exact-program-upgrade-plan",
    )
    second_backup = manager.prepare_activation(
        data_root=data_root,
        data_schema_min=0,
        data_schema_max=len(MIGRATIONS),
        operation_id="exact-program-upgrade-plan",
    )
    after = manager.capture_state_inventory(data_root)
    comparison = manager.compare_state_inventories(before, after)

    assert first_backup == second_backup
    assert first_backup is not None and Path(first_backup).exists()
    assert before["data_schema"] == 14
    assert after["data_schema"] == len(MIGRATIONS)
    assert after["catalog_snapshot"] == before["catalog_snapshot"]
    assert after["counts"]["catalog_snapshots"] == 1
    assert comparison["counts"]["catalog_snapshots"]["disposition"] == "retained"
    assert comparison["schema_transition"] == [14, len(MIGRATIONS)]


def test_activation_operation_identity_refuses_a_mixed_plan(tmp_path: Path) -> None:
    data_root = tmp_path / "data"
    upgrade_database(NativeMigrationManager.database_path(data_root))
    manager = NativeMigrationManager()
    manager.prepare_activation(
        data_root=data_root,
        data_schema_min=0,
        data_schema_max=len(MIGRATIONS),
        operation_id="immutable-plan",
    )

    with pytest.raises(MigrationPreflightError, match="activation_operation_conflict"):
        manager.prepare_activation(
            data_root=data_root,
            data_schema_min=1,
            data_schema_max=len(MIGRATIONS),
            operation_id="immutable-plan",
        )
