"""Audit the canonical workflow recovery checkpoint without claiming external gates.

This validator binds the frozen predecessor, exact approved walkthrough, current
recovery task ledger, dashboard result, capability/syntax evidence, and local
release-candidate evidence.  It deliberately reports the remaining human and
external-authority gates instead of treating a locally green tree as complete.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
FEATURE = ROOT / "specs" / "080-canonical-workflow-recovery"
WALKTHROUGH = (
    ROOT
    / "artifacts"
    / "ui-walkthrough"
    / "workflow-recovery"
    / "20260901T031913Z-continuation-1"
)
FROZEN_COMMIT = "b4a7e996f10ec95f7d24185a43fd1401843db66d"
APPROVED_COMMIT = "f9237763d6fa6e9748dfb7b713e753a7fc4b4d17"
APPROVED_TREE = "aeca6ab8294dd54112d3e9ac10148537af32b0f0"
APPROVED_MANIFEST = "f2b4964ec1f599b55a8a8d53704147d2133674baa5db9a28072d4a2808c57347"
T059_SOURCE = "fe6140d85f0598454394d7b7105d756c3794a7dd"
T059_TREE = "8df2b19c94926c8fe922870de4bbad92bb285720"
FROZEN_TASK_FILES = (
    "specs/079-visual-workflow-composition/tasks.md",
)


def _git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=check,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _task_state(path: Path) -> tuple[set[str], set[str]]:
    completed: set[str] = set()
    open_tasks: set[str] = set()
    pattern = re.compile(r"^- \[([ xX])\].*?\b(T\d{3})\b", re.MULTILINE)
    for mark, task_id in pattern.findall(path.read_text(encoding="utf-8")):
        (completed if mark.lower() == "x" else open_tasks).add(task_id)
    return completed, open_tasks


def _requirement(
    requirement_id: str,
    label: str,
    passed: bool,
    evidence: list[str],
    detail: str,
) -> dict[str, Any]:
    return {
        "id": requirement_id,
        "label": label,
        "status": "passed" if passed else "failed",
        "evidence": evidence,
        "detail": detail,
    }


def collect() -> dict[str, Any]:
    findings: list[str] = []
    head = _git("rev-parse", "HEAD").stdout.strip()
    tree = _git("show", "-s", "--format=%T", "HEAD").stdout.strip()

    tracked_clean = (
        _git("diff", "--quiet", check=False).returncode == 0
        and _git("diff", "--cached", "--quiet", check=False).returncode == 0
    )
    untracked = [
        line.removeprefix("?? ")
        for line in _git("status", "--short").stdout.splitlines()
        if line.startswith("?? ")
    ]

    frozen_diff = _git("diff", "--quiet", FROZEN_COMMIT, "--", *FROZEN_TASK_FILES, check=False)
    frozen_open: dict[str, list[str]] = {}
    frozen_ids_ok = True
    for relative in FROZEN_TASK_FILES:
        _, open_tasks = _task_state(ROOT / relative)
        expected = {f"T{number:03d}" for number in range(28, 39)}
        present = sorted(open_tasks & expected)
        frozen_open[relative] = present
        frozen_ids_ok = frozen_ids_ok and set(present) == expected
    frozen_ok = frozen_diff.returncode == 0 and frozen_ids_ok

    completed, open_tasks = _task_state(FEATURE / "tasks.md")
    ledger_ok = len(completed) == 57 and len(completed | open_tasks) == 60
    remaining_ok = open_tasks == {"T056", "T058", "T060"}

    capability = _json(FEATURE / "evidence" / "capability-coverage.json")
    capability_ok = (
        capability.get("status") == "PASS"
        and capability.get("row_count") == 859
        and capability.get("unique_source_key_count") == 859
        and capability.get("capabilities_represented") == 33
        and capability.get("unexplained_omissions") == []
    )

    syntax = _json(FEATURE / "evidence" / "syntax-evaluation.json")
    syntax_ok = len(syntax.get("edit_tasks", [])) >= 5 and all(
        treatment.get("round_trip")
        and treatment.get("schema_valid")
        and treatment.get("edit_candidates_valid") == treatment.get("edit_candidates_total")
        for treatment in syntax.get("treatments", {}).values()
    ) and set(syntax.get("treatments", {})) == {"json", "yaml", "dsl"}

    status = _json(WALKTHROUGH / "status.json")
    manifest = _json(WALKTHROUGH / "manifest.json")
    diagnostics = _json(WALKTHROUGH / "trace" / "browser-diagnostics.json")
    missing_manifest_files: list[str] = []
    mismatched_manifest_files: list[str] = []
    for item in manifest.get("files", []):
        target = WALKTHROUGH / item["path"]
        if not target.is_file():
            missing_manifest_files.append(item["path"])
        elif _sha256(target) != item["sha256"]:
            mismatched_manifest_files.append(item["path"])
    raw_count = len(list((WALKTHROUGH / "screenshots" / "raw").glob("*.png")))
    annotated_count = len(list((WALKTHROUGH / "screenshots" / "annotated").glob("*.png")))
    walkthrough_ok = (
        status.get("overall") == "pass"
        and len(status.get("steps", [])) == 50
        and all(step.get("state") == "pass" for step in status.get("steps", []))
        and manifest.get("overall") == "pass"
        and manifest.get("subject_commit") == APPROVED_COMMIT
        and manifest.get("subject_tree") == APPROVED_TREE
        and _sha256(WALKTHROUGH / "manifest.json") == APPROVED_MANIFEST
        and len(manifest.get("files", [])) == 204
        and raw_count == 99
        and annotated_count == 99
        and diagnostics.get("diagnostics") == []
        and not missing_manifest_files
        and not mismatched_manifest_files
    )

    approval_text = (FEATURE / "evidence" / "product-approval.md").read_text(encoding="utf-8")
    approval_ok = all(
        value in approval_text
        for value in (APPROVED_COMMIT, APPROVED_TREE, APPROVED_MANIFEST, "name not supplied")
    )

    dashboard = _json(ROOT / "artifacts" / "dashboard-recovery-verification" / "dashboard-verification.json")
    dashboard_ok = (
        dashboard.get("overall") == "pass"
        and dashboard.get("diagnostics") == []
        and dashboard.get("checks", {}).get("desktop", {}).get("horizontalOverflowPixels") == 0
        and dashboard.get("checks", {}).get("mobile", {}).get("horizontalOverflowPixels") == 0
        and dashboard.get("checks", {}).get("api", {}).get("completed") == 57
        and dashboard.get("checks", {}).get("api", {}).get("total") == 60
        and dashboard.get("checks", {}).get("api", {}).get("customerReady") is False
    )

    preflight = _json(ROOT / "artifacts" / "t059-release-candidate" / "preflight.json")
    native_build = _json(ROOT / "artifacts" / "t059-release-candidate" / "native-build-evidence.json")
    native_lifecycle = _json(
        ROOT / "artifacts" / "t059-release-candidate" / "native-lifecycle-windows.json"
    )
    release = _json(ROOT / "artifacts" / "t059-release-candidate" / "release-evidence.json")
    release_text = (FEATURE / "evidence" / "release-candidate-hardening.md").read_text(
        encoding="utf-8"
    )
    all_stages_non_mutating = all(
        stage.get("external_mutation") is False for stage in release.get("stage_results", [])
    )
    t059_ok = (
        preflight.get("release_identity", {}).get("source_commit") == T059_SOURCE
        and native_build.get("version") == "0.1.9"
        and len(native_build.get("artifacts", [])) == 2
        and native_lifecycle.get("status") == "passed"
        and native_lifecycle.get("source_isolation") is True
        and native_lifecycle.get("forbidden_executables") == []
        and release.get("status") == "release_ready"
        and release.get("mode") == "dry-run"
        and all_stages_non_mutating
        and T059_SOURCE in release_text
        and T059_TREE in release_text
        and "sha256:666ed2dee57fa1a4c65a2e3dedc290e70035078e29b948d52f2408b4cddab76a"
        in release_text
    )

    local_contract_tasks = {f"T{number:03d}" for number in range(8, 44)} | {
        "T052",
        "T053",
        "T054",
        "T055",
        "T057",
        "T059",
    }
    contracts_ok = local_contract_tasks <= completed

    requirements = [
        _requirement(
            "OBJ-001",
            "Frozen EPP-F02B checkpoint is unchanged",
            frozen_ok,
            [*FROZEN_TASK_FILES, "specs/080-canonical-workflow-recovery/evidence/checkpoint-d-freeze.md"],
            "Git diff is empty against b4a7e996 and T028-T038 remain unchecked in the frozen task file.",
        ),
        _requirement(
            "OBJ-002",
            "Canonical model, syntax, command, layout, run, and component contracts are present",
            contracts_ok and syntax_ok,
            [
                "specs/080-canonical-workflow-recovery/contracts/",
                "specs/080-canonical-workflow-recovery/evidence/syntax-evaluation.json",
                "specs/080-canonical-workflow-recovery/tasks.md",
            ],
            "All local contract tasks through T055 are complete and JSON/YAML/DSL share five valid edit probes.",
        ),
        _requirement(
            "OBJ-003",
            "Bidirectional graph/text conformance and atomic containment are evidenced",
            {f"T{number:03d}" for number in range(24, 30)} <= completed,
            [
                "tests/recovery/test_workflow_conformance.py",
                "apps/web/src/prototypes/workflow-recovery/command-system.spec.ts",
                "artifacts/ui-walkthrough/workflow-recovery/20260901T031913Z-continuation-1/status.json",
            ],
            "The paired-edit, last-valid containment, digest-isolation, and stable-diagnostic tasks are complete in the exact walkthrough subject.",
        ),
        _requirement(
            "OBJ-004",
            "Canvas-first high-fidelity workflow experience has exact walkthrough evidence",
            walkthrough_ok,
            [str(WALKTHROUGH.relative_to(ROOT)).replace("\\", "/")],
            "50/50 steps, 99 raw plus 99 annotated screenshots, 204 manifest-bound files, exact subject/tree, and zero diagnostics verify the reviewed experience.",
        ),
        _requirement(
            "OBJ-005",
            "Human direction approval is recorded without invented reviewer facts",
            approval_ok,
            ["specs/080-canonical-workflow-recovery/evidence/product-approval.md"],
            "The record cites the requesting user's message, exact approved subject, and explicitly states that reviewer name and timestamp were not supplied.",
        ),
        _requirement(
            "OBJ-006",
            "Capability inventory and recovery dashboard are current and truthful",
            capability_ok and dashboard_ok and ledger_ok and remaining_ok,
            [
                "specs/080-canonical-workflow-recovery/evidence/capability-coverage.json",
                "artifacts/dashboard-recovery-verification/dashboard-verification.json",
                "specs/080-canonical-workflow-recovery/tasks.md",
            ],
            "Coverage is 859/859 and 33/33; dashboard is 57/60 with customer readiness false and zero desktop/mobile overflow or browser diagnostics.",
        ),
        _requirement(
            "OBJ-007",
            "Dependency-ordered locally safe post-approval implementation is qualified",
            t059_ok and {"T052", "T053", "T054", "T055", "T057", "T059"} <= completed,
            [
                "specs/080-canonical-workflow-recovery/evidence/production-promotion.md",
                "specs/080-canonical-workflow-recovery/evidence/security-offline-qualification.md",
                "specs/080-canonical-workflow-recovery/evidence/release-candidate-hardening.md",
                "artifacts/t059-release-candidate/",
            ],
            "Stable definition/layout/run/component, security/offline, deterministic packaging, Windows lifecycle, Docker, and zero-mutation rehearsal gates pass locally.",
        ),
    ]

    for requirement in requirements:
        if requirement["status"] != "passed":
            findings.append(f"{requirement['id']}: {requirement['label']}")
    if missing_manifest_files:
        findings.append(f"Missing walkthrough files: {missing_manifest_files}")
    if mismatched_manifest_files:
        findings.append(f"Walkthrough digest mismatches: {mismatched_manifest_files}")

    blockers = [
        {
            "task": "T056",
            "kind": "human_evidence",
            "condition": "Real assistive-technology and moderated representative-engineer sessions have not occurred.",
            "next_action": "Run the committed moderated-engineer protocol with real participants and retain contemporaneous exact-subject evidence.",
        },
        {
            "task": "T058",
            "kind": "human_authority_and_roadmap_dependencies",
            "condition": "Named decisions, F03/F05/F06/B01 dependencies, independent oracles, holdout, and 100 qualified cases are unavailable; result remains 0/100.",
            "next_command": "uv run python scripts/recovery/benchmark_preflight.py --output test-results/dataset-evaluation/benchmark-preflight.json",
        },
        {
            "task": "T060",
            "kind": "prohibited_external_delivery",
            "condition": "Push, merge, publication, release, and customer actions require separate authorization.",
            "next_action": "Obtain explicit T060 authorization before reading the dev-push runbook and running its merge/release gates.",
        },
    ]

    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "audit_subject": {"commit": head, "tree": tree},
        "audit_status": "PASS" if not findings else "FAIL",
        "goal_status": "blocked_external" if not findings and remaining_ok else "incomplete",
        "goal_complete": False,
        "tracked_worktree_clean_before_output": tracked_clean,
        "untracked_paths": untracked,
        "untracked_paths_note": "Untracked paths are disclosed, not treated as committed evidence.",
        "recovery_ledger": {
            "completed": len(completed),
            "total": len(completed | open_tasks),
            "open_tasks": sorted(open_tasks),
        },
        "frozen_checkpoint": {
            "commit": FROZEN_COMMIT,
            "unchanged": frozen_diff.returncode == 0,
            "open_tasks_by_file": frozen_open,
        },
        "approved_walkthrough": {
            "commit": manifest.get("subject_commit"),
            "tree": manifest.get("subject_tree"),
            "manifest_sha256": _sha256(WALKTHROUGH / "manifest.json"),
            "steps_passed": sum(step.get("state") == "pass" for step in status.get("steps", [])),
            "steps_total": len(status.get("steps", [])),
            "raw_screenshots": raw_count,
            "annotated_screenshots": annotated_count,
            "manifest_files": len(manifest.get("files", [])),
            "browser_diagnostics": len(diagnostics.get("diagnostics", [])),
            "missing_files": missing_manifest_files,
            "digest_mismatches": mismatched_manifest_files,
        },
        "capability_coverage": {
            "status": capability.get("status"),
            "mapped": capability.get("row_count"),
            "unique": capability.get("unique_source_key_count"),
            "capabilities": capability.get("capabilities_represented"),
            "unexplained_omissions": capability.get("unexplained_omissions"),
        },
        "requirements": requirements,
        "findings": findings,
        "blockers": blockers,
        "prohibited_actions_performed": [],
        "customer_ready": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = collect()
    rendered = json.dumps(result, indent=2) + "\n"
    if args.output:
        output = args.output if args.output.is_absolute() else ROOT / args.output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if result["audit_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
