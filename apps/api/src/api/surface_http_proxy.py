"""Streaming capability-bound HTTP proxy for isolated surface previews."""

from __future__ import annotations

import asyncio
import time
import zlib
from collections.abc import AsyncIterable, AsyncIterator, Awaitable, Callable, Sequence
from dataclasses import dataclass
import httpx

from api.surface_proxy_security import (
    ProxySecurityError,
    filter_request_headers,
    filter_response_headers,
    validate_redirect,
)
from workspace_service.surfaces.limits import EffectiveSurfaceLimits, SurfaceLimitError
from workspace_service.surfaces.target_policy import ResolvedTargetPin


class HttpProxyError(RuntimeError):
    def __init__(self, code: str, message: str, *, status_code: int = 502) -> None:
        super().__init__(message)
        self.code = code
        self.status_code = status_code


async def _empty_body() -> AsyncIterator[bytes]:
    if False:
        yield b""


@dataclass(frozen=True, slots=True)
class ProxyHttpRequest:
    method: str
    raw_path: str
    raw_query: str
    headers: tuple[tuple[str, str], ...]
    body: AsyncIterable[bytes]
    presentation_id: str

    @classmethod
    def get(cls, path: str, *, presentation_id: str) -> "ProxyHttpRequest":
        return cls("GET", path, "", (), _empty_body(), presentation_id)


class _BodyStream:
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
            async for item in self._source:
                yield item
        finally:
            await self.aclose()

    async def aclose(self) -> None:
        if not self._closed:
            self._closed = True
            await self._close()


@dataclass(frozen=True, slots=True)
class ProxyHttpResponse:
    status: int
    headers: tuple[tuple[str, str], ...]
    body: _BodyStream

    async def aclose(self) -> None:
        await self.body.aclose()


class _DecodedTracker:
    def __init__(self, content_encoding: str | None) -> None:
        encoding = (content_encoding or "identity").strip().lower()
        self.encoding = encoding
        self.decoded_bytes = 0
        if encoding in {"", "identity"}:
            self._decoder = None
        elif encoding == "gzip":
            self._decoder = zlib.decompressobj(16 + zlib.MAX_WBITS)
        elif encoding == "deflate":
            self._decoder = zlib.decompressobj()
        else:
            raise HttpProxyError(
                "SURFACE_LIMIT_DECOMPRESSION",
                f"Content encoding {encoding!r} cannot be bounded by this proxy",
                status_code=415,
            )

    def feed(self, payload: bytes) -> int:
        decoded = payload if self._decoder is None else self._decoder.decompress(payload)
        self.decoded_bytes += len(decoded)
        return self.decoded_bytes

    def finish(self) -> int:
        if self._decoder is not None:
            self.decoded_bytes += len(self._decoder.flush())
        return self.decoded_bytes


def _header_value(headers: Sequence[tuple[str, str]], name: str) -> str | None:
    lowered = name.lower()
    values = [value for key, value in headers if key.lower() == lowered]
    if not values:
        return None
    if len(values) > 1 and lowered in {"content-length", "content-encoding", "location"}:
        raise HttpProxyError(
            "SURFACE_PROTOCOL_HEADER_INVALID",
            f"Upstream supplied ambiguous {name} headers",
        )
    return values[-1]


def _target_path(pin: ResolvedTargetPin, raw_path: str, raw_query: str) -> str:
    if (
        not raw_path.startswith("/")
        or raw_path.startswith("//")
        or any(value in raw_path for value in ("\0", "\r", "\n", "\\"))
        or any(value in raw_query for value in ("\0", "\r", "\n", "#"))
    ):
        raise HttpProxyError(
            "SURFACE_PROTOCOL_TARGET_INVALID", "Application request target is invalid", status_code=400
        )
    base = pin.base_path or "/"
    if not base.startswith("/"):
        raise HttpProxyError("SURFACE_TARGET_PIN_INVALID", "Pinned base path is invalid")
    path = raw_path if base == "/" else f"{base.rstrip('/')}/{raw_path.lstrip('/')}"
    return f"{path}?{raw_query}" if raw_query else path


class SurfaceHttpProxy:
    informational_response_support = "upstream-adapter-not-exposed"

    def __init__(
        self,
        *,
        client: httpx.AsyncClient | None = None,
        allowed_methods: frozenset[str] = frozenset(
            {"GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"}
        ),
        monotonic: Callable[[], float] | None = None,
    ) -> None:
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(timeout=None, follow_redirects=False)
        self._allowed_methods = allowed_methods
        self._monotonic = monotonic or time.monotonic
        self._semaphores: dict[tuple[str | None, int | None], asyncio.Semaphore] = {}

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    @staticmethod
    def _translate_limit(error: SurfaceLimitError) -> HttpProxyError:
        return HttpProxyError(error.code, str(error), status_code=413)

    def _request_body(
        self,
        request: ProxyHttpRequest,
        *,
        headers: Sequence[tuple[str, str]],
        limits: EffectiveSurfaceLimits,
        authority_valid: Callable[[], bool],
        target_valid: Callable[[], bool],
    ) -> AsyncIterator[bytes]:
        async def iterate() -> AsyncIterator[bytes]:
            encoded = 0
            tracker = _DecodedTracker(_header_value(headers, "content-encoding"))
            async for chunk in request.body:
                self._require_current_route(
                    authority_valid=authority_valid, target_valid=target_valid
                )
                if not isinstance(chunk, bytes):
                    raise HttpProxyError(
                        "SURFACE_PROTOCOL_BODY_INVALID",
                        "Application request body yielded a non-byte chunk",
                        status_code=400,
                    )
                if len(chunk) > int(limits.maximum_buffered_output_bytes):
                    raise HttpProxyError(
                        "SURFACE_LIMIT_BUFFER", "Application request chunk exceeds buffer limit", status_code=413
                    )
                encoded += len(chunk)
                decoded = tracker.feed(chunk)
                try:
                    limits.validate_http(
                        tuple(headers), encoded_bytes=encoded, decoded_bytes=decoded
                    )
                except SurfaceLimitError as error:
                    raise self._translate_limit(error) from error
                yield chunk
            decoded = tracker.finish()
            try:
                limits.validate_http(
                    tuple(headers), encoded_bytes=encoded, decoded_bytes=decoded
                )
            except SurfaceLimitError as error:
                raise self._translate_limit(error) from error

        return iterate()

    async def forward(
        self,
        request: ProxyHttpRequest,
        *,
        pin: ResolvedTargetPin,
        limits: EffectiveSurfaceLimits,
        authority_valid: Callable[[], bool] = lambda: True,
        target_valid: Callable[[], bool] = lambda: True,
        activity: Callable[[], None] = lambda: None,
    ) -> ProxyHttpResponse:
        method = request.method.upper()
        if method == "TRACE" or method not in self._allowed_methods:
            raise HttpProxyError(
                "SURFACE_PROTOCOL_METHOD_DENIED",
                "Application request method is not declared or permitted",
                status_code=405,
            )
        if not request.presentation_id:
            raise HttpProxyError(
                "SURFACE_PRESENTATION_UNAUTHORIZED", "Presentation identity is required", status_code=401
            )
        self._require_current_route(
            authority_valid=authority_valid, target_valid=target_valid
        )
        try:
            limits.admit_request(request.presentation_id)
            limits.validate_http(request.headers, encoded_bytes=0, decoded_bytes=0)
            activity()
        except SurfaceLimitError as error:
            raise self._translate_limit(error) from error
        filtered = filter_request_headers(request.headers, pin=pin)
        content_length = _header_value(filtered, "content-length")
        if content_length is not None:
            try:
                declared_length = int(content_length)
            except ValueError as error:
                raise HttpProxyError(
                    "SURFACE_PROTOCOL_HEADER_INVALID", "Content-Length is invalid", status_code=400
                ) from error
            if declared_length < 0 or declared_length > int(limits.maximum_request_body_bytes):
                raise HttpProxyError(
                    "SURFACE_LIMIT_REQUEST_BODY", "Surface request body limit exceeded", status_code=413
                )

        target = _target_path(pin, request.raw_path, request.raw_query)
        host = f"[{pin.numeric_address}]" if ":" in pin.numeric_address else pin.numeric_address
        url = f"{pin.scheme}://{host}:{pin.port}{target}"
        upstream = self._client.build_request(
            method,
            url,
            headers=filtered,
            content=self._request_body(
                request,
                headers=filtered,
                limits=limits,
                authority_valid=authority_valid,
                target_valid=target_valid,
            ),
        )
        if pin.server_name:
            upstream.extensions["sni_hostname"] = pin.server_name.encode("ascii")
        key = (pin.instance_id, pin.generation)
        semaphore = self._semaphores.setdefault(
            key, asyncio.Semaphore(int(limits.connections_per_app))
        )
        await semaphore.acquire()
        response: httpx.Response | None = None
        try:
            response = await asyncio.wait_for(
                self._client.send(upstream, stream=True, follow_redirects=False),
                timeout=float(limits.first_byte_timeout_seconds),
            )
            raw_headers = tuple(
                (name.decode("latin-1"), value.decode("latin-1"))
                for name, value in response.headers.raw
            )
            header_bytes = sum(
                len(name.encode("latin-1")) + len(value.encode("latin-1")) + 4
                for name, value in raw_headers
            )
            if (
                len(raw_headers) > int(limits.maximum_header_count)
                or header_bytes > int(limits.maximum_header_bytes)
            ):
                raise HttpProxyError(
                    "SURFACE_LIMIT_HEADER_BYTES", "Upstream response headers exceed policy", status_code=502
                )
            safe_headers = filter_response_headers(raw_headers)
            location = _header_value(safe_headers, "location")
            if location is not None and 300 <= response.status_code < 400:
                try:
                    rewritten = validate_redirect(location, pin=pin)
                except ProxySecurityError as error:
                    raise HttpProxyError(
                        "SURFACE_TARGET_REDIRECT_REJECTED",
                        "Upstream redirect leaves the immutable target",
                        status_code=502,
                    ) from error
                safe_headers = [
                    (name, rewritten if name.lower() == "location" else value)
                    for name, value in safe_headers
                ]
            if response.status_code in {204, 304} or method == "HEAD":
                await response.aclose()
                semaphore.release()
                return ProxyHttpResponse(
                    response.status_code,
                    tuple(safe_headers),
                    _BodyStream(_empty_body(), close=_noop_close),
                )

            body = self._response_body(
                response,
                limits=limits,
                rate_key=request.presentation_id,
                started=self._monotonic(),
                authority_valid=authority_valid,
                target_valid=target_valid,
                activity=activity,
            )

            async def close() -> None:
                assert response is not None
                await response.aclose()
                semaphore.release()

            return ProxyHttpResponse(
                response.status_code,
                tuple(safe_headers),
                _BodyStream(body, close=close),
            )
        except BaseException:
            if response is not None:
                await response.aclose()
            semaphore.release()
            raise

    def _response_body(
        self,
        response: httpx.Response,
        *,
        limits: EffectiveSurfaceLimits,
        rate_key: str,
        started: float,
        authority_valid: Callable[[], bool],
        target_valid: Callable[[], bool],
        activity: Callable[[], None],
    ) -> AsyncIterator[bytes]:
        async def iterate() -> AsyncIterator[bytes]:
            tracker = _DecodedTracker(response.headers.get("content-encoding"))
            encoded = 0
            source = response.aiter_raw().__aiter__()
            while True:
                self._require_current_route(
                    authority_valid=authority_valid, target_valid=target_valid
                )
                if self._monotonic() - started > float(
                    limits.live_connection_lifetime_seconds
                ):
                    raise HttpProxyError(
                        "SURFACE_LIMIT_LIFETIME", "HTTP response lifetime limit exceeded"
                    )
                try:
                    chunk = await asyncio.wait_for(
                        source.__anext__(),
                        timeout=float(limits.http_idle_timeout_seconds),
                    )
                except StopAsyncIteration:
                    break
                except TimeoutError as error:
                    raise HttpProxyError(
                        "SURFACE_LIMIT_IDLE", "HTTP response idle timeout exceeded"
                    ) from error
                if len(chunk) > int(limits.maximum_buffered_output_bytes):
                    raise HttpProxyError(
                        "SURFACE_LIMIT_BUFFER", "HTTP response chunk exceeds buffer limit"
                    )
                encoded += len(chunk)
                decoded = tracker.feed(chunk)
                try:
                    limits.validate_response(
                        encoded_bytes=encoded, decoded_bytes=decoded
                    )
                    limits.admit_stream_bytes(rate_key, len(chunk))
                except SurfaceLimitError as error:
                    raise self._translate_limit(error) from error
                activity()
                yield chunk
            decoded = tracker.finish()
            try:
                limits.validate_response(encoded_bytes=encoded, decoded_bytes=decoded)
            except SurfaceLimitError as error:
                raise self._translate_limit(error) from error

        return iterate()

    @staticmethod
    def _require_current_route(
        *, authority_valid: Callable[[], bool], target_valid: Callable[[], bool]
    ) -> None:
        if not authority_valid():
            raise HttpProxyError(
                "SURFACE_PRESENTATION_REVOKED",
                "Presentation authority is no longer active",
                status_code=401,
            )
        if not target_valid():
            raise HttpProxyError(
                "SURFACE_TARGET_OWNERSHIP_MISMATCH",
                "Target pin is no longer valid",
            )


async def _noop_close() -> None:
    return None


__all__ = [
    "HttpProxyError",
    "ProxyHttpRequest",
    "ProxyHttpResponse",
    "SurfaceHttpProxy",
]
