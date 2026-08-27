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
) -> dict[str, dict[str, Any]]:
    """Derive four independent readiness areas from catalog membership and evidence."""

    if list(catalog.get("area_order", [])) != list(AREA_ORDER):
        raise DashboardError("GATE_AREA_ORDER_INVALID")
    gates = list(catalog.get("gates", []))
    gate_ids = [gate.get("id") for gate in gates]
    if len(gate_ids) != len(set(gate_ids)):
        raise DashboardError("GATE_ID_DUPLICATE")
    assertions = list(evidence_set.get("assertions", []))
    assertion_ids = [row.get("gate_id") for row in assertions]
    if len(assertion_ids) != len(set(assertion_ids)):
        raise DashboardError("GATE_EVIDENCE_DUPLICATE")
    assertion_by_id = {str(row["gate_id"]): row for row in assertions if "gate_id" in row}
    areas: dict[str, dict[str, Any]] = {}
    for area in AREA_ORDER:
        required = [gate for gate in gates if gate.get("area") == area and gate.get("required")]
        rows: list[dict[str, Any]] = []
        for gate in required:
            gate_id = str(gate["id"])
            assertion = assertion_by_id.get(gate_id)
            if assertion is None:
                rows.append(
                    {
                        "id": gate_id,
                        "status": "not_started",
                        "classification": "not_tested",
                        "reason_code": "EVIDENCE_NOT_RECORDED",
                        "evidence": [],
                    }
                )
                continue
            status = _effective_status(assertion, observed_at)
            rows.append(
                {
                    "id": gate_id,
                    "status": status,
                    "classification": assertion["classification"],
                    "reason_code": assertion["reason_code"],
                    "evidence": [
                        {
                            "path": item["path"],
                            "sha256": item["sha256"],
                            "git_blob": item.get("git_blob", "0" * 40),
                        }
                        for item in assertion.get("evidence", [])
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
            "fresh": bool(rows) and all(row["status"] not in {"stale", "not_started"} for row in rows),
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
