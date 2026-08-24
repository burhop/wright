from __future__ import annotations

import sqlite3
from datetime import UTC, datetime

import pytest

from data_vault import (
    WorkspaceArtifactConflict,
    WorkspaceArtifactRecord,
    WorkspaceArtifactRepository,
    upgrade_database,
)
from data_vault.migrations import MIGRATIONS


def test_workspace_artifact_migration_is_additive_and_contiguous(tmp_path) -> None:
    database = tmp_path / "migration-17.db"
    prior = upgrade_database(database, migrations=MIGRATIONS[:16])

    result = upgrade_database(database)

    assert prior.ending_version == 16
    assert result.applied == ({"version": 17, "name": "workspace_document_artifacts"},)
    assert [migration.version for migration in MIGRATIONS] == list(range(1, 18))
    with sqlite3.connect(database) as connection:
        assert connection.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name='workspace_artifacts'"
        ).fetchone() == ("workspace_artifacts",)


def _seed(path) -> None:
    upgrade_database(path)
    with sqlite3.connect(path) as connection:
        connection.execute(
            """INSERT INTO engineering_workspaces
            (workspace_id, session_id, local_path, created_at, updated_at)
            VALUES ('w1', 's1', '/work/w1', 1, 1)"""
        )
        connection.execute(
            """INSERT INTO workspace_workflow_runs
            (run_id, workspace_id, session_id, workflow_id, revision, digest,
             graph, state, generation, output_truncated)
            VALUES ('run-1', 'w1', 's1', 'flow-1', 1, ?, 'Main',
                    'succeeded', 1, 0)""",
            ("a" * 64,),
        )
        connection.commit()


def _record(**changes) -> WorkspaceArtifactRecord:
    values = {
        "artifact_id": "artifact-1",
        "workspace_id": "w1",
        "session_id": "s1",
        "principal_id": "p1",
        "relative_path": "reports/review.md",
        "media_type": "text/markdown",
        "sha256": "b" * 64,
        "byte_count": 12,
        "producer_provider_id": "wright-workspace-files",
        "producer_tool_name": "wright-workspace-files__write_text_document",
        "producer_declaration_digest": "c" * 64,
        "request_id": "request-1",
        "correlation_id": "trace-1",
        "created_at": datetime(2026, 8, 21, tzinfo=UTC),
    }
    values.update(changes)
    return WorkspaceArtifactRecord(**values)


def test_artifact_identity_is_insert_only_and_restart_safe(tmp_path) -> None:
    database = tmp_path / "state.db"
    _seed(database)
    repository = WorkspaceArtifactRepository(str(database))
    record = _record()

    repository.insert(record)
    repository.insert(record)
    restarted = WorkspaceArtifactRepository(str(database))

    assert restarted.get("artifact-1", workspace_id="w1") == record
    assert restarted.list_for_scope(workspace_id="w1", session_id="s1") == (record,)
    assert restarted.get("artifact-1", workspace_id="other") is None
    with pytest.raises(WorkspaceArtifactConflict, match="immutable"):
        repository.insert(_record(sha256="d" * 64))


def test_run_linkage_is_scoped_idempotent_and_immutable(tmp_path) -> None:
    database = tmp_path / "state.db"
    _seed(database)
    repository = WorkspaceArtifactRepository(str(database))
    record = _record()
    repository.insert(record)

    repository.link_run(
        artifact_id=record.artifact_id,
        workspace_id="w1",
        session_id="s1",
        run_id="run-1",
        linked_at=datetime.now(UTC),
    )
    repository.link_run(
        artifact_id=record.artifact_id,
        workspace_id="w1",
        session_id="s1",
        run_id="run-1",
        linked_at=datetime.now(UTC),
    )

    assert (
        repository.get_for_run(
            workspace_id="w1",
            session_id="s1",
            run_id="run-1",
            artifact_id="artifact-1",
        )
        == record
    )
    assert (
        repository.get_for_run(
            workspace_id="w1",
            session_id="other",
            run_id="run-1",
            artifact_id="artifact-1",
        )
        is None
    )
