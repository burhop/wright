"""Real source-runtime probe; this desktop supplies replies through local tools.

This is a transport spike, not proof of an installed MCP plugin or GUI hosting.
No LLM service is started or invoked. All state is under --state-dir.
"""

import argparse
import asyncio
from datetime import datetime, timezone
import json
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

from agent_adapters.desktop_reasoning import DesktopWorkflowReasoner
from core.desktop_reasoning import DesktopHarnessBinding, DesktopReasoningResponse
from data_vault import WorkspaceRepository, upgrade_database
from data_vault.desktop_reasoning_repository import DesktopReasoningRepository
from data_vault.secret_provider import FileSecretProvider
from workspace_service.service import WorkspaceService
from workspace_service.workflow_run_record import record_workflow_run
from workspace_service.workflow_model_routing import freeze_workflow_model_routing
from workspace_service.workflow_source_execution import (
    prepare_prompt_workflow,
    execute_prompt_workflow,
)


SOURCE = """workflow desktop_handoff
  name: "Desktop reasoning handoff"
  purpose: "Qualify one desktop-supplied digital inspection brief through Wright's source runtime."
  discipline: "mechanical.inspection"
  reviewed_ai_suggestions: true
end
task brief
  name: "Prepare a digital inspection brief"
  purpose: "Separate supplied dimensions from missing inspection criteria without claiming measurement."
  step_type: work
  group: null
  performed_by: ai_assisted
  inputs: [{"key":"brief_prompt","kind":"engineering_document","name":"Prompt","item":null,"required":false,"quantity":"optional","description":"Optional upstream requirements"}]
  outputs: [{"key":"brief_response","kind":"engineering_document","name":"Inspection brief","item":null,"required":true,"quantity":"one","description":"Digital inspection brief, not measured evidence"}]
  prompt: "Prepare a short digital inspection brief for a rectangular plate: length 120 mm, width 80 mm, thickness 6 mm, four mounting holes of diameter 8 mm. Identify the dimensions to check, distinguish supplied requirements from unspecified hole locations, and explain why no manufacturing release can be claimed. This task performs no physical action and no CAD measurement."
  settings: {"output_format":"markdown","output_filename":"inspection-brief.md"}
  tool: null
  reusable_step: null
end
"""


class DesktopConnectionMetadata:
    """Allocate a Wright connection handle without creating another AI session."""

    async def create_session(self, workspace_path):
        return SimpleNamespace(session_id="desktop-probe-" + str(uuid4()))


def metadata(state):
    return json.loads((state / "probe.json").read_text())


async def start(state):
    state.mkdir(parents=True, exist_ok=False)
    database = state / "wright.sqlite"
    upgrade_database(database)
    repository = WorkspaceRepository(
        str(database), secrets=FileSecretProvider(state / "credentials.json")
    )
    app = WorkspaceService(
        str(database),
        repository=repository,
        parent_dir_provider=lambda: str(state / "workspaces"),
    )
    try:
        workspace = await app.create_workspace(
            "Desktop Handoff Proof",
            None,
            DesktopConnectionMetadata(),
            agent_id="openai-desktop-harness",
        )
        # Explicit platform attribution: create_dashboard currently initializes
        # a legacy Hermes association. No Hermes session was created here.
        repository.associate_session(
            workspace.workspace_id,
            workspace.session_id,
            agent_id="openai-desktop-harness",
        )
        run_id = str(uuid4())
        binding = DesktopHarnessBinding(connection_id="local-desktop-probe")
        desktop = DesktopWorkflowReasoner(
            DesktopReasoningRepository(database),
            workspace_id=workspace.workspace_id,
            session_id=workspace.session_id,
            run_id=run_id,
            binding=binding,
        )
        app.workflow_model_capabilities = desktop.capabilities
        document = await app.workflow_sources.create(
            workspace.local_path, "workflows/desktop-handoff.workflow.wflow", SOURCE
        )
        plan, input_values = await prepare_prompt_workflow(
            service=app,
            workspace_dir=workspace.local_path,
            path=document.path,
            expected_digest=document.storage_digest,
            workspace_id=workspace.workspace_id,
            run_id=run_id,
        )
        plan, context = await freeze_workflow_model_routing(app, plan, {})
        info = {
            "workspace_id": workspace.workspace_id,
            "session_id": workspace.session_id,
            "workspace_path": workspace.local_path,
            "run_id": run_id,
            "source_path": document.path,
            "source_digest": document.storage_digest,
            "binding": binding.model_dump(mode="json"),
            "transport": "local-tool-mediated-sqlite-probe",
            "model_identity": "unreported; not independently attested",
            "execution_context": context,
        }
        (state / "probe.json").write_text(json.dumps(info, indent=2))
        print(
            json.dumps(
                {"status": "started", "state_dir": str(state), "run_id": run_id}
            ),
            flush=True,
        )

        async def execute(emit):
            return await execute_prompt_workflow(
                service=app,
                workspace_dir=workspace.local_path,
                plan=plan,
                input_values=input_values,
                response_generator=desktop.generate_response,
                on_event=emit,
                execution_context=context,
                run_id=run_id,
            )

        result = await record_workflow_run(
            service=app,
            workspace_dir=workspace.local_path,
            source_path=document.path,
            source_digest=document.storage_digest,
            execute=execute,
            workspace_id=workspace.workspace_id,
            execution_context=context,
            run_id=run_id,
        )
        (state / "result.json").write_text(json.dumps(result, indent=2))
        print(
            json.dumps(
                {
                    "status": result.get("status"),
                    "run_log_path": result.get("run_log_path"),
                }
            ),
            flush=True,
        )
    finally:
        await app.close()


def pending(state):
    info = metadata(state)
    repo = DesktopReasoningRepository(state / "wright.sqlite")
    tasks = repo.pending(info["workspace_id"], info["session_id"])
    print(
        json.dumps(
            [
                {
                    "request": task.model_dump(mode="json"),
                    "request_digest": task.digest,
                    "binding_digest": task.binding.digest,
                }
                for task in tasks
            ],
            indent=2,
        )
    )


def respond(state, response_file):
    info = metadata(state)
    data = json.loads(response_file.read_text())
    response = DesktopReasoningResponse.model_validate(
        {
            **data,
            "received_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    repo = DesktopReasoningRepository(state / "wright.sqlite")
    _, accepted = repo.submit_response(
        info["workspace_id"], info["session_id"], response
    )
    print(json.dumps({"accepted": accepted, "response_id": response.response_id}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["start", "pending", "respond"])
    parser.add_argument("--state-dir", required=True, type=Path)
    parser.add_argument("--response-file", type=Path)
    args = parser.parse_args()
    if args.command == "start":
        asyncio.run(start(args.state_dir.resolve()))
    elif args.command == "pending":
        pending(args.state_dir.resolve())
    else:
        if not args.response_file:
            parser.error("respond requires --response-file")
        respond(args.state_dir.resolve(), args.response_file)
