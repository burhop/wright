"""Private loopback HTTP/NDJSON bridge for one authorized Rivet runner.

This server is deliberately not a FastAPI route. It binds an ephemeral
127.0.0.1 port, has no CORS surface, and delegates every operation to the
Wright authority/binding/gateway services.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import Mapping
from http import HTTPStatus
from typing import Any

import structlog
from data_vault import RivetMcpRepository
from workspace_service import (
    RivetApprovalError,
    RivetAuthorityError,
    RivetBoundInvocation,
    RivetGatewayBridge,
    RivetMcpGatewaySettings,
    RivetRunAuthorityService,
)


logger = structlog.get_logger(__name__)
_BASE_PATH = "/internal/rivet-mcp/v1"
_HEADER_LIMIT = 16 * 1024


class RivetRunnerBridgeError(RuntimeError):
    def __init__(self, code: str, message: str, status: int = 400) -> None:
        super().__init__(message)
        self.code = code
        self.status = status


class RivetRunnerBridgeApplication:
    """Own the exact-origin runner bridge and no other network surface."""

    def __init__(
        self,
        *,
        bridge: RivetGatewayBridge,
        authorities: RivetRunAuthorityService,
        repository: RivetMcpRepository,
        settings: RivetMcpGatewaySettings,
    ) -> None:
        self._bridge = bridge
        self._authorities = authorities
        self._repository = repository
        self._settings = settings
        self._server: asyncio.AbstractServer | None = None
        self._audience: str | None = None
        self._lock = asyncio.Lock()

    async def ensure_started(self) -> str:
        async with self._lock:
            if self._server is None:
                self._server = await asyncio.start_server(
                    self._handle,
                    host="127.0.0.1",
                    port=0,
                    limit=max(_HEADER_LIMIT, self._settings.maximum_request_bytes),
                )
                socket = self._server.sockets[0]
                port = int(socket.getsockname()[1])
                self._audience = f"http://127.0.0.1:{port}{_BASE_PATH}"
                logger.info("rivet_runner_bridge_started", port=port)
            assert self._audience is not None
            return self._audience

    async def close(self) -> None:
        async with self._lock:
            server = self._server
            self._server = None
            self._audience = None
        if server is not None:
            server.close()
            await server.wait_closed()
            logger.info("rivet_runner_bridge_stopped")

    def cancel_authority(self, authority_id: str, *, reason: str) -> int:
        return self._bridge.cancel_authority(authority_id, reason=reason)

    async def _handle(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        peer = writer.get_extra_info("peername")
        try:
            if not peer or peer[0] not in {"127.0.0.1", "::1"}:
                raise RivetRunnerBridgeError(
                    "RIVET_MCP_BRIDGE_DENIED", "Loopback access is required", 401
                )
            method, path, headers, payload = await self._read_request(reader)
            if method != "POST" or path not in {
                f"{_BASE_PATH}/discover",
                f"{_BASE_PATH}/calls",
            }:
                raise RivetRunnerBridgeError(
                    "RIVET_MCP_BRIDGE_DENIED", "Bridge route is unavailable", 404
                )
            supplied = headers.get("authorization", "")
            if not supplied.startswith("Bearer ") or len(supplied) > 1024:
                raise RivetRunnerBridgeError(
                    "RIVET_MCP_AUTHORITY_UNAVAILABLE", "Authority is unavailable", 401
                )
            token = supplied[7:]
            if not token or any(character.isspace() for character in token):
                raise RivetRunnerBridgeError(
                    "RIVET_MCP_AUTHORITY_UNAVAILABLE", "Authority is unavailable", 401
                )
            if path.endswith("/discover"):
                await self._discover(writer, token, payload)
            else:
                await self._call(writer, token, payload)
        except (
            RivetRunnerBridgeError,
            RivetAuthorityError,
            RivetApprovalError,
        ) as error:
            await self._error(writer, error)
        except (asyncio.IncompleteReadError, asyncio.LimitOverrunError, ValueError):
            await self._error(
                writer,
                RivetRunnerBridgeError(
                    "RIVET_MCP_BRIDGE_DENIED", "Bridge request is invalid", 400
                ),
            )
        except Exception as error:  # safe boundary: never expose internals to Node
            logger.warning(
                "rivet_runner_bridge_failed", error_type=type(error).__name__
            )
            await self._error(
                writer,
                RivetRunnerBridgeError(
                    "RIVET_MCP_CALL_FAILED", "The governed MCP call failed", 502
                ),
            )
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except (BrokenPipeError, ConnectionResetError):
                pass

    async def _read_request(
        self, reader: asyncio.StreamReader
    ) -> tuple[str, str, dict[str, str], dict[str, Any]]:
        raw_headers = await reader.readuntil(b"\r\n\r\n")
        if len(raw_headers) > _HEADER_LIMIT:
            raise RivetRunnerBridgeError(
                "RIVET_MCP_REQUEST_TOO_LARGE", "Bridge headers exceed the limit", 413
            )
        try:
            lines = raw_headers.decode("ascii").split("\r\n")
            method, path, version = lines[0].split(" ", 2)
        except (UnicodeError, ValueError) as error:
            raise RivetRunnerBridgeError(
                "RIVET_MCP_BRIDGE_DENIED", "Bridge request line is invalid"
            ) from error
        if version not in {"HTTP/1.0", "HTTP/1.1"} or "?" in path or "#" in path:
            raise RivetRunnerBridgeError(
                "RIVET_MCP_BRIDGE_DENIED", "Bridge request target is invalid"
            )
        headers: dict[str, str] = {}
        for line in lines[1:]:
            if not line:
                continue
            if ":" not in line:
                raise RivetRunnerBridgeError(
                    "RIVET_MCP_BRIDGE_DENIED", "Bridge header is invalid"
                )
            name, value = line.split(":", 1)
            key = name.strip().lower()
            if key in headers:
                raise RivetRunnerBridgeError(
                    "RIVET_MCP_BRIDGE_DENIED", "Duplicate bridge header is denied"
                )
            headers[key] = value.strip()
        if headers.get("transfer-encoding"):
            raise RivetRunnerBridgeError(
                "RIVET_MCP_BRIDGE_DENIED", "Streaming request bodies are denied"
            )
        if (
            headers.get("content-type", "").split(";", 1)[0].lower()
            != "application/json"
        ):
            raise RivetRunnerBridgeError(
                "RIVET_MCP_BRIDGE_DENIED", "Bridge content type is invalid", 415
            )
        try:
            length = int(headers.get("content-length", ""))
        except ValueError as error:
            raise RivetRunnerBridgeError(
                "RIVET_MCP_BRIDGE_DENIED", "Bridge content length is invalid"
            ) from error
        if length < 2 or length > self._settings.maximum_request_bytes:
            raise RivetRunnerBridgeError(
                "RIVET_MCP_REQUEST_TOO_LARGE", "Bridge request exceeds the limit", 413
            )
        raw = await reader.readexactly(length)
        try:
            payload = json.loads(raw)
        except (UnicodeError, json.JSONDecodeError) as error:
            raise RivetRunnerBridgeError(
                "RIVET_MCP_BRIDGE_DENIED", "Bridge body is invalid"
            ) from error
        if not isinstance(payload, dict):
            raise RivetRunnerBridgeError(
                "RIVET_MCP_BRIDGE_DENIED", "Bridge body must be an object"
            )
        return method, path, headers, payload

    def _authority(
        self,
        *,
        token: str,
        authority_id: object,
        run_id: object,
    ):
        if not isinstance(authority_id, str) or not isinstance(run_id, str):
            raise RivetRunnerBridgeError(
                "RIVET_MCP_AUTHORITY_UNAVAILABLE", "Authority identity is invalid", 401
            )
        record = self._authorities.snapshot(authority_id)
        if record is None:
            raise RivetRunnerBridgeError(
                "RIVET_MCP_AUTHORITY_UNAVAILABLE", "Authority is unavailable", 401
            )
        if self._audience is None:
            raise RivetRunnerBridgeError(
                "RIVET_MCP_BRIDGE_DENIED", "Bridge is unavailable", 503
            )
        validated = self._authorities.validate(
            token,
            audience=self._audience,
            run_id=run_id,
            generation=record.claims.generation,
        )
        if validated.authority_id != authority_id:
            raise RivetRunnerBridgeError(
                "RIVET_MCP_AUTHORITY_UNAVAILABLE", "Authority is unavailable", 401
            )
        return validated

    async def _discover(
        self, writer: asyncio.StreamWriter, token: str, payload: dict[str, Any]
    ) -> None:
        if (
            set(payload)
            != {
                "authorityId",
                "runId",
                "discoveryHandle",
                "requestId",
            }
            or payload.get("discoveryHandle") != "wright-workspace"
        ):
            raise RivetRunnerBridgeError(
                "RIVET_MCP_BINDING_MISMATCH", "Discovery handle is unavailable"
            )
        record = self._authority(
            token=token,
            authority_id=payload["authorityId"],
            run_id=payload["runId"],
        )
        binding_set = self._repository.get_binding_set_by_digest(
            record.claims.binding_set_digest
        )
        if (
            binding_set is None
            or binding_set.workspace_id != record.claims.workspace_id
        ):
            raise RivetRunnerBridgeError(
                "RIVET_MCP_BINDING_MISMATCH", "Reviewed bindings are unavailable"
            )
        tools: list[dict[str, Any]] = []
        names: set[str] = set()
        for binding in binding_set.bindings:
            if (
                record.claims.node_bindings.get(binding.node_handle)
                != binding.binding_digest
                or binding.qualified_tool_name in names
            ):
                continue
            names.add(binding.qualified_tool_name)
            tool: dict[str, Any] = {
                "name": binding.qualified_tool_name,
                "description": "Wright-reviewed workspace capability",
                "inputSchema": dict(binding.input_schema),
            }
            if binding.output_schema is not None:
                tool["outputSchema"] = dict(binding.output_schema)
            tools.append(tool)
        await self._begin_ndjson(writer)
        await self._event(
            writer,
            {
                "type": "result",
                "requestId": payload["requestId"],
                "structuredContent": {"tools": tools},
                "isError": False,
            },
        )

    async def _call(
        self, writer: asyncio.StreamWriter, token: str, payload: dict[str, Any]
    ) -> None:
        if set(payload) != {
            "authorityId",
            "runId",
            "nodeHandle",
            "bindingDigest",
            "requestId",
            "arguments",
        } or not isinstance(payload.get("arguments"), dict):
            raise RivetRunnerBridgeError(
                "RIVET_MCP_BINDING_MISMATCH", "Bound call is invalid"
            )
        record = self._authority(
            token=token,
            authority_id=payload["authorityId"],
            run_id=payload["runId"],
        )
        for key in ("nodeHandle", "bindingDigest", "requestId"):
            if not isinstance(payload.get(key), str) or not payload[key]:
                raise RivetRunnerBridgeError(
                    "RIVET_MCP_BINDING_MISMATCH", "Bound call identity is invalid"
                )
        await self._begin_ndjson(writer)
        event_count = 0

        async def progress(update: Mapping[str, Any]) -> None:
            nonlocal event_count
            event_count += 1
            if event_count > self._settings.maximum_events_per_call:
                raise RivetRunnerBridgeError(
                    "RIVET_MCP_RESULT_TOO_LARGE", "MCP event count exceeded the limit"
                )
            await self._event(writer, dict(update))

        try:
            result = await self._bridge.invoke_bound(
                token,
                self._audience or "",
                RivetBoundInvocation(
                    run_id=payload["runId"],
                    generation=record.claims.generation,
                    authority_id=payload["authorityId"],
                    node_handle=payload["nodeHandle"],
                    binding_digest=payload["bindingDigest"],
                    request_id=payload["requestId"],
                    arguments=dict(payload["arguments"]),
                ),
                progress_callback=progress,
            )
        except Exception as error:
            code = str(getattr(error, "code", "RIVET_MCP_CALL_FAILED"))
            if not code.startswith("RIVET_"):
                code = "RIVET_MCP_CALL_FAILED"
            await self._event(
                writer,
                {
                    "type": "result",
                    "isError": True,
                    "error": {
                        "code": code,
                        "message": "The governed MCP call failed.",
                    },
                },
            )
            return
        await self._event(
            writer,
            {
                "type": "result",
                "callId": result.call.call_id if result.call else payload["requestId"],
                "content": list(result.result.content),
                "structuredContent": result.result.structured_content,
                "isError": result.result.is_error,
                "artifacts": [item.canonical() for item in result.artifacts],
            },
        )

    async def _begin_ndjson(self, writer: asyncio.StreamWriter) -> None:
        writer.write(
            b"HTTP/1.1 200 OK\r\n"
            b"Content-Type: application/x-ndjson\r\n"
            b"Cache-Control: no-store\r\n"
            b"X-Content-Type-Options: nosniff\r\n"
            b"Connection: close\r\n\r\n"
        )
        await writer.drain()

    async def _event(
        self, writer: asyncio.StreamWriter, event: Mapping[str, Any]
    ) -> None:
        encoded = json.dumps(event, separators=(",", ":"), default=str).encode()
        if len(encoded) > self._settings.maximum_event_bytes:
            raise RivetRunnerBridgeError(
                "RIVET_MCP_RESULT_TOO_LARGE", "MCP event exceeds the limit"
            )
        writer.write(encoded + b"\n")
        await writer.drain()

    async def _error(self, writer: asyncio.StreamWriter, error: Exception) -> None:
        if writer.is_closing():
            return
        code = str(getattr(error, "code", "RIVET_MCP_CALL_FAILED"))
        if not code.startswith("RIVET_"):
            code = "RIVET_MCP_CALL_FAILED"
        status = int(getattr(error, "status", HTTPStatus.FORBIDDEN))
        event = json.dumps(
            {
                "type": "result",
                "error": {"code": code, "message": "The governed MCP request failed."},
                "isError": True,
            },
            separators=(",", ":"),
        ).encode()
        writer.write(
            f"HTTP/1.1 {status} Error\r\n".encode()
            + b"Content-Type: application/x-ndjson\r\n"
            + b"Cache-Control: no-store\r\n"
            + b"X-Content-Type-Options: nosniff\r\n"
            + b"Connection: close\r\n\r\n"
            + event
            + b"\n"
        )
        try:
            await writer.drain()
        except (BrokenPipeError, ConnectionResetError):
            pass


__all__ = ["RivetRunnerBridgeApplication", "RivetRunnerBridgeError"]
