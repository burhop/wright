from dataclasses import replace
import json

import pytest

from data_vault import workflow_continuation_repository as c
from data_vault import workflow_artifact_review_repository as a


def checkpoint(index, **changes):
    return replace(
        c.WorkflowContinuationCheckpoint(
            checkpoint_id=f"checkpoint-{index:04}",
            workspace_id="workspace-a",
            workflow_id="workflows/handle.wflow",
            run_id=f"run-{index}",
            step_id="review",
            action_kind="local_review",
            subject={"private_evidence": "must not leave owner"},
            subject_digest=f"{index:064x}",
            state="pending",
            continuation={
                "run_log_path": f"runs/{index}.json",
                "source_digest": "a" * 64,
                "step_title": "Review strength results",
                "execution_context": {"private": True},
            },
            actor=None,
            reason=None,
            created_at=index,
            updated_at=index,
            expires_at=None,
            external_action=None,
        ),
        **changes,
    )


def test_workspace_query_reaches_old_pending_beyond_history_and_keeps_authority(
    tmp_path,
):
    repo = c.WorkflowContinuationRepository(str(tmp_path / "state.db"))
    old = checkpoint(0, expires_at=1)
    repo.create(old)
    for i in range(1, 130):
        repo.create(checkpoint(i, state="consumed"))
    repo.create(checkpoint(130, workspace_id="workspace-b"))
    page = repo.pending_navigation("workspace-a")
    assert [r["run_id"] for r in page["items"]] == ["run-0"]
    assert page["items"][0]["expires_at"] == 1
    assert page["items"][0]["source_digest"] == "a" * 64
    assert "private" not in json.dumps(page)
    assert repo.get(old.checkpoint_id) == old
    assert page["next_cursor"] is None


def test_continuation_pagination_preserves_input_review_action_and_answered_states(
    tmp_path,
):
    repo = c.WorkflowContinuationRepository(str(tmp_path / "state.db"))
    for i in range(23):
        repo.create(checkpoint(i))
    special = checkpoint(
        24,
        action_kind="human_input",
        continuation={
            "checkpoint_kind": "input",
            "response_id": "answer-1",
            "run_log_path": "runs/24.json",
            "source_digest": "b" * 64,
        },
    )
    repo.create(special)
    repo.create(checkpoint(25, action_kind="printer_transfer", state="approved"))
    first = repo.pending_navigation("workspace-a")
    second = repo.pending_navigation("workspace-a", after=first["next_cursor"])
    rows = first["items"] + second["items"]
    assert len(rows) == len({r["checkpoint_id"] for r in rows}) == 25
    assert rows[-2]["checkpoint_kind"] == "input"
    assert rows[-2]["response_id"] == "answer-1"
    assert rows[-1]["state"] == "approved"
    assert rows[-1]["action_kind"] == "printer_transfer"
    assert second["next_cursor"] is None
    assert repo.get(special.checkpoint_id) == special


def test_terminal_reviews_paginate_without_snapshots_or_other_workspace(tmp_path):
    repo = a.WorkflowArtifactReviewRepository(str(tmp_path / "state.db"))
    for i in range(25):
        repo.create(
            f"review-{i:04}",
            "workspace-a",
            "workflows/handle.wflow",
            f"{i:064x}",
            {
                "summary": {
                    "run_id": f"run-{i}",
                    "run_log_path": f"runs/{i}.json",
                    "source_digest": "c" * 64,
                    "task_id": "review",
                    "task_title": "Review CAD",
                },
                "snapshots": [{"content_base64": "private-body"}],
                "input_values": {"private": "original values"},
            },
        )
    repo.create("review-other", "workspace-b", "other.wflow", "f" * 64, {})
    before = repo.get("workspace-a", "review-0000")
    repo.decide("workspace-a", "review-0024", f"{24:064x}", {"state": "approved"})
    first = repo.pending_navigation("workspace-a")
    second = repo.pending_navigation("workspace-a", after=first["next_cursor"])
    rows = first["items"] + second["items"]
    assert len(rows) == len({r["review_id"] for r in rows}) == 24
    assert all(r["workflow_path"] == "workflows/handle.wflow" for r in rows)
    assert all(r["source_digest"] == "c" * 64 for r in rows)
    assert "private" not in json.dumps(rows)
    assert second["next_cursor"] is None
    assert repo.get("workspace-a", "review-0000") == before


@pytest.mark.parametrize("limit", [0, -1, 51])
def test_page_bounds(tmp_path, limit):
    for repo in [
        c.WorkflowContinuationRepository(str(tmp_path / "c.db")),
        a.WorkflowArtifactReviewRepository(str(tmp_path / "a.db")),
    ]:
        with pytest.raises(ValueError):
            repo.pending_navigation("workspace-a", limit=limit)
