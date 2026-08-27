"""Roadmap, approval history, date, pointer, WIP, and lease contracts."""

from __future__ import annotations

import copy
import json
from datetime import datetime, timezone
from pathlib import Path

from program_control.validation import (
    evaluate_approval_history,
    validate_roadmap_approval_and_lease,
)


PROGRAM_ROOT = "docs/programs/engineering-process-platform"
OBSERVED = datetime(2026, 8, 27, 12, 0, tzinfo=timezone.utc)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def current_documents(repository_root: Path) -> dict[str, dict]:
    root = repository_root / PROGRAM_ROOT
    return {
        f"{PROGRAM_ROOT}/program-state.json": load(root / "program-state.json"),
        f"{PROGRAM_ROOT}/roadmap.json": load(root / "roadmap.json"),
        f"{PROGRAM_ROOT}/decision-register.json": load(root / "decision-register.json"),
        f"{PROGRAM_ROOT}/risk-register.json": load(root / "risk-register.json"),
        f"{PROGRAM_ROOT}/lifecycle-policy.json": load(root / "lifecycle-policy.json"),
    }


def code_set(findings) -> set[str]:
    return {finding.code for finding in findings}


def test_current_pointer_wip_dates_and_lease_are_consistent(
    repository_root: Path,
) -> None:
    findings, action = validate_roadmap_approval_and_lease(
        current_documents(repository_root),
        PROGRAM_ROOT,
        observed_at=OBSERVED,
        actual_branch="077-control-plane-validator",
        worktree_id="epp-f01",
    )
    assert findings == []
    assert action == "EXECUTE_EPP_F01_TASKS"


def test_cycle_wip_and_pointer_mismatch_are_all_reported(repository_root: Path) -> None:
    documents = copy.deepcopy(current_documents(repository_root))
    roadmap = documents[f"{PROGRAM_ROOT}/roadmap.json"]
    roadmap["items"][0]["depends_on"] = [roadmap["items"][-1]["id"]]
    roadmap["items"][2]["status"] = "active"
    documents[f"{PROGRAM_ROOT}/program-state.json"]["current_feature"] = "EPP-F99"
    findings, _ = validate_roadmap_approval_and_lease(
        documents,
        PROGRAM_ROOT,
        observed_at=OBSERVED,
        actual_branch="077-control-plane-validator",
        worktree_id="epp-f01",
    )
    assert {"ROADMAP_CYCLE", "WIP_LIMIT_EXCEEDED", "LEASE_IDENTITY_MISMATCH"}.issubset(
        code_set(findings)
    )


def test_expired_or_wrong_worktree_lease_and_unsafe_paths_fail(
    repository_root: Path,
) -> None:
    documents = copy.deepcopy(current_documents(repository_root))
    lease = documents[f"{PROGRAM_ROOT}/program-state.json"]["active_mutating_lease"]
    lease["expires_at"] = "2026-08-27T11:59:59Z"
    lease["branch"] = "wrong-branch"
    lease["worktree_id"] = "wrong-worktree"
    lease["allowed_paths"].append("C:/private/escape")
    lease["allowed_actions"].append("push")
    findings, _ = validate_roadmap_approval_and_lease(
        documents,
        PROGRAM_ROOT,
        observed_at=OBSERVED,
        actual_branch="077-control-plane-validator",
        worktree_id="epp-f01",
    )
    assert {
        "LEASE_EXPIRED",
        "LEASE_BRANCH_MISMATCH",
        "LEASE_WORKTREE_MISMATCH",
        "LEASE_PATH_UNSAFE",
        "LEASE_ACTION_UNAUTHORIZED",
    }.issubset(code_set(findings))


def test_decision_and_risk_dates_are_machine_structured(repository_root: Path) -> None:
    decisions = load(
        repository_root
        / "docs/programs/engineering-process-platform/decision-register.json"
    )["records"]
    risks = load(
        repository_root
        / "docs/programs/engineering-process-platform/risk-register.json"
    )["risks"]
    assert all(
        set(row["due"]) == {"before_event", "due_at", "last_reviewed_at"}
        for row in decisions
    )
    assert all(
        set(row["review"]) == {"cadence", "due_at", "last_reviewed_at"} for row in risks
    )


def test_exact_v3_two_scope_approval_bundle_with_restrictive_conditions_is_current(
    repository_root: Path,
) -> None:
    root = (
        repository_root
        / "docs/programs/engineering-process-platform/evidence/approvals"
    )
    approvals = [
        load(root / "APR-EPP-F01-MC-003.json"),
        load(root / "APR-EPP-F01-IMPL-003.json"),
    ]
    subject = approvals[0]["subject"]
    findings, selected = evaluate_approval_history(
        approvals,
        required_scopes=("material_change", "feature_implementation"),
        exact_subject=subject,
        observed_at=OBSERVED,
    )
    assert findings == []
    assert {row["scope"] for row in selected} == {
        "material_change",
        "feature_implementation",
    }
    assert all(row["conditions"] for row in selected)
    assert {row["bundle_id"] for row in selected} == {"APB-EPP-F01-003"}


def test_approval_revocation_expiry_scope_and_subject_drift_fail(
    repository_root: Path,
) -> None:
    root = (
        repository_root
        / "docs/programs/engineering-process-platform/evidence/approvals"
    )
    material = load(root / "APR-EPP-F01-MC-003.json")
    implementation = load(root / "APR-EPP-F01-IMPL-003.json")
    exact_subject = copy.deepcopy(material["subject"])
    material["revoked"] = True
    implementation["expires_at"] = "2026-08-27T11:59:59Z"
    implementation["subject"]["git_tree"] = "0" * 40
    findings, _ = evaluate_approval_history(
        [material, implementation],
        required_scopes=("material_change", "feature_implementation", "external_write"),
        exact_subject=exact_subject,
        observed_at=OBSERVED,
    )
    assert {
        "APPROVAL_REVOKED",
        "APPROVAL_EXPIRED",
        "APPROVAL_SUBJECT_MISMATCH",
        "APPROVAL_SCOPE_MISSING",
    }.issubset(code_set(findings))


def test_conditional_decision_requires_an_explicit_condition(
    repository_root: Path,
) -> None:
    root = (
        repository_root
        / "docs/programs/engineering-process-platform/evidence/approvals"
    )
    material = load(root / "APR-EPP-F01-MC-003.json")
    material["decision"] = "approved_with_conditions"
    material["conditions"] = []
    findings, _ = evaluate_approval_history(
        [material],
        required_scopes=("material_change",),
        exact_subject=material["subject"],
        observed_at=OBSERVED,
    )
    assert "APPROVAL_NOT_CURRENT" in code_set(findings)
