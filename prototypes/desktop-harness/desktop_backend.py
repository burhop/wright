"""Opt-in prototype composition over Wright's existing services and owners."""

import hashlib
from importlib.metadata import version
import json
from pathlib import Path
from types import SimpleNamespace
import time
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

from agent_adapters.desktop_reasoning import DesktopWorkflowReasoner
from core.desktop_reasoning import DesktopHarnessBinding, DesktopReasoningResponse
from core.process_validation import canonical_digest
from data_vault.desktop_reasoning_repository import (
    DesktopHandoffConflict,
    DesktopReasoningRepository,
)
from workspace_service.workflow_reasoning_dispatch import WorkflowReasoningCallbacks
from api.services.mcp_services import McpApiService, get_mcp_api_service
from api.security import require_admin
from desktop_oauth import DesktopOAuthPresentation


CLIENT_LEASE_SECONDS = 30
HEARTBEAT_INTERVAL_SECONDS = 5


class ConnectRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    client_id: str = Field(min_length=1, max_length=128)
    binding: DesktopHarnessBinding


class CreateWorkspaceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=100)


class AnswerRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    workspace_id: str
    session_id: str
    response: DesktopReasoningResponse


class ConnectionPlanRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    workspace_id: str
    session_id: str
    capability_id: str = Field(min_length=1, max_length=256)
    independently_completed_license: bool = False


class ConnectionPlanAction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    workspace_id: str
    session_id: str
    plan_digest: str = Field(pattern=r"^[a-f0-9]{64}$")


class DesktopBackend:
    def __init__(
        self,
        service,
        state,
        web_port,
        *,
        confined_inspection=False,
        native_editor=False,
        native_working_view=False,
        image_inputs=False,
    ):
        if native_working_view and not native_editor:
            raise ValueError("Native working view requires the native editor resource")
        self.service = service
        self.state = Path(state).resolve(strict=True)
        self.web_port = web_port
        self.clients = {}
        self.oauth = DesktopOAuthPresentation()
        self._now = time.monotonic
        self.confined_inspection = confined_inspection
        self.repository = DesktopReasoningRepository(service.db_path)
        runtime = {
            "mcp_sdk": version("mcp"),
            "image_inputs": image_inputs,
            "files": {},
            "confined_inspection": confined_inspection,
            "native_editor": native_editor,
            "native_working_view": native_working_view,
            "connection_lease_seconds": CLIENT_LEASE_SECONDS,
            "heartbeat_interval_seconds": HEARTBEAT_INTERVAL_SECONDS,
        }
        import agent_adapters.desktop_reasoning as adapter
        import workspace_service.workflow_reasoning_dispatch as dispatch

        for name, file in (
            ("adapter", adapter.__file__),
            ("dispatch", dispatch.__file__),
            ("backend", __file__),
            ("transport", Path(__file__).with_name("mcp_bridge.py")),
        ):
            runtime["files"][name] = hashlib.sha256(Path(file).read_bytes()).hexdigest()
        for name, file in (
            [("native_source_tools", "native_source_tools.py")]
            + [("desktop_oauth", "desktop_oauth.py")]
            + ([("native_editor", "native-editor.html")] if native_editor else [])
            + (
                [("native_process_tools", "native_process_tools.py")]
                if native_working_view
                else []
            )
        ):
            runtime["files"][name] = hashlib.sha256(
                Path(__file__).with_name(file).read_bytes()
            ).hexdigest()
        self.binding = DesktopHarnessBinding(
            connection_id="wright-desktop-prototype:" + canonical_digest(runtime),
            image_input_profile="inline-png-jpeg-v1" if image_inputs else "unavailable",
        )
        (self.state / "desktop-binding.json").write_text(
            self.binding.model_dump_json(indent=2)
        )
        (self.state / "desktop-versions.json").write_text(json.dumps(runtime, indent=2))
        service.workflow_model_capabilities = self.capabilities
        service.workflow_reasoning_factory = self.reasoning_for_run

    async def create_session(self, workspace_path):
        return SimpleNamespace(session_id="desktop-" + str(uuid4()))

    async def check_health(self):
        return {"state": "connected" if self.connected else "disconnected"}

    @property
    def connected(self):
        self._expire_clients()
        return bool(self.clients)

    def _expire_clients(self):
        now = self._now()
        self.clients = {
            client: deadline
            for client, deadline in self.clients.items()
            if deadline > now
        }

    def workspace(self, workspace_id, session_id):
        row = self.service.repository.get_by_session(session_id)
        if row is None or row["workspace_id"] != workspace_id:
            raise HTTPException(403, "Desktop workspace/session scope differs")
        root = Path(row["local_path"]).resolve(strict=True)
        if not root.is_relative_to(self.state / "workspaces"):
            raise HTTPException(403, "This connection cannot access that workspace")
        sessions = self.service.repository.list_sessions(workspace_id)
        if not any(
            session["session_id"] == session_id
            and session["agent_id"] == "openai-desktop-harness"
            for session in sessions
        ):
            raise HTTPException(403, "This session belongs to another agent platform")
        return row

    def require_connection(self):
        if not self.connected:
            raise HTTPException(503, "Desktop MCP connection is not active")

    async def capabilities(self):
        if not self.connected:
            return {
                "available": False,
                "reason": "Desktop MCP connection is not active",
            }
        resolver = DesktopWorkflowReasoner(
            self.repository,
            workspace_id="readiness",
            session_id="readiness",
            run_id="readiness",
            binding=self.binding,
        )
        return await resolver.capabilities()

    def reasoning_for_run(self, *, workspace_dir, run_id, execution_context):
        self.require_connection()
        row = self.service.repository.get_by_path(str(Path(workspace_dir).resolve()))
        if row is None:
            raise ValueError("Desktop run has no registered workspace")
        self.workspace(row["workspace_id"], row["session_id"])
        reasoner = DesktopWorkflowReasoner(
            self.repository,
            workspace_id=row["workspace_id"],
            session_id=row["session_id"],
            run_id=run_id,
            binding=self.binding,
            initial_ordinal=self.repository.continuation_ordinal(
                row["workspace_id"], row["session_id"], run_id
            ),
        )
        route = (execution_context or {}).get("model_routing", {}).get("text")
        if route != reasoner.resolution().model_dump(mode="json"):
            raise ValueError("Desktop execution has no matching frozen configuration")
        return WorkflowReasoningCallbacks(
            reasoner.generate_response, reasoner.decide_action
        )

    def router(self):
        router = APIRouter(prefix="/api/desktop")

        async def scoped_plan(workspace_id, session_id, plan_id, request, service):
            self.workspace(workspace_id, session_id)
            from api.routers.mcp import get_mcp_install_plan

            plan = await get_mcp_install_plan(plan_id, request, service)
            if plan.workspace_id != workspace_id or plan.requested_scope != "workspace":
                raise HTTPException(403, "Setup plan belongs to a different scope")
            return plan

        @router.get("/connection-plans")
        async def saved_connection_plans(
            workspace_id: str,
            session_id: str,
            capability_id: str,
            service: McpApiService = Depends(get_mcp_api_service),
        ):
            self.workspace(workspace_id, session_id)
            plans = service.list_workspace_install_plans(workspace_id, capability_id)
            return {
                "workspace_id": workspace_id,
                "session_id": session_id,
                "capability_id": capability_id,
                "limit": 20,
                "plans": [
                    {
                        key: plan.model_dump(mode="json")[key]
                        for key in (
                            "plan_id",
                            "capability_id",
                            "workspace_id",
                            "state",
                            "created_at",
                        )
                    }
                    for plan in plans
                    if plan.workspace_id == workspace_id
                    and plan.requested_scope == "workspace"
                    and plan.capability_id == capability_id
                ],
            }

        @router.get("/connection-plans/{plan_id}")
        async def read_connection_plan(
            plan_id: str,
            workspace_id: str,
            session_id: str,
            request: Request,
            service: McpApiService = Depends(get_mcp_api_service),
        ):
            plan = await scoped_plan(
                workspace_id, session_id, plan_id, request, service
            )
            return {
                "workspace_id": workspace_id,
                "session_id": session_id,
                "plan": plan,
            }

        @router.post(
            "/connection-plans/{plan_id}/approve", dependencies=[Depends(require_admin)]
        )
        async def approve_connection_plan(
            plan_id: str,
            body: ConnectionPlanAction,
            request: Request,
            service: McpApiService = Depends(get_mcp_api_service),
        ):
            await scoped_plan(
                body.workspace_id, body.session_id, plan_id, request, service
            )
            from api.routers.mcp import PlanDigestRequest, approve_mcp_install_plan

            plan = await approve_mcp_install_plan(
                plan_id,
                PlanDigestRequest(plan_digest=body.plan_digest),
                request,
                service,
            )
            return {
                "workspace_id": body.workspace_id,
                "session_id": body.session_id,
                "plan": plan,
            }

        @router.post(
            "/connection-plans/{plan_id}/apply", dependencies=[Depends(require_admin)]
        )
        async def apply_connection_plan(
            plan_id: str,
            body: ConnectionPlanAction,
            request: Request,
            service: McpApiService = Depends(get_mcp_api_service),
        ):
            await scoped_plan(
                body.workspace_id, body.session_id, plan_id, request, service
            )
            from api.routers.mcp import PlanDigestRequest, apply_mcp_install_plan

            run = await apply_mcp_install_plan(
                plan_id,
                PlanDigestRequest(plan_digest=body.plan_digest),
                request,
                service,
            )
            return {
                "workspace_id": body.workspace_id,
                "session_id": body.session_id,
                "onboarding_run": run,
            }

        @router.post("/connection-plans")
        async def connection_plan(
            body: ConnectionPlanRequest,
            request: Request,
            service: McpApiService = Depends(get_mcp_api_service),
        ):
            self.workspace(body.workspace_id, body.session_id)
            # Delegate to the existing owner and its error mapping. This records
            # a reviewable plan only; approval, apply and grants remain separate.
            from api.routers.mcp import InstallPlanRequest, create_mcp_install_plan

            plan = await create_mcp_install_plan(
                InstallPlanRequest(
                    capability_id=body.capability_id,
                    requested_scope="workspace",
                    workspace_id=body.workspace_id,
                    independently_completed_license=body.independently_completed_license,
                ),
                request,
                service,
            )
            return {
                "workspace_id": body.workspace_id,
                "session_id": body.session_id,
                "plan": plan,
            }

        @router.get(
            "/connection-plans/{plan_id}/signin", dependencies=[Depends(require_admin)]
        )
        async def read_signin(
            plan_id: str,
            workspace_id: str,
            session_id: str,
            request: Request,
            service: McpApiService = Depends(get_mcp_api_service),
        ):
            plan = await scoped_plan(
                workspace_id, session_id, plan_id, request, service
            )
            from tool_registry.canonical_catalog import LEGACY_SERVER_IDS

            server_id = LEGACY_SERVER_IDS.get(plan.capability_id, plan.capability_id)
            try:
                pending = self.oauth.read(server_id, workspace_id, session_id, plan_id)
            except ValueError:
                raise HTTPException(
                    403, "Sign-in presentation belongs to another scope"
                ) from None
            # Sensitive transient URL: served only to the authenticated operator.
            from starlette.responses import JSONResponse

            return JSONResponse(
                {
                    "workspace_id": workspace_id,
                    "session_id": session_id,
                    "plan_id": plan_id,
                    **pending,
                },
                headers={"Cache-Control": "no-store"},
            )

        @router.post(
            "/connection-plans/{plan_id}/validate",
            dependencies=[Depends(require_admin)],
        )
        async def validate_connection(
            plan_id: str,
            body: ConnectionPlanAction,
            request: Request,
            service: McpApiService = Depends(get_mcp_api_service),
        ):
            plan = await scoped_plan(
                body.workspace_id, body.session_id, plan_id, request, service
            )
            if plan.state != "completed" or plan.plan_digest != body.plan_digest:
                raise HTTPException(
                    409, "Read the exact completed setup plan before validation"
                )
            from tool_registry.canonical_catalog import LEGACY_SERVER_IDS
            from api.routers.mcp import run_capability_validation_endpoint

            server_id = LEGACY_SERVER_IDS.get(plan.capability_id, plan.capability_id)
            try:
                self.oauth.bind(server_id, body.workspace_id, body.session_id, plan_id)
            except ValueError:
                raise HTTPException(
                    409, "A sign-in operation is already pending"
                ) from None
            try:
                validation = await run_capability_validation_endpoint(
                    server_id, request, service
                )
                return {
                    "workspace_id": body.workspace_id,
                    "session_id": body.session_id,
                    "plan_id": plan_id,
                    "validation": validation,
                }
            finally:
                self.oauth.clear(server_id)

        @router.post(
            "/connection-plans/{plan_id}/enable",
            dependencies=[Depends(require_admin)],
        )
        async def enable_connection(
            plan_id: str,
            body: ConnectionPlanAction,
            request: Request,
            service: McpApiService = Depends(get_mcp_api_service),
        ):
            plan = await scoped_plan(
                body.workspace_id, body.session_id, plan_id, request, service
            )
            if plan.state != "completed" or plan.plan_digest != body.plan_digest:
                raise HTTPException(
                    409, "Read the exact completed setup plan before enabling"
                )
            from tool_registry.canonical_catalog import LEGACY_SERVER_IDS
            from api.routers.mcp import enable_capability_for_workspace_endpoint

            server_id = LEGACY_SERVER_IDS.get(plan.capability_id, plan.capability_id)
            # The existing owner revalidates current evidence/configuration and
            # grants only workspace availability, never invocation approval.
            result = await enable_capability_for_workspace_endpoint(
                body.workspace_id, server_id, request, service
            )
            return {
                "workspace_id": body.workspace_id,
                "session_id": body.session_id,
                "plan_id": plan_id,
                "enablement": result,
            }

        @router.get("/connection")
        async def connection():
            return {
                "connected": self.connected,
                "binding": self.binding.model_dump(mode="json"),
                "model_identity": "unreported; not independently attested",
                "native_tool_ceiling": "unverified; Wright enforces its own API/gateway authority",
                "connection_lease_seconds": CLIENT_LEASE_SECONDS,
                "heartbeat_interval_seconds": HEARTBEAT_INTERVAL_SECONDS,
            }

        @router.post("/connect")
        async def connect(body: ConnectRequest):
            if body.binding != self.binding:
                raise HTTPException(409, "Desktop bridge configuration changed")
            self._expire_clients()
            self.clients[body.client_id] = self._now() + CLIENT_LEASE_SECONDS
            return {
                "connected": True,
                "binding_digest": self.binding.digest,
                "connection_lease_seconds": CLIENT_LEASE_SECONDS,
                "heartbeat_interval_seconds": HEARTBEAT_INTERVAL_SECONDS,
            }

        @router.post("/heartbeat")
        async def heartbeat(body: ConnectRequest):
            if body.binding != self.binding:
                raise HTTPException(409, "Desktop bridge configuration changed")
            if not self.connected or body.client_id not in self.clients:
                raise HTTPException(
                    409, "Desktop connection lease expired; initialize a new connection"
                )
            self.clients[body.client_id] = self._now() + CLIENT_LEASE_SECONDS
            return {"connected": True, "binding_digest": self.binding.digest}

        @router.post("/disconnect")
        async def disconnect(body: ConnectRequest):
            if body.binding != self.binding:
                raise HTTPException(409, "Desktop bridge configuration changed")
            self.clients.pop(body.client_id, None)
            return {"connected": self.connected}

        @router.post("/workspaces", status_code=201)
        async def create_workspace(body: CreateWorkspaceRequest):
            self.require_connection()
            workspace = await self.service.create_workspace(
                body.name, None, self, agent_id="openai-desktop-harness"
            )
            self.service.repository.set_enabled_tools(
                workspace.workspace_id, ["wright__workspace_status"]
            )
            return {
                "workspace_id": workspace.workspace_id,
                "session_id": workspace.session_id,
                "workspace_name": workspace.workspace_name,
                "url": f"http://127.0.0.1:{self.web_port}/workspace/{workspace.workspace_id}?host=openai-desktop",
            }

        @router.get("/workspaces/{workspace_id}")
        async def read_workspace(workspace_id: str, session_id: str):
            row = self.workspace(workspace_id, session_id)
            return {
                "workspace_id": row["workspace_id"],
                "session_id": session_id,
                "workspace_name": row["workspace_name"],
                "url": f"http://127.0.0.1:{self.web_port}/workspace/{workspace_id}?host=openai-desktop",
            }

        @router.get("/workspaces")
        async def list_workspaces():
            items = []
            for row in self.service.lifecycle.list_all():
                root = Path(row["local_path"]).resolve()
                if not root.is_relative_to(self.state / "workspaces"):
                    continue
                for session in self.service.repository.list_sessions(
                    row["workspace_id"]
                ):
                    if session["agent_id"] != "openai-desktop-harness":
                        continue
                    available = root.is_dir()
                    try:
                        self.workspace(row["workspace_id"], session["session_id"])
                    except HTTPException as error:
                        if error.status_code != 403:
                            raise
                        continue
                    except OSError:
                        available = False
                    items.append(
                        {
                            "workspace_id": row["workspace_id"],
                            "session_id": session["session_id"],
                            "workspace_name": row.get("workspace_name") or root.name,
                            "available": available,
                            "reason": None
                            if available
                            else "Workspace directory is unavailable",
                        }
                    )
                    # The repository orders sessions by recency. Discovery offers
                    # that explicit scope; it never activates or rebinds a session.
                    break
            return {
                "workspaces": sorted(
                    items,
                    key=lambda item: (
                        item["workspace_name"].casefold(),
                        item["workspace_id"],
                    ),
                )
            }

        @router.get("/workspaces/{workspace_id}/files")
        async def workspace_files(workspace_id: str, session_id: str):
            row = self.workspace(workspace_id, session_id)
            return {
                "workspace_id": workspace_id,
                "session_id": session_id,
                "tree": await self.service.files.tree(row["local_path"]),
            }

        @router.get("/reasoning")
        async def pending(workspace_id: str, session_id: str):
            self.workspace(workspace_id, session_id)
            return [
                {
                    "request": item.model_dump(mode="json"),
                    "request_digest": item.digest,
                    "binding_digest": item.binding.digest,
                }
                for item in self.repository.pending(workspace_id, session_id)
            ]

        @router.post("/reasoning/respond")
        async def answer(body: AnswerRequest):
            self.require_connection()
            self.workspace(body.workspace_id, body.session_id)
            try:
                task = self.repository.get_request(
                    body.workspace_id, body.session_id, body.response.request_id
                )
                if task.binding != self.binding:
                    raise DesktopHandoffConflict(
                        "The task belongs to another frozen connection"
                    )
                if not self.service.process_interfaces.runs.is_live(task.run_id):
                    raise DesktopHandoffConflict(
                        "The run has no live reasoning consumer; reconcile its retained request"
                    )
                _, accepted = self.repository.submit_response(
                    body.workspace_id, body.session_id, body.response
                )
                return {"accepted": accepted, "response_id": body.response.response_id}
            except KeyError as error:
                raise HTTPException(
                    404, "Request is not in this connection scope"
                ) from error
            except DesktopHandoffConflict as error:
                raise HTTPException(409, str(error)) from error

        return router

    async def qualify_digital_source(self, body, *, operation=""):
        """Prototype boundary: no physical or application execution capabilities."""
        from workspace_service.workflow_source_execution import compile_prompt_workflow

        if (
            not isinstance(body, dict)
            or not isinstance(body.get("session_id"), str)
            or not isinstance(body.get("path"), str)
        ):
            return  # The owning API's request schema will reject it.
        session_id = body.get("session_id")
        row = self.service.repository.get_by_session(session_id)
        if row is None:
            raise HTTPException(403, "Desktop session is unavailable")
        self.workspace(row["workspace_id"], session_id)
        document = await self.service.workflow_sources.read(
            row["local_path"], body.get("path")
        )
        plan = compile_prompt_workflow(document.source)
        if any(
            port.get("kind") == "reference_images"
            for fields in plan.inputs.values()
            for port in fields.get("outputs", [])
        ) or any(step.native_image_format for step in plan.steps):
            raise HTTPException(
                503, "Desktop image input and generation capabilities are not qualified"
            )
        if any(
            step.cad or step.application or step.external_action or step.tool_name
            for step in plan.steps
        ):
            raise HTTPException(
                503,
                "CAD, application, external-action and direct-tool execution remain unavailable in this prototype.",
            )
        tasks = [step for step in plan.steps if step.agent_task]
        if tasks and (
            not self.confined_inspection
            or any(
                step.server_id != "wright-workspace-files"
                or step.task_tool_allowlist != ("inspect_file",)
                or step.max_tool_calls != 1
                for step in tasks
            )
        ):
            raise HTTPException(
                503, "Only separately enabled confined file inspection is qualified"
            )
        if tasks and operation in {
            "/api/workspace/process-interfaces/runs",
            "/api/workspace/workflow-sources/run",
        }:
            # Local setup enrolls an exact existing policy. An HTTP/MCP request
            # cannot create its authority; canonical preparation revalidates
            # source, inputs, schema and output scope before every dispatch.
            digest = body.get("integration_policy_digest")
            if not digest:
                raise HTTPException(
                    403,
                    "Confined inspection requires an exact privately enrolled grant",
                )
            from workspace_service.workflow_source_execution import (
                WorkflowSourceExecutionError,
            )

            try:
                grant = self.service.workflow_integration_policies.get(digest)
            except (KeyError, WorkflowSourceExecutionError) as error:
                raise HTTPException(
                    403, "Confined inspection grant is unavailable"
                ) from error
            identities = grant.get("allowed_tools", [])
            if (
                grant["workspace_id"] != row["workspace_id"]
                or grant["source_path"] != document.path
                or grant["source_digest"] != document.storage_digest
                or grant["approval_mode"] != "manual"
                or len(identities) != 1
                or identities[0]["server_id"] != "wright-workspace-files"
                or identities[0]["name"] != "wright-workspace-files__inspect_file"
            ):
                raise HTTPException(
                    403,
                    "Confined inspection grant differs from the exact read-only scope",
                )
