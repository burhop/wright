from __future__ import annotations

from functools import lru_cache

from workspace_service import (  # type: ignore[import-untyped]
    WorkspaceService,
    build_workspace_service,
)
from workspace_service.composition import (
    SurfaceApplication,
    build_surface_application,
)
from data_vault import GatewayRepository
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
from tool_registry.gateway_notifications import GatewayNotificationHub
from tool_registry.gateway_resources import GatewayResourceProvider
from tool_registry.gateway_service import GatewayService
from tool_registry.lifecycle_adapters import EngineMcpUiResourceReader
from tool_registry.ui.resources import McpUiResourceStore

from api.config import DATABASE_PATH
from api.notifications import GatewayWorkspaceNotifier


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
            "slug": {"type": "string"},
            "graph_id": {"type": "string"},
        },
        ["slug"],
    )
    mutation_properties = {
        "slug": {"type": "string"},
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
            "slug": {"type": "string"},
            "expected_revision": {"type": "integer", "minimum": 1},
            "project": {"type": "string"},
            "datasets": {
                "type": "object",
                "additionalProperties": {"type": "string"},
            },
        },
        ["slug", "expected_revision", "project"],
    )
    run_schema = _object_schema(
        {
            "slug": {"type": "string"},
            "expected_generation": {"type": "integer", "minimum": 1},
        },
        ["slug"],
    )
    write_gate = frozenset({"workspace_write_approval"})
    output = {"type": "object"}

    async def inspect_graph(session: GatewaySessionContext, args: dict) -> dict:
        result = await workspace_service().workflow_graph.inspect(
            workspace_dir=session.workspace_path,
            slug=str(args["slug"]),
            graph_id=args.get("graph_id"),
        )
        return _graph_summary_payload(result)

    async def lint_graph(session: GatewaySessionContext, args: dict) -> dict:
        result = await workspace_service().workflow_graph.lint(
            workspace_dir=session.workspace_path,
            slug=str(args["slug"]),
            graph_id=args.get("graph_id"),
        )
        return _graph_summary_payload(result)

    def mutation_handler(action: str):
        async def apply(session: GatewaySessionContext, args: dict) -> dict:
            result = await workspace_service().workflow_graph.apply(
                workspace_id=session.workspace_id,
                workspace_dir=session.workspace_path,
                slug=str(args["slug"]),
                expected_revision=int(args["expected_revision"]),
                action=action,  # type: ignore[arg-type]
                arguments={key: value for key, value in args.items() if key != "slug"},
            )
            return _graph_summary_payload(result)

        return apply

    async def run_workflow(session: GatewaySessionContext, args: dict) -> dict:
        run = await workspace_service().workflow_operations.start(
            workspace_id=session.workspace_id,
            session_id=session.binding_session_id or session.session_id,
            workspace_dir=session.workspace_path,
            slug=str(args["slug"]),
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
                "Inspect a Wright-owned Rivet workflow graph from workspace storage.",
                read_schema,
                output,
                read_only=True,
            ),
            inspect_graph,
        ),
        (
            GatewayManagementToolSpec(
                "wright__rivet_lint",
                "Lint a Wright-owned Rivet workflow graph from workspace storage.",
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
                        ["slug", "expected_revision"],
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
                "Save a full Rivet project revision into the active Wright workspace.",
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
                "Run an approved Wright-owned Rivet workflow through Wright/Hermes scope.",
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


async def close_application_services() -> None:
    if surface_application.cache_info().currsize:
        await surface_application().close()
        surface_application.cache_clear()
    if workspace_service.cache_info().currsize:
        await workspace_service().close()
        workspace_service.cache_clear()


async def close_surface_application_services() -> None:
    if surface_application.cache_info().currsize:
        await surface_application().close()
        surface_application.cache_clear()


def build_api_gateway_service(db_path: str, engine, settings) -> GatewayService:
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
    return GatewayService(
        workspaces=DatabaseGatewayWorkspace(repository),
        catalog=catalog,
        lifecycle=EngineGatewayLifecycle(engine),
        audit=DatabaseGatewayAudit(repository),
        notifier=GatewayNotificationHub(),
        resources=GatewayResourceProvider(),
        management=management,
        mcp_ui_resources=ui_resources,
        operation_timeout=settings.operation_timeout_seconds,
        maximum_timeout=settings.maximum_timeout_seconds,
    )
