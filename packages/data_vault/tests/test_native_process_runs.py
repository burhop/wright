from __future__ import annotations

import hashlib
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier

import pytest

from core.native_process import validate_definition
from data_vault.migrations import upgrade_database
from data_vault.native_process_repository import NativeRepositoryError
from data_vault.native_process_runs import NativeRunRepository
from data_vault.state_store import connect_state_db

ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture
def runs(tmp_path):
    path = tmp_path / "state.db"
    upgrade_database(path)
    with connect_state_db(path) as connection:
        for name in ("one", "two"):
            connection.execute(
                """INSERT INTO engineering_workspaces
                (workspace_id,session_id,local_path,created_at,updated_at) VALUES (?,?,?,1,1)""",
                (name, "session-" + name, "/workspace/" + name),
            )
    repository = NativeRunRepository(str(path))
    definition = validate_definition(
        (
            ROOT / "src/wright_engineering/static/native-processes/concept-brief.json"
        ).read_bytes()
    )
    saved = repository.save(
        "one",
        definition,
        {},
        request_id="document",
        expected_token=None,
        trace_id="save-trace",
    )
    return repository, saved


def create(runs, request_id="run-request", **overrides):
    repository, saved = runs
    args = {
        "session_id": "session-one",
        "expected_token": saved["token"],
        "request_id": request_id,
        "bindings": {},
        "timeout_seconds": 60,
        "derived_from_run_id": None,
        "actor": "engineer",
        "trace_id": "run-trace",
    }
    args.update(overrides)
    return repository.create_run("one", saved["definition"]["id"], **args)


def reason():
    return {
        "code": "ASSERTION_FAILED",
        "message": "Independent output assertion failed.",
        "recovery": "Correct the input and create a linked run.",
        "step_id": "need-source",
        "port_id": None,
    }


def test_snapshot_replay_and_terminal_evidence_are_immutable(runs):
    repository, saved = runs
    queued = create(runs)
    run_id = queued["run_id"]
    observed = repository.inspect("one", run_id)
    assert observed["snapshot"]["definition"] == saved["definition"]
    changed = {**saved["definition"], "title": "Later change"}
    repository.save(
        "one",
        validate_definition(changed),
        {},
        request_id="later",
        expected_token=saved["token"],
        trace_id="later-trace",
    )
    assert repository.inspect("one", run_id)["snapshot"] == observed["snapshot"]
    assert create(runs) == queued
    assert repository.start("one", run_id)
    for step in observed["steps"]:
        assert repository.start_step("one", run_id, step["step_id"], {})
        assert repository.complete_step("one", run_id, step["step_id"], {})
    terminal = repository.finish("one", run_id, "succeeded")
    assert terminal["state"] == "succeeded"
    assert repository.finish("one", run_id, "cancelled") == terminal
    assert not repository.start("one", run_id)
    assert create(runs) == queued
    events = repository.events("one", run_id)["events"]
    assert [event["sequence"] for event in events] == list(range(1, len(events) + 1))
    assert {event["trace_id"] for event in events} == {"run-trace"}
    assert events[-1]["kind"] == "run.succeeded"
    with pytest.raises(NativeRepositoryError) as error:
        create(runs, timeout_seconds=61)
    assert error.value.code == "NATIVE_REQUEST_REUSED"


def test_first_failure_records_dependents_and_independent_unstarted_steps(runs):
    repository, _ = runs
    run_id = create(runs)["run_id"]
    repository.start("one", run_id)
    repository.start_step("one", run_id, "need-source", {})
    repository.finish(
        "one", run_id, "failed", reason=reason(), failed_step_id="need-source"
    )
    observed = repository.inspect("one", run_id)
    states = {step["step_id"]: step for step in observed["steps"]}
    assert states["need-source"]["state"] == "failed"
    assert states["constraint-source"]["state"] == "cancelled"
    assert states["brief-compose"]["state"] == "blocked"
    assert states["brief-compose"]["reason"]["step_id"] == "need-source"
    assert observed["reason"] == reason()
    assert all(step["completed_at"] for step in states.values())


def test_queued_cancel_and_late_step_or_artifact_cannot_publish(runs):
    repository, _ = runs
    run_id = create(runs)["run_id"]
    repository.finish("one", run_id, "cancelled")
    assert not repository.start("one", run_id)
    assert not repository.start_step("one", run_id, "need-source", {})
    assert not repository.complete_step(
        "one", run_id, "need-source", {}, artifacts=({},)
    )
    observed = repository.inspect("one", run_id)
    assert observed["artifacts"] == []
    assert {step["state"] for step in observed["steps"]} == {"cancelled"}


def test_concurrent_terminal_transitions_have_exactly_one_committed_winner(runs):
    repository, _ = runs
    run_id = create(runs)["run_id"]
    repository.start("one", run_id)
    barrier = Barrier(2)

    def finish(state):
        barrier.wait()
        return repository.finish("one", run_id, state)

    with ThreadPoolExecutor(max_workers=2) as executor:
        terminal = list(executor.map(finish, ("cancelled", "timed_out")))
    assert terminal[0] == terminal[1]
    events = repository.events("one", run_id)["events"]
    assert (
        sum(event["kind"] in {"run.cancelled", "run.timed_out"} for event in events)
        == 1
    )


def test_success_requires_completed_steps_and_scope_is_enforced(runs):
    repository, _ = runs
    run_id = create(runs)["run_id"]
    repository.start("one", run_id)
    with pytest.raises(NativeRepositoryError):
        repository.finish("one", run_id, "succeeded")
    for operation in (
        repository.inspect,
        repository.summary,
        repository.start,
        repository.events,
    ):
        with pytest.raises(NativeRepositoryError) as error:
            operation("two", run_id)
        assert error.value.code == "NATIVE_NOT_FOUND"
    assert repository.summary("one", run_id)["state"] == "running"


def test_restart_marks_only_nonterminal_runs_and_links_new_evidence(runs):
    repository, _ = runs
    active = create(runs)["run_id"]
    repository.start("one", active)
    cancelled = create(runs, "cancelled")["run_id"]
    repository.finish("one", cancelled, "cancelled")
    assert repository.interrupt_abandoned() == 1
    assert repository.summary("one", active)["state"] == "interrupted"
    assert repository.summary("one", cancelled)["state"] == "cancelled"
    linked = create(runs, "linked", derived_from_run_id=active)["run_id"]
    assert repository.inspect("one", linked)["derived_from_run_id"] == active
    assert (
        repository.inspect("one", linked)["snapshot"]
        == repository.inspect("one", active)["snapshot"]
    )


def test_history_and_event_cursors_are_bounded_and_ordered(runs):
    repository, saved = runs
    ids = [create(runs, f"run-{index}")["run_id"] for index in range(3)]
    page = repository.history("one", saved["definition"]["id"], limit=2)
    last = repository.history(
        "one", saved["definition"]["id"], limit=2, cursor=page["next_cursor"]
    )
    assert [run["run_id"] for run in page["runs"] + last["runs"]] == list(reversed(ids))
    assert last["next_cursor"] is None
    repository.start("one", ids[0])
    first = repository.events("one", ids[0], limit=1)
    second = repository.events("one", ids[0], after_sequence=first["next_sequence"])
    assert first["events"][0]["kind"] == "run.queued"
    assert second["events"][0]["kind"] == "run.started"
    with pytest.raises(NativeRepositoryError):
        repository.events("one", ids[0], limit=201)


def test_artifact_index_step_result_and_event_commit_together(runs):
    repository, _ = runs
    run_id = create(runs)["run_id"]
    repository.start("one", run_id)
    repository.start_step("one", run_id, "brief-file", {})
    record = {
        "artifact_id": "fixture-artifact",
        "port_id": "brief-file-output-artifact",
        "filename": "brief.md",
        "storage_key": "generated/blob",
        "content_digest": hashlib.sha256(b"ok").hexdigest(),
        "size": 2,
        "media_type": "text/markdown",
        "provenance": {"operation": "artifact.write-text@1"},
    }
    with connect_state_db(repository.db_path) as connection:
        connection.execute("""CREATE TRIGGER fail_step_event BEFORE INSERT ON native_process_events
            WHEN NEW.kind='step.succeeded' BEGIN SELECT RAISE(ABORT,'injected commit fault'); END""")
    with pytest.raises(sqlite3.IntegrityError):
        repository.complete_step("one", run_id, "brief-file", {}, artifacts=(record,))
    observed = repository.inspect("one", run_id)
    assert observed["artifacts"] == []
    assert (
        next(step for step in observed["steps"] if step["step_id"] == "brief-file")[
            "state"
        ]
        == "running"
    )
    assert not any(
        event["kind"] == "artifact.indexed"
        for event in repository.events("one", run_id)["events"]
    )
    with connect_state_db(repository.db_path) as connection:
        connection.execute("DROP TRIGGER fail_step_event")
    assert repository.complete_step(
        "one", run_id, "brief-file", {}, artifacts=(record,)
    )
    assert (
        repository.artifact("one", run_id, "fixture-artifact")["content_digest"]
        == record["content_digest"]
    )
    repository.finish("one", run_id, "failed", reason=reason())
    assert len(repository.inspect("one", run_id)["artifacts"]) == 1


def test_value_budget_rejects_before_step_mutation(runs):
    repository, _ = runs
    run_id = create(runs)["run_id"]
    repository.start("one", run_id)
    with pytest.raises(NativeRepositoryError) as error:
        repository.start_step(
            "one", run_id, "need-source", {"input": "x" * 1024 * 1024}
        )
    assert error.value.code == "NATIVE_LIMIT"
    assert repository.inspect("one", run_id)["steps"][0]["state"] == "pending"
