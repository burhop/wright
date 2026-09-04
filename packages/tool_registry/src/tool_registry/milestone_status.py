"""Pure evidence-backed native milestone projection shared with the publisher.

Git inspection stays in the offline publisher. The runtime recomputes every
derived count/status from the bounded source record and its identity attestations.
"""

from __future__ import annotations

import copy
from collections.abc import Mapping
from typing import Any


STATUSES = (
    "invalid",
    "failed",
    "stale",
    "blocked",
    "skipped",
    "not_run",
    "unavailable",
    "inconclusive",
    "not_tested",
)


def _unique(rows: list[dict[str, Any]], key: str = "id") -> dict[str, dict[str, Any]]:
    result = {row[key]: row for row in rows}
    if len(result) != len(rows):
        raise ValueError("duplicate milestone identity")
    return result


def _status(values: list[str]) -> str:
    if values and all(value == "passed" for value in values):
        return "passed"
    return next((value for value in STATUSES if value in values), "not_tested")


def derive_milestone(
    source: Mapping[str, Any],
    task_records: Mapping[str, Mapping[str, Any]],
    *,
    source_commit: str,
    observed_at: str,
    attestations: list[dict[str, Any]],
    delivery_attested: bool,
) -> dict[str, Any]:
    """Derive status without ever treating a missing check as passed."""
    tasks = _unique(source["tasks"])
    checks = _unique(source["checks"])
    criteria = _unique(source["acceptance"])
    evidence = _unique(source["evidence"])
    blockers = _unique(source["blockers"])
    examples = _unique(source["examples"])
    attest = _unique(attestations, "evidence_id")
    if set(tasks) != set(task_records) or not tasks:
        raise ValueError("milestone task population differs from registered tasks")
    population: set[str] = set()
    history = source["scope_history"]
    for revision, row in enumerate(history, 1):
        added, removed = set(row["added_task_ids"]), set(row["removed_task_ids"])
        if (
            row["revision"] != revision
            or added & population
            or not removed <= population
            or added & removed
        ):
            raise ValueError("milestone scope history is inconsistent")
        population = (population - removed) | added
    if population != set(tasks) or len(history) != source["scope_revision"]:
        raise ValueError("milestone scope denominator has no recorded change")
    if set(attest) != set(evidence):
        raise ValueError("milestone evidence attestation set differs")
    if not set(source["next_task_ids"]) <= set(tasks):
        raise ValueError("next task is not registered")
    for row in tasks.values():
        if not set(row["blocker_ids"]) <= set(blockers):
            raise ValueError("task blocker is not registered")
        if bool(row["integration_exemption"]) == row["integration_required"]:
            raise ValueError("integration exemption is missing or contradictory")
    for row in blockers.values():
        if not set(row["task_ids"]) <= set(tasks) or not set(row["check_ids"]) <= set(
            checks
        ):
            raise ValueError("blocker has an unknown subject")
    for row in checks.values():
        if not row["task_ids"] or not set(row["task_ids"]) <= set(tasks):
            raise ValueError("quality check has an unknown task")
    for row in criteria.values():
        if (
            not row["task_ids"]
            or not set(row["task_ids"]) <= set(tasks)
            or not row["required_check_ids"]
            or not set(row["required_check_ids"]) <= set(checks)
        ):
            raise ValueError("acceptance criterion has missing task/check coverage")
    for row in examples.values():
        if not set(row["check_ids"]) <= set(checks):
            raise ValueError("example has an unknown quality check")
    attempts: set[tuple[str, int]] = set()
    latest: dict[str, dict[str, Any]] = {}
    for row in evidence.values():
        check_id = row["check_id"]
        if check_id not in checks or (check_id, row["attempt"]) in attempts:
            raise ValueError("unknown check or duplicate evidence attempt")
        attempts.add((check_id, row["attempt"]))
        counts = row["counts"]
        if (
            counts is not None
            and sum(counts[k] for k in ("passed", "failed", "skipped", "not_run"))
            != counts["total"]
        ):
            raise ValueError("milestone quality counts do not reconcile")
        if check_id not in latest or latest[check_id]["attempt"] < row["attempt"]:
            latest[check_id] = row
    projected_checks = []
    for identifier, check in checks.items():
        row = latest.get(identifier)
        status, current = "not_tested", None
        urls: list[str] = []
        if row:
            counts = row["counts"]
            proof = attest[row["id"]]
            current = proof["tested_scope_sha256"] == proof["current_scope_sha256"]
            identity_valid = (
                proof["commit_tree_matches"]
                and proof["artifacts_match"]
                and proof["coverage_available"]
                and proof["tested_scope_sha256"] == row["scope_sha256"]
            )
            status = row["result"]
            if not identity_valid:
                status = "invalid"
            elif status == "passed":
                independent = (
                    row["verifier_id"] is not None
                    and row["verifier_id"] != row["author_id"]
                )
                if not row["artifacts"] or (
                    check["independent_required"] and not independent
                ):
                    status = "invalid"
                elif (
                    check["kind"] == "human_review"
                    and row["verification_actor_kind"] != "human"
                ):
                    status = "invalid"
                elif not current:
                    status = "stale"
                elif (
                    check["stage"] == "integration" or check["kind"] == "dev_deployment"
                ) and not delivery_attested:
                    status = "unavailable"
                elif counts is not None and (
                    not counts["total"]
                    or counts["failed"]
                    or counts["not_run"]
                    or counts["skipped"]
                ):
                    status = "inconclusive"
            urls = [
                f"https://github.com/burhop/wright/blob/{item['commit']}/{item['path']}"
                for item in row["artifacts"]
            ]
        projected_checks.append(
            {
                "id": identifier,
                "label": check["label"],
                "stage": check["stage"],
                "kind": check["kind"],
                "task_ids": check["task_ids"],
                "status": status,
                "evidence_id": row["id"] if row else None,
                "observed_at": row["observed_at"] if row else None,
                "tested_commit": row["tested_commit"] if row else None,
                "coverage_current": current,
                "counts": row["counts"] if row else None,
                "summary": row["summary"]
                if row
                else "No result has been recorded for this required check.",
                "artifact_urls": urls,
            }
        )
    by_check = _unique(projected_checks)
    projected_tasks = []
    for identifier, task in tasks.items():
        implemented = bool(task_records[identifier]["completed"])
        states = {
            stage: _status(
                [
                    check["status"]
                    for check in projected_checks
                    if check["stage"] == stage and identifier in check["task_ids"]
                ]
            )
            for stage in ("verification", "integration")
        }
        for stage in states:
            if states[stage] == "passed" and not implemented:
                states[stage] = "not_tested"
        if not task["integration_required"]:
            states["integration"] = "not_applicable"
        projected_tasks.append(
            {
                "id": identifier,
                "title": task_records[identifier]["title"],
                "activity": task["activity"],
                "owner": task["owner"],
                "implemented": implemented,
                **states,
                "integration_required": task["integration_required"],
                "blocker_ids": task["blocker_ids"],
            }
        )
    by_task = _unique(projected_tasks)
    projected_criteria = []
    for identifier, criterion in criteria.items():
        missing = [
            key
            for key in criterion["required_check_ids"]
            if by_check[key]["status"] != "passed"
        ]
        complete = all(by_task[key]["implemented"] for key in criterion["task_ids"])
        status = (
            "passed"
            if complete and not missing
            else _status(
                [by_check[key]["status"] for key in criterion["required_check_ids"]]
            )
        )
        if not complete and status == "passed":
            status = "not_tested"
        projected_criteria.append(
            {
                "id": identifier,
                "title": criterion["title"],
                "task_ids": criterion["task_ids"],
                "check_ids": criterion["required_check_ids"],
                "status": status,
                "missing_check_ids": missing,
            }
        )
    delivery = copy.deepcopy(source["delivery"])
    deployment = delivery["deployment_check_ids"]
    if not set(deployment) <= set(checks):
        raise ValueError("unknown deployment check")
    delivery["deployment_status"] = _status(
        [by_check[key]["status"] for key in deployment]
    )
    projected_examples = []
    for example in examples.values():
        relevant = [by_check[key] for key in example["check_ids"]]
        maturity = (
            "tested"
            if relevant and all(check["status"] == "passed" for check in relevant)
            else "planned"
        )
        if maturity == "tested" and any(
            checks[row["id"]]["independent_required"] for row in relevant
        ):
            maturity = "independently_verified"
        projected_examples.append({**example, "maturity": maturity})
    total = len(tasks)
    integrated_total = sum(row["integration_required"] for row in tasks.values())
    complete = (
        all(row["status"] == "passed" for row in projected_criteria)
        and delivery["deployment_status"] == "passed"
        and all(
            row["implemented"]
            and row["verification"] == "passed"
            and row["integration"] in {"passed", "not_applicable"}
            for row in projected_tasks
        )
    )
    return {
        "id": source["id"],
        "title": source["title"],
        "feature_id": source["feature_id"],
        "scope_revision": source["scope_revision"],
        "scope_history": source["scope_history"],
        "source_commit": source_commit,
        "observed_at": observed_at,
        "candidate_commit": delivery["candidate_commit"] or source_commit,
        "language_authority": source["language_authority"],
        "capabilities": source["capabilities"],
        "tasks": projected_tasks,
        "acceptance": projected_criteria,
        "checks": projected_checks,
        "counts": {
            "implementation": {
                "completed": sum(row["implemented"] for row in projected_tasks),
                "total": total,
            },
            "verification": {
                "completed": sum(
                    row["verification"] == "passed" for row in projected_tasks
                ),
                "total": total,
            },
            "integration": {
                "completed": sum(
                    row["integration"] == "passed" for row in projected_tasks
                ),
                "total": integrated_total,
                "not_applicable": total - integrated_total,
            },
        },
        "blockers": source["blockers"],
        "next_task_ids": source["next_task_ids"],
        "examples": projected_examples,
        "delivery": delivery,
        "readiness": {
            "native_milestone": "complete" if complete else "in_progress",
            "benchmark": "not_qualified",
            "commercial": "not_assessed",
            "release": "not_authorized",
            "rivet_migration": "not_started",
            "rivet_retirement": "not_started",
        },
        "source_record": copy.deepcopy(dict(source)),
        "attestations": attestations,
        "delivery_attested": delivery_attested,
    }


def validate_milestone(value: Mapping[str, Any], source_commit: str) -> None:
    """Reject self-hashed false arithmetic and unbacked quality claims."""
    if value["source_commit"] != source_commit:
        raise ValueError("milestone source differs from bundle source")
    records = {
        row["id"]: {"title": row["title"], "completed": row["implemented"]}
        for row in value["tasks"]
    }
    if len(records) != len(value["tasks"]):
        raise ValueError("duplicate projected milestone task")
    expected = derive_milestone(
        value["source_record"],
        records,
        source_commit=source_commit,
        observed_at=value["observed_at"],
        attestations=value["attestations"],
        delivery_attested=value["delivery_attested"],
    )
    if expected != value:
        raise ValueError("milestone projection does not match its evidence")
