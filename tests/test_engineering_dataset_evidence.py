"""Adversarial export checks; synthetic unit records never enter real ledger."""
from datetime import datetime, timedelta, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path

import pytest

MODULE = Path(__file__).resolve().parents[1] / "scripts/engineering_dataset_evidence.py"
spec = importlib.util.spec_from_file_location("dataset_evidence", MODULE)
evidence = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evidence)


def sha(data):
    return hashlib.sha256(data).hexdigest()


@pytest.fixture
def case(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    source = b"canonical full source identity"
    (workspace / "definition.workflow.wflow").write_bytes(source)
    root = "campaign/case/attempt/artifacts"
    output = workspace / root / "mesh.stl"
    output.parent.mkdir(parents=True)
    output.write_bytes(b"real-tool-output-unit-fixture")
    started = (datetime.now(timezone.utc)-timedelta(seconds=2)).isoformat()
    ended = datetime.now(timezone.utc).isoformat()
    artifact = {"id":"run-1:mesh:mesh-out", "kind":"file", "name":"mesh",
                "artifact_role":"deliverable", "provenance":{"run_id":"run-1","task_id":"mesh","output_port":"mesh-out"},
                "representations":[{"kind":"workspace_file","location":root+"/mesh.stl","format":"stl","durability":"persistent","sha256":sha(output.read_bytes()),"size_bytes":output.stat().st_size}]}
    record = {"run_id":"run-1", "workflow_path":"definition.workflow.wflow", "source_digest":sha(source),
        "started_at":started,"completed_at":ended,"status":"completed","required_step_ids":["mesh"],
        "execution_context":{"dataset_id":"case-01","dataset_digest":"a"*64,"source_digest":sha(source),
             "source_path":"definition.workflow.wflow","output_root":root,"execution_kind":"integration",
             "campaign_id":"campaign","actor":"integration_test:campaign","integration_policy_digest":"b"*64,
             "input_files":{"inputs/prompt.txt":"c"*64},"test_destinations":[]},
        "events":[{"kind":"run_started","run_id":"run-1","run_log_path":"runs/example/run.json","at":started},
                  {"kind":"step_started","task_id":"mesh","at":started,"arguments":{"api_key":"secret-never-export"}},
                  {"kind":"result_ready","task_id":"mesh","at":ended,"engineering_result":artifact},
                  {"kind":"step_completed","task_id":"mesh","at":ended},
                  {"kind":"run_completed","run_id":"run-1","at":ended,"required_steps_completed":["mesh"]}],
        "result":{"run_id":"run-1","status":"completed","steps":[{"task_id":"mesh","execution_kind":"mcp_task"}],"results":[artifact]},
    }
    path = workspace / "runs/example/run.json"
    path.parent.mkdir(parents=True)
    args = dict(workspace_root=workspace, export_root=tmp_path/"exports", scenario_id="case-01", attempt_id="attempt-01",
                dataset_digest="a"*64, template_digest="d"*64, definition_digest=sha(source), required_step_ids=["mesh"], output_root=root)
    def export():
        path.write_text(json.dumps(record))
        return evidence.export_run_evidence(path, **args)
    return record, args, output, export


def test_export_derives_receipt_and_copies_exact_actual_artifact(case):
    record, args, output, export = case
    receipt = export()
    assert receipt["accepted_by_runtime"] is True
    assert receipt["all_required_steps_succeeded"] is True
    assert receipt["terminal_step_reached"] is True
    assert receipt["content_validated"] is False
    destination = args["export_root"] / "case-01/attempt-01"
    assert (destination/"artifacts/mesh.stl").read_bytes() == output.read_bytes()
    assert "secret-never-export" not in (destination/"run.json").read_text()
    assert export() == receipt


def test_export_persists_available_model_usage_and_keeps_missing_unknown(case):
    record, _, _, export = case
    unknown = export()
    assert unknown["usage"] == {
        "status": "unknown",
        "request_count": 0,
        "reported_request_count": 0,
        "models": [],
        "input_tokens": None,
        "cached_input_tokens": None,
        "output_tokens": None,
        "reasoning_output_tokens": None,
        "total_tokens": None,
    }

    # Use a fresh immutable attempt destination for the populated projection.
    record["events"].insert(
        -1,
        {
            "kind": "model_usage",
            "task_id": "mesh",
            "at": record["completed_at"],
            "usage": {
                "status": "reported",
                "model": "gpt-5.6-sol",
                "input_tokens": 120,
                "cached_input_tokens": 80,
                "output_tokens": 12,
                "reasoning_output_tokens": 3,
                "total_tokens": 132,
            },
        },
    )
    case[1]["attempt_id"] = "attempt-usage"
    populated = export()
    assert populated["usage"] == {
        "status": "reported",
        "request_count": 1,
        "reported_request_count": 1,
        "models": ["gpt-5.6-sol"],
        "input_tokens": 120,
        "cached_input_tokens": 80,
        "output_tokens": 12,
        "reasoning_output_tokens": 3,
        "total_tokens": 132,
    }


@pytest.mark.parametrize("mutation,match", [
    (lambda r: r["events"].pop(0), "run_started"),
    (lambda r: r["events"][0].update(run_id="other"), "run_started"),
    (lambda r: r["events"].pop(3), "before all steps"),
    (lambda r: r["events"].pop(), "terminal evidence"),
    (lambda r: r["result"].update(steps=[]), "omits"),
    (lambda r: r.update(required_step_ids=["mesh","unexecuted"]), "required step set"),
    (lambda r: r["execution_context"].update(dataset_digest="e"*64), "execution context"),
    (lambda r: r["events"][2]["engineering_result"]["provenance"].update(run_id="other"), "Cross-run"),
    (lambda r: r["execution_context"]["input_files"].update({"input.stl":r["result"]["results"][0]["representations"][0]["sha256"]}), "Input copy"),
])
def test_rejects_unproven_or_mismatched_execution(case, mutation, match):
    record, args, _, export = case
    mutation(record)
    with pytest.raises(evidence.EvidenceError, match=match):
        export()
    assert not args["export_root"].exists()


def test_rejects_current_file_hash_drift(case):
    _, _, output, export = case
    output.write_bytes(b"changed artifact")
    with pytest.raises(evidence.EvidenceError, match="hash or size"):
        export()


def test_rejects_precreated_output(case):
    _, _, output, export = case
    os.utime(output, (1,1))
    with pytest.raises(evidence.EvidenceError, match="predates"):
        export()


def test_running_record_counts_acceptance_but_never_completion(case):
    record, _, _, export = case
    record.update(status="running")
    record.pop("result")
    record["events"] = record["events"][:2]
    receipt = export()
    assert receipt["accepted_by_runtime"] is True
    assert receipt["terminal_step_reached"] is False
    assert receipt["all_required_steps_succeeded"] is False
    assert receipt["produced_files"] == []


def test_receipt_requires_dispatched_action_evidence(case):
    record, _, _, export = case
    record["events"][2]["engineering_result"]["artifact_role"] = "external_action_receipt"
    with pytest.raises(evidence.EvidenceError, match="dispatched"):
        export()


def test_artifact_cannot_escape_declared_attempt(case):
    record, _, _, export = case
    record["events"][2]["engineering_result"]["representations"][0]["location"] = "../outside.stl"
    with pytest.raises(evidence.EvidenceError, match="escapes"):
        export()


@pytest.mark.parametrize("change,passes", [(None,True),("real_destination",False),("real_dispatch",False)])
def test_only_exact_dispatched_test_receipt_is_exported(case, change, passes):
    record, _, output, export = case
    context = record["execution_context"]
    context["test_destinations"] = ["test://campaign/printer/case-01"]
    receipt = {"integration_test":True,"simulated_handoff":True,"network_dispatch":False,
               "run_id":"run-1","step_id":"mesh","dataset_id":"case-01","campaign_id":"campaign",
               "integration_policy_digest":"b"*64,"checkpoint_id":"checkpoint","subject_digest":"f"*64,"action_id":"action-1",
               "destination":{"kind":"integration_test","id":"test://campaign/printer/case-01"}}
    if change == "real_destination":
        receipt["destination"]["id"] = "printer://real-device"
    if change == "real_dispatch":
        receipt["network_dispatch"] = True
    output.write_text(json.dumps(receipt))
    artifact = record["events"][2]["engineering_result"]
    artifact["artifact_role"] = "external_action_receipt"
    artifact["representations"][0].update(sha256=sha(output.read_bytes()),size_bytes=output.stat().st_size)
    representation = artifact["representations"][0]
    record["result"]["steps"][0].update(execution_kind="approval",checkpoint_id="checkpoint",subject_digest="f"*64,
        external_action={"outcome":"dispatched","action_id":"action-1","evidence":{"operation":"test_handoff","integration_test":True,
            "simulated_handoff":True,"produced_files":[{"output_path":representation["location"],
            "sha256":representation["sha256"],"output_bytes":representation["size_bytes"]}]}})
    if passes:
        assert export()["external_effects"] == "test_destinations"
    else:
        with pytest.raises(evidence.EvidenceError, match="(destination|isolated)"):
            export()


def test_safe_runtime_blocker_survives_export_without_credentials(case):
    record,_,_,export=case
    record.update(status="failed",code="TASK_BLOCKED",
        error='Create source mesh: safe mode rejects required file I/O; api_key="secret-key" Authorization: Bearer secret-token')
    record["events"].pop()
    receipt=export()
    assert receipt["error_code"] == "TASK_BLOCKED"
    assert "safe mode rejects required file I/O" in receipt["error"]
    assert "secret-key" not in receipt["error"] and "secret-token" not in receipt["error"]
    assert receipt["status"] == "failed" and receipt["terminal_step_reached"] is False


@pytest.mark.parametrize("status", ["running", "failed"])
def test_input_copy_excluded_without_hiding_actual_noncompleted_status(case, status):
    record, args, _, export = case
    record.update(status=status)
    record["events"].pop()
    representation = record["events"][2]["engineering_result"]["representations"][0]
    record["execution_context"]["input_files"]["inputs/source.py"] = representation["sha256"]
    receipt = export()
    assert receipt["status"] == status
    assert receipt["accepted_by_runtime"] is True
    assert receipt["produced_files"] == []
    assert receipt["excluded_artifacts"][0]["reason_code"] == "input_copy"
    assert receipt["terminal_step_reached"] is False
    assert receipt["all_required_steps_succeeded"] is False
    assert not (args["export_root"] / "case-01/attempt-01/artifacts/mesh.stl").exists()
