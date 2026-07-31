from __future__ import annotations

import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from data_vault import SurfaceGrantRecord, SurfaceGrantRepository, upgrade_database
from workspace_service.surfaces.revocation import RevocationCoordinator


pytestmark = pytest.mark.workspace_surfaces
NOW = datetime(2026, 7, 30, 12, 0, tzinfo=UTC)


def _database(tmp_path: Path) -> Path:
    database = tmp_path / "state.db"
    upgrade_database(database)
    with sqlite3.connect(database) as connection:
        connection.execute(
            """INSERT INTO engineering_workspaces
            (workspace_id, session_id, local_path, created_at, updated_at)
            VALUES ('workspace-1', 'session-1', '/workspace/one', 1, 1)"""
        )
        for user, surface, instance, presentation in (
            ("user-1", "surface-1", "instance-old", "presentation-1"),
            ("user-1", "surface-2", "instance-new", "presentation-2"),
            ("user-2", "surface-3", "instance-other", "presentation-3"),
        ):
            connection.execute(
                """INSERT INTO workspace_surfaces (
                    surface_id, workspace_id, user_id, session_id, schema_version,
                    source_kind, source_id, source_version, source_json, title,
                    lifecycle, presentations_json, capabilities_json, revision,
                    created_at, updated_at
                ) VALUES (?, 'workspace-1', ?, 'session-1', 1, 'live_app',
                    ?, '1.0', '{}', 'App', 'ready', '[]', '[]', 1, ?, ?)""",
                (surface, user, f"source-{surface}", NOW.isoformat(), NOW.isoformat()),
            )
            connection.execute(
                """INSERT INTO surface_presentations (
                    presentation_id, instance_id, surface_id, workspace_id,
                    user_id, session_id, kind, state, generation, source_id,
                    source_version, effective_origin, bootstrap_nonce_hash,
                    cookie_audience, idempotency_key, created_at, last_seen_at,
                    expires_at, closed_at, bootstrap_expires_at,
                    presentation_cookie_hash
                ) VALUES (?, ?, ?, 'workspace-1', ?, 'session-1', 'panel',
                    'active', 1, ?, '1.0', ?, NULL, ?, ?, ?, ?, ?, NULL, ?, ?)""",
                (
                    presentation,
                    instance,
                    surface,
                    user,
                    f"source-{surface}",
                    f"https://s-{presentation}.preview.test",
                    f"audience-{presentation}",
                    f"idempotency-{presentation}",
                    NOW.isoformat(),
                    NOW.isoformat(),
                    (NOW + timedelta(hours=8)).isoformat(),
                    (NOW + timedelta(minutes=1)).isoformat(),
                    "cookie-hash",
                ),
            )
        connection.commit()
    grants = SurfaceGrantRepository(database)
    for grant_id, user, instance in (
        ("grant-old", "user-1", "instance-old"),
        ("grant-new", "user-1", "instance-new"),
        ("grant-other", "user-2", "instance-other"),
    ):
        grants.create(
            SurfaceGrantRecord(
                grant_id=grant_id,
                user_id=user,
                workspace_id="workspace-1",
                source_id=f"source-{instance}",
                source_version="1.0",
                instance_id=instance,
                capability="tool.call",
                operation="call",
                constraints={},
                risk_tier="high",
                persistence="instance",
                decision="allow",
                decision_source="user",
                expires_at=NOW + timedelta(hours=1),
                created_at=NOW,
            )
        )
    return database


def _states(database: Path):
    with sqlite3.connect(database) as connection:
        presentations = dict(
            connection.execute(
                "SELECT presentation_id, state FROM surface_presentations"
            ).fetchall()
        )
        grants = dict(
            connection.execute(
                "SELECT grant_id, revoked_at FROM surface_capability_grants"
            ).fetchall()
        )
    return presentations, grants


def test_presentation_disposal_revokes_only_its_credentials(tmp_path: Path) -> None:
    database = _database(tmp_path)
    coordinator = RevocationCoordinator(database, clock=lambda: NOW)
    result = coordinator.presentation_disposed(
        workspace_id="workspace-1",
        user_id="user-1",
        presentation_id="presentation-1",
    )
    assert result.presentations == 1
    assert result.grants == 0
    presentations, grants = _states(database)
    assert presentations["presentation-1"] == "closed"
    assert presentations["presentation-2"] == "active"
    assert grants["grant-old"] is None


def test_runtime_replacement_revokes_old_instance_authority(tmp_path: Path) -> None:
    database = _database(tmp_path)
    coordinator = RevocationCoordinator(database, clock=lambda: NOW)
    result = coordinator.runtime_replaced(
        workspace_id="workspace-1", instance_id="instance-old"
    )
    assert (result.presentations, result.grants) == (1, 1)
    presentations, grants = _states(database)
    assert presentations["presentation-1"] == "closed"
    assert grants["grant-old"] == NOW.isoformat()
    assert presentations["presentation-2"] == "active"
    assert grants["grant-new"] is None


def test_logout_and_workspace_close_revoke_exact_scopes(tmp_path: Path) -> None:
    database = _database(tmp_path)
    coordinator = RevocationCoordinator(database, clock=lambda: NOW)
    logged_out = coordinator.logout(
        workspace_id="workspace-1", user_id="user-1"
    )
    assert (logged_out.presentations, logged_out.grants) == (2, 2)
    presentations, grants = _states(database)
    assert presentations["presentation-3"] == "active"
    assert grants["grant-other"] is None

    closed = coordinator.workspace_closed(workspace_id="workspace-1")
    assert (closed.presentations, closed.grants) == (1, 1)
    presentations, grants = _states(database)
    assert set(presentations.values()) == {"closed"}
    assert all(value == NOW.isoformat() for value in grants.values())
