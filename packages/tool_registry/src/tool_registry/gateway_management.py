from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from .gateway_models import GatewaySessionContext, GatewayTool

StatusReader = Callable[[GatewaySessionContext], Mapping[str, Any]]


class GatewayManagementTools:
    def __init__(
        self,
        *,
        server_status: StatusReader,
        catalog_status: StatusReader,
        workspace_status: StatusReader,
    ) -> None:
        self._handlers = {
            "wright__server_status": server_status,
            "wright__catalog_status": catalog_status,
            "wright__workspace_status": workspace_status,
        }

    def tools(self) -> tuple[GatewayTool, ...]:
        schema = {"type": "object", "properties": {}, "additionalProperties": False}
        output = {"type": "object"}
        descriptions = {
            "wright__server_status": "Report lifecycle state for workspace-enabled MCP servers.",
            "wright__catalog_status": "Report canonical catalog identity and validation status.",
            "wright__workspace_status": "Report the immutable workspace binding for this session.",
        }
        return tuple(
            GatewayTool(
                name=name,
                server_id="wright",
                tool_name=name.removeprefix("wright__"),
                description=descriptions[name],
                input_schema=schema,
                output_schema=output,
                annotations={
                    "readOnlyHint": True,
                    "destructiveHint": False,
                    "idempotentHint": True,
                    "openWorldHint": False,
                    "approval_gates": [],
                },
                provenance={
                    "server_id": "wright",
                    "source": "built-in",
                    "version": "0.1.0",
                },
            )
            for name in self._handlers
        )

    def call(self, session: GatewaySessionContext, name: str) -> dict[str, Any]:
        handler = self._handlers.get(name)
        if handler is None:
            raise KeyError(name)
        return dict(handler(session))
