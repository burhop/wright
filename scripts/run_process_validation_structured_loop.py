"""Run the saved structured validator loop with Wright's configured real model."""

from __future__ import annotations

import argparse
import asyncio
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil

import httpx
from agent_adapters.report_generation import generate_workflow_response
from agent_adapters.hermes_config import resolve_hermes_api_settings
from core.process_validation import Assessment, canonical_digest
from data_vault import install_default_secret_provider, upgrade_database
from workspace_service.service import WorkspaceService
from workspace_service.workflow_run_record import record_workflow_run
from workspace_service.workflow_source_execution import (
    compile_prompt_workflow,
    execute_prompt_workflow,
)


def _write(path: Path, value) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def finalize_evidence(output_dir: Path) -> None:
    """Drop isolated runtime state and inventory the retained review evidence."""
    git_dir = output_dir / "workspace/.git"
    if git_dir.exists():
        shutil.rmtree(git_dir)
    for transient in ("runtime.sqlite3", "runtime.sqlite3.lifecycle.lock"):
        (output_dir / transient).unlink(missing_ok=True)
    files = sorted(
        path
        for path in output_dir.rglob("*")
        if path.is_file() and path.name != "manifest.json"
    )
    _write(
        output_dir / "manifest.json",
        {
            "schema_version": 1,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "files": [
                {
                    "path": path.relative_to(output_dir).as_posix(),
                    "bytes": path.stat().st_size,
                    "sha256": _sha256(path),
                }
                for path in files
            ],
        },
    )


async def run(source_path: Path, output_dir: Path) -> dict:
    if output_dir.exists():
        raise FileExistsError(f"Evidence directory already exists: {output_dir}")
    workspace = output_dir / "workspace"
    workspace.mkdir(parents=True)
    copied_source = workspace / source_path.name
    shutil.copyfile(source_path, copied_source)
    source = copied_source.read_text(encoding="utf-8")
    plan = compile_prompt_workflow(source)
    started = datetime.now(timezone.utc)
    run_id = "structured-loop-" + started.strftime("%Y%m%dT%H%M%SZ")
    workspace_id = "process-validation-structured-loop"
    database = output_dir / "runtime.sqlite3"
    install_default_secret_provider()
    upgrade_database(str(database))
    service = WorkspaceService(str(database))
    service.repository.create(
        workspace_id,
        "structured-loop-session",
        str(workspace.resolve()),
        workspace_name="Process validation structured loop",
    )
    model_settings = resolve_hermes_api_settings()
    headers = (
        {"Authorization": f"Bearer {model_settings.api_key}"}
        if model_settings.api_key
        else {}
    )
    async with httpx.AsyncClient(timeout=10, headers=headers) as client:
        health_response = await client.get(f"{model_settings.base_url}/health")
        models_response = await client.get(f"{model_settings.base_url}/v1/models")
        health_response.raise_for_status()
        models_response.raise_for_status()
        health = health_response.json()
        models = models_response.json()
    model_runtime = {
        "adapter": "agent_adapters.generate_workflow_response",
        "endpoint": model_settings.base_url,
        "configuration_source": (
            model_settings.source
            if model_settings.source.isupper()
            else "Hermes profile configuration"
        ),
        "health": {
            key: health.get(key) for key in ("status", "platform", "version")
        },
        "models": [
            item.get("id")
            for item in models.get("data", [])
            if isinstance(item, dict) and isinstance(item.get("id"), str)
        ],
    }
    if health.get("status") != "ok" or not model_runtime["models"]:
        raise RuntimeError("Configured Hermes model endpoint is not ready")
    events: list[dict] = []

    async def observe(event):
        events.append(dict(event))

    async def execute(emit):
        return await execute_prompt_workflow(
            service=service,
            workspace_dir=str(workspace),
            plan=plan,
            input_values={},
            response_generator=generate_workflow_response,
            on_event=emit,
            run_id=run_id,
        )

    result = await record_workflow_run(
        service=service,
        workspace_dir=str(workspace),
        workspace_id=workspace_id,
        source_path=source_path.name,
        source_digest=_sha256(copied_source),
        execute=execute,
        on_event=observe,
        run_id=run_id,
        required_step_ids=[step.id for step in plan.steps],
    )
    assessments = []
    for event in events:
        if event.get("kind") != "design_check":
            continue
        path = workspace / event["assessment_path"]
        assessment = Assessment.model_validate_json(path.read_bytes())
        assessments.append(
            {
                "id": assessment.id,
                "digest": canonical_digest(assessment),
                "path": event["assessment_path"],
                "verdict": event["status"],
                "release_eligible": assessment.summary.release_eligible,
                "subject_current": assessment.subject_current,
                "subjects": [
                    {
                        "id": subject.id,
                        "sha256": subject.sha256,
                        "producer": subject.producer.model_dump(mode="json"),
                    }
                    for subject in assessment.request.subjects
                ],
                "finding_codes": [finding.code for finding in assessment.findings],
            }
        )
    producer_attempts = [
        record
        for record in (*result["revision_attempts"], *result["steps"])
        if record["task_id"] == "produce"
    ]
    producer_attempts.sort(key=lambda record: record["producer_attempt"])
    model_usage = [event["usage"] for event in events if event["kind"] == "model_usage"]
    feedback = [
        event for event in events if event["kind"] == "validation_feedback_delivered"
    ]
    checks = [event for event in events if event["kind"] == "design_check"]
    assert result["status"] == "completed"
    assert [json.loads(item["response"])["length_mm"] for item in producer_attempts] == [
        98,
        100,
    ]
    assert [item["status"] for item in checks] == ["revise", "pass"]
    assert [item["producer_attempt"] for item in producer_attempts] == [1, 2]
    assert len(feedback) == 1 and feedback[0]["target_step_id"] == "produce"
    assert result["steps"][-1]["task_id"] == "consume"
    assert len(model_usage) >= 3
    finished = datetime.now(timezone.utc)
    evidence = {
        "schema_version": 1,
        "demonstration": "ordinary-ai-structured-output-correction",
        "started_at": started.isoformat(),
        "finished_at": finished.isoformat(),
        "run_id": run_id,
        "workspace_id": workspace_id,
        "workflow_source": source_path.name,
        "workflow_sha256": _sha256(copied_source),
        "run_log_path": result["run_log_path"],
        "model_usage": model_usage,
        "model_runtime": model_runtime,
        "assessments": assessments,
        "feedback_delivery": feedback,
        "producer_attempts": [
            {
                "attempt": item["producer_attempt"],
                "response": json.loads(item["response"]),
                "repair_feedback": item.get("repair_feedback"),
                "saved_response": item.get("saved_response"),
            }
            for item in producer_attempts
        ],
        "consumer": next(
            item for item in result["steps"] if item["task_id"] == "consume"
        ),
        "assertions": {
            "controlled_initial_defect": True,
            "typed_feedback_delivered": True,
            "new_output_identity": assessments[0]["subjects"][0]["id"]
            != assessments[1]["subjects"][0]["id"],
            "new_output_digest": assessments[0]["subjects"][0]["sha256"]
            != assessments[1]["subjects"][0]["sha256"],
            "current_revision_passed": assessments[-1]["release_eligible"],
            "consumer_released": result["steps"][-1]["task_id"] == "consume",
        },
    }
    _write(output_dir / "events.json", events)
    _write(output_dir / "result.json", result)
    _write(output_dir / "evidence.json", evidence)
    finalize_evidence(output_dir)
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source",
        type=Path,
        default=Path(
            "tests/datasets/process-validation/processes/structured-loop.workflow.wflow"
        ),
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    evidence = asyncio.run(run(args.source.resolve(), args.output_dir.resolve()))
    print(json.dumps(evidence["assertions"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
