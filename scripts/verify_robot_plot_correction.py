"""Read-only full-profile diagnostic of Robot 009; never approves or resumes it."""
from __future__ import annotations

import argparse
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path

from core.process_validation import ProducerIdentity, SubjectBinding, ValidationRequest
from data_vault.process_validation_repository import ProcessValidationRepository
from data_vault.state_store import connect_state_db
from workspace_service.process_validation.process import output_id
from workspace_service.process_validation.profiles import load_profile
from workspace_service.process_validation.service import ProcessValidationService
from workspace_service.process_validation.subjects import SubjectResolver
from workspace_service.workflow_source_execution import compile_prompt_workflow

ROOT = Path(__file__).resolve().parents[1]
FILES = {"conversion_manifest": "converted/conversion-manifest.json", "timeline": "analysis/timeline.csv",
    "metrics": "analysis/tracking-metrics.json", "plot": "analysis/trajectory-overlay.svg", "diagnosis": "diagnosis.md"}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    workspace, output = args.workspace_root.resolve(), args.output.resolve()
    if output.exists() or output.is_relative_to(workspace):
        raise ValueError("Diagnostic output must be new and outside the engineering workspace")
    local = ROOT / ".local-run/feature-081-live/campaign-execution/validator-campaign-082/robot-tracking-diagnosis-01/attempt-009"
    predecessor = json.loads((local / "predecessor.json").read_text(encoding="utf-8"))
    old = workspace / "campaign/robot-tracking-diagnosis-01/attempt-008"
    if predecessor["files"] != {p.relative_to(old).as_posix(): sha(p) for p in old.rglob("*") if p.is_file()}:
        raise ValueError("Original attempt files changed")
    case = json.loads((local / "execution.json").read_text(encoding="utf-8"))
    records = list((workspace / "runs" / Path(case["source_path"]).name.removesuffix(".workflow.wflow")).glob("*.json"))
    if len(records) != 1:
        raise ValueError("Expected exactly one successor run")
    record_path = records[0]
    record_digest = sha(record_path)
    run = json.loads(record_path.read_text(encoding="utf-8"))
    review = run["approval"]
    if run["status"] != "awaiting_approval" or review["state"] != "pending" or review["actor"] is not None:
        raise ValueError("Successor is no longer at the pending review boundary")
    if run["source_digest"] != case["source_digest"] or sha(workspace / case["source_path"]) != case["source_digest"]:
        raise ValueError("Successor workflow source identity changed")
    subjects = []
    missing_bindings = []
    plan = compile_prompt_workflow((workspace / case["source_path"]).read_text(encoding="utf-8"))
    validator = next(step for step in plan.steps if step.validation)
    for role, relative in FILES.items():
        location = case["output_root"] + "/" + relative
        result, representation = next((result, rep) for result in review["continuation"]["results"]
            for rep in result["representations"] if rep["kind"] == "workspace_file" and rep["location"] == location)
        if sha(workspace / location) != representation["sha256"]:
            raise ValueError("Recorded output bytes changed: " + location)
        address = dict(validator.validation_sources)[role]
        step_id, port = address.split(".", 1)
        producer_record = next(r for r in review["continuation"]["records"] if r["task_id"] == step_id)
        identity = output_id(run["run_id"], step_id, producer_record["producer_attempt"], port)
        # Read the scheduler's exact registered port, not a guessed file result ID.
        with connect_state_db(ROOT / ".local-run/feature-081-live/data/wright.db", read_only=True) as database:
            row = database.execute("SELECT payload_json FROM process_validation_outputs WHERE workspace_id=? AND id=?",
                (review["workspace_id"], identity)).fetchone()
        if row is None:
            missing_bindings.append({"role": role, "step_id": step_id, "output_port": port})
            # Assess the observed file in the isolated database, while explicitly
            # retaining the missing canonical handoff as a blocker. Never backfill
            # the live ledger or pretend this diagnostic is the run's gate.
            subject = SubjectBinding(id=identity, role=role, result_id="diagnostic-" + role,
                producer=ProducerIdentity(run_id=run["run_id"], step_id=step_id,
                    attempt=producer_record["producer_attempt"], output_port=port),
                kind="file", locator=location, format=representation["format"], encoding="raw-bytes", sha256=representation["sha256"])
        else:
            subject = SubjectBinding.model_validate_json(row["payload_json"]).model_copy(update={"role": role})
        if subject.sha256 != representation["sha256"]:
            raise ValueError("Canonical port and recorded file disagree: " + role)
        subjects.append(subject)
    profile = load_profile("robot-tracking-diagnosis-01")
    # No canonical invocation identity and no copied/fabricated human decisions.
    # This separate database is diagnostic evidence, not the run's gate or campaign credit.
    output.mkdir(parents=True)
    service = ProcessValidationService(ProcessValidationRepository(output / "diagnostic.sqlite3"),
        SubjectResolver(review["workspace_id"], str(workspace)))
    request = ValidationRequest(trace_id="robot009-plot-diagnostic", workspace_id=review["workspace_id"],
        invocation_id="robot009-plot-diagnostic", subjects=tuple(subjects), profile_ref=profile.reference(),
        baseline_ref=profile.baseline.reference(), idempotency_key="robot009-plot-diagnostic")
    outcome = service.evaluate(request, profile)
    assessment = outcome.assessment
    if assessment is None:
        raise ValueError("Diagnostic did not produce an assessment")
    for fmt in ("json", "markdown", "csv"):
        exported = service.export_result(assessment.id, fmt)
        (output / exported.filename).write_bytes(exported.content)
    original_metrics = json.loads((old / "artifacts/analysis/tracking-metrics.json").read_text(encoding="utf-8"))
    corrected = workspace / case["output_root"]
    current_metrics = json.loads((corrected / "analysis/tracking-metrics.json").read_text(encoding="utf-8"))
    metrics_equal = {key: current_metrics.get(key) == value for key, value in original_metrics.items()
        if key not in {"operation_sha256", "plot_files"}}
    summary = {"scope": "Detached full-profile diagnostic; no approval, canonical gate execution, or campaign credit",
        "observed_at": datetime.now(UTC).isoformat(), "run_id": run["run_id"],
        "profile_ref": profile.reference().model_dump(mode="json"),
        "checks": [{"id": c.check_id, "state": c.state} for c in assessment.checks],
        "findings": [{"check": f.check_id, "code": f.code, "requirements": f.requirement_ids} for f in assessment.findings],
        "release_eligible": outcome.release_eligible, "review_state": review["state"], "review_actor": review["actor"],
        "canonical_output_bindings_missing": missing_bindings,
        "original_files_unchanged": True, "original_file_count": len(predecessor["files"]),
        "timeline_bytes_unchanged": (old / "artifacts/analysis/timeline.csv").read_bytes() == (corrected / "analysis/timeline.csv").read_bytes(),
        "original_metric_values_unchanged": metrics_equal, "saved_run_unchanged": sha(record_path) == record_digest}
    (output / "verification.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    if not (summary["timeline_bytes_unchanged"] and summary["saved_run_unchanged"] and all(metrics_equal.values())):
        raise ValueError("Correction changed measured evidence; inspect verification.json")
    if set(f.code for f in assessment.findings) != {"review.required"}:
        raise ValueError("Unexpected full-profile findings; inspect diagnostic report")
    print(json.dumps({"output": str(output), "automated_checks_passed": sum(c.state == "pass" for c in assessment.checks),
        "pending_review_checks": sum(c.state != "pass" for c in assessment.checks), "release_eligible": outcome.release_eligible,
        "canonical_output_bindings_missing": [item["role"] for item in missing_bindings],
        "original_files_unchanged": True, "timeline_bytes_unchanged": True}, indent=2))


if __name__ == "__main__":
    main()
