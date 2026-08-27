"""Gate catalog, evidence completeness, and independent readiness projection."""

from __future__ import annotations

import copy
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from program_control.dashboard import (
    DashboardError,
    default_benchmark_summary,
    derive_areas,
    derive_benchmark_summary,
)


OBSERVED = datetime(2026, 8, 27, 12, 0, tzinfo=timezone.utc)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture
def catalog(repository_root: Path) -> dict:
    return load(
        repository_root / "docs/programs/engineering-process-platform/gate-catalog.json"
    )


@pytest.fixture
def evidence(repository_root: Path) -> dict:
    return load(
        repository_root
        / "docs/programs/engineering-process-platform/gate-evidence.json"
    )


def test_catalog_has_exact_four_areas_and_34_unique_required_gates(
    catalog: dict,
) -> None:
    ids = [gate["id"] for gate in catalog["gates"]]
    assert catalog["area_order"] == [
        "product_readiness",
        "benchmark_readiness",
        "commercial_readiness",
        "program_health",
    ]
    assert len(ids) == len(set(ids)) == 34
    assert all(gate["required"] for gate in catalog["gates"])


def test_honest_initial_evidence_projects_four_independent_nonpassing_areas(
    catalog: dict, evidence: dict
) -> None:
    areas = derive_areas(catalog, evidence, OBSERVED)
    assert areas["product_readiness"]["status"] == "not_started"
    assert areas["benchmark_readiness"]["status"] == "not_started"
    assert areas["commercial_readiness"]["status"] == "blocked"
    assert areas["program_health"]["status"] == "in_progress"
    assert sum(area["required_gates"] for area in areas.values()) == 34
    assert sum(area["passed_gates"] for area in areas.values()) == 0
    assert [row["id"] for area in areas.values() for row in area["gates"]] == [
        gate["id"] for gate in catalog["gates"]
    ]
    assert all(
        area["passed_gates"] <= area["required_gates"] for area in areas.values()
    )


@pytest.mark.parametrize(
    ("mutation", "expected"),
    [
        (
            lambda c, e: e["assertions"].append(copy.deepcopy(e["assertions"][0])),
            "GATE_EVIDENCE_DUPLICATE",
        ),
        (
            lambda c, e: e["assertions"][0].__setitem__("evaluator", "WRONG_EVALUATOR"),
            "GATE_EVALUATOR_MISMATCH",
        ),
        (
            lambda c, e: e["assertions"][0].__setitem__("assertion_results", []),
            "GATE_ASSERTION_SET_MISMATCH",
        ),
        (
            lambda c, e: e["assertions"][0]["assertion_results"][0].__setitem__(
                "assertion_id", "PROD-01-A99"
            ),
            "GATE_ASSERTION_SET_MISMATCH",
        ),
        (
            lambda c, e: e["assertions"][0].__setitem__("status", "passed"),
            "GATE_AGGREGATE_MISMATCH",
        ),
    ],
)
def test_catalog_evidence_contract_rejects_incomplete_or_hand_set_rows(
    catalog: dict, evidence: dict, mutation, expected: str
) -> None:
    mutation(catalog, evidence)
    with pytest.raises(DashboardError) as caught:
        derive_areas(catalog, evidence, OBSERVED)
    assert caught.value.code == expected


@pytest.mark.parametrize(
    ("mutation", "expected"),
    [
        (
            lambda c, e: c["gates"].append(copy.deepcopy(c["gates"][0])),
            "GATE_ID_DUPLICATE",
        ),
        (
            lambda c, e: c["evidence_classes"].append(
                copy.deepcopy(c["evidence_classes"][0])
            ),
            "EVIDENCE_CLASS_DUPLICATE",
        ),
        (lambda c, e: e["assertions"].pop(), "GATE_EVIDENCE_SET_MISMATCH"),
    ],
)
def test_closed_catalog_rejects_duplicate_or_incomplete_membership(
    catalog: dict, evidence: dict, mutation, expected: str
) -> None:
    mutation(catalog, evidence)
    with pytest.raises(DashboardError) as caught:
        derive_areas(catalog, evidence, OBSERVED)
    assert caught.value.code == expected


def make_first_gate_pass(catalog: dict, evidence: dict) -> list[dict]:
    gate = catalog["gates"][0]
    row = evidence["assertions"][0]
    registry = {item["class_id"]: item for item in catalog["evidence_classes"]}
    artifacts = []
    manifest = []
    for index, class_id in enumerate(
        gate["evidence_policy"]["required_classes"], start=1
    ):
        binding = registry[class_id]
        artifact = {
            "path": f"evidence/verification/prod-01-{index}.json",
            "sha256": str(index) * 64,
            "evidence_class": class_id,
            "schema_id": binding["schema_id"],
            "source_role": binding["source_role"],
        }
        artifacts.append(artifact)
        manifest.append(
            {
                "path": artifact["path"],
                "sha256": artifact["sha256"],
                "git_blob": str(index) * 40,
                "schema_id": artifact["schema_id"],
                "role": artifact["source_role"],
            }
        )
    verifier = {
        "identity": "independent fixture",
        "role": "verifier",
        "independent": True,
    }
    row.update(
        {
            "status": "passed",
            "classification": "supporting",
            "reason_code": "PROVEN",
            "fresh": True,
            "expires_at": "2026-08-28T12:00:00Z",
            "verifier": verifier,
            "evidence": artifacts,
        }
    )
    for result in row["assertion_results"]:
        result.update(
            {
                "status": "passed",
                "classification": "supporting",
                "reason_code": "PROVEN",
                "fresh": True,
                "expires_at": "2026-08-28T12:00:00Z",
                "verifier": verifier,
                "evidence": copy.deepcopy(artifacts),
            }
        )
    return manifest


def test_one_product_gate_pass_cannot_change_other_areas(
    catalog: dict, evidence: dict
) -> None:
    manifest = make_first_gate_pass(catalog, evidence)
    before = derive_areas(catalog, load_initial(evidence), OBSERVED)
    after = derive_areas(
        catalog,
        evidence,
        OBSERVED,
        source_manifest=manifest,
        candidate=evidence["subject"],
    )
    assert after["product_readiness"]["passed_gates"] == 1
    for area in ("benchmark_readiness", "commercial_readiness", "program_health"):
        assert after[area] == before[area]


def load_initial(evidence: dict) -> dict:
    value = copy.deepcopy(evidence)
    row = value["assertions"][0]
    row.update(
        {
            "status": "not_started",
            "classification": "not_tested",
            "reason_code": "PRODUCT_EVIDENCE_NOT_RECORDED",
            "fresh": False,
            "expires_at": None,
            "evidence": [],
        }
    )
    for result in row["assertion_results"]:
        result.update(
            {
                "status": "not_started",
                "classification": "not_tested",
                "reason_code": "PRODUCT_EVIDENCE_NOT_RECORDED",
                "fresh": False,
                "expires_at": None,
                "evidence": [],
            }
        )
    return value


@pytest.mark.parametrize(
    ("mutation", "expected"),
    [
        (
            lambda c, e, m: e["assertions"][0].__setitem__("evidence", []),
            "GATE_PASS_EVIDENCE_EMPTY",
        ),
        (
            lambda c, e, m: e["assertions"][0]["evidence"][0].__setitem__(
                "evidence_class", "UNKNOWN_CLASS"
            ),
            "EVIDENCE_CLASS_UNKNOWN",
        ),
        (
            lambda c, e, m: e["assertions"][0]["evidence"][0].__setitem__(
                "schema_id", "wrong"
            ),
            "EVIDENCE_CLASS_BINDING_MISMATCH",
        ),
        (
            lambda c, e, m: m[0].__setitem__("sha256", "f" * 64),
            "EVIDENCE_SOURCE_MISMATCH",
        ),
        (
            lambda c, e, m: e["assertions"][0]["evidence"].pop(),
            "EVIDENCE_CLASS_COVERAGE_MISSING",
        ),
        (
            lambda c, e, m: e["assertions"][0]["verifier"].__setitem__(
                "independent", False
            ),
            "GATE_INDEPENDENCE_MISSING",
        ),
        (
            lambda c, e, m: e["assertions"][0].__setitem__(
                "expires_at", "2026-08-27T11:59:59Z"
            ),
            "GATE_FRESHNESS_MISMATCH",
        ),
        (
            lambda c, e, m: e["assertions"][0]["assertion_results"][0].__setitem__(
                "classification", "not_tested"
            ),
            "GATE_PASS_CLASSIFICATION_INVALID",
        ),
        (
            lambda c, e, m: e["assertions"][0]["assertion_results"][0].__setitem__(
                "evidence", []
            ),
            "GATE_PASS_EVIDENCE_EMPTY",
        ),
    ],
)
def test_passing_gate_rejects_unbound_incomplete_or_stale_evidence(
    catalog: dict, evidence: dict, mutation, expected: str
) -> None:
    manifest = make_first_gate_pass(catalog, evidence)
    catalog["gates"][0]["evidence_policy"]["independent_verifier_required"] = True
    mutation(catalog, evidence, manifest)
    with pytest.raises(DashboardError) as caught:
        derive_areas(
            catalog,
            evidence,
            OBSERVED,
            source_manifest=manifest,
            candidate=evidence["subject"],
        )
    assert caught.value.code == expected


def test_exact_candidate_mismatch_fails(catalog: dict, evidence: dict) -> None:
    manifest = make_first_gate_pass(catalog, evidence)
    candidate = copy.deepcopy(evidence["subject"])
    candidate["git_tree"] = "f" * 40
    with pytest.raises(DashboardError) as caught:
        derive_areas(
            catalog, evidence, OBSERVED, source_manifest=manifest, candidate=candidate
        )
    assert caught.value.code == "GATE_CANDIDATE_MISMATCH"


def test_catalog_digest_and_shared_freshness_policy_are_enforced(
    catalog: dict, evidence: dict
) -> None:
    with pytest.raises(DashboardError) as caught:
        derive_areas(
            catalog,
            evidence,
            OBSERVED,
            catalog_digest="f" * 64,
        )
    assert caught.value.code == "GATE_CATALOG_DIGEST_MISMATCH"

    evidence["assertions"][0]["assertion_results"][0]["stale_triggers"] = [
        "candidate_changed"
    ]
    with pytest.raises(DashboardError) as caught:
        derive_areas(catalog, evidence, OBSERVED)
    assert caught.value.code == "GATE_FRESHNESS_POLICY_INVALID"


def test_gate_aggregate_metadata_and_evidence_union_are_derived(
    catalog: dict, evidence: dict
) -> None:
    evidence["assertions"][0]["reason_code"] = "HAND_SET_REASON"
    with pytest.raises(DashboardError) as caught:
        derive_areas(catalog, evidence, OBSERVED)
    assert caught.value.code == "GATE_AGGREGATE_METADATA_MISMATCH"

    evidence["assertions"][0]["reason_code"] = "PRODUCT_EVIDENCE_NOT_RECORDED"
    evidence["assertions"][0]["evidence"] = [
        {
            "path": "evidence/verification/not-derived.json",
            "sha256": "a" * 64,
            "evidence_class": catalog["evidence_classes"][0]["class_id"],
            "schema_id": catalog["evidence_classes"][0]["schema_id"],
            "source_role": catalog["evidence_classes"][0]["source_role"],
        }
    ]
    with pytest.raises(DashboardError) as caught:
        derive_areas(catalog, evidence, OBSERVED)
    assert caught.value.code == "GATE_EVIDENCE_UNION_MISMATCH"


def _case(number: int, *, partition: str, tiers: list[str]) -> dict:
    return {
        "process_id": f"PROC-{number:03d}",
        "equivalence_family": f"family-{number:03d}",
        "status": "current",
        "partition": partition,
        "oracle_refs": [{"oracle_id": f"ORC-{number:03d}"}],
        "profiles": [{"tier": tier} for tier in tiers],
    }


def _run(number: int, terminal: str, *, hours_old: int = 0) -> dict:
    observed = datetime(2026, 8, 27, 12 - hours_old, tzinfo=timezone.utc)
    return {
        "process_id": f"PROC-{number:03d}",
        "attempt": {
            "attempt_id": f"ATT-{number:03d}-1",
            "ordinal": 1,
            "first_attempt": True,
            "prior_attempt": None,
        },
        "qualification_transition": {"to": "current"},
        "terminal_classification": terminal,
        "observed_at": observed.isoformat().replace("+00:00", "Z"),
        "maximum_age_hours": 1,
        "required_output_coverage": {"complete": True},
        "artifacts": [{"parse_open_result": "passed"}],
    }


def test_empty_benchmark_is_honest_zero_of_one_hundred() -> None:
    summary = derive_benchmark_summary([], [], OBSERVED)
    assert summary == default_benchmark_summary()
    assert summary["counted"] == 0
    assert summary["target"] == summary["not_tested"] == 100
    assert (
        sum(
            summary[key]
            for key in (
                "eventual_passed",
                "failed",
                "blocked",
                "stale",
                "contaminated",
                "not_tested",
            )
        )
        == 100
    )
    assert all(
        summary[key]
        for key in (
            "coverage_deficits",
            "oracle_deficits",
            "artifact_deficits",
            "partition_deficits",
            "freshness_deficits",
        )
    )


def test_benchmark_population_outcomes_tiers_and_deficits_are_derived() -> None:
    cases = [
        _case(1, partition="development", tiers=["T0", "T1", "T2"]),
        _case(2, partition="frozen_qualification", tiers=["T0", "T1", "T3"]),
        _case(3, partition="blind_holdout", tiers=["T0"]),
    ]
    records = [_run(1, "passed"), _run(2, "failed_product")]
    summary = derive_benchmark_summary(cases, records, OBSERVED)
    assert (summary["counted"], summary["eventual_passed"]) == (3, 1)
    assert (summary["first_attempt_passed"], summary["failed"]) == (1, 1)
    assert summary["not_tested"] == 98
    assert (summary["t0"], summary["t1"], summary["t2"], summary["t3"]) == (
        3,
        2,
        1,
        1,
    )
    assert summary["oracle_deficits"] == []
    assert summary["artifact_deficits"] == []
    assert summary["partition_deficits"] == []
    assert summary["freshness_deficits"] == []
    assert summary["coverage_deficits"] == ["BENCHMARK_COVERAGE_INCOMPLETE"]


@pytest.mark.parametrize(
    ("mutation", "expected"),
    [
        (
            lambda cases, records: cases[0].__setitem__(
                "profiles", [{"tier": "T0"}, {"tier": "T2"}]
            ),
            "BENCHMARK_TIER_DEPENDENCY_INVALID",
        ),
        (
            lambda cases, records: records[0]["attempt"].__setitem__("ordinal", 2),
            "BENCHMARK_ATTEMPT_HISTORY_INVALID",
        ),
        (
            lambda cases, records: cases[1].__setitem__(
                "equivalence_family", cases[0]["equivalence_family"]
            ),
            "BENCHMARK_DISTINCTNESS_INVALID",
        ),
    ],
)
def test_benchmark_invalid_tier_attempt_and_distinctness_fail_closed(
    mutation, expected: str
) -> None:
    cases = [
        _case(1, partition="development", tiers=["T0", "T1"]),
        _case(2, partition="blind_holdout", tiers=["T0", "T1"]),
    ]
    records = [_run(1, "passed")]
    mutation(cases, records)
    with pytest.raises(DashboardError) as caught:
        derive_benchmark_summary(cases, records, OBSERVED)
    assert caught.value.code == expected


def test_hand_set_benchmark_summary_is_never_authoritative() -> None:
    with pytest.raises(DashboardError) as caught:
        default_benchmark_summary({"counted": 100, "eventual_passed": 100})
    assert caught.value.code == "BENCHMARK_SUMMARY_HAND_SET"
