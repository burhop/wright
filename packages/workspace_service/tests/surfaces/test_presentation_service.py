from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
import sqlite3
from urllib.parse import urlsplit

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
from data_vault import (
    PresentationPreferenceRecord,
    SurfacePreferenceRepository,
    SurfaceRepository,
    upgrade_database,
)
from workspace_service.config import SurfacePreviewSettings
from workspace_service.surfaces.presentation_service import (
    IsolatedPresentationAcknowledgementRequired,
    PresentationService,
    PresentationUnavailable,
)
from workspace_service.surfaces.service import ActorRole, SurfaceActor


pytestmark = pytest.mark.workspace_surfaces
NOW = datetime(2026, 7, 30, 12, 0, tzinfo=UTC)


def _database(tmp_path: Path) -> Path:
    path = tmp_path / "state.db"
    upgrade_database(path)
    with sqlite3.connect(path) as connection:
        connection.execute(
            """INSERT INTO engineering_workspaces
            (workspace_id, session_id, local_path, created_at, updated_at)
            VALUES ('workspace-1', 'session-1', '/workspace/one', 1, 1)"""
        )
        connection.commit()
    return path


def _actor(**changes) -> SurfaceActor:
    values = {
        "user_id": "user-1",
        "workspace_id": "workspace-1",
        "session_id": "session-1",
        "role": ActorRole.ENGINEER,
    }
    values.update(changes)
    return SurfaceActor(**values)


def _source(sharing: SharingMode = SharingMode.SHARED, version: str = "a" * 64):
    return LiveAppSurfaceSource(
        manifest_id="shareable-app",
        manifest_version="1.0.0",
        manifest_hash=version,
        ownership=LiveAppOwnership.WRIGHT_OWNED,
        administrator_approved=True,
        sharing_mode=sharing,
    )


def _ready_descriptor(
    *, sharing: SharingMode = SharingMode.SHARED, version: str = "a" * 64
) -> SurfaceDescriptor:
    return SurfaceDescriptor(
        schema_version=1,
        surface_id=SurfaceId("surface-app"),
        workspace_id="workspace-1",
        source=_source(sharing, version),
        title="Shareable app",
        lifecycle=SurfaceLifecycle.READY,
        instance={
            "instanceId": "instance-shared",
            "generation": 3,
            "sharing": sharing.value,
            "readyAt": NOW.isoformat(),
        },
        presentations=(
            {"kind": "panel", "eligible": True},
            {"kind": "browser", "eligible": True},
        ),
        revision=SurfaceRevision(4),
        created_at=NOW,
        updated_at=NOW,
    )


def _service(tmp_path: Path, descriptor: SurfaceDescriptor | None = None):
    database = _database(tmp_path)
    surfaces = SurfaceRepository(database)
    surfaces.create(
        descriptor or _ready_descriptor(),
        user_id="user-1",
        session_id="session-1",
        idempotency_key="declare-shareable-app",
    )
    tokens = iter(["A" * 43, "B" * 43, "C" * 43, "D" * 43])
    identifiers = iter(
        ["presentation-panel", "presentation-browser", "isolated-one", "isolated-two"]
    )
    service = PresentationService(
        database,
        preview=SurfacePreviewSettings(
            scheme="https",
            bind_host="127.0.0.1",
            domain="preview.example.test",
            public_port=443,
        ),
        clock=lambda: NOW,
        id_factory=lambda: next(identifiers),
        token_factory=lambda: next(tokens),
        token_ttl_seconds=60,
    )
    return database, surfaces, service


def test_shared_panel_and_browser_reuse_instance_and_close_does_not_stop(
    tmp_path: Path,
) -> None:
    database, surfaces, service = _service(tmp_path)

    panel = service.open(
        actor=_actor(),
        surface_id=SurfaceId("surface-app"),
        kind="panel",
        idempotency_key="open-panel-request",
        remember_preference=True,
    )
    browser = service.open(
        actor=_actor(),
        surface_id=SurfaceId("surface-app"),
        kind="browser",
        idempotency_key="open-browser-request",
    )

    assert panel.launch.instance_id == browser.launch.instance_id == "instance-shared"
    assert panel.launch.presentation_id != browser.launch.presentation_id
    assert urlsplit(panel.launch.absolute_bootstrap_url).hostname == (
        "s-presentation-panel.preview.example.test"
    )
    assert urlsplit(panel.launch.absolute_bootstrap_url).fragment == "A" * 43
    assert panel.launch.absolute_bootstrap_url.startswith("https://")

    service.close(
        actor=_actor(),
        surface_id=SurfaceId("surface-app"),
        presentation_id=panel.launch.presentation_id,
    )
    assert service.get_record(
        actor=_actor(), presentation_id=panel.launch.presentation_id
    ).state == "closed"
    assert service.get_record(
        actor=_actor(), presentation_id=browser.launch.presentation_id
    ).state == "issued"
    assert surfaces.get(
        SurfaceId("surface-app"),
        workspace_id="workspace-1",
        user_id="user-1",
        session_id="session-1",
    ).lifecycle is SurfaceLifecycle.READY

    with sqlite3.connect(database) as connection:
        stored = connection.execute(
            "SELECT bootstrap_nonce_hash FROM surface_presentations"
        ).fetchall()
    assert all("A" * 10 not in (row[0] or "") for row in stored)


def test_idempotent_reopen_rotates_bootstrap_without_duplicate_presentation(
    tmp_path: Path,
) -> None:
    _database_path, _surfaces, service = _service(tmp_path)
    first = service.open(
        actor=_actor(),
        surface_id=SurfaceId("surface-app"),
        kind="panel",
        idempotency_key="same-open-request",
    )
    replay = service.open(
        actor=_actor(),
        surface_id=SurfaceId("surface-app"),
        kind="panel",
        idempotency_key="same-open-request",
        remember_preference=True,
    )
    assert first.created is True
    assert replay.created is False
    assert replay.launch.presentation_id == first.launch.presentation_id
    assert replay.launch.absolute_bootstrap_url != first.launch.absolute_bootstrap_url
    assert len(service.list_records(actor=_actor(), surface_id=SurfaceId("surface-app"))) == 1
    preference = service.resolve_preference(
        actor=_actor(), surface_id=SurfaceId("surface-app")
    )
    assert preference.kind == "panel"
    assert preference.remembered is True


def test_concurrent_idempotent_create_returns_the_winning_presentation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _database_path, _surfaces, service = _service(tmp_path)
    create = service.presentations.create

    def concurrent_winner(record):
        create(record)
        raise sqlite3.IntegrityError("simulated concurrent idempotency winner")

    monkeypatch.setattr(service.presentations, "create", concurrent_winner)
    result = service.open(
        actor=_actor(),
        surface_id=SurfaceId("surface-app"),
        kind="panel",
        idempotency_key="concurrent-open-request",
    )
    assert result.created is False
    assert result.launch.presentation_id == "presentation-panel"
    assert len(
        service.list_records(actor=_actor(), surface_id=SurfaceId("surface-app"))
    ) == 1


def test_preference_is_revalidated_against_source_version_and_eligibility(
    tmp_path: Path,
) -> None:
    database, _surfaces, service = _service(tmp_path)
    preferences = SurfacePreferenceRepository(database)
    preferences.compare_and_set(
        PresentationPreferenceRecord(
            user_id="user-1",
            workspace_id="workspace-1",
            source_id="shareable-app",
            source_version="f" * 64,
            preferred_kind="panel",
            revision=1,
            created_at=NOW,
            updated_at=NOW,
        ),
        expected_revision=None,
    )

    decision = service.resolve_preference(
        actor=_actor(), surface_id=SurfaceId("surface-app")
    )
    assert decision.kind == "browser"
    assert decision.remembered is False
    assert "source version" in decision.reason.lower()

    current = service.surfaces.get(
        SurfaceId("surface-app"),
        workspace_id="workspace-1",
        user_id="user-1",
        session_id="session-1",
    )
    ineligible = replace(
        current,
        presentations=(
            {"kind": "panel", "eligible": False, "reason": "Framing denied"},
            {"kind": "browser", "eligible": True},
        ),
        revision=current.revision.next(),
    )
    service.surfaces.compare_and_set(
        ineligible,
        expected_revision=current.revision,
        user_id="user-1",
        session_id="session-1",
    )
    decision = service.resolve_preference(
        actor=_actor(), surface_id=SurfaceId("surface-app")
    )
    assert decision.kind == "browser"


def test_stale_or_ineligible_instance_is_rejected_without_new_app(tmp_path: Path) -> None:
    descriptor = replace(_ready_descriptor(), instance=None)
    _database_path, _surfaces, service = _service(tmp_path, descriptor)
    with pytest.raises(PresentationUnavailable, match="ready instance"):
        service.open(
            actor=_actor(),
            surface_id=SurfaceId("surface-app"),
            kind="panel",
            idempotency_key="stale-instance-request",
        )


def test_idempotent_replay_rejects_a_replaced_instance_even_at_same_generation(
    tmp_path: Path,
) -> None:
    _database_path, surfaces, service = _service(tmp_path)
    service.open(
        actor=_actor(),
        surface_id=SurfaceId("surface-app"),
        kind="panel",
        idempotency_key="same-instance-request",
    )
    current = surfaces.get(
        SurfaceId("surface-app"),
        workspace_id="workspace-1",
        user_id="user-1",
        session_id="session-1",
    )
    replaced = replace(
        current,
        instance={**current.instance, "instanceId": "instance-replaced"},
        revision=current.revision.next(),
    )
    surfaces.compare_and_set(
        replaced,
        expected_revision=current.revision,
        user_id="user-1",
        session_id="session-1",
    )

    with pytest.raises(PresentationUnavailable, match="another presentation"):
        service.open(
            actor=_actor(),
            surface_id=SurfaceId("surface-app"),
            kind="panel",
            idempotency_key="same-instance-request",
        )


def test_isolated_presentations_require_acknowledgement_and_do_not_reuse_instance(
    tmp_path: Path,
) -> None:
    descriptor = _ready_descriptor(sharing=SharingMode.ISOLATED)
    _database_path, _surfaces, service = _service(tmp_path, descriptor)
    with pytest.raises(IsolatedPresentationAcknowledgementRequired):
        service.open(
            actor=_actor(),
            surface_id=SurfaceId("surface-app"),
            kind="panel",
            idempotency_key="isolated-panel-request",
        )
    panel = service.open(
        actor=_actor(),
        surface_id=SurfaceId("surface-app"),
        kind="panel",
        idempotency_key="isolated-panel-request",
        isolated_acknowledged=True,
    )
    browser = service.open(
        actor=_actor(),
        surface_id=SurfaceId("surface-app"),
        kind="browser",
        idempotency_key="isolated-browser-request",
        isolated_acknowledged=True,
    )
    assert panel.launch.instance_id != browser.launch.instance_id


def test_cross_scope_and_ineligible_panel_are_indistinguishable(tmp_path: Path) -> None:
    _database_path, _surfaces, service = _service(tmp_path)
    for actor in (
        _actor(user_id="user-2"),
        _actor(workspace_id="workspace-2"),
        _actor(session_id="session-2"),
    ):
        with pytest.raises(PresentationUnavailable):
            service.open(
                actor=actor,
                surface_id=SurfaceId("surface-app"),
                kind="panel",
                idempotency_key="unauthorized-request",
            )


def test_generated_presentation_identity_cannot_escape_the_preview_hostname(
    tmp_path: Path,
) -> None:
    _database_path, _surfaces, service = _service(tmp_path)
    service.id_factory = lambda: "../api"
    with pytest.raises(RuntimeError, match="presentation ID"):
        service.open(
            actor=_actor(),
            surface_id=SurfaceId("surface-app"),
            kind="panel",
            idempotency_key="unsafe-generated-id",
        )
