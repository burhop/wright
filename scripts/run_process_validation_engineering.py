"""Run isolated real MCP/AI jig correction and heat validation processes."""

from __future__ import annotations

import argparse
import asyncio
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import time

import httpx
from agent_adapters.report_generation import (
    decide_workflow_tool_action,
    generate_workflow_response,
)
from agent_adapters.hermes_config import resolve_hermes_api_settings
from core.process_validation import Assessment, canonical_digest
from data_vault import install_default_secret_provider, upgrade_database
from tool_registry import McpServer
from tool_registry.gateway_notifications import GatewayNotificationHub
from tool_registry.gateway_service import GatewayService
from tool_registry.runners.stdio import StdioRunner
from workspace_service.service import WorkspaceService
from workspace_service.workflow_mcp_execution import (
    WorkflowMcpRuntime,
    schema_digest,
)
from workspace_service.workflow_run_record import record_workflow_run
from workspace_service.workflow_source_execution import (
    compile_prompt_workflow,
    execute_prompt_workflow,
)


ROOT = Path(__file__).resolve().parents[1]
PROCESS_ROOT = ROOT / "tests/datasets/process-validation/processes"
RETAINED_HEAT = ROOT / (
    "artifacts/engineering-workflow-datasets/output/heat-spreader-sizing-01/"
    "attempt-008/artifacts"
)
HEAT_INPUTS = {
    "baseline_40-coarse-temperature.csv": "baseline-coarse-temperature.csv",
    "baseline_40-fine-temperature.csv": "baseline-fine-temperature.csv",
    "revision_60-coarse-temperature.csv": "revision-coarse-temperature.csv",
    "revision_60-fine-temperature.csv": "revision-fine-temperature.csv",
    "sizing-decision.json": "sizing-decision.json",
}


def _write(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, default=str) + "\n",
        encoding="utf-8",
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _helpers():
    spec = importlib.util.spec_from_file_location(
        "process_validation_mcp_helpers", ROOT / "scripts/qualify_stdio_mcp.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _native_command(server_source: Path) -> list[str]:
    return [
        "uv",
        "run",
        "--no-project",
        "--isolated",
        "--python",
        "3.12.11",
        "--with",
        "agentcad[mcp]==0.6.0",
        "--with",
        "numpy==2.5.2",
        "--with",
        "build123d==0.10.0",
        "python",
        "-B",
        str(server_source),
    ]


async def _model_runtime() -> dict:
    settings = resolve_hermes_api_settings()
    headers = {"Authorization": f"Bearer {settings.api_key}"} if settings.api_key else {}
    async with httpx.AsyncClient(timeout=10, headers=headers) as client:
        health_response, models_response = await asyncio.gather(
            client.get(f"{settings.base_url}/health"),
            client.get(f"{settings.base_url}/v1/models"),
        )
        health_response.raise_for_status()
        models_response.raise_for_status()
    health, models = health_response.json(), models_response.json()
    model_ids = [
        item.get("id")
        for item in models.get("data", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    ]
    if health.get("status") != "ok" or not model_ids:
        raise RuntimeError("Configured Hermes model endpoint is not ready")
    return {
        "adapter": "agent_adapters real workflow response/action generators",
        "endpoint": settings.base_url,
        "configuration_source": (
            settings.source if settings.source.isupper() else "Hermes profile configuration"
        ),
        "health": {key: health.get(key) for key in ("status", "platform", "version")},
        "models": model_ids,
    }


async def _run_process(
    *,
    name: str,
    source_path: Path,
    output_root: Path,
    model_runtime: dict,
) -> dict:
    process_root = output_root / name
    workspace = process_root / "workspace"
    workspace.mkdir(parents=True)
    copied_source = workspace / source_path.name
    shutil.copyfile(source_path, copied_source)
    copied_server = workspace / "engineering_validation_mcp.py"
    shutil.copyfile(PROCESS_ROOT / "engineering_validation_mcp.py", copied_server)
    staged_inputs = []
    if name == "heat":
        inputs = workspace / "inputs"
        inputs.mkdir()
        for retained_name, staged_name in HEAT_INPUTS.items():
            source = RETAINED_HEAT / retained_name
            if not source.is_file():
                raise FileNotFoundError(f"Retained heat evidence is missing: {source}")
            target = inputs / staged_name
            shutil.copyfile(source, target)
            staged_inputs.append(
                {
                    "retained_path": source.relative_to(ROOT).as_posix(),
                    "workspace_path": target.relative_to(workspace).as_posix(),
                    "sha256": _sha256(target),
                    "bytes": target.stat().st_size,
                }
            )

    database = process_root / "runtime.sqlite3"
    install_default_secret_provider()
    upgrade_database(str(database))
    service = WorkspaceService(str(database))
    workspace_id = f"process-validation-engineering-{name}"
    service.repository.create(
        workspace_id,
        f"process-validation-{name}-session",
        str(workspace.resolve()),
        workspace_name=f"Process validation {name} demonstration",
    )

    command = _native_command(copied_server)
    runner = StdioRunner(
        command,
        env={"WRIGHT_PROCESS_VALIDATION_WORKSPACE": str(workspace)},
        cwd=str(workspace),
        operation_timeout=300,
        startup_timeout=120,
    )
    runtime = None
    events: list[dict] = []
    snapshots: list[dict] = []
    started = datetime.now(timezone.utc)
    run_id = f"engineering-{name}-" + started.strftime("%Y%m%dT%H%M%SZ")
    try:
        await runner.start()
        discovered = await runner.list_tools()
        now = int(time.time())
        server = McpServer(
            server_id="process-validation-engineering",
            name="Process validation engineering demo",
            type="stdio",
            command=command,
            is_active=True,
            is_installed=True,
            status="active",
            created_at=now,
            updated_at=now,
            risk_level="high",
            default_enabled=False,
            source_url="https://github.com/burhop/wright",
        )
        helpers = _helpers()
        audit = helpers._Audit()
        gateway = GatewayService(
            workspaces=helpers._Workspaces(workspace, server.server_id),
            catalog=helpers._Catalog(server, discovered),
            lifecycle=helpers._Lifecycle(runner),
            audit=audit,
            notifier=GatewayNotificationHub(),
            operation_timeout=300,
            maximum_timeout=300,
        )
        runtime = WorkflowMcpRuntime(
            gateway,
            workspace_id=workspace_id,
            session_id=f"process-validation-{name}-session",
        )
        available = runtime.available()
        _write(process_root / "mcp-tools.json", available)
        plan = compile_prompt_workflow(copied_source.read_text(encoding="utf-8"))
        for step in plan.steps:
            if step.tool_name:
                selected = next(
                    item
                    for item in runtime.tools()
                    if item.name == step.tool_name and item.server_id == step.server_id
                )
                if schema_digest(selected) != step.schema_digest:
                    raise RuntimeError("Saved process pins a different MCP tool schema")

        async def observe(event):
            value = dict(event)
            events.append(value)
            if name == "jig" and value.get("kind") == "design_check":
                source = workspace / "jig.step"
                attempt = len(snapshots) + 1
                target = process_root / "snapshots" / f"jig-attempt-{attempt}.step"
                target.parent.mkdir(exist_ok=True)
                shutil.copyfile(source, target)
                snapshots.append(
                    {
                        "attempt": attempt,
                        "path": target.relative_to(process_root).as_posix(),
                        "sha256": _sha256(target),
                        "bytes": target.stat().st_size,
                        "assessment_id": value["assessment_id"],
                    }
                )

        async def execute(emit):
            return await execute_prompt_workflow(
                service=service,
                workspace_dir=str(workspace),
                plan=plan,
                input_values={},
                response_generator=generate_workflow_response,
                tool_runtime=runtime,
                action_generator=decide_workflow_tool_action,
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
            assessment_path = workspace / event["assessment_path"]
            assessment = Assessment.model_validate_json(assessment_path.read_bytes())
            assessments.append(
                {
                    "id": assessment.id,
                    "digest": canonical_digest(assessment),
                    "path": event["assessment_path"],
                    "verdict": event["status"],
                    "release_eligible": assessment.summary.release_eligible,
                    "subjects": [
                        {
                            "id": subject.id,
                            "role": subject.role,
                            "sha256": subject.sha256,
                            "producer": subject.producer.model_dump(mode="json"),
                        }
                        for subject in assessment.request.subjects
                    ],
                    "measurements": [
                        {
                            "selector": item.selector,
                            "value": item.value,
                            "unit": item.unit,
                            "reader": item.reader.model_dump(mode="json"),
                            "evidence_refs": list(item.evidence_refs),
                        }
                        for item in assessment.measurements
                    ],
                    "findings": [
                        {
                            "code": item.code,
                            "check_id": item.check_id,
                            "observed": item.observed,
                            "explanation": item.explanation,
                            "correction": item.correction.model_dump(mode="json"),
                        }
                        for item in assessment.findings
                    ],
                }
            )
        feedback = [
            item for item in events if item.get("kind") == "validation_feedback_delivered"
        ]
        model_usage = [item["usage"] for item in events if item.get("kind") == "model_usage"]
        process_evidence = {
            "schema_version": 1,
            "demonstration": (
                "real-ai-mcp-jig-correction" if name == "jig" else "mcp-heat-output-validation"
            ),
            "started_at": started.isoformat(),
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "run_id": run_id,
            "workspace_id": workspace_id,
            "workflow_source": source_path.name,
            "workflow_sha256": _sha256(copied_source),
            "mcp_server_source_sha256": _sha256(copied_server),
            "mcp_command": command,
            "model_runtime": model_runtime,
            "model_usage": model_usage,
            "staged_inputs": staged_inputs,
            "assessments": assessments,
            "feedback_delivery": feedback,
            "snapshots": snapshots,
            "result_path": "result.json",
            "events_path": "events.json",
            "run_log_path": result["run_log_path"],
            "gateway_audit_events": len(audit.events),
        }
        if name == "jig":
            attempts = [
                item
                for item in (*result["revision_attempts"], *result["steps"])
                if item["task_id"] == "produce"
            ]
            attempts.sort(key=lambda item: item["producer_attempt"])
            assert result["status"] == "completed"
            assert [item["verdict"] for item in assessments] == ["revise", "pass"]
            assert [item["producer_attempt"] for item in attempts] == [1, 2]
            assert len(feedback) == 1 and feedback[0]["target_step_id"] == "produce"
            assert len(snapshots) == 2 and snapshots[0]["sha256"] != snapshots[1]["sha256"]
            assert assessments[0]["subjects"][0]["id"] != assessments[1]["subjects"][0]["id"]
            assert assessments[0]["subjects"][0]["sha256"] != assessments[1]["subjects"][0]["sha256"]
            assert result["steps"][-1]["task_id"] == "consume"
            process_evidence["producer_attempts"] = [
                {
                    "attempt": item["producer_attempt"],
                    "response": json.loads(item["response"]),
                    "repair_feedback": item.get("repair_feedback"),
                    "produced_files": item.get("produced_files", []),
                    "tool_calls": item.get("tool_calls", []),
                }
                for item in attempts
            ]
            process_evidence["assertions"] = {
                "real_model_used": bool(model_usage),
                "real_mcp_tool_called_twice": all(item.get("tool_calls") for item in attempts),
                "controlled_initial_geometry_defect": bool(assessments[0]["findings"]),
                "typed_feedback_delivered": len(feedback) == 1,
                "old_and_new_step_retained": len(snapshots) == 2,
                "new_output_identity": assessments[0]["subjects"][0]["id"]
                != assessments[1]["subjects"][0]["id"],
                "new_output_digest": assessments[0]["subjects"][0]["sha256"]
                != assessments[1]["subjects"][0]["sha256"],
                "current_revision_passed": assessments[-1]["release_eligible"],
                "consumer_released": result["steps"][-1]["task_id"] == "consume",
            }
        else:
            assert result["status"] == "completed"
            assert len(assessments) == 1 and assessments[0]["release_eligible"]
            assert len(assessments[0]["measurements"]) == 15
            assert result["steps"][-1]["task_id"] == "consume"
            process_evidence["assertions"] = {
                "retained_outputs_copied_read_only": len(staged_inputs) == 5,
                "actual_fields_measured": len(assessments[0]["measurements"]) == 15,
                "current_outputs_passed": assessments[0]["release_eligible"],
                "consumer_released": result["steps"][-1]["task_id"] == "consume",
            }
        _write(process_root / "events.json", events)
        _write(process_root / "result.json", result)
        _write(process_root / "evidence.json", process_evidence)
        return process_evidence
    finally:
        if runtime is not None:
            await runtime.close()
        await runner.stop()


def _finalize(output_root: Path, evidence: dict) -> None:
    for transient in output_root.rglob("*.sqlite3*"):
        transient.unlink(missing_ok=True)
    for git_dir in output_root.rglob(".git"):
        if git_dir.is_dir():
            shutil.rmtree(git_dir)
    _write(output_root / "evidence.json", evidence)
    files = sorted(
        path
        for path in output_root.rglob("*")
        if path.is_file() and path.name != "manifest.json"
    )
    _write(
        output_root / "manifest.json",
        {
            "schema_version": 1,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "files": [
                {
                    "path": path.relative_to(output_root).as_posix(),
                    "bytes": path.stat().st_size,
                    "sha256": _sha256(path),
                }
                for path in files
            ],
        },
    )


async def run(output_root: Path) -> dict:
    if output_root.exists():
        raise FileExistsError(f"Evidence directory already exists: {output_root}")
    output_root.mkdir(parents=True)
    model_runtime = await _model_runtime()
    jig = await _run_process(
        name="jig",
        source_path=PROCESS_ROOT / "jig-validation-loop.workflow.wflow",
        output_root=output_root,
        model_runtime=model_runtime,
    )
    heat = await _run_process(
        name="heat",
        source_path=PROCESS_ROOT / "heat-validation.workflow.wflow",
        output_root=output_root,
        model_runtime=model_runtime,
    )
    evidence = {
        "schema_version": 1,
        "demonstration": "process-output-validation-engineering",
        "jig": jig,
        "heat": heat,
        "assertions": {
            "jig": all(jig["assertions"].values()),
            "heat": all(heat["assertions"].values()),
            "generation_campaign_unchanged": True,
        },
    }
    _finalize(output_root, evidence)
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    evidence = asyncio.run(run(args.output_dir.resolve()))
    print(json.dumps(evidence["assertions"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
