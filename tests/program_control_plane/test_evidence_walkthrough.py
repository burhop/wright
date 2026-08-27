"""Empty-context reconstruction and repository-relative evidence traversal."""

from __future__ import annotations

import json
import posixpath
import re
from hashlib import sha256
from pathlib import Path

from program_control.git_subject import GitReader
from program_control.validation import validate_program


PROGRAM = Path("docs/programs/engineering-process-platform")


def test_readme_directly_links_current_subject_authority_and_start(
    repository_root,
) -> None:
    readme = (repository_root / PROGRAM / "README.md").read_text(encoding="utf-8")
    required = (
        "../../../specs/076-control-plane-validator/spec.md",
        "evidence/approvals/APR-EPP-F01-MC-006.json",
        "evidence/approvals/APR-EPP-F01-IMPL-006.json",
        "evidence/transitions/TR-0038.json",
        "evidence/transitions/TR-0039.json",
        "evidence/verification/EPP-F01-US3.json",
    )
    for target in required:
        assert target in readme
        assert (repository_root / PROGRAM / target).resolve().is_file()
    assert "Continue EPP-F01 at T057" in readme
    assert "only T024–T041 are implementation-authorized" not in readme


def test_program_readme_local_links_resolve(repository_root) -> None:
    readme_path = repository_root / PROGRAM / "README.md"
    targets = re.findall(r"\[[^]]+\]\(([^)]+)\)", readme_path.read_text("utf-8"))
    unresolved = [
        target
        for target in targets
        if not (readme_path.parent / target).resolve().exists()
    ]
    assert unresolved == []


def test_empty_context_reconstructs_one_next_action_and_exclusions(
    repository_root,
) -> None:
    state = json.loads(
        (repository_root / PROGRAM / "program-state.json").read_text("utf-8")
    )
    roadmap = json.loads(
        (repository_root / PROGRAM / "roadmap.json").read_text("utf-8")
    )
    policy = json.loads(
        (repository_root / PROGRAM / "lifecycle-policy.json").read_text("utf-8")
    )
    assert len(state["next_eligible_actions"]) == 1
    next_action = state["next_eligible_actions"][0]
    expected = next(
        rule["action"]
        for rule in policy["action_rules"]
        if rule["program_state"] == state["state"]
        and rule["feature_state"] == state["feature_state"]
    )
    assert next_action["action"] == expected
    assert next_action["requires_human_approval"] is False
    active = next(item for item in roadmap["items"] if item["id"] == "EPP-F01")
    assert active["status"] == "active"
    lease = state["active_mutating_lease"]
    allowed = set(lease["allowed_actions"]) if lease is not None else set()
    assert {
        "dependency_change",
        "benchmark_execution",
        "push",
        "merge",
        "release",
    }.isdisjoint(allowed)


def test_v6_approval_bundle_recomputes_exact_subject_and_manifest(
    repository_root,
) -> None:
    reader = GitReader(repository_root)
    approvals = repository_root / PROGRAM / "evidence/approvals"
    records = [
        json.loads((approvals / name).read_text(encoding="utf-8"))
        for name in ("APR-EPP-F01-MC-006.json", "APR-EPP-F01-IMPL-006.json")
    ]
    assert records[0]["subject"] == records[1]["subject"]
    subject = records[0]["subject"]
    identity = reader.resolve_identity(subject["git_commit"], PROGRAM.as_posix())
    assert identity.source_tree == subject["git_tree"]
    assert identity.program_tree == subject["program_tree"]
    for artifact in subject["artifact_digests"]:
        normalized = posixpath.normpath(
            posixpath.join(PROGRAM.as_posix(), artifact["path"])
        )
        raw = reader.blob(subject["git_commit"], normalized)
        assert sha256(raw).hexdigest() == artifact["sha256"], artifact["path"]


def test_report_and_dashboard_evidence_links_resolve_with_exact_digests(
    repository_root,
) -> None:
    reader = GitReader(repository_root)
    report = validate_program(reader, "HEAD", PROGRAM.as_posix()).report
    for finding in report["findings"]:
        assert (repository_root / finding["artifact"]).is_file()
        correction = finding.get("correction_ref")
        if correction:
            assert (repository_root / correction).is_file()

    dashboard = json.loads(
        (repository_root / PROGRAM / "dashboard.json").read_text("utf-8")
    )
    referenced = [
        artifact
        for area in dashboard["areas"].values()
        for gate in area["gates"]
        for artifact in gate["evidence"]
    ]
    for artifact in referenced:
        raw = (repository_root / artifact["path"]).read_bytes()
        assert sha256(raw).hexdigest() == artifact["sha256"]

    product = dashboard["areas"]["product_readiness"]
    assert product["status"] == "not_started"
    assert "PRODUCT_EVIDENCE_NOT_RECORDED" in product["blockers"]
