from __future__ import annotations

from datetime import UTC, datetime

import pytest

from core.surfaces.models import (
    FileSurfaceSource,
    SurfaceDescriptor,
    SurfaceId,
    SurfaceLifecycle,
    SurfaceRevision,
)
from workspace_service.surfaces.events import SurfaceEventHistory


pytestmark = pytest.mark.workspace_surfaces


def _descriptor(revision: int) -> SurfaceDescriptor:
    timestamp = datetime(2026, 7, 30, 12, revision, tzinfo=UTC)
    return SurfaceDescriptor(
        schema_version=1,
        surface_id=SurfaceId("surface-1"),
        workspace_id="workspace-1",
        source=FileSurfaceSource(
            path="models/bracket.step",
            file_revision=f"revision-{revision}",
            media_type="model/step",
            provider_id="three-d-viewer",
        ),
        title="Bracket",
        lifecycle=SurfaceLifecycle.DECLARED,
        revision=SurfaceRevision(revision),
        created_at=timestamp,
        updated_at=timestamp,
    )


def test_event_history_is_bounded_resumable_and_exactly_scoped() -> None:
    history = SurfaceEventHistory(maximum_events_per_workspace=2)
    for revision in range(1, 4):
        history.publish(
            _descriptor(revision),
            event_type="surface.updated",
            user_id="user-1",
            session_id="session-1",
        )

    available = history.after(
        workspace_id="workspace-1",
        user_id="user-1",
        session_id="session-1",
    )
    assert [event.revision for event in available] == [2, 3]
    assert history.after(
        workspace_id="workspace-1",
        user_id="user-1",
        session_id="session-1",
        last_event_id=available[0].event_id,
    ) == (available[1],)
    assert history.after(
        workspace_id="workspace-1",
        user_id="user-2",
        session_id="session-1",
    ) == ()
    assert history.after(
        workspace_id="workspace-1",
        user_id="user-1",
        session_id="session-2",
    ) == ()
    assert history.after(
        workspace_id="workspace-2",
        user_id="user-1",
        session_id="session-1",
    ) == ()
    assert history.after(
        workspace_id="workspace-1",
        user_id="user-1",
        session_id="session-1",
        last_event_id="evicted-or-unknown",
    ) == available
