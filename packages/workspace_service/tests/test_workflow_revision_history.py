"""A failed correction keeps exact prior files inspectable, never current."""

from copy import deepcopy
import hashlib

import pytest

from workspace_service import workflow_run_record as recorder
from .test_process_recorded_run_read import SOURCE, result_row, saved


def revision_events():
    first = result_row("produce")
    first["representations"][0]["sha256"] = hashlib.sha256(
        b"failed geometry"
    ).hexdigest()
    first["representations"][0]["location"] = "attempts/1/model.csv"
    return first, [
        {"kind": "result_ready", "task_id": "produce", "engineering_result": first},
        {"kind": "design_revision", "invalidated_task_ids": ["produce", "check"]},
        {"kind": "step_started", "task_id": "produce"},
    ]


def test_failed_correction_exposes_prior_exact_files_without_restoring_current_output(
    tmp_path,
):
    first, events = revision_events()
    path, _ = saved(tmp_path, status="failed", events=events, partial_results={})
    before = path.read_bytes()
    view = recorder.read_workflow_run(tmp_path, SOURCE, "run-1", complete_results=True)
    assert view["results"] == []
    (prior,) = view["previous_results"]
    assert prior["producer_attempt"] == "1"
    assert prior["original_result_id"] == first["id"]
    assert prior["result"]["id"] != first["id"]
    assert prior["result"]["representations"] == list(first["representations"])
    assert prior["result"]["provenance"]["task_id"] == first["provenance"]["task_id"]
    assert prior["result"]["provenance"]["run_id"] == first["provenance"]["run_id"]
    assert path.read_bytes() == before
    assert (
        recorder.read_workflow_run(tmp_path, SOURCE, "run-1", complete_results=True)[
            "previous_results"
        ]
        == view["previous_results"]
    )


def test_multiple_revisions_keep_distinct_history_and_only_latest_current(tmp_path):
    first, events = revision_events()
    second = deepcopy(first)
    second["representations"][0].update(
        location="attempts/2/model.csv", sha256="b" * 64
    )
    events += [
        {"kind": "result_ready", "task_id": "produce", "engineering_result": second},
        {"kind": "design_revision", "invalidated_task_ids": ["produce", "check"]},
    ]
    latest = deepcopy(second)
    latest["representations"][0].update(
        location="attempts/3/model.csv", sha256="c" * 64
    )
    saved(tmp_path, status="completed", events=events, result={"results": [latest]})
    view = recorder.read_workflow_run(tmp_path, SOURCE, "run-1", complete_results=True)
    assert [row["id"] for row in view["results"]] == [latest["id"]]
    assert [row["producer_attempt"] for row in view["previous_results"]] == ["1", "2"]
    assert len({row["result"]["id"] for row in view["previous_results"]}) == 2


def test_prior_result_inventory_has_same_bounds_as_current_results(
    tmp_path, monkeypatch
):
    _, events = revision_events()
    saved(tmp_path, status="failed", events=events, partial_results={})
    monkeypatch.setattr(recorder, "_MAX_RESULT_INVENTORY_ITEMS", 0)
    with pytest.raises(recorder.WorkflowRunReadError, match="inventory"):
        recorder.read_workflow_run(tmp_path, SOURCE, "run-1", complete_results=True)


def test_history_cannot_promote_unpinned_or_live_application_references(tmp_path):
    first, events = revision_events()
    first["representations"] = [
        {"kind": "value", "location": "steps/produce/response", "format": "text"}
    ]
    saved(tmp_path, status="failed", events=events, partial_results={})
    view = recorder.read_workflow_run(tmp_path, SOURCE, "run-1", complete_results=True)
    assert view["previous_results"] == []


def test_mixed_run_history_is_rejected(tmp_path):
    first, events = revision_events()
    first["provenance"]["run_id"] = "another-run"
    saved(tmp_path, status="failed", events=events, partial_results={})
    with pytest.raises(recorder.WorkflowRunReadError, match="identities disagree"):
        recorder.read_workflow_run(tmp_path, SOURCE, "run-1", complete_results=True)
