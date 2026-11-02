import importlib.util
import hashlib
import json
import sqlite3
from pathlib import Path

import pytest

from workspace_service.workflow_run_record import recent_workflow_runs
from workspace_service.workflow_trace.canonical import build_canonical_trace


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "prepare-workflow-trace-review-workspace.py"
SPEC = importlib.util.spec_from_file_location("trace_review_workspace", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_prepares_real_run_history_without_changing_campaign_record(
    tmp_path: Path, monkeypatch
) -> None:
    bundle = tmp_path / "campaign"
    attempt = bundle / "output" / "example-01" / "attempt-003"
    artifacts = attempt / "artifacts"
    artifacts.mkdir(parents=True)
    (artifacts / "result.png").write_bytes(b"image")
    record = {
        "schema_version": 1,
        "scenario_id": "example-01",
        "attempt_id": "attempt-003",
        "run_id": "run-1",
        "status": "completed",
        "started_at": "2026-09-16T10:00:00+00:00",
        "finished_at": "2026-09-16T10:01:00+00:00",
        "required_step_ids": ["make_result"],
        "step_events": [
            {
                "kind": "step_started",
                "at": "2026-09-16T10:00:00+00:00",
                "task_id": "make_result",
            },
            {
                "kind": "step_completed",
                "at": "2026-09-16T10:01:00+00:00",
                "task_id": "make_result",
            },
        ],
        "produced_files": [
            {
                "artifact_id": "artifact-1",
                "path": "result.png",
                "sha256": "0" * 64,
                "size_bytes": 5,
                "task_id": "make_result",
                "artifact_role": "deliverable",
            }
        ],
    }
    original = json.dumps(record, indent=2).encode()
    (attempt / "run.json").write_bytes(original)
    selection = tmp_path / "selection.json"
    selection.write_text(
        json.dumps(
            {
                "selection": [
                    {
                        "case_id": "example-01",
                        "attempt_id": "attempt-003",
                        "run_path": "output/example-01/attempt-003/run.json",
                    }
                ]
            }
        )
    )
    templates = tmp_path / "templates"
    templates.mkdir()
    (templates / "example.workflow.wflow").write_text(
        'workflow example\n  name: "Example"\nend\n'
    )
    monkeypatch.setattr(MODULE, "TEMPLATE_ROOT", templates)

    workspace = tmp_path / "review"
    index = MODULE.prepare(bundle, workspace, selection)

    assert index["indexed_runs"] == 1
    assert (attempt / "run.json").read_bytes() == original
    history = recent_workflow_runs(workspace, "workflows/example-01.workflow.wflow")
    assert history[0]["status"] == "completed"
    imported = json.loads((workspace / history[0]["path"]).read_text())
    trace = build_canonical_trace(
        imported,
        workspace_id="review-workspace",
        session_id="review-session",
        path=history[0]["path"],
    )
    assert trace["run"]["state"] == "succeeded"
    assert trace["final_outputs"][0]["artifact"]["workspace_path"] == (
        "runs/example-01/artifacts/result.png"
    )
    assert (workspace / "runs/example-01/artifacts/result.png").read_bytes() == b"image"


@pytest.mark.parametrize("changed", [False, True])
def test_recovers_only_digest_matched_original_dataset_inputs(
    tmp_path, monkeypatch, changed
):
    inputs = tmp_path / "inputs"
    source = inputs / "example" / "prompt.txt"
    source.parent.mkdir(parents=True)
    prompt = b"Make a six-scallop telescope focus wheel."
    source.write_bytes(b"A later, different request." if changed else prompt)
    monkeypatch.setattr(MODULE, "INPUT_ROOT", inputs)
    manifest = {"scenario_id": "example-01", "files": {"prompt": "prompt.txt"}}
    hashes = {"prompt.txt": hashlib.sha256(prompt).hexdigest()}
    digest = hashlib.sha256(
        json.dumps({"manifest": manifest, "files": hashes}, sort_keys=True).encode()
    ).hexdigest()
    revision = {
        **manifest,
        "input_hashes": hashes,
        "digest": digest,
        "template_digest": "t" * 64,
        "path": "example",
    }
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    with sqlite3.connect(bundle / "campaign.sqlite3") as database:
        database.execute(
            "CREATE TABLE dataset_revisions (fingerprint TEXT, document TEXT)"
        )
        database.execute(
            "INSERT INTO dataset_revisions VALUES (?, ?)",
            (digest + "/" + "t" * 64, json.dumps(revision)),
        )
    record = {
        "scenario_id": "example-01",
        "attempt_id": "attempt-003",
        "dataset_digest": digest,
        "template_digest": "t" * 64,
    }
    workspace = tmp_path / "workspace"
    original_db = (bundle / "campaign.sqlite3").read_bytes()
    recovered = MODULE._recover_input_pack(bundle, workspace, record)
    assert (bundle / "campaign.sqlite3").read_bytes() == original_db
    assert recovered["unavailable"] == (["prompt.txt"] if changed else [])
    assert len(recovered["files"]) == (0 if changed else 1)
    if not changed:
        imported = workspace / "runs/example-01/inputs/attempt-003/prompt.txt"
        assert imported.read_bytes() == prompt
        source.write_bytes(b"Edited after recovery")
        assert imported.read_bytes() == prompt
    assert (
        MODULE._recover_input_pack(
            bundle, workspace, {**record, "dataset_digest": "x" * 64}
        )
        is None
    )
    revision["input_hashes"]["prompt.txt"] = "f" * 64
    with sqlite3.connect(bundle / "campaign.sqlite3") as database:
        database.execute(
            "UPDATE dataset_revisions SET document = ?", (json.dumps(revision),)
        )
    with pytest.raises(ValueError, match="does not match the executed dataset"):
        MODULE._recover_input_pack(bundle, workspace, record)


def test_review_supplements_keep_reconstruction_separate_from_execution(tmp_path):
    case, attempt = "printed-replacement-part-01", "attempt-003"
    root = tmp_path / "runs" / case / "inputs" / attempt
    root.mkdir(parents=True)
    (root / "context.md").write_text("Design context\n")
    (root / "user-profile.md").write_text("Requester profile\n")
    record = {
        "scenario_id": case,
        "attempt_id": attempt,
        "required_step_ids": ["create_mesh_example"],
    }
    pack = {
        "files": [
            {"path": name, "artifact_id": name}
            for name in ("context.md", "user-profile.md")
        ]
    }
    supplements = MODULE._review_supplements(tmp_path, record, pack)
    context, checkpoint = supplements
    data = (
        tmp_path / "runs" / case / "review-sources" / attempt / context["path"]
    ).read_bytes()
    assert data == b"Requester profile\n\n\nDesign context\n"
    assert context["sha256"] == hashlib.sha256(data).hexdigest()
    assert context["artifact_role"] == "input_reconstruction"
    assert context["source_artifact_ids"] == ["user-profile.md", "context.md"]
    assert (
        "original assembled execution snapshot was not transferred"
        in context["provenance"]
    )
    assert checkpoint["software"] == "Blender"
    assert checkpoint["node_id"] == "create_mesh_example"
    assert checkpoint["artifact_role"] == "source_document"
    assert (
        MODULE._review_supplements(
            tmp_path, {**record, "attempt_id": "attempt-099"}, None
        )
        == []
    )
    assert len(MODULE._review_supplements(tmp_path, record, {"files": []})) == 1


def test_review_supplements_retain_cfd_visualizations_with_field_provenance(tmp_path):
    case, attempt = "raspberry-pi-enclosure-01", "attempt-032"
    bundle = tmp_path / "bundle"
    visuals = bundle / "visuals" / "ai-cfd-essay"
    visuals.mkdir(parents=True)
    (visuals / "raspberry-pi-enclosure-velocity-comparison.png").write_bytes(
        b"velocity-png"
    )
    (visuals / "raspberry-pi-enclosure-temperature-comparison.png").write_bytes(
        b"temperature-png"
    )
    record = {
        "scenario_id": case,
        "attempt_id": attempt,
        "required_step_ids": [
            "collect_cfd_results_raspberry_pi_enclosure_01_attempt_032"
        ],
        "produced_files": [
            {"path": "cfd-comparison.json", "artifact_id": "comparison"},
            {"path": "cfd-fields.zip", "artifact_id": "fields"},
        ],
    }

    supplements = MODULE._review_supplements(tmp_path, record, None, bundle)

    assert [item["title"] for item in supplements] == [
        "Airflow comparison",
        "Temperature comparison",
    ]
    assert all(item["artifact_role"] == "review_visualization" for item in supplements)
    assert all(
        item["source_artifact_ids"] == ["comparison", "fields"] for item in supplements
    )
    assert all(
        item["node_id"].startswith("collect_cfd_results") for item in supplements
    )
    assert all(
        "not an original solver screenshot" in item["provenance"]
        for item in supplements
    )
    retained = tmp_path / "runs" / case / "review-sources" / attempt
    assert (retained / supplements[0]["path"]).read_bytes() == b"velocity-png"
