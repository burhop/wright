from __future__ import annotations

from fastapi import Depends, HTTPException, Request, status

from api.services.wright_gateway_sync import sync_mcp_server_to_wright_gateway
from workspace_service.adapters.runtime import get_workspace_enabled_tools
from tool_registry import McpEngine
from tool_registry import services as registry_services
from tool_registry.capability_services import CapabilityServiceDependencies
from tool_registry.capability_views import (
    CapabilityCursorError,
    CapabilityFilters,
    build_capability_views,
    find_capability,
    load_workspace_membership,
    paginate_capabilities,
)
from tool_registry.canonical_catalog import load_canonical_entries
from tool_registry.compatibility import (
    load_latest_machine_observation,
    observe_machine,
    save_machine_observation,
)
from tool_registry.services import (
    McpConflictError,
    McpInvalidOperationError,
    McpNotFoundError,
    McpOperationError,
    McpServiceError,
)


def get_mcp_engine(request: Request) -> McpEngine:
    engine = getattr(request.app.state, "mcp_engine", None)
    if not engine:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="MCP engine not initialized in app state",
        )
    return engine


class McpApiService:
    def __init__(
        self,
        engine: McpEngine,
        app_state,
        capability_dependencies: CapabilityServiceDependencies | None = None,
    ) -> None:
        self.engine = engine
        self.app_state = app_state
        self.capability_dependencies = (
            capability_dependencies
            or CapabilityServiceDependencies.for_database(engine.db_path)
        )

    @property
    def db_path(self) -> str:
        return self.engine.db_path

    def list_servers(self):
        return registry_services.list_registered_servers(self.db_path)

    def _capability_entries(self):
        return load_canonical_entries()

    def _machine_observation(self, entries, *, refresh: bool = False):
        if not refresh:
            existing = load_latest_machine_observation(
                self.capability_dependencies.database_path,
                now=self.capability_dependencies.clock(),
            )
            if existing is not None:
                return existing
        executables = {
            dependency for entry in entries for dependency in entry.dependencies.system
        }
        return observe_machine(
            clock=self.capability_dependencies.clock,
            required_executables=executables,
            host_detectors=self.capability_dependencies.machine_detectors,
        )

    def _capability_views(self, entries, observation):
        return build_capability_views(
            entries,
            self.list_servers(),
            observation,
            workspace_membership=load_workspace_membership(self.db_path),
        )

    def list_capabilities(
        self,
        *,
        filters: CapabilityFilters,
        limit: int,
        cursor: str | None,
    ):
        entries = self._capability_entries()
        observation = self._machine_observation(entries)
        views = self._capability_views(entries, observation)
        try:
            return paginate_capabilities(
                entries,
                views,
                filters=filters,
                limit=limit,
                cursor=cursor,
            )
        except CapabilityCursorError as error:
            raise McpInvalidOperationError(str(error)) from error

    def get_capability(self, capability_id: str):
        entries = self._capability_entries()
        observation = self._machine_observation(entries)
        view = find_capability(
            self._capability_views(entries, observation), capability_id
        )
        if view is None:
            raise McpNotFoundError(f"Capability '{capability_id}' not found.")
        return view

    def observe_capability(self, capability_id: str):
        entries = self._capability_entries()
        existing_views = self._capability_views(
            entries, self._machine_observation(entries)
        )
        if find_capability(existing_views, capability_id) is None:
            raise McpNotFoundError(f"Capability '{capability_id}' not found.")
        observation = self._machine_observation(entries, refresh=True)
        save_machine_observation(
            self.capability_dependencies.database_path, observation
        )
        view = find_capability(
            self._capability_views(entries, observation), capability_id
        )
        return {"observation": observation, "compatibility": view.compatibility}

    def register_server(self, body):
        return registry_services.register_server(self.db_path, body)

    async def toggle_server_activation(self, server_id: str, is_active: bool):
        updated = await registry_services.toggle_server_activation(
            self.engine, server_id, is_active
        )
        sync_mcp_server_to_wright_gateway(updated)
        self._notify_gateway_changes()
        return updated

    async def install_server(self, server_id: str, session_id: str | None = None):
        result = await registry_services.install_server(
            self.engine,
            server_id,
            session_id=session_id,
            is_server_enabled_for_session=self._server_enabled_for_session(session_id),
        )
        self._sync_workspace_tools(result.sync_session_id)
        self._notify_gateway_changes(result.sync_session_id)
        return result.server

    async def uninstall_server(self, server_id: str, session_id: str | None = None):
        result = await registry_services.uninstall_server(
            self.engine, server_id, session_id=session_id
        )
        self._sync_workspace_tools(result.sync_session_id)
        self._notify_gateway_changes(result.sync_session_id)
        return result.server

    async def delete_server(self, server_id: str):
        server = await registry_services.delete_registered_server(
            self.engine, server_id
        )
        sync_mcp_server_to_wright_gateway(server)
        self._notify_gateway_changes()
        return server

    def list_tools(self):
        return registry_services.list_registered_tools(self.db_path)

    def set_tool_enabled(self, tool_id: str, is_enabled: bool):
        result = registry_services.set_tool_enabled(self.db_path, tool_id, is_enabled)
        self._notify_gateway_changes()
        return result

    def validate_server(self, server_id: str):
        return registry_services.validate_registered_server(self.db_path, server_id)

    def report_missing_server(self, body):
        return registry_services.report_missing_server(
            self.db_path,
            name=body.name,
            source_url=body.source_url,
            notes=body.notes,
            category=body.category,
        )

    async def check_server_version(self, server_id: str):
        return await registry_services.check_registered_server_version(
            self.db_path, server_id
        )

    async def update_server_version(self, server_id: str):
        return await registry_services.update_registered_server_version(
            self.db_path, server_id
        )

    def get_credential_status(self, server_id: str):
        return registry_services.get_credential_status(self.db_path, server_id)

    def save_credentials(self, server_id: str, credentials: dict):
        return registry_services.save_server_credentials(
            self.db_path, server_id, credentials
        )

    def delete_credentials(self, server_id: str) -> None:
        registry_services.delete_server_credentials(self.db_path, server_id)

    def _server_enabled_for_session(self, session_id: str | None):
        if not session_id:
            return None

        def is_enabled(server) -> bool:
            enabled_tools = get_workspace_enabled_tools(self.db_path, session_id)
            if enabled_tools is None:
                return False
            return (server.name in enabled_tools) or (server.server_id in enabled_tools)

        return is_enabled

    def _sync_workspace_tools(self, session_id: str | None) -> None:
        if not session_id:
            return
        sync_manager = getattr(self.app_state, "agent_sync_manager", None)
        if sync_manager:
            sync_manager.sync_workspace_tools(session_id)

    def _notify_gateway_changes(self, session_id: str | None = None) -> None:
        gateway = getattr(self.app_state, "gateway_service", None)
        if gateway is None:
            return
        workspace_id = None
        if session_id:
            service = getattr(self.app_state, "workspace_service", None)
            repository = getattr(service, "repository", None)
            workspace = repository.get_by_session(session_id) if repository else None
            workspace_id = workspace.get("workspace_id") if workspace else None
        gateway.publish_list_changes(workspace_id=workspace_id)


def get_mcp_api_service(
    request: Request, engine: McpEngine = Depends(get_mcp_engine)
) -> McpApiService:
    return McpApiService(engine, request.app.state)


def mcp_service_http_exception(error: McpServiceError) -> HTTPException:
    if isinstance(error, McpNotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error))
    if isinstance(error, (McpConflictError, McpInvalidOperationError)):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))
    if isinstance(error, McpOperationError):
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(error)
        )
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(error)
    )
