"""Qualify actual desktop proposals through existing confined gateway execution.

This is a local-tool transport spike before enabling gateway tasks in the MCP
plugin. It uses Wright's real source preparation/runtime/recorder, gateway and
private integration file-inspection authority; it contains no model worker.
"""

import argparse
import asyncio
import hashlib
import json
from pathlib import Path
from uuid import uuid4

from agent_adapters.desktop_reasoning import DesktopWorkflowReasoner
from core.desktop_reasoning import DesktopHarnessBinding
from core.process_validation import canonical_digest
from data_vault import (
    GatewayRepository,
    WorkspaceArtifactRepository,
    WorkspaceRepository,
    upgrade_database,
)
from data_vault.desktop_reasoning_repository import DesktopReasoningRepository
from data_vault.gateway_repository import GatewayBindingError
from data_vault.secret_provider import FileSecretProvider
from tool_registry.gateway_adapters import (
    DatabaseGatewayAudit,
    DatabaseGatewayCatalog,
    DatabaseGatewayWorkspace,
    EngineGatewayLifecycle,
)
from tool_registry.gateway_notifications import GatewayNotificationHub
from tool_registry.gateway_models import GatewayError, GatewayErrorCode
from tool_registry.gateway_service import GatewayService, SUPPORTED_PROTOCOL_VERSION
from tool_registry.manager import McpEngine
from workspace_service.service import WorkspaceService
from workspace_service.workflow_integration_policy import (
    WorkflowIntegrationPolicyService,
)
from workspace_service.workflow_mcp_execution import schema_digest
from workspace_service.workflow_reasoning_dispatch import WorkflowReasoningCallbacks
from workspace_service.workflow_run_preparation import prepare_authorized_workflow_run
from workspace_service.workflow_run_record import record_workflow_run
from workspace_service.workflow_source_execution import execute_prompt_workflow
from workspace_service.workspace_document_artifacts import (
    WorkspaceDocumentArtifactService,
)
from workspace_service.workspace_document_gateway import (
    WorkspaceDocumentGatewayProvider,
)
from workspace_service.workspace_file_inspection import INSPECT_TOOL_NAME

from reasoning_probe import DesktopConnectionMetadata, pending, respond


SOURCE = """workflow confined_read
  name: "Desktop confined gateway inspection"
  purpose: "Use actual desktop reasoning to inspect one enrolled digital input through Wright."
  discipline: "engineering.evidence"
  reviewed_ai_suggestions: true
end
input requirements
  name: "Supplied inspection requirements"
  purpose: "Retain exact digital demonstration input"
  provided_by: engineer
  group: null
  step_type: work
  inputs: []
  outputs: [{"key":"document","kind":"engineering_document","name":"Requirements","item":null,"required":true,"quantity":"one","description":"Supplied digital requirements"}]
  instructions: "Use the supplied document without changing it."
  tool: null
  reusable_step: null
  settings: {"workspace_file":"inputs/requirements.md"}
end
task inspect
  name: "Inspect the enrolled requirements"
  purpose: "Retain actual file evidence without measuring or releasing a physical part"
  step_type: work
  group: null
  performed_by: ai_assisted
  inputs: [{"key":"requirements","kind":"engineering_document","name":"Requirements","item":null,"required":true,"quantity":"one","description":"Exact input"}]
  outputs: [{"key":"inspection_note","kind":"engineering_document","name":"Digital inspection note","item":null,"required":true,"quantity":"one","description":"Evidence from the permitted file inspection"}]
  prompt: "Use the provided inspect_file capability once to inspect inputs/requirements.md, including its text. Report the observed byte size and SHA-256, preserve the supplied dimensions, and identify any missing hole-location information. This is a digital file inspection, not a CAD measurement or manufacturing approval. Propose the tool call for Wright to execute; do not read files using another tool or execute the proposed call yourself."
  tool: null
  reusable_step: null
  settings: {"authoring_template":"mcp-task","mcp_server":"wright-workspace-files","mcp_task_tools":["inspect_file"],"max_tool_calls":1,"timeout_seconds":600,"output_format":"markdown","output_filename":"outputs/probe/inspection-note.md"}
end
connection supplied
  type: item
  from: "requirements.document"
  to: "inspect.requirements"
  label: "Exact supplied document"
  when: null
end
"""

INPUT = (
    "# Supplied digital inspection requirements\n\n"
    "Plate length: 120 mm. Width: 80 mm. Thickness: 6 mm.\n"
    "Mounting holes: four, each diameter 8 mm.\n"
    "Hole locations and tolerances have not been supplied.\n"
    "This file is demonstration data; it contains no measurements or approval.\n"
)


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
    engine = McpEngine(str(database))  # No provider synchronization or host install.
    artifacts = WorkspaceDocumentArtifactService(
        WorkspaceArtifactRepository(str(database))
    )
    app.workspace_document_artifacts = artifacts
    app.workflow_integration_policies = WorkflowIntegrationPolicyService(
        str(database), enabled=True
    )
    audit = GatewayRepository(str(database))
    gateway = GatewayService(
        workspaces=DatabaseGatewayWorkspace(audit),
        catalog=DatabaseGatewayCatalog(str(database)),
        lifecycle=EngineGatewayLifecycle(engine),
        audit=DatabaseGatewayAudit(audit),
        notifier=GatewayNotificationHub(),
        capability_providers=(WorkspaceDocumentGatewayProvider(artifacts),),
    )
    prepared = None
    try:
        workspace = await app.create_workspace(
            "Desktop Gateway Proof",
            None,
            DesktopConnectionMetadata(),
            agent_id="openai-desktop-harness",
        )
        root = Path(workspace.local_path)
        (root / "inputs").mkdir(exist_ok=True)
        (root / "inputs/requirements.md").write_text(INPUT)
        input_hash = hashlib.sha256(INPUT.encode()).hexdigest()
        document = await app.workflow_sources.create(
            str(root), "workflows/desktop-gateway.workflow.wflow", SOURCE
        )
        control_session = "gateway-control-" + uuid4().hex
        gateway.open_session(
            session_id=control_session,
            binding_session_id=workspace.session_id,
            principal_id="local-desktop-qualification",
            workspace_id=workspace.workspace_id,
            transport="streamable_http",
        )
        gateway.initialize_session(
            control_session,
            protocol_version=SUPPORTED_PROTOCOL_VERSION,
            client_name="wright-desktop-qualification",
            client_version="1",
            client_capabilities={},
        )
        tool = next(
            t
            for t in gateway.list_tools(control_session)
            if t.name == INSPECT_TOOL_NAME
        )
        identity = {
            "server_id": tool.server_id,
            "name": tool.name,
            "schema_digest": schema_digest(tool),
        }
        try:
            await gateway.call_tool(
                control_session,
                "deliberate-no-permit",
                tool.name,
                {"relativePath": "inputs/requirements.md"},
                workspace_approvals=set(),
            )
        except GatewayError as error:
            if error.code != GatewayErrorCode.POLICY_DENIED:
                raise
            controls = {
                "inspection_without_permit": {
                    "denied": True,
                    "error_code": error.code.value,
                    "message": str(error),
                }
            }
        else:
            raise ValueError(
                "The read-only annotation incorrectly granted private file access"
            )
        try:
            gateway.open_session(
                session_id="wrong-workspace-control",
                binding_session_id=workspace.session_id,
                principal_id="local-desktop-qualification",
                workspace_id="wrong-workspace",
                transport="streamable_http",
            )
        except GatewayBindingError as error:
            controls["wrong_workspace"] = {
                "denied": True,
                "exception": type(error).__name__,
            }
        else:
            raise ValueError("Gateway accepted an incorrect workspace binding")
        import agent_adapters.desktop_reasoning as adapter

        binding = DesktopHarnessBinding(
            connection_id="desktop-gateway-proof:"
            + canonical_digest(
                {
                    "adapter_sha256": hashlib.sha256(
                        Path(adapter.__file__).read_bytes()
                    ).hexdigest(),
                    "tool": identity,
                    "gateway_protocol": SUPPORTED_PROTOCOL_VERSION,
                }
            )
        )
        handoffs = DesktopReasoningRepository(database)
        resolver = DesktopWorkflowReasoner(
            handoffs,
            workspace_id=workspace.workspace_id,
            session_id=workspace.session_id,
            run_id="qualification",
            binding=binding,
        )
        app.workflow_model_capabilities = resolver.capabilities
        grant = app.workflow_integration_policies.enroll(
            campaign_id="desktop-harness-digital-prototype",
            dataset_id="confined-file-read",
            dataset_digest=input_hash,
            workspace_id=workspace.workspace_id,
            source_path=document.path,
            source_digest=document.storage_digest,
            input_files={"inputs/requirements.md": input_hash},
            output_root="outputs/probe",
            allowed_tools=[identity],
            approval_mode="manual",
        )
        prepared = await prepare_authorized_workflow_run(
            service=app,
            workspace_dir=str(root),
            workspace_id=workspace.workspace_id,
            session_id=workspace.session_id,
            source_path=document.path,
            source_digest=document.storage_digest,
            gateway=lambda: gateway,
            integration_policy_digest=grant,
        )
        desktop = DesktopWorkflowReasoner(
            handoffs,
            workspace_id=workspace.workspace_id,
            session_id=workspace.session_id,
            run_id=prepared.run_id,
            binding=binding,
        )

        def callbacks(**scope):
            if scope["run_id"] != prepared.run_id or scope["workspace_dir"] != str(
                root
            ):
                raise ValueError("Gateway proof callback has another run scope")
            return WorkflowReasoningCallbacks(
                desktop.generate_response, desktop.decide_action
            )

        app.workflow_reasoning_factory = callbacks
        info = {
            "workspace_id": workspace.workspace_id,
            "session_id": workspace.session_id,
            "workspace_path": str(root),
            "run_id": prepared.run_id,
            "source_path": document.path,
            "source_digest": document.storage_digest,
            "binding": binding.model_dump(mode="json"),
            "execution_context": prepared.execution_context,
            "transport": "local-tool-mediated handoff; installed MCP action transport not yet qualified",
            "allowed_tool": identity,
            "input_sha256": input_hash,
            "input_bytes": len(INPUT.encode()),
            "controls": controls,
        }
        (state / "probe.json").write_text(json.dumps(info, indent=2))
        print(
            json.dumps(
                {
                    "status": "awaiting_desktop_proposal",
                    "state_dir": str(state),
                    "run_id": prepared.run_id,
                }
            ),
            flush=True,
        )

        async def forbidden_model(*args, **kwargs):
            raise AssertionError("Gateway proof cannot fall back to a model service")

        async def execute(emit):
            return await execute_prompt_workflow(
                service=app,
                workspace_dir=str(root),
                plan=prepared.plan,
                input_values=prepared.values,
                response_generator=forbidden_model,
                action_generator=forbidden_model,
                tool_runtime=prepared.runtime,
                execution_context=prepared.execution_context,
                run_id=prepared.run_id,
                on_event=emit,
            )

        result = await record_workflow_run(
            service=app,
            workspace_dir=str(root),
            workspace_id=workspace.workspace_id,
            source_path=document.path,
            source_digest=document.storage_digest,
            execute=execute,
            execution_context=prepared.execution_context,
            run_id=prepared.run_id,
        )
        (state / "result.json").write_text(json.dumps(result, indent=2))
        events = audit.list_audit(prepared.runtime.session_id)
        (state / "gateway-audit.json").write_text(json.dumps(events, indent=2))
        unchanged = (
            hashlib.sha256((root / "inputs/requirements.md").read_bytes()).hexdigest()
            == input_hash
        )
        proof = {
            "status": result.get("status"),
            "run_id": prepared.run_id,
            "run_log_path": result.get("run_log_path"),
            "input_unchanged": unchanged,
            "qualified_boundary": "existing confined gateway/runtime with local-tool desktop handoff, not installed plugin",
        }
        (state / "qualification.json").write_text(json.dumps(proof, indent=2))
        print(json.dumps(proof), flush=True)
        if result.get("status") != "completed" or not unchanged:
            raise ValueError(
                "Gateway qualification did not complete with unchanged input"
            )
    finally:
        if prepared is not None and prepared.runtime is not None:
            await prepared.runtime.close()
        await gateway.shutdown()
        await engine.shutdown()
        await app.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["start", "pending", "respond"])
    parser.add_argument("--state-dir", required=True, type=Path)
    parser.add_argument("--response-file", type=Path)
    args = parser.parse_args()
    state = args.state_dir.resolve()
    if args.command == "start":
        asyncio.run(start(state))
    elif args.command == "pending":
        pending(state)
    else:
        if not args.response_file:
            parser.error("respond requires --response-file")
        respond(state, args.response_file)
