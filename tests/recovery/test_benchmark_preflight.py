from __future__ import annotations

import copy
import json
from pathlib import Path

from scripts.recovery.benchmark_preflight import audit_benchmark_readiness


ROOT = Path(__file__).parents[2]


def _read(relative: str):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def test_current_benchmark_preflight_fails_closed_at_zero_of_100() -> None:
    result = audit_benchmark_readiness(ROOT)

    assert result["status"] == "BLOCKED"
    assert result["score"] == "0/100"
    assert result["safe_to_generate_cases"] is False
    assert result["safe_to_count_cases"] is False
    assert result["case_count"] == 0
    assert set(result["blocking_decisions"]) == {
        "DEC-P0-007",
        "DEC-P0-009",
        "DEC-P0-010",
        "DEC-P0-011",
        "DEC-P0-012",
    }
    assert set(result["blocking_dependencies"]) == {
        "EPP-F03",
        "EPP-F05",
        "EPP-F06",
        "EPP-B01",
    }
    assert result["violations"] == []


def test_nonzero_count_while_preconditions_are_blocked_is_a_violation() -> None:
    coverage = copy.deepcopy(
        _read("docs/programs/engineering-process-platform/benchmark-coverage.json")
    )
    coverage["current_status"]["counted"] = 1
    coverage["current_status"]["not_tested"] = 99

    result = audit_benchmark_readiness(
        ROOT,
        decisions=_read(
            "docs/programs/engineering-process-platform/decision-register.json"
        ),
        roadmap=_read("docs/programs/engineering-process-platform/roadmap.json"),
        coverage=coverage,
    )

    assert result["status"] == "FAIL"
    assert result["score"] == "1/100"
    assert "BENCHMARK_COUNT_WITH_BLOCKED_PRECONDITIONS" in result["violations"]


def test_decided_record_without_digest_bound_decision_artifact_remains_blocking() -> None:
    decisions = _read(
        "docs/programs/engineering-process-platform/decision-register.json"
    )
    threshold = next(
        record for record in decisions["records"] if record["id"] == "DEC-P0-011"
    )
    assert threshold["status"] == "decided"
    assert threshold["decision_record"] is None

    result = audit_benchmark_readiness(
        ROOT,
        decisions=decisions,
        roadmap=_read("docs/programs/engineering-process-platform/roadmap.json"),
        coverage=_read(
            "docs/programs/engineering-process-platform/benchmark-coverage.json"
        ),
    )

    assert "DEC-P0-011" in result["blocking_decisions"]
    assert result["decision_findings"]["DEC-P0-011"] == (
        "decided_without_decision_record"
    )
