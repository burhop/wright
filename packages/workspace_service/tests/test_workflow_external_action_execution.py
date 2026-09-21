from __future__ import annotations

import asyncio
import json
from dataclasses import replace
from types import SimpleNamespace

from data_vault import WorkflowContinuationRepository
from workspace_service.adapters.filesystem import LocalWorkspaceFiles
from workspace_service.workflow_external_actions import WorkflowExternalActionService
from workspace_service.workflow_run_record import (
    record_workflow_approval_transition,
    record_workflow_run,
)
from workspace_service.workflow_source_execution import (
    compile_prompt_workflow,
    execute_prompt_workflow,
)
from workspace_service.executor import BoundedExecutor
from workspace_service.use_cases.files import WorkspaceFileUseCases


def source() -> str:
    action = {
        "authoring_template": "external-action-approval",
        "action_kind": "printer_transfer",
        "approval_binding": {
            "server": "bambu-adapter",
            "tool": "transfer_package",
            "schema": "d" * 64,
        },
        "approval_destination": {"kind": "printer", "id": "bambu-p1s-01"},
        "approval_settings": {"material": "PLA", "profile": "0.20-standard"},
        "approval_action": {
            "kind": "printer_transfer",
            "mode": "transfer_only",
        },
    }
    return f"""workflow test
  name: "Printer workflow"
end
task package
  name: "Create package"
  step_type: work
  performed_by: ai_assisted
  inputs: []
  outputs: [{{"key":"package_file","kind":"workspace_file","name":"Package"}}]
  prompt: "Create the bounded package manifest."
  settings: {{"output_format":"json","output_filename":"package.json","save_output":true}}
  tool: null
  reusable_step: null
end
task approve
  name: "Authorize transfer"
  step_type: review
  performed_by: engineer
  inputs: []
  outputs: []
  instructions: "Review the exact package and printer."
  settings: {json.dumps(action)}
  tool: null
  reusable_step: null
end
connection package_to_approval
  type: order
  from: "package"
  to: "approve"
  label: "exact package"
  when: null
end
"""


def service(root):
    return SimpleNamespace(
        files=WorkspaceFileUseCases(
            str(root / "file-state.db"), BoundedExecutor(), LocalWorkspaceFiles
        ),
        workflow_external_actions=WorkflowExternalActionService(
            WorkflowContinuationRepository(str(root / "state.db"))
        ),
    )


def test_compile_and_execute_pause_on_exact_external_action_subject(tmp_path):
    plan = replace(compile_prompt_workflow(source()), definition_digest="a" * 64)

    async def generate(prompt, fmt):
        return '{"package":"ready"}'

    result = asyncio.run(
        execute_prompt_workflow(
            service=service(tmp_path),
            workspace_dir=str(tmp_path),
            plan=plan,
            input_values={},
            response_generator=generate,
        )
    )

    request = result["_approval_request"]
    assert [step["task_id"] for step in result["steps"]] == ["package"]
    assert request["step_id"] == "approve"
    assert request["subject"] == {
        "definition_digest": "a" * 64,
        "input_digests": [],
        "artifact_digests": [result["outputs"][0]["sha256"]],
        "binding": {
            "server": "bambu-adapter",
            "tool": "transfer_package",
            "schema": "d" * 64,
        },
        "destination": {"kind": "printer", "id": "bambu-p1s-01"},
        "settings": {"material": "PLA", "profile": "0.20-standard"},
        "action": {"kind": "printer_transfer", "mode": "transfer_only"},
    }


def test_run_log_recovers_approval_decision_and_one_shot_authority(tmp_path):
    services = service(tmp_path)
    plan = replace(compile_prompt_workflow(source()), definition_digest="a" * 64)

    async def execute(emit):
        async def generate(prompt, fmt):
            return '{"package":"ready"}'

        return await execute_prompt_workflow(
            service=services,
            workspace_dir=str(tmp_path),
            plan=plan,
            input_values={},
            response_generator=generate,
            on_event=emit,
        )

    result = asyncio.run(
        record_workflow_run(
            service=services,
            workspace_dir=str(tmp_path),
            workspace_id="workspace-1",
            source_path="printer.workflow.wflow",
            source_digest="a" * 64,
            execute=execute,
        )
    )
    assert result["status"] == "awaiting_approval"
    checkpoint = services.workflow_external_actions.lookup(
        result["approval"]["checkpoint_id"]
    )
    assert checkpoint.continuation["completed_step_ids"] == ["package"]

    checkpoint = services.workflow_external_actions.decide(
        checkpoint.checkpoint_id,
        workspace_id="workspace-1",
        expected_subject_digest=checkpoint.subject_digest,
        actor="local-user",
        approved=True,
    )
    asyncio.run(
        record_workflow_approval_transition(
            service=services,
            workspace_dir=str(tmp_path),
            checkpoint=checkpoint,
            kind="approval_decided",
        )
    )
    checkpoint = services.workflow_external_actions.consume_for_dispatch(
        checkpoint.checkpoint_id,
        workspace_id="workspace-1",
        current_subject=checkpoint.subject,
        action_id="resume-1",
    )
    asyncio.run(
        record_workflow_approval_transition(
            service=services,
            workspace_dir=str(tmp_path),
            checkpoint=checkpoint,
            kind="external_action_authorized",
        )
    )

    run_log = json.loads((tmp_path / result["run_log_path"]).read_text())
    assert run_log["status"] == "awaiting_external_outcome"
    assert run_log["result"]["approval"]["external_action"]["action_id"] == "resume-1"
    assert [event["kind"] for event in run_log["events"]][-3:] == [
        "approval_requested",
        "approval_decided",
        "external_action_authorized",
    ]
