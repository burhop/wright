from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from typing import Any

from mcp.types import LATEST_PROTOCOL_VERSION


MCP_APPS_EXTENSION = "io.modelcontextprotocol/ui"
MCP_APP_MIME_TYPE = "text/html;profile=mcp-app"
NotificationHandler = Callable[[str, Mapping[str, Any]], Awaitable[None] | None]


class ChildProtocolState:
    """Transport-neutral child MCP negotiation and notification state."""

    def __init__(self, *, ui_enabled: bool = False) -> None:
        self.ui_enabled = ui_enabled
        self.protocol_version: str | None = None
        self.server_capabilities: dict[str, Any] = {}
        self.server_info: dict[str, Any] = {}
        self._notification_handlers: list[NotificationHandler] = []

    def initialize_parameters(self) -> dict[str, Any]:
        capabilities: dict[str, Any] = {}
        if self.ui_enabled:
            capabilities["extensions"] = {
                MCP_APPS_EXTENSION: {"mimeTypes": [MCP_APP_MIME_TYPE]}
            }
        return {
            "protocolVersion": LATEST_PROTOCOL_VERSION,
            "capabilities": capabilities,
            "clientInfo": {"name": "wright", "version": "0.1.0"},
        }

    def accept_initialize(self, result: Mapping[str, Any]) -> None:
        version = result.get("protocolVersion")
        if not isinstance(version, str) or not version:
            raise RuntimeError("Child initialize result omitted protocolVersion")
        capabilities = result.get("capabilities")
        if not isinstance(capabilities, Mapping):
            raise RuntimeError("Child initialize result omitted capabilities")
        info = result.get("serverInfo")
        self.protocol_version = version
        self.server_capabilities = dict(capabilities)
        self.server_info = dict(info) if isinstance(info, Mapping) else {}

    def supports(self, capability: str, feature: str | None = None) -> bool:
        value = self.server_capabilities.get(capability)
        if not isinstance(value, Mapping):
            return False
        return feature is None or bool(value.get(feature))

    def add_notification_handler(self, handler: NotificationHandler) -> None:
        self._notification_handlers.append(handler)

    async def handle_notification(
        self,
        method: str,
        params: Mapping[str, Any] | None,
    ) -> None:
        payload = dict(params or {})
        for handler in tuple(self._notification_handlers):
            result = handler(method, payload)
            if result is not None:
                await result
