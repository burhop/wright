"""Regression probes for Git-bound native quality and delivery claims."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from scripts.program_status import publisher

ROOT = Path(__file__).resolve().parents[2]
PROGRAM = "docs/programs/engineering-process-platform"


def subject():
    commit = str(publisher._git(ROOT, "rev-parse", "HEAD")).strip()
    return {
        "commit": commit,
        "generated_at": "2026-09-04T22:00:00Z",
        "state": json.loads(
            (ROOT / PROGRAM / "program-state.json").read_text(encoding="utf-8")
        ),
        "work_registry": json.loads(
            (ROOT / PROGRAM / "work-registry.json").read_text(encoding="utf-8")
        ),
    }


def add_evidence(value, check_id):
    source = value["work_registry"]["milestone"]
    check = next(c for c in source["checks"] if c["id"] == check_id)
    commit = value["commit"]
    path = "specs/079-wright-native-authoring/tasks.md"
    source["evidence"] = [
        {
            "id": "EV-REGRESSION",
            "check_id": check_id,
            "attempt": 1,
            "result": "passed",
            "observed_at": value["generated_at"],
            "tested_commit": commit,
            "tested_tree": str(
                publisher._git(ROOT, "rev-parse", f"{commit}^{{tree}}")
            ).strip(),
            "scope_sha256": publisher._milestone_scope_digest(
                ROOT, commit, check["source_paths"]
            ),
            "author_id": "test-author",
            "verifier_id": "test-reviewer",
            "verification_actor_kind": "automated",
            "summary": "Regression fixture only",
            "artifacts": [
                {
                    "path": path,
                    "sha256": publisher._raw_digest(
                        publisher._git_blob(ROOT, commit, path)
                    ),
                    "commit": commit,
                }
            ],
            "counts": None,
        }
    ]


def test_absent_required_source_never_receives_quality_credit():
    value = subject()
    check = next(
        c
        for c in value["work_registry"]["milestone"]["checks"]
        if c["id"] == "Q-SEMANTICS"
    )
    check["source_paths"] = ["packages/core/src/core/absent-native-regression.py"]
    add_evidence(value, "Q-SEMANTICS")
    projected = publisher._project_native_milestone(ROOT, value)
    assert projected["attestations"][0]["coverage_available"] is False
    assert (
        next(c for c in projected["checks"] if c["id"] == "Q-SEMANTICS")["status"]
        == "invalid"
    )


def test_old_f02_merge_does_not_attest_native_integration():
    value = subject()
    value["work_registry"]["milestone"]["delivery"].update(
        merged_commit="a69cb74405350fc90f2c9ae91c82eec6fd17e91d",
        pull_requests=[
            {
                "url": "https://github.com/burhop/wright/pull/117",
                "head_commit": "aff8179b15f0064acf88d5f282ed5fdce3cf5900",
                "observed_at": value["generated_at"],
            }
        ],
    )
    add_evidence(value, "Q-INTEGRATION")
    projected = publisher._project_native_milestone(ROOT, value)
    assert projected["delivery_attested"] is False
    assert (
        next(c for c in projected["checks"] if c["id"] == "Q-INTEGRATION")["status"]
        == "unavailable"
    )


def test_missing_narrative_sidecars_have_complete_safe_fallback():
    path = ROOT / "scripts/program_status/implementation-dashboard/server.py"
    spec = importlib.util.spec_from_file_location("dashboard_server_regression", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    lanes = module.unavailable_lanes()
    assert all(
        lanes[key]["nextAction"]
        for key in ("currentGoal", "integration", "development")
    )
    assert lanes["currentGoal"]["history"] == []
    assert lanes["integration"]["checks"]["passing"] == 0
