from __future__ import annotations

from functools import lru_cache

from workspace_service import (  # type: ignore[import-untyped]
    WorkspaceService,
    build_workspace_service,
)
from data_vault import GatewayRepository
from tool_registry.canonical_catalog import load_catalog_document
from tool_registry.gateway_adapters import (
    DatabaseGatewayAudit,
    DatabaseGatewayCatalog,
    DatabaseGatewayWorkspace,
    EngineGatewayLifecycle,
)
from tool_registry.gateway_management import GatewayManagementTools
from tool_registry.gateway_notifications import GatewayNotificationHub
from tool_registry.gateway_resources import GatewayResourceProvider
from tool_registry.gateway_service import GatewayService

from api.config import DATABASE_PATH
from api.notifications import GatewayWorkspaceNotifier


@lru_cache(maxsize=1)
def workspace_service() -> WorkspaceService:
    return build_workspace_service(DATABASE_PATH, notifier=GatewayWorkspaceNotifier())


async def close_application_services() -> None:
    if workspace_service.cache_info().currsize:
        await workspace_service().close()
        workspace_service.cache_clear()


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
            "session_id": session.session_id,
        },
    )
    return GatewayService(
        workspaces=DatabaseGatewayWorkspace(repository),
        catalog=catalog,
        lifecycle=EngineGatewayLifecycle(engine),
        audit=DatabaseGatewayAudit(repository),
        notifier=GatewayNotificationHub(),
        resources=GatewayResourceProvider(),
        management=management,
        operation_timeout=settings.operation_timeout_seconds,
        maximum_timeout=settings.maximum_timeout_seconds,
    )
