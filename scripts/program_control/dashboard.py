"""Gate projection and transactional dashboard delivery."""

from __future__ import annotations

import os
import tempfile
from collections.abc import Callable, Mapping, Sequence
from datetime import datetime, timedelta, timezone
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
    catalog_digest: str | None = None,
    source_documents: Mapping[str, Any] | None = None,
) -> dict[str, dict[str, Any]]:
    """Derive four independent readiness areas from catalog membership and evidence."""

    if list(catalog.get("area_order", [])) != list(AREA_ORDER):
        raise DashboardError("GATE_AREA_ORDER_INVALID")
    if (
        catalog_digest is not None
        and evidence_set.get("catalog_digest") != catalog_digest
    ):
        raise DashboardError("GATE_CATALOG_DIGEST_MISMATCH")
    data_cutoff = _parse_time(str(evidence_set.get("data_cutoff")))
    if data_cutoff > observed_at:
        raise DashboardError("GATE_DATA_CUTOFF_INVALID")
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
    assertion_by_id = {
        str(row["gate_id"]): row for row in assertions if "gate_id" in row
    }
    manifest_by_path: dict[str, Mapping[str, Any]] = {}
    for row in source_manifest or []:
        if not isinstance(row, Mapping):
            continue
        path = str(row.get("path"))
        manifest_by_path[path] = row
        marker = "docs/programs/engineering-process-platform/"
        if path.startswith(marker):
            manifest_by_path[path.removeprefix(marker)] = row
    documents = source_documents or {}

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
            if artifact.get("schema_id") != binding.get("schema_id") or artifact.get(
                "source_role"
            ) != binding.get("source_role"):
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
                artifact_path = str(artifact.get("path"))
                document = documents.get(artifact_path)
                if document is None:
                    document = documents.get(
                        "docs/programs/engineering-process-platform/" + artifact_path
                    )
                if isinstance(document, Mapping):
                    embedded = document.get("subject", document.get("candidate"))
                    if isinstance(embedded, Mapping) and embedded != candidate:
                        raise DashboardError("EVIDENCE_CANDIDATE_MISMATCH")
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
        required = [
            gate for gate in gates if gate.get("area") == area and gate.get("required")
        ]
        rows: list[dict[str, Any]] = []
        for gate in required:
            gate_id = str(gate["id"])
            assertion = assertion_by_id.get(gate_id)
            if assertion is None:
                raise DashboardError("GATE_EVIDENCE_SET_MISMATCH")
            if assertion.get("evaluator") != gate.get("evaluator"):
                raise DashboardError("GATE_EVALUATOR_MISMATCH")
            results = list(assertion.get("assertion_results", []))
            expected_result_ids = [
                row.get("assertion_id") for row in gate.get("assertions", [])
            ]
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
            gate_freshness = gate.get("freshness", {})
            expected_triggers = set(gate_freshness.get("invalidation_triggers", []))
            maximum_age = int(gate_freshness.get("maximum_age_seconds", 0))
            if maximum_age <= 0:
                raise DashboardError("GATE_FRESHNESS_POLICY_INVALID")
            if set(assertion.get("stale_triggers", [])) != expected_triggers:
                raise DashboardError("GATE_FRESHNESS_POLICY_INVALID")
            for result in results:
                if set(result.get("stale_triggers", [])) != expected_triggers:
                    raise DashboardError("GATE_FRESHNESS_POLICY_INVALID")
                age = (
                    observed_at - _parse_time(str(result.get("observed_at")))
                ).total_seconds()
                if age < 0 or (result.get("fresh") is True and age > maximum_age):
                    raise DashboardError("GATE_FRESHNESS_MISMATCH")
            worst = next(
                (
                    candidate_status
                    for candidate_status in NONPASSING_PRECEDENCE
                    if candidate_status in statuses
                ),
                "passed",
            )
            governing_results = [
                result
                for result, result_state in zip(results, statuses, strict=True)
                if result_state == worst
            ]
            expected_classification = str(governing_results[0].get("classification"))
            expected_reason = sorted(
                str(row.get("reason_code")) for row in governing_results
            )[0]
            if (
                assertion.get("classification") != expected_classification
                or assertion.get("reason_code") != expected_reason
            ):
                raise DashboardError("GATE_AGGREGATE_METADATA_MISMATCH")
            row_expires = assertion.get("expires_at")
            row_expired = (
                row_expires is not None and _parse_time(str(row_expires)) < observed_at
            )
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
            row_artifacts = [
                item
                for item in assertion.get("evidence", [])
                if isinstance(item, Mapping)
            ]
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

            def artifact_key(item: Mapping[str, Any]) -> tuple[str, ...]:
                return (
                    str(item.get("path")),
                    str(item.get("sha256")),
                    str(item.get("evidence_class")),
                    str(item.get("schema_id")),
                    str(item.get("source_role")),
                )

            required_classes = set(
                gate.get("evidence_policy", {}).get("required_classes", [])
            )
            if passing and not required_classes.issubset(row_classes):
                raise DashboardError("EVIDENCE_CLASS_COVERAGE_MISSING")
            if sorted(map(artifact_key, row_artifacts)) != sorted(
                set(map(artifact_key, result_artifacts))
            ):
                raise DashboardError("GATE_EVIDENCE_UNION_MISMATCH")
            independent_required = bool(
                gate.get("evidence_policy", {}).get("independent_verifier_required")
            )
            if passing and independent_required:
                if assertion.get("verifier", {}).get("independent") is not True or any(
                    result.get("verifier", {}).get("independent") is not True
                    for result in results
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
                (
                    candidate
                    for candidate in NONPASSING_PRECEDENCE
                    if candidate in statuses
                ),
                "not_started",
            )
        blockers = sorted(
            {str(row["reason_code"]) for row in rows if row["status"] != "passed"}
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
            "last_success_at": (
                max(
                    str(assertion_by_id[str(gate["id"])].get("observed_at"))
                    for gate in required
                )
                if area_status == "passed"
                else None
            ),
        }
    return areas


def default_benchmark_summary(
    source: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if source:
        raise DashboardError("BENCHMARK_SUMMARY_HAND_SET")
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
    for name, fallback in (
        ("coverage_deficits", ["BENCHMARK_COVERAGE_EMPTY"]),
        ("oracle_deficits", ["BENCHMARK_ORACLES_ABSENT"]),
        ("artifact_deficits", ["BENCHMARK_ARTIFACTS_ABSENT"]),
        ("partition_deficits", ["BENCHMARK_PARTITIONS_ABSENT"]),
        ("freshness_deficits", ["BENCHMARK_EVIDENCE_ABSENT"]),
    ):
        counters[name] = list(fallback)
    return counters


def derive_benchmark_summary(
    cases: Sequence[Mapping[str, Any]],
    evidence_records: Sequence[Mapping[str, Any]],
    observed_at: datetime,
) -> dict[str, Any]:
    """Derive the 100-slot benchmark summary from governed case/run records."""

    if not cases and not evidence_records:
        return default_benchmark_summary()
    current_cases: dict[str, Mapping[str, Any]] = {}
    families: set[str] = set()
    for case in cases:
        process_id = str(case.get("process_id", ""))
        family = str(case.get("equivalence_family", ""))
        if process_id in current_cases or not process_id or family in families:
            raise DashboardError("BENCHMARK_DISTINCTNESS_INVALID")
        if case.get("status") == "current":
            current_cases[process_id] = case
            families.add(family)
    if len(current_cases) > 100:
        raise DashboardError("BENCHMARK_POPULATION_INVALID")

    histories: dict[str, list[Mapping[str, Any]]] = {}
    for record in evidence_records:
        process_id = str(record.get("process_id", ""))
        if process_id not in current_cases:
            raise DashboardError("BENCHMARK_EVIDENCE_CASE_MISMATCH")
        histories.setdefault(process_id, []).append(record)
    for process_id, rows in histories.items():
        rows.sort(key=lambda row: int(row.get("attempt", {}).get("ordinal", 0)))
        ordinals = [int(row.get("attempt", {}).get("ordinal", 0)) for row in rows]
        if ordinals != list(range(1, len(rows) + 1)):
            raise DashboardError("BENCHMARK_ATTEMPT_HISTORY_INVALID")
        for index, row in enumerate(rows):
            attempt = row.get("attempt", {})
            if bool(attempt.get("first_attempt")) != (index == 0):
                raise DashboardError("BENCHMARK_ATTEMPT_HISTORY_INVALID")
            expected_prior = (
                None
                if index == 0
                else rows[index - 1].get("attempt", {}).get("attempt_id")
            )
            if attempt.get("prior_attempt") != expected_prior:
                raise DashboardError("BENCHMARK_ATTEMPT_HISTORY_INVALID")

    counters = default_benchmark_summary()
    counters["counted"] = len(current_cases)
    counters["not_tested"] = 100
    outcome_by_process: dict[str, str] = {}
    for process_id, case in current_cases.items():
        rows = histories.get(process_id, [])
        latest = rows[-1] if rows else None
        outcome = "not_tested"
        if case.get("status") == "contaminated" or (
            latest
            and latest.get("qualification_transition", {}).get("to") == "contaminated"
        ):
            outcome = "contaminated"
        elif latest:
            expires = _parse_time(str(latest.get("observed_at")))
            expires += timedelta(hours=int(latest.get("maximum_age_hours", 0)))
            terminal = str(latest.get("terminal_classification"))
            if expires < observed_at:
                outcome = "stale"
            elif terminal == "passed":
                outcome = "eventual_passed"
            elif terminal == "blocked_prerequisite":
                outcome = "blocked"
            elif terminal in {
                "failed_product",
                "failed_oracle_or_benchmark",
                "failed_infrastructure",
                "timed_out",
                "cancelled",
                "inconclusive",
            }:
                outcome = "failed"
        outcome_by_process[process_id] = outcome
        if outcome != "not_tested":
            counters[outcome] += 1
            counters["not_tested"] -= 1
        if (
            outcome == "eventual_passed"
            and rows[0].get("terminal_classification") == "passed"
        ):
            counters["first_attempt_passed"] += 1

    for case in current_cases.values():
        tiers = {str(profile.get("tier")) for profile in case.get("profiles", [])}
        if ("T1" in tiers and "T0" not in tiers) or (
            ({"T2", "T3"} & tiers) and not {"T0", "T1"}.issubset(tiers)
        ):
            raise DashboardError("BENCHMARK_TIER_DEPENDENCY_INVALID")
        for tier in ("T0", "T1", "T2", "T3"):
            counters[tier.lower()] += int(tier in tiers)

    counters["coverage_deficits"] = (
        [] if len(current_cases) == 100 else ["BENCHMARK_COVERAGE_INCOMPLETE"]
    )
    counters["oracle_deficits"] = (
        []
        if current_cases
        and all(case.get("oracle_refs") for case in current_cases.values())
        else ["BENCHMARK_ORACLES_INCOMPLETE"]
    )
    passed_records = [
        histories[process_id][-1]
        for process_id, outcome in outcome_by_process.items()
        if outcome == "eventual_passed"
    ]
    counters["artifact_deficits"] = (
        []
        if passed_records
        and all(
            row.get("required_output_coverage", {}).get("complete") is True
            and row.get("artifacts")
            and all(
                item.get("parse_open_result") in {"passed", "not_applicable"}
                for item in row.get("artifacts", [])
            )
            for row in passed_records
        )
        else ["BENCHMARK_ARTIFACTS_INCOMPLETE"]
    )
    partitions = {str(case.get("partition")) for case in current_cases.values()}
    counters["partition_deficits"] = (
        []
        if {"development", "frozen_qualification", "blind_holdout"}.issubset(partitions)
        else ["BENCHMARK_PARTITIONS_INCOMPLETE"]
    )
    counters["freshness_deficits"] = (
        []
        if histories and "stale" not in outcome_by_process.values()
        else ["BENCHMARK_EVIDENCE_STALE_OR_ABSENT"]
    )
    return counters


def make_dashboard(
    report: Mapping[str, Any], *, data_cutoff: str | None = None
) -> dict[str, Any]:
    subject = report["subject"]
    return {
        "$schema": "./schemas/dashboard.schema.json",
        "schema_version": "2.0",
        "program_id": "EPP-2026",
        "generation_status": "candidate_not_evidence",
        "generated_at": report["observed_at"],
        "data_cutoff": data_cutoff or report["observed_at"],
        "source": {
            "git_commit": subject["source_commit"],
            "git_tree": subject["source_tree"],
            "program_tree": subject["program_tree"],
            "generator_version": report["validator"]["version"],
            "generator_bundle_manifest_digest": report["validator"][
                "bundle_manifest_digest"
            ],
            "generator_bundle_manifest": report["validator"]["bundle_manifest"],
            "input_manifest_digest": subject["input_manifest_digest"],
            "artifact_digests": subject["input_manifest"],
        },
        "container_relation": {
            "first_parent_must_equal_source": True,
            "allowed_generated_outputs": [
                "docs/programs/engineering-process-platform/dashboard.json"
            ],
            "container_commit_embedded": False,
            "delivery_evidence_embedded": False,
        },
        "release_candidate": subject["release_candidate"],
        "areas": report["areas"],
        "benchmark_summary": report["benchmark_summary"],
        "release_approval": report["release_approval"],
        "release_eligible": report["release_eligible"],
        "release_formula": "product_readiness && benchmark_readiness && commercial_readiness && program_health && human_release_approval",
        "next_action": (
            str(report["next_action"]["action"])
            if isinstance(report.get("next_action"), Mapping)
            else "NO_ELIGIBLE_ACTION_INSPECT_BLOCKERS"
        ),
    }


def atomic_replace_json(
    target: Path,
    value: Mapping[str, Any],
    schema: Mapping[str, Any],
    *,
    replace: Callable[
        [
            str | bytes | os.PathLike[str] | os.PathLike[bytes],
            str | bytes | os.PathLike[str] | os.PathLike[bytes],
        ],
        None,
    ] = os.replace,
    write: Callable[[Any, bytes], Any] | None = None,
    flush: Callable[[Any], Any] | None = None,
    fsync: Callable[[int], Any] = os.fsync,
    reread: Callable[[Path], bytes] = Path.read_bytes,
) -> None:
    """Validate and atomically replace one JSON file, preserving prior bytes on failure."""

    raw = deterministic_json_bytes(value)
    parsed = strict_loads(raw)
    if validate_schema(schema, parsed):
        raise DashboardError("OUTPUT_CANDIDATE_INVALID")
    temporary: Path | None = None
    stage = "prepare"
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="wb",
            prefix=f".{target.name}.",
            suffix=".tmp",
            dir=target.parent,
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            stage = "write"
            (write or (lambda stream, data: stream.write(data)))(handle, raw)
            stage = "flush"
            (flush or (lambda stream: stream.flush()))(handle)
            stage = "fsync"
            fsync(handle.fileno())
        stage = "reread"
        reread_bytes = reread(temporary)
        if reread_bytes != raw or validate_schema(schema, strict_loads(reread_bytes)):
            raise DashboardError("OUTPUT_REREAD_INVALID")
        stage = "replace"
        replace(temporary, target)
        temporary = None
    except DashboardError:
        raise
    except KeyboardInterrupt as exc:
        raise DashboardError("OUTPUT_INTERRUPTED") from exc
    except OSError as exc:
        codes = {
            "prepare": "OUTPUT_PREPARE_FAILED",
            "write": "OUTPUT_WRITE_FAILED",
            "flush": "OUTPUT_FLUSH_FAILED",
            "fsync": "OUTPUT_FSYNC_FAILED",
            "reread": "OUTPUT_REREAD_FAILED",
            "replace": "OUTPUT_REPLACE_FAILED",
        }
        raise DashboardError(codes[stage]) from exc
    finally:
        if temporary is not None:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
