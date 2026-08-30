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
        f"{PROGRAM_ROOT}/gate-catalog.json": load(root / "gate-catalog.json"),
    }


def code_set(findings) -> set[str]:
    return {finding.code for finding in findings}


def lease_identity(state: dict) -> tuple[str, str]:
    lease = state.get("active_mutating_lease")
    if not isinstance(lease, dict):
        return "", ""
    return lease["branch"], lease["worktree_id"]


def test_current_pointer_matches_lifecycle_action(
    repository_root: Path,
) -> None:
    documents = current_documents(repository_root)
    state = documents[f"{PROGRAM_ROOT}/program-state.json"]
    branch, worktree_id = lease_identity(state)
    findings, action = validate_roadmap_approval_and_lease(
        documents,
        PROGRAM_ROOT,
        observed_at=OBSERVED,
        actual_branch=branch,
        worktree_id=worktree_id,
    )
    assert findings == []
    policy = documents[f"{PROGRAM_ROOT}/lifecycle-policy.json"]
    expected = next(
        rule["action"]
        for rule in policy["action_rules"]
        if rule["program_state"] == state["state"]
        and rule["feature_state"] == state["feature_state"]
        and rule["action"] == state["next_eligible_actions"][0]["action"]
    )
    assert action == expected


def test_cycle_wip_and_pointer_mismatch_are_all_reported(repository_root: Path) -> None:
    documents = copy.deepcopy(current_documents(repository_root))
    roadmap = documents[f"{PROGRAM_ROOT}/roadmap.json"]
    state = documents[f"{PROGRAM_ROOT}/program-state.json"]
    branch, worktree_id = lease_identity(state)
    roadmap["items"][0]["depends_on"] = [roadmap["items"][-1]["id"]]
    next(
        item
        for item in roadmap["items"]
        if item["id"] != state["current_feature"] and item["status"] != "active"
    )["status"] = "active"
    state["current_feature"] = "EPP-F99"
    findings, _ = validate_roadmap_approval_and_lease(
        documents,
        PROGRAM_ROOT,
        observed_at=OBSERVED,
        actual_branch=branch,
        worktree_id=worktree_id,
    )
    assert {"ROADMAP_CYCLE", "WIP_LIMIT_EXCEEDED", "LEASE_IDENTITY_MISMATCH"}.issubset(
        code_set(findings)
    )


def test_expired_or_wrong_worktree_lease_and_unsafe_paths_fail(
    repository_root: Path,
) -> None:
    documents = copy.deepcopy(current_documents(repository_root))
    root = repository_root / PROGRAM_ROOT
    documents[f"{PROGRAM_ROOT}/program-state.json"] = load(
        root / "evidence/states/program-state-revision-0026.json"
    )
    next(
        item
        for item in documents[f"{PROGRAM_ROOT}/roadmap.json"]["items"]
        if item["id"] == "EPP-F01"
    )["status"] = "active"
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


def test_active_item_requires_complete_dependencies_and_resolved_decisions(
    repository_root: Path,
) -> None:
    documents = copy.deepcopy(current_documents(repository_root))
    roadmap = documents[f"{PROGRAM_ROOT}/roadmap.json"]
    state = documents[f"{PROGRAM_ROOT}/program-state.json"]
    branch, worktree_id = lease_identity(state)
    active = next(
        item for item in roadmap["items"] if item["id"] == state["current_feature"]
    )
    dependency = active["depends_on"][0]
    next(item for item in roadmap["items"] if item["id"] == dependency)["status"] = (
        "proposed"
    )
    active["blocking_decisions"] = ["DEC-P0-001"]
    findings, _ = validate_roadmap_approval_and_lease(
        documents,
        PROGRAM_ROOT,
        observed_at=OBSERVED,
        actual_branch=branch,
        worktree_id=worktree_id,
    )
    assert {
        "ROADMAP_DEPENDENCY_INCOMPLETE",
        "ROADMAP_BLOCKING_DECISION_OPEN",
    }.issubset(code_set(findings))


def test_missing_decision_gate_and_risk_references_fail(repository_root: Path) -> None:
    documents = copy.deepcopy(current_documents(repository_root))
    roadmap = documents[f"{PROGRAM_ROOT}/roadmap.json"]
    active = next(item for item in roadmap["items"] if item["id"] == "EPP-F01")
    active["blocking_decisions"] = ["DEC-P0-999"]
    active["gate_impacts"] = ["PROG-99"]
    documents[f"{PROGRAM_ROOT}/program-state.json"]["readiness"]["program_health"][
        "blockers"
    ].append("RISK-999: missing")
    findings, _ = validate_roadmap_approval_and_lease(
        documents,
        PROGRAM_ROOT,
        observed_at=OBSERVED,
        actual_branch="077-control-plane-validator",
        worktree_id="epp-f01",
    )
    assert {
        "ROADMAP_DECISION_REFERENCE_INVALID",
        "ROADMAP_GATE_REFERENCE_INVALID",
        "CONTROL_REFERENCE_INVALID",
    }.issubset(code_set(findings))


def test_next_action_human_flag_must_match_policy(repository_root: Path) -> None:
    documents = copy.deepcopy(current_documents(repository_root))
    action = documents[f"{PROGRAM_ROOT}/program-state.json"]["next_eligible_actions"][0]
    action["requires_human_approval"] = not action["requires_human_approval"]
    findings, _ = validate_roadmap_approval_and_lease(
        documents,
        PROGRAM_ROOT,
        observed_at=OBSERVED,
        actual_branch="077-control-plane-validator",
        worktree_id="epp-f01",
    )
    assert "ACTION_POLICY_MISMATCH" in code_set(findings)


def test_dependency_priority_tie_is_ambiguous(repository_root: Path) -> None:
    documents = copy.deepcopy(current_documents(repository_root))
    roadmap = documents[f"{PROGRAM_ROOT}/roadmap.json"]
    for item in roadmap["items"]:
        if item["status"] == "active":
            item["status"] = "proposed"
        if item["id"] in {"EPP-F01", "EPP-F01B"}:
            item["status"] = "proposed"
            item["depends_on"] = ["EPP-P00"]
            item["blocking_decisions"] = []
            item["priority"] = 10
    state = documents[f"{PROGRAM_ROOT}/program-state.json"]
    state["current_feature"] = None
    state["active_mutating_lease"] = None
    findings, _ = validate_roadmap_approval_and_lease(
        documents,
        PROGRAM_ROOT,
        observed_at=OBSERVED,
        actual_branch="077-control-plane-validator",
        worktree_id="epp-f01",
    )
    assert "ROADMAP_ELIGIBILITY_AMBIGUOUS" in code_set(findings)
