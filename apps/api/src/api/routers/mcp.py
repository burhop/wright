import structlog
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status, Response
from pydantic import BaseModel, Field, model_validator
from tool_registry import (
    McpServer,
    McpServerCreate,
    McpTool,
)
from core.tracing import traced
from api.services.mcp_services import (
    McpApiService,
    get_mcp_api_service,
    mcp_service_http_exception,
)
from tool_registry.services import McpServiceError
from tool_registry.capability_models import (
    CapabilityCompatibility,
    CapabilityList,
    CapabilityView,
    MachineCompatibilityObservation,
    MissingCapabilityReport,
)
from tool_registry.capability_views import CapabilityFilters
from tool_registry.catalog_updates import CatalogUpdateError
from tool_registry.config_import import ConfigurationImportError
from tool_registry.install_plans import InstallPlanError
from tool_registry.onboarding import OnboardingError
from tool_registry.validation_evidence import ValidationEvidenceError
from tool_registry.missing_reports import MissingCapabilityReportError
from api.security import require_admin

logger = structlog.get_logger(__name__)
router = APIRouter()


# ── REST Models ──────────────────────────────────────────────────────────────
class ServersListResponse(BaseModel):
    servers: List[McpServer]


class InstalledServerSummary(BaseModel):
    server_id: str
    name: str
    type: str
    is_active: bool
    is_installed: bool
    description: Optional[str] = None
    source_url: Optional[str] = None


class InstalledServersListResponse(BaseModel):
    servers: List[InstalledServerSummary]


class RegisterServerResponse(BaseModel):
    server_id: str
    name: str
    status: str


class ServerToggleRequest(BaseModel):
    is_active: bool


class ServerToggleResponse(BaseModel):
    server_id: str
    is_active: bool
    status: str
    error_message: Optional[str] = None
    type: Optional[str] = None


class ServerInstallResponse(BaseModel):
    server_id: str
    is_installed: bool
    status: str
    error_message: Optional[str] = None
    type: Optional[str] = None


class ToolsListResponse(BaseModel):
    tools: List[McpTool]


class ToolToggleRequest(BaseModel):
    is_enabled: bool


class ToolToggleResponse(BaseModel):
    tool_id: str
    is_enabled: bool


class CredentialStatusResponse(BaseModel):
    server_id: str
    env_vars: list = []
    configured: dict = {}


class SaveCredentialsRequest(BaseModel):
    credentials: dict


class ValidateServerResponse(BaseModel):
    server_id: str
    environment: str
    status: str
    installability_tier: str
    message: str
    missing_dependencies: list[str] = []
    diagnostics: str = ""
    follow_up_url: Optional[str] = None


class MissingMcpReportRequest(BaseModel):
    name: str
    source_url: Optional[str] = None
    notes: Optional[str] = None
    category: str = "utilities"


class MissingCapabilityReportRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    vendor: str = Field(min_length=1, max_length=200)
    source_url: Optional[str] = Field(default=None, max_length=2048)
    domains: list[str] = Field(min_length=1, max_length=20)
    expected_task: str = Field(min_length=1, max_length=2000)
    platform: Optional[str] = Field(default=None, max_length=200)
    host_application: Optional[str] = Field(default=None, max_length=200)
    notes: Optional[str] = Field(default=None, max_length=4000)
    search_context: dict = Field(default_factory=dict)


class CapabilityObservationResponse(BaseModel):
    observation: MachineCompatibilityObservation
    compatibility: CapabilityCompatibility


class CatalogPreviewRequest(BaseModel):
    envelope: dict | None = None
    configured_channel: str | bool | None = None

    @model_validator(mode="after")
    def exactly_one_source(self):
        selected = int(self.envelope is not None) + int(bool(self.configured_channel))
        if selected != 1:
            raise ValueError("Choose exactly one catalog update source")
        return self


class CatalogActivateRequest(BaseModel):
    preview_digest: str


class CatalogRollbackRequest(BaseModel):
    active_snapshot_id: str
    previous_snapshot_id: str


class ImportPreviewRequest(BaseModel):
    configuration: str = Field(max_length=256 * 1024)


class InstallPlanRequest(BaseModel):
    capability_id: str | None = None
    import_preview_id: str | None = None
    draft_id: str | None = None
    draft_digest: str | None = None
    requested_scope: str = "global_registered"
    workspace_id: str | None = None
    independently_completed_license: bool = False

    @model_validator(mode="after")
    def exactly_one_source(self):
        catalog = self.capability_id is not None
        imported = all(
            value is not None
            for value in (self.import_preview_id, self.draft_id, self.draft_digest)
        )
        if catalog == imported:
            raise ValueError("Choose exactly one catalog or imported MCP source")
        return self


class PlanDigestRequest(BaseModel):
    plan_digest: str = Field(pattern=r"^[a-f0-9]{64}$")


def require_engineer_or_admin(request: Request) -> None:
    settings = request.app.state.security_settings
    if not settings.enforced:
        return
    if getattr(request.state, "principal_role", None) not in {"engineer", "admin"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Engineer or administrator role required",
        )


def _request_actor(request: Request) -> str:
    return str(getattr(request.state, "principal_id", "local-admin"))


def _request_trace(request: Request) -> str:
    return str(getattr(request.state, "trace_id", "catalog-api"))


def _catalog_http_exception(error: CatalogUpdateError, trace_id: str) -> HTTPException:
    return HTTPException(
        status_code=error.status_code,
        detail={
            "code": error.code,
            "message": str(error),
            "recovery": error.recovery,
            "trace_id": trace_id,
        },
    )


def _operation_http_exception(error, trace_id: str) -> HTTPException:
    return HTTPException(
        status_code=error.status_code,
        detail={
            "code": error.code,
            "message": str(error),
            "recovery": "Review the exact input and create a fresh preview or plan.",
            "trace_id": trace_id,
        },
    )


# ── Route Handlers ───────────────────────────────────────────────────────────


@router.get("/catalog/state", dependencies=[Depends(require_admin)])
@traced("mcp.catalog.state")
async def catalog_state(service: McpApiService = Depends(get_mcp_api_service)):
    return service.get_catalog_state()


@router.post("/catalog/updates/preview", dependencies=[Depends(require_admin)])
@traced("mcp.catalog.preview")
async def preview_catalog_update_endpoint(
    body: CatalogPreviewRequest,
    request: Request,
    service: McpApiService = Depends(get_mcp_api_service),
):
    trace_id = _request_trace(request)
    try:
        return service.preview_catalog_update(
            envelope=body.envelope,
            configured_channel=body.configured_channel,
            actor=_request_actor(request),
            trace_id=trace_id,
        )
    except CatalogUpdateError as error:
        raise _catalog_http_exception(error, trace_id)
    except McpServiceError as error:
        raise mcp_service_http_exception(error)


@router.post(
    "/catalog/updates/{preview_id}/activate",
    dependencies=[Depends(require_admin)],
)
@traced("mcp.catalog.activate")
async def activate_catalog_update_endpoint(
    preview_id: str,
    body: CatalogActivateRequest,
    request: Request,
    service: McpApiService = Depends(get_mcp_api_service),
):
    trace_id = _request_trace(request)
    try:
        return service.activate_catalog_update(
            preview_id,
            body.preview_digest,
            actor=_request_actor(request),
            trace_id=trace_id,
        )
    except CatalogUpdateError as error:
        raise _catalog_http_exception(error, trace_id)


@router.post("/catalog/rollback", dependencies=[Depends(require_admin)])
@traced("mcp.catalog.rollback")
async def rollback_catalog_endpoint(
    body: CatalogRollbackRequest,
    request: Request,
    service: McpApiService = Depends(get_mcp_api_service),
):
    trace_id = _request_trace(request)
    try:
        return service.rollback_catalog(
            active_snapshot_id=body.active_snapshot_id,
            previous_snapshot_id=body.previous_snapshot_id,
            actor=_request_actor(request),
            trace_id=trace_id,
        )
    except CatalogUpdateError as error:
        raise _catalog_http_exception(error, trace_id)


@router.get("/capabilities", response_model=CapabilityList)
@traced("mcp.capability.list")
async def list_capabilities(
    search: str | None = None,
    domain: list[str] | None = Query(default=None),
    platform: list[str] | None = Query(default=None),
    lifecycle_stage: list[str] | None = Query(default=None),
    maturity: list[str] | None = Query(default=None),
    evidence_class: list[str] | None = Query(default=None),
    compatibility: list[str] | None = Query(default=None),
    risk: list[str] | None = Query(default=None),
    locality: list[str] | None = Query(default=None),
    host: list[str] | None = Query(default=None),
    validation: list[str] | None = Query(default=None),
    installed: bool | None = None,
    limit: int = Query(default=100, ge=1, le=200),
    cursor: str | None = None,
    service: McpApiService = Depends(get_mcp_api_service),
):
    try:
        return service.list_capabilities(
            filters=CapabilityFilters(
                search=search,
                domains=frozenset(domain or []),
                platforms=frozenset(platform or []),
                lifecycle_stages=frozenset(lifecycle_stage or []),
                maturities=frozenset(maturity or []),
                evidence_classes=frozenset(evidence_class or []),
                compatibility=frozenset(compatibility or []),
                risks=frozenset(risk or []),
                localities=frozenset(locality or []),
                hosts=frozenset(host or []),
                validation=frozenset(validation or []),
                installed=installed,
            ),
            limit=limit,
            cursor=cursor,
        )
    except McpServiceError as error:
        raise mcp_service_http_exception(error)
    except Exception:
        logger.exception("list_capabilities_failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list capabilities.",
        )


@router.get("/capabilities/{capability_id}", response_model=CapabilityView)
@traced("mcp.capability.detail")
async def get_capability(
    capability_id: str,
    service: McpApiService = Depends(get_mcp_api_service),
):
    try:
        return service.get_capability(capability_id)
    except McpServiceError as error:
        raise mcp_service_http_exception(error)


@router.post(
    "/capabilities/{capability_id}/observe",
    response_model=CapabilityObservationResponse,
)
@traced("mcp.capability.observe")
async def observe_capability(
    capability_id: str,
    service: McpApiService = Depends(get_mcp_api_service),
):
    try:
        return service.observe_capability(capability_id)
    except McpServiceError as error:
        raise mcp_service_http_exception(error)


@router.post("/imports/preview")
@traced("mcp.import.preview")
async def preview_mcp_import(
    body: ImportPreviewRequest,
    request: Request,
    service: McpApiService = Depends(get_mcp_api_service),
):
    trace_id = _request_trace(request)
    try:
        return service.preview_import(body.configuration)
    except ConfigurationImportError as error:
        raise _operation_http_exception(error, trace_id)


@router.post("/install-plans")
@traced("mcp.install_plan.create")
async def create_mcp_install_plan(
    body: InstallPlanRequest,
    request: Request,
    service: McpApiService = Depends(get_mcp_api_service),
):
    trace_id = _request_trace(request)
    try:
        return service.create_install_plan(
            capability_id=body.capability_id,
            import_preview_id=body.import_preview_id,
            draft_id=body.draft_id,
            draft_digest=body.draft_digest,
            requested_scope=body.requested_scope,
            workspace_id=body.workspace_id,
            independently_completed_license=body.independently_completed_license,
            actor=_request_actor(request),
        )
    except (ConfigurationImportError, InstallPlanError) as error:
        raise _operation_http_exception(error, trace_id)
    except McpServiceError as error:
        raise mcp_service_http_exception(error)


@router.get("/install-plans/{plan_id}")
@traced("mcp.install_plan.get")
async def get_mcp_install_plan(
    plan_id: str,
    request: Request,
    service: McpApiService = Depends(get_mcp_api_service),
):
    try:
        return service.get_install_plan(plan_id)
    except InstallPlanError as error:
        raise _operation_http_exception(error, _request_trace(request))


@router.post("/install-plans/{plan_id}/approve", dependencies=[Depends(require_admin)])
@traced("mcp.install_plan.approve")
async def approve_mcp_install_plan(
    plan_id: str,
    body: PlanDigestRequest,
    request: Request,
    service: McpApiService = Depends(get_mcp_api_service),
):
    try:
        return service.approve_install_plan(
            plan_id, body.plan_digest, actor=_request_actor(request)
        )
    except InstallPlanError as error:
        raise _operation_http_exception(error, _request_trace(request))


@router.post("/install-plans/{plan_id}/apply", dependencies=[Depends(require_admin)])
@traced("mcp.install_plan.apply")
async def apply_mcp_install_plan(
    plan_id: str,
    body: PlanDigestRequest,
    request: Request,
    service: McpApiService = Depends(get_mcp_api_service),
):
    try:
        return service.apply_install_plan(
            plan_id,
            body.plan_digest,
            actor=_request_actor(request),
            trace_id=_request_trace(request),
        )
    except (InstallPlanError, OnboardingError) as error:
        raise _operation_http_exception(error, _request_trace(request))


@router.get("/onboarding-runs/{run_id}")
@traced("mcp.onboarding_run.get")
async def get_mcp_onboarding_run(
    run_id: str,
    request: Request,
    service: McpApiService = Depends(get_mcp_api_service),
):
    try:
        return service.get_onboarding_run(run_id)
    except OnboardingError as error:
        raise _operation_http_exception(error, _request_trace(request))


@router.post("/onboarding-runs/{run_id}/cancel", dependencies=[Depends(require_admin)])
@traced("mcp.onboarding_run.cancel")
async def cancel_mcp_onboarding_run(
    run_id: str,
    request: Request,
    service: McpApiService = Depends(get_mcp_api_service),
):
    try:
        return service.cancel_onboarding_run(run_id)
    except OnboardingError as error:
        raise _operation_http_exception(error, _request_trace(request))


@router.get("/servers", response_model=ServersListResponse)
@traced("mcp.server.list")
async def list_servers(service: McpApiService = Depends(get_mcp_api_service)):
    try:
        return ServersListResponse(servers=service.list_servers())
    except McpServiceError as e:
        raise mcp_service_http_exception(e)
    except Exception as e:
        logger.exception("list_servers_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list MCP servers: {e}",
        )


@router.get("/servers/installed", response_model=InstalledServersListResponse)
@traced("mcp.server.list_installed")
async def list_installed_servers(
    service: McpApiService = Depends(get_mcp_api_service),
):
    """Return the small server projection needed by the workspace selector."""

    try:
        servers = service.list_servers()
        return InstalledServersListResponse(
            servers=[
                InstalledServerSummary(
                    server_id=server.server_id,
                    name=server.name,
                    type=server.type,
                    is_active=server.is_active,
                    is_installed=server.is_installed,
                    description=server.description,
                    source_url=server.source_url,
                )
                for server in servers
                if server.is_installed
            ]
        )
    except McpServiceError as error:
        raise mcp_service_http_exception(error)
    except Exception as error:
        logger.exception("list_installed_servers_failed", error=str(error))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list installed MCP servers: {error}",
        )


@router.post(
    "/servers",
    response_model=RegisterServerResponse,
    status_code=status.HTTP_201_CREATED,
)
@traced("mcp.server.register")
async def register_server(
    body: McpServerCreate,
    service: McpApiService = Depends(get_mcp_api_service),
):
    logger.info("registering_server", name=body.name, type=body.type)
    try:
        new_server = service.register_server(body)
        return RegisterServerResponse(
            server_id=new_server.server_id,
            name=new_server.name,
            status=new_server.status,
        )
    except McpServiceError as e:
        raise mcp_service_http_exception(e)
    except Exception as e:
        logger.exception("register_server_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register MCP server: {e}",
        )


@router.patch("/servers/{server_id}", response_model=ServerToggleResponse)
@traced("mcp.server.toggle")
async def toggle_server_activation(
    server_id: str,
    body: ServerToggleRequest,
    service: McpApiService = Depends(get_mcp_api_service),
):
    logger.info(
        "toggling_server_activation",
        server_id=server_id,
        target_is_active=body.is_active,
    )

    try:
        updated = await service.toggle_server_activation(server_id, body.is_active)
        return ServerToggleResponse(
            server_id=updated.server_id,
            is_active=updated.is_active,
            status=updated.status,
            error_message=updated.error_message,
            type=updated.type,
        )
    except McpServiceError as e:
        raise mcp_service_http_exception(e)
    except Exception as e:
        logger.exception("toggle_server_failed", server_id=server_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to toggle MCP server activation: {e}",
        )


@router.post("/servers/{server_id}/install", response_model=ServerInstallResponse)
@traced("mcp.server.install")
async def install_server_endpoint(
    server_id: str,
    session_id: Optional[str] = None,
    service: McpApiService = Depends(get_mcp_api_service),
):
    logger.info("installing_server", server_id=server_id, session_id=session_id)

    try:
        updated = await service.install_server(server_id, session_id)
        return ServerInstallResponse(
            server_id=updated.server_id,
            is_installed=updated.is_installed,
            status=updated.status,
            error_message=updated.error_message,
            type=updated.type,
        )
    except McpServiceError as e:
        raise mcp_service_http_exception(e)
    except Exception as e:
        logger.exception("install_server_failed", server_id=server_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to install MCP server: {e}",
        )


@router.post("/servers/{server_id}/validate", response_model=ValidateServerResponse)
@traced("mcp.server.validate")
async def validate_server_endpoint(
    server_id: str,
    service: McpApiService = Depends(get_mcp_api_service),
):
    try:
        result = service.validate_server(server_id)
        return ValidateServerResponse(**result.model_dump())
    except McpServiceError as e:
        raise mcp_service_http_exception(e)


@router.post(
    "/servers/{server_id}/validation-runs",
    dependencies=[Depends(require_engineer_or_admin)],
)
@traced("mcp.capability.validation.run")
async def run_capability_validation_endpoint(
    server_id: str,
    request: Request,
    service: McpApiService = Depends(get_mcp_api_service),
):
    try:
        return await service.run_capability_validation(
            server_id, trace_id=_request_trace(request)
        )
    except McpServiceError as error:
        raise mcp_service_http_exception(error)
    except ValidationEvidenceError as error:
        raise _operation_http_exception(error, _request_trace(request))


@router.post(
    "/workspaces/{workspace_id}/capabilities/{server_id}/enable",
    dependencies=[Depends(require_engineer_or_admin)],
)
@traced("mcp.capability.workspace.enable")
async def enable_capability_for_workspace_endpoint(
    workspace_id: str,
    server_id: str,
    request: Request,
    service: McpApiService = Depends(get_mcp_api_service),
):
    try:
        return service.enable_capability_for_workspace(server_id, workspace_id)
    except ValidationEvidenceError as error:
        raise _operation_http_exception(error, _request_trace(request))
    except McpServiceError as error:
        raise mcp_service_http_exception(error)


@router.post(
    "/missing-capability-reports",
    response_model=MissingCapabilityReport,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_engineer_or_admin)],
)
@traced("mcp.capability.report_missing")
async def submit_missing_capability_report_endpoint(
    body: MissingCapabilityReportRequest,
    request: Request,
    service: McpApiService = Depends(get_mcp_api_service),
):
    try:
        return service.submit_missing_capability_report(
            body,
            reporter=_request_actor(request),
            idempotency_key=request.headers.get("Idempotency-Key"),
        )
    except MissingCapabilityReportError as error:
        raise HTTPException(
            status_code=error.status_code,
            detail={
                "code": error.code,
                "message": error.safe_message,
                "recovery": "Review the report fields and submit again.",
                "trace_id": _request_trace(request),
            },
        ) from error
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "missing_capability_report_invalid",
                "message": "The report contains an unsafe or invalid field.",
                "recovery": "Remove credentials and review the structured fields.",
                "trace_id": _request_trace(request),
            },
        ) from error


@router.post(
    "/servers/report-missing",
    response_model=RegisterServerResponse,
    status_code=status.HTTP_201_CREATED,
)
@traced("mcp.server.report_missing")
async def report_missing_mcp(
    body: MissingMcpReportRequest,
    service: McpApiService = Depends(get_mcp_api_service),
):
    try:
        report = service.report_missing_server(body)
    except McpServiceError as e:
        raise mcp_service_http_exception(e)
    return RegisterServerResponse(
        server_id=report.report_id,
        name=report.name,
        status=report.state,
    )


@router.post("/servers/{server_id}/uninstall", response_model=ServerInstallResponse)
@traced("mcp.server.uninstall")
async def uninstall_server_endpoint(
    server_id: str,
    session_id: Optional[str] = None,
    service: McpApiService = Depends(get_mcp_api_service),
):
    logger.info("uninstalling_server", server_id=server_id, session_id=session_id)

    try:
        updated = await service.uninstall_server(server_id, session_id)
        return ServerInstallResponse(
            server_id=updated.server_id,
            is_installed=updated.is_installed,
            status=updated.status,
            error_message=updated.error_message,
            type=updated.type,
        )
    except McpServiceError as e:
        raise mcp_service_http_exception(e)
    except Exception as e:
        logger.exception("uninstall_server_failed", server_id=server_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to uninstall MCP server: {e}",
        )


@router.delete("/servers/{server_id}", status_code=status.HTTP_204_NO_CONTENT)
@traced("mcp.server.delete")
async def delete_server_endpoint(
    server_id: str, service: McpApiService = Depends(get_mcp_api_service)
):
    logger.info("deleting_server", server_id=server_id)

    try:
        await service.delete_server(server_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except McpServiceError as e:
        raise mcp_service_http_exception(e)
    except Exception as e:
        logger.exception("delete_server_failed", server_id=server_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete MCP server: {e}",
        )


@router.get("/tools", response_model=ToolsListResponse)
@traced("mcp.tool.list")
async def list_tools_endpoint(service: McpApiService = Depends(get_mcp_api_service)):
    try:
        return ToolsListResponse(tools=service.list_tools())
    except McpServiceError as e:
        raise mcp_service_http_exception(e)
    except Exception as e:
        logger.exception("list_tools_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list MCP tools: {e}",
        )


@router.patch("/tools/{tool_id}", response_model=ToolToggleResponse)
@traced("mcp.tool.toggle")
async def toggle_tool_enabled(
    tool_id: str,
    body: ToolToggleRequest,
    service: McpApiService = Depends(get_mcp_api_service),
):
    logger.info("toggling_tool_enabled", tool_id=tool_id, is_enabled=body.is_enabled)

    try:
        service.set_tool_enabled(tool_id, body.is_enabled)
        return ToolToggleResponse(tool_id=tool_id, is_enabled=body.is_enabled)
    except McpServiceError as e:
        raise mcp_service_http_exception(e)
    except Exception as e:
        logger.exception("toggle_tool_failed", tool_id=tool_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to toggle tool enabled state: {e}",
        )


@router.get("/servers/{server_id}/version-check")
@traced("mcp.server.version_check")
async def version_check_endpoint(
    server_id: str, service: McpApiService = Depends(get_mcp_api_service)
):
    try:
        return await service.check_server_version(server_id)
    except McpServiceError as e:
        raise mcp_service_http_exception(e)


@router.post("/servers/{server_id}/update")
@traced("mcp.server.update")
async def update_server_endpoint(
    server_id: str, service: McpApiService = Depends(get_mcp_api_service)
):
    try:
        return await service.update_server_version(server_id)
    except McpServiceError as e:
        raise mcp_service_http_exception(e)


# ── Credential Management Endpoints ──────────────────────────────────────────


@router.get("/servers/{server_id}/credentials", response_model=CredentialStatusResponse)
@traced("mcp.server.credentials.get")
async def get_credential_status(
    server_id: str, service: McpApiService = Depends(get_mcp_api_service)
):
    """Get credential definitions and configured status for a server.
    Never returns actual credential values."""
    try:
        return CredentialStatusResponse(**service.get_credential_status(server_id))
    except McpServiceError as e:
        raise mcp_service_http_exception(e)


@router.put("/servers/{server_id}/credentials", response_model=CredentialStatusResponse)
@traced("mcp.server.credentials.save")
async def save_credentials(
    server_id: str,
    body: SaveCredentialsRequest,
    service: McpApiService = Depends(get_mcp_api_service),
):
    """Save credential values for a server. Values are stored in the local
    secrets file, never in the database or API responses."""
    try:
        status_data = service.save_credentials(server_id, body.credentials)
        return CredentialStatusResponse(**status_data)
    except McpServiceError as e:
        raise mcp_service_http_exception(e)


@router.delete(
    "/servers/{server_id}/credentials", status_code=status.HTTP_204_NO_CONTENT
)
@traced("mcp.server.credentials.delete")
async def delete_credentials_endpoint(
    server_id: str, service: McpApiService = Depends(get_mcp_api_service)
):
    """Delete all saved credentials for a server."""
    logger.info("deleting_credentials", server_id=server_id)
    try:
        service.delete_credentials(server_id)
    except McpServiceError as e:
        raise mcp_service_http_exception(e)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
