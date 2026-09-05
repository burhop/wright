from __future__ import annotations

import hashlib
import json
import re
from copy import deepcopy
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


def test_canonical_numbers_match_browser_shortest_representation() -> None:
    assert publisher._canonical_bytes({"integral": 1.0}) == b'{"integral":1}'
    assert publisher._canonical_bytes({"ratio": 2 / 3}) == (
        b'{"ratio":0.6666666666666666}'
    )
    assert publisher._canonical_bytes({"small": 0.00001}) == b'{"small":1e-05}'


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
    dependencies = bundle["supplement"]["benchmark_context"]["dependencies"]
    assert {item["id"] for item in dependencies if item["blocking"]} == {
        "EPP-B01",
        "EPP-F03",
        "EPP-F05",
        "EPP-F06",
    }
    assert (
        next(item for item in dependencies if item["id"] == "EPP-F01")["status"]
        == "satisfied"
    )
    histories = {series["id"]: series for series in bundle["supplement"]["history"]}
    assert histories["feature_tasks"]["availability"] == "available"
    expected_completed, expected_total = publisher._task_counts(
        publisher._git_blob(
            REPOSITORY,
            first.source_commit,
            json.loads(
                publisher._git_blob(
                    REPOSITORY, first.source_commit, publisher.SOURCE_CATALOG_PATH
                )
            )["sources"]["feature_tasks"]["path"],
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
    observed_times = [
        observation["observed_at"]
        for observation in histories["feature_tasks"]["observations"]
    ]
    assert observed_times == sorted(observed_times)
    feature_observations = histories["feature_tasks"]["observations"]
    assert histories["feature_tasks"]["latest_change"] == {
        "commit": feature_observations[-1]["commit"],
        "observed_at": feature_observations[-1]["observed_at"],
        "from_value": feature_observations[-2]["value"]
        if len(feature_observations) > 1
        else None,
        "to_value": feature_observations[-1]["value"],
        "reason": feature_observations[-1]["change_reason"],
    }
    evidence_index = bundle["supplement"]["evidence_index"]
    development_lane = bundle["supplement"]["work"]["lanes"][1]
    task_reference = next(
        item
        for item in development_lane["evidence"]
        if item["id"] == "active-feature-tasks"
    )
    assert task_reference in [
        {key: item[key] for key in ("id", "path", "sha256")} for item in evidence_index
    ]
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


def test_committed_test_ledger_append_only_attestation_is_proven() -> None:
    subject = publisher._load_subject(REPOSITORY, "HEAD")

    assert (
        publisher._verify_test_ledger_append_only(REPOSITORY, subject)
        == (subject["ledger"]["prior_ledger"]["runs_sha256"])
    )

    subject["ledger"] = {
        **subject["ledger"],
        "ledger_revision": subject["ledger"]["ledger_revision"] + 1,
    }
    with pytest.raises(ProgramStatusPublishError) as raised:
        publisher._verify_test_ledger_append_only(REPOSITORY, subject)

    assert raised.value.code == "PROGRAM_STATUS_TEST_LEDGER_INVALID"

    subject = publisher._load_subject(REPOSITORY, "HEAD")
    subject["ledger"] = {**subject["ledger"], "runs_sha256": "0" * 64}
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


def test_use_case_projection_rejects_duplicate_and_out_of_range_process_ids() -> None:
    duplicate = _use_case_subject()
    first = duplicate["use_case_registry"]["use_cases"][0]
    duplicate["use_case_registry"]["use_cases"] = [
        first,
        {**first, "id": "EPP-UC-002"},
    ]
    with pytest.raises(ProgramStatusPublishError) as raised:
        publisher._derive_use_cases(duplicate)
    assert raised.value.code == "PROGRAM_STATUS_PROCESS_ID_INVALID"

    outside = _use_case_subject()
    outside["use_case_registry"]["use_cases"][0]["process_100_id"] = "EPP-PROC-101"
    with pytest.raises(ProgramStatusPublishError) as raised:
        publisher._derive_use_cases(outside)
    assert raised.value.code == "PROGRAM_STATUS_PROCESS_ID_INVALID"


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


def test_work_registry_projects_exact_tasks_assignments_and_roadmap_gap(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    subject = publisher._load_subject(REPOSITORY, "HEAD")
    # Exercise historical F02 task assignment against the current closed registry.
    subject["state"]["current_feature"] = "EPP-F02"
    for task_source in subject["work_registry"]["task_sources"]:
        task_source["active_feature"] = task_source["feature_id"] == "EPP-F02"
    subject["catalog_sources"] = publisher._load_closed_catalog_sources(
        REPOSITORY, subject
    )
    task_path = "specs/078-process-definition-view/tasks.md"
    task_raw = publisher._git_blob(REPOSITORY, subject["commit"], task_path)
    task_id = "T001"
    completed_marker = f"- [X] {task_id} ".encode()
    incomplete_marker = f"- [ ] {task_id} ".encode()
    assert task_raw.count(completed_marker) == 1
    incomplete_task_raw = task_raw.replace(completed_marker, incomplete_marker, 1)
    task = publisher._task_records(incomplete_task_raw)[task_id]
    original_git_blob = publisher._git_blob

    def _git_blob_with_active_task(repository: Path, commit: str, path: str) -> bytes:
        if path == task_path:
            return incomplete_task_raw
        return original_git_blob(repository, commit, path)

    monkeypatch.setattr(publisher, "_git_blob", _git_blob_with_active_task)
    subject["work_registry"] = {
        **subject["work_registry"],
        "active_assignments": [
            {
                "agent_id": "primary-agent",
                "feature_id": "EPP-F02",
                "task_id": task_id,
                "task_title": task["title"],
                "task_state": "in_progress",
                "branch": "test-assignment-branch",
                "worktree_id": "test-assignment-worktree",
                "lane": "continued_development",
                "why_this_matters": "Closes false status claims before customer review.",
                "observed_at": subject["generated_at"],
                "evidence": [
                    {
                        "path": task_path,
                        "sha256": hashlib.sha256(incomplete_task_raw).hexdigest(),
                    }
                ],
            }
        ],
    }
    subject["state"] = {
        **subject["state"],
        "active_mutating_lease": {
            "branch": "test-assignment-branch",
            "worktree_id": "test-assignment-worktree",
        },
    }
    result = publisher._registered_task_counts(REPOSITORY, subject, "EPP-F02")

    registered, program_done, program_total, feature_done, feature_total = result[:5]
    assignments, undecomposed = result[5:]
    assert registered == [
        "specs/076-control-plane-validator/tasks.md",
        "specs/077-browser-program-status/tasks.md",
        task_path,
        "specs/079-wright-native-authoring/tasks.md",
    ]
    assert 0 <= program_done <= program_total
    assert 0 <= feature_done < feature_total
    assert assignments[0]["task_id"] == task_id
    assert assignments[0]["evidence"][0]["path"] == task_path
    assert "EPP-F03" in undecomposed
    assert "EPP-F02" not in undecomposed
    assert "EPP-F01B" not in undecomposed

    invalid = {**subject, "work_registry": {**subject["work_registry"]}}
    invalid["work_registry"]["task_sources"] = [
        *subject["work_registry"]["task_sources"],
        subject["work_registry"]["task_sources"][1],
    ]
    with pytest.raises(ProgramStatusPublishError) as raised:
        publisher._registered_task_counts(REPOSITORY, invalid, "EPP-F02")
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


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("path", ""),
        ("path", "docs//programs/status.json"),
        ("path", "docs/./programs/status.json"),
        ("path", "docs/programs/../status.json"),
        (
            "exact_url",
            "https://user@github.com/burhop/wright/blob/"
            + "a" * 40
            + "/docs/status.json",
        ),
        (
            "exact_url",
            "https://github.com:443/burhop/wright/blob/"
            + "a" * 40
            + "/docs/status.json",
        ),
        (
            "exact_url",
            "https://github.com/burhop/wright/blob/"
            + "a" * 40
            + "/docs/status.json?raw=1",
        ),
        (
            "exact_url",
            "https://github.com/burhop/wright/blob/"
            + "a" * 40
            + "/docs/status.json#frag",
        ),
        (
            "exact_url",
            "https://github.com/burhop/wrong/blob/" + "a" * 40 + "/docs/status.json",
        ),
    ],
)
def test_frozen_bundle_rejects_noncanonical_paths_and_github_urls(
    field: str, value: str
) -> None:
    packaged = REPOSITORY / "src" / "wright_engineering" / "static" / "program-status"
    bundle = json.loads((packaged / "current.json").read_bytes())
    candidate = deepcopy(bundle)
    detail = candidate["supplement"]["evidence_index"][0]
    detail[field] = value
    if field == "exact_url":
        detail["availability"] = "exact_github"
    bundle_schema = json.loads(
        (
            REPOSITORY
            / "specs"
            / "077-browser-program-status"
            / "contracts"
            / "program-status-bundle.schema.json"
        ).read_bytes()
    )
    dashboard_schema = json.loads(
        (
            REPOSITORY
            / "docs"
            / "programs"
            / "engineering-process-platform"
            / "schemas"
            / "dashboard.schema.json"
        ).read_bytes()
    )
    registry = publisher.Registry().with_resource(
        dashboard_schema["$id"], publisher.Resource.from_contents(dashboard_schema)
    )

    errors = list(
        publisher.Draft202012Validator(
            bundle_schema,
            registry=registry,
            format_checker=publisher.FormatChecker(),
        ).iter_errors(candidate)
    )

    if errors:
        return
    with pytest.raises(ProgramStatusPublishError):
        publisher._validate_evidence_details(candidate)


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
    summary = {
        **base,
        "run_id": "summary-attempt-1",
        "suite_id": "summary-suite",
        "population_id": "summary",
        "attempt": 1,
        "aggregate_role": "summary_only",
        "counts": {"total": 2, "passed": 1, "failed": 1, "skipped": 0, "not_run": 0},
    }
    summary["run_key"] = publisher._test_run_key(summary)

    checkpoints, selected, _evidence = publisher._project_test_history(
        {"runs": [first, second, summary]}, "a" * 40
    )

    assert selected == ["summary-attempt-1", "unit-attempt-2"]
    assert checkpoints[0]["counts"] == second["counts"]
    assert checkpoints[0]["pass_rate"] == 1
    assert checkpoints[0]["categories"]["unit"] == second["counts"]
    assert checkpoints[0]["categories"]["benchmark"] is None


def test_canonical_test_projection_rejects_run_key_and_count_drift() -> None:
    base = {
        "run_id": "unit-attempt-1",
        "commit": "a" * 40,
        "suite_id": "unit-suite",
        "population_id": "pkg",
        "attempt": 1,
        "observed_at": "2026-08-29T14:00:00Z",
        "category": "unit",
        "terminal": True,
        "aggregate_role": "component",
        "test_case_ids": ["tests/a.py::test_x"],
        "counts": {"total": 1, "passed": 1, "failed": 0, "skipped": 0, "not_run": 0},
        "evidence": [
            {
                "path": "test-results/program-status/unit.json",
                "sha256": "b" * 64,
            }
        ],
    }
    base["test_case_set_sha256"] = publisher._test_case_set_digest(
        base["test_case_ids"]
    )
    base["run_key"] = publisher._test_run_key(base)
    for field, value in (
        ("run_key", "0" * 64),
        ("counts", {"total": 2, "passed": 1, "failed": 0, "skipped": 0, "not_run": 0}),
    ):
        invalid = {**base, field: value}
        with pytest.raises(ProgramStatusPublishError) as raised:
            publisher._project_test_history({"runs": [invalid]}, "a" * 40)
        assert raised.value.code == "PROGRAM_STATUS_TEST_LEDGER_INVALID"


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


def test_history_series_have_fixed_semantics_and_causal_committed_order(
    tmp_path: Path,
) -> None:
    publish_program_status(request(tmp_path))
    bundle = json.loads((tmp_path / "current.json").read_bytes())
    series = bundle["supplement"]["history"]

    assert [item["id"] for item in series] == [
        "customer_capability",
        "quality",
        "process_automation",
        "governance",
        "product_readiness",
        "benchmark_readiness",
        "commercial_readiness",
        "program_health",
        "benchmark_qualified",
        "program_tasks",
        "feature_tasks",
        "integration_delivery",
    ]
    semantic_keys = {
        (
            item["id"],
            item["unit"],
            item["counting_rule"],
            item["source_classification"],
        )
        for item in series
    }
    assert len(semantic_keys) == len(series)
    for item in series:
        observations = item["observations"]
        assert item["omitted_observations"] >= 0
        assert len(observations) <= 250
        assert [row["observed_at"] for row in observations] == sorted(
            row["observed_at"] for row in observations
        )
        if observations:
            assert item["latest_change"]["commit"] == observations[-1]["commit"]
            assert item["latest_change"]["to_value"] == observations[-1]["value"]

    work = bundle["supplement"]["work"]
    assert work["program_tasks"]["remaining"] == (
        work["program_tasks"]["total"] - work["program_tasks"]["completed"]
    )
    assert work["tasks"]["remaining"] == (
        work["tasks"]["total"] - work["tasks"]["completed"]
    )
    assert work["program_tasks"]["undecomposed_roadmap_items"]

    details = bundle["supplement"]["evidence_index"]
    use_case = bundle["supplement"]["use_cases"]["items"][0]
    for stage_name in (
        "acceptance_evidence",
        "test_evidence",
        "independent_verification_evidence",
    ):
        for record in use_case[stage_name]:
            reference = record["evidence"]
            assert [
                detail
                for detail in details
                if all(
                    detail[key] == reference[key] for key in ("id", "path", "sha256")
                )
            ]

    development = next(
        lane
        for lane in bundle["supplement"]["work"]["lanes"]
        if lane["kind"] == "continued_development"
    )
    assert development["latest_capability"] == (
        "Native acceptance is tracked by the milestone criteria. "
        "The historical catalog has 1 accepted and 1 independently verified use cases; "
        "these do not grant native acceptance credit."
    )
    assert use_case["acceptance_evidence"][0]["evidence"] in development["evidence"]


def test_delivery_lanes_are_derived_from_closed_committed_sources() -> None:
    # Retain the closed historical checkpoint even while native implementation
    # opens a new lease or advances to later delivery states.
    subject = publisher._load_subject(REPOSITORY, "HEAD")
    subject["blobs"][publisher.STATE_PATH] = publisher._git_blob(
        REPOSITORY,
        "88d36f3793f05a29f10a210623788b93ed32cfcd",
        publisher.STATE_PATH,
    )
    subject["state"] = json.loads(subject["blobs"][publisher.STATE_PATH])
    # This unit projection deliberately selects the preserved historical feature.
    subject["state"]["current_feature"] = "EPP-F02"
    subject["catalog_sources"] = publisher._load_closed_catalog_sources(
        REPOSITORY, subject
    )
    state_ref = publisher._evidence(
        "program-state", publisher.STATE_PATH, subject["blobs"][publisher.STATE_PATH]
    )
    tasks_ref = publisher._evidence(
        "active-feature-tasks",
        "specs/078-process-definition-view/tasks.md",
        publisher._git_blob(
            REPOSITORY,
            subject["commit"],
            "specs/078-process-definition-view/tasks.md",
        ),
    )

    integration, development = publisher._project_delivery_lanes(
        subject, state_ref, tasks_ref, 0, 19
    )

    assert integration["kind"] == "integration"
    assert integration["branch"] == "unavailable"
    assert integration["target_branch"] == "dev"
    assert integration["phase"] == "dev deployment verified"
    assert integration["pull_request"] == {
        "number": 114,
        "url": "https://github.com/burhop/wright/pull/114",
    }
    assert integration["blocker"] is None
    assert integration["events"][-1]["kind"] == "DEV_DEPLOYMENT_VERIFIED"
    assert integration["events"][-1]["evidence"][0] in integration["evidence"]
    assert integration["latest_capability"].startswith("Verified integration evidence:")
    assert integration["next_action"]["authority_state"] == "not_required"

    assert development["kind"] == "continued_development"
    assert subject["state"]["active_mutating_lease"] is None
    assert development["branch"] == "unavailable"
    assert development["base_commit"] == subject["state"]["baseline"]["commit"]
    assert development["milestone"] == (
        "Canonical process definition and read-only engineer view"
    )
    assert development["authority_state"] == "unavailable"
    assert (
        development["blocker"] == subject["state"]["next_eligible_actions"][0]["reason"]
    )
    assert development["next_action"]["requires_human_approval"] is False
    assert development["next_action"]["authority_state"] == "not_authorized"
    assert state_ref in development["evidence"]
    assert tasks_ref in development["evidence"]
    assert development["latest_capability"] == (
        "Unavailable: no committed customer acceptance evidence demonstrates "
        "a customer-visible EPP-F02 capability yet."
    )
