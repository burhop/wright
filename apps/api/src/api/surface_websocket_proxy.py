"""Capability-bound WebSocket proxy with exact origin and close semantics."""

from __future__ import annotations

import asyncio
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal, Protocol

from websockets.asyncio.client import connect
from websockets.exceptions import ConnectionClosed

from api.surface_proxy_security import filter_request_headers
from workspace_service.surfaces.limits import EffectiveSurfaceLimits, SurfaceLimitError
from workspace_service.surfaces.target_policy import ResolvedTargetPin


class WebSocketProxyError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True, slots=True)
class WebSocketMessage:
    kind: Literal["text", "binary", "close"]
    data: str | bytes | None = None
    code: int = 1000
    reason: str = ""

    @classmethod
    def text(cls, value: str) -> "WebSocketMessage":
        return cls("text", value)

    @classmethod
    def binary(cls, value: bytes) -> "WebSocketMessage":
        return cls("binary", value)

    @classmethod
    def close(cls, code: int = 1000, reason: str = "") -> "WebSocketMessage":
        return cls("close", code=code, reason=reason)


class DownstreamWebSocket(Protocol):
    async def accept(self, *, subprotocol: str | None = None) -> None: ...

    async def receive(self) -> WebSocketMessage: ...

    async def send(self, message: WebSocketMessage) -> None: ...

    async def close(self, *, code: int, reason: str = "") -> None: ...


@dataclass(frozen=True, slots=True)
class WebSocketProxyRequest:
    raw_path: str
    raw_query: str
    origin: str | None
    presentation_origin: str
    subprotocols: tuple[str, ...]
    headers: tuple[tuple[str, str], ...]
    presentation_id: str
    websocket_declared: bool


@dataclass(frozen=True, slots=True)
class WebSocketBridgeResult:
    outcome: str
    close_code: int
    close_reason: str
    messages_upstream: int
    messages_downstream: int


class _MessageBucket:
    def __init__(
        self,
        *,
        rate: int,
        burst: int,
        monotonic: Callable[[], float],
    ) -> None:
        self.rate = rate
        self.burst = burst
        self.monotonic = monotonic
        self.tokens = float(burst)
        self.updated = monotonic()

    def admit(self) -> None:
        current = self.monotonic()
        self.tokens = min(
            float(self.burst),
            self.tokens + max(0.0, current - self.updated) * self.rate,
        )
        self.updated = current
        if self.tokens < 1:
            raise WebSocketProxyError(
                "SURFACE_LIMIT_WEBSOCKET_RATE", "WebSocket message rate limit exceeded"
            )
        self.tokens -= 1


def _target_path(pin: ResolvedTargetPin, raw_path: str, raw_query: str) -> str:
    if (
        not raw_path.startswith("/")
        or raw_path.startswith("//")
        or any(value in raw_path for value in ("\0", "\r", "\n", "\\"))
        or any(value in raw_query for value in ("\0", "\r", "\n", "#"))
    ):
        raise WebSocketProxyError(
            "SURFACE_PROTOCOL_TARGET_INVALID", "WebSocket request target is invalid"
        )
    base = pin.base_path or "/"
    path = raw_path if base == "/" else f"{base.rstrip('/')}/{raw_path.lstrip('/')}"
    return f"{path}?{raw_query}" if raw_query else path


def _message_bytes(message: WebSocketMessage) -> bytes:
    if message.kind == "text" and isinstance(message.data, str):
        return message.data.encode("utf-8")
    if message.kind == "binary" and isinstance(message.data, bytes):
        return message.data
    raise WebSocketProxyError(
        "SURFACE_PROTOCOL_WEBSOCKET_MESSAGE_INVALID",
        "WebSocket message shape is invalid",
    )


class SurfaceWebSocketProxy:
    def __init__(
        self,
        *,
        connector: Callable[..., Any] = connect,
        revalidation_seconds: float = 0.25,
        monotonic: Callable[[], float] | None = None,
    ) -> None:
        if revalidation_seconds <= 0:
            raise ValueError("WebSocket revalidation interval must be positive")
        self._connector = connector
        self._revalidation_seconds = revalidation_seconds
        self._monotonic = monotonic or time.monotonic

    @staticmethod
    def _validate_request(request: WebSocketProxyRequest) -> None:
        if not request.websocket_declared:
            raise WebSocketProxyError(
                "SURFACE_PROTOCOL_TRANSPORT_UNDECLARED",
                "Manifest does not declare WebSocket transport",
            )
        if not request.origin or request.origin != request.presentation_origin:
            raise WebSocketProxyError(
                "SURFACE_PROTOCOL_ORIGIN_MISMATCH",
                "WebSocket Origin does not match the presentation origin",
            )
        if (
            not request.presentation_id
            or len(request.subprotocols) > 32
            or len(request.subprotocols) != len(set(request.subprotocols))
            or any(not value or len(value) > 256 for value in request.subprotocols)
        ):
            raise WebSocketProxyError(
                "SURFACE_PROTOCOL_WEBSOCKET_REQUEST_INVALID",
                "WebSocket presentation or subprotocol declaration is invalid",
            )

    async def bridge(
        self,
        downstream: DownstreamWebSocket,
        *,
        request: WebSocketProxyRequest,
        pin: ResolvedTargetPin,
        limits: EffectiveSurfaceLimits,
        authority_valid: Callable[[], bool],
        target_valid: Callable[[], bool],
        activity: Callable[[], None] = lambda: None,
    ) -> WebSocketBridgeResult:
        self._validate_request(request)
        if not authority_valid():
            raise WebSocketProxyError(
                "SURFACE_PRESENTATION_REVOKED",
                "Presentation authority is no longer active",
            )
        if not target_valid():
            raise WebSocketProxyError(
                "SURFACE_TARGET_OWNERSHIP_MISMATCH", "Target pin is no longer valid"
            )
        target = _target_path(pin, request.raw_path, request.raw_query)
        scheme = "wss" if pin.scheme == "https" else "ws"
        uri_host = (
            f"[{pin.source_hostname}]"
            if ":" in pin.source_hostname
            else pin.source_hostname
        )
        uri = f"{scheme}://{uri_host}:{pin.port}{target}"
        safe_headers = [
            (name, value)
            for name, value in filter_request_headers(request.headers, pin=pin)
            if name.lower()
            not in {
                "host",
                "origin",
                "sec-websocket-key",
                "sec-websocket-version",
                "sec-websocket-protocol",
                "sec-websocket-extensions",
            }
        ]
        connect_options: dict[str, Any] = {
            "origin": request.origin,
            "subprotocols": list(request.subprotocols) or None,
            "additional_headers": safe_headers,
            "open_timeout": float(limits.first_byte_timeout_seconds),
            "ping_interval": None,
            "close_timeout": min(5, float(limits.http_idle_timeout_seconds)),
            "max_size": int(limits.websocket_message_bytes),
            "max_queue": 1,
            "write_limit": int(limits.maximum_buffered_output_bytes),
            "host": pin.numeric_address,
            "port": pin.port,
        }
        if pin.server_name:
            connect_options["server_hostname"] = pin.server_name

        try:
            connection = self._connector(uri, **connect_options)
            async with connection as upstream:
                selected = upstream.subprotocol
                if selected is not None and selected not in request.subprotocols:
                    raise WebSocketProxyError(
                        "SURFACE_PROTOCOL_SUBPROTOCOL_MISMATCH",
                        "Upstream selected an undeclared WebSocket subprotocol",
                    )
                await downstream.accept(subprotocol=selected)
                return await self._run_pumps(
                    downstream,
                    upstream,
                    request=request,
                    limits=limits,
                    authority_valid=authority_valid,
                    target_valid=target_valid,
                    activity=activity,
                )
        except WebSocketProxyError:
            raise
        except Exception as error:
            raise WebSocketProxyError(
                "SURFACE_TARGET_TRANSPORT_UNAVAILABLE",
                "Pinned WebSocket target could not be reached",
            ) from error

    async def _run_pumps(
        self,
        downstream: DownstreamWebSocket,
        upstream: Any,
        *,
        request: WebSocketProxyRequest,
        limits: EffectiveSurfaceLimits,
        authority_valid: Callable[[], bool],
        target_valid: Callable[[], bool],
        activity: Callable[[], None],
    ) -> WebSocketBridgeResult:
        started = self._monotonic()
        up_count = 0
        down_count = 0
        up_bucket = _MessageBucket(
            rate=int(limits.websocket_messages_per_second),
            burst=int(limits.websocket_message_burst),
            monotonic=self._monotonic,
        )
        down_bucket = _MessageBucket(
            rate=int(limits.websocket_messages_per_second),
            burst=int(limits.websocket_message_burst),
            monotonic=self._monotonic,
        )

        async def browser_to_target() -> WebSocketBridgeResult:
            nonlocal up_count
            while True:
                message = await downstream.receive()
                if message.kind == "close":
                    await upstream.close(code=message.code, reason=message.reason)
                    await upstream.wait_closed()
                    return WebSocketBridgeResult(
                        "client-close",
                        message.code,
                        message.reason,
                        up_count,
                        down_count,
                    )
                payload = _message_bytes(message)
                try:
                    limits.validate_frame(payload)
                    up_bucket.admit()
                except SurfaceLimitError as error:
                    raise WebSocketProxyError(error.code, str(error)) from error
                await upstream.send(message.data)
                activity()
                up_count += 1

        async def target_to_browser() -> WebSocketBridgeResult:
            nonlocal down_count
            try:
                async for payload in upstream:
                    message = (
                        WebSocketMessage.text(payload)
                        if isinstance(payload, str)
                        else WebSocketMessage.binary(payload)
                    )
                    encoded = _message_bytes(message)
                    try:
                        limits.validate_frame(encoded)
                        down_bucket.admit()
                    except SurfaceLimitError as error:
                        raise WebSocketProxyError(error.code, str(error)) from error
                    await downstream.send(message)
                    activity()
                    down_count += 1
            except ConnectionClosed:
                code = upstream.close_code or 1006
                reason = upstream.close_reason or ""
                await downstream.close(code=code, reason=reason)
                return WebSocketBridgeResult(
                    "upstream-close",
                    code,
                    reason,
                    up_count,
                    down_count,
                )
            await downstream.close(
                code=upstream.close_code, reason=upstream.close_reason
            )
            return WebSocketBridgeResult(
                "upstream-close",
                upstream.close_code,
                upstream.close_reason,
                up_count,
                down_count,
            )

        async def monitor() -> WebSocketBridgeResult:
            while True:
                await asyncio.sleep(self._revalidation_seconds)
                if self._monotonic() - started > float(
                    limits.live_connection_lifetime_seconds
                ):
                    await upstream.close(
                        code=1008, reason="connection lifetime expired"
                    )
                    await downstream.close(
                        code=1008, reason="connection lifetime expired"
                    )
                    return WebSocketBridgeResult(
                        "lifetime",
                        1008,
                        "connection lifetime expired",
                        up_count,
                        down_count,
                    )
                if not authority_valid() or not target_valid():
                    await upstream.close(code=1008, reason="presentation revoked")
                    await downstream.close(code=1008, reason="presentation revoked")
                    return WebSocketBridgeResult(
                        "revoked", 1008, "presentation revoked", up_count, down_count
                    )

        tasks = {
            asyncio.create_task(browser_to_target(), name="surface-ws-upstream"),
            asyncio.create_task(target_to_browser(), name="surface-ws-downstream"),
            asyncio.create_task(monitor(), name="surface-ws-authority"),
        }
        try:
            done, pending = await asyncio.wait(
                tasks, return_when=asyncio.FIRST_COMPLETED
            )
            results: list[WebSocketBridgeResult] = []
            proxy_error: WebSocketProxyError | None = None
            for task in done:
                try:
                    results.append(task.result())
                except WebSocketProxyError as error:
                    proxy_error = error
            if proxy_error is not None:
                error = proxy_error
                code = 1009 if error.code == "SURFACE_LIMIT_MESSAGE_BYTES" else 1008
                await upstream.close(code=code, reason="surface policy limit")
                await downstream.close(code=code, reason="surface policy limit")
                result = WebSocketBridgeResult(
                    "limit", code, "surface policy limit", up_count, down_count
                )
            else:
                priority = {
                    "revoked": 0,
                    "lifetime": 1,
                    "upstream-close": 2,
                    "client-close": 3,
                }
                result = min(results, key=lambda item: priority.get(item.outcome, 10))
            for task in pending:
                task.cancel()
            await asyncio.gather(*pending, return_exceptions=True)
            return result
        finally:
            for task in tasks:
                if not task.done():
                    task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)


__all__ = [
    "DownstreamWebSocket",
    "SurfaceWebSocketProxy",
    "WebSocketBridgeResult",
    "WebSocketMessage",
    "WebSocketProxyError",
    "WebSocketProxyRequest",
]
