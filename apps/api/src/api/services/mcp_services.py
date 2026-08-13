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
from tool_registry.capability_models import CapabilitySnapshotSummary
from tool_registry.canonical_catalog import CatalogFetchError, fetch_catalog_envelope
from tool_registry.catalog_models import CatalogEntry
from tool_registry.catalog_signing import CatalogTrustRoot
from tool_registry.catalog_snapshots import (
    bootstrap_bundled_snapshot,
    get_catalog_state,
    known_catalog_server_ids,
    load_active_catalog,
)
from tool_registry.catalog_updates import (
    CatalogUpdateError,
    activate_catalog_update,
    preview_catalog_update,
    rollback_catalog,
)
from tool_registry.compatibility import (
    load_latest_machine_observation,
    observe_machine,
    save_machine_observation,
)
from tool_registry.config_import import ImportPreviewRepository
from tool_registry.install_plans import (
    InstallPlanError,
    approve_install_plan,
    create_install_plan,
    get_install_plan,
)
from tool_registry.onboarding import (
    apply_install_plan,
    cancel_onboarding_run,
    get_onboarding_run,
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
        self.import_previews = (
            self.capability_dependencies.import_preview_repository
            or ImportPreviewRepository()
        )

    @property
    def db_path(self) -> str:
        return self.engine.db_path

    def list_servers(self):
        return registry_services.list_registered_servers(self.db_path)

    def _capability_context(self):
        bootstrap_bundled_snapshot(self.db_path)
        document, diagnostic = load_active_catalog(self.db_path)
        state = get_catalog_state(self.db_path)
        state["diagnostic"] = diagnostic
        entries = [CatalogEntry.model_validate(entry) for entry in document["servers"]]
        snapshot = CapabilitySnapshotSummary(
            snapshot_id=state["active_snapshot_id"],
            channel=state["active_channel"],
            sequence=state["active_sequence"],
            offline=state["active_channel"] == "bundled",
            updated_at=state["updated_at"],
        )
        return entries, snapshot

    def _capability_entries(self):
        return self._capability_context()[0]

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
        observation = observe_machine(
            clock=self.capability_dependencies.clock,
            required_executables=executables,
            host_detectors=self.capability_dependencies.machine_detectors,
        )
        save_machine_observation(
            self.capability_dependencies.database_path, observation
        )
        return observation

    def _capability_views(self, entries, observation):
        return build_capability_views(
            entries,
            self.list_servers(),
            observation,
            workspace_membership=load_workspace_membership(self.db_path),
            known_catalog_ids=frozenset(known_catalog_server_ids(self.db_path)),
        )

    def list_capabilities(
        self,
        *,
        filters: CapabilityFilters,
        limit: int,
        cursor: str | None,
    ):
        entries, snapshot = self._capability_context()
        observation = self._machine_observation(entries)
        views = self._capability_views(entries, observation)
        try:
            return paginate_capabilities(
                entries,
                views,
                filters=filters,
                limit=limit,
                cursor=cursor,
                snapshot=snapshot,
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

    def get_catalog_state(self):
        bootstrap_bundled_snapshot(self.db_path)
        state = get_catalog_state(self.db_path)
        _, diagnostic = load_active_catalog(self.db_path)
        state["diagnostic"] = diagnostic
        state["configured_channels"] = sorted(
            set(self.capability_dependencies.catalog_channels)
            & set(self.capability_dependencies.trust_roots)
        )
        return state

    def _trust_root(self, channel: str) -> CatalogTrustRoot:
        configured = self.capability_dependencies.trust_roots.get(channel)
        if isinstance(configured, CatalogTrustRoot):
            return configured
        if isinstance(configured, dict):
            try:
                return CatalogTrustRoot(
                    channel=channel,
                    key_id=str(configured["key_id"]),
                    public_key=bytes(configured["public_key"]),
                )
            except (KeyError, TypeError, ValueError) as error:
                raise McpInvalidOperationError(
                    "Catalog trust root is not configured correctly."
                ) from error
        raise McpInvalidOperationError(
            f"No catalog trust root is configured for channel '{channel}'."
        )

    def preview_catalog_update(
        self,
        *,
        envelope: dict | None,
        configured_channel: str | bool | None,
        actor: str,
        trace_id: str,
    ):
        if configured_channel is True:
            available = sorted(
                set(self.capability_dependencies.catalog_channels)
                & set(self.capability_dependencies.trust_roots)
            )
            if len(available) != 1:
                raise McpInvalidOperationError(
                    "Exactly one configured catalog channel is required."
                )
            configured_channel = available[0]
        if isinstance(configured_channel, str):
            channel = self.capability_dependencies.catalog_channels.get(
                configured_channel
            )
            if channel is None:
                raise McpInvalidOperationError(
                    f"Catalog channel '{configured_channel}' is not configured."
                )
            fetcher = (
                self.capability_dependencies.catalog_fetcher or fetch_catalog_envelope
            )
            try:
                envelope = fetcher(channel)
            except CatalogFetchError as error:
                raise CatalogUpdateError(
                    error.code,
                    str(error),
                    "Keep the current catalog and verify the configured channel.",
                    status_code=422,
                ) from error
            channel_name = configured_channel
        else:
            signed = envelope.get("signed") if isinstance(envelope, dict) else None
            channel_name = signed.get("channel") if isinstance(signed, dict) else None
        if not isinstance(envelope, dict) or not isinstance(channel_name, str):
            raise McpInvalidOperationError("A signed catalog envelope is required.")
        return preview_catalog_update(
            self.db_path,
            envelope,
            trust_root=self._trust_root(channel_name),
            actor=actor,
            now=self.capability_dependencies.clock(),
            trace_id=trace_id,
        )

    def activate_catalog_update(
        self,
        preview_id: str,
        preview_digest: str,
        *,
        actor: str,
        trace_id: str,
    ):
        return activate_catalog_update(
            self.db_path,
            preview_id,
            preview_digest,
            actor=actor,
            now=self.capability_dependencies.clock(),
            trace_id=trace_id,
        )

    def rollback_catalog(
        self,
        *,
        active_snapshot_id: str,
        previous_snapshot_id: str,
        actor: str,
        trace_id: str,
    ):
        return rollback_catalog(
            self.db_path,
            expected_active_snapshot_id=active_snapshot_id,
            expected_previous_snapshot_id=previous_snapshot_id,
            actor=actor,
            now=self.capability_dependencies.clock(),
            trace_id=trace_id,
        )

    def preview_import(self, configuration: str):
        return self.import_previews.create(
            configuration, now=self.capability_dependencies.clock()
        )

    def create_install_plan(
        self,
        *,
        capability_id: str | None,
        import_preview_id: str | None,
        draft_id: str | None,
        draft_digest: str | None,
        requested_scope: str,
        workspace_id: str | None,
        independently_completed_license: bool,
        actor: str,
    ):
        entries, snapshot = self._capability_context()
        entry = (
            next((item for item in entries if item.id == capability_id), None)
            if capability_id
            else None
        )
        import_draft = None
        if import_preview_id:
            preview = self.import_previews.get(
                import_preview_id, now=self.capability_dependencies.clock()
            )
            import_draft = next(
                (item for item in preview["drafts"] if item["draft_id"] == draft_id),
                None,
            )
            if import_draft is None:
                raise McpNotFoundError("Imported MCP draft was not found.")
            if import_draft["draft_digest"] != draft_digest:
                raise InstallPlanError(
                    "import_draft_digest_mismatch",
                    "Imported MCP draft digest does not match.",
                )
        if capability_id and entry is None:
            raise McpNotFoundError(f"Capability '{capability_id}' not found.")
        observation = self._machine_observation(entries)
        return create_install_plan(
            self.db_path,
            snapshot_id=snapshot.snapshot_id,
            observation=observation,
            actor=actor,
            requested_scope=requested_scope,
            workspace_id=workspace_id,
            entry=entry,
            import_draft=import_draft,
            independently_completed_license=independently_completed_license,
            now=self.capability_dependencies.clock(),
        )

    def get_install_plan(self, plan_id: str):
        return get_install_plan(self.db_path, plan_id)

    def approve_install_plan(self, plan_id: str, digest: str, *, actor: str):
        return approve_install_plan(
            self.db_path,
            plan_id,
            digest,
            actor=actor,
            now=self.capability_dependencies.clock(),
        )

    def apply_install_plan(
        self, plan_id: str, digest: str, *, actor: str, trace_id: str
    ):
        return apply_install_plan(
            self.db_path,
            plan_id,
            digest,
            adapters=dict(self.capability_dependencies.onboarding_adapters),
            actor=actor,
            now=self.capability_dependencies.clock(),
            trace_id=trace_id,
        )

    def get_onboarding_run(self, run_id: str):
        return get_onboarding_run(self.db_path, run_id)

    def cancel_onboarding_run(self, run_id: str):
        return cancel_onboarding_run(
            self.db_path,
            run_id,
            adapters=dict(self.capability_dependencies.onboarding_adapters),
            now=self.capability_dependencies.clock(),
        )

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
