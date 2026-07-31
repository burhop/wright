"""Data-plane bootstrap and capability-bound application proxy routes."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Annotated, Any
from urllib.parse import urlsplit

from fastapi import (
    APIRouter,
    Depends,
    Header,
    HTTPException,
    Request,
    Response,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, ConfigDict, Field
from starlette.background import BackgroundTask

from api.config import get_workspace_surface_settings
from api.composition import surface_application
from api.surface_http_proxy import HttpProxyError, ProxyHttpRequest, SurfaceHttpProxy
from api.surface_route_authority import (
    AuthorizedSurfaceRoute,
    SurfaceRouteAuthorizationError,
    SurfaceRouteAuthority,
)
from api.surface_sse_proxy import SseProxyError, SseProxyRequest, SurfaceSseProxy
from api.surface_websocket_proxy import (
    SurfaceWebSocketProxy,
    WebSocketMessage,
    WebSocketProxyError,
    WebSocketProxyRequest,
)
from workspace_service.surfaces.presentation_tokens import (
    PresentationTokenError,
    PresentationTokenService,
)
from tool_registry.webmcp_router import (
    WebMcpBinding,
    WebMcpRegistration,
    WebMcpRouter,
    WebMcpRoutingError,
)


router = APIRouter()

_SANDBOX_ASSETS = {
    "index.html": "text/html; charset=utf-8",
    "sandbox-proxy.js": "text/javascript; charset=utf-8",
}
_SANDBOX_CSP = (
    "default-src 'none'; script-src 'self' 'unsafe-inline' https:; "
    "style-src 'unsafe-inline' https:; connect-src https: wss:; "
    "img-src data: blob: https:; font-src https:; media-src blob: https:; "
    "worker-src blob: https:; frame-src 'self' https:; base-uri https:; "
    "form-action 'none'; object-src 'none'; frame-ancestors http: https:"
)

_BOOTSTRAP_SCRIPT = """(() => {
  const token = location.hash.startsWith('#') ? location.hash.slice(1) : '';
  history.replaceState(null, '', location.pathname + location.search);
  if (!token) { document.body.textContent = 'Preview link is incomplete.'; return; }
  fetch('/__wright/bootstrap', {
    method: 'POST', credentials: 'same-origin',
    headers: {'Content-Type': 'application/json'}, body: JSON.stringify({token})
  }).then((response) => {
    if (!response.ok) throw new Error('bootstrap failed');
    location.replace('/');
  }).catch(() => { document.body.textContent = 'Preview link expired. Reopen it from Wright.'; });
})();"""
_SCRIPT_DIGEST = base64.b64encode(
    hashlib.sha256(_BOOTSTRAP_SCRIPT.encode("utf-8")).digest()
).decode("ascii")
_BOOTSTRAP_HTML = (
    "<!doctype html><html><head><meta charset='utf-8'>"
    "<meta name='referrer' content='no-referrer'><title>Opening preview</title>"
    "</head><body>Opening preview…<script>"
    + _BOOTSTRAP_SCRIPT
    + "</script></body></html>"
)


class BootstrapExchange(BaseModel):
    model_config = ConfigDict(extra="forbid")

    token: str = Field(min_length=32, max_length=2048)


def get_presentation_tokens() -> PresentationTokenService:
    return surface_application().presentation_tokens


def _translate(error: PresentationTokenError) -> HTTPException:
    return HTTPException(status_code=error.status_code, detail=error.code)


def _sandbox_dist_dir(request: Request) -> Path:
    configured = getattr(request.app.state, "surface_sandbox_dist_dir", None)
    if configured is not None:
        return Path(configured)
    if "FRONTEND_DIST_DIR" in os.environ:
        return Path(os.environ["FRONTEND_DIST_DIR"])
    try:
        from wright_engineering.runtime.server import packaged_static_path

        return Path(packaged_static_path())
    except Exception:
        return Path("/workspace/apps/web/dist")


@router.api_route(
    "/surface-sandbox/{asset_name}",
    methods=["GET", "HEAD"],
)
def surface_sandbox_asset(
    asset_name: str,
    request: Request,
    host: Annotated[str, Header(alias="Host")],
) -> Response:
    """Serve only Wright's immutable proxy on its reserved isolated origin."""

    expected_domain = getattr(request.app.state, "surface_sandbox_domain", None)
    if expected_domain is None:
        expected_domain = get_workspace_surface_settings().preview.domain
    try:
        hostname = urlsplit(f"//{host}").hostname
    except ValueError:
        hostname = None
    if hostname is None or hostname.lower().rstrip(".") != (
        f"mcp-sandbox.{expected_domain}".lower().rstrip(".")
    ):
        raise HTTPException(status_code=404, detail="SURFACE_PREVIEW_NOT_FOUND")
    media_type = _SANDBOX_ASSETS.get(asset_name)
    if media_type is None:
        raise HTTPException(status_code=404, detail="SURFACE_PREVIEW_NOT_FOUND")
    target = _sandbox_dist_dir(request) / "surface-sandbox" / asset_name
    if not target.is_file():
        raise HTTPException(status_code=503, detail="SURFACE_SANDBOX_UNAVAILABLE")
    return FileResponse(
        target,
        media_type=media_type,
        headers={
            "Cache-Control": "public, max-age=31536000, immutable",
            "Content-Security-Policy": _SANDBOX_CSP,
            "Permissions-Policy": (
                "camera=*, microphone=*, geolocation=*, clipboard-write=*"
            ),
            "Referrer-Policy": "no-referrer",
            "X-Content-Type-Options": "nosniff",
        },
    )


def _reserved_application_path(application_path: str) -> bool:
    first = application_path.lstrip("/").split("/", 1)[0].lower()
    return first in {"__wright", "api", "mcp"}


def _raw_target(scope: dict[str, Any]) -> tuple[str, str]:
    raw_path = scope.get("raw_path") or str(scope.get("path") or "/").encode("ascii")
    raw_query = scope.get("query_string") or b""
    try:
        return bytes(raw_path).decode("ascii"), bytes(raw_query).decode("ascii")
    except UnicodeDecodeError as error:
        raise HTTPException(status_code=400, detail="SURFACE_PROTOCOL_TARGET_INVALID") from error


def _raw_headers(scope: dict[str, Any]) -> tuple[tuple[str, str], ...]:
    return tuple(
        (bytes(name).decode("latin-1"), bytes(value).decode("latin-1"))
        for name, value in scope.get("headers", ())
    )


def _component(connection: Request | WebSocket, name: str) -> Any:
    value = getattr(connection.app.state, name, None)
    if value is None:
        raise SurfaceRouteAuthorizationError(
            "SURFACE_RUNTIME_UNAVAILABLE",
            "Surface runtime routing is unavailable",
            status_code=503,
        )
    return value


def _authorize_application_route(
    connection: Request | WebSocket,
) -> AuthorizedSurfaceRoute:
    host_values = [
        value for name, value in _raw_headers(connection.scope) if name.lower() == "host"
    ]
    cookie = connection.cookies.get("wright_surface", "")
    if len(host_values) != 1 or not cookie:
        raise SurfaceRouteAuthorizationError(
            "SURFACE_PREVIEW_UNAUTHORIZED",
            "Preview credential is invalid",
            status_code=401,
        )
    authority: SurfaceRouteAuthority = _component(
        connection, "surface_route_authority"
    )
    return authority.authorize(host=host_values[0], cookie=cookie)


def _route_error(error: SurfaceRouteAuthorizationError) -> HTTPException:
    return HTTPException(status_code=error.status_code, detail=error.code)


def _streaming_response(
    *, status: int, headers: tuple[tuple[str, str], ...], body: Any, close: Any
) -> StreamingResponse:
    response = StreamingResponse(
        body,
        status_code=status,
        background=BackgroundTask(close),
    )
    response.raw_headers = [
        (name.encode("latin-1"), value.encode("latin-1"))
        for name, value in headers
    ]
    return response


class _StarletteWebSocket:
    def __init__(self, websocket: WebSocket) -> None:
        self._websocket = websocket

    async def accept(self, *, subprotocol: str | None = None) -> None:
        await self._websocket.accept(subprotocol=subprotocol)

    async def receive(self) -> WebSocketMessage:
        message = await self._websocket.receive()
        if message["type"] == "websocket.disconnect":
            return WebSocketMessage.close(int(message.get("code") or 1000))
        if message.get("text") is not None:
            return WebSocketMessage.text(str(message["text"]))
        if message.get("bytes") is not None:
            return WebSocketMessage.binary(bytes(message["bytes"]))
        return WebSocketMessage.close(1002, "invalid WebSocket frame")

    async def send(self, message: WebSocketMessage) -> None:
        if message.kind == "text":
            await self._websocket.send_text(str(message.data))
        elif message.kind == "binary":
            await self._websocket.send_bytes(bytes(message.data or b""))
        else:
            await self.close(code=message.code, reason=message.reason)

    async def close(self, *, code: int, reason: str = "") -> None:
        await self._websocket.close(code=code, reason=reason)


@router.get("/__wright/bootstrap")
def bootstrap_document(
    host: Annotated[str, Header(alias="Host")],
    tokens: Annotated[PresentationTokenService, Depends(get_presentation_tokens)],
) -> Response:
    try:
        tokens.require_bound_host(host)
    except PresentationTokenError as error:
        raise _translate(error) from error
    return Response(
        content=_BOOTSTRAP_HTML,
        media_type="text/html",
        headers={
            "Cache-Control": "no-store",
            "Content-Security-Policy": (
                "default-src 'none'; connect-src 'self'; base-uri 'none'; "
                f"form-action 'none'; script-src 'sha256-{_SCRIPT_DIGEST}'"
            ),
            "Referrer-Policy": "no-referrer",
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.post("/__wright/bootstrap", status_code=204)
def exchange_bootstrap(
    body: BootstrapExchange,
    host: Annotated[str, Header(alias="Host")],
    tokens: Annotated[PresentationTokenService, Depends(get_presentation_tokens)],
) -> Response:
    try:
        session = tokens.exchange(host=host, token=body.token)
    except PresentationTokenError as error:
        raise _translate(error) from error
    remaining = max(1, int((session.expires_at - tokens.clock()).total_seconds()))
    response = Response(status_code=204, headers={"Cache-Control": "no-store"})
    response.set_cookie(
        "wright_surface",
        session.cookie_value,
        httponly=True,
        secure=tokens.preview.scheme == "https",
        samesite="strict",
        path="/",
        max_age=remaining,
    )
    return response


@router.api_route(
    "/{application_path:path}",
    methods=["GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
)
async def proxy_application(application_path: str, request: Request) -> Response:
    if _reserved_application_path(application_path):
        raise HTTPException(status_code=404, detail="SURFACE_PREVIEW_NOT_FOUND")
    try:
        route = _authorize_application_route(request)
        raw_path, raw_query = _raw_target(request.scope)
        headers = _raw_headers(request.scope)
        accepts_sse = request.method == "GET" and any(
            name.lower() == "accept" and "text/event-stream" in value.lower()
            for name, value in headers
        )
        if accepts_sse:
            sse_proxy: SurfaceSseProxy = _component(request, "surface_sse_proxy")
            stream = await sse_proxy.open(
                SseProxyRequest(
                    raw_path=raw_path,
                    raw_query=raw_query,
                    headers=headers,
                    presentation_id=route.presentation_id,
                    sse_declared=route.sse_declared,
                ),
                pin=route.pin,
                limits=route.limits,
                authority_valid=route.authority_valid,
                target_valid=route.target_valid,
                activity=route.activity,
            )
            return _streaming_response(
                status=stream.status,
                headers=stream.headers,
                body=stream.body,
                close=stream.aclose,
            )
        if not route.http_declared:
            raise HTTPException(
                status_code=403, detail="SURFACE_PROTOCOL_TRANSPORT_UNDECLARED"
            )
        http_proxy: SurfaceHttpProxy = _component(request, "surface_http_proxy")
        response = await http_proxy.forward(
            ProxyHttpRequest(
                method=request.method,
                raw_path=raw_path,
                raw_query=raw_query,
                headers=headers,
                body=request.stream(),
                presentation_id=route.presentation_id,
            ),
            pin=route.pin,
            limits=route.limits,
            authority_valid=route.authority_valid,
            target_valid=route.target_valid,
            activity=route.activity,
        )
        return _streaming_response(
            status=response.status,
            headers=response.headers,
            body=response.body,
            close=response.aclose,
        )
    except SurfaceRouteAuthorizationError as error:
        raise _route_error(error) from error
    except (HttpProxyError, SseProxyError) as error:
        raise HTTPException(status_code=error.status_code, detail=error.code) from error


def _webmcp_registration(
    route: AuthorizedSurfaceRoute,
    payload: Any,
    router: WebMcpRouter,
) -> WebMcpRegistration:
    if not isinstance(payload, dict):
        raise WebMcpRoutingError(
            "SURFACE_PROTOCOL_WEBMCP_MESSAGE_INVALID",
            "WebMCP registration must be a surface message",
        )
    router.validate_surface_message(payload)
    body = payload.get("payload")
    tool = body.get("tool") if isinstance(body, dict) else None
    if not isinstance(tool, dict):
        raise WebMcpRoutingError(
            "SURFACE_PROTOCOL_WEBMCP_REGISTRATION_INVALID",
            "WebMCP registration omitted its tool declaration",
        )
    name = tool.get("name")
    description = tool.get("description", "")
    input_schema = tool.get("inputSchema", {"type": "object"})
    if not isinstance(name, str) or not isinstance(description, str):
        raise WebMcpRoutingError(
            "SURFACE_PROTOCOL_WEBMCP_REGISTRATION_INVALID",
            "WebMCP tool identity is invalid",
        )
    if not isinstance(input_schema, dict):
        raise WebMcpRoutingError(
            "SURFACE_PROTOCOL_WEBMCP_SCHEMA_INVALID",
            "WebMCP input schema must be an object",
        )
    registration = WebMcpRegistration(
        binding=WebMcpBinding(
            principal_id=route.principal_id,
            workspace_id=route.workspace_id,
            session_id=route.session_id,
            surface_id=route.surface_id,
            instance_id=route.instance_id,
            generation=route.generation,
            document_origin=route.presentation_origin,
            server_id=route.source_id,
            tool_name=name,
        ),
        description=description,
        input_schema=input_schema,
    )
    if payload.get("binding") != registration.binding.envelope():
        raise WebMcpRoutingError(
            "SURFACE_PROTOCOL_WEBMCP_SCOPE_INVALID",
            "WebMCP message scope does not match the authorized presentation",
        )
    return registration


@router.websocket("/__wright/webmcp")
async def surface_webmcp(websocket: WebSocket) -> None:
    router: WebMcpRouter | None = getattr(
        websocket.app.state, "surface_webmcp_router", None
    )
    if router is None:
        await websocket.close(code=1008, reason="WebMCP is disabled")
        return
    try:
        route = _authorize_application_route(websocket)
        origins = [
            value
            for name, value in _raw_headers(websocket.scope)
            if name.lower() == "origin"
        ]
        if origins != [route.presentation_origin]:
            raise WebMcpRoutingError(
                "SURFACE_PROTOCOL_WEBMCP_ORIGIN_INVALID",
                "WebMCP origin does not match the authorized presentation",
            )
        await websocket.accept()
        connected_at = datetime.now(UTC)
        base_binding = {
            "workspaceId": route.workspace_id,
            "sessionId": route.session_id,
            "surfaceId": route.surface_id,
            "instanceId": route.instance_id,
            "generation": route.generation,
            "documentOrigin": route.presentation_origin,
            "serverId": route.source_id,
        }
        await websocket.send_json(
            {
                "protocolVersion": "1.0",
                "kind": "event",
                "messageId": str(uuid.uuid4()),
                "correlationId": str(uuid.uuid4()),
                "binding": base_binding,
                "operation": "webmcp.connected",
                "sequence": 0,
                "createdAt": connected_at.isoformat(),
                "deadlineAt": (
                    connected_at + timedelta(seconds=30)
                ).isoformat(),
                "payload": {"draft": "2026-07-28"},
            }
        )
        while route.authority_valid() and route.target_valid():
            raw = await websocket.receive_text()
            payload = json.loads(raw)
            operation = payload.get("operation") if isinstance(payload, dict) else None
            if operation == "webmcp.register":
                registration = _webmcp_registration(route, payload, router)
                router.register(websocket, registration)
                await websocket.send_json(
                    {
                        "protocolVersion": "1.0",
                        "kind": "result",
                        "messageId": str(uuid.uuid4()),
                        "correlationId": payload["correlationId"],
                        "replyTo": payload["messageId"],
                        "binding": registration.binding.envelope(),
                        "operation": "webmcp.register.result",
                        "toolName": registration.binding.tool_name,
                        "sequence": 0,
                        "createdAt": datetime.now(UTC).isoformat(),
                        "deadlineAt": payload["deadlineAt"],
                        "payload": {"registered": True},
                    }
                )
            elif operation == "webmcp.unregister":
                registration = _webmcp_registration(route, payload, router)
                router.unregister(
                    websocket, registration.binding, reason="disposed"
                )
                await websocket.send_json(
                    {
                        "protocolVersion": "1.0",
                        "kind": "result",
                        "messageId": str(uuid.uuid4()),
                        "correlationId": payload["correlationId"],
                        "replyTo": payload["messageId"],
                        "binding": registration.binding.envelope(),
                        "operation": "webmcp.unregister.result",
                        "toolName": registration.binding.tool_name,
                        "sequence": 0,
                        "createdAt": datetime.now(UTC).isoformat(),
                        "deadlineAt": payload["deadlineAt"],
                        "payload": {"unregistered": True},
                    }
                )
            else:
                router.handle_message(websocket, raw)
    except (SurfaceRouteAuthorizationError, WebMcpRoutingError, ValueError, json.JSONDecodeError):
        await websocket.close(code=1008, reason="WebMCP route denied")
    except WebSocketDisconnect:
        pass
    finally:
        if router is not None:
            router.disconnect(websocket)


@router.websocket("/{application_path:path}")
async def proxy_application_websocket(
    application_path: str, websocket: WebSocket
) -> None:
    if _reserved_application_path(application_path):
        await websocket.close(code=1008, reason="surface route denied")
        return
    try:
        route = _authorize_application_route(websocket)
        proxy: SurfaceWebSocketProxy = _component(
            websocket, "surface_websocket_proxy"
        )
        raw_path, raw_query = _raw_target(websocket.scope)
        origins = [
            value
            for name, value in _raw_headers(websocket.scope)
            if name.lower() == "origin"
        ]
        await proxy.bridge(
            _StarletteWebSocket(websocket),
            request=WebSocketProxyRequest(
                raw_path=raw_path,
                raw_query=raw_query,
                origin=origins[0] if len(origins) == 1 else None,
                presentation_origin=route.presentation_origin,
                subprotocols=tuple(websocket.scope.get("subprotocols") or ()),
                headers=_raw_headers(websocket.scope),
                presentation_id=route.presentation_id,
                websocket_declared=route.websocket_declared,
            ),
            pin=route.pin,
            limits=route.limits,
            authority_valid=route.authority_valid,
            target_valid=route.target_valid,
            activity=route.activity,
        )
    except SurfaceRouteAuthorizationError:
        await websocket.close(code=1008, reason="surface authorization denied")
    except WebSocketProxyError as error:
        code = 1009 if error.code == "SURFACE_LIMIT_MESSAGE_BYTES" else 1008
        await websocket.close(code=code, reason="surface route denied")
    except HTTPException:
        await websocket.close(code=1008, reason="surface route denied")
