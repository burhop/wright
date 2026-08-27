"""US1 CLI parsing, source/container/delivery resolution, and rendering tests."""

from __future__ import annotations

import copy
from hashlib import sha256

from program_control.cli import build_parser, render_text
from program_control.git_subject import GitReader
from program_control.validation import _resolve_container_and_delivery


PROGRAM_ROOT = "docs/programs/engineering-process-platform"
DASHBOARD = f"{PROGRAM_ROOT}/dashboard.json"
DELIVERY = f"{PROGRAM_ROOT}/evidence/verification/EPP-F01-dashboard-delivery.json"


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
