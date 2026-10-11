"""Exact run attachment reads the recorder; it neither retries nor edits a run."""

import hashlib
import json
import socket

import pytest

from workspace_service import workflow_run_record as recorder


SOURCE = "workflows/example.workflow.wflow"


def result_row(task):
    from workspace_service.workflow_results import Provenance, file_result

    return file_result(
        {"output_path": task + ".csv", "output_format": "csv", "output_bytes": 8},
        Provenance("run-1", task, "result"),
    ).to_dict()


def saved(
    root, run_id="run-1", *, name="20260930T120000Z-aaaaaaaaaaaa.json", **changes
):
    source = root / SOURCE
    source.parent.mkdir(parents=True, exist_ok=True)
    if not source.exists():
        source.write_text("workflow example\nend", encoding="utf-8")
    record = {
        "workflow_path": SOURCE,
        "source_digest": hashlib.sha256(source.read_bytes()).hexdigest(),
        "run_id": run_id,
        "status": "running",
        "started_at": "2026-09-30T12:00:00Z",
        "owner": {"host": socket.gethostname(), "lease": "controlled"},
        "events": [],
        **changes,
    }
    path = root / "runs/example" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record), encoding="utf-8")
    return path, record


@pytest.fixture(autouse=True)
def active_owner(monkeypatch):
    monkeypatch.setattr(
        "workspace_service.workflow_resource_lease.lease_is_active", lambda _: True
    )


def test_initial_record_identifies_run_before_any_result(tmp_path):
    path, _ = saved(tmp_path)
    original = path.read_bytes()
    view = recorder.read_workflow_run(tmp_path, SOURCE, "run-1")
    assert view["run_id"] == "run-1"
    assert view["status"] == "running"
    assert view["execution"]["event_count"] == 0
    assert view["source_matches_current"] is True
    assert view["results"] == []
    assert path.read_bytes() == original


@pytest.mark.parametrize(
    "status", ["running", "failed", "awaiting_approval", "cancelled"]
)
def test_current_continuation_results_survive_a_stale_earlier_segment(tmp_path, status):
    basis, numerical = result_row("basis"), result_row("numerical")
    events = [
        {"kind": "output_saved", "task_id": task, "output_path": task + ".csv"}
        for task in ("basis", "numerical")
    ]
    path, _ = saved(
        tmp_path,
        status=status,
        events=events,
        partial_results={row["id"]: row for row in (basis, numerical)},
        result={"run_id": "run-1", "results": [basis], "outputs": [events[0]]},
    )
    original = path.read_bytes()
    view = recorder.read_workflow_run(tmp_path, SOURCE, "run-1")
    assert {row["id"] for row in view["results"]} == {basis["id"], numerical["id"]}
    assert {row["output_path"] for row in view["execution"]["outputs"]} == {
        "basis.csv",
        "numerical.csv",
    }
    history = recorder.recent_workflow_runs(tmp_path, SOURCE, latest_only=False)
    assert {row["id"] for row in history[0]["results"]} == {
        basis["id"],
        numerical["id"],
    }
    assert path.read_bytes() == original


def test_empty_current_results_preserve_invalidation_after_a_prior_wait(tmp_path):
    basis = result_row("basis")
    saved(
        tmp_path,
        status="failed",
        partial_results={},
        result={"run_id": "run-1", "results": [basis]},
    )
    assert recorder.read_workflow_run(tmp_path, SOURCE, "run-1")["results"] == []
    assert recorder.recent_workflow_runs(tmp_path, SOURCE)[0]["results"] == []


def test_completed_segment_uses_its_final_result_authority(tmp_path):
    earlier, final = result_row("earlier"), result_row("final")
    saved(
        tmp_path,
        status="completed",
        partial_results={earlier["id"]: earlier},
        result={"run_id": "run-1", "results": [final]},
    )
    view = recorder.read_workflow_run(tmp_path, SOURCE, "run-1")
    assert [row["id"] for row in view["results"]] == [final["id"]]


def test_attachment_finds_requested_run_instead_of_latest(tmp_path):
    saved(tmp_path, "newer", name="20260930T120100Z-bbbbbbbbbbbb.json")
    path, _ = saved(tmp_path, "older", status="completed")
    view = recorder.read_workflow_run(tmp_path, SOURCE, "older")
    assert view["run_id"] == "older" and view["status"] == "completed"
    assert view["path"] == path.relative_to(tmp_path).as_posix()


@pytest.mark.parametrize(
    "owner_state, expected",
    [(True, "running"), (False, "interrupted"), (None, "unknown")],
)
def test_attachment_reuses_lease_observation(
    tmp_path, monkeypatch, owner_state, expected
):
    monkeypatch.setattr(
        "workspace_service.workflow_resource_lease.lease_is_active",
        lambda _: owner_state,
    )
    path, _ = saved(tmp_path)
    original = path.read_bytes()
    assert recorder.read_workflow_run(tmp_path, SOURCE, "run-1")["status"] == expected
    assert (
        recorder.recent_workflow_runs(tmp_path, SOURCE, latest_only=True)[0]["status"]
        == expected
    )
    assert path.read_bytes() == original


def test_foreign_or_unreadable_owner_does_not_prove_interruption(tmp_path, monkeypatch):
    saved(tmp_path, owner={"host": "another-host", "lease": "controlled"})
    assert recorder.read_workflow_run(tmp_path, SOURCE, "run-1")["status"] == "unknown"

    def unreadable(_):
        raise OSError("lease inaccessible")

    monkeypatch.setattr(
        "workspace_service.workflow_resource_lease.lease_is_active", unreadable
    )
    saved(tmp_path)
    assert recorder.read_workflow_run(tmp_path, SOURCE, "run-1")["status"] == "unknown"


def test_source_change_preserves_original_run_identity(tmp_path):
    _, record = saved(tmp_path)
    (tmp_path / SOURCE).write_text("changed source", encoding="utf-8")
    view = recorder.read_workflow_run(tmp_path, SOURCE, "run-1")
    assert view["source_digest"] == record["source_digest"]
    assert view["source_matches_current"] is False


def test_compact_view_omits_native_payload_and_exposes_only_owner_references(tmp_path):
    saved(
        tmp_path,
        status="awaiting_approval",
        events=[
            {
                "kind": "tool_completed",
                "arguments": {"token": "PRIVATE"},
                "result": "PRIVATE",
            }
        ],
        approval={
            "checkpoint_id": "checkpoint-1",
            "subject_digest": "a" * 64,
            "continuation": {"private": "PRIVATE"},
        },
        review={
            "review_id": "review-1",
            "package_digest": "b" * 64,
            "input_values": "PRIVATE",
        },
    )
    view = recorder.read_workflow_run(tmp_path, SOURCE, "run-1")
    assert view["approval"] == {
        "checkpoint_id": "checkpoint-1",
        "subject_digest": "a" * 64,
    }
    assert view["review"] == {"review_id": "review-1", "package_digest": "b" * 64}
    assert "PRIVATE" not in json.dumps(view)


def test_legacy_run_without_top_identity_is_restored_from_result(tmp_path):
    path, record = saved(tmp_path, result={"run_id": "legacy", "results": []})
    del record["run_id"]
    path.write_text(json.dumps(record), encoding="utf-8")
    assert recorder.read_workflow_run(tmp_path, SOURCE, "legacy")["run_id"] == "legacy"


@pytest.mark.parametrize(
    "changes",
    [
        {"workflow_path": "workflows/other.workflow.wflow"},
        {"result": {"run_id": "another"}},
        {"events": ["not an event"]},
        {"result": []},
        {"partial_results": []},
        {"status": "invented"},
    ],
)
def test_bad_or_other_source_record_cannot_attach(tmp_path, changes):
    saved(tmp_path, **changes)
    with pytest.raises(recorder.WorkflowRunReadError):
        recorder.read_workflow_run(tmp_path, SOURCE, "run-1")


def test_duplicate_run_identity_is_explicit_not_random_file_selection(tmp_path):
    saved(tmp_path)
    saved(tmp_path, name="20260930T120100Z-bbbbbbbbbbbb.json")
    with pytest.raises(recorder.WorkflowRunReadError) as error:
        recorder.read_workflow_run(tmp_path, SOURCE, "run-1")
    assert error.value.code == "ambiguous"


@pytest.mark.parametrize(
    "hint",
    [
        "../outside.json",
        "C:/outside.json",
        "runs/other/file.json",
        "workflows/example.workflow.wflow",
    ],
)
def test_log_hint_is_confined_to_exact_source_run_folder(tmp_path, hint):
    saved(tmp_path)
    with pytest.raises(recorder.WorkflowRunReadError):
        recorder.read_workflow_run(tmp_path, SOURCE, "run-1", run_log_path=hint)


def test_hint_still_requires_exact_run_and_source(tmp_path):
    path, _ = saved(tmp_path)
    hint = path.relative_to(tmp_path).as_posix()
    with pytest.raises(recorder.WorkflowRunReadError):
        recorder.read_workflow_run(tmp_path, SOURCE, "another", run_log_path=hint)
    assert (
        recorder.read_workflow_run(tmp_path, SOURCE, "run-1", run_log_path=hint)[
            "run_id"
        ]
        == "run-1"
    )


def test_exhausted_fallback_is_unresolved_until_server_owned_locator_available(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(recorder, "_MAX_RUN_READ_FILES", 1)
    path, _ = saved(tmp_path, "older")
    saved(tmp_path, "newer", name="20260930T120100Z-bbbbbbbbbbbb.json")
    with pytest.raises(recorder.WorkflowRunReadError) as error:
        recorder.read_workflow_run(tmp_path, SOURCE, "older")
    assert error.value.code == "read_limit"
    assert (
        recorder.read_workflow_run(
            tmp_path,
            SOURCE,
            "older",
            run_log_path=path.relative_to(tmp_path).as_posix(),
        )["run_id"]
        == "older"
    )


def test_oversized_record_is_not_read_as_partial_truth(tmp_path, monkeypatch):
    monkeypatch.setattr(recorder, "_MAX_RUN_RECORD_BYTES", 100)
    path, _ = saved(tmp_path)
    with pytest.raises(recorder.WorkflowRunReadError) as error:
        recorder.read_workflow_run(
            tmp_path,
            SOURCE,
            "run-1",
            run_log_path=path.relative_to(tmp_path).as_posix(),
        )
    assert error.value.code == "invalid"


def test_extended_run_retains_requests_and_projects_actual_failure(tmp_path):
    path, _ = saved(
        tmp_path,
        status="failed",
        code="WORKFLOW_INTEGRATION_POLICY_INVALID",
        error="A declared evidence file is unavailable.",
        correction="Correct the producer declaration before a new run.",
        events=[
            {
                "kind": "model_invocation",
                "task_id": "research",
                "invocation": {
                    "request_fields": {"instructions": "x" * (20 * 1024 * 1024)}
                },
            }
        ],
    )
    original_digest = hashlib.sha256(path.read_bytes()).hexdigest()
    view = recorder.read_workflow_run(
        tmp_path, SOURCE, "run-1", run_log_path=path.relative_to(tmp_path).as_posix()
    )
    assert view["status"] == "failed"
    assert view["code"] == "WORKFLOW_INTEGRATION_POLICY_INVALID"
    assert view["error"] == "A declared evidence file is unavailable."
    assert len(json.dumps(view)) < 10_000
    assert hashlib.sha256(path.read_bytes()).hexdigest() == original_digest


def test_rework_removes_invalidated_output_from_attachment(tmp_path):
    saved(
        tmp_path,
        events=[
            {"kind": "step_completed", "task_id": "produce"},
            {"kind": "output_saved", "task_id": "produce", "output_path": "old.stl"},
            {"kind": "design_revision", "invalidated_task_ids": ["produce"]},
        ],
    )
    view = recorder.read_workflow_run(tmp_path, SOURCE, "run-1")
    assert view["execution"]["completed_task_ids"] == []
    assert view["execution"]["outputs"] == []


def test_missing_run_does_not_create_files(tmp_path):
    path, _ = saved(tmp_path)
    files = {
        p.relative_to(tmp_path).as_posix(): p.read_bytes()
        for p in tmp_path.rglob("*")
        if p.is_file()
    }
    with pytest.raises(recorder.WorkflowRunReadError) as error:
        recorder.read_workflow_run(tmp_path, SOURCE, "missing")
    assert error.value.code == "not_found"
    assert {
        p.relative_to(tmp_path).as_posix(): p.read_bytes()
        for p in tmp_path.rglob("*")
        if p.is_file()
    } == files
    assert path.exists()


def test_interaction_inventory_keeps_later_results_past_progress_budget(tmp_path):
    rows = [
        result_row(f"engineering-stage-{index:03d}-" + "a" * 120)
        for index in range(160)
    ]
    path, _ = saved(
        tmp_path,
        status="awaiting_approval",
        partial_results={row["id"]: row for row in rows},
    )
    original = path.read_bytes()
    progress = recorder.read_workflow_run(tmp_path, SOURCE, "run-1")
    assert len(progress["results"]) < len(rows)  # Actual legacy progress ceiling.
    view = recorder.read_workflow_run(tmp_path, SOURCE, "run-1", complete_results=True)
    assert [row["id"] for row in view["results"]] == [row["id"] for row in rows]
    assert not view["execution"]["truncated"]
    assert path.read_bytes() == original


def test_inventory_limit_is_explicit_and_does_not_return_partial_results(
    tmp_path, monkeypatch
):
    row = result_row("drawing")
    path, _ = saved(tmp_path, partial_results={row["id"]: row})
    original = path.read_bytes()
    monkeypatch.setattr(recorder, "_MAX_RESULT_INVENTORY_BYTES", 10)
    with pytest.raises(recorder.WorkflowRunReadError) as caught:
        recorder.read_workflow_run(tmp_path, SOURCE, "run-1", complete_results=True)
    assert caught.value.code == "result_inventory_limit"
    assert path.read_bytes() == original


def test_full_inventory_rejects_foreign_result_after_legacy_cutoff(tmp_path):
    rows = [
        result_row(f"engineering-stage-{index:03d}-" + "a" * 120)
        for index in range(160)
    ]
    rows[-1]["provenance"]["run_id"] = "foreign-run"
    saved(tmp_path, partial_results={row["id"]: row for row in rows})
    with pytest.raises(recorder.WorkflowRunReadError) as caught:
        recorder.read_workflow_run(tmp_path, SOURCE, "run-1", complete_results=True)
    assert caught.value.code == "invalid"


def test_inventory_does_not_inherit_another_runs_metadata_limit(tmp_path, monkeypatch):
    row = result_row("drawing")
    saved(
        tmp_path,
        "another",
        name="20260930T120100Z-bbbbbbbbbbbb.json",
        partial_results={row["id"]: row},
    )
    saved(tmp_path, "run-1")
    monkeypatch.setattr(recorder, "_MAX_RESULT_INVENTORY_BYTES", 10)
    view = recorder.read_workflow_run(tmp_path, SOURCE, "run-1", complete_results=True)
    assert view["results"] == []
