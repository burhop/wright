from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from tool_registry.milestone_status import derive_milestone, validate_milestone


ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "docs/programs/engineering-process-platform/work-registry.json"


def fixture():
    source = json.loads(SOURCE.read_text(encoding="utf-8"))["milestone"]
    # Each test supplies its own evidence and attestations. Live checkpoint
    # observations must not turn this synthetic empty-evidence case into a
    # mismatched proof set as implementation progresses.
    source["evidence"] = []
    tasks = {r["id"]: {"title": r["id"], "completed": False} for r in source["tasks"]}
    return source, tasks


def project(source, tasks, attestations=None, commit="a" * 40):
    return derive_milestone(
        source,
        tasks,
        source_commit=commit,
        observed_at="2026-09-04T22:00:00Z",
        attestations=attestations or [],
        delivery_attested=False,
    )


def evidence_fixture(source, result="passed"):
    source["evidence"] = [
        {
            "id": "EV-1",
            "check_id": "Q-SEMANTICS",
            "attempt": 1,
            "result": result,
            "observed_at": "2026-09-04T22:00:00Z",
            "tested_commit": "a" * 40,
            "tested_tree": "b" * 40,
            "scope_sha256": "c" * 64,
            "author_id": "author",
            "verifier_id": "reviewer",
            "verification_actor_kind": "automated",
            "summary": "Fixture result",
            "artifacts": [
                {
                    "path": "specs/079-wright-native-authoring/results.json",
                    "sha256": "d" * 64,
                    "commit": "a" * 40,
                }
            ],
            "counts": {
                "total": 1,
                "passed": 1,
                "failed": 0,
                "skipped": 0,
                "not_run": 0,
            },
        }
    ]
    return [
        {
            "evidence_id": "EV-1",
            "tested_scope_sha256": "c" * 64,
            "current_scope_sha256": "c" * 64,
            "commit_tree_matches": True,
            "artifacts_match": True,
            "coverage_available": True,
        }
    ]


@pytest.mark.parametrize("implemented", [False, True])
def test_missing_evidence_has_no_verification_or_integration_credit(implemented):
    source, tasks = fixture()
    for task in tasks.values():
        task["completed"] = implemented
    value = project(source, tasks)
    assert value["counts"] == {
        "implementation": {"completed": 32 if implemented else 0, "total": 32},
        "verification": {"completed": 0, "total": 32},
        "integration": {"completed": 0, "total": 30, "not_applicable": 2},
    }
    validate_milestone(value, "a" * 40)
    value["counts"]["verification"]["completed"] = 1
    with pytest.raises(ValueError):
        validate_milestone(value, "a" * 40)


@pytest.mark.parametrize("mismatch", ["missing", "extra", "different_identity"])
def test_evidence_and_attestations_must_match_exactly(mismatch):
    source, tasks = fixture()
    attestations = evidence_fixture(source)
    if mismatch == "missing":
        attestations.clear()
    elif mismatch == "extra":
        source["evidence"].clear()
    else:
        attestations[0]["evidence_id"] = "OTHER"
    with pytest.raises(ValueError, match="milestone evidence attestation set differs"):
        project(source, tasks, attestations)


def test_unchanged_scoped_code_retains_credit_at_new_evidence_commit():
    source, tasks = fixture()
    attestations = evidence_fixture(source)
    tasks["T006"]["completed"] = True
    value = project(source, tasks, attestations, "e" * 40)
    assert (
        next(c for c in value["checks"] if c["id"] == "Q-SEMANTICS")["status"]
        == "passed"
    )
    attestations[0]["current_scope_sha256"] = "f" * 64
    value = project(source, tasks, attestations, "e" * 40)
    assert (
        next(c for c in value["checks"] if c["id"] == "Q-SEMANTICS")["status"]
        == "stale"
    )
    assert value["counts"]["verification"]["completed"] == 0


@pytest.mark.parametrize(
    "result", ["failed", "skipped", "not_run", "unavailable", "inconclusive"]
)
def test_nonpassing_results_are_visible_without_credit(result):
    source, tasks = fixture()
    value = project(source, tasks, evidence_fixture(source, result))
    assert (
        next(c for c in value["checks"] if c["id"] == "Q-SEMANTICS")["status"] == result
    )
    assert value["counts"]["verification"]["completed"] == 0


def test_agent_does_not_count_as_human_and_missing_artifact_is_invalid():
    source, tasks = fixture()
    attestations = evidence_fixture(source)
    source["evidence"][0]["check_id"] = "Q-HUMAN"
    value = project(source, tasks, attestations)
    assert (
        next(c for c in value["checks"] if c["id"] == "Q-HUMAN")["status"] == "invalid"
    )
    source["evidence"][0]["verification_actor_kind"] = "human"
    source["evidence"][0]["artifacts"] = []
    value = project(source, tasks, attestations)
    assert (
        next(c for c in value["checks"] if c["id"] == "Q-HUMAN")["status"] == "invalid"
    )


@pytest.mark.parametrize("mutation", ["duplicate", "unknown", "denominator", "counts"])
def test_invalid_identity_coverage_and_counts_rejected(mutation):
    source, tasks = fixture()
    attestations = evidence_fixture(source)
    if mutation == "duplicate":
        source["tasks"].append(copy.deepcopy(source["tasks"][0]))
    if mutation == "unknown":
        source["acceptance"][0]["required_check_ids"].append("UNKNOWN")
    if mutation == "denominator":
        source["scope_history"][0]["added_task_ids"].pop()
    if mutation == "counts":
        source["evidence"][0]["counts"]["total"] = 2
    with pytest.raises(ValueError):
        project(source, tasks, attestations)
