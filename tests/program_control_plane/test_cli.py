"""US1 CLI parsing, source/container/delivery resolution, and rendering tests."""

from __future__ import annotations

import copy
import json
from dataclasses import replace
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path

import pytest

from program_control.cli import (
    EXIT_INTERNAL,
    EXIT_SCHEMA,
    _bounded_failure,
    _emit,
    _set_delivery,
    build_parser,
    main,
    render_text,
)
from program_control.git_subject import GitReader
from program_control import validation as validation_module
from program_control.validation import (
    _resolve_container_and_delivery,
    validate_program,
    validate_transition_input_origin_correction,
)
from program_control.model import Finding


PROGRAM_ROOT = "docs/programs/engineering-process-platform"
DASHBOARD = f"{PROGRAM_ROOT}/dashboard.json"
DELIVERY = f"{PROGRAM_ROOT}/evidence/verification/EPP-F01-dashboard-delivery.json"
INPUT_ORIGIN_CORRECTION = (
    f"{PROGRAM_ROOT}/evidence/corrections/COR-EPP-F01-US1-TR0027-INPUT-ORIGIN-001.json"
)
INPUT_ORIGIN_TARGET = (
    f"{PROGRAM_ROOT}/evidence/transitions/TR-0027.json",
    "/inputs/3",
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _input_origin_inputs(repository_root: Path) -> tuple[dict, dict[str, dict]]:
    profile = _load(repository_root / INPUT_ORIGIN_CORRECTION)
    approval_root = (
        repository_root
        / "docs/programs/engineering-process-platform/evidence/approvals"
    )
    approvals = {
        f"{PROGRAM_ROOT}/evidence/approvals/{name}": _load(approval_root / name)
        for name in ("APR-EPP-F01-MC-005.json", "APR-EPP-F01-IMPL-005.json")
    }
    return profile, approvals


def _delivery_history(git_builder) -> tuple[GitReader, str, str, str]:
    git_builder.write_json(DASHBOARD, {"generation_status": "seed"})
    git_builder.write_json(
        f"{PROGRAM_ROOT}/schemas/verification-evidence.schema.json",
        {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
        },
    )
    source = git_builder.commit("source S")
    dashboard = b'{"generation_status":"candidate_not_evidence"}\n'
    git_builder.write_bytes(DASHBOARD, dashboard)
    container = git_builder.commit("dashboard-only C")
    git_builder.write_json(
        DELIVERY,
        {
            "kind": "delivery",
            "verdict": "passed",
            "actor": {"role": "independent_verifier", "independent": True},
            "delivery_relation": {
                "source_commit": source,
                "container_commit": container,
                "dashboard": {"sha256": sha256(dashboard).hexdigest()},
            },
        },
    )
    delivery = git_builder.commit("delivery-only D")
    return GitReader(git_builder.root), source, container, delivery


def test_validate_parser_accepts_optional_container_and_delivery() -> None:
    args = build_parser().parse_args(
        [
            "validate",
            "--source",
            "source",
            "--container",
            "container",
            "--delivery",
            "delivery",
            "--format",
            "json",
        ]
    )
    assert (args.source, args.container, args.delivery, args.format) == (
        "source",
        "container",
        "delivery",
        "json",
    )


def test_container_is_explicit_or_only_constrained_head(git_builder) -> None:
    reader, source, container, _ = _delivery_history(git_builder)
    explicit_findings = []
    explicit, envelope = _resolve_container_and_delivery(
        reader,
        source,
        PROGRAM_ROOT,
        container=container,
        delivery=None,
        findings=explicit_findings,
    )
    assert explicit_findings == []
    assert explicit["container_resolution"] == "explicit"
    assert envelope["status"] == "candidate_not_evidence"

    # HEAD is D here, not the immediate dashboard-only successor, so inference
    # is deliberately rejected instead of searching ancestors.
    inferred_findings = []
    inferred, _ = _resolve_container_and_delivery(
        reader,
        source,
        PROGRAM_ROOT,
        container=None,
        delivery=None,
        findings=inferred_findings,
    )
    assert inferred["container_resolution"] == "unresolved"
    assert {finding.code for finding in inferred_findings} == {
        "DASHBOARD_CONTAINER_MISMATCH"
    }


def test_constrained_head_container_inference(git_builder) -> None:
    git_builder.write_json(DASHBOARD, {"generation_status": "seed"})
    source = git_builder.commit("source S")
    git_builder.write_json(DASHBOARD, {"generation_status": "candidate_not_evidence"})
    container = git_builder.commit("dashboard-only C")
    reader = GitReader(git_builder.root)
    subject, envelope = _resolve_container_and_delivery(
        reader,
        source,
        PROGRAM_ROOT,
        container=None,
        delivery=None,
        findings=[],
    )
    assert subject["container_resolution"] == "inferred_head"
    assert subject["container_commit"] == container
    assert envelope["status"] == "candidate_not_evidence"


def test_delivery_is_validated_only_when_explicit(git_builder) -> None:
    reader, source, container, delivery = _delivery_history(git_builder)
    findings = []
    subject, envelope = _resolve_container_and_delivery(
        reader,
        source,
        PROGRAM_ROOT,
        container=container,
        delivery=delivery,
        findings=findings,
    )
    assert findings == []
    assert subject["delivery_resolution"] == "explicit"
    assert envelope["status"] == "committed_valid"
    assert envelope["evidence_record"]["git_blob"]

    absent, absent_envelope = _resolve_container_and_delivery(
        reader,
        source,
        PROGRAM_ROOT,
        container=container,
        delivery=None,
        findings=[],
    )
    assert absent["delivery_resolution"] == "absent"
    assert absent_envelope["status"] == "candidate_not_evidence"


def test_container_and_delivery_reject_non_allowlisted_diffs(git_builder) -> None:
    reader, source, container, delivery = _delivery_history(git_builder)
    git_builder.write_bytes("extra.txt", b"unexpected\n")
    bad_delivery = git_builder.commit("not delivery-only")
    findings = []
    subject, envelope = _resolve_container_and_delivery(
        reader,
        source,
        PROGRAM_ROOT,
        container=container,
        delivery=bad_delivery,
        findings=findings,
    )
    assert subject["delivery_resolution"] == "unresolved"
    assert envelope["status"] == "failed"
    assert "DASHBOARD_DELIVERY_RELATION_INVALID" in {
        finding.code for finding in findings
    }

    wrong_container_findings = []
    wrong, _ = _resolve_container_and_delivery(
        reader,
        source,
        PROGRAM_ROOT,
        container=delivery,
        delivery=None,
        findings=wrong_container_findings,
    )
    assert wrong["container_resolution"] == "unresolved"
    assert "DASHBOARD_CONTAINER_MISMATCH" in {
        finding.code for finding in wrong_container_findings
    }


def test_text_render_is_concise_and_includes_provenance() -> None:
    report = {
        "verdict": "passed",
        "subject": {
            "source_commit": "a" * 40,
            "source_tree": "b" * 40,
            "program_tree": "c" * 40,
            "container_resolution": "absent",
            "container_commit": None,
            "delivery_resolution": "absent",
            "delivery_commit": None,
            "worktree_clean": True,
        },
        "areas": {
            area: {"status": "not_started", "passed_gates": 0, "required_gates": 1}
            for area in (
                "product_readiness",
                "benchmark_readiness",
                "commercial_readiness",
                "program_health",
            )
        },
        "release_eligible": False,
        "findings": [],
        "next_action": {"action": "EXECUTE_EPP_F01_TASKS"},
    }
    rendered = render_text(copy.deepcopy(report))
    assert "source: " + "a" * 40 in rendered
    assert "container: absent" in rendered
    assert "delivery: absent" in rendered
    assert rendered.endswith("next_action: EXECUTE_EPP_F01_TASKS\n")


def test_text_render_exposes_committed_identity_disposition() -> None:
    report = {
        "verdict": "passed",
        "subject": {
            "source_commit": "a" * 40,
            "source_tree": "b" * 40,
            "program_tree": "c" * 40,
            "container_resolution": "absent",
            "container_commit": None,
            "delivery_resolution": "absent",
            "delivery_commit": None,
            "worktree_clean": True,
        },
        "areas": {
            area: {"status": "not_started", "passed_gates": 0, "required_gates": 1}
            for area in (
                "product_readiness",
                "benchmark_readiness",
                "commercial_readiness",
                "program_health",
            )
        },
        "release_eligible": False,
        "findings": [
            {
                "severity": "info",
                "code": "COMMITTED_IDENTITY_MISMATCH",
                "artifact": f"{PROGRAM_ROOT}/evidence/transitions/TR-0023.json",
                "json_pointer": "/outputs/0/sha256",
                "resolution_status": "resolved",
                "correction_ref": (
                    f"{PROGRAM_ROOT}/evidence/corrections/"
                    "COR-EPP-F01-US1-COMMITTED-IDENTITY-001.json"
                ),
                "recovery": "No rewrite; inspect the approved correction evidence.",
            }
        ],
        "next_action": {"action": "EXECUTE_EPP_F01_TASKS"},
    }
    rendered = render_text(report)
    assert "/outputs/0/sha256" in rendered
    assert "resolved" in rendered
    assert "COR-EPP-F01-US1-COMMITTED-IDENTITY-001.json" in rendered


def test_exact_tr0027_input_origin_correction_recomputes_one_of_one(
    repository_root: Path,
) -> None:
    profile, approvals = _input_origin_inputs(repository_root)
    findings, targets = validate_transition_input_origin_correction(
        GitReader(repository_root),
        "HEAD",
        PROGRAM_ROOT,
        profile,
        approvals,
    )
    mismatch = [
        finding
        for finding in findings
        if finding.code == "TRANSITION_INPUT_ORIGIN_MISMATCH"
    ]
    assert targets == frozenset({INPUT_ORIGIN_TARGET})
    assert len(mismatch) == 1
    assert mismatch[0].severity == "info"
    assert mismatch[0].json_pointer == "/inputs/3"
    assert mismatch[0].resolution_status == "resolved"
    assert mismatch[0].correction_ref == INPUT_ORIGIN_CORRECTION
    assert not {
        "TRANSITION_INPUT_CORRECTION_INVALID",
        "TRANSITION_INPUT_CORRECTION_UNAUTHORIZED",
    } & {finding.code for finding in findings}


@pytest.mark.parametrize(
    "mutation",
    [
        lambda profile, approvals: profile["claim"].__setitem__(
            "json_pointer", "/inputs/2"
        ),
        lambda profile, approvals: profile["claim"].__setitem__(
            "transition_path", f"{PROGRAM_ROOT}/evidence/transitions/TR-0026.json"
        ),
        lambda profile, approvals: profile["claim"].__setitem__(
            "approval_path",
            f"{PROGRAM_ROOT}/evidence/approvals/APR-EPP-F01-MC-003.json",
        ),
        lambda profile, approvals: profile["claim"].__setitem__(
            "declared_source_commit", "0" * 40
        ),
        lambda profile, approvals: profile["claim"].__setitem__(
            "container_commit", "0" * 40
        ),
        lambda profile, approvals: profile["claim"].__setitem__(
            "container_tree", "0" * 40
        ),
        lambda profile, approvals: profile["claim"].__setitem__(
            "transition_git_blob", "0" * 40
        ),
        lambda profile, approvals: profile["claim"].__setitem__(
            "transition_raw_sha256", "0" * 64
        ),
        lambda profile, approvals: profile["claim"].__setitem__(
            "approval_git_blob", "0" * 40
        ),
        lambda profile, approvals: profile["claim"].__setitem__(
            "approval_raw_sha256", "0" * 64
        ),
        lambda profile, approvals: profile.__setitem__("expected_claim_count", 2),
        lambda profile, approvals: profile["forbidden_target_classes"].append(
            "another_target"
        ),
        lambda profile, approvals: profile["unchanged_projection_fields"].append(
            "unapproved_field"
        ),
        lambda profile, approvals: approvals[
            f"{PROGRAM_ROOT}/evidence/approvals/APR-EPP-F01-MC-005.json"
        ].__setitem__("decision", "rejected"),
    ],
)
def test_tr0027_input_origin_correction_fails_closed_for_any_contract_change(
    repository_root: Path, mutation
) -> None:
    profile, approvals = _input_origin_inputs(repository_root)
    mutation(profile, approvals)
    findings, targets = validate_transition_input_origin_correction(
        GitReader(repository_root),
        "HEAD",
        PROGRAM_ROOT,
        profile,
        approvals,
    )
    assert targets == frozenset()
    assert any(finding.severity == "fatal" for finding in findings)
    assert {
        "TRANSITION_INPUT_CORRECTION_INVALID",
        "TRANSITION_INPUT_CORRECTION_UNAUTHORIZED",
    } & {finding.code for finding in findings}


@pytest.mark.parametrize(
    "benchmark_summary",
    [
        {
            "counted": 0,
            "target": 100,
            "first_attempt_passed": 0,
            "eventual_passed": 0,
            "failed": 0,
            "blocked": 0,
            "stale": 0,
            "contaminated": 0,
            "not_tested": 100,
            "t0": 0,
            "t1": 0,
            "t2": 0,
            "t3": 0,
            "coverage_deficits": ["BENCHMARK_COVERAGE_EMPTY"],
            "oracle_deficits": ["BENCHMARK_ORACLES_ABSENT"],
            "artifact_deficits": ["BENCHMARK_ARTIFACTS_ABSENT"],
            "partition_deficits": ["BENCHMARK_PARTITIONS_ABSENT"],
            "freshness_deficits": ["BENCHMARK_EVIDENCE_ABSENT"],
        },
        {
            "counted": 4,
            "target": 100,
            "first_attempt_passed": 1,
            "eventual_passed": 2,
            "failed": 1,
            "blocked": 1,
            "stale": 0,
            "contaminated": 0,
            "not_tested": 96,
            "t0": 2,
            "t1": 1,
            "t2": 1,
            "t3": 0,
            "coverage_deficits": ["COVERAGE_REMAINS"],
            "oracle_deficits": [],
            "artifact_deficits": [],
            "partition_deficits": ["HOLDOUT_REMAINS"],
            "freshness_deficits": [],
        },
    ],
)
def test_input_origin_disposition_cannot_change_protected_projection(
    repository_root: Path,
    monkeypatch: pytest.MonkeyPatch,
    benchmark_summary: dict,
) -> None:
    profile, _ = _input_origin_inputs(repository_root)
    assert profile["unchanged_projection_fields"] == [
        "benchmark_readiness_area",
        "benchmark_summary",
        "benchmark_target_and_counted",
        "benchmark_outcomes_and_tiers",
        "benchmark_coverage_and_qualification",
        "benchmark_oracles_and_artifacts",
        "benchmark_holdout_and_contamination",
        "benchmark_attempts_and_freshness",
        "all_readiness_statuses_and_colors",
        "candidate_identity",
        "approval_authority",
        "release_eligibility",
    ]
    original = validation_module.validate_transition_input_origin_correction
    monkeypatch.setattr(
        validation_module,
        "default_benchmark_summary",
        lambda _source=None: copy.deepcopy(benchmark_summary),
    )

    def run(*, correction_on: bool) -> dict:
        def disposition(*args, **kwargs):
            findings, targets = original(*args, **kwargs)
            if correction_on:
                return findings, targets
            unresolved = [
                replace(
                    finding,
                    severity="fatal",
                    resolution_status="unresolved",
                    correction_ref=None,
                )
                if finding.code == "TRANSITION_INPUT_ORIGIN_MISMATCH"
                else finding
                for finding in findings
            ]
            return unresolved, frozenset()

        monkeypatch.setattr(
            validation_module,
            "validate_transition_input_origin_correction",
            disposition,
        )
        return validate_program(
            GitReader(repository_root),
            "HEAD",
            PROGRAM_ROOT,
            observed_at=datetime(2026, 8, 27, 19, 20, tzinfo=timezone.utc),
        ).report

    def protected(report: dict) -> dict:
        return {
            "areas": report["areas"],
            "benchmark_summary": report["benchmark_summary"],
            "candidate_identity": report["subject"]["release_candidate"],
            "approval_authority": report["release_approval"],
            "release_eligibility": report["release_eligible"],
        }

    assert protected(run(correction_on=True)) == protected(run(correction_on=False))


def test_findings_have_stable_multifault_order_and_exit_precedence() -> None:
    findings = [
        Finding("SEMANTIC_Z", "error", "z.json", "SEMANTIC_Z", (), "c", "r"),
        Finding("SCHEMA_UNSUPPORTED_X", "error", "b.json", "SCHEMA_X", (), "c", "r"),
        Finding("JSON_INVALID", "fatal", "a.json", "JSON_VALID", (), "c", "r"),
    ]
    assert [item.code for item in sorted(findings, key=Finding.sort_key)] == [
        "JSON_INVALID",
        "SCHEMA_UNSUPPORTED_X",
        "SEMANTIC_Z",
    ]
    # Structural/schema failures take precedence over semantic failures.
    structural = [item for item in findings if item.code.startswith(("JSON_", "SCHEMA_"))]
    assert structural


def test_unknown_exception_is_bounded_and_does_not_disclose_canary(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    canary = "token=" + "do-not-print"

    def fail(*args, **kwargs):
        raise RuntimeError(canary)

    monkeypatch.setattr("program_control.cli.GitReader.discover", fail)
    assert main(["validate", "--source", "HEAD"]) == EXIT_INTERNAL
    captured = capsys.readouterr()
    assert "INTERNAL_VALIDATION_FAILURE" in captured.err
    assert canary not in captured.out + captured.err


def test_bounded_failure_uses_cataloged_code_and_recovery(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert _bounded_failure("not a code", "text", EXIT_SCHEMA) == EXIT_SCHEMA
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "INTERNAL_VALIDATION_FAILURE" in captured.err
    assert len(captured.err) < 220


def test_generate_delivery_update_preserves_full_validation_envelope() -> None:
    report = {
        "delivery": {
            "mode": "validate",
            "status": "not_requested",
            "target_changed": False,
            "prior_snapshot_preserved": True,
            "container_resolution": "absent",
            "container_commit": None,
            "delivery_resolution": "absent",
            "delivery_commit": None,
            "evidence_record": None,
        }
    }
    _set_delivery(
        report,
        status="candidate_not_evidence",
        target_changed=True,
        prior_snapshot_preserved=False,
    )
    assert report["delivery"] == {
        "mode": "generate_dashboard",
        "status": "candidate_not_evidence",
        "target_changed": True,
        "prior_snapshot_preserved": False,
        "container_resolution": "absent",
        "container_commit": None,
        "delivery_resolution": "absent",
        "delivery_commit": None,
        "evidence_record": None,
    }


def test_json_and_text_render_share_stable_finding_order(
    capsys: pytest.CaptureFixture[str],
) -> None:
    report = {
        "verdict": "failed",
        "subject": {
            "source_commit": None,
            "source_tree": None,
            "program_tree": None,
            "container_commit": None,
            "container_resolution": "unresolved",
            "delivery_commit": None,
            "delivery_resolution": "unresolved",
            "worktree_clean": True,
        },
        "areas": {
            name: {"status": "blocked", "passed_gates": 0, "required_gates": 1}
            for name in (
                "product_readiness",
                "benchmark_readiness",
                "commercial_readiness",
                "program_health",
            )
        },
        "release_eligible": False,
        "findings": [
            {
                "severity": "error",
                "code": "SECOND_FAILURE",
                "artifact": "docs/second.json",
                "json_pointer": "/x",
                "resolution_status": "unresolved",
                "correction_ref": None,
                "recovery": "Repair second.",
                "invariant": "SECOND_INVARIANT",
                "evidence": [],
                "consequence": "Second failed.",
            },
            {
                "severity": "fatal",
                "code": "FIRST_FAILURE",
                "artifact": "docs/first.json",
                "json_pointer": "/x",
                "resolution_status": "unresolved",
                "correction_ref": None,
                "recovery": "Repair first.",
                "invariant": "FIRST_INVARIANT",
                "evidence": [],
                "consequence": "First failed.",
            },
        ],
        "next_action": None,
    }
    report["findings"] = sorted(
        report["findings"],
        key=lambda item: (0 if item["severity"] == "fatal" else 1, item["code"]),
    )
    _emit(report, "text")
    text_output = capsys.readouterr().out
    _emit(report, "json")
    json_output = capsys.readouterr().out
    assert text_output.index("FIRST_FAILURE") < text_output.index("SECOND_FAILURE")
    assert json_output.index("FIRST_FAILURE") < json_output.index("SECOND_FAILURE")
