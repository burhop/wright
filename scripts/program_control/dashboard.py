"""Gate projection and transactional dashboard delivery."""

from __future__ import annotations

import os
import tempfile
from collections.abc import Callable, Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .json_contracts import deterministic_json_bytes, strict_loads, validate_schema


AREA_ORDER = (
    "product_readiness",
    "benchmark_readiness",
    "commercial_readiness",
    "program_health",
)
NONPASSING_PRECEDENCE = (
    "failed",
    "blocked",
    "stale",
    "in_progress",
    "not_started",
)


class DashboardError(ValueError):
    """A bounded dashboard derivation or delivery failure."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def _parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _effective_status(assertion: Mapping[str, Any], observed_at: datetime) -> str:
    status = str(assertion.get("status", "not_started"))
    if status == "passed" and assertion.get("classification") != "supporting":
        return "blocked"
    expires_at = assertion.get("expires_at")
    if expires_at is not None and _parse_time(str(expires_at)) < observed_at:
        return "stale"
    return status


def derive_areas(
    catalog: Mapping[str, Any],
    evidence_set: Mapping[str, Any],
    observed_at: datetime,
    *,
    source_manifest: list[Mapping[str, Any]] | None = None,
    candidate: Mapping[str, Any] | None = None,
) -> dict[str, dict[str, Any]]:
    """Derive four independent readiness areas from catalog membership and evidence."""

    if list(catalog.get("area_order", [])) != list(AREA_ORDER):
        raise DashboardError("GATE_AREA_ORDER_INVALID")
    gates = list(catalog.get("gates", []))
    gate_ids = [gate.get("id") for gate in gates]
    if len(gate_ids) != len(set(gate_ids)):
        raise DashboardError("GATE_ID_DUPLICATE")
    registry_rows = list(catalog.get("evidence_classes", []))
    registry_ids = [row.get("class_id") for row in registry_rows]
    if len(registry_ids) != len(set(registry_ids)):
        raise DashboardError("EVIDENCE_CLASS_DUPLICATE")
    registry = {str(row["class_id"]): row for row in registry_rows if "class_id" in row}
    assertions = list(evidence_set.get("assertions", []))
    assertion_ids = [row.get("gate_id") for row in assertions]
    if len(assertion_ids) != len(set(assertion_ids)):
        raise DashboardError("GATE_EVIDENCE_DUPLICATE")
    if set(assertion_ids) != set(gate_ids) or len(assertion_ids) != len(gate_ids):
        raise DashboardError("GATE_EVIDENCE_SET_MISMATCH")
    if candidate is not None and evidence_set.get("subject") != candidate:
        raise DashboardError("GATE_CANDIDATE_MISMATCH")
    assertion_by_id = {str(row["gate_id"]): row for row in assertions if "gate_id" in row}
    manifest_by_path = {
        str(row.get("path")): row for row in (source_manifest or []) if isinstance(row, Mapping)
    }

    def validate_artifacts(
        artifacts: list[Mapping[str, Any]],
        *,
        passing: bool,
    ) -> set[str]:
        classes: set[str] = set()
        for artifact in artifacts:
            class_id = str(artifact.get("evidence_class", ""))
            binding = registry.get(class_id)
            if binding is None:
                raise DashboardError("EVIDENCE_CLASS_UNKNOWN")
            if (
                artifact.get("schema_id") != binding.get("schema_id")
                or artifact.get("source_role") != binding.get("source_role")
            ):
                raise DashboardError("EVIDENCE_CLASS_BINDING_MISMATCH")
            classes.add(class_id)
            if passing:
                source = manifest_by_path.get(str(artifact.get("path")))
                if source is None or (
                    source.get("sha256") != artifact.get("sha256")
                    or source.get("schema_id") != artifact.get("schema_id")
                    or source.get("role") != artifact.get("source_role")
                ):
                    raise DashboardError("EVIDENCE_SOURCE_MISMATCH")
        return classes

    def result_status(result: Mapping[str, Any]) -> str:
        status = str(result.get("status", "not_started"))
        expires_at = result.get("expires_at")
        expired = expires_at is not None and _parse_time(str(expires_at)) < observed_at
        if status == "passed":
            if result.get("classification") != "supporting":
                raise DashboardError("GATE_PASS_CLASSIFICATION_INVALID")
            if result.get("fresh") is not True or expired:
                raise DashboardError("GATE_FRESHNESS_MISMATCH")
            if not result.get("evidence"):
                raise DashboardError("GATE_PASS_EVIDENCE_EMPTY")
        return "stale" if expired else status

    def aggregate_status(statuses: list[str]) -> str:
        if statuses and all(status == "passed" for status in statuses):
            return "passed"
        return next(
            (status for status in NONPASSING_PRECEDENCE if status in statuses),
            "not_started",
        )

    areas: dict[str, dict[str, Any]] = {}
    for area in AREA_ORDER:
        required = [gate for gate in gates if gate.get("area") == area and gate.get("required")]
        rows: list[dict[str, Any]] = []
        for gate in required:
            gate_id = str(gate["id"])
            assertion = assertion_by_id.get(gate_id)
            if assertion is None:
                raise DashboardError("GATE_EVIDENCE_SET_MISMATCH")
            if assertion.get("evaluator") != gate.get("evaluator"):
                raise DashboardError("GATE_EVALUATOR_MISMATCH")
            results = list(assertion.get("assertion_results", []))
            expected_result_ids = [row.get("assertion_id") for row in gate.get("assertions", [])]
            actual_result_ids = [row.get("assertion_id") for row in results]
            if (
                len(actual_result_ids) != len(set(actual_result_ids))
                or set(actual_result_ids) != set(expected_result_ids)
                or len(actual_result_ids) != len(expected_result_ids)
            ):
                raise DashboardError("GATE_ASSERTION_SET_MISMATCH")
            statuses = [result_status(result) for result in results]
            status = aggregate_status(statuses)
            if assertion.get("status") != status:
                raise DashboardError("GATE_AGGREGATE_MISMATCH")
            row_expires = assertion.get("expires_at")
            row_expired = row_expires is not None and _parse_time(str(row_expires)) < observed_at
            derived_fresh = bool(results) and all(
                result.get("fresh") is True
                and not (
                    result.get("expires_at") is not None
                    and _parse_time(str(result.get("expires_at"))) < observed_at
                )
                for result in results
            )
            if row_expired or bool(assertion.get("fresh")) != derived_fresh:
                raise DashboardError("GATE_FRESHNESS_MISMATCH")
            passing = status == "passed"
            row_artifacts = [item for item in assertion.get("evidence", []) if isinstance(item, Mapping)]
            if passing and not row_artifacts:
                raise DashboardError("GATE_PASS_EVIDENCE_EMPTY")
            row_classes = validate_artifacts(row_artifacts, passing=passing)
            result_artifacts = [
                item
                for result in results
                for item in result.get("evidence", [])
                if isinstance(item, Mapping)
            ]
            validate_artifacts(result_artifacts, passing=passing)
            required_classes = set(gate.get("evidence_policy", {}).get("required_classes", []))
            if passing and not required_classes.issubset(row_classes):
                raise DashboardError("EVIDENCE_CLASS_COVERAGE_MISSING")
            independent_required = bool(
                gate.get("evidence_policy", {}).get("independent_verifier_required")
            )
            if passing and independent_required:
                if assertion.get("verifier", {}).get("independent") is not True or any(
                    result.get("verifier", {}).get("independent") is not True for result in results
                ):
                    raise DashboardError("GATE_INDEPENDENCE_MISSING")
            rows.append(
                {
                    "id": gate_id,
                    "status": status,
                    "classification": assertion["classification"],
                    "reason_code": assertion["reason_code"],
                    "fresh": derived_fresh,
                    "evidence": [
                        {
                            "path": item["path"],
                            "sha256": item["sha256"],
                            "git_blob": manifest_by_path.get(str(item["path"]), {}).get(
                                "git_blob", "0" * 40
                            ),
                        }
                        for item in row_artifacts
                    ],
                }
            )
        statuses = [row["status"] for row in rows]
        passed = sum(status == "passed" for status in statuses)
        if rows and passed == len(rows):
            area_status = "passed"
        else:
            area_status = next(
                (candidate for candidate in NONPASSING_PRECEDENCE if candidate in statuses),
                "not_started",
            )
        blockers = sorted(
            {
                str(row["reason_code"])
                for row in rows
                if row["status"] != "passed"
            }
        )
        evidence = sorted(
            (item for row in rows for item in row["evidence"]),
            key=lambda item: (item["path"], item["sha256"]),
        )
        areas[area] = {
            "status": area_status,
            "passed_gates": passed,
            "required_gates": len(rows),
            "gates": rows,
            "blockers": blockers,
            "evidence": evidence,
            "fresh": bool(rows) and all(row["fresh"] for row in rows),
            "last_success_at": evidence_set.get("last_success", {}).get(area)
            if area_status == "passed"
            else None,
        }
    return areas


def default_benchmark_summary(source: Mapping[str, Any] | None = None) -> dict[str, Any]:
    existing = dict(source or {})
    counters = {
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
    }
    counters.update({key: existing[key] for key in counters if key in existing})
    for name, fallback in (
        ("coverage_deficits", ["BENCHMARK_COVERAGE_EMPTY"]),
        ("oracle_deficits", ["BENCHMARK_ORACLES_ABSENT"]),
        ("artifact_deficits", ["BENCHMARK_ARTIFACTS_ABSENT"]),
        ("partition_deficits", ["BENCHMARK_PARTITIONS_ABSENT"]),
        ("freshness_deficits", ["BENCHMARK_EVIDENCE_ABSENT"]),
    ):
        counters[name] = list(existing.get(name, fallback))
    return counters


def make_dashboard(report: Mapping[str, Any]) -> dict[str, Any]:
    subject = report["subject"]
    return {
        "$schema": "./schemas/dashboard.schema.json",
        "schema_version": "2.0",
        "program_id": "EPP-2026",
        "generation_status": "candidate_not_evidence",
        "generated_at": report["observed_at"],
        "data_cutoff": report["observed_at"],
        "source": {
            "git_commit": subject["source_commit"],
            "git_tree": subject["source_tree"],
            "program_tree": subject["program_tree"],
            "generator_version": report["validator"]["version"],
            "generator_digest": report["validator"]["blob_sha256"],
            "input_manifest_digest": subject["input_manifest_digest"],
            "input_manifest": subject["input_manifest"],
        },
        "container_relation": {
            "container_commit": None,
            "required_first_parent": subject["source_commit"],
            "allowed_changed_paths": ["docs/programs/engineering-process-platform/dashboard.json"],
            "relation_status": "candidate_not_committed",
        },
        "release_candidate": subject["release_candidate"],
        "areas": report["areas"],
        "benchmark_summary": report["benchmark_summary"],
        "release_approval": report["release_approval"],
        "release_eligible": report["release_eligible"],
        "next_action": report["next_action"],
    }


def atomic_replace_json(
    target: Path,
    value: Mapping[str, Any],
    schema: Mapping[str, Any],
    *,
    replace: Callable[[str | bytes | os.PathLike[str] | os.PathLike[bytes], str | bytes | os.PathLike[str] | os.PathLike[bytes]], None] = os.replace,
) -> None:
    """Validate and atomically replace one JSON file, preserving prior bytes on failure."""

    raw = deterministic_json_bytes(value)
    parsed = strict_loads(raw)
    if validate_schema(schema, parsed):
        raise DashboardError("OUTPUT_CANDIDATE_INVALID")
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            prefix=f".{target.name}.",
            suffix=".tmp",
            dir=target.parent,
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        reread = temporary.read_bytes()
        if reread != raw or validate_schema(schema, strict_loads(reread)):
            raise DashboardError("OUTPUT_REREAD_INVALID")
        replace(temporary, target)
        temporary = None
    except DashboardError:
        raise
    except OSError as exc:
        raise DashboardError("OUTPUT_REPLACE_FAILED") from exc
    finally:
        if temporary is not None:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
