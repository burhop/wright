from __future__ import annotations

from dataclasses import replace
import sqlite3

import pytest

from data_vault import (
    WorkflowRunEventRecord,
    WorkflowRunRecord,
    WorkflowRunRepository,
    upgrade_database,
)


def _run(state: str = "queued") -> WorkflowRunRecord:
    return WorkflowRunRecord(
        run_id="run-1",
        workspace_id="workspace-1",
        session_id="session-1",
        workflow_id="workflow-1",
        revision=3,
        digest="a" * 64,
        graph="Main",
        state=state,
        generation=1,
        started_at=100,
        completed_at=None,
        reason_code=None,
        output_summary=None,
        output_truncated=False,
    )


def _prepare(database) -> WorkflowRunRepository:
    upgrade_database(database)
    with sqlite3.connect(database) as connection:
        connection.execute(
            """INSERT INTO engineering_workspaces
            (workspace_id, session_id, local_path, created_at, updated_at)
            VALUES ('workspace-1', 'session-1', '.', 1, 1)"""
        )
        connection.commit()
    return WorkflowRunRepository(str(database))


def test_run_repository_preserves_immutable_workflow_identity(tmp_path):
    database = tmp_path / "state.db"
    repository = _prepare(database)
    repository.create(_run())

    with pytest.raises(ValueError, match="identity"):
        repository.create(replace(_run(), workflow_id="other"))

    assert repository.get("run-1") == _run()


def test_run_repository_enforces_terminal_transitions_and_bounded_results(tmp_path):
    database = tmp_path / "state.db"
    repository = _prepare(database)
    repository.maximum_output_bytes = 64
    repository.create(_run())
    repository.transition("run-1", "running")
    repository.transition(
        "run-1", "succeeded", completed_at=110, output_summary={"output": "ok"}
    )

    with pytest.raises(ValueError, match="terminal"):
        repository.transition("run-1", "running")
    with pytest.raises(ValueError, match="output"):
        repository.create(
            replace(_run(), run_id="run-2", output_summary={"large": "x" * 100})
        )


def test_run_events_are_sequenced_and_bounded(tmp_path):
    database = tmp_path / "state.db"
    repository = _prepare(database)
    repository.maximum_event_bytes = 64
    repository.create(_run())
    repository.append_event(
        WorkflowRunEventRecord("run-1", 1, 101, "queued", {"message": "ready"})
    )
    with pytest.raises(ValueError, match="sequence"):
        repository.append_event(WorkflowRunEventRecord("run-1", 1, 102, "started", {}))
    with pytest.raises(ValueError, match="event"):
        repository.append_event(
            WorkflowRunEventRecord("run-1", 2, 103, "progress", {"message": "x" * 100})
        )
    assert repository.events("run-1") == (
        WorkflowRunEventRecord("run-1", 1, 101, "queued", {"message": "ready"}),
    )
