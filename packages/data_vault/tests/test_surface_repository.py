from __future__ import annotations

from contextlib import contextmanager
from dataclasses import replace
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
from data_vault.surface_repository import (
    GenerationProvenanceReference,
    GenerationProvenanceRepository,
    PresentationPreferenceRecord,
    SurfaceDiagnosticRepository,
    SurfaceGrantRecord,
    SurfaceGrantRepository,
    SurfacePreferenceRepository,
    SurfaceRepository,
    SurfaceRevisionConflict,
    SurfaceRuntimeRecord,
    SurfaceRuntimeRepository,
)


pytestmark = pytest.mark.workspace_surfaces


class RecordingTracer:
    def __init__(self) -> None:
        self.spans: list[str] = []

    @contextmanager
    def start_as_current_span(self, name: str, **_kwargs):
        self.spans.append(name)
        yield None


def _descriptor(surface_id: str, workspace_id: str, revision: int = 1):
    timestamp = datetime(2026, 7, 30, 12, revision, tzinfo=UTC)
    return SurfaceDescriptor(
        schema_version=1,
        surface_id=SurfaceId(surface_id),
        workspace_id=workspace_id,
        source=FileSurfaceSource(
            path=f"models/{surface_id}.step",
            file_revision=f"revision-{revision}",
            media_type="model/step",
            provider_id="three-d-viewer",
        ),
        title=surface_id,
        lifecycle=SurfaceLifecycle.DECLARED,
        revision=SurfaceRevision(revision),
        created_at=timestamp,
        updated_at=timestamp,
    )


def _repository(tmp_path: Path) -> SurfaceRepository:
    path = tmp_path / "state.db"
    upgrade_database(path)
    with sqlite3.connect(path) as connection:
        connection.executemany(
            """INSERT INTO engineering_workspaces
            (workspace_id, session_id, local_path, created_at, updated_at)
            VALUES (?, ?, ?, 1, 1)""",
            [
                ("workspace-1", "session-1", "/workspace/one"),
                ("workspace-2", "session-2", "/workspace/two"),
            ],
        )
        connection.commit()
    return SurfaceRepository(path)


def test_repository_queries_require_exact_workspace_user_and_session_scope(
    tmp_path: Path,
) -> None:
    repository = _repository(tmp_path)
    first = _descriptor("surface-1", "workspace-1")
    second = _descriptor("surface-2", "workspace-2")
    repository.create(first, user_id="user-1", session_id="session-1")
    repository.create(second, user_id="user-2", session_id="session-2")

    assert (
        repository.get(
            first.surface_id,
            workspace_id="workspace-1",
            user_id="user-1",
            session_id="session-1",
        )
        == first
    )
    assert (
        repository.get(
            first.surface_id,
            workspace_id="workspace-2",
            user_id="user-1",
            session_id="session-1",
        )
        is None
    )
    assert (
        repository.get(
            first.surface_id,
            workspace_id="workspace-1",
            user_id="user-2",
            session_id="session-1",
        )
        is None
    )
    assert (
        repository.get(
            first.surface_id,
            workspace_id="workspace-1",
            user_id="user-1",
            session_id="session-2",
        )
        is None
    )
    assert repository.list(
        workspace_id="workspace-1", user_id="user-1", session_id="session-1"
    ) == [first]


def test_repository_compare_and_set_rejects_stale_revision_without_mutation(
    tmp_path: Path,
) -> None:
    repository = _repository(tmp_path)
    original = _descriptor("surface-1", "workspace-1")
    repository.create(original, user_id="user-1", session_id="session-1")
    updated = replace(
        original,
        lifecycle=SurfaceLifecycle.STARTING,
        revision=SurfaceRevision(2),
        updated_at=datetime(2026, 7, 30, 12, 2, tzinfo=UTC),
    )

    assert (
        repository.compare_and_set(
            updated,
            expected_revision=SurfaceRevision(1),
            user_id="user-1",
            session_id="session-1",
        )
        == updated
    )
    stale = replace(
        updated,
        lifecycle=SurfaceLifecycle.READY,
        revision=SurfaceRevision(3),
    )
    with pytest.raises(SurfaceRevisionConflict):
        repository.compare_and_set(
            stale,
            expected_revision=SurfaceRevision(1),
            user_id="user-1",
            session_id="session-1",
        )
    assert (
        repository.get(
            original.surface_id,
            workspace_id="workspace-1",
            user_id="user-1",
            session_id="session-1",
        )
        == updated
    )


def test_repository_idempotency_is_scoped_and_returns_original_result(
    tmp_path: Path,
) -> None:
    repository = _repository(tmp_path)
    descriptor = _descriptor("surface-1", "workspace-1")
    first = repository.create(
        descriptor,
        user_id="user-1",
        session_id="session-1",
        idempotency_key="declare-1",
    )
    replay = repository.create(
        replace(descriptor, title="must not replace"),
        user_id="user-1",
        session_id="session-1",
        idempotency_key="declare-1",
    )
    assert replay == first
    with pytest.raises(ValueError, match="idempotency"):
        repository.create(
            _descriptor("surface-2", "workspace-1"),
            user_id="user-1",
            session_id="session-1",
            idempotency_key="declare-1",
        )


def test_repository_round_trips_authorized_generation_provenance(
    tmp_path: Path,
) -> None:
    repository = _repository(tmp_path)
    descriptor = replace(
        _descriptor("surface-1", "workspace-1"),
        generation_provenance=GenerationProvenance(
            mode=ProvenanceMode.AGENT_GENERATED,
            prompt="Graph load by time.",
            no_prompt=False,
            effective_constraints={"offline": True},
            script_vault_digest="sha256:" + "a" * 64,
            script_content_hash="b" * 64,
            script_revision=1,
            task_id="task-1",
            execution_id="execution-1",
            trace_id="c" * 32,
            created_at=datetime(2026, 7, 30, 12, 0, tzinfo=UTC),
        ),
    )
    repository.create(descriptor, user_id="user-1", session_id="session-1")
    assert repository.get(
        descriptor.surface_id,
        workspace_id="workspace-1",
        user_id="user-1",
        session_id="session-1",
    ) == descriptor


def test_preference_repository_is_user_workspace_source_scoped_and_optimistic(
    tmp_path: Path,
) -> None:
    repository = _repository(tmp_path)
    tracer = RecordingTracer()
    preferences = SurfacePreferenceRepository(repository.db_path, tracer=tracer)
    created = datetime(2026, 7, 30, 12, 0, tzinfo=UTC)
    record = PresentationPreferenceRecord(
        user_id="user-1",
        workspace_id="workspace-1",
        source_id="brep",
        source_version="manifest-v1",
        preferred_kind="panel",
        revision=1,
        created_at=created,
        updated_at=created,
    )
    assert preferences.compare_and_set(record, expected_revision=None) == record
    assert preferences.get(
        user_id="user-1", workspace_id="workspace-1", source_id="brep"
    ) == record
    assert (
        preferences.get(
            user_id="user-2", workspace_id="workspace-1", source_id="brep"
        )
        is None
    )
    updated = replace(
        record,
        preferred_kind="browser",
        revision=2,
        updated_at=datetime(2026, 7, 30, 12, 1, tzinfo=UTC),
    )
    assert preferences.compare_and_set(updated, expected_revision=1) == updated
    with pytest.raises(SurfaceRevisionConflict):
        preferences.compare_and_set(replace(updated, revision=3), expected_revision=1)
    assert tracer.spans == [
        "surface.sqlite.preference.compare_and_set",
        "surface.sqlite.preference.get",
        "surface.sqlite.preference.get",
        "surface.sqlite.preference.compare_and_set",
        "surface.sqlite.preference.compare_and_set",
    ]


def test_runtime_and_grant_repositories_enforce_full_authority_scope(
    tmp_path: Path,
) -> None:
    repository = _repository(tmp_path)
    descriptor = _descriptor("surface-1", "workspace-1")
    repository.create(descriptor, user_id="user-1", session_id="session-1")
    now = datetime(2026, 7, 30, 12, 0, tzinfo=UTC)
    tracer = RecordingTracer()
    runtimes = SurfaceRuntimeRepository(repository.db_path, tracer=tracer)
    runtime = SurfaceRuntimeRecord(
        runtime_id="runtime-1",
        instance_id="instance-1",
        surface_id="surface-1",
        workspace_id="workspace-1",
        generation=1,
        ownership="launched",
        platform="windows_job",
        state="starting",
        manifest_hash="a" * 64,
        lifetime={"kind": "workspace"},
        limits={"memory_mib": 2048},
        revision=1,
        created_at=now,
        updated_at=now,
    )
    assert runtimes.create(runtime, user_id="user-1", session_id="session-1") == runtime
    assert runtimes.get(
        runtime_id="runtime-1",
        workspace_id="workspace-1",
        user_id="user-1",
        session_id="session-1",
    ) == runtime
    assert (
        runtimes.get(
            runtime_id="runtime-1",
            workspace_id="workspace-1",
            user_id="user-2",
            session_id="session-1",
        )
        is None
    )
    running = replace(
        runtime,
        state="ready",
        revision=2,
        updated_at=datetime(2026, 7, 30, 12, 1, tzinfo=UTC),
    )
    assert runtimes.compare_and_set(
        running,
        expected_revision=1,
        user_id="user-1",
        session_id="session-1",
    ) == running
    with pytest.raises(SurfaceRevisionConflict):
        runtimes.compare_and_set(
            replace(running, revision=3),
            expected_revision=1,
            user_id="user-1",
            session_id="session-1",
        )

    grants = SurfaceGrantRepository(repository.db_path, tracer=tracer)
    grant = SurfaceGrantRecord(
        grant_id="grant-1",
        user_id="user-1",
        workspace_id="workspace-1",
        source_id="brep",
        source_version="manifest-v1",
        instance_id="instance-1",
        capability="tool",
        operation="measure",
        constraints={"maximum_calls": 1},
        risk_tier="mutating",
        persistence="operation",
        decision="allow",
        decision_source="user",
        expires_at=now,
        created_at=now,
    )
    assert grants.create(grant) == grant
    assert grants.list(
        user_id="user-1",
        workspace_id="workspace-1",
        source_id="brep",
        source_version="manifest-v1",
    ) == [grant]
    assert (
        grants.list(
            user_id="user-2",
            workspace_id="workspace-1",
            source_id="brep",
            source_version="manifest-v1",
        )
        == []
    )
    assert tracer.spans == [
        "surface.sqlite.runtime.create",
        "surface.sqlite.runtime.get",
        "surface.sqlite.runtime.get",
        "surface.sqlite.runtime.compare_and_set",
        "surface.sqlite.runtime.compare_and_set",
        "surface.sqlite.grant.create",
        "surface.sqlite.grant.list",
        "surface.sqlite.grant.list",
    ]


def test_generation_provenance_and_diagnostics_require_authorized_scope(
    tmp_path: Path,
) -> None:
    repository = _repository(tmp_path)
    descriptor = _descriptor("surface-1", "workspace-1")
    repository.create(descriptor, user_id="user-1", session_id="session-1")
    now = datetime(2026, 7, 30, 12, 0, tzinfo=UTC)
    with sqlite3.connect(repository.db_path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute(
            """INSERT INTO surface_display_artifacts (
                artifact_id, surface_id, workspace_id, display_id, revision,
                producer_execution_id, representations_json, durability,
                current, created_at
            ) VALUES ('artifact-1', 'surface-1', 'workspace-1', 'loads', 1,
                'execution-1', '[]', 'durable', 1, ?)""",
            (now.isoformat(),),
        )
        connection.commit()
    provenance = GenerationProvenanceReference(
        artifact_id="artifact-1",
        workspace_id="workspace-1",
        mode="agent_generated",
        prompt_vault_digest="sha256:" + "a" * 64,
        no_prompt=False,
        constraints_vault_digest="sha256:" + "b" * 64,
        script_vault_digest="sha256:" + "c" * 64,
        script_content_hash="d" * 64,
        script_revision=1,
        task_id="task-1",
        execution_id="execution-1",
        trace_id="e" * 32,
        created_at=now,
    )
    tracer = RecordingTracer()
    provenance_repository = GenerationProvenanceRepository(
        repository.db_path, tracer=tracer
    )
    assert provenance_repository.create(provenance, user_id="user-1") == provenance
    assert provenance_repository.get(
        artifact_id="artifact-1", workspace_id="workspace-1", user_id="user-1"
    ) == provenance
    assert (
        provenance_repository.get(
            artifact_id="artifact-1", workspace_id="workspace-1", user_id="user-2"
        )
        is None
    )

    event = SurfaceDiagnosticEvent(
        timestamp=now,
        severity=SurfaceSeverity.INFO,
        code="SURFACE_STATE_TRANSITION",
        message="Declared",
        correlation=TraceCorrelation(
            correlation_id="correlation-1", trace_id="f" * 32, span_id="a" * 16
        ),
        retryable=False,
        user_id="user-1",
        workspace_id="workspace-1",
        session_id="session-1",
        surface_id="surface-1",
        attributes={"token": "must-redact"},
    )
    diagnostics = SurfaceDiagnosticRepository(repository.db_path, tracer=tracer)
    diagnostics.record(event, retention_class="workspace")
    assert diagnostics.list(
        workspace_id="workspace-1", user_id="user-1", surface_id="surface-1"
    )[0].attributes == {"token": "[REDACTED]"}
    assert (
        diagnostics.list(
            workspace_id="workspace-1", user_id="user-2", surface_id="surface-1"
        )
        == []
    )
    assert tracer.spans == [
        "surface.sqlite.provenance.create",
        "surface.sqlite.provenance.get",
        "surface.sqlite.provenance.get",
        "surface.sqlite.diagnostic.record",
        "surface.sqlite.diagnostic.list",
        "surface.sqlite.diagnostic.list",
    ]
