from __future__ import annotations

import hashlib
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Callable

from workspace_service import (  # type: ignore[import-untyped]
    EngineeringModelService,
    SupportDiagnosticService,
    WorkspaceService,
    build_workspace_service,
    RivetApprovalService,
    RivetCapabilityService,
    RivetGatewayBridge,
    RivetMcpGatewaySettings,
    RivetRunAuthorityService,
    observe_local_model_host,
)
from workspace_service.composition import (
    SurfaceApplication,
    build_surface_application,
)
from data_vault import (
    GatewayRepository,
    ModelArtifactStore,
    ModelRepository,
    RivetMcpRepository,
    upgrade_database,
)
from model_registry.gateway_provider import EngineeringModelGatewayProvider
from tool_registry.canonical_catalog import load_catalog_document
from tool_registry.gateway_adapters import (
    DatabaseGatewayAudit,
    DatabaseGatewayCatalog,
    DatabaseGatewayWorkspace,
    EngineGatewayLifecycle,
)
from tool_registry.gateway_management import (
    GatewayManagementTools,
    GatewayManagementToolSpec,
)
from tool_registry.gateway_models import GatewaySessionContext
from tool_registry.gateway_models import GatewayError, GatewayErrorCode
from tool_registry.gateway_notifications import GatewayNotificationHub
from tool_registry.gateway_resources import GatewayResourceProvider
from tool_registry.gateway_service import GatewayService, SUPPORTED_PROTOCOL_VERSION
from tool_registry.lifecycle_adapters import EngineMcpUiResourceReader
from tool_registry.program_status import ProgramStatusReader
from tool_registry.process_definition import ProcessDefinitionReader
from tool_registry.ui.resources import McpUiResourceStore
from tool_registry.wright_managed_servers import RIVET_WORKFLOW_MUTATION_APPROVAL

from api.config import DATABASE_PATH
from api.brep_gateway import BrepPanelGatewayLifecycle
from api.notifications import GatewayWorkspaceNotifier
from api.rivet_runner_bridge import RivetRunnerBridgeApplication
from workspace_service.brep_panel import (
    BrepPanelError,
    select_brep_application_server,
)
from workspace_service.adapters.runtime import get_active_rivet_workflow


_RIVET_SLUG_SCHEMA = {
    "type": "string",
    "pattern": "^[a-z0-9][a-z0-9-]{0,62}$",
    "description": (
        "Optional workflow slug. Wright uses the currently displayed Rivet "
        "workflow and rejects a different slug."
    ),
}


def _resolve_rivet_tool_slug(
    session: GatewaySessionContext,
    args: dict,
    *,
    require_displayed: bool,
) -> str:
    """Bind Rivet tool calls to the workflow visible in the Wright chat session."""
    binding_session_id = session.binding_session_id or session.session_id
    displayed = get_active_rivet_workflow(DATABASE_PATH, binding_session_id)
    supplied = str(args.get("slug") or "").strip()

    if displayed:
        if supplied and supplied != displayed:
            raise GatewayError(
                GatewayErrorCode.INVALID_INPUT,
                (
                    f'Rivet target mismatch: Wright currently displays "{displayed}". '
                    "Use the displayed workflow. Opening or targeting another "
                    "workflow requires an explicit user action."
                ),
            )
        return displayed

    if require_displayed:
        raise GatewayError(
            GatewayErrorCode.INVALID_INPUT,
            (
                "No Rivet workflow is currently displayed in Wright. Open the "
                "workflow in Wright before modifying or running it."
            ),
        )
    if supplied:
        return supplied
    raise GatewayError(
        GatewayErrorCode.INVALID_INPUT,
        "No Rivet workflow is currently displayed and no workflow slug was provided.",
    )


def _graph_summary_payload(result) -> dict:
    return {
        "workflow_id": result.document.workflow_id,
        "slug": result.document.slug,
        "revision": result.document.revision,
        "etag": result.document.digest,
        "graph": {
            "graph_id": result.graph.graph_id,
            "name": result.graph.name,
            "main": result.graph.main,
            "node_count": len(result.graph.nodes),
            "nodes": [
                {
                    "node_id": node.node_id,
                    "node_type": node.node_type,
                    "title": node.title,
                    "data": dict(node.data),
                    "outgoing_connections": list(node.outgoing_connections),
                }
                for node in result.graph.nodes
            ],
        },
        "issues": [dict(issue) for issue in result.issues],
    }


def _object_schema(properties: dict, required: list[str] | None = None) -> dict:
    return {
        "type": "object",
        "properties": properties,
        "required": required or [],
        "additionalProperties": False,
    }


def _rivet_gateway_tools() -> list[tuple[GatewayManagementToolSpec, object]]:
    read_schema = _object_schema(
        {
            "slug": _RIVET_SLUG_SCHEMA,
            "graph_id": {"type": "string"},
        },
    )
    mutation_properties = {
        "slug": _RIVET_SLUG_SCHEMA,
        "expected_revision": {"type": "integer", "minimum": 1},
        "graph_id": {"type": "string"},
        "node_id": {"type": "string"},
        "source_node_id": {"type": "string"},
        "source_port": {"type": "string"},
        "target_node_ref": {"type": "string"},
        "target_port": {"type": "string"},
        "connection": {"type": "string"},
        "visual_data": {"type": "string"},
        "node": {"type": "object"},
        "node_patch": {"type": "object"},
        "data": {"type": "object"},
    }
    save_schema = _object_schema(
        {
            "slug": _RIVET_SLUG_SCHEMA,
            "expected_revision": {"type": "integer", "minimum": 1},
            "project": {"type": "string"},
            "datasets": {
                "type": "object",
                "additionalProperties": {"type": "string"},
            },
        },
        ["expected_revision", "project"],
    )
    run_schema = _object_schema(
        {
            "slug": _RIVET_SLUG_SCHEMA,
            "expected_generation": {"type": "integer", "minimum": 1},
        },
    )
    write_gate = frozenset({RIVET_WORKFLOW_MUTATION_APPROVAL})
    output = {"type": "object"}

    async def inspect_graph(session: GatewaySessionContext, args: dict) -> dict:
        slug = _resolve_rivet_tool_slug(session, args, require_displayed=False)
        result = await workspace_service().workflow_graph.inspect(
            workspace_dir=session.workspace_path,
            slug=slug,
            graph_id=args.get("graph_id"),
        )
        return _graph_summary_payload(result)

    async def lint_graph(session: GatewaySessionContext, args: dict) -> dict:
        slug = _resolve_rivet_tool_slug(session, args, require_displayed=False)
        result = await workspace_service().workflow_graph.lint(
            workspace_dir=session.workspace_path,
            slug=slug,
            graph_id=args.get("graph_id"),
        )
        return _graph_summary_payload(result)

    def mutation_handler(action: str):
        async def apply(session: GatewaySessionContext, args: dict) -> dict:
            slug = _resolve_rivet_tool_slug(session, args, require_displayed=True)
            result = await workspace_service().workflow_graph.apply(
                workspace_id=session.workspace_id,
                workspace_dir=session.workspace_path,
                slug=slug,
                expected_revision=int(args["expected_revision"]),
                action=action,  # type: ignore[arg-type]
                arguments={key: value for key, value in args.items() if key != "slug"},
            )
            return _graph_summary_payload(result)

        return apply

    async def run_workflow(session: GatewaySessionContext, args: dict) -> dict:
        slug = _resolve_rivet_tool_slug(session, args, require_displayed=True)
        run = await workspace_service().workflow_operations.start(
            workspace_id=session.workspace_id,
            session_id=session.binding_session_id or session.session_id,
            workspace_dir=session.workspace_path,
            slug=slug,
            expected_generation=args.get("expected_generation"),
        )
        return {
            "run_id": run.run_id,
            "workspace_id": run.workspace_id,
            "session_id": run.session_id,
            "workflow_id": run.workflow_id,
            "revision": run.revision,
            "generation": run.generation,
            "state": run.state,
            "reason": run.reason,
        }

    return [
        (
            GatewayManagementToolSpec(
                "wright__rivet_inspect_graph",
                "Inspect the Rivet workflow currently displayed in Wright.",
                read_schema,
                output,
                read_only=True,
            ),
            inspect_graph,
        ),
        (
            GatewayManagementToolSpec(
                "wright__rivet_lint",
                "Lint the Rivet workflow currently displayed in Wright.",
                read_schema,
                output,
                read_only=True,
            ),
            lint_graph,
        ),
        *[
            (
                GatewayManagementToolSpec(
                    f"wright__rivet_{action}",
                    f"{action.replace('_', ' ').title()} in a Wright-owned Rivet workflow.",
                    _object_schema(
                        mutation_properties,
                        ["expected_revision"],
                    ),
                    output,
                    read_only=False,
                    idempotent=action in {"connect_ports", "disconnect_ports"},
                    required_approvals=write_gate,
                ),
                mutation_handler(action),
            )
            for action in (
                "add_node",
                "edit_node",
                "delete_node",
                "connect_ports",
                "disconnect_ports",
            )
        ],
        (
            GatewayManagementToolSpec(
                "wright__rivet_save_revision",
                "Save a full project revision to the Rivet workflow displayed in Wright.",
                save_schema,
                output,
                read_only=False,
                idempotent=False,
                required_approvals=write_gate,
            ),
            mutation_handler("save_revision"),
        ),
        (
            GatewayManagementToolSpec(
                "wright__rivet_run_workflow",
                "Run the Rivet workflow currently displayed in Wright.",
                run_schema,
                output,
                read_only=False,
                idempotent=False,
                required_approvals=write_gate,
            ),
            run_workflow,
        ),
    ]


@lru_cache(maxsize=1)
def workspace_service() -> WorkspaceService:
    return build_workspace_service(DATABASE_PATH, notifier=GatewayWorkspaceNotifier())


@lru_cache(maxsize=1)
def surface_application() -> SurfaceApplication:
    return build_surface_application(DATABASE_PATH)


@lru_cache(maxsize=1)
def engineering_model_application() -> EngineeringModelService:
    return build_engineering_model_application(DATABASE_PATH)


@lru_cache(maxsize=1)
def support_diagnostic_application() -> SupportDiagnosticService:
    return SupportDiagnosticService(DATABASE_PATH)


@lru_cache(maxsize=1)
def program_status_reader() -> ProgramStatusReader:
    import wright_engineering  # type: ignore[import-untyped]

    installed_root = Path(DATABASE_PATH).parent / "program-status"
    packaged_root = (
        Path(wright_engineering.__file__).resolve().parent / "static" / "program-status"
    )
    return ProgramStatusReader(installed_root, packaged_root)


@lru_cache(maxsize=1)
def process_definition_reader() -> ProcessDefinitionReader:
    import wright_engineering  # type: ignore[import-untyped]

    installed_root = Path(DATABASE_PATH).parent / "process-definitions"
    packaged_root = (
        Path(wright_engineering.__file__).resolve().parent
        / "static"
        / "process-definitions"
    )
    return ProcessDefinitionReader(installed_root, packaged_root)


@lru_cache(maxsize=1)
def native_process_service():
    import wright_engineering
    from data_vault.native_process_repository import NativeProcessRepository
    from workspace_service.native_process_service import NativeProcessService

    return NativeProcessService(
        NativeProcessRepository(DATABASE_PATH),
        workspace_service().require_safe_session_workspace,
        Path(wright_engineering.__file__).resolve().parent
        / "static"
        / "native-processes",
    )


def build_native_process_service(
    db_path: str, gateway: GatewayService, workspace: WorkspaceService | None = None
):
    """Compose one native executor using the already configured shared gateway."""
    import wright_engineering
    from data_vault.native_process_runs import NativeRunRepository
    from workspace_service.native_process_service import NativeProcessService
    from workspace_service.native_process_runtime import NativeRuntime
    from workspace_service.native_process_mcp import NativeMcpAdapter

    managed = workspace or workspace_service()
    repository = NativeRunRepository(db_path)
    service = NativeProcessService(
        repository,
        managed.require_safe_session_workspace,
        Path(wright_engineering.__file__).resolve().parent
        / "static"
        / "native-processes",
    )
    adapter = NativeMcpAdapter(gateway, managed.require_safe_session_workspace)
    runtime = NativeRuntime(repository, service.scope, mcp=adapter)
    service.configure_execution(runtime, adapter)
    return service


def build_engineering_model_application(db_path: str) -> EngineeringModelService:
    database = Path(db_path)
    upgrade_database(database)
    data_root = database.parent / "wright-data"
    return EngineeringModelService(
        repository=ModelRepository(str(database)),
        artifact_store=ModelArtifactStore(data_root),
        host_observer=lambda: observe_local_model_host(data_root),
    )


async def close_application_services() -> None:
    program_status_reader.cache_clear()
    process_definition_reader.cache_clear()
    native_process_service.cache_clear()
    if support_diagnostic_application.cache_info().currsize:
        support_diagnostic_application().invalidate_all()
        support_diagnostic_application.cache_clear()
    if surface_application.cache_info().currsize:
        await surface_application().close()
        surface_application.cache_clear()
    if workspace_service.cache_info().currsize:
        await workspace_service().close()
        workspace_service.cache_clear()
    if engineering_model_application.cache_info().currsize:
        await engineering_model_application().shutdown_model_runtime()
    engineering_model_application.cache_clear()


async def close_surface_application_services() -> None:
    if surface_application.cache_info().currsize:
        await surface_application().close()
        surface_application.cache_clear()


def build_api_gateway_service(
    db_path: str,
    engine,
    settings,
    *,
    proxy_brep_via_api: bool = False,
) -> GatewayService:
    repository = GatewayRepository(db_path)
    catalog = DatabaseGatewayCatalog(db_path)
    document = load_catalog_document()
    management = GatewayManagementTools(
        server_status=lambda session: {
            "servers": [
                {
                    "server_id": item.server_id,
                    "status": item.status,
                    "installed": item.is_installed,
                }
                for item in catalog.servers()
            ]
        },
        catalog_status=lambda session: {
            "format_version": document["format_version"],
            "server_count": len(document["servers"]),
        },
        workspace_status=lambda session: {
            "workspace_id": session.workspace_id,
            "session_id": session.binding_session_id or session.session_id,
        },
        extra_tools=_rivet_gateway_tools(),
    )
    ui_reader = EngineMcpUiResourceReader(engine)
    ui_resources = McpUiResourceStore(ui_reader)

    runtime_only_hosts = {
        "bun",
        "docker",
        "java runtime",
        "libgl",
        "node.js",
        "node.js 18+",
        "python",
        "python 3.11+",
        "uv",
        "windows",
        "xvfb",
    }

    def lifecycle_projection(server_id: str) -> dict:
        server = next(
            (item for item in catalog.servers() if item.server_id == server_id), None
        )
        host_required = bool(
            server
            and any(
                str(item).strip().lower() not in runtime_only_hosts
                for item in server.host_software_required
            )
        )
        return {
            "kind": "host_bridge" if host_required else "ordinary",
            "visible_application": host_required,
            "cancellation_supported": True,
            "recovery_action": "inspect_host_application" if host_required else None,
        }

    gateway: GatewayService | None = None

    def publish_discovered_tools(_server_id: str) -> None:
        if gateway is not None:
            gateway.publish_list_changes(tools=True, resources=False)

    engine_lifecycle = EngineGatewayLifecycle(
        engine,
        projection_resolver=lifecycle_projection,
        tools_changed=publish_discovered_tools,
    )
    lifecycle = engine_lifecycle
    if proxy_brep_via_api:
        try:
            brep_server = select_brep_application_server(catalog.servers())
        except BrepPanelError:
            pass
        else:
            lifecycle = BrepPanelGatewayLifecycle(lifecycle, brep_server.server_id)
    model_application = (
        engineering_model_application()
        if Path(db_path).resolve() == Path(DATABASE_PATH).resolve()
        else build_engineering_model_application(db_path)
    )
    gateway = GatewayService(
        workspaces=DatabaseGatewayWorkspace(repository),
        catalog=catalog,
        lifecycle=lifecycle,
        audit=DatabaseGatewayAudit(repository),
        notifier=GatewayNotificationHub(),
        resources=GatewayResourceProvider(),
        management=management,
        mcp_ui_resources=ui_resources,
        capability_providers=(EngineeringModelGatewayProvider(model_application),),
        operation_timeout=settings.operation_timeout_seconds,
        maximum_timeout=settings.maximum_timeout_seconds,
    )
    application = build_rivet_mcp_application(db_path, gateway)
    service = workspace_service()
    service.rivet_mcp_application = application
    return gateway


@dataclass(frozen=True, slots=True)
class RivetMcpApplication:
    settings: RivetMcpGatewaySettings
    repository: RivetMcpRepository
    authorities: RivetRunAuthorityService
    approvals: RivetApprovalService
    capabilities: RivetCapabilityService
    bridge: RivetGatewayBridge
    runner_bridge: RivetRunnerBridgeApplication
    gateway_session_id: Callable[[str, str], str]


def build_rivet_mcp_application(
    db_path: str, gateway: GatewayService
) -> RivetMcpApplication:
    """Build the local MCP run boundary once; routes only delegate into it."""

    settings = RivetMcpGatewaySettings.from_env()
    repository = RivetMcpRepository(db_path)
    authorities = RivetRunAuthorityService()
    approvals = RivetApprovalService(repository=repository)
    initialized_sessions: set[str] = set()

    def gateway_session_id(session_id: str, workspace_id: str) -> str:
        identity = hashlib.sha256(
            f"{workspace_id}\0{session_id}".encode("utf-8")
        ).hexdigest()[:32]
        internal_session_id = f"rivet-{identity}"
        if internal_session_id not in initialized_sessions:
            gateway.open_session(
                session_id=internal_session_id,
                principal_id="wright-rivet-workflow",
                workspace_id=workspace_id,
                transport="legacy",
                binding_session_id=session_id,
            )
            gateway.initialize_session(
                internal_session_id,
                protocol_version=SUPPORTED_PROTOCOL_VERSION,
                client_name="wright-rivet-workflow",
                client_version="2",
                client_capabilities={},
            )
            initialized_sessions.add(internal_session_id)
        return internal_session_id

    capabilities = RivetCapabilityService(gateway, session_resolver=gateway_session_id)
    bridge = RivetGatewayBridge(
        gateway,
        authorities=authorities,
        resolve_binding=repository.get_binding_by_digest,
        validate_current=lambda binding, session_id, workspace_id: (
            capabilities.stale_reasons(
                binding,
                capabilities.discover_gateway_session(
                    session_id=session_id,
                    workspace_id=workspace_id,
                ),
            )
        ),
        approvals=approvals,
        repository=repository,
        approval_ttl_seconds=settings.approval_ttl_seconds,
        automatic_call_approvals=settings.automatic_call_approvals,
    )
    runner_bridge = RivetRunnerBridgeApplication(
        bridge=bridge,
        authorities=authorities,
        repository=repository,
        settings=settings,
    )
    application = RivetMcpApplication(
        settings,
        repository,
        authorities,
        approvals,
        capabilities,
        bridge,
        runner_bridge,
        gateway_session_id,
    )
    service = workspace_service()
    service.workflow_operations.configure_mcp(
        capabilities=capabilities,
        repository=repository,
        settings=settings,
        approvals=approvals,
    )
    service.workflow_runner.configure_mcp(
        repository=repository,
        authorities=authorities,
        approvals=approvals,
        bridge=runner_bridge,
        session_resolver=gateway_session_id,
        settings=settings,
    )
    return application
