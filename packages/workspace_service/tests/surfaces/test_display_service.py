from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
import sqlite3

import pytest

from data_vault import SurfaceVault, upgrade_database
from workspace_service.surfaces.display_service import (
    DisplayDeletionNotConfirmed,
    DisplayExecutionContext,
    DisplayRevisionConflict,
    DisplayService,
)
from workspace_service.surfaces.events import SurfaceEventHistory


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


def _context(**changes) -> DisplayExecutionContext:
    values = {
        "user_id": "user-1",
        "workspace_id": "workspace-1",
        "session_id": "session-1",
        "task_id": "task-1",
        "execution_id": "execution-1",
        "prompt": "Plot load by time.",
        "no_prompt": False,
        "effective_constraints": {"offline": True, "units": "N"},
        "script": "import wright\nwright.line(...)\n",
        "script_revision": 3,
        "trace_id": "a" * 32,
    }
    values.update(changes)
    return DisplayExecutionContext(**values)


def _envelope(revision: int, *, data: str = "10 N", key: str | None = None) -> dict:
    return {
        "schemaVersion": 1,
        "displayId": "loads",
        "revision": revision,
        "idempotencyKey": key or f"display-request-{revision:04d}",
        "title": "Loads",
        "durability": "durable",
        "accessibility": {"description": "Load by time."},
        "representations": [
            {"mediaType": "text/plain", "encoding": "utf-8", "data": data}
        ],
    }


def _service(tmp_path: Path) -> DisplayService:
    database = _database(tmp_path)
    return DisplayService(database, vault=SurfaceVault(tmp_path / "vault"), clock=lambda: NOW)


def test_ingest_is_atomic_updates_one_logical_surface_and_preserves_history(
    tmp_path: Path,
) -> None:
    service = _service(tmp_path)
    first = service.ingest(_envelope(1), context=_context())
    second = service.ingest(_envelope(2, data="12 N"), context=_context())

    assert first.created is True
    assert second.created is True
    assert second.descriptor.surface_id == first.descriptor.surface_id
    assert second.descriptor.source.artifact_revision == 2
    history = service.history(
        display_id="loads",
        context=_context(),
    )
    assert [artifact.revision for artifact in history] == [1, 2]
    assert [artifact.current for artifact in history] == [False, True]
    assert service.read_representation(
        artifact_id=history[-1].artifact_id,
        index=0,
        context=_context(),
    ) == b"12 N"


def test_duplicate_is_idempotent_and_stale_revision_never_replaces_current(
    tmp_path: Path,
) -> None:
    service = _service(tmp_path)
    first = service.ingest(_envelope(1), context=_context())
    replay = service.ingest(
        _envelope(1, data="must not replace", key="display-request-0001"),
        context=_context(),
    )
    assert replay.created is False
    assert replay.descriptor == first.descriptor
    service.ingest(_envelope(2), context=_context())
    with pytest.raises(DisplayRevisionConflict):
        service.ingest(_envelope(1, key="different-request-0001"), context=_context())
    assert service.history(display_id="loads", context=_context())[-1].revision == 2

    old_replay = service.ingest(
        _envelope(1, data="must still not replace", key="display-request-0001"),
        context=_context(),
    )
    assert old_replay.created is False
    assert old_replay.descriptor.source.artifact_revision == 1
    assert old_replay.descriptor.revision.value == 1


def test_fresh_process_rerun_advances_the_same_logical_display(tmp_path: Path) -> None:
    service = _service(tmp_path)
    first_context = _context(execution_id="execution-1")
    second_context = _context(execution_id="execution-2", script_revision=4)

    first = service.ingest(_envelope(1), context=first_context)
    second = service.ingest(
        _envelope(1, data="14 N", key="second-process-request"),
        context=second_context,
    )

    assert second.descriptor.surface_id == first.descriptor.surface_id
    assert second.descriptor.source.execution_id == "execution-2"
    assert second.descriptor.source.artifact_revision == 2
    history = service.history(display_id="loads", context=second_context)
    assert [artifact.revision for artifact in history] == [1, 2]
    assert [artifact.current for artifact in history] == [False, True]


def test_provenance_is_exact_workspace_authorized_and_absent_from_general_logs(
    tmp_path: Path,
) -> None:
    service = _service(tmp_path)
    result = service.ingest(_envelope(1), context=_context())
    verification = service.verify_artifact(
        surface_id=str(result.descriptor.surface_id), context=_context()
    )
    assert verification == {
        "mode": "agent_generated",
        "prompt": "Plot load by time.",
        "no_prompt": False,
        "effective_constraints": {"offline": True, "units": "N"},
        "script": "import wright\nwright.line(...)\n",
        "script_revision": 3,
        "task_id": "task-1",
        "execution_id": "execution-1",
        "trace_id": "a" * 32,
    }
    with pytest.raises(KeyError):
        service.verify_artifact(
            surface_id=str(result.descriptor.surface_id),
            context=_context(user_id="user-2"),
        )
    assert "Plot load" not in repr(service.diagnostic_projection(result.descriptor))
    assert "wright.line" not in repr(service.diagnostic_projection(result.descriptor))


def test_direct_execution_uses_explicit_no_prompt_marker(tmp_path: Path) -> None:
    service = _service(tmp_path)
    result = service.ingest(
        _envelope(1), context=_context(prompt=None, no_prompt=True)
    )
    verification = service.verify_artifact(
        surface_id=str(result.descriptor.surface_id),
        context=_context(prompt=None, no_prompt=True),
    )
    assert verification["prompt"] is None
    assert verification["no_prompt"] is True
    assert verification["mode"] == "direct_execution"


def test_vault_failure_or_transaction_failure_never_moves_current_pointer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    service = _service(tmp_path)
    service.ingest(_envelope(1), context=_context())
    original_put = service.vault.put

    def fail_put(**_kwargs):
        raise OSError("simulated vault failure")

    monkeypatch.setattr(service.vault, "put", fail_put)
    with pytest.raises(OSError):
        service.ingest(_envelope(2), context=_context())
    monkeypatch.setattr(service.vault, "put", original_put)
    assert service.history(display_id="loads", context=_context())[-1].revision == 1


def test_durable_output_delete_requires_truthful_retention_confirmation(
    tmp_path: Path,
) -> None:
    service = _service(tmp_path)
    result = service.ingest(_envelope(1), context=_context())
    with pytest.raises(DisplayDeletionNotConfirmed):
        service.delete(
            surface_id=str(result.descriptor.surface_id),
            context=_context(),
            retention_disclosure_confirmed=False,
        )
    deletion = service.delete(
        surface_id=str(result.descriptor.surface_id),
        context=_context(),
        retention_disclosure_confirmed=True,
    )
    assert deletion.deleted is True
    assert deletion.recoverable is False
    assert deletion.retention_status == "payload_cleanup_scheduled"
    assert service.history(display_id="loads", context=_context()) == []


def test_create_update_and_delete_publish_scoped_descriptor_events(
    tmp_path: Path,
) -> None:
    database = _database(tmp_path)
    events = SurfaceEventHistory()
    service = DisplayService(
        database,
        vault=SurfaceVault(tmp_path / "vault"),
        events=events,
        clock=lambda: NOW,
    )

    first = service.ingest(_envelope(1), context=_context())
    service.ingest(_envelope(2), context=_context())
    service.delete(
        surface_id=str(first.descriptor.surface_id),
        context=_context(),
        retention_disclosure_confirmed=True,
    )

    published = events.after(
        workspace_id="workspace-1",
        user_id="user-1",
        session_id="session-1",
    )
    assert [event.event_type for event in published] == [
        "surface.display.created",
        "surface.display.updated",
        "surface.display.deleted",
    ]
    assert [event.revision for event in published] == [1, 2, 2]
    assert {event.surface_id for event in published} == {
        str(first.descriptor.surface_id)
    }
