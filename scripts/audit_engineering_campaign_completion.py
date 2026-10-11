"""Build the final machine-readable and Markdown 30-case campaign audit."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path


METRICS = (
    "datasets_created",
    "combinations_run",
    "processes_with_outputs",
    "valid_data",
)


def _refs(value: dict) -> dict:
    return {
        "profile_ref": value.get("profile_ref"),
        "baseline_ref": value.get("baseline_ref"),
    }


def audit(status: dict, coverage: dict, *, target: int = 30) -> dict:
    coverage_rows = {
        row["scenario_id"]: row for row in coverage.get("scenarios", [])
    }
    datasets = status.get("datasets", [])
    rows = []
    for dataset in datasets:
        scenario_id = dataset.get("scenario_id")
        support = coverage_rows.get(scenario_id, {})
        credit = support.get("campaign_credit") or {}
        profile = support.get("profile") or {}
        attempt = dataset.get("latest_attempt")
        blockers = []
        if support.get("support_status") != "qualified":
            blockers.append("validator_capability_not_qualified")
        if credit.get("full_scope") is not True:
            blockers.append("full_scope_not_declared")
        if not credit.get("requirement_ids"):
            blockers.append("mandatory_requirements_not_declared")
        if not credit.get("subject_roles"):
            blockers.append("subject_roles_not_declared")
        if not attempt:
            blockers.append("no_current_attempt")
            attempt = {}
        if (
            attempt.get("dataset_digest") != dataset.get("digest")
            or attempt.get("template_digest") != dataset.get("template_digest")
        ):
            blockers.append("attempt_not_current")
        if not (
            attempt.get("accepted_by_runtime") is True
            and attempt.get("execution_kind") in {"live", "integration"}
            and attempt.get("run_id")
        ):
            blockers.append("current_process_not_run")
        output_check = attempt.get("output_check") or {}
        if not (
            dataset.get("completed_current_revision") is True
            and attempt.get("completed_with_outputs") is True
            and output_check.get("passed") is True
            and not output_check.get("missing_roles")
            and not output_check.get("output_errors")
        ):
            blockers.append("current_outputs_incomplete")
        required_steps = set(attempt.get("required_step_ids") or [])
        completed_steps = set(attempt.get("completed_step_ids") or [])
        if not required_steps or not required_steps.issubset(completed_steps):
            blockers.append("required_process_steps_incomplete")
        produced = attempt.get("produced_files") or []
        if not produced or any(
            not isinstance(item, dict)
            or not item.get("artifact_id")
            or not item.get("path")
            or not item.get("sha256")
            or item.get("run_id") != attempt.get("run_id")
            or not isinstance(item.get("size_bytes"), int)
            or item["size_bytes"] <= 0
            for item in produced
        ):
            blockers.append("produced_file_identity_incomplete")
        validation = output_check.get("validation") or {}
        assessments = validation.get("assessments") or []
        if not (
            output_check.get("content_validated") is True
            and validation.get("status") == "pass"
            and validation.get("release_eligible") is True
            and assessments
            and all(
                assessment.get("schema_version") == "wright.process-validation/1"
                and assessment.get("is_current") is True
                and assessment.get("full_scope") is True
                and assessment.get("release_eligible") is True
                and assessment.get("assessment_id")
                and assessment.get("assessment_digest")
                and assessment.get("assessment_artifact")
                for assessment in assessments
            )
        ):
            blockers.append("current_full_scope_assessment_not_passing")
        integrity = attempt.get("integrity_check") or {}
        if integrity.get("mode") != "full_audit" or not integrity.get("last_hashed_at"):
            blockers.append("current_output_bytes_not_full_audited")
        rows.append(
            {
                "scenario_id": scenario_id,
                "dataset_digest": dataset.get("digest"),
                "template_digest": dataset.get("template_digest"),
                "attempt_id": attempt.get("attempt_id"),
                "run_id": attempt.get("run_id"),
                "runtime_status": attempt.get("status", "not_run"),
                "profile": _refs(profile),
                "mandatory_requirement_ids": credit.get("requirement_ids", []),
                "required_subject_roles": credit.get("subject_roles", []),
                "produced_file_count": len(produced),
                "assessment_ids": [
                    item.get("assessment_id") for item in assessments
                    if isinstance(item, dict) and item.get("assessment_id")
                ],
                "ran_current_process": "current_process_not_run" not in blockers,
                "complete_current_outputs": "current_outputs_incomplete" not in blockers,
                "full_scope_requirements_pass": (
                    "current_full_scope_assessment_not_passing" not in blockers
                ),
                "full_byte_audit": (
                    "current_output_bytes_not_full_audited" not in blockers
                ),
                "status": "pass" if not blockers else "incomplete",
                "blockers": blockers,
            }
        )

    global_blockers = []
    if len(datasets) != target or len({row.get("scenario_id") for row in datasets}) != target:
        global_blockers.append("dataset_inventory_not_target")
    if len(coverage_rows) != target:
        global_blockers.append("coverage_inventory_not_target")
    if status.get("target") != target:
        global_blockers.append("campaign_target_changed")
    metrics = status.get("metrics") or {}
    if any(metrics.get(metric) != target for metric in METRICS):
        global_blockers.append("historical_metrics_not_complete")
    current = status.get("current_metrics") or {}
    if any(
        current.get(metric) != target
        for metric in ("combinations_run", "processes_with_outputs", "valid_data")
    ):
        global_blockers.append("current_metrics_not_complete")
    coverage_summary = status.get("validation_coverage") or {}
    if (
        coverage_summary.get("qualified") != target
        or coverage_summary.get("full_scope") != target
        or coverage_summary.get("unsupported") != 0
    ):
        global_blockers.append("validation_coverage_not_complete")
    reconciliation = status.get("reconciliation") or {}
    if (
        reconciliation.get("state") != "current"
        or reconciliation.get("integrity_mode") != "full_audit"
        or reconciliation.get("error") is not None
    ):
        global_blockers.append("campaign_full_audit_not_current")
    if status.get("issues"):
        global_blockers.append("campaign_ingestion_issues_present")
    passed = sum(row["status"] == "pass" for row in rows)
    complete = not global_blockers and passed == target
    return {
        "schema_version": "wright.engineering-campaign-completion/1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "campaign_id": status.get("campaign_id"),
        "target": target,
        "status": "complete" if complete else "incomplete",
        "metrics": metrics,
        "current_metrics": current,
        "validation_coverage": coverage_summary,
        "reconciliation": reconciliation,
        "summary": {
            "rows": len(rows),
            "passed": passed,
            "incomplete": len(rows) - passed,
            "global_blockers": global_blockers,
        },
        "rows": rows,
    }


def markdown(report: dict) -> str:
    lines = [
        "# Engineering campaign completion audit",
        "",
        f"**Status:** {report['status']}",
        f"**Campaign:** `{report['campaign_id']}`",
        f"**Generated:** `{report['generated_at']}`",
        "",
        "| Measure | Historical | Current | Target |",
        "|---|---:|---:|---:|",
        f"| Datasets | {report['metrics'].get('datasets_created', 0)} | {report['metrics'].get('datasets_created', 0)} | {report['target']} |",
        f"| Process runs | {report['metrics'].get('combinations_run', 0)} | {report['current_metrics'].get('combinations_run', 0)} | {report['target']} |",
        f"| Complete outputs | {report['metrics'].get('processes_with_outputs', 0)} | {report['current_metrics'].get('processes_with_outputs', 0)} | {report['target']} |",
        f"| Full-scope requirements passes | {report['metrics'].get('valid_data', 0)} | {report['current_metrics'].get('valid_data', 0)} | {report['target']} |",
        "",
    ]
    blockers = report["summary"]["global_blockers"]
    if blockers:
        lines.extend(["Global blockers: " + ", ".join(f"`{item}`" for item in blockers), ""])
    lines.extend(
        [
            "| Scenario | Attempt | Run | Outputs | Requirements | Byte audit | Status | Blockers |",
            "|---|---|---|---:|---:|---:|---|---|",
        ]
    )
    for row in report["rows"]:
        lines.append(
            "| {scenario} | {attempt} | {run} | {outputs} | {requirements} | {audit} | {status} | {blockers} |".format(
                scenario=row["scenario_id"],
                attempt=row["attempt_id"] or "—",
                run=row["run_id"] or "—",
                outputs="yes" if row["complete_current_outputs"] else "no",
                requirements="yes" if row["full_scope_requirements_pass"] else "no",
                audit="yes" if row["full_byte_audit"] else "no",
                status=row["status"],
                blockers=", ".join(row["blockers"]) or "—",
            )
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--status",
        type=Path,
        default=root / "artifacts/engineering-workflow-datasets/status.json",
    )
    parser.add_argument(
        "--coverage",
        type=Path,
        default=root
        / "packages/workspace_service/src/workspace_service/process_validation/"
        "profiles/coverage.json",
    )
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-markdown", type=Path, required=True)
    parser.add_argument("--target", type=int, default=30)
    parser.add_argument("--require-complete", action="store_true")
    args = parser.parse_args()
    report = audit(
        json.loads(args.status.read_text(encoding="utf-8-sig")),
        json.loads(args.coverage.read_text(encoding="utf-8-sig")),
        target=args.target,
    )
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_markdown.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    args.output_markdown.write_text(markdown(report), encoding="utf-8")
    print(json.dumps(report["summary"]))
    if args.require_complete and report["status"] != "complete":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
