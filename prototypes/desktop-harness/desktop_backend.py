"""Opt-in prototype composition over Wright's existing services and owners."""

import base64
import asyncio
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
from types import SimpleNamespace
import time
from uuid import uuid4
from urllib.parse import urlsplit
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, field_validator, model_validator

from agent_adapters.desktop_reasoning import DesktopWorkflowReasoner
from core.desktop_reasoning import (
    ENGINEERING_IMAGE_PROFILE,
    DesktopHarnessBinding,
    DesktopReasoningResponse,
)
from core.process_validation import canonical_digest, Digest, Identifier
from data_vault.desktop_reasoning_repository import (
    DesktopHandoffConflict,
    DesktopReasoningRepository,
)
from workspace_service.errors import WorkspaceConflictError
from workspace_service.workflow_reasoning_dispatch import WorkflowReasoningCallbacks
from api.services.mcp_services import (
    McpApiService, McpInvalidOperationError, get_mcp_api_service,
)
from api.security import require_admin
from desktop_oauth import DesktopOAuthPresentation
from desktop_credential_form import DesktopCredentialForms, CredentialFormError
from desktop_connection_template import replacement_template
from workspace_service.use_cases.context import WorkspaceConfigurationChanges


CLIENT_LEASE_SECONDS = 30
HEARTBEAT_INTERVAL_SECONDS = 5


class ConnectRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    client_id: str = Field(min_length=1, max_length=128)
    binding: DesktopHarnessBinding


class CreateWorkspaceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=100)


class WorkspaceSettingsReadRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    workspace_id: Identifier
    session_id: Identifier


class WorkspaceSettingsSaveRequest(WorkspaceSettingsReadRequest):
    expected_revision: Digest
    changes: WorkspaceConfigurationChanges


class FileUploadRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    workspace_id: str
    session_id: str
    filename: str = Field(min_length=1, max_length=160)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    content_base64: str = Field(min_length=1, max_length=22369624)


class RecordedRunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    workspace_id: Identifier
    session_id: Identifier
    path: str = Field(min_length=1, max_length=256)
    run_id: Identifier
    source_digest: Digest


class EditorDraftReadRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    workspace_id: Identifier
    session_id: Identifier
    path: str = Field(min_length=1, max_length=256)
    draft_id: str | None = Field(
        default=None, pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]{0,95}$"
    )


class EditorDraftSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    base_storage_revision: int = Field(ge=1)
    base_storage_digest: Digest
    source: str = Field(max_length=1048576)
    applied_source: str = Field(max_length=1048576)
    layout: dict | None
    view: Literal["diagram", "code", "split"]


class EditorDraftSaveRequest(EditorDraftReadRequest):
    draft_id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]{0,95}$")
    request_id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]{0,95}$")
    expected_draft_digest: Digest | None
    snapshot: EditorDraftSnapshot


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


class RemoteConnectionPreviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    workspace_id: str
    session_id: str
    name: str = Field(min_length=1, max_length=100)
    url: str = Field(min_length=1, max_length=2048)

    @field_validator("url")
    @classmethod
    def public_endpoint(cls, value: str) -> str:
        parsed = urlsplit(value)
        if (parsed.scheme != "https" or not parsed.hostname or parsed.username
                or parsed.password or parsed.query or parsed.fragment):
            raise ValueError("Use a public HTTPS MCP endpoint without credentials, query or fragment")
        return value


class LocalConnectionPreviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    workspace_id: str
    session_id: str
    name: str = Field(min_length=1, max_length=100)
    command: str = Field(min_length=1, max_length=500)
    arguments: list[str] = Field(default_factory=list, max_length=512)

    @field_validator("arguments")
    @classmethod
    def bounded_arguments(cls, value: list[str]) -> list[str]:
        if any(len(item) > 4096 for item in value) or sum(map(len, value)) > 65536:
            raise ValueError("Local command arguments exceed the preview limit")
        return value


class ConfiguredLocalConnectionPreviewRequest(LocalConnectionPreviewRequest):
    environment_fields: list[str] = Field(default_factory=list, max_length=32)
    public_environment: dict[str, str] = Field(default_factory=dict, max_length=32)

    @model_validator(mode="after")
    def environment_definitions(self):
        import re
        if (len(set(self.environment_fields)) != len(self.environment_fields)
                or any(not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,127}", key) for key in self.environment_fields)
                or not self.public_environment.keys() <= set(self.environment_fields)
                or any(len(value) > 4096 for value in self.public_environment.values())
                or any(re.search(r"token|secret|password|passwd|api[_-]?key|authorization|credential", key, re.I)
                       for key in self.public_environment)):
            raise ValueError("Unsupported environment fields; secret values belong in the private credential form")
        return self


class ConfiguredRemoteConnectionPreviewRequest(RemoteConnectionPreviewRequest):
    header_fields: list[str] = Field(min_length=1, max_length=32)

    @model_validator(mode="after")
    def header_definitions(self):
        from tool_registry.models import validate_mcp_header_name

        names = [validate_mcp_header_name(key).lower() for key in self.header_fields]
        if len(set(names)) != len(names):
            raise ValueError("Authentication header names must be distinct")
        return self


class ImportedConnectionPlanRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    workspace_id: str
    session_id: str
    preview_token: str = Field(min_length=1, max_length=128)
    draft_id: str = Field(min_length=1, max_length=128)
    draft_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    independently_completed_license: bool = False


class ConnectionPlanAction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    workspace_id: str
    session_id: str
    plan_digest: str = Field(pattern=r"^[a-f0-9]{64}$")


class CredentialFormSaveRequest(ConnectionPlanAction):
    form_id: str = Field(min_length=1, max_length=64)
    ciphertext: str = Field(min_length=1, max_length=24576)


class DisableConnectionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    workspace_id: str
    session_id: str
    capability_id: str = Field(min_length=1, max_length=256)
    server_id: str = Field(min_length=1, max_length=256)


class ConnectionTemplateRequest(DisableConnectionRequest):
    control_digest: str = Field(pattern=r"^[a-f0-9]{64}$")


class ConnectionControlRequest(DisableConnectionRequest):
    control_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    shared_scope: Literal["wright-host"]
    operation: Literal["start", "stop", "uninstall", "tool-enable", "tool-disable"]
    tool_id: str | None = Field(default=None, min_length=1, max_length=512)

    @model_validator(mode="after")
    def exact_operation_subject(self):
        if self.operation.startswith("tool-") != (self.tool_id is not None):
            raise ValueError(
                "Tool switches require one exact tool; provider controls accept none"
            )
        return self


def connection_control_state(
    service, capability_id, server_id, *, repository, include_replacement=False
):
    """Redacted operator view over existing registry configuration and tool owners."""
    from tool_registry.db import get_server, get_tools
    from tool_registry.gateway_adapters import _server_authority_revision

    capability = service.get_capability(capability_id)
    if capability.user_state.server_id != server_id:
        raise HTTPException(
            409, "The registered connection changed; refresh its controls."
        )
    server = get_server(service.db_path, server_id)
    if server is None:
        raise HTTPException(404, "The registered provider is unavailable.")
    tools = sorted(get_tools(service.db_path, server_id), key=lambda tool: tool.tool_id)
    lifecycle = getattr(getattr(service, "engine", None), "lifecycle", None)
    runner = lifecycle.runner_for(server_id) if lifecycle is not None else None
    directory = getattr(runner, "cwd", None)
    workspace = repository.get_by_path(directory) if directory else None
    subjects = [
        {
            "tool_id": tool.tool_id,
            "name": tool.name,
            "enabled": tool.is_enabled,
            "input_schema": tool.input_schema,
            "output_schema": tool.output_schema,
            "annotations": tool.annotations,
        }
        for tool in tools
    ]
    state = {
        "capability_id": capability_id,
        "server_id": server_id,
        "shared_scope": "wright-host",
        "installed": server.is_installed,
        "active": server.is_active,
        "status": server.status,
        "installed_version": server.installed_version,
        "bound_workspace_id": workspace["workspace_id"] if workspace else None,
        "tools": [
            {
                "tool_id": tool.tool_id,
                "name": tool.name,
                "enabled": tool.is_enabled,
                "reported_read_only": tool.annotations.get("readOnlyHint") is True,
            }
            for tool in tools
        ],
    }
    state["control_digest"] = canonical_digest(
        {
            **state,
            "configuration_revision": _server_authority_revision(server),
            "tools": subjects,
        }
    )
    # Projection uses the exact same row as the observed control digest. It is
    # an inert new draft, never an upgrade or transfer of old permission.
    if include_replacement:
        state["replacement"] = replacement_template(server)
    return state


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
        engineering_image_inputs=False,
        enrolled_mcp_tasks=False,
        workspace_mcp_tasks=False,
        local_reviews=False,
        remote_signin_mode="authorization_code",
    ):
        if remote_signin_mode not in {"authorization_code", "device_code"}:
            raise ValueError("Unsupported remote OAuth flow")
        if native_working_view and not native_editor:
            raise ValueError("Native working view requires the native editor resource")
        if image_inputs and engineering_image_inputs:
            raise ValueError("Choose one explicit image-input profile")
        if workspace_mcp_tasks and (enrolled_mcp_tasks or confined_inspection):
            raise ValueError("Choose either workspace authority or private task enrollment")
        image_profile = (
            ENGINEERING_IMAGE_PROFILE
            if engineering_image_inputs
            else "inline-png-jpeg-v1"
            if image_inputs
            else "unavailable"
        )
        self.service = service
        self.state = Path(state).resolve(strict=True)
        self.web_port = web_port
        self.native_editor = native_editor
        self.clients = {}
        self.import_scopes = {}
        self.oauth = DesktopOAuthPresentation()
        self.credential_forms = DesktopCredentialForms()
        self._now = time.monotonic
        self.confined_inspection = confined_inspection
        self.enrolled_mcp_tasks = enrolled_mcp_tasks
        self.workspace_mcp_tasks = workspace_mcp_tasks
        self.local_reviews = local_reviews
        self.image_inputs = image_inputs or engineering_image_inputs
        self.repository = DesktopReasoningRepository(service.db_path)
        runtime = {
            "mcp_sdk": version("mcp"),
            "remote_oauth_flow": remote_signin_mode,
            "credential_form_crypto": version("jwcrypto"),
            "image_inputs": self.image_inputs,
            "image_input_profile": image_profile,
            "enrolled_mcp_tasks": enrolled_mcp_tasks,
            "workspace_mcp_tasks": workspace_mcp_tasks,
            "local_reviews": local_reviews,
            "files": {},
            "confined_inspection": confined_inspection,
            "native_editor": native_editor,
            "native_working_view": native_working_view,
            "connection_lease_seconds": CLIENT_LEASE_SECONDS,
            "heartbeat_interval_seconds": HEARTBEAT_INTERVAL_SECONDS,
        }
        import core.desktop_reasoning as contract
        import agent_adapters.desktop_reasoning as adapter
        import workspace_service.workflow_reasoning_dispatch as dispatch
        import tool_registry.runners.device_oauth as device_oauth
        import tool_registry.runners.sse as remote_transport

        for name, file in (
            ("contract", contract.__file__),
            ("adapter", adapter.__file__),
            ("dispatch", dispatch.__file__),
            ("backend", __file__),
            ("transport", Path(__file__).with_name("mcp_bridge.py")),
            ("device_oauth", device_oauth.__file__),
            ("remote_transport", remote_transport.__file__),
        ):
            runtime["files"][name] = hashlib.sha256(Path(file).read_bytes()).hexdigest()
        for name, file in (
            [("native_source_tools", "native_source_tools.py")]
            + [
                ("desktop_oauth", "desktop_oauth.py"),
                ("desktop_credential_form", "desktop_credential_form.py"),
                ("desktop_connection_template", "desktop_connection_template.py"),
            ]
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
            image_input_profile=image_profile,
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
            capability_id: str | None = None,
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
                    and (capability_id is None or plan.capability_id == capability_id)
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

        @router.post("/connection-imports/preview")
        async def preview_remote_connection(
            body: RemoteConnectionPreviewRequest
            | LocalConnectionPreviewRequest
            | ConfiguredLocalConnectionPreviewRequest
            | ConfiguredRemoteConnectionPreviewRequest,
            request: Request,
            service: McpApiService = Depends(get_mcp_api_service),
        ):
            self.workspace(body.workspace_id, body.session_id)
            from api.routers.mcp import ImportPreviewRequest, preview_mcp_import

            now = self._now()
            self.import_scopes = {
                key: item for key, item in self.import_scopes.items()
                if item[3] > now
            }
            if len(self.import_scopes) >= 128:
                raise HTTPException(429, "Too many active previews; wait for previews to expire")
            configuration = (
                {"name": body.name, "type": "http", "url": body.url}
                if isinstance(body, RemoteConnectionPreviewRequest)
                else {"name": body.name, "type": "stdio", "command": body.command,
                      "args": body.arguments}
            )
            if isinstance(body, ConfiguredLocalConnectionPreviewRequest):
                configuration["env"] = {key: "" for key in body.environment_fields}
                configuration["public_env"] = body.public_environment
            if isinstance(body, ConfiguredRemoteConnectionPreviewRequest):
                configuration["headers"] = {key: "" for key in body.header_fields}
            preview = await preview_mcp_import(
                ImportPreviewRequest(configuration=json.dumps(configuration)),
                request, service,
            )
            token = str(uuid4())
            self.import_scopes[token] = (
                body.workspace_id, body.session_id, preview["preview_id"], now + 900,
            )
            return {"workspace_id": body.workspace_id, "session_id": body.session_id,
                    "preview_token": token, "preview": preview}

        @router.post("/connection-imports/plan")
        async def plan_imported_connection(
            body: ImportedConnectionPlanRequest,
            request: Request,
            service: McpApiService = Depends(get_mcp_api_service),
        ):
            self.workspace(body.workspace_id, body.session_id)
            saved = self.import_scopes.get(body.preview_token)
            if (saved is None or saved[:2] != (body.workspace_id, body.session_id)
                    or saved[3] <= self._now()):
                raise HTTPException(409, "Preview unavailable for this workspace; explicitly preview again")
            from api.routers.mcp import InstallPlanRequest, create_mcp_install_plan

            plan = await create_mcp_install_plan(
                InstallPlanRequest(
                    import_preview_id=saved[2], draft_id=body.draft_id,
                    draft_digest=body.draft_digest, requested_scope="workspace",
                    workspace_id=body.workspace_id,
                    independently_completed_license=body.independently_completed_license,
                ), request, service,
            )
            return {"workspace_id": body.workspace_id, "session_id": body.session_id,
                    "plan": plan}

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

        async def credential_subject(plan_id, workspace_id, session_id, request, service, digest=None):
            plan = await scoped_plan(workspace_id, session_id, plan_id, request, service)
            if plan.state != "completed" or (digest is not None and plan.plan_digest != digest):
                raise HTTPException(409, "Read the exact completed setup plan before configuring credentials")
            from tool_registry.canonical_catalog import LEGACY_SERVER_IDS
            from tool_registry.db import get_server

            server_id = LEGACY_SERVER_IDS.get(plan.capability_id, plan.capability_id)
            server = get_server(service.db_path, server_id)
            if server is None or not server.is_installed:
                raise HTTPException(409, "Provider is not installed")
            status = service.get_credential_status(server_id)
            # Configuration identity, never credential values or transient status.
            configuration = {key: getattr(server, key) for key in (
                "server_id", "type", "transport_variant", "command", "launch_env", "env_vars"
            )}
            configuration["env_vars"] = status["env_vars"]
            configuration["configured"] = status["configured"]
            subject = (workspace_id, session_id, plan_id, plan.plan_digest,
                       server_id, canonical_digest(configuration))
            return plan, server, status, subject

        def credential_status_payload(workspace_id, session_id, plan, server, status):
            return {"workspace_id": workspace_id, "session_id": session_id,
                    "plan_id": plan.plan_id, "plan_digest": plan.plan_digest,
                    "server_id": server.server_id, "active": server.is_active,
                    "configured": status["configured"], "fields": status["env_vars"]}

        @router.get("/connection-plans/{plan_id}/credentials", dependencies=[Depends(require_admin)])
        async def read_credentials(plan_id: str, workspace_id: str, session_id: str,
                                   request: Request, service: McpApiService = Depends(get_mcp_api_service)):
            plan, server, status, _ = await credential_subject(
                plan_id, workspace_id, session_id, request, service)
            from starlette.responses import JSONResponse
            return JSONResponse(credential_status_payload(workspace_id, session_id, plan, server, status),
                                headers={"Cache-Control": "no-store"})

        @router.post("/connection-plans/{plan_id}/credentials/form", dependencies=[Depends(require_admin)])
        async def open_credential_form(plan_id: str, body: ConnectionPlanAction,
                                       request: Request, service: McpApiService = Depends(get_mcp_api_service)):
            plan, server, status, subject = await credential_subject(
                plan_id, body.workspace_id, body.session_id, request, service, body.plan_digest)
            if server.is_active:
                raise HTTPException(409, "Stop the provider through its lifecycle controls before changing credentials")
            try:
                form = self.credential_forms.issue(subject, [field["name"] for field in status["env_vars"]
                                                           if not status["configured"].get(field["name"], False)])
            except CredentialFormError as error:
                raise HTTPException(409, str(error)) from None
            from starlette.responses import JSONResponse
            return JSONResponse({**credential_status_payload(body.workspace_id, body.session_id, plan, server, status),
                                 "form": form}, headers={"Cache-Control": "no-store"})

        @router.post("/connection-plans/{plan_id}/credentials/save", dependencies=[Depends(require_admin)])
        async def save_credentials(plan_id: str, body: CredentialFormSaveRequest,
                                   request: Request, service: McpApiService = Depends(get_mcp_api_service)):
            plan, server, status, subject = await credential_subject(
                plan_id, body.workspace_id, body.session_id, request, service, body.plan_digest)
            if server.is_active:
                raise HTTPException(409, "Stop the provider before changing credentials")
            try:
                values = self.credential_forms.consume(body.form_id, subject, body.ciphertext)
                status = service.save_credentials(server.server_id, values)
            except CredentialFormError as error:
                raise HTTPException(409, str(error)) from None
            except Exception:
                raise HTTPException(503, "Credential save outcome is unconfirmed; read configured status before reopening the form") from None
            return credential_status_payload(body.workspace_id, body.session_id, plan, server, status)

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
            # Recover recorded validation/availability without starting another
            # check. Enable still requalifies current evidence in its owner.
            provider_status = None
            if plan.state == "completed":
                from api.routers.mcp import mcp_service_http_exception
                from tool_registry.services import McpServiceError

                try:
                    view = service.get_capability(server_id)
                except McpServiceError as error:
                    raise mcp_service_http_exception(error) from None
                validation = view.local_validation
                provider_status = {
                    "installed": view.user_state.installed,
                    "active": view.user_state.active,
                    "enabled_here": any(
                        item.get("workspace_id") == workspace_id
                        for item in view.user_state.enabled_workspaces
                    ),
                    "recorded_validation": (
                        {key: validation.get(key) for key in
                         ("evidence_id", "state", "observed_at")}
                        if validation is not None else None
                    ),
                }
            # Sensitive transient URL: served only to the authenticated operator.
            from starlette.responses import JSONResponse

            return JSONResponse(
                {
                    "workspace_id": workspace_id,
                    "session_id": session_id,
                    "plan_id": plan_id,
                    "plan_digest": plan.plan_digest,
                    "provider_status": provider_status,
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

        @router.post("/connections/disable", dependencies=[Depends(require_admin)])
        async def disable_connection(
            body: DisableConnectionRequest,
            service: McpApiService = Depends(get_mcp_api_service),
        ):
            self.workspace(body.workspace_id, body.session_id)
            from api.services.mcp_services import (
                McpServiceError,
                mcp_service_http_exception,
            )

            try:
                result = service.disable_capability_for_workspace(
                    body.capability_id,
                    body.workspace_id,
                    expected_server_id=body.server_id,
                )
            except McpServiceError as error:
                raise mcp_service_http_exception(error) from error
            return {
                "workspace_id": body.workspace_id,
                "session_id": body.session_id,
                "availability": result,
            }

        @router.get("/connection-controls")
        async def read_connection_controls(
            workspace_id: str,
            session_id: str,
            capability_id: str,
            server_id: str,
            service: McpApiService = Depends(get_mcp_api_service),
        ):
            self.workspace(workspace_id, session_id)
            from api.services.mcp_services import (
                McpServiceError,
                mcp_service_http_exception,
            )

            try:
                state = connection_control_state(
                    service,
                    capability_id,
                    server_id,
                    repository=self.service.repository,
                )
            except McpServiceError as error:
                raise mcp_service_http_exception(error) from error
            return {
                "workspace_id": workspace_id,
                "session_id": session_id,
                "state": state,
            }

        @router.post("/connection-replacement", dependencies=[Depends(require_admin)])
        async def prepare_connection_replacement(
            body: ConnectionTemplateRequest,
            service: McpApiService = Depends(get_mcp_api_service),
        ):
            self.workspace(body.workspace_id, body.session_id)
            from api.services.mcp_services import (
                McpServiceError,
                mcp_service_http_exception,
            )

            try:
                state = connection_control_state(
                    service,
                    body.capability_id,
                    body.server_id,
                    repository=self.service.repository,
                    include_replacement=True,
                )
            except McpServiceError as error:
                raise mcp_service_http_exception(error) from error
            if state["control_digest"] != body.control_digest:
                raise HTTPException(
                    409, "Provider configuration changed; refresh controls"
                )
            template = state["replacement"]
            if template is None:
                raise HTTPException(
                    409,
                    "This source cannot be safely prefilled; review catalog setup or import a sanitized configuration",
                )
            return {
                "workspace_id": body.workspace_id,
                "session_id": body.session_id,
                "capability_id": body.capability_id,
                "server_id": body.server_id,
                "control_digest": body.control_digest,
                "configuration": template,
            }

        @router.post("/connection-controls", dependencies=[Depends(require_admin)])
        async def change_connection_control(
            body: ConnectionControlRequest,
            service: McpApiService = Depends(get_mcp_api_service),
        ):
            workspace = self.workspace(body.workspace_id, body.session_id)
            from api.services.mcp_services import (
                McpServiceError,
                mcp_service_http_exception,
            )

            try:
                before = connection_control_state(
                    service,
                    body.capability_id,
                    body.server_id,
                    repository=self.service.repository,
                )
            except McpServiceError as error:
                raise mcp_service_http_exception(error) from error
            if before["control_digest"] != body.control_digest:
                raise HTTPException(
                    409,
                    "Provider or tool state changed; refresh before another action.",
                )
            if not before["installed"]:
                raise HTTPException(
                    409, "Complete provider setup before using shared controls."
                )
            selected = next(
                (tool for tool in before["tools"] if tool["tool_id"] == body.tool_id),
                None,
            )
            if body.operation.startswith("tool-") and selected is None:
                raise HTTPException(
                    403, "This tool does not belong to the selected provider."
                )
            try:
                if body.operation in {"start", "stop"}:
                    await service.toggle_server_activation(
                        body.server_id,
                        body.operation == "start",
                        sync_agent_profile=False,
                        **(
                            {"workspace_dir": workspace["local_path"]}
                            if body.operation == "start"
                            else {}
                        ),
                    )
                elif body.operation == "uninstall":
                    # This shared owner stops and marks uninstalled, retaining
                    # configuration/credentials. No session-specific agent sync.
                    await service.uninstall_server(body.server_id)
                else:
                    service.set_tool_enabled(
                        body.tool_id, body.operation == "tool-enable"
                    )
                state = connection_control_state(
                    service,
                    body.capability_id,
                    body.server_id,
                    repository=self.service.repository,
                )
            except McpInvalidOperationError:
                raise HTTPException(
                    400,
                    "Wright's provider policy rejected this control. Check required credentials and setup.",
                ) from None
            except (McpServiceError, OSError, RuntimeError, ValueError):
                raise HTTPException(
                    503,
                    "Shared control outcome is not confirmed; refresh saved provider state before another action.",
                ) from None
            return {
                "workspace_id": body.workspace_id,
                "session_id": body.session_id,
                "operation": body.operation,
                "tool_id": body.tool_id,
                "state": state,
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
            try:
                workspace = await self.service.create_workspace(
                    body.name, None, self, agent_id="openai-desktop-harness"
                )
            except WorkspaceConflictError:
                raise HTTPException(
                    409,
                    "A workspace with this name or directory already exists. "
                    "Open the existing workspace or choose a different name.",
                ) from None
            self.service.repository.set_enabled_tools(
                workspace.workspace_id, ["wright__workspace_status"]
            )
            return {
                "workspace_id": workspace.workspace_id,
                "session_id": workspace.session_id,
                "workspace_name": workspace.workspace_name,
                "presentation": {
                    "kind": "native-panel" if self.native_editor else "conversation",
                    "browser_available": False,
                    "reopen_tool": "wright_home" if self.native_editor else None,
                },
            }

        @router.get("/workspaces/{workspace_id}")
        async def read_workspace(workspace_id: str, session_id: str):
            row = self.workspace(workspace_id, session_id)
            return {
                "workspace_id": row["workspace_id"],
                "session_id": session_id,
                "workspace_name": row["workspace_name"],
                "presentation": {
                    "kind": "native-panel" if self.native_editor else "conversation",
                    "browser_available": False,
                    "reopen_tool": "wright_home" if self.native_editor else None,
                },
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

        @router.post("/workspace-settings/read")
        async def workspace_settings_read(body: WorkspaceSettingsReadRequest):
            self.workspace(body.workspace_id, body.session_id)
            settings = await self.service.executor.run(
                "workspace.configuration.read",
                lambda: self.service.context.configuration(body.workspace_id),
                timeout_seconds=30,
            )
            return {
                "workspace_id": body.workspace_id,
                "session_id": body.session_id,
                "settings": settings,
            }

        @router.post("/workspace-settings/save", dependencies=[Depends(require_admin)])
        async def workspace_settings_save(body: WorkspaceSettingsSaveRequest):
            from data_vault.workspace_repository import WorkspaceConfigurationConflict

            self.workspace(body.workspace_id, body.session_id)
            try:
                settings = await self.service.executor.run_to_completion(
                    "workspace.configuration.patch",
                    lambda: self.service.context.patch_configuration(
                        body.workspace_id,
                        expected_revision=body.expected_revision,
                        changes=body.changes,
                    ),
                )
            except WorkspaceConfigurationConflict:
                raise HTTPException(
                    409, "Workspace settings changed; read them before saving again"
                ) from None
            except (OSError, RuntimeError):
                raise HTTPException(
                    503, "Settings save is unconfirmed; read saved state before continuing"
                ) from None
            return {
                "workspace_id": body.workspace_id,
                "session_id": body.session_id,
                "settings": settings,
            }

        @router.post("/run-records/read")
        async def read_recorded_run(body: RecordedRunRequest):
            from core.redaction import redact_evidence
            from workspace_service.workflow_run_record import (
                read_workflow_run, WorkflowRunReadError,
            )
            from workspace_service.workflow_results import EngineeringResult

            row = self.workspace(body.workspace_id, body.session_id)
            try:
                record = await asyncio.to_thread(
                    read_workflow_run, row["local_path"], body.path, body.run_id,
                    complete_results=True,
                )
                if record["source_digest"] != body.source_digest:
                    raise HTTPException(409, "Recorded source identity differs")
                # Restore the existing public result defaults after the recorder's
                # compact projection; legacy malformed metadata stays unavailable.
                result_type = TypeAdapter(EngineeringResult)
                def public_result(item):
                    if (item.get("schema_version") != 1
                            or item.get("provenance", {}).get("run_id") != body.run_id):
                        raise ValueError("Unsupported result identity or version")
                    return result_type.validate_python({
                        **item, "exports": [public_result(child) for child in item.get("exports", [])],
                    }).to_dict()
                record["results"] = [
                    public_result(item)
                    for item in record["results"]
                ]
                for previous in record.get("previous_results", []):
                    previous["result"] = public_result(previous["result"])
            except (WorkflowRunReadError, ValueError, TypeError, KeyError):
                raise HTTPException(409, "Exact saved run evidence is unavailable") from None
            return {
                "workspace_id": body.workspace_id, "session_id": body.session_id,
                "workflow_path": body.path, "record": redact_evidence(record),
            }

        @router.post("/editor-drafts/read")
        async def editor_drafts_read(body: EditorDraftReadRequest):
            from workspace_service.workflow_sources import WorkflowSourceStorageError

            row = self.workspace(body.workspace_id, body.session_id)
            try:
                value = await self.service.workflow_sources.editor_drafts_read(
                    row["local_path"],
                    body.path,
                    body.draft_id,
                )
            except (WorkflowSourceStorageError, FileNotFoundError, OSError):
                raise HTTPException(
                    409, "Saved draft is unavailable; your open edits are unchanged"
                ) from None
            return {"workspace_id": body.workspace_id, "session_id": body.session_id, **value}

        @router.post("/editor-drafts/save", dependencies=[Depends(require_admin)])
        async def editor_draft_save(body: EditorDraftSaveRequest):
            from workspace_service.workflow_sources import WorkflowSourceStorageError

            row = self.workspace(body.workspace_id, body.session_id)
            try:
                value = await self.service.workflow_sources.editor_draft_save(
                    row["local_path"],
                    body.path,
                    draft_id=body.draft_id,
                    request_id=body.request_id,
                    expected_draft_digest=body.expected_draft_digest,
                    snapshot=body.snapshot.model_dump(),
                )
            except WorkflowSourceStorageError as error:
                # Validation/CAS cannot have written. Storage/integrity failures
                # may follow a committed write: force exact read reconciliation.
                if error.code in {
                    "workflow_draft_invalid",
                    "workflow_draft_base_invalid",
                    "workflow_draft_conflict",
                    "workflow_draft_limit",
                    "workflow_source_too_large",
                    "workflow_layout_invalid",
                }:
                    raise HTTPException(
                        409, "Draft was not saved; inspect its saved version before continuing"
                    ) from None
                raise HTTPException(
                    503, "Draft save outcome is unconfirmed; read it before another write"
                ) from None
            except OSError:
                raise HTTPException(
                    503, "Draft save outcome is unconfirmed; read it before another write"
                ) from None
            return {"workspace_id": body.workspace_id, "session_id": body.session_id, **value}

        @router.post("/files/upload", dependencies=[Depends(require_admin)])
        async def upload_workspace_file(body: FileUploadRequest):
            row = self.workspace(body.workspace_id, body.session_id)
            try:
                content = base64.b64decode(body.content_base64, validate=True)
                path = await self.service.files.stage_upload(
                    row["local_path"], body.filename, content, body.sha256
                )
            except FileExistsError:
                raise HTTPException(
                    409, "Saved upload differs; inspect the existing file before proceeding."
                ) from None
            except ValueError:
                raise HTTPException(
                    422, "Choose a nonempty file up to 16 MiB with a simple filename and matching SHA-256."
                ) from None
            except OSError:
                raise HTTPException(
                    503, "Upload outcome is not confirmed; check the saved upload before another attempt."
                ) from None
            return {
                "workspace_id": body.workspace_id,
                "session_id": body.session_id,
                "path": path,
                "filename": body.filename,
                "sha256": body.sha256,
                "bytes": len(content),
            }

        @router.get("/workspaces/{workspace_id}/file-preview")
        async def workspace_file_preview(workspace_id: str, session_id: str, path: str):
            row = self.workspace(workspace_id, session_id)
            scope = {
                "workspace_id": workspace_id,
                "session_id": session_id,
                "path": path,
            }
            try:
                result = await self.service.files.read(
                    row["local_path"], path, max_bytes=65536
                )
            except (ValueError, FileNotFoundError, PermissionError):
                return {
                    **scope,
                    "supported": False,
                    "reason": "Text preview is unavailable. Choose an existing workspace text file up to 64 KiB.",
                }
            if result.binary or result.content is None:
                return {
                    **scope,
                    "supported": False,
                    "reason": "This file type has no preview here yet. Inspect run artifacts in Run and results.",
                }
            return {
                **scope,
                "supported": True,
                "content": result.content.decode("utf-8"),
                "sha256": hashlib.sha256(result.content).hexdigest(),
                "bytes": len(result.content),
            }

        @router.get("/workspaces/{workspace_id}/file-download")
        async def workspace_file_download(
            workspace_id: str, session_id: str, path: str
        ):
            row = self.workspace(workspace_id, session_id)
            scope = {
                "workspace_id": workspace_id,
                "session_id": session_id,
                "path": path,
            }
            from workspace_service.workspace_path import WorkspacePath

            try:
                # Match Files visibility; hidden runtime/configuration data is not
                # a downloadable engineering document. The owner checks confinement.
                parts = path.replace("\\", "/").split("/")
                if (
                    len(path) > 4096
                    or any(ord(char) < 32 or ord(char) == 127 for char in path)
                    or any(
                        not part or part.startswith(".") or part == "freecad_mcp_work"
                        for part in parts
                    )
                ):
                    raise ValueError("File is outside the visible file surface")
                WorkspacePath(row["local_path"]).resolve(path, must_exist=True)
                content = await self.service.files.read_bytes(
                    row["local_path"], path, maximum_bytes=16 * 1024 * 1024
                )
            except (ValueError, OSError):
                return {
                    **scope,
                    "supported": False,
                    "reason": "Download unavailable. Choose a visible workspace file up to 16 MiB.",
                }
            return {
                **scope,
                "supported": True,
                "filename": parts[-1],
                "content_base64": base64.b64encode(content).decode("ascii"),
                "sha256": hashlib.sha256(content).hexdigest(),
                "bytes": len(content),
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
        from workspace_service.workflow_source_execution import (
            compile_prompt_workflow,
            WorkflowSourceExecutionError,
        )

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
        if self.workspace_mcp_tasks and body.get("integration_policy_digest") is not None:
            raise HTTPException(
                403, "Workspace task execution cannot use integration-test authority"
            )
        document = await self.service.workflow_sources.read(
            row["local_path"], body.get("path")
        )
        try:
            plan = compile_prompt_workflow(document.source)
        except WorkflowSourceExecutionError as error:
            raise HTTPException(
                400,
                {
                    "code": error.code,
                    "message": str(error),
                    "correction": error.correction,
                },
            ) from error
        if (
            not self.image_inputs
            and any(
                port.get("kind") == "reference_images"
                for fields in plan.inputs.values()
                for port in fields.get("outputs", [])
            )
        ) or any(step.native_image_format for step in plan.steps):
            raise HTTPException(
                503, "Desktop image input and generation capabilities are not qualified"
            )
        from workspace_service.workflow_integration_policy import (
            LOCAL_REVIEW_BINDING,
            LOCAL_REVIEW_DESTINATION,
        )

        reviews = [step.external_action for step in plan.steps if step.external_action]
        local_reviews_only = all(
            action.get("action_kind") == "local_review"
            and action.get("binding") == LOCAL_REVIEW_BINDING
            and action.get("destination") == LOCAL_REVIEW_DESTINATION
            and action.get("action") == {"kind": "local_review", "mode": "review_only"}
            for action in reviews
        )
        if any(step.cad or step.application for step in plan.steps) or (
            reviews
            and (
                not (self.enrolled_mcp_tasks or self.workspace_mcp_tasks or self.local_reviews)
                or not local_reviews_only
            )
        ):
            raise HTTPException(
                503,
                "CAD, application and external-action execution remain unavailable in this prototype.",
            )
        tasks = [step for step in plan.steps if step.agent_task]
        direct = [step for step in plan.steps if step.tool_name]
        if direct and not (self.enrolled_mcp_tasks or self.workspace_mcp_tasks):
            raise HTTPException(
                503, "Direct-tool execution requires separate enrollment qualification"
            )
        if self.workspace_mcp_tasks:
            if any(not step.task_tool_allowlist for step in tasks):
                raise HTTPException(503, "Workspace MCP tasks require explicit tool lists")
            # Normal preparation and dispatch retain gateway workspace grants,
            # exact schemas, bounded decisions and per-action approval checks.
            return
        if reviews and self.local_reviews and not tasks and not direct:
            if operation in {
                "/api/workspace/process-interfaces/runs",
                "/api/workspace/workflow-sources/run",
            }:
                # Reuse the exact manual policy owner with an empty tool set.
                # Local review opt-in cannot grant a tool or external dispatch.
                self.qualify_enrolled_tasks([], document, row, body)
            return
        if (tasks or direct or reviews) and self.enrolled_mcp_tasks:
            if any(not step.task_tool_allowlist for step in tasks):
                raise HTTPException(
                    503, "Enrolled MCP tasks require explicit tool lists"
                )
            if operation in {
                "/api/workspace/process-interfaces/runs",
                "/api/workspace/workflow-sources/run",
            }:
                self.qualify_enrolled_tasks(tasks, document, row, body, direct=direct)
            return
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

    def qualify_enrolled_tasks(self, tasks, document, workspace, body, *, direct=()):
        """Opt-in qualification only; the existing runtime/gateway still owns dispatch."""
        from workspace_service.workflow_source_execution import (
            WorkflowSourceExecutionError,
        )

        digest = body.get("integration_policy_digest")
        if not digest:
            raise HTTPException(
                403, "MCP task qualification requires private enrollment"
            )
        try:
            grant = self.service.workflow_integration_policies.get(digest)
        except (KeyError, WorkflowSourceExecutionError) as error:
            raise HTTPException(403, "MCP task enrollment is unavailable") from error
        expected = {
            (step.server_id, f"{step.server_id}__{name}")
            for step in tasks
            for name in step.task_tool_allowlist
        }
        expected.update((step.server_id, step.tool_name) for step in direct)
        actual = {(tool["server_id"], tool["name"]) for tool in grant["allowed_tools"]}
        schemas = {
            (tool["server_id"], tool["name"]): tool.get("schema_digest")
            for tool in grant["allowed_tools"]
        }
        direct_schemas_match = all(
            step.schema_digest
            and schemas.get((step.server_id, step.tool_name)) == step.schema_digest
            for step in direct
        )
        if (
            grant["workspace_id"] != workspace["workspace_id"]
            or grant["source_path"] != document.path
            or grant["source_digest"] != document.storage_digest
            or grant["approval_mode"] != "manual"
            or actual != expected
            or not direct_schemas_match
        ):
            raise HTTPException(
                403, "MCP task enrollment differs from the exact manual scope"
            )
