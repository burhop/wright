import asyncio
import json
import pytest
from workspace_service.workflow_campaign import inventory, verify_output, run_campaign
from packages.workspace_service.tests.test_workflow_source_execution import (
    source,
    task,
    HTML,
)


def test_inventory_does_not_invent_workflows_and_ids_survive_prompt_edits(tmp_path):
    folder = tmp_path / "workflows"
    folder.mkdir()
    f = folder / "example.workflow.wflow"
    f.write_text(source(task()))
    first = inventory(tmp_path)
    assert first["target"] == 100 and len(first["cases"]) == 1
    assert first["cases"][0]["authored"] and not first["cases"][0]["runnable"]
    f.write_text(source(task(prompt="Different prompt")))
    second = inventory(tmp_path)
    assert first["cases"][0]["id"] == second["cases"][0]["id"]
    assert first["cases"][0]["source_sha256"] != second["cases"][0]["source_sha256"]


def test_output_oracle_rejects_a_successfully_named_but_invalid_cad_file(tmp_path):
    f = tmp_path / "part.step"
    f.write_bytes(b"the model says it created a part")
    with pytest.raises(ValueError, match="STEP"):
        verify_output(
            tmp_path, {"output_path": "part.step", "output_bytes": f.stat().st_size}
        )
    f = tmp_path / "report.html"
    f.write_text(HTML)
    assert verify_output(
        tmp_path, {"output_path": "report.html", "output_bytes": f.stat().st_size}
    )["passed"]


def test_campaign_budget_rejected_before_opening_client_or_running(tmp_path):
    manifest = {
        "workspace": str(tmp_path),
        "cases": [{"id": "a", "compiles": True, "model_call_bound": 30}],
    }
    with pytest.raises(ValueError, match="budget"):
        asyncio.run(
            run_campaign(
                manifest,
                ids=["a"],
                api="",
                session="",
                output_dir=tmp_path,
                max_model_calls=2,
            )
        )
    assert not list(tmp_path.iterdir())


def test_image_export_oracle_checks_actual_format_and_recorded_digest(tmp_path):
    import base64
    import hashlib

    data = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aD1sAAAAASUVORK5CYII="
    )
    path = tmp_path / "preview.png"
    path.write_bytes(data)
    output = {
        "output_path": path.name,
        "output_bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }
    assert verify_output(tmp_path, output)["passed"]
    path.write_bytes(data[:-1] + b"x")
    with pytest.raises(ValueError, match="digest"):
        verify_output(tmp_path, output)
    path.write_bytes(b"Not an image")
    with pytest.raises(ValueError, match="contents match"):
        verify_output(
            tmp_path, {"output_path": path.name, "output_bytes": path.stat().st_size}
        )


def test_existing_scenarios_are_planned_not_counted_as_authored(tmp_path):
    data = inventory(tmp_path)
    assert data["cases"] == []
    assert len(data["planned_cases"]) == 4
    bracket = next(
        c for c in data["planned_cases"] if c["id"] == "SCENARIO-structural-bracket"
    )
    assert not bracket["runnable"] and not bracket["authored"]
    assert any(
        a["rule"].get("maximum") == 120 for a in bracket["verification_criteria"]
    )


def test_missing_original_fixture_is_a_recorded_failure_not_an_aborted_campaign(
    tmp_path,
):
    from workspace_service.workflow_campaign import run_case

    case = {
        "id": "copy",
        "source_sha256": "abc",
        "inputs": [{"path": "missing.psm", "preserve": True}],
    }
    result = asyncio.run(
        run_case(case, root=tmp_path, api="", session="", timeout=10, client=None)
    )
    assert result["status"] == "failed" and result["completed_at"]


def test_dashboard_does_not_treat_past_evidence_as_current_run_readiness(tmp_path):
    import importlib.util
    from pathlib import Path

    module_path = (
        Path(__file__).resolve().parents[3] / "scripts/workflow_campaign_dashboard.py"
    )
    spec = importlib.util.spec_from_file_location(
        "campaign_dashboard_test", module_path
    )
    dashboard = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(dashboard)
    folder = tmp_path / "workflows"
    folder.mkdir()
    (folder / "test.workflow.wflow").write_text(source(task()))
    manifest = inventory(tmp_path)
    case = manifest["cases"][0]
    (tmp_path / "manifest.json").write_text(json.dumps(manifest))
    (tmp_path / "attempts").mkdir()
    (tmp_path / "attempts/past.json").write_text(
        json.dumps(
            {
                "id": "past",
                "case_id": case["id"],
                "source_sha256": case["source_sha256"],
                "status": "structure_verified",
                "started_at": "2026-09-07T00:00:00Z",
            }
        )
    )
    data = dashboard.read_campaign(tmp_path)
    assert data["cases"][0]["verified_on_revision"]
    assert not data["cases"][0]["runnable"]
    assert data["cases"][0]["readiness"] == "Preflight needed"
    assert "Evidence for this revision" in dashboard.render_campaign(data)
