from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pytest

from scripts.program_status import publisher
from scripts.program_status.publisher import (
    ProgramStatusPublishError,
    ProgramStatusPublishRequest,
    publish_program_status,
    watch_program_status,
)


REPOSITORY = Path(__file__).resolve().parents[2]


def request(data_root: Path, source: str = "HEAD") -> ProgramStatusPublishRequest:
    return ProgramStatusPublishRequest(REPOSITORY, source, data_root)


def canonical(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def test_publishes_exact_dashboard_and_deterministic_identity(tmp_path: Path) -> None:
    first = publish_program_status(request(tmp_path))
    installed = (tmp_path / "current.json").read_bytes()
    bundle = json.loads(installed)

    dashboard_raw = publisher._git_blob(
        REPOSITORY, first.source_commit, publisher.DASHBOARD_PATH
    )
    dashboard = json.loads(dashboard_raw)
    assert bundle["dashboard"] == dashboard
    assert (
        bundle["source"]["snapshot_raw_sha256"]
        == hashlib.sha256(dashboard_raw).hexdigest()
    )
    assert bundle["source"]["commit"] == first.source_commit
    assert bundle["source"]["tree"] == first.source_tree
    assert bundle["source"]["program_tree"] == first.program_tree
    assert bundle["supplement"]["governance"]["limits"] == {
        "wip_max": 1,
        "repair_max": 2,
        "push_max": 2,
    }
    assert bundle["supplement"]["use_cases"]["process_100"]["benchmark_qualified"] == 0
    histories = {series["id"]: series for series in bundle["supplement"]["history"]}
    assert histories["feature_tasks"]["availability"] == "available"
    expected_completed, expected_total = publisher._task_counts(
        publisher._git_blob(
            REPOSITORY,
            first.source_commit,
            "specs/077-browser-program-status/tasks.md",
        )
    )
    assert histories["feature_tasks"]["observations"][-1]["value"] == expected_completed
    assert (
        histories["feature_tasks"]["observations"][-1]["denominator"] == expected_total
    )
    assert histories["benchmark_qualified"]["observations"][-1]["value"] == 0
    assert histories["benchmark_qualified"]["observations"][-1]["denominator"] == 100
    for observation in histories["feature_tasks"]["observations"]:
        assert len(observation["commit"]) == 40
        assert observation["observed_at"]
        assert observation["evidence"]
        assert isinstance(observation["value"], int)
        assert isinstance(observation["denominator"], int)
    evidence_index = bundle["supplement"]["evidence_index"]
    for series in histories.values():
        for observation in series["observations"]:
            for reference in observation["evidence"]:
                matches = [
                    detail
                    for detail in evidence_index
                    if all(detail[key] == reference[key] for key in reference)
                ]
                assert len(matches) == 1
                assert matches[0]["availability"] == "identity_only"
    assert first.changed is True

    second = publish_program_status(request(tmp_path))
    assert second == publisher.ProgramStatusPublishResult(
        source_commit=first.source_commit,
        source_tree=first.source_tree,
        program_tree=first.program_tree,
        bundle_id=first.bundle_id,
        installed_artifact="current.json",
        changed=False,
    )
    assert (tmp_path / "current.json").read_bytes() == installed


def test_nonexistent_subject_fails_without_installing(tmp_path: Path) -> None:
    with pytest.raises(ProgramStatusPublishError) as raised:
        publish_program_status(request(tmp_path, "does-not-exist"))

    assert raised.value.code == "PROGRAM_STATUS_GIT_READ_FAILED"
    assert not (tmp_path / "current.json").exists()


def test_replacement_failure_preserves_prior_bundle(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    prior = b"prior-valid-bundle"
    current = tmp_path / "current.json"
    current.write_bytes(prior)

    def fail_replace(_source: Path, _destination: Path) -> None:
        raise PermissionError("simulated Windows sharing violation")

    monkeypatch.setattr(publisher.os, "replace", fail_replace)
    with pytest.raises(ProgramStatusPublishError) as raised:
        publish_program_status(request(tmp_path))

    assert raised.value.code == "PROGRAM_STATUS_INSTALL_FAILED"
    assert current.read_bytes() == prior
    assert list(tmp_path.glob(".current.json.*.tmp")) == []


def test_bundle_identity_recomputes_from_canonical_payload(tmp_path: Path) -> None:
    result = publish_program_status(request(tmp_path))
    bundle = json.loads((tmp_path / "current.json").read_bytes())
    payload = {
        "source": bundle["source"],
        "dashboard": bundle["dashboard"],
        "supplement": bundle["supplement"],
    }

    assert hashlib.sha256(canonical(payload)).hexdigest() == result.bundle_id
    assert bundle["bundle_id"] == result.bundle_id


def test_committed_watch_publishes_once_and_refreshes_heartbeat(tmp_path: Path) -> None:
    result = watch_program_status(request(tmp_path), poll_seconds=0.001, max_polls=2)

    assert result is not None
    assert result.changed is True
    heartbeat = json.loads((tmp_path / "publisher.json").read_bytes())
    assert heartbeat["state"] == "active"
    assert heartbeat["mode"] == "committed_watch"
    assert heartbeat["observed_commit"] == result.source_commit
    assert heartbeat["last_success_at"]


def test_committed_watch_records_bounded_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def reject(
        _request: ProgramStatusPublishRequest,
    ) -> publisher.ProgramStatusPublishResult:
        raise ProgramStatusPublishError(
            "PROGRAM_STATUS_TEST_FAILURE", "test failure", "repair_test_subject"
        )

    monkeypatch.setattr(publisher, "publish_program_status", reject)
    assert watch_program_status(request(tmp_path), max_polls=1) is None

    heartbeat = json.loads((tmp_path / "publisher.json").read_bytes())
    assert heartbeat["state"] == "failed"
    assert heartbeat["failure_code"] == "PROGRAM_STATUS_TEST_FAILURE"
    assert heartbeat["recovery"] == "repair_test_subject"


def test_action_preserves_human_approval_boundary() -> None:
    evidence = [{"id": "state", "path": publisher.STATE_PATH, "sha256": "a" * 64}]

    action = publisher._action(
        "APPROVE_NEXT_GATE",
        "Approve the next exact subject",
        "current_program_action",
        evidence,
        eligible=False,
        blocker="Human approval is required.",
        requires_human_approval=True,
    )

    assert action["eligibility"] == "requires_approval"
    assert action["authority_state"] == "not_authorized"
    assert action["requires_human_approval"] is True
    assert action["blocker"] == "Human approval is required."


def test_initial_test_ledger_append_only_attestation_is_proven() -> None:
    subject = publisher._load_subject(REPOSITORY, "HEAD")

    assert publisher._verify_test_ledger_append_only(REPOSITORY, subject) is None

    subject["ledger"] = {**subject["ledger"], "ledger_revision": 2}
    with pytest.raises(ProgramStatusPublishError) as raised:
        publisher._verify_test_ledger_append_only(REPOSITORY, subject)

    assert raised.value.code == "PROGRAM_STATUS_TEST_LEDGER_INVALID"


def test_frozen_source_catalog_selects_only_its_20_committed_inputs() -> None:
    subject = publisher._load_subject(REPOSITORY, "HEAD")
    selected = publisher._load_closed_catalog_sources(REPOSITORY, subject)

    assert set(selected) == set(subject["source_catalog"]["sources"])
    for name, rule in subject["source_catalog"]["sources"].items():
        paths = [path for path, _raw in selected[name]]
        if rule["path_kind"] == "exact":
            assert paths == [rule["path"]]
        else:
            pattern = re.compile(rule["path_pattern"])
            assert all(pattern.fullmatch(path) for path in paths)


def test_customer_story_maturity_is_derived_without_duplicate_definitions() -> None:
    raw = publisher._git_blob(REPOSITORY, "HEAD", publisher.CUSTOMER_CATALOG_PATH)

    assert publisher._customer_story_maturity(raw) == {
        "ready_to_specify": 5,
        "shaped": 15,
        "candidate": 45,
        "discovery_shaped": 15,
        "discovery": 14,
        "discovery_separate_t4_authority_required": 1,
        "fully_defined": 5,
    }

    with pytest.raises(ProgramStatusPublishError) as raised:
        publisher._customer_story_maturity(raw + b"\n### EPP-US-001 duplicate\n")
    assert raised.value.code == "PROGRAM_STATUS_CUSTOMER_CATALOG_INVALID"


def _use_case_subject() -> dict[str, object]:
    acceptance = {
        "id": "ACC-001",
        "verdict": "passed",
        "evidence_author": "customer-reviewer",
    }
    verification = {
        "id": "VER-001",
        "verdict": "passed",
        "acceptance_subject_id": "ACC-001",
        "evidence_author": "implementation-agent",
        "independent_verifier": "independent-reviewer",
    }
    gate_raw = canonical({"records": [acceptance]})
    verification_raw = canonical({"records": [verification]})
    item = {
        "id": "EPP-UC-001",
        "title": "Inspect program status",
        "customer_outcome": "A customer can inspect an evidence-backed status page.",
        "process_100_id": "EPP-PROC-001",
        "definition_evidence": [],
        "progress_evidence": [],
        "acceptance_evidence": [
            {
                "evidence_class": "customer_acceptance",
                "source_name": "gate_evidence",
                "path": "docs/programs/engineering-process-platform/gate-evidence.json",
                "sha256": hashlib.sha256(gate_raw).hexdigest(),
                "subject_id": "ACC-001",
                "verdict": "passed",
                "acceptance_subject_id": None,
                "evidence_author": "customer-reviewer",
                "independent_verifier": None,
            }
        ],
        "test_evidence": [],
        "independent_verification_evidence": [
            {
                "evidence_class": "independent_verification",
                "source_name": "verification_evidence",
                "path": "docs/programs/engineering-process-platform/evidence/verification/VER-001.json",
                "sha256": hashlib.sha256(verification_raw).hexdigest(),
                "subject_id": "VER-001",
                "verdict": "passed",
                "acceptance_subject_id": "ACC-001",
                "evidence_author": "implementation-agent",
                "independent_verifier": "independent-reviewer",
            }
        ],
        "benchmark_qualification_evidence": [],
    }
    return {
        "use_case_registry": {"use_cases": [item]},
        "catalog_sources": {
            "gate_evidence": [
                (
                    "docs/programs/engineering-process-platform/gate-evidence.json",
                    gate_raw,
                )
            ],
            "verification_evidence": [
                (
                    "docs/programs/engineering-process-platform/evidence/verification/VER-001.json",
                    verification_raw,
                )
            ],
        },
        "dashboard": {"benchmark_summary": {"counted": 0}},
    }


def test_use_case_projection_requires_resolved_evidence_and_independence() -> None:
    subject = _use_case_subject()

    items, process_ids, funnels = publisher._derive_use_cases(subject)

    assert process_ids == ["EPP-PROC-001"]
    assert funnels["all"] == {
        "total": 1,
        "not_started": 0,
        "in_progress": 0,
        "implemented": 1,
        "independently_verified": 1,
        "remaining": 0,
    }
    assert funnels["process_100"]["implemented"] == 1
    assert funnels["process_100"]["benchmark_qualified"] == 0
    assert items[0]["acceptance_evidence"][0]["evidence"]["id"]

    invalid = _use_case_subject()
    invalid_item = invalid["use_case_registry"]["use_cases"][0]
    invalid_item["independent_verification_evidence"][0]["independent_verifier"] = (
        "implementation-agent"
    )
    with pytest.raises(ProgramStatusPublishError) as raised:
        publisher._derive_use_cases(invalid)
    assert raised.value.code == "PROGRAM_STATUS_USE_CASE_EVIDENCE_INVALID"


def test_use_case_projection_rejects_wrong_path_digest_and_missing_subject() -> None:
    for field, value in (
        ("path", "docs/programs/engineering-process-platform/gate-catalog.json"),
        ("sha256", "f" * 64),
        ("subject_id", "ACC-MISSING"),
    ):
        subject = _use_case_subject()
        evidence = subject["use_case_registry"]["use_cases"][0]["acceptance_evidence"][
            0
        ]
        evidence[field] = value
        with pytest.raises(ProgramStatusPublishError) as raised:
            publisher._derive_use_cases(subject)
        assert raised.value.code == "PROGRAM_STATUS_USE_CASE_EVIDENCE_INVALID"


def test_governance_register_projection_uses_exact_catalog_sources() -> None:
    subject = publisher._load_subject(REPOSITORY, "HEAD")
    subject["catalog_sources"] = publisher._load_closed_catalog_sources(
        REPOSITORY, subject
    )

    risks, decisions = publisher._project_governance_registers(subject)

    assert len(risks) == 22
    assert len(decisions) == 20
    assert sum(item["blocks"] for item in risks) == 3
    assert sum(item["blocks"] for item in decisions) == 11
    assert all(item["evidence"] for item in risks + decisions)

    subject["catalog_sources"] = {
        **subject["catalog_sources"],
        "risk_register": [],
    }
    with pytest.raises(ProgramStatusPublishError) as raised:
        publisher._project_governance_registers(subject)
    assert raised.value.code == "PROGRAM_STATUS_GOVERNANCE_SOURCE_INVALID"


def test_work_registry_projects_exact_tasks_assignments_and_roadmap_gap() -> None:
    subject = publisher._load_subject(REPOSITORY, "HEAD")
    subject["catalog_sources"] = publisher._load_closed_catalog_sources(
        REPOSITORY, subject
    )
    task_path = "specs/077-browser-program-status/tasks.md"
    task_raw = publisher._git_blob(REPOSITORY, subject["commit"], task_path)
    task = publisher._task_records(task_raw)["T005"]
    subject["work_registry"] = {
        **subject["work_registry"],
        "active_assignments": [
            {
                "agent_id": "primary-agent",
                "feature_id": "EPP-F01B",
                "task_id": "T005",
                "task_title": task["title"],
                "task_state": "in_progress",
                "branch": subject["state"]["active_mutating_lease"]["branch"],
                "worktree_id": subject["state"]["active_mutating_lease"]["worktree_id"],
                "lane": "continued_development",
                "why_this_matters": "Closes false status claims before customer review.",
                "observed_at": subject["generated_at"],
                "evidence": [
                    {
                        "path": task_path,
                        "sha256": hashlib.sha256(task_raw).hexdigest(),
                    }
                ],
            }
        ],
    }

    result = publisher._registered_task_counts(REPOSITORY, subject, "EPP-F01B")

    registered, program_done, program_total, feature_done, feature_total = result[:5]
    assignments, undecomposed = result[5:]
    assert registered == [
        "specs/076-control-plane-validator/tasks.md",
        task_path,
    ]
    assert 0 <= program_done <= program_total
    assert 0 <= feature_done < feature_total
    assert assignments[0]["task_id"] == "T005"
    assert assignments[0]["evidence"][0]["path"] == task_path
    assert "EPP-F02" in undecomposed
    assert "EPP-F01B" not in undecomposed

    invalid = {**subject, "work_registry": {**subject["work_registry"]}}
    invalid["work_registry"]["task_sources"] = [
        *subject["work_registry"]["task_sources"],
        subject["work_registry"]["task_sources"][1],
    ]
    with pytest.raises(ProgramStatusPublishError) as raised:
        publisher._registered_task_counts(REPOSITORY, invalid, "EPP-F01B")
    assert raised.value.code == "PROGRAM_STATUS_WORK_REGISTRY_INVALID"


def test_correction_graph_projects_only_closed_reciprocal_evidence() -> None:
    subject = publisher._load_subject(REPOSITORY, "HEAD")
    subject["catalog_sources"] = publisher._load_closed_catalog_sources(
        REPOSITORY, subject
    )

    corrections, findings, verifications, details = publisher._project_correction_graph(
        subject
    )

    assert [item["profile_id"] for item in corrections] == [
        "COR-EPP-F01-V9-PREFLIGHT-EVIDENCE-001"
    ]
    assert {item["id"] for item in findings} == {
        "V8-DISCOVERY-SCHEMA-REFERENCE-001",
        "TR0051-MANIFEST-ORDER-001",
    }
    assert [item["id"] for item in verifications] == ["VER-EPP-F01-V9-001"]
    assert corrections[0]["verification_ids"] == [verifications[0]["id"]]
    assert verifications[0]["finding_ids"] == corrections[0]["finding_ids"]
    assert len({item["id"] for item in details}) == len(details)


def test_canonical_test_identity_and_latest_terminal_selection() -> None:
    test_ids = ["tests/a.py::test_x", "tests/a.py::test_y[param]"]
    assert (
        publisher._test_case_set_digest(test_ids)
        == "c4e6eafe639dc63fa01d5d2b41d04e105847a75f97c669fc3c0087c94376a1b7"
    )
    base = {
        "commit": "a" * 40,
        "suite_id": "unit-suite",
        "population_id": "pkg",
        "observed_at": "2026-08-29T14:00:00Z",
        "category": "unit",
        "terminal": True,
        "aggregate_role": "component",
        "test_case_ids": test_ids,
        "test_case_set_sha256": publisher._test_case_set_digest(test_ids),
        "evidence": [
            {
                "path": "test-results/program-status/unit.json",
                "sha256": "b" * 64,
            }
        ],
    }
    first = {
        **base,
        "run_id": "unit-attempt-1",
        "attempt": 1,
        "counts": {"total": 2, "passed": 1, "failed": 1, "skipped": 0, "not_run": 0},
    }
    first["run_key"] = publisher._test_run_key(first)
    assert (
        first["run_key"]
        == "dddb7540d46b1f8e83791141ac94b5f0bc38effee28f32baa36c6fc5be96ad5f"
    )
    second = {
        **base,
        "run_id": "unit-attempt-2",
        "attempt": 2,
        "observed_at": "2026-08-29T14:01:00Z",
        "counts": {"total": 2, "passed": 2, "failed": 0, "skipped": 0, "not_run": 0},
    }
    second["run_key"] = publisher._test_run_key(second)

    checkpoints, selected, _evidence = publisher._project_test_history(
        {"runs": [first, second]}, "a" * 40
    )

    assert selected == ["unit-attempt-2"]
    assert checkpoints[0]["counts"] == second["counts"]
    assert checkpoints[0]["pass_rate"] == 1
    assert checkpoints[0]["categories"]["unit"] == second["counts"]
    assert checkpoints[0]["categories"]["benchmark"] is None


def test_canonical_test_projection_rejects_overlapping_component_populations() -> None:
    def run(population: str, test_ids: list[str]) -> dict[str, object]:
        value: dict[str, object] = {
            "run_id": f"run-{population}",
            "commit": "a" * 40,
            "suite_id": "unit-suite",
            "population_id": population,
            "attempt": 1,
            "observed_at": "2026-08-29T14:00:00Z",
            "category": "unit",
            "terminal": True,
            "aggregate_role": "component",
            "test_case_ids": test_ids,
            "test_case_set_sha256": publisher._test_case_set_digest(test_ids),
            "counts": {
                "total": len(test_ids),
                "passed": len(test_ids),
                "failed": 0,
                "skipped": 0,
                "not_run": 0,
            },
            "evidence": [
                {
                    "path": f"test-results/program-status/{population}.json",
                    "sha256": "c" * 64,
                }
            ],
        }
        value["run_key"] = publisher._test_run_key(value)
        return value

    with pytest.raises(ProgramStatusPublishError) as raised:
        publisher._project_test_history(
            {
                "runs": [
                    run("one", ["tests/a.py::shared"]),
                    run("two", ["tests/a.py::shared"]),
                ]
            },
            "a" * 40,
        )

    assert raised.value.code == "PROGRAM_STATUS_TEST_LEDGER_INVALID"
