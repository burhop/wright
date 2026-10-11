"""Build a compact, read-only inventory for the engineering campaign."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3


def _normalise_lines(data: bytes) -> bytes:
    return data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def _latest(attempts: list[dict]) -> dict | None:
    if not attempts:
        return None
    return max(attempts, key=lambda item: (item.get("started_at") or "", item.get("attempt_id") or ""))


def _snapshot_comparison(dataset: dict, attempt: dict | None, grants: sqlite3.Connection, workspace: Path) -> dict:
    changed = []
    line_endings_only = []
    content_changed = []
    missing = []
    not_in_snapshot = []
    if not attempt:
        return {
            "changed_input_files": changed,
            "line_endings_only": line_endings_only,
            "content_changed": content_changed,
            "not_in_snapshot": not_in_snapshot,
            "snapshot_missing": missing,
        }
    current_hashes = dataset.get("input_hashes") or {}
    policy_digest = attempt.get("integration_policy_digest")
    row = grants.execute(
        "SELECT document FROM workflow_integration_grants WHERE policy_digest=?", (policy_digest,)
    ).fetchone() if policy_digest else None
    paths_by_name = {}
    if row:
        grant = json.loads(row[0])
        for relative, file_digest in grant.get("input_files", {}).items():
            name = Path(relative).name
            if name in current_hashes:
                paths_by_name[name] = (relative, file_digest)
    revision = attempt.get("_dataset_revision") or {}
    prior_hashes = revision.get("input_hashes") or {
        name: value[1] for name, value in paths_by_name.items()
    }
    changed = sorted(name for name, digest in current_hashes.items() if prior_hashes.get(name) != digest)
    scenario_root = Path(dataset["_input_root"])
    for name in changed:
        old_entry = paths_by_name.get(name)
        if not old_entry:
            not_in_snapshot.append(name)
            continue
        old_relative = old_entry[0] if old_entry else None
        old_path = (workspace / old_relative).resolve() if old_relative else None
        new_path = scenario_root / name
        if not old_path or not old_path.is_file() or not new_path.is_file():
            missing.append(name)
            continue
        old_bytes, new_bytes = old_path.read_bytes(), new_path.read_bytes()
        if old_bytes != new_bytes and _normalise_lines(old_bytes) == _normalise_lines(new_bytes):
            line_endings_only.append(name)
        elif old_bytes != new_bytes:
            content_changed.append(name)
    return {
        "changed_input_files": changed,
        "line_endings_only": sorted(line_endings_only),
        "content_changed": sorted(content_changed),
        "not_in_snapshot": sorted(not_in_snapshot),
        "snapshot_missing": sorted(missing),
    }


def build(args: argparse.Namespace) -> dict:
    status_path = Path(args.status).resolve()
    status = json.loads(status_path.read_text(encoding="utf-8"))
    campaign_db = sqlite3.connect(f"file:{Path(args.campaign_database).resolve().as_posix()}?mode=ro", uri=True)
    grants_db = sqlite3.connect(f"file:{Path(args.runtime_database).resolve().as_posix()}?mode=ro", uri=True)
    revisions = {
        row[0]: json.loads(row[1])
        for row in campaign_db.execute("SELECT fingerprint, document FROM dataset_revisions")
    }
    attempts_by_scenario: dict[str, list[dict]] = {}
    for scenario_id, document, fingerprint in campaign_db.execute(
        "SELECT scenario_id, document, fingerprint FROM attempts"
    ):
        attempt = json.loads(document)
        attempt["_dataset_revision"] = revisions.get(fingerprint, {})
        attempts_by_scenario.setdefault(scenario_id, []).append(attempt)

    input_root = Path(args.inputs).resolve() / "scenarios"
    workspace = Path(args.workspace).resolve()
    rows = []
    for dataset in sorted(status["datasets"], key=lambda item: item["scenario_id"]):
        dataset = dict(dataset)
        dataset["_input_root"] = str(input_root / dataset["path"])
        attempts = attempts_by_scenario.get(dataset["scenario_id"], [])
        historical = _latest(attempts)
        current = _latest([
            item for item in attempts
            if item.get("dataset_digest") == dataset["digest"]
            and item.get("template_digest") == dataset["template_digest"]
        ])
        validation = dataset.get("validation") or {}
        credit = validation.get("campaign_credit") or {}
        full_scope = credit.get("full_scope") is True
        if current is None:
            blocker = "No canonical run exists for the current dataset/template revision."
        elif not current.get("completed_with_outputs"):
            blocker = current.get("error") or "The selected current run has no complete output set."
        elif not full_scope:
            blocker = credit.get("reason") or "Full-scope validator coverage is not qualified."
        elif validation.get("status") != "pass":
            blocker = "The selected current output set has no current passing full-scope assessment."
        else:
            blocker = None
        if not full_scope:
            next_action = "Freeze and qualify the full source-backed baseline before awarding campaign validation credit."
        elif current is None:
            next_action = "Run the current canonical workflow when the configured inference route is available."
        elif not current.get("completed_with_outputs"):
            next_action = "Resolve the recorded producer/provider failure, prove it in isolation, then use the bounded retry path."
        elif validation.get("status") != "pass":
            next_action = "Validate the selected output and route actionable findings to its producing step."
        else:
            next_action = "Retain the current immutable evidence."
        comparison = _snapshot_comparison(dataset, historical, grants_db, workspace)
        rows.append({
            "scenario_id": dataset["scenario_id"],
            "current_identity": {
                "dataset_digest": dataset["digest"],
                "template_digest": dataset["template_digest"],
                "input_hashes": dataset.get("input_hashes", {}),
            },
            "selected_historical": None if not historical else {
                "attempt_id": historical.get("attempt_id"),
                "run_id": historical.get("run_id"),
                "status": historical.get("status"),
                "dataset_digest": historical.get("dataset_digest"),
                "template_digest": historical.get("template_digest"),
                "complete_outputs": bool(historical.get("completed_with_outputs")),
                "produced_file_count": len(historical.get("produced_files") or []),
            },
            "selected_current": None if not current else {
                "attempt_id": current.get("attempt_id"),
                "run_id": current.get("run_id"),
                "status": current.get("status"),
                "complete_outputs": bool(current.get("completed_with_outputs")),
                "produced_file_count": len(current.get("produced_files") or []),
            },
            "retained_snapshot_comparison": comparison,
            "revision_comparison": {
                "dataset_changed": bool(
                    historical and historical.get("dataset_digest") != dataset["digest"]
                ),
                "template_changed": bool(
                    historical and historical.get("template_digest") != dataset["template_digest"]
                ),
            },
            "requirements_baseline": (validation.get("profile") or {}).get("baseline_ref"),
            "validator_coverage": {
                "support_status": validation.get("support_status", "unsupported"),
                "full_scope": full_scope,
                "scope": (validation.get("profile") or {}).get("scope"),
                "limitations": (validation.get("profile") or {}).get("limitations"),
            },
            "blocker": blocker,
            "next_action": next_action,
        })
    campaign_db.close()
    grants_db.close()
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_status": str(status_path),
        "selection_rule": "latest started_at, then attempt_id; current requires exact dataset and template digests",
        "line_ending_rule": "line_endings_only compares retained staged bytes after CRLF/CR-to-LF normalization",
        "counters": status.get("current_metrics", status.get("metrics")),
        "rows": rows,
        "summary": {
            "cases": len(rows),
            "current_runs": sum(row["selected_current"] is not None for row in rows),
            "current_complete_outputs": sum(bool(row["selected_current"] and row["selected_current"]["complete_outputs"]) for row in rows),
            "full_scope_validators": sum(row["validator_coverage"]["full_scope"] for row in rows),
            "historical_input_drift_cases": sum(bool(row["retained_snapshot_comparison"]["changed_input_files"]) for row in rows),
            "line_ending_only_files": sum(len(row["retained_snapshot_comparison"]["line_endings_only"]) for row in rows),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--status", required=True)
    parser.add_argument("--campaign-database", required=True)
    parser.add_argument("--runtime-database", required=True)
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--inputs", default="tests/datasets/engineering-workflows")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = build(args)
    destination = Path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(destination), **result["summary"]}))


if __name__ == "__main__":
    main()
