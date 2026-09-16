from __future__ import annotations

import asyncio
import csv as csv_module
import json
from pathlib import Path

from api import composition
from api.routers import workspace as workspace_router
from core.process_validation import Assessment
from workspace_service.workflow_source_execution import (
    compile_prompt_workflow,
    execute_prompt_workflow,
)


ROOT = Path(__file__).parents[2]
PROCESS = (
    ROOT
    / "tests"
    / "datasets"
    / "process-validation"
    / "processes"
    / "structured-loop.workflow.wflow"
)


def test_served_validator_run_exposes_actionable_and_human_readable_evidence(
    offline_api_client, tmp_path: Path, monkeypatch
) -> None:
    """Run the canonical validator, then consume its evidence through FastAPI."""

    service = composition.workspace_service()
    database = service.db_path
    workspace = tmp_path / "process-validation-workspace"
    workspace.mkdir()
    service.repository.create(
        "validation-workspace",
        "validation-session",
        str(workspace),
        workspace_name="Process validation",
    )
    monkeypatch.setattr(workspace_router, "DATABASE_PATH", database)
    # The managed test root is inside the checkout. Keep the production path
    # guard covered by the security suite while allowing this isolated fixture
    # workspace to exercise the served API boundary.
    monkeypatch.setattr(
        service,
        "ensure_workspace_path_safe",
        lambda local_path: str(Path(local_path).resolve()),
    )

    plan = compile_prompt_workflow(PROCESS.read_text(encoding="utf-8"))
    events: list[dict] = []
    json_attempt = 0

    async def generate(prompt: str, output_format: str) -> str:
        nonlocal json_attempt
        if output_format == "json":
            json_attempt += 1
            length = 98 if json_attempt == 1 else 100
            return json.dumps({"part_id": "demo-plate", "length_mm": length})
        return "demo-plate at 100 mm was released after validation."

    async def emit(event: dict) -> None:
        events.append(event)

    result = asyncio.run(
        execute_prompt_workflow(
            service=service,
            workspace_dir=str(workspace),
            plan=plan,
            input_values={},
            response_generator=generate,
            on_event=emit,
            run_id="served-process-validation-run",
        )
    )

    checks = [event for event in events if event["kind"] == "design_check"]
    assert [event["status"] for event in checks] == ["revise", "pass"]
    feedback = next(
        event for event in events if event["kind"] == "validation_feedback_delivered"
    )
    assert feedback["assessment_id"] == checks[0]["assessment_id"]
    assert feedback["remaining_revisions"] == 2
    assert feedback["complete_result_ref"].endswith(checks[0]["assessment_id"])
    assert [step["task_id"] for step in result["steps"]][-1] == "consume"

    for check in checks:
        evidence_path = workspace / check["assessment_path"]
        assert evidence_path.is_file()
        evidence = Assessment.model_validate_json(evidence_path.read_bytes())
        assert evidence.id == check["assessment_id"]
        assert evidence.summary.release_eligible is (check["status"] == "pass")

        served = offline_api_client.get(
            f"/api/workspace/process-validations/{evidence.id}",
            params={"session_id": "validation-session"},
        )
        assert served.status_code == 200, served.text
        payload = served.json()
        assert payload["assessment"]["id"] == evidence.id
        assert payload["assessment_digest"] == check["report"]["assessment_digest"]
        assert payload["currentness"]["is_current"] is (
            check["status"] == "pass"
        )

    failed = checks[0]
    findings = offline_api_client.get(
        f"/api/workspace/process-validations/{failed['assessment_id']}/findings",
        params={"session_id": "validation-session"},
    )
    assert findings.status_code == 200
    first = findings.json()["findings"][0]
    assert first["state"] == "fail"
    assert first["observed"] == 98
    assert "100" in first["explanation"]
    assert first["correction"]["action"] == "revise_output"

    markdown = offline_api_client.get(
        f"/api/workspace/process-validations/{failed['assessment_id']}/export",
        params={"session_id": "validation-session", "format": "markdown"},
    )
    assert markdown.status_code == 200
    assert markdown.headers["cache-control"] == "no-store"
    assert "text/markdown" in markdown.headers["content-type"]
    assert failed["assessment_id"] in markdown.text
    assert "98" in markdown.text and "100" in markdown.text

    passing = checks[-1]
    csv = offline_api_client.get(
        f"/api/workspace/process-validations/{passing['assessment_id']}/export",
        params={"session_id": "validation-session", "format": "csv"},
    )
    assert csv.status_code == 200
    rows = list(csv_module.DictReader(csv.text.splitlines()))
    assert rows
    assert {row["status"] for row in rows} == {"pass"}
    assert {row["assessment_id"] for row in rows} == {
        passing["assessment_id"]
    }
    assert {row["is_current"] for row in rows} == {"true"}
