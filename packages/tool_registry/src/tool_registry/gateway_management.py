from __future__ import annotations

import inspect
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from .gateway_models import GatewaySessionContext, GatewayTool

StatusReader = Callable[[GatewaySessionContext], Mapping[str, Any]]
ToolHandler = Callable[[GatewaySessionContext, Mapping[str, Any]], Any]


@dataclass(frozen=True, slots=True)
class GatewayManagementToolSpec:
    name: str
    description: str
    input_schema: Mapping[str, Any]
    output_schema: Mapping[str, Any] | None = None
    read_only: bool = True
    idempotent: bool = True
    required_approvals: frozenset[str] = frozenset()


class GatewayManagementTools:
    def __init__(
        self,
        *,
        server_status: StatusReader,
        catalog_status: StatusReader,
        workspace_status: StatusReader,
        extra_tools: Sequence[tuple[GatewayManagementToolSpec, ToolHandler]]
        | None = None,
    ) -> None:
        empty_schema = {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        }
        output = {"type": "object"}
        base_specs = (
            GatewayManagementToolSpec(
                "wright__server_status",
                "Report lifecycle state for workspace-enabled MCP servers.",
                empty_schema,
                output,
            ),
            GatewayManagementToolSpec(
                "wright__catalog_status",
                "Report canonical catalog identity and validation status.",
                empty_schema,
                output,
            ),
            GatewayManagementToolSpec(
                "wright__workspace_status",
                "Report the immutable workspace binding for this session.",
                empty_schema,
                output,
            ),
        )
        base_handlers: dict[str, ToolHandler] = {
            "wright__server_status": lambda session, _args: server_status(session),
            "wright__catalog_status": lambda session, _args: catalog_status(session),
            "wright__workspace_status": lambda session, _args: workspace_status(
                session
            ),
        }
        self._specs = {spec.name: spec for spec in base_specs}
        self._handlers = dict(base_handlers)
        for spec, handler in extra_tools or ():
            self._specs[spec.name] = spec
            self._handlers[spec.name] = handler

    def tools(self) -> tuple[GatewayTool, ...]:
        return tuple(
            GatewayTool(
                name=spec.name,
                server_id="wright",
                tool_name=spec.name.removeprefix("wright__"),
                description=spec.description,
                input_schema=spec.input_schema,
                output_schema=spec.output_schema,
                annotations={
                    "readOnlyHint": spec.read_only,
                    "destructiveHint": not spec.read_only,
                    "idempotentHint": spec.idempotent,
                    "openWorldHint": False,
                    "approval_gates": sorted(spec.required_approvals),
                },
                required_approvals=spec.required_approvals,
                provenance={
                    "server_id": "wright",
                    "source": "built-in",
                    "version": "0.1.0",
                },
            )
            for spec in self._specs.values()
        )

    async def call(
        self,
        session: GatewaySessionContext,
        name: str,
        arguments: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        handler = self._handlers.get(name)
        if handler is None:
            raise KeyError(name)
        result = handler(session, dict(arguments or {}))
        if inspect.isawaitable(result):
            result = await result
        return dict(result)
