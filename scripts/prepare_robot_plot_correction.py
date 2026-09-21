"""Enroll one preserved Robot 008 successor after the isolated plot proof; never run it.

Uses the existing template, preparer and enrollment service. No review decision,
receipt substitution, output copying, or campaign-queue replacement is performed.
"""
from __future__ import annotations

import argparse
from datetime import UTC, datetime
import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import urllib.parse

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / ".local-run/feature-081-live"
SCENARIO = "robot-tracking-diagnosis-01"
MODEL = "openai-codex::gpt-5.6-sol"


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save_once(path, value):
    if path.exists():
        raise ValueError(f"Receipt already exists; inspect before continuing: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace-root", type=Path, required=True)
    parser.add_argument("--api", default="http://127.0.0.1:8000")
    parser.add_argument("--session", default="wright-local-e3dc0ef1-06da-45dd-83b9-290347814f8a")
    parser.add_argument("--attempt", default="attempt-009", choices=["attempt-009"])
    args = parser.parse_args()
    enroller = load("plot_correction_enroller", "enroll_engineering_dataset_case.py")
    preparer = load("plot_correction_preparer", "prepare-robot-dataset-campaign.py")
    bindings = load("plot_correction_bindings", "engineering_dataset_input_bindings.py")

    def api(method, path, body=None):
        return enroller.api_request(args.api, method, path, body)

    campaign = BASE / "campaign-execution/validator-campaign-082"
    local = campaign / SCENARIO / args.attempt
    workspace = args.workspace_root.resolve()
    previous = workspace / "campaign" / SCENARIO / "attempt-008"
    source_path = f"workflows/validator-082-{SCENARIO}-{args.attempt}.workflow.wflow"
    if local.exists() or (workspace / "campaign" / SCENARIO / args.attempt).exists() or (workspace / source_path).exists():
        raise ValueError("Successor already exists; reconcile it instead of preparing again")
    before = {p.relative_to(previous).as_posix(): sha(p) for p in previous.rglob("*") if p.is_file()}
    if not before:
        raise ValueError("Original attempt evidence is unavailable")
    proof_path = ROOT / "artifacts/robot-tracking-plot/20260921-r2/preview-provenance.json"
    proof = json.loads(proof_path.read_text(encoding="utf-8"))
    if not (proof["source_files_unchanged"] and proof["timeline_bytes_unchanged"]
            and all(proof["original_metric_values_unchanged"].values())
            and proof["operation_sha256"] == sha(ROOT / "scripts/robot_tracking_operations.py")):
        raise ValueError("Isolated plot proof is missing, failed, or not for the current source")
    if api("GET", "/api/agent/models").get("current_value") != MODEL:
        raise ValueError("Configured campaign model changed")
    old_query = urllib.parse.urlencode({"session_id": args.session,
        "path": f"workflows/validator-082-{SCENARIO}-attempt-008.workflow.wflow", "latest_only": "true"})
    prior = api("GET", "/api/workspace/workflow-sources/runs?" + old_query)["runs"][0]
    if (prior["run_id"] != "bf32d836e9dd4250bd34594748ceda87"
            or prior["status"] != "awaiting_approval" or prior["approval"]["state"] != "pending"
            or prior["approval"]["actor"] is not None):
        raise ValueError("Original review state changed; reconcile the user's decision first")
    predecessor = {"attempt_id": "attempt-008", "run_id": prior["run_id"],
        "checkpoint_id": prior["approval"]["checkpoint_id"], "subject_digest": prior["approval"]["subject_digest"],
        "state": prior["approval"]["state"], "actor": prior["approval"]["actor"], "files": before}
    save_once(local / "predecessor.json", predecessor)

    metadata = api("GET", "/api/workspace/workflow-source-templates/robot-tracking-diagnosis")["template"]
    request = {"session_id": args.session, "template_version": metadata["version"],
        "expected_source_digest": metadata["source_digest"], "workflow_path": source_path,
        "request_id": f"validator-082-{SCENARIO}-{args.attempt}"}
    save_once(local / "instance-request.json", request)
    # The persisted request marks the write boundary. Never automatically repeat an uncertain POST.
    instance = api("POST", "/api/workspace/workflow-source-templates/robot-tracking-diagnosis/instances", request)
    save_once(local / "template-instance.json", instance)
    original = local / "original.workflow.wflow"
    original.write_text(instance["source"], encoding="utf-8", newline="")
    tools = api("GET", "/api/workspace/workflow-sources/tools?" + urllib.parse.urlencode({"session_id": args.session}))["tools"]
    preparer.prepare(SimpleNamespace(workspace_root=str(workspace), draft_root=str(local / "prepared"),
        attempt=args.attempt, instance_source=str(original), server_map={
            "wright-campaign-rosbag": "413c3100-cd94-4436-b34a-5fa0373985a9",
            "wright-campaign-robot-operations": "c7279493-594a-4e17-b38e-673395a5f987",
        }), ROOT / "tests/datasets/engineering-workflows/scenarios/robot-tracking-diagnosis/01-aisle-floor-seam", tools)
    report_path = local / "prepared" / SCENARIO / args.attempt / "staging-manifest.json"
    execution_path = local / "execution.json"
    enroller.enroll(SimpleNamespace(prepared=str(report_path), campaign_state=str(ROOT / "artifacts/engineering-workflow-datasets/status.json"),
        database=str(BASE / "data/wright.db"), session=args.session, source_path=source_path,
        output=str(execution_path), api=args.api))
    case = json.loads(execution_path.read_text(encoding="utf-8"))
    if not bindings.validate_case(case)["complete"]:
        raise ValueError("Successor input evidence is incomplete")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if any((workspace / p).exists() for p in report["expected_tool_created_files"]):
        raise ValueError("Successor already has outputs; no reuse is allowed")
    after = {p.relative_to(previous).as_posix(): sha(p) for p in previous.rglob("*") if p.is_file()}
    if before != after:
        raise ValueError("Original attempt files changed")
    evidence = ROOT / "artifacts/engineering-workflow-datasets/diagnostics/robot01-engineering-presentation-r1.json"
    save_once(evidence, {"schema_version": 1, "observed_at": datetime.now(UTC).isoformat(),
        "status": "qualified_for_bounded_correction", "reason": "User requested legible, explained plots and a useful engineering review package.",
        "predecessor": predecessor, "successor_attempt": args.attempt,
        "isolated_proof": {"path": str(proof_path), "sha256": sha(proof_path)},
        "operation_sha256": sha(ROOT / "scripts/robot_tracking_operations.py"),
        "preparer_sha256": sha(ROOT / "scripts/prepare-robot-dataset-campaign.py"),
        "original_files_unchanged": True, "engineering_approval_recorded": False,
        "requirements_changed": False, "dispatched": False})
    case["retry_episode"] = {"episode_id": "robot01-engineering-presentation", "failure_key": "usability:unexplained-tracking-plots",
        "boundary": f"{SCENARIO}:engineering-review", "max_corrections": 2, "baseline_attempt_ids": ["attempt-008"],
        "correction": {"id": "explained-three-path-plots-r1", "evidence": [{"id": "robot01-engineering-presentation-r1",
            "path": evidence.relative_to(ROOT / "artifacts/engineering-workflow-datasets").as_posix(), "sha256": sha(evidence)}]}}
    manifest = campaign / "pilot-robot01-attempt009-correction.json"
    save_once(manifest, {"schema_version": 1, "cases": [case]})
    summary = {"status": "enrolled_not_dispatched", "manifest": str(manifest), "manifest_sha256": sha(manifest),
        "source_path": source_path, "source_digest": case["source_digest"], "predecessor_unchanged": True}
    save_once(local / "staging-verification.json", summary)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
