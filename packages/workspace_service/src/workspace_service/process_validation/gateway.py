"""Existing gateway provider boundary; no additional MCP server or authority."""

import asyncio
from threading import Event

from core.process_validation import canonical_digest, canonical_json
from core.tools import ToolContext
from tool_registry.gateway_models import GatewayError, GatewayErrorCode, GatewayTool

from ..process_validation_tools import ProcessValidationTool
from .application import ValidationApplication


class ProcessValidationGatewayProvider:
    provider_id = "wright-process-validation"
    declared_tool_names = frozenset(
        {
            "wright_validation__evaluate",
            "wright_validation__read",
            "wright_validation__get",
            "wright_validation__export",
        }
    )

    def __init__(self, db_path):
        self.db_path = db_path
        self._active = {}

    def _application(self, session):
        # GatewayService has already resolved and revalidated this session's
        # workspace binding. Arguments cannot provide another root or database.
        return ValidationApplication(
            self.db_path, session.workspace_id, session.workspace_path
        )

    def tools(self, session):
        projected = []
        for operation in ("evaluate", "read", "get", "export"):
            # Schema discovery does not open/migrate the evidence database.
            base = ProcessValidationTool(None, operation)
            contract = base.contract()
            projected.append(
                GatewayTool(
                    name=base.name,
                    server_id=self.provider_id,
                    tool_name=operation,
                    title={
                        "evaluate": "Validate process output",
                        "read": "List validation findings",
                        "get": "Get validation report",
                        "export": "Export validation report",
                    }[operation],
                    description=base.description,
                    input_schema=base.input_schema,
                    output_schema=base.output_schema,
                    annotations={
                        "readOnlyHint": operation != "evaluate",
                        "idempotentHint": True,
                        "destructiveHint": False,
                        "openWorldHint": False,
                    },
                    provenance={
                        "server_revision": "wright.process-validation/1",
                        "capability_digest": canonical_digest(contract),
                    },
                )
            )
        return tuple(projected)

    async def call(
        self,
        session,
        tool,
        arguments,
        *,
        request_id,
        approval_context,
        progress_callback,
    ):
        if tool.name not in self.declared_tool_names:
            raise GatewayError(GatewayErrorCode.NOT_FOUND, "Validation tool not found")
        key = (session.session_id, request_id)
        cancelled = Event()
        self._active[key] = cancelled
        try:
            base = ProcessValidationTool(
                self._application(session), tool.tool_name, cancelled=cancelled
            )
            value = await base.execute(
                arguments,
                context=ToolContext(
                    principal_id=session.principal_id,
                    workspace_id=session.workspace_id,
                    trace_id=request_id,
                    request_id=request_id,
                ),
            )
            return {
                "structuredContent": value,
                "content": [{"type": "text", "text": canonical_json(value)}],
                "isError": False,
            }
        except asyncio.CancelledError:
            cancelled.set()
            raise
        except (KeyError, ValueError, PermissionError) as exc:
            # A measured noncompliance returns normally above. Invalid authority,
            # arguments or unavailable result identity are transport failures.
            raise GatewayError(GatewayErrorCode.INVALID_BINDING, str(exc)) from exc
        finally:
            self._active.pop(key, None)

    async def cancel(self, session, request_id):
        event = self._active.get((session.session_id, request_id))
        if event:
            event.set()

    async def close_session(self, session):
        for (session_id, _), event in tuple(self._active.items()):
            if session_id == session.session_id:
                event.set()

    async def shutdown(self):
        for event in tuple(self._active.values()):
            event.set()
