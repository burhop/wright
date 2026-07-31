from __future__ import annotations

from dataclasses import dataclass

from core.surfaces.models import (
    McpAppSurfaceSource,
    SurfaceDescriptor,
    SurfaceLifecycle,
)
from tool_registry.lifecycle_adapters import EngineMcpUiResourceReader
from tool_registry.ui.resources import McpUiResourceStore
from workspace_service.surfaces import (
    ActorRole,
    McpUiPublication,
    McpUiPublisherPort,
    SurfaceActor,
    SurfaceService,
)


class McpUiPublishingDisabled(RuntimeError):
    pass


class ApiMcpUiPublisher(McpUiPublisherPort):
    def __init__(self, surfaces: SurfaceService, *, enabled: bool) -> None:
        self.surfaces = surfaces
        self.enabled = enabled

    async def publish(self, publication: McpUiPublication) -> SurfaceDescriptor:
        if not self.enabled:
            raise McpUiPublishingDisabled(
                "MCP Apps host is disabled; non-UI fallback remains available"
            )
        actor = SurfaceActor(
            user_id=publication.user_id,
            workspace_id=publication.workspace_id,
            session_id=publication.session_id,
            role=ActorRole.ENGINEER,
        )
        descriptor = await self.surfaces.declare(
            actor=actor,
            source=McpAppSurfaceSource(
                gateway_session_id=publication.gateway_session_id,
                server_id=publication.server_id,
                server_connection_id=publication.server_connection_id,
                resource_uri=publication.resource_uri,
                content_hash=publication.content_hash,
                protocol_version=publication.protocol_version,
                initial_tool_input=publication.initial_tool_input,
                fallback_result=publication.fallback_result,
                declared_host_capabilities=publication.declared_host_capabilities,
            ),
            title=publication.title,
            idempotency_key=publication.idempotency_key,
        )
        if descriptor.lifecycle is not SurfaceLifecycle.DECLARED:
            return descriptor
        starting = await self.surfaces.transition(
            actor=actor,
            surface_id=descriptor.surface_id,
            target=SurfaceLifecycle.STARTING,
            expected_revision=descriptor.revision,
        )
        return await self.surfaces.transition(
            actor=actor,
            surface_id=starting.surface_id,
            target=SurfaceLifecycle.READY,
            expected_revision=starting.revision,
        )


@dataclass(frozen=True, slots=True)
class McpUiComposition:
    resources: McpUiResourceStore
    publisher: ApiMcpUiPublisher


def compose_mcp_ui(
    *,
    engine,
    surfaces: SurfaceService,
    enabled: bool,
) -> McpUiComposition:
    reader = EngineMcpUiResourceReader(engine)
    resources = McpUiResourceStore(reader)
    return McpUiComposition(
        resources=resources,
        publisher=ApiMcpUiPublisher(surfaces, enabled=enabled),
    )
