"""Unbuffered Server-Sent Events proxy for pinned surface targets."""

from __future__ import annotations

import asyncio
import time
from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass

import httpx

from api.surface_proxy_security import filter_request_headers, filter_response_headers
from workspace_service.surfaces.limits import EffectiveSurfaceLimits, SurfaceLimitError
from workspace_service.surfaces.target_policy import ResolvedTargetPin


class SseProxyError(RuntimeError):
    def __init__(self, code: str, message: str, *, status_code: int = 502) -> None:
        super().__init__(message)
        self.code = code
        self.status_code = status_code


@dataclass(frozen=True, slots=True)
class SseProxyRequest:
    raw_path: str
    raw_query: str
    headers: tuple[tuple[str, str], ...]
    presentation_id: str
    sse_declared: bool


async def _empty() -> AsyncIterator[bytes]:
    if False:
        yield b""


class _SseBody:
    def __init__(
        self,
        source: AsyncIterator[bytes],
        *,
        close: Callable[[], Awaitable[None]],
    ) -> None:
        self._source = source
        self._close = close
        self._closed = False

    def __aiter__(self) -> AsyncIterator[bytes]:
        return self._iterate()

    async def _iterate(self) -> AsyncIterator[bytes]:
        try:
            async for payload in self._source:
                yield payload
        finally:
            await self.aclose()

    async def aclose(self) -> None:
        if not self._closed:
            self._closed = True
            await self._close()


@dataclass(frozen=True, slots=True)
class SseProxyStream:
    status: int
    headers: tuple[tuple[str, str], ...]
    body: _SseBody

    async def aclose(self) -> None:
        await self.body.aclose()


def _target_path(pin: ResolvedTargetPin, raw_path: str, raw_query: str) -> str:
    if (
        not raw_path.startswith("/")
        or raw_path.startswith("//")
        or any(value in raw_path for value in ("\0", "\r", "\n", "\\"))
        or any(value in raw_query for value in ("\0", "\r", "\n", "#"))
    ):
        raise SseProxyError(
            "SURFACE_PROTOCOL_TARGET_INVALID",
            "SSE request target is invalid",
            status_code=400,
        )
    base = pin.base_path or "/"
    path = raw_path if base == "/" else f"{base.rstrip('/')}/{raw_path.lstrip('/')}"
    return f"{path}?{raw_query}" if raw_query else path


class SurfaceSseProxy:
    def __init__(
        self,
        *,
        client: httpx.AsyncClient | None = None,
        revalidation_seconds: float = 0.25,
        monotonic: Callable[[], float] | None = None,
    ) -> None:
        if revalidation_seconds <= 0:
            raise ValueError("SSE revalidation interval must be positive")
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(timeout=None, follow_redirects=False)
        self._revalidation_seconds = revalidation_seconds
        self._monotonic = monotonic or time.monotonic
        self._semaphores: dict[tuple[str | None, int | None], asyncio.Semaphore] = {}

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def open(
        self,
        request: SseProxyRequest,
        *,
        pin: ResolvedTargetPin,
        limits: EffectiveSurfaceLimits,
        authority_valid: Callable[[], bool],
        target_valid: Callable[[], bool],
        activity: Callable[[], None] = lambda: None,
    ) -> SseProxyStream:
        if not request.sse_declared:
            raise SseProxyError(
                "SURFACE_PROTOCOL_TRANSPORT_UNDECLARED",
                "Manifest does not declare SSE transport",
                status_code=403,
            )
        if not request.presentation_id or not authority_valid():
            raise SseProxyError(
                "SURFACE_PRESENTATION_REVOKED",
                "Presentation authority is no longer active",
                status_code=401,
            )
        if not target_valid():
            raise SseProxyError(
                "SURFACE_TARGET_OWNERSHIP_MISMATCH", "Target pin is no longer valid"
            )
        try:
            limits.admit_request(request.presentation_id)
            limits.validate_http(request.headers, encoded_bytes=0, decoded_bytes=0)
        except SurfaceLimitError as error:
            raise SseProxyError(error.code, str(error), status_code=413) from error
        headers = list(filter_request_headers(request.headers, pin=pin))
        if not any(name.lower() == "accept" for name, _value in headers):
            headers.append(("Accept", "text/event-stream"))
        target = _target_path(pin, request.raw_path, request.raw_query)
        host = (
            f"[{pin.numeric_address}]"
            if ":" in pin.numeric_address
            else pin.numeric_address
        )
        url = f"{pin.scheme}://{host}:{pin.port}{target}"
        upstream = self._client.build_request("GET", url, headers=headers)
        if pin.server_name:
            upstream.extensions["sni_hostname"] = pin.server_name.encode("ascii")
        key = (pin.instance_id, pin.generation)
        semaphore = self._semaphores.setdefault(
            key, asyncio.Semaphore(int(limits.connections_per_app))
        )
        await semaphore.acquire()
        response: httpx.Response | None = None
        read_task: asyncio.Task[bytes] | None = None
        try:
            response = await asyncio.wait_for(
                self._client.send(upstream, stream=True, follow_redirects=False),
                timeout=float(limits.first_byte_timeout_seconds),
            )
            raw_headers = tuple(
                (name.decode("latin-1"), value.decode("latin-1"))
                for name, value in response.headers.raw
            )
            safe_headers = tuple(filter_response_headers(raw_headers))
            if response.status_code == 204:
                await response.aclose()
                semaphore.release()
                return SseProxyStream(
                    204, safe_headers, _SseBody(_empty(), close=_noop)
                )
            if response.status_code != 200:
                raise SseProxyError(
                    "SURFACE_SSE_STATUS_INVALID",
                    f"SSE target returned HTTP {response.status_code}",
                )
            content_type = response.headers.get("content-type", "").lower()
            if not content_type.startswith("text/event-stream"):
                raise SseProxyError(
                    "SURFACE_SSE_CONTENT_TYPE_INVALID",
                    "SSE target did not return text/event-stream",
                )
            source = response.aiter_raw().__aiter__()
            read_task = asyncio.create_task(
                source.__anext__(), name="surface-sse-first-byte"
            )
            try:
                first = await asyncio.wait_for(
                    asyncio.shield(read_task),
                    timeout=float(limits.first_byte_timeout_seconds),
                )
            except TimeoutError as error:
                read_task.cancel()
                await asyncio.gather(read_task, return_exceptions=True)
                raise SseProxyError(
                    "SURFACE_LIMIT_FIRST_BYTE", "SSE first-byte timeout exceeded"
                ) from error
            except StopAsyncIteration:
                first = None
            read_task = None
            body = self._body(
                source,
                first=first,
                limits=limits,
                rate_key=request.presentation_id,
                authority_valid=authority_valid,
                target_valid=target_valid,
                activity=activity,
            )

            async def close() -> None:
                assert response is not None
                await response.aclose()
                semaphore.release()

            return SseProxyStream(
                response.status_code, safe_headers, _SseBody(body, close=close)
            )
        except BaseException:
            if read_task is not None:
                read_task.cancel()
                await asyncio.gather(read_task, return_exceptions=True)
            if response is not None:
                await response.aclose()
            semaphore.release()
            raise

    def _body(
        self,
        source: AsyncIterator[bytes],
        *,
        first: bytes | None,
        limits: EffectiveSurfaceLimits,
        rate_key: str,
        authority_valid: Callable[[], bool],
        target_valid: Callable[[], bool],
        activity: Callable[[], None],
    ) -> AsyncIterator[bytes]:
        async def iterate() -> AsyncIterator[bytes]:
            started = self._monotonic()
            last_byte = started
            encoded = 0
            pending: asyncio.Task[bytes] | None = None

            async def validate(payload: bytes) -> bytes:
                nonlocal encoded, last_byte
                if len(payload) > int(limits.maximum_buffered_output_bytes):
                    raise SseProxyError(
                        "SURFACE_LIMIT_BUFFER", "SSE chunk exceeds buffer limit"
                    )
                encoded += len(payload)
                try:
                    limits.validate_response(
                        encoded_bytes=encoded, decoded_bytes=encoded
                    )
                    limits.admit_stream_bytes(rate_key, len(payload))
                except SurfaceLimitError as error:
                    raise SseProxyError(
                        error.code, str(error), status_code=413
                    ) from error
                last_byte = self._monotonic()
                activity()
                return payload

            try:
                if first is not None:
                    yield await validate(first)
                while True:
                    if not authority_valid():
                        raise SseProxyError(
                            "SURFACE_PRESENTATION_REVOKED",
                            "Presentation authority was revoked during SSE",
                            status_code=401,
                        )
                    if not target_valid():
                        raise SseProxyError(
                            "SURFACE_TARGET_OWNERSHIP_MISMATCH",
                            "Target ownership changed during SSE",
                        )
                    now = self._monotonic()
                    if now - started > float(limits.live_connection_lifetime_seconds):
                        raise SseProxyError(
                            "SURFACE_LIMIT_LIFETIME", "SSE connection lifetime exceeded"
                        )
                    if now - last_byte > float(limits.stream_heartbeat_idle_seconds):
                        raise SseProxyError(
                            "SURFACE_LIMIT_IDLE", "SSE heartbeat idle timeout exceeded"
                        )
                    if pending is None:
                        pending = asyncio.create_task(
                            source.__anext__(), name="surface-sse-next-byte"
                        )
                    done, _ = await asyncio.wait(
                        {pending}, timeout=self._revalidation_seconds
                    )
                    if not done:
                        continue
                    try:
                        payload = pending.result()
                    except StopAsyncIteration:
                        break
                    finally:
                        pending = None
                    yield await validate(payload)
            finally:
                if pending is not None:
                    pending.cancel()
                    await asyncio.gather(pending, return_exceptions=True)

        return iterate()


async def _noop() -> None:
    return None


__all__ = ["SseProxyError", "SseProxyRequest", "SseProxyStream", "SurfaceSseProxy"]
