"""Scoped dev delivery keeps exact review and pending acceptance separate."""

from __future__ import annotations

import copy
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from program_control.git_subject import GitReader
from program_control.json_contracts import canonical_digest, validate_schema
from program_control.validation import (
    NATIVE_REVIEWED_STATES,
    _validate_native_delivery_review,
    _validate_state_chain,
    validate_roadmap_approval_and_lease,
)


ROOT = "docs/programs/engineering-process-platform"
REVIEW = "evidence/reviews/NATIVE-REVIEW-TEST-001.json"
NOW = datetime(2026, 9, 5, tzinfo=timezone.utc)


@pytest.fixture
def candidate(git_builder, repository_root: Path):
    names = (
        "program-state.json",
        "roadmap.json",
        "decision-register.json",
        "risk-register.json",
        "lifecycle-policy.json",
        "gate-catalog.json",
        "work-registry.json",
        "schemas/native-candidate-review.schema.json",
        "schemas/program-state.schema.json",
    )
    docs = {
        f"{ROOT}/{name}": json.loads(
            (repository_root / ROOT / name).read_text(encoding="utf-8")
        )
        for name in names
    }
    git_builder.write_json(
        f"{ROOT}/work-registry.json", docs[f"{ROOT}/work-registry.json"]
    )
    git_builder.write_bytes("product.py", b"VALUE = 1\n")
    git_builder.write_bytes(
        "specs/079-wright-native-authoring/tasks.md", b"- [x] T001 Implement baseline\n"
    )
    commit = git_builder.commit("implementation candidate")
    reader = GitReader(git_builder.root)
    identity = reader.resolve_identity(commit, ROOT)
    state = docs[f"{ROOT}/program-state.json"]
    state.update(revision=98, feature_state="PR_READY", active_mutating_lease=None)
    state["next_eligible_actions"] = [
        {
            "action": "VERIFY_CURRENT_FEATURE_CI",
            "roadmap_item": "EPP-N01",
            "requires_human_approval": False,
            "reason": "Review scoped delivery; human study remains pending.",
        }
    ]
    review = {
        "$schema": "../../schemas/native-candidate-review.schema.json",
        "schema_version": "1.0",
        "feature_id": "EPP-N01",
        "review_type": "independent_technical",
        "review_scope": "entire_candidate",
        "candidate_commit": commit,
        "candidate_tree": identity.source_tree,
        "task_ids": ["T001"],
        "reviewer_identity": "Independent reviewer",
        "implementation_authors": ["Implementation author"],
        "reviewed_at": "2026-09-04T23:00:00Z",
        "result": "passed",
        "open_actionable_findings": 0,
        "human_study_evidence": False,
        "evidence": "Fixture only: entire candidate inspected and critical probe rerun.",
    }
    docs[f"{ROOT}/{REVIEW}"] = review
    state["scoped_checkpoint"] = {
        "status": "independently_verified",
        "candidate_commit": commit,
        "candidate_tree": identity.source_tree,
        "task_ids": ["T001"],
        "pending_task_ids": [f"T{i:03}" for i in range(2, 33)],
        "independent_review": {
            "path": REVIEW,
            "record_digest": canonical_digest(review),
        },
        "whole_feature_complete": False,
        "reason": "Independent implementation delivery; remaining acceptance is pending.",
    }
    return git_builder, reader, docs


def findings(candidate):
    builder, reader, docs = candidate
    return validate_roadmap_approval_and_lease(
        docs,
        ROOT,
        observed_at=NOW,
        actual_branch="",
        worktree_id="detached-synthetic-merge",
        reader=reader,
        source_commit=builder.git_output("rev-parse", "HEAD"),
    )[0]


@pytest.mark.parametrize("feature_state", sorted(NATIVE_REVIEWED_STATES))
def test_reviewed_scoped_states_keep_human_and_final_tasks_pending(
    candidate, feature_state: str
):
    builder, _, docs = candidate
    state = docs[f"{ROOT}/program-state.json"]
    state["feature_state"] = feature_state
    rule = next(
        row
        for row in docs[f"{ROOT}/lifecycle-policy.json"]["action_rules"]
        if row["feature_state"] == feature_state
        and (
            row["action"] == "PREPARE_NATIVE_SCOPED_PR"
            if feature_state == "INDEPENDENTLY_VERIFIED"
            else True
        )
    )
    state["next_eligible_actions"][0].update(
        action=rule["action"], requires_human_approval=rule["requires_human_approval"]
    )
    builder.write_json(f"{ROOT}/{REVIEW}", docs[f"{ROOT}/{REVIEW}"])
    builder.write_json(f"{ROOT}/program-state.json", state)
    builder.commit("append review and scoped state")
    assert (
        validate_schema(docs[f"{ROOT}/schemas/program-state.schema.json"], state) == []
    )
    assert findings(candidate) == []
    assert {"T028", "T031", "T032"} <= set(
        state["scoped_checkpoint"]["pending_task_ids"]
    )
    assert docs[f"{ROOT}/{REVIEW}"]["human_study_evidence"] is False
    assert state["scoped_checkpoint"]["whole_feature_complete"] is False


@pytest.mark.parametrize(
    "defect",
    [
        "different_candidate",
        "different_tree",
        "self_review",
        "human_claim",
        "open_finding",
        "future_review",
        "missing_review",
        "changed_record",
        "review_task_mismatch",
        "missing_pending",
        "overlap",
        "unchecked_task",
        "whole_feature_claim",
        "no_checkpoint",
        "not_reviewed",
        "open_lease",
    ],
)
def test_scoped_delivery_fails_closed(candidate, defect: str):
    _, _, docs = candidate
    state = docs[f"{ROOT}/program-state.json"]
    checkpoint = state["scoped_checkpoint"]
    review = docs[f"{ROOT}/{REVIEW}"]
    if defect == "different_candidate":
        review["candidate_commit"] = "0" * 40
    elif defect == "different_tree":
        review["candidate_tree"] = "0" * 40
    elif defect == "self_review":
        review["reviewer_identity"] = "  IMPLEMENTATION AUTHOR  "
    elif defect == "human_claim":
        review["human_study_evidence"] = True
    elif defect == "open_finding":
        review["open_actionable_findings"] = 1
    elif defect == "future_review":
        review["reviewed_at"] = "2027-01-01T00:00:00Z"
    elif defect == "missing_review":
        docs.pop(f"{ROOT}/{REVIEW}")
    elif defect == "changed_record":
        checkpoint["independent_review"]["record_digest"] = "0" * 64
    elif defect == "review_task_mismatch":
        review["task_ids"] = ["T002"]
    elif defect == "missing_pending":
        checkpoint["pending_task_ids"].remove("T028")
    elif defect == "overlap":
        checkpoint["pending_task_ids"].append("T001")
    elif defect == "unchecked_task":
        checkpoint["task_ids"] = review["task_ids"] = ["T002"]
        checkpoint["pending_task_ids"] = ["T001"] + [f"T{i:03}" for i in range(3, 33)]
    elif defect == "whole_feature_claim":
        checkpoint["whole_feature_complete"] = True
    elif defect == "no_checkpoint":
        state.pop("scoped_checkpoint")
    elif defect == "not_reviewed":
        checkpoint["status"] = "awaiting_independent_review"
    elif defect == "open_lease":
        state["active_mutating_lease"] = {"feature_id": "EPP-N01"}
    if defect != "changed_record":
        checkpoint["independent_review"]["record_digest"] = canonical_digest(review)
    assert any(
        f.code in {"NATIVE_SCOPED_DELIVERY_INVALID", "LEASE_IDENTITY_MISMATCH"}
        for f in findings(candidate)
    )


@pytest.mark.parametrize("path", ["product.py", "tests/check.py", "package.json"])
def test_changes_after_review_require_new_candidate(candidate, path: str):
    builder, _, _ = candidate
    builder.write_bytes(path, b"changed\n")
    builder.commit("implementation changed after review")
    assert any(
        f.invariant == "NATIVE_SCOPED_CANDIDATE_IDENTITY" for f in findings(candidate)
    )


def test_initial_author_freeze_does_not_fabricate_review(candidate):
    _, _, docs = candidate
    state = docs[f"{ROOT}/program-state.json"]
    state["feature_state"] = "AUTHOR_VERIFIED"
    state["scoped_checkpoint"].update(
        status="awaiting_independent_review", independent_review=None
    )
    state["next_eligible_actions"][0].update(action="FREEZE_CURRENT_FEATURE_CANDIDATE")
    assert findings(candidate) == []
    assert _validate_native_delivery_review(docs, ROOT, state, NOW)


def test_prior_closed_dashboard_checkpoint_schema_still_valid(repository_root: Path):
    schemas = repository_root / ROOT / "schemas"
    schema = json.loads((schemas / "program-state.schema.json").read_text())
    old = json.loads(
        (
            repository_root / ROOT / "evidence/states/program-state-revision-0096.json"
        ).read_text()
    )
    assert validate_schema(schema, copy.deepcopy(old)) == []


@pytest.mark.parametrize(
    ("event", "target", "invalid"),
    [
        ("lifecycle_transition", "AUTHOR_VERIFIED", False),
        ("lifecycle_transition", "PR_READY", True),
        ("verification", "PR_READY", True),
        ("verification", "IMPLEMENTING", False),
    ],
)
def test_native_delivery_cannot_skip_existing_lifecycle(
    candidate, event, target, invalid
):
    _, _, docs = candidate
    docs[f"{ROOT}/evidence/transitions/TR-0097.json"] = {
        "schema_version": "2.0",
        "transition_id": "TR-0097",
        "feature_id": "EPP-N01",
        "prior_revision": 97,
        "new_revision": 98,
        "state_domain": "feature",
        "event_kind": event,
        "from_state": "IMPLEMENTING",
        "to_state": target,
        "git": {"changed_paths_manifest": []},
    }
    result = []
    _validate_state_chain(docs, ROOT, result)
    assert any(f.code == "LIFECYCLE_EDGE_INVALID" for f in result) is invalid
