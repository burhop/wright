from __future__ import annotations

import sqlite3
import json
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

import pytest

from core.surfaces.models import (
    LiveAppOwnership,
    LiveAppSurfaceSource,
    SharingMode,
    SurfaceDescriptor,
    SurfaceId,
    SurfaceLifecycle,
    SurfaceRevision,
)
from core.surfaces.live_app_manifest import parse_live_app_manifest
from data_vault import (
    SurfaceRepository,
    SurfaceRuntimeRecord,
    SurfaceRuntimeRepository,
    upgrade_database,
)
from workspace_service.config import (
    SurfaceFeatureFlags,
    SurfacePolicySettings,
    SurfacePreviewSettings,
    WorkspaceSurfaceSettings,
)
from workspace_service.surfaces.live_app_manager import LiveAppInstance
from workspace_service.surfaces.live_app_runtime import (
    LiveAppRuntimeRegistry,
    SqliteLiveAppPersistence,
)
from workspace_service.surfaces.limits import SurfaceLimitPolicy
from workspace_service.surfaces.manifests import DiscoveredManifest
from workspace_service.surfaces.target_pins import TargetPinRegistry
from workspace_service.surfaces.target_policy import TargetPolicy
from workspace_service.surfaces.presentation_service import PresentationService
from workspace_service.surfaces.revocation import RevocationCoordinator
from workspace_service.surfaces.service import ActorRole, SurfaceActor


pytestmark = pytest.mark.workspace_surfaces
NOW = datetime(2026, 7, 30, 12, 0, tzinfo=UTC)


def _settings() -> WorkspaceSurfaceSettings:
    return WorkspaceSurfaceSettings(
        flags=SurfaceFeatureFlags(model=True, live_apps=True),
        preview=SurfacePreviewSettings(
            scheme="http",
            bind_host="127.0.0.1",
            domain="preview.test",
            public_port=8000,
        ),
        policy=SurfacePolicySettings(),
    )


def _actor() -> SurfaceActor:
    return SurfaceActor(
        user_id="user-1",
        workspace_id="workspace-1",
        session_id="session-1",
        role=ActorRole.ENGINEER,
    )


def _database(tmp_path: Path) -> Path:
    database = tmp_path / "state.db"
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    upgrade_database(database)
    with sqlite3.connect(database) as connection:
        connection.execute(
            """INSERT INTO engineering_workspaces
            (workspace_id, session_id, local_path, created_at, updated_at)
            VALUES (?, ?, ?, 1, 1)""",
            ("workspace-1", "session-1", str(workspace)),
        )
        connection.commit()
    descriptor = SurfaceDescriptor(
        schema_version=1,
        surface_id=SurfaceId("surface-app"),
        workspace_id="workspace-1",
        source=LiveAppSurfaceSource(
            manifest_id="demo.app",
            manifest_version="1.0.0",
            manifest_hash="a" * 64,
            ownership=LiveAppOwnership.WRIGHT_OWNED,
            administrator_approved=True,
            sharing_mode=SharingMode.SHARED,
        ),
        title="Demo app",
        lifecycle=SurfaceLifecycle.READY,
        instance={"instanceId": "instance-1", "generation": 2, "sharing": "shared"},
        presentations=(
            {"kind": "panel", "eligible": True},
            {"kind": "browser", "eligible": True},
        ),
        revision=SurfaceRevision(3),
        created_at=NOW,
        updated_at=NOW,
    )
    SurfaceRepository(database).create(
        descriptor,
        user_id="user-1",
        session_id="session-1",
        idempotency_key="declare-runtime-surface",
    )
    SurfaceRuntimeRepository(database).create(
        SurfaceRuntimeRecord(
            runtime_id="runtime-1",
            instance_id="instance-1",
            surface_id="surface-app",
            workspace_id="workspace-1",
            generation=2,
            ownership="launched",
            platform="windows_job",
            state="ready",
            manifest_hash="a" * 64,
            lifetime={"policy": "workspace"},
            limits={"memoryMiB": 256},
            revision=1,
            created_at=NOW,
            updated_at=NOW,
            process_identity={"pid": 100, "creationTime": 1.0},
            target_pin={"address": "127.0.0.1", "port": 8123},
        ),
        user_id="user-1",
        session_id="session-1",
    )
    PresentationService(
        database,
        preview=_settings().preview,
        clock=lambda: NOW,
        id_factory=lambda: "presentation-1",
        token_factory=lambda: "A" * 43,
    ).open(
        actor=_actor(),
        surface_id=SurfaceId("surface-app"),
        kind="panel",
        idempotency_key="open-presentation-0001",
    )
    return database


@pytest.mark.anyio
async def test_startup_reconciliation_revokes_credentials_and_pins_fail_closed(
    tmp_path: Path,
) -> None:
    database = _database(tmp_path)
    registry = LiveAppRuntimeRegistry(
        database,
        settings=_settings(),
        revocation=RevocationCoordinator(database),
        monitor_seconds=60,
    )
    await registry.reconcile_startup()
    try:
        with sqlite3.connect(database) as connection:
            connection.row_factory = sqlite3.Row
            runtime = connection.execute(
                "SELECT state, target_pin_json, revision FROM surface_runtimes"
            ).fetchone()
            presentation = connection.execute(
                """SELECT state, bootstrap_nonce_hash, presentation_cookie_hash
                FROM surface_presentations"""
            ).fetchone()
            surface = connection.execute(
                "SELECT lifecycle, diagnostic_summary_json FROM workspace_surfaces"
            ).fetchone()
        assert dict(runtime) == {
            "state": "failed",
            "target_pin_json": None,
            "revision": 2,
        }
        assert dict(presentation) == {
            "state": "closed",
            "bootstrap_nonce_hash": None,
            "presentation_cookie_hash": None,
        }
        assert surface["lifecycle"] == "failed"
        assert (
            "SURFACE_RECONCILE_OWNERSHIP_UNPROVABLE"
            in surface["diagnostic_summary_json"]
        )
    finally:
        await registry.shutdown()


class _Revocation:
    def __init__(self, events: list[str]) -> None:
        self.events = events

    def workspace_closed(self, *, workspace_id: str) -> None:
        self.events.append(f"credentials:{workspace_id}")


class _Manager:
    def __init__(self, events: list[str]) -> None:
        self.events = events

    def revoke_all_routes(self) -> int:
        self.events.append("routes:workspace-1")
        return 1

    async def shutdown_workspace(self, workspace_id: str):
        self.events.append(f"processes:{workspace_id}")
        return ()


@pytest.mark.anyio
async def test_shutdown_revokes_credentials_and_routes_before_processes(
    tmp_path: Path,
) -> None:
    database = _database(tmp_path)
    events: list[str] = []
    registry = LiveAppRuntimeRegistry(
        database,
        settings=_settings(),
        revocation=_Revocation(events),  # type: ignore[arg-type]
    )
    registry._managers["workspace-1"] = _Manager(events)  # type: ignore[assignment]

    await registry.shutdown()
    assert events == [
        "credentials:workspace-1",
        "routes:workspace-1",
        "processes:workspace-1",
    ]


class _NoProcessSupervisor:
    def snapshot(self, _runtime_id: str):
        raise KeyError("no process")


def test_runtime_snapshot_upsert_tracks_generation_state_limits_and_revision(
    tmp_path: Path,
) -> None:
    database = _database(tmp_path)
    document = json.loads(
        (
            Path(__file__).parents[4]
            / "tests/fixtures/workspace_surfaces/shareable_app/manifest.surface.json"
        ).read_text(encoding="utf-8")
    )
    declaration = DiscoveredManifest(
        manifest=parse_live_app_manifest(document),
        relative_path=".wright/apps/shareable.surface.json",
        working_directory=tmp_path,
    )
    persistence = SqliteLiveAppPersistence(
        database,
        supervisor=_NoProcessSupervisor(),  # type: ignore[arg-type]
        target_pins=TargetPinRegistry(policy=TargetPolicy()),
        limit_policy=SurfaceLimitPolicy(_settings().policy),
        platform_hint="posix",
    )
    instance = LiveAppInstance(
        instance_id="instance-2",
        workspace_id="workspace-1",
        surface_id="surface-app",
        manifest_id="shareable.app",
        manifest_hash=declaration.manifest.canonical_hash,
        generation=1,
        revision=1,
        state="starting",
        sharing="shared",
        ownership="launched",
        platform="posix",
        runtime_id=None,
        lifetime_policy="workspace",
        lease_expires_at=None,
        idle_seconds=None,
        last_activity_at=NOW,
        started_at=NOW,
        ready_at=None,
        ended_at=None,
        last_health=None,
        failure=None,
    )
    persistence(instance, declaration)
    persistence(
        replace(instance, generation=2, revision=2, state="stopped", ended_at=NOW),
        declaration,
    )

    with sqlite3.connect(database) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute(
            """SELECT generation, state, platform, limits_json,
                      target_pin_json, revision
               FROM surface_runtimes WHERE instance_id='instance-2'"""
        ).fetchone()
    assert row["generation"] == 2
    assert row["state"] == "stopped"
    assert row["platform"] == "posix"
    assert json.loads(row["limits_json"])["maximum_header_count"] == 100
    assert row["target_pin_json"] is None
    assert row["revision"] == 2
