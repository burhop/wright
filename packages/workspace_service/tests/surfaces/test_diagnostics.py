from __future__ import annotations

from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
import sqlite3

import pytest

from core.surfaces.models import (
    FileSurfaceSource,
    GenerationProvenance,
    ProvenanceMode,
    SurfaceDescriptor,
    SurfaceId,
    SurfaceLifecycle,
    SurfaceRevision,
)
from core.surfaces.telemetry import (
    SurfaceDiagnosticEvent,
    SurfaceSeverity,
    TraceCorrelation,
)
from data_vault.migrations import upgrade_database
from data_vault.surface_repository import SurfaceRepository
from data_vault.surface_vault import SurfaceVault
from workspace_service.surfaces.diagnostics import (
    SurfaceDiagnosticHistory,
    SurfaceProvenanceAccessDenied,
    project_generation_provenance,
)


pytestmark = pytest.mark.workspace_surfaces


class RecordingSpan:
    def __init__(self, record) -> None:
        self.record = record

    def set_attribute(self, name, value) -> None:
        self.record["attributes"][name] = value


class RecordingTracer:
    def __init__(self) -> None:
        self.spans = []

    @contextmanager
    def start_as_current_span(self, name, *, attributes=None, **_kwargs):
        record = {"name": name, "attributes": dict(attributes or {})}
        self.spans.append(record)
        yield RecordingSpan(record)


def _event(index: int) -> SurfaceDiagnosticEvent:
    return SurfaceDiagnosticEvent(
        timestamp=datetime(2026, 7, 30, 12, index, tzinfo=UTC),
        severity=SurfaceSeverity.INFO,
        code="SURFACE_STATE_TRANSITION",
        message=f"Transition {index}",
        correlation=TraceCorrelation(
            correlation_id=f"correlation-{index}",
            trace_id=f"{index:032x}",
            span_id=f"{index:016x}",
        ),
        retryable=False,
        workspace_id="workspace-1",
        surface_id="surface-1",
        attributes={"token": f"secret-{index}", "index": index},
    )


def test_diagnostic_history_is_bounded_scoped_and_redacted() -> None:
    history = SurfaceDiagnosticHistory(max_events_per_surface=2)
    for index in range(3):
        history.record(_event(index))
    events = history.list(workspace_id="workspace-1", surface_id="surface-1")
    assert [event.message for event in events] == ["Transition 1", "Transition 2"]
    assert "secret" not in repr([event.as_dict() for event in events]).lower()
    assert history.list(workspace_id="workspace-2", surface_id="surface-1") == []


def test_generated_provenance_requires_authorization_and_is_not_general_log_data() -> (
    None
):
    provenance = GenerationProvenance(
        mode=ProvenanceMode.AGENT_GENERATED,
        prompt="Create a stress plot from the bracket results.",
        no_prompt=False,
        effective_constraints={"units": "MPa", "max_stress": 220},
        script_vault_digest="sha256:" + "a" * 64,
        script_content_hash="b" * 64,
        script_revision=4,
        task_id="task-1",
        execution_id="execution-1",
        trace_id="c" * 32,
        created_at=datetime(2026, 7, 30, 12, 0, tzinfo=UTC),
    )
    with pytest.raises(SurfaceProvenanceAccessDenied):
        project_generation_provenance(
            provenance,
            authorized=False,
            script_loader=lambda _digest: "print('private')",
        )
    projection = project_generation_provenance(
        provenance,
        authorized=True,
        script_loader=lambda digest: (
            "print('private')" if digest == provenance.script_vault_digest else ""
        ),
    )
    assert projection["prompt"] == provenance.prompt
    assert projection["effective_constraints"] == provenance.effective_constraints
    assert projection["script"] == "print('private')"
    assert "prompt" not in _event(1).as_dict()["attributes"]


def test_every_surface_sqlite_and_vault_read_write_creates_a_scoped_span(
    tmp_path: Path,
) -> None:
    tracer = RecordingTracer()
    database = tmp_path / "state.db"
    upgrade_database(database)
    with sqlite3.connect(database) as connection:
        connection.execute(
            """INSERT INTO engineering_workspaces
            (workspace_id, session_id, local_path, created_at, updated_at)
            VALUES ('workspace-1', 'session-1', '/workspace/one', 1, 1)"""
        )
        connection.commit()
    repository = SurfaceRepository(database, tracer=tracer)
    vault = SurfaceVault(tmp_path / "vault", tracer=tracer)
    now = datetime(2026, 7, 30, 12, 0, tzinfo=UTC)
    descriptor = SurfaceDescriptor(
        schema_version=1,
        surface_id=SurfaceId("surface-1"),
        workspace_id="workspace-1",
        source=FileSurfaceSource(
            path="models/bracket.step",
            file_revision="revision-1",
            media_type="model/step",
            provider_id="three-d-viewer",
        ),
        title="Bracket",
        lifecycle=SurfaceLifecycle.DECLARED,
        revision=SurfaceRevision(1),
        created_at=now,
        updated_at=now,
    )
    repository.create(descriptor, user_id="user-1", session_id="session-1")
    repository.get(
        descriptor.surface_id,
        workspace_id="workspace-1",
        user_id="user-1",
        session_id="session-1",
    )
    repository.list(
        workspace_id="workspace-1", user_id="user-1", session_id="session-1"
    )
    updated = descriptor.with_lifecycle(SurfaceLifecycle.STARTING, updated_at=now)
    repository.compare_and_set(
        updated,
        expected_revision=SurfaceRevision(1),
        user_id="user-1",
        session_id="session-1",
    )
    digest = vault.put(workspace_id="workspace-1", payload=b"safe payload")
    assert vault.get(workspace_id="workspace-1", digest=digest) == b"safe payload"

    assert [span["name"] for span in tracer.spans] == [
        "surface.sqlite.create",
        "surface.sqlite.get",
        "surface.sqlite.list",
        "surface.sqlite.compare_and_set",
        "surface.vault.put",
        "surface.vault.get",
    ]
    assert all(
        span["attributes"]["wright.workspace_id"] == "workspace-1"
        for span in tracer.spans
    )
