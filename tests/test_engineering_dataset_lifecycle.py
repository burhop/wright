"""Lease observations project uncertainty without rewriting canonical evidence."""

from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


def module(name):
    path = Path(__file__).resolve().parents[1] / "scripts" / (name + ".py")
    spec = importlib.util.spec_from_file_location(
        "scripts." + name + "_lifecycle_test", path
    )
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


runner_module = module("run_engineering_dataset_campaign")
campaign_module = module("engineering_dataset_campaign")
evidence = runner_module._evidence


def sha(data):
    return hashlib.sha256(data).hexdigest()


@pytest.fixture
def prepared(tmp_path):
    inputs = tmp_path / "inputs"
    templates = tmp_path / "templates"
    templates.mkdir()
    source = b"isolated lifecycle test source"
    (templates / "unit-template.workflow.wflow").write_bytes(source)
    directory = inputs / "scenarios/unit-template/unit-template-01"
    directory.mkdir(parents=True)
    for name in ("profile.md", "prompt.txt", "context.md", "sketch.svg"):
        (directory / name).write_text("Synthetic unit input " + name)
    manifest = {
        "schema_version": 1,
        "template_id": "unit-template",
        "scenario_id": "unit-template-01",
        "title": "Unit lifecycle evidence",
        "difficulty": "basic",
        "provenance": {"kind": "synthetic"},
        "files": {
            "user_profile": "profile.md",
            "prompt": "prompt.txt",
            "context": ["context.md"],
            "images": ["sketch.svg"],
        },
        "expected_outputs": [{"role": "generated", "patterns": ["result.json"]}],
    }
    (directory / "scenario.json").write_text(json.dumps(manifest))
    config = {
        "campaign_id": "unit-campaign",
        "approval_mode": "auto",
        "target": 30,
        "template_ids": ["unit-template"],
    }
    (inputs / "campaign.json").write_text(json.dumps(config))
    campaign = campaign_module.Campaign(inputs, tmp_path / "campaign", templates)
    campaign.scan()
    dataset = campaign.status()["datasets"][0]
    workspace = tmp_path / "workspace"
    (workspace / "workflows").mkdir(parents=True)
    (workspace / "workflows/example.workflow.wflow").write_bytes(source)
    case = {
        "scenario_id": "unit-template-01",
        "attempt_id": "attempt-01",
        "session_id": "unit-session",
        "workspace_root": str(workspace),
        "source_path": "workflows/example.workflow.wflow",
        "source_digest": sha(source),
        "dataset_digest": dataset["digest"],
        "template_digest": dataset["template_digest"],
        "required_step_ids": ["task"],
        "output_root": "campaign/unit/attempt/artifacts",
        "integration_policy_digest": "b" * 64,
    }
    start = (datetime.now(timezone.utc) - timedelta(seconds=2)).isoformat()
    relative_log = "runs/example/run.json"
    record = {
        "run_id": "run-1",
        "workflow_path": case["source_path"],
        "source_digest": case["source_digest"],
        "status": "running",
        "started_at": start,
        "required_step_ids": ["task"],
        "execution_context": {
            "dataset_id": case["scenario_id"],
            "dataset_digest": case["dataset_digest"],
            "source_digest": case["source_digest"],
            "source_path": case["source_path"],
            "output_root": case["output_root"],
            "execution_kind": "integration",
            "campaign_id": "unit-campaign",
            "actor": "integration_test:unit-campaign",
            "integration_policy_digest": case["integration_policy_digest"],
            "workspace_id": "workspace-1",
            "input_files": {"inputs/prompt.txt": "c" * 64},
            "test_destinations": [],
        },
        "events": [
            {
                "kind": "run_started",
                "run_id": "run-1",
                "run_log_path": relative_log,
                "at": start,
            },
            {"kind": "step_started", "task_id": "task", "at": start},
        ],
    }
    path = workspace / relative_log
    runner_module.atomic_json(path, record)
    response = {
        "workspace_id": "workspace-1",
        "workflow_path": case["source_path"],
        "runs": [
            {
                "path": relative_log,
                "run_id": None,
                "status": "interrupted",
                "started_at": start,
                "source_digest": case["source_digest"],
                "source_matches_current": True,
                "execution": {"event_count": 2},
            }
        ],
    }
    args = {
        "workspace_root": workspace,
        "export_root": campaign.root / "output",
        "scenario_id": case["scenario_id"],
        "attempt_id": case["attempt_id"],
        "dataset_digest": case["dataset_digest"],
        "template_digest": case["template_digest"],
        "definition_digest": case["source_digest"],
        "required_step_ids": case["required_step_ids"],
        "output_root": case["output_root"],
    }
    return case, record, path, response, args, campaign


def observation(prepared, response=None):
    case, record, path, original, _, _ = prepared
    return evidence.lifecycle_observation(
        record,
        path.relative_to(case["workspace_root"]).as_posix(),
        sha(path.read_bytes()),
        original if response is None else response,
        runner_module.now(),
    )


class ReadOnlyTransport:
    def __init__(self, response):
        self.response, self.requests, self.available = response, [], True

    def request(self, path, body=None, **kwargs):
        assert body is None, "Lifecycle recovery must never replay an operation"
        assert path.startswith("/api/workspace/workflow-sources/runs?")
        self.requests.append(path)
        return {"ok": self.available, "data": deepcopy(self.response)}


@pytest.mark.parametrize("run_id", [None, "run-1"])
def test_exact_api_interruption_retains_raw_and_never_asserts_completion(
    prepared, run_id
):
    _, _, path, response, args, campaign = prepared
    response["runs"][0]["run_id"] = run_id
    raw = path.read_bytes()
    proof = observation(prepared)
    receipt = evidence.export_run_evidence(path, **args, lifecycle=proof)
    assert receipt["status"] == "outcome_unknown"
    assert receipt["raw_runtime_status"] == "running"
    assert receipt["accepted_by_runtime"] is True
    assert (
        receipt["terminal_step_reached"]
        is receipt["all_required_steps_succeeded"]
        is False
    )
    assert receipt["finished_at"] is None
    assert receipt["produced_files"] == []
    assert path.read_bytes() == raw
    assert receipt["runtime_evidence"]["sha256"] == sha(raw)
    target = args["export_root"] / args["scenario_id"] / args["attempt_id"]
    sidecar = target / receipt["lifecycle_evidence"]["path"]
    assert sha(sidecar.read_bytes()) == receipt["lifecycle_evidence"]["sha256"]
    assert json.loads(sidecar.read_bytes()) == proof
    assert proof["matching_mode"] == (
        "run_id_and_log_source_start"
        if run_id
        else "log_source_start_run_id_unavailable"
    )
    campaign.scan()
    assert list(campaign.status()["metrics"].values()) == [1, 1, 0, 0]


@pytest.mark.parametrize(
    "change",
    [
        lambda r: r.update(workspace_id="other"),
        lambda r: r.update(workflow_path="other.workflow.wflow"),
        lambda r: r["runs"][0].update(run_id="other"),
        lambda r: r["runs"][0].update(source_digest="f" * 64),
        lambda r: r["runs"][0].update(path="runs/other/run.json"),
        lambda r: r["runs"][0].update(started_at="2020-01-01T00:00:00+00:00"),
        lambda r: r["runs"][0].update(source_matches_current=False),
        lambda r: r["runs"][0]["execution"].update(event_count=3),
        lambda r: r["runs"].append(deepcopy(r["runs"][0])),
        lambda r: r["runs"][0].update(status="completed"),
        lambda r: r["runs"][0].update(status="failed"),
    ],
)
def test_mismatched_or_terminal_api_projection_is_rejected(prepared, change):
    response = deepcopy(prepared[3])
    change(response)
    with pytest.raises(evidence.EvidenceError):
        observation(prepared, response)


def test_no_actual_start_cannot_project_a_run(prepared):
    prepared[1]["events"].pop(0)
    with pytest.raises(evidence.EvidenceError, match="run_started"):
        observation(prepared)


@pytest.mark.parametrize(
    "change",
    [
        lambda o: o["runtime_evidence"].update(sha256="e" * 64),
        lambda o: o.update(matched_run_id="other"),
        lambda o: o.update(observed_at="2020-01-01T00:00:00+00:00"),
        lambda o: o.update(observed_at="2099-01-01T00:00:00+00:00"),
        lambda o: o["run"].update(status="completed"),
    ],
)
def test_exporter_revalidates_sidecar_claims(prepared, change):
    proof = observation(prepared)
    change(proof)
    with pytest.raises(evidence.EvidenceError):
        evidence.export_run_evidence(prepared[2], **prepared[4], lifecycle=proof)
    assert not list(prepared[4]["export_root"].rglob("*.json"))


def test_changed_raw_snapshot_cannot_use_prior_api_observation(prepared):
    proof = observation(prepared)
    record, path = prepared[1:3]
    record["unrelated_metadata"] = "new bytes invalidate prior binding"
    runner_module.atomic_json(path, record)
    with pytest.raises(evidence.EvidenceError, match="immutable run snapshot"):
        evidence.export_run_evidence(path, **prepared[4], lifecycle=proof)


def test_absent_lifecycle_cannot_erase_published_interruption(prepared):
    path, args = prepared[2], prepared[4]
    receipt = evidence.export_run_evidence(
        path, **args, lifecycle=observation(prepared)
    )
    target = args["export_root"] / args["scenario_id"] / args["attempt_id"] / "run.json"
    with pytest.raises(evidence.EvidenceError, match="Matched lifecycle evidence"):
        evidence.export_run_evidence(path, **args)
    assert json.loads(target.read_bytes()) == receipt


def test_real_runner_export_and_ledger_update_only_on_changed_evidence(
    prepared, tmp_path
):
    case, _, path, response, args, campaign = prepared
    transport = ReadOnlyTransport(response)
    runner = runner_module.Runner(
        state_root=tmp_path / "runner",
        export_root=args["export_root"],
        transport=transport,
    )
    state, state_path = {}, tmp_path / "runner/attempt.json"
    raw = path.read_bytes()
    response["runs"][0]["status"] = "running"
    runner.observe(case, state, state_path, force_lifecycle=True)
    campaign.scan()
    first = campaign.status()
    assert first["datasets"][0]["latest_status"] == "running"
    response["runs"][0]["status"] = "interrupted"
    runner.observe(case, state, state_path, force_lifecycle=True)
    campaign.scan()
    interrupted = campaign.status()
    assert interrupted["datasets"][0]["latest_status"] == "outcome_unknown"
    assert len(interrupted["history"]) == len(first["history"]) + 1
    target = args["export_root"] / case["scenario_id"] / case["attempt_id"]
    receipt_bytes = (target / "run.json").read_bytes()
    sidecars = sorted((target / "lifecycle").glob("*.json"))
    # New observation times and unavailable API do not grow status history.
    runner.observe(case, state, state_path, force_lifecycle=True)
    transport.available = False
    runner.observe(case, state, state_path, force_lifecycle=True)
    campaign.scan()
    assert campaign.status()["history"] == interrupted["history"]
    assert (target / "run.json").read_bytes() == receipt_bytes
    assert sorted((target / "lifecycle").glob("*.json")) == sidecars
    # A later exact positive owner observation removes only the uncertainty projection.
    transport.available = True
    response["runs"][0]["status"] = "running"
    runner.observe(case, state, state_path, force_lifecycle=True)
    campaign.scan()
    live = campaign.status()
    assert live["datasets"][0]["latest_status"] == "running"
    assert len(live["history"]) == len(interrupted["history"]) + 1
    assert live["metrics"] == interrupted["metrics"] == first["metrics"]
    assert list(live["metrics"].values()) == [1, 1, 0, 0]
    assert path.read_bytes() == raw
    assert not live["issues"]


def test_periodic_reads_are_bounded_but_forced_observation_refreshes(
    prepared, tmp_path
):
    case, _, _, response, args, _ = prepared
    transport = ReadOnlyTransport(response)
    runner = runner_module.Runner(
        state_root=tmp_path / "runner",
        export_root=args["export_root"],
        transport=transport,
    )
    state, state_path = {}, tmp_path / "runner/attempt.json"
    runner.observe(case, state, state_path)
    runner.observe(case, state, state_path)
    assert len(transport.requests) == 1
    runner.observe(case, state, state_path, force_lifecycle=True)
    assert len(transport.requests) == 2


def test_restart_observes_interruption_without_replaying_start(
    prepared, tmp_path, monkeypatch
):
    case, _, path, response, args, _ = prepared
    # Input contract validation is independently tested; this isolates lifecycle restart.
    monkeypatch.setattr(runner_module._bindings, "validate_case", lambda value: None)
    transport = ReadOnlyTransport(response)
    runner = runner_module.Runner(
        state_root=tmp_path / "runner",
        export_root=args["export_root"],
        transport=transport,
    )
    raw = path.read_bytes()
    result = runner.run_case(case)
    assert result["phase"] == "outcome_unknown"
    assert result["reason_code"] == "runtime_owner_missing"
    assert result["last_receipt_status"] == "outcome_unknown"
    assert result["operations"] == {}
    assert len(transport.requests) == 1
    assert path.read_bytes() == raw


def test_ended_start_future_forces_exact_lifecycle_read(
    prepared, tmp_path, monkeypatch
):
    case, record, path, response, args, _ = prepared
    monkeypatch.setattr(runner_module._bindings, "validate_case", lambda value: None)
    path.unlink()  # Isolated unit fixture: the test transport persists the actual start.

    class StartThenInterrupt(ReadOnlyTransport):
        posts = 0

        def request(self, request_path, body=None, **kwargs):
            if body is None:
                return super().request(request_path, body, **kwargs)
            assert request_path == "/api/workspace/workflow-sources/run"
            self.posts += 1
            runner_module.atomic_json(path, record)
            return {"ok": True, "data": {}}

    transport = StartThenInterrupt(response)
    runner = runner_module.Runner(
        state_root=tmp_path / "runner",
        export_root=args["export_root"],
        transport=transport,
        poll_seconds=0.001,
        minimum_free_bytes=1,
    )
    result = runner.run_case(case)
    assert result["phase"] == "outcome_unknown"
    assert result["reason_code"] == "runtime_owner_missing"
    assert transport.posts == 1
    # The forced read after the HTTP future finishes is required. Depending on
    # thread scheduling, a preliminary raw observation may also perform a read.
    assert len(transport.requests) in {1, 2}
    assert result["operations"]["start"]["state"] == "response_received"
