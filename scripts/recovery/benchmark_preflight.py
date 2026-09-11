#!/usr/bin/env python3
"""Fail-closed preflight for governed engineering benchmark qualification.

This script never generates, executes, or counts a benchmark case. It reports
whether the human decisions, roadmap dependencies, schemas, and current coverage
state permit those later actions.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[2]
PROGRAM = Path("docs/programs/engineering-process-platform")
DECISIONS = PROGRAM / "decision-register.json"
ROADMAP = PROGRAM / "roadmap.json"
COVERAGE = PROGRAM / "benchmark-coverage.json"
SCHEMAS = (
    PROGRAM / "schemas/benchmark-case.schema.json",
    PROGRAM / "schemas/oracle-manifest.schema.json",
    PROGRAM / "schemas/benchmark-evidence.schema.json",
)
BENCHMARK_FEATURES = ("EPP-B01", "EPP-B02")


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _decision_findings(
    root: Path, decision_register: dict[str, Any], required: set[str]
) -> dict[str, str]:
    records = {record["id"]: record for record in decision_register["records"]}
    findings: dict[str, str] = {}
    for decision_id in sorted(required):
        record = records.get(decision_id)
        if record is None:
            findings[decision_id] = "missing"
            continue
        if record.get("status") != "decided":
            findings[decision_id] = str(record.get("status") or "status_missing")
            continue
        decision_record = record.get("decision_record")
        if not decision_record:
            findings[decision_id] = "decided_without_decision_record"
            continue
        if not (root / PROGRAM / decision_record).is_file():
            findings[decision_id] = "decision_record_missing"
    return findings


def _schema_findings(root: Path) -> dict[str, str]:
    findings: dict[str, str] = {}
    for relative in SCHEMAS:
        try:
            Draft202012Validator.check_schema(_read(root / relative))
        except Exception as error:  # pragma: no cover - exact library text is unstable
            findings[relative.name] = type(error).__name__
    return findings


def audit_benchmark_readiness(
    root: Path = ROOT,
    *,
    decisions: dict[str, Any] | None = None,
    roadmap: dict[str, Any] | None = None,
    coverage: dict[str, Any] | None = None,
) -> dict[str, Any]:
    decision_register = decisions or _read(root / DECISIONS)
    roadmap_document = roadmap or _read(root / ROADMAP)
    coverage_document = coverage or _read(root / COVERAGE)
    items = {item["id"]: item for item in roadmap_document["items"]}

    required_decisions = {
        decision_id
        for feature_id in BENCHMARK_FEATURES
        for decision_id in items[feature_id]["blocking_decisions"]
    }
    decision_findings = _decision_findings(
        root, decision_register, required_decisions
    )

    benchmark_features = set(BENCHMARK_FEATURES)
    blocking_dependencies = sorted(
        {
            dependency
            for feature_id in BENCHMARK_FEATURES
            for dependency in items[feature_id]["depends_on"]
            if dependency in benchmark_features
            or items.get(dependency, {}).get("status") != "complete"
        }
    )
    schema_findings = _schema_findings(root)

    current = coverage_document["current_status"]
    target = int(coverage_document["total_target"])
    counted = int(current["counted"])
    case_root = root / "benchmarks" / "cases"
    case_count = len(tuple(case_root.rglob("PROC-*.json"))) if case_root.is_dir() else 0

    violations: list[str] = []
    if counted + int(current["not_tested"]) != target:
        violations.append("BENCHMARK_DENOMINATOR_MISMATCH")
    if counted > case_count:
        violations.append("BENCHMARK_COUNT_EXCEEDS_CASE_MANIFESTS")
    if counted and (decision_findings or blocking_dependencies):
        violations.append("BENCHMARK_COUNT_WITH_BLOCKED_PRECONDITIONS")
    if schema_findings:
        violations.append("BENCHMARK_SCHEMA_INVALID")

    policy_blockers = []
    if coverage_document.get("policy_status") != "approved":
        policy_blockers.append("benchmark_coverage_policy_not_approved")
    if coverage_document["release_threshold_proposal"].get("status") != "approved":
        policy_blockers.append("release_threshold_policy_not_approved")

    safe_to_generate = not (
        decision_findings or blocking_dependencies or policy_blockers or violations
    )
    status = "FAIL" if violations else "PASS" if safe_to_generate else "BLOCKED"
    return {
        "status": status,
        "score": f"{counted}/{target}",
        "case_count": case_count,
        "safe_to_generate_cases": safe_to_generate,
        "safe_to_count_cases": safe_to_generate,
        "blocking_decisions": sorted(decision_findings),
        "decision_findings": decision_findings,
        "blocking_dependencies": blocking_dependencies,
        "policy_blockers": policy_blockers,
        "schema_findings": schema_findings,
        "violations": violations,
        "next_action": (
            "Obtain the named human decisions and complete roadmap dependencies; "
            "then rerun this preflight before generating or executing any case."
            if status == "BLOCKED"
            else "Repair benchmark state before any generation or execution."
            if status == "FAIL"
            else "Case generation may proceed under the approved policies."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit_benchmark_readiness(ROOT)
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        destination = args.output if args.output.is_absolute() else ROOT / args.output
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 1 if result["status"] == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
