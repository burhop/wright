"""
FastAPI middleware for automatic OpenTelemetry span creation per HTTP request.

Creates a root span named by the route's semantic domain (e.g., workspace.files.list).
Extracts X-Trace-Id header from frontend for cross-service correlation.
Injects trace_id into request.state for downstream handler access.
"""

import secrets
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from opentelemetry import trace
from opentelemetry.trace import StatusCode

_tracer = trace.get_tracer("wright.api")

# Map route paths to semantic span names per spec.md span hierarchy
_ROUTE_SPAN_MAP: dict[str, str] = {
    # Workspace operations
    "/api/workspace/create": "workspace.create",
    "/api/workspace/activate": "workspace.activate",
    "/api/workspace/recent": "workspace.list",
    "/api/workspace/list": "workspace.list",
    "/api/workspace/default-dir": "workspace.get",
    # Workspace files
    "files": "workspace.files.list",
    "files/content": "workspace.files.read",
    "files/move": "workspace.files.move",
    # Workspace git
    "git/status": "workspace.git.status",
    "git/diff": "workspace.git.diff",
    "git/commit": "workspace.git.commit",
    "git/revert": "workspace.git.revert",
    "git/push": "workspace.git.push",
    "git/pull": "workspace.git.pull",
    "git/history": "workspace.git.status",
    # Workspace config
    "config": "workspace.config.get",
    "tools": "workspace.tools.list",
    "tools/toggle": "workspace.tools.toggle",
    "context/save": "workspace.context.save",
    "context/load": "workspace.context.load",
    # Agent operations
    "/api/agent/sessions/new": "agent.session.create",
    "/api/agent/sessions": "agent.session.list",
    "/api/agent/chat/start": "agent.chat.start",
    "/api/agent/chat/stream": "agent.chat.stream",
    "/api/agent/active": "agent.active",
    # MCP operations
    "/api/mcp/servers": "mcp.server.list",
    "/api/mcp/tools": "mcp.tool.list",
    # Health
    "/api/health": "health.check",
}


def _resolve_span_name(path: str, method: str) -> str:
    """Resolve a semantic span name from the request path."""
    # Direct match first
    if path in _ROUTE_SPAN_MAP:
        return _ROUTE_SPAN_MAP[path]

    # Check suffixes for workspace sub-routes
    for suffix, name in _ROUTE_SPAN_MAP.items():
        if path.endswith(suffix):
            return name

    # Handle parameterized routes
    if "/sessions/" in path and method == "DELETE":
        return "agent.session.delete"
    if "/by-id/" in path:
        return "workspace.get"
    if "/servers/" in path:
        if method == "PATCH":
            return "mcp.server.toggle"
        if method == "DELETE":
            return "mcp.server.delete"
        if "install" in path:
            return "mcp.server.install"
        if "uninstall" in path:
            return "mcp.server.uninstall"
    if "/tools/" in path and method == "PATCH":
        return "mcp.tool.toggle"

    # Fallback: method + path
    return f"{method.lower()} {path}"


class TracingMiddleware(BaseHTTPMiddleware):
    """Creates an OTel root span for every HTTP request with semantic naming."""

    async def dispatch(self, request: Request, call_next):
        # Extract or generate trace_id
        frontend_trace_id = request.headers.get("x-trace-id")
        if frontend_trace_id:
            trace_id = frontend_trace_id
        else:
            span = trace.get_current_span()
            if span and span.get_span_context().is_valid:
                trace_id = f"{span.get_span_context().trace_id:032x}"
            else:
                trace_id = secrets.token_hex(16)

        # Store trace_id in request state for downstream handlers
        request.state.trace_id = trace_id

        span_name = _resolve_span_name(request.url.path, request.method)
        start_time = time.monotonic()

        with _tracer.start_as_current_span(span_name) as span:
            span.set_attribute("http.method", request.method)
            span.set_attribute("http.url", str(request.url))
            span.set_attribute("http.route", request.url.path)
            span.set_attribute("trace_id", trace_id)

            try:
                response = await call_next(request)
                duration_ms = (time.monotonic() - start_time) * 1000

                span.set_attribute("http.status_code", response.status_code)
                span.set_attribute("http.duration_ms", round(duration_ms, 2))

                if response.status_code >= 400:
                    span.set_status(StatusCode.ERROR, f"HTTP {response.status_code}")
                else:
                    span.set_status(StatusCode.OK)

                # Inject trace_id into response headers
                response.headers["X-Trace-Id"] = trace_id
                return response

            except Exception as exc:
                duration_ms = (time.monotonic() - start_time) * 1000
                span.set_attribute("http.duration_ms", round(duration_ms, 2))
                span.set_status(StatusCode.ERROR, str(exc))
                span.record_exception(exc)
                raise
