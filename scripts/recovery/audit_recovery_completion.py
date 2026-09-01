"""Audit the canonical workflow recovery checkpoint without claiming external gates.

This validator binds the frozen predecessor, exact approved walkthrough, current
recovery task ledger, dashboard result, capability/syntax evidence, and local
release-candidate evidence.  It deliberately reports the remaining human and
external-authority gates instead of treating a locally green tree as complete.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
FEATURE = ROOT / "specs" / "080-canonical-workflow-recovery"
APPROVED_WALKTHROUGH = (
    ROOT
    / "artifacts"
    / "ui-walkthrough"
    / "workflow-recovery"
    / "20260901T031913Z-continuation-1"
)
CORRECTION_WALKTHROUGH = (
    ROOT
    / "artifacts"
    / "ui-walkthrough"
    / "workflow-recovery-usability"
    / "20260901T200836Z-continuation-14"
)
FROZEN_COMMIT = "b4a7e996f10ec95f7d24185a43fd1401843db66d"
APPROVED_COMMIT = "f9237763d6fa6e9748dfb7b713e753a7fc4b4d17"
APPROVED_TREE = "aeca6ab8294dd54112d3e9ac10148537af32b0f0"
APPROVED_MANIFEST = "f2b4964ec1f599b55a8a8d53704147d2133674baa5db9a28072d4a2808c57347"
CORRECTION_COMMIT = "38b409bf149a1241cc87cdedd48f83fed16b5050"
CORRECTION_TREE = "452c1ab82b12fe94ba743e3dfe612c8cd4b9dac6"
CORRECTION_MANIFEST = "b8764a02ef83dfc52b65714de0cdbb05071feb9c0ebf4f5fde4995a2870cf335"
T059_SOURCE = "fe6140d85f0598454394d7b7105d756c3794a7dd"
T059_TREE = "8df2b19c94926c8fe922870de4bbad92bb285720"
FROZEN_TASK_FILES = ("specs/079-visual-workflow-composition/tasks.md",)
ALLOWED_OPEN_TASKS = frozenset({"T056", "T058", "T060"})
EXPECTED_SYNTAX_TREATMENTS = frozenset({"json", "yaml", "engineering_source"})
TASK_PATTERN = re.compile(r"^- \[([ xX])\].*?\b(T\d{3})\b", re.MULTILINE)


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


def _walkthrough_evidence(
    root: Path,
    *,
    commit: str,
    tree: str,
    manifest_sha256: str,
    steps: int,
    screenshots: int,
    files: int,
) -> dict[str, Any]:
    status = _json(root / "status.json")
    manifest = _json(root / "manifest.json")
    diagnostics = _json(root / "trace" / "browser-diagnostics.json")
    missing: list[str] = []
    mismatched: list[str] = []
    for item in manifest.get("files", []):
        target = root / item["path"]
        if not target.is_file():
            missing.append(item["path"])
        elif _sha256(target) != item["sha256"]:
            mismatched.append(item["path"])
    raw_count = len(list((root / "screenshots" / "raw").glob("*.png")))
    annotated_count = len(list((root / "screenshots" / "annotated").glob("*.png")))
    diagnostic_count = len(diagnostics.get("diagnostics", [])) + sum(
        len(diagnostics.get(key, []))
        for key in (
            "consoleErrors",
            "pageErrors",
            "requestFailures",
            "unexpectedHttpResponses",
        )
    )
    passed_steps = sum(step.get("state") == "pass" for step in status.get("steps", []))
    ok = (
        status.get("overall") == "pass"
        and len(status.get("steps", [])) == steps
        and passed_steps == steps
        and manifest.get("overall") == "pass"
        and manifest.get("subject_commit") == commit
        and manifest.get("subject_tree") == tree
        and _sha256(root / "manifest.json") == manifest_sha256
        and len(manifest.get("files", [])) == files
        and raw_count == screenshots
        and annotated_count == screenshots
        and diagnostic_count == 0
        and not missing
        and not mismatched
    )
    return {
        "ok": ok,
        "commit": manifest.get("subject_commit"),
        "tree": manifest.get("subject_tree"),
        "manifest_sha256": _sha256(root / "manifest.json"),
        "steps_passed": passed_steps,
        "steps_total": len(status.get("steps", [])),
        "raw_screenshots": raw_count,
        "annotated_screenshots": annotated_count,
        "manifest_files": len(manifest.get("files", [])),
        "browser_diagnostics": diagnostic_count,
        "missing_files": missing,
        "digest_mismatches": mismatched,
    }


def _task_ledger(path: Path) -> dict[str, Any]:
    completed: set[str] = set()
    open_tasks: set[str] = set()
    matches = TASK_PATTERN.findall(path.read_text(encoding="utf-8"))
    for mark, task_id in matches:
        (completed if mark.lower() == "x" else open_tasks).add(task_id)
    task_ids = completed | open_tasks
    ordinals = sorted(int(task_id.removeprefix("T")) for task_id in task_ids)
    contiguous = bool(ordinals) and ordinals == list(range(1, ordinals[-1] + 1))
    return {
        "completed": completed,
        "open_tasks": open_tasks,
        "total": len(task_ids),
        "well_formed": contiguous and len(matches) == len(task_ids),
    }


def _task_state(path: Path) -> tuple[set[str], set[str]]:
    ledger = _task_ledger(path)
    return ledger["completed"], ledger["open_tasks"]


def _capability_map_summary(path: Path) -> dict[str, int]:
    with path.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    return {
        "row_count": len(rows),
        "unique_source_key_count": len({row["source_key"] for row in rows}),
        "capabilities_represented": len({row["capability_id"] for row in rows}),
    }


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

    frozen_diff = _git(
        "diff", "--quiet", FROZEN_COMMIT, "--", *FROZEN_TASK_FILES, check=False
    )
    frozen_open: dict[str, list[str]] = {}
    frozen_ids_ok = True
    for relative in FROZEN_TASK_FILES:
        _, open_tasks = _task_state(ROOT / relative)
        expected = {f"T{number:03d}" for number in range(28, 39)}
        present = sorted(open_tasks & expected)
        frozen_open[relative] = present
        frozen_ids_ok = frozen_ids_ok and set(present) == expected
    frozen_ok = frozen_diff.returncode == 0 and frozen_ids_ok

    ledger = _task_ledger(FEATURE / "tasks.md")
    completed = ledger["completed"]
    open_tasks = ledger["open_tasks"]
    ledger_ok = ledger["well_formed"]
    remaining_ok = open_tasks == ALLOWED_OPEN_TASKS

    capability = _json(FEATURE / "evidence" / "capability-coverage.json")
    capability_map = _capability_map_summary(FEATURE / "capability-source-map.csv")
    capability_ok = (
        capability.get("status") == "PASS"
        and capability.get("row_count") == capability_map["row_count"]
        and capability.get("unique_source_key_count")
        == capability_map["unique_source_key_count"]
        and capability_map["row_count"] == capability_map["unique_source_key_count"]
        and capability.get("capabilities_represented")
        == capability_map["capabilities_represented"]
        and capability.get("capability_count")
        == capability_map["capabilities_represented"]
        and capability.get("core_actual") == capability.get("core_expected")
        and capability.get("unexplained_omissions") == []
    )

    syntax = _json(FEATURE / "evidence" / "syntax-evaluation.json")
    syntax_ok = (
        len(syntax.get("edit_tasks", [])) >= 5
        and all(
            treatment.get("round_trip")
            and treatment.get("schema_valid")
            and treatment.get("edit_candidates_valid")
            == treatment.get("edit_candidates_total")
            for treatment in syntax.get("treatments", {}).values()
        )
        and set(syntax.get("treatments", {})) == EXPECTED_SYNTAX_TREATMENTS
    )

    approved_walkthrough = _walkthrough_evidence(
        APPROVED_WALKTHROUGH,
        commit=APPROVED_COMMIT,
        tree=APPROVED_TREE,
        manifest_sha256=APPROVED_MANIFEST,
        steps=50,
        screenshots=99,
        files=204,
    )
    correction_walkthrough = _walkthrough_evidence(
        CORRECTION_WALKTHROUGH,
        commit=CORRECTION_COMMIT,
        tree=CORRECTION_TREE,
        manifest_sha256=CORRECTION_MANIFEST,
        steps=24,
        screenshots=26,
        files=59,
    )
    walkthrough_ok = approved_walkthrough["ok"] and correction_walkthrough["ok"]

    approval_text = (FEATURE / "evidence" / "product-approval.md").read_text(
        encoding="utf-8"
    )
    approval_ok = all(
        value in approval_text
        for value in (
            APPROVED_COMMIT,
            APPROVED_TREE,
            APPROVED_MANIFEST,
            CORRECTION_COMMIT,
            CORRECTION_TREE,
            CORRECTION_MANIFEST,
            "name not supplied",
            "mechanical engineer",
        )
    )

    dashboard = _json(
        ROOT
        / "artifacts"
        / "dashboard-recovery-verification"
        / "dashboard-verification.json"
    )
    dashboard_ok = (
        dashboard.get("overall") == "pass"
        and dashboard.get("diagnostics") == []
        and dashboard.get("checks", {})
        .get("desktop", {})
        .get("horizontalOverflowPixels")
        == 0
        and dashboard.get("checks", {})
        .get("mobile", {})
        .get("horizontalOverflowPixels")
        == 0
        and dashboard.get("checks", {}).get("api", {}).get("completed")
        == len(completed)
        and dashboard.get("checks", {}).get("api", {}).get("total") == ledger["total"]
        and dashboard.get("checks", {}).get("api", {}).get("customerReady") is False
    )

    preflight = _json(ROOT / "artifacts" / "t059-release-candidate" / "preflight.json")
    native_build = _json(
        ROOT / "artifacts" / "t059-release-candidate" / "native-build-evidence.json"
    )
    native_lifecycle = _json(
        ROOT / "artifacts" / "t059-release-candidate" / "native-lifecycle-windows.json"
    )
    release = _json(
        ROOT / "artifacts" / "t059-release-candidate" / "release-evidence.json"
    )
    release_text = (FEATURE / "evidence" / "release-candidate-hardening.md").read_text(
        encoding="utf-8"
    )
    all_stages_non_mutating = all(
        stage.get("external_mutation") is False
        for stage in release.get("stage_results", [])
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
            [
                *FROZEN_TASK_FILES,
                "specs/080-canonical-workflow-recovery/evidence/checkpoint-d-freeze.md",
            ],
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
            "All local contract tasks through T055 are complete and JSON, YAML, and the public engineering source share at least five valid edit probes.",
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
            [
                str(APPROVED_WALKTHROUGH.relative_to(ROOT)).replace("\\", "/"),
                str(CORRECTION_WALKTHROUGH.relative_to(ROOT)).replace("\\", "/"),
            ],
            "The immutable approval baseline and the current 24/24 workspace-owned correction walkthrough both have exact subject/tree binding, complete manifest integrity, paired screenshots, and zero unexpected diagnostics.",
        ),
        _requirement(
            "OBJ-005",
            "Human direction approval is recorded without invented reviewer facts",
            approval_ok,
            ["specs/080-canonical-workflow-recovery/evidence/product-approval.md"],
            "The record preserves the original direction approval, binds the corrected exact subject by evidence, identifies the requesting user only as a self-described mechanical engineer, and states that name and timestamp were not supplied.",
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
            (
                f"Coverage is {capability_map['row_count']}/{capability_map['unique_source_key_count']} "
                f"and {capability_map['capabilities_represented']}/{capability_map['capabilities_represented']}; "
                f"dashboard must match the current {len(completed)}/{ledger['total']} ledger with "
                "customer readiness false and zero desktop/mobile overflow or browser diagnostics."
            ),
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
    for label, evidence in (
        ("approval", approved_walkthrough),
        ("correction", correction_walkthrough),
    ):
        if evidence["missing_files"]:
            findings.append(
                f"Missing {label} walkthrough files: {evidence['missing_files']}"
            )
        if evidence["digest_mismatches"]:
            findings.append(
                f"{label.title()} walkthrough digest mismatches: {evidence['digest_mismatches']}"
            )

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
        "goal_status": "blocked_external"
        if not findings and remaining_ok
        else "incomplete",
        "goal_complete": False,
        "tracked_worktree_clean_before_output": tracked_clean,
        "untracked_paths": untracked,
        "untracked_paths_note": "Untracked paths are disclosed, not treated as committed evidence.",
        "recovery_ledger": {
            "completed": len(completed),
            "total": ledger["total"],
            "open_tasks": sorted(open_tasks),
        },
        "frozen_checkpoint": {
            "commit": FROZEN_COMMIT,
            "unchanged": frozen_diff.returncode == 0,
            "open_tasks_by_file": frozen_open,
        },
        "approved_walkthrough": {
            key: value for key, value in approved_walkthrough.items() if key != "ok"
        },
        "usability_correction_walkthrough": {
            key: value for key, value in correction_walkthrough.items() if key != "ok"
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
