from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any
from typing import Protocol

from core.surfaces.models import SurfaceDescriptor


@dataclass(frozen=True, slots=True)
class McpUiPublication:
    user_id: str
    workspace_id: str
    session_id: str
    gateway_session_id: str
    server_id: str
    server_connection_id: str
    resource_uri: str
    content_hash: str
    protocol_version: str
    title: str
    idempotency_key: str
    initial_tool_input: Mapping[str, Any] | None = None
    fallback_result: Mapping[str, Any] | None = None
    declared_host_capabilities: frozenset[str] = frozenset()


class McpUiPublisherPort(Protocol):
    """Consumer-owned port for turning an authorized MCP UI into a Surface."""

    async def publish(self, publication: McpUiPublication) -> SurfaceDescriptor: ...


__all__ = ["McpUiPublication", "McpUiPublisherPort"]
