"""Exact native bindings over Wright's existing governed MCP gateway.

Schema metadata is ordinary finite JSON, separate from the native process
language's stricter numeric rules. No document can provide executable commands,
paths, approval grants, or a replacement transport through this adapter.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import math
import re
import uuid
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

import structlog
from jsonschema import SchemaError
from jsonschema.validators import validator_for
from referencing.exceptions import Unresolvable
from core.native_process import Finding
from core.native_tracing import native_span, traced_native
from tool_registry.gateway_models import (
    GatewayError,
    GatewayErrorCode,
    GatewaySessionContext,
    GatewayTool,
    GatewayToolResult,
    SessionState,
)
from tool_registry.gateway_service import SUPPORTED_PROTOCOL_VERSION, GatewayService

from .native_process_service import NativeServiceError

_MAX_JSON_BYTES = 1024 * 1024
_BINDING_KEYS = {
    "server_id",
    "tool_name",
    "input_schema_digest",
    "output_schema_digest",
}
_logger = structlog.get_logger(__name__)


class _LimitError(ValueError):
    pass


def _error(code: str, message: str, recovery: str) -> NativeServiceError:
    envelope = {
        "NATIVE_MCP_DENIED": "NATIVE_DENIED",
        "NATIVE_MCP_BINDING_CHANGED": "NATIVE_BINDING_CHANGED",
        "NATIVE_MCP_LIMIT": "NATIVE_LIMIT",
    }.get(code, "NATIVE_NOT_READY")
    return NativeServiceError(
        envelope,
        message,
        recovery,
        findings=(Finding(code.removeprefix("NATIVE_"), message, recovery),),
    )


def _json_text(value: Any) -> str:
    """Stable finite JSON without permissive stringification or key coercion."""

    def check(item: Any, depth: int = 0) -> None:
        if depth > 64:
            raise _LimitError("JSON nesting exceeds the native MCP limit")
        if item is None or type(item) in (str, bool, int):
            return
        if type(item) is float and math.isfinite(item):
            return
        if type(item) is list:
            for child in item:
                check(child, depth + 1)
            return
        if isinstance(item, Mapping) and all(type(key) is str for key in item):
            for child in item.values():
                check(child, depth + 1)
            return
        raise ValueError("MCP value must contain only finite JSON values")

    check(value)
    result = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )
    if len(result.encode("utf-8")) > _MAX_JSON_BYTES:
        raise _LimitError("MCP JSON exceeds the native size limit")
    return result


def schema_digest(schema: Mapping[str, Any] | None) -> str:
    """SHA256 of sorted, compact, UTF-8 finite JSON; absent schema hashes null."""
    return hashlib.sha256(_json_text(schema).encode("utf-8")).hexdigest()


def _descriptor(tool: GatewayTool) -> dict[str, Any]:
    # Round-trip snapshots avoid leaking mutable catalog schema objects.
    input_schema = json.loads(_json_text(tool.input_schema))
    output_schema = json.loads(_json_text(tool.output_schema))

    def check_schema(schema: Any) -> None:
        if schema is None:
            return

        def local_references(value: Any) -> None:
            if isinstance(value, dict):
                for key, child in value.items():
                    if key in {"$ref", "$dynamicRef", "$recursiveRef"} and (
                        not isinstance(child, str) or not child.startswith("#")
                    ):
                        raise ValueError("Native MCP schemas must use local references")
                    local_references(child)
            elif isinstance(value, list):
                for child in value:
                    local_references(child)

        local_references(schema)
        try:
            validator_for(schema).check_schema(schema)
        except SchemaError as exc:
            raise ValueError("Tool schema is invalid") from exc

    check_schema(input_schema)
    check_schema(output_schema)
    return {
        "server_id": tool.server_id,
        "tool_name": tool.tool_name,
        "title": tool.title or tool.tool_name,
        "input_schema_digest": schema_digest(input_schema),
        "output_schema_digest": schema_digest(output_schema),
        "input_schema": input_schema,
        "output_schema": output_schema,
    }


def _binding(binding: Mapping[str, Any]) -> dict[str, str]:
    if (
        not isinstance(binding, Mapping)
        or set(binding) != _BINDING_KEYS
        or any(
            type(value) is not str or not 1 <= len(value) <= 256
            for value in binding.values()
        )
        or any(
            re.fullmatch(r"[0-9a-f]{64}", str(binding.get(key, ""))) is None
            for key in ("input_schema_digest", "output_schema_digest")
        )
    ):
        raise _error(
            "NATIVE_MCP_BINDING_INVALID",
            "The tool binding is malformed.",
            "Choose an exact tool from current workspace bindings.",
        )
    return dict(binding)


class _DispatchRejected(GatewayError):
    def __init__(self, error: NativeServiceError):
        super().__init__(
            GatewayErrorCode.POLICY_DENIED
            if error.code == "NATIVE_DENIED"
            else GatewayErrorCode.INVALID_BINDING,
            "Native binding could not be authorized",
        )
        self.native_error = error


class NativeMcpAdapter:
    def __init__(
        self,
        gateway: GatewayService,
        workspace_resolver: Callable[[str], Mapping[str, Any]],
    ):
        self.gateway = gateway
        self.workspace_resolver = workspace_resolver
        self._owned_sessions: set[str] = set()
        self._closed = False

    async def close(self) -> None:
        """Close this adapter's bounded session set without stopping other callers."""
        self._closed = True
        await asyncio.gather(
            *(
                self.gateway.close_session(session_id)
                for session_id in self._owned_sessions
            )
        )
        self._owned_sessions.clear()

    def _session(self, session_id: str) -> GatewaySessionContext:
        if not isinstance(session_id, str) or not 1 <= len(session_id) <= 200:
            raise _error(
                "NATIVE_MCP_DENIED",
                "The workspace session is invalid.",
                "Select an existing managed workspace.",
            )
        try:
            if self._closed:
                raise ValueError("Native MCP adapter is closed")
            workspace = self.workspace_resolver(session_id)
            # Reopen on every check to revalidate the live database association.
            # Identity depends only on the session, so reassigning its workspace
            # cannot silently move a running call into another workspace.
            identity = hashlib.sha256(session_id.encode("utf-8")).hexdigest()
            internal_id = f"native-process-{identity}"
            if (
                internal_id not in self._owned_sessions
                and len(self._owned_sessions) >= 128
            ):
                raise _error(
                    "NATIVE_MCP_LIMIT",
                    "Native tool session capacity is reached.",
                    "Restart the native runtime to release inactive sessions.",
                )
            context = self.gateway.open_session(
                session_id=internal_id,
                principal_id="wright-native-process",
                workspace_id=str(workspace["workspace_id"]),
                binding_session_id=session_id,
                transport="legacy",
            )
            self._owned_sessions.add(internal_id)
            if (
                Path(context.workspace_path).resolve()
                != Path(str(workspace["local_path"])).resolve()
            ):
                raise _error(
                    "NATIVE_MCP_BINDING_CHANGED",
                    "The workspace location changed.",
                    "Restart the native runtime before calling tools in the relocated workspace.",
                )
            if context.state is SessionState.CREATED:
                context = self.gateway.initialize_session(
                    context.session_id,
                    protocol_version=SUPPORTED_PROTOCOL_VERSION,
                    client_name="wright-native-process",
                    client_version="1",
                    client_capabilities={},
                )
            if context.state is not SessionState.ACTIVE:
                raise ValueError("Gateway session is not active")
            return context
        except NativeServiceError:
            raise
        except Exception as exc:
            raise _error(
                "NATIVE_MCP_DENIED",
                "Workspace tool access is unavailable.",
                "Select an active managed workspace and check its enabled tools.",
            ) from exc

    @traced_native("native.mcp.discover")
    def discover(self, session_id: str) -> dict[str, Any]:
        context = self._session(session_id)
        try:
            descriptors = [
                _descriptor(tool)
                for tool in self.gateway.list_tools(context.session_id)
                if self.gateway.policy.can_call(context, tool, {}).allowed
            ]
            identities = [
                (item["server_id"], item["tool_name"]) for item in descriptors
            ]
            if len(set(identities)) != len(identities):
                raise ValueError("Ambiguous gateway tool identity")
            return {
                "bindings": sorted(
                    descriptors, key=lambda item: (item["server_id"], item["tool_name"])
                )
            }
        except (GatewayError, ValueError, TypeError, UnicodeError) as exc:
            raise _error(
                "NATIVE_MCP_LIMIT"
                if isinstance(exc, _LimitError)
                else "NATIVE_MCP_UNAVAILABLE",
                "Workspace tool discovery is unavailable.",
                "Refresh the installed tool catalog and retry binding discovery.",
            ) from exc

    def _preflight(
        self, session_id: str, binding: Mapping[str, Any], arguments: Mapping[str, Any]
    ) -> tuple[GatewaySessionContext, GatewayTool]:
        selected = _binding(binding)
        context = self._session(session_id)
        try:
            available = self.gateway.list_tools(context.session_id)
            matches = [
                tool
                for tool in available
                if tool.server_id == selected["server_id"]
                and tool.tool_name == selected["tool_name"]
            ]
            if len(matches) != 1:
                raise _error(
                    "NATIVE_MCP_DENIED",
                    "The bound tool is unavailable in this workspace.",
                    "Enable the installed tool, then choose a current exact binding.",
                )
            tool = matches[0]
            if sum(item.name == tool.name for item in available) != 1:
                raise ValueError("Ambiguous gateway dispatch identity")
            descriptor = _descriptor(tool)
            if any(descriptor[key] != selected[key] for key in _BINDING_KEYS):
                raise _error(
                    "NATIVE_MCP_BINDING_CHANGED",
                    "The bound tool schema has changed.",
                    "Review the current schemas and choose the tool binding again.",
                )
            if not self.gateway.policy.can_call(context, tool, arguments).allowed:
                raise _error(
                    "NATIVE_MCP_DENIED",
                    "Workspace policy does not permit this tool call.",
                    "Choose an allowed tool or resolve its approval requirements in tool settings.",
                )
            return context, tool
        except (GatewayError, ValueError, TypeError, UnicodeError) as exc:
            if isinstance(exc, NativeServiceError):
                raise
            raise _error(
                "NATIVE_MCP_LIMIT"
                if isinstance(exc, _LimitError)
                else "NATIVE_MCP_UNAVAILABLE",
                "The current tool contract cannot be verified.",
                "Refresh the tool catalog and choose a current exact binding.",
            ) from exc

    @traced_native("native.mcp.preflight")
    def preflight(self, session_id: str, binding: Mapping[str, Any]) -> dict[str, Any]:
        _, tool = self._preflight(session_id, binding, {})
        return _descriptor(tool)

    async def call(
        self,
        session_id: str,
        binding: Mapping[str, Any],
        arguments: dict[str, Any],
        timeout_seconds: float,
        trace_id: str,
    ) -> str:
        with native_span("native.mcp.call") as span:
            span.set_attribute("native.trace_id", trace_id)
            try:
                result = await self._call(
                    session_id, binding, arguments, timeout_seconds, trace_id
                )
            except asyncio.CancelledError:
                _logger.info("native_mcp_call", trace_id=trace_id, outcome="cancelled")
                raise
            except NativeServiceError as exc:
                span.set_attribute("native.error_code", exc.code)
                _logger.info(
                    "native_mcp_call",
                    trace_id=trace_id,
                    outcome="failed",
                    code=exc.code,
                )
                raise
            _logger.info("native_mcp_call", trace_id=trace_id, outcome="succeeded")
            return result

    async def _call(
        self,
        session_id: str,
        binding: Mapping[str, Any],
        arguments: dict[str, Any],
        timeout_seconds: float,
        trace_id: str,
    ) -> str:
        try:
            if type(arguments) is not dict:
                raise ValueError("Tool arguments must be an object")
            # Freeze caller-owned data across the asynchronous startup boundary.
            arguments = json.loads(_json_text(arguments))
            selected = _binding(binding)
            if (
                type(timeout_seconds) not in (int, float)
                or not math.isfinite(timeout_seconds)
                or timeout_seconds <= 0
            ):
                raise ValueError("Tool timeout must be finite and positive")
            if not isinstance(trace_id, str) or not 1 <= len(trace_id) <= 200:
                raise ValueError("A bounded trace identity is required")
        except (ValueError, TypeError, UnicodeError) as exc:
            if isinstance(exc, NativeServiceError):
                raise
            raise _error(
                "NATIVE_MCP_LIMIT"
                if isinstance(exc, _LimitError)
                else "NATIVE_MCP_INPUT_INVALID",
                "The tool input or timeout is invalid.",
                "Supply a finite JSON object within 1 MiB and a positive timeout.",
            ) from exc
        context, tool = self._preflight(session_id, selected, arguments)

        def guard(original: GatewayTool) -> None:
            try:
                _, current = self._preflight(session_id, selected, arguments)
                if current.name != original.name:
                    raise _error(
                        "NATIVE_MCP_BINDING_CHANGED",
                        "The bound tool identity changed.",
                        "Choose a current exact tool binding.",
                    )
            except NativeServiceError as exc:
                raise _DispatchRejected(exc) from exc

        try:
            result = await self.gateway.call_tool(
                context.session_id,
                f"native-{uuid.uuid4().hex}",
                tool.name,
                arguments,
                timeout=min(float(timeout_seconds), 15.0),
                before_dispatch=guard,
                trace_id=trace_id,
            )
        except _DispatchRejected as exc:
            raise exc.native_error from exc
        except (SchemaError, Unresolvable, RecursionError) as exc:
            # Local references can pass a schema's metaschema check yet fail
            # when the gateway validates actual arguments. Keep that provider
            # contract failure inside the native error boundary.
            raise _error(
                "NATIVE_MCP_SCHEMA_INVALID",
                "The bound tool schema cannot validate this call.",
                "Repair the installed tool's local schema references, then refresh its binding.",
            ) from exc
        except GatewayError as exc:
            codes = {
                GatewayErrorCode.TIMEOUT: (
                    "NATIVE_MCP_TIMEOUT",
                    "The tool call timed out.",
                    "Check tool availability and retry with a new run.",
                ),
                GatewayErrorCode.INVALID_INPUT: (
                    "NATIVE_MCP_INPUT_INVALID",
                    "The arguments do not match the tool schema.",
                    "Review the selected input schema and correct the arguments.",
                ),
                GatewayErrorCode.INVALID_OUTPUT: (
                    "NATIVE_MCP_OUTPUT_INVALID",
                    "The tool result does not match its schema.",
                    "Check the tool's output contract before retrying.",
                ),
                GatewayErrorCode.POLICY_DENIED: (
                    "NATIVE_MCP_DENIED",
                    "Workspace policy denied the tool call.",
                    "Choose an allowed tool or resolve its approval requirements.",
                ),
                GatewayErrorCode.NOT_FOUND: (
                    "NATIVE_MCP_DENIED",
                    "The bound tool is no longer enabled.",
                    "Enable the installed tool and choose its current binding.",
                ),
            }
            raise _error(
                *codes.get(
                    exc.code,
                    (
                        "NATIVE_MCP_UNAVAILABLE",
                        "The tool could not complete the call.",
                        "Check the installed tool's status and retry with a new run.",
                    ),
                )
            ) from exc
        return self._result(result)

    @staticmethod
    def _result(result: GatewayToolResult) -> str:
        if result.is_error:
            denied = result.error_code is GatewayErrorCode.POLICY_DENIED
            raise _error(
                "NATIVE_MCP_DENIED" if denied else "NATIVE_MCP_TOOL_FAILED",
                "Workspace policy denied the call."
                if denied
                else "The tool reported a failure.",
                "Check tool policy and status, then retry with a new run.",
            )
        try:
            if result.structured_content is not None:
                return _json_text(result.structured_content)
            if not result.content or any(
                item.get("type") != "text" or not isinstance(item.get("text"), str)
                for item in result.content
            ):
                raise ValueError("Tool did not return text or structured JSON")
            value = "\n".join(item["text"] for item in result.content)
            if len(value.encode("utf-8")) > _MAX_JSON_BYTES:
                raise _LimitError("Tool text exceeds the native size limit")
            return value
        except (ValueError, TypeError, UnicodeError) as exc:
            raise _error(
                "NATIVE_MCP_LIMIT"
                if isinstance(exc, _LimitError)
                else "NATIVE_MCP_OUTPUT_INVALID",
                "The tool did not return bounded text or finite JSON.",
                "Choose a text or JSON result within the 1 MiB native output limit.",
            ) from exc
