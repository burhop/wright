"""Opt-in desktop composition using the normal authenticated API lifecycle."""

import json
import os
import re
from pathlib import Path

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


def enabled():
    value = os.environ.get("WRIGHT_DESKTOP_ENABLED", "0")
    if value not in {"0", "1"}:
        raise ValueError("WRIGHT_DESKTOP_ENABLED must be 0 or 1")
    return value == "1"


def configure(app, service):
    """Select an isolated desktop instance after normal database initialization."""
    from .desktop_backend import DesktopBackend

    if not enabled():
        return
    security = app.state.security_settings
    if not security.enforced or security.bind_host != "127.0.0.1":
        raise ValueError("Desktop integration requires authenticated loopback hosting")
    state = Path(os.environ["WRIGHT_DATA_ROOT"]).resolve(strict=True)
    desktop = DesktopBackend(
        service,
        state,
        0,
        native_editor=True,
        native_working_view=True,
        native_workspace_files=True,
        engineering_image_inputs=True,
        workspace_mcp_tasks=True,
        write_legacy_descriptor=False,
        remote_signin_mode=os.environ.get(
            "WRIGHT_MCP_OAUTH_FLOW", "authorization_code"
        ),
    )
    app.state.desktop_backend = desktop
    app.state.agent_engine = desktop
    app.state.mcp_authorization_presenter = desktop.oauth.present
    if desktop.runtime["remote_oauth_flow"] == "device_code":
        app.state.mcp_device_authorization_presenter = desktop.oauth.present_device
    # Register before the frontend catch-all without relying on private wrappers.
    count = len(app.router.routes)
    app.include_router(desktop.router())
    app.router.routes[:] = app.router.routes[count:] + app.router.routes[:count]


class DesktopBoundaryMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        desktop = getattr(request.app.state, "desktop_backend", None)
        if desktop is None:
            return await call_next(request)
        path = request.url.path
        if (
            request.method == "GET"
            and not path.startswith("/api/")
            and "text/html" in request.headers.get("accept", "")
            and not request.headers.get("authorization")
        ):
            from fastapi.responses import HTMLResponse

            return HTMLResponse(
                "<!doctype html><title>Open Wright in your desktop conversation</title>"
                "<h1>Open Wright in your desktop conversation</h1>"
                "<p>This Wright runtime uses the native Wright panel. Ask the "
                "conversation to open Wright and select your workspace. "
                "This address is not an authenticated browser handoff.</p>",
                status_code=403,
                headers={"Cache-Control": "no-store"},
            )
        agent_call = path.startswith("/api/agent") and path != "/api/agent/health"
        source_edit = path == "/api/workspace/workflow-sources" and request.method in {
            "POST",
            "PUT",
        }
        template_copy = (
            request.method == "POST"
            and re.fullmatch(
                r"/api/workspace/workflow-source-templates/[A-Za-z0-9_-]+/instances",
                path,
            )
            is not None
        )
        browser_auth = path == "/api/auth/session"
        # File input storage is a scoped owner operation, not execution. Its
        # multipart body is validated by the existing authenticated upload route.
        input_upload = (
            request.method == "POST"
            and path == "/api/workspace/process-interfaces/inputs/upload"
        )
        workflow_transfer = request.method == "POST" and path in {
            "/api/workspace/workflow-bundles/export",
            "/api/workspace/workflow-bundles/inspect",
            "/api/workspace/workflow-bundles/import",
        }
        process_operation = (
            path
            in {
                "/api/workspace/process-interfaces/inputs",
                "/api/workspace/process-interfaces/readiness",
                "/api/workspace/process-interfaces/runs",
                "/api/workspace/process-interfaces/representations/read",
                "/api/workspace/process-interfaces/navigation",
                "/api/workspace/workflow-sources/run",
            }
            or re.fullmatch(
                r"/api/workspace/process-interfaces/(?:runs/[A-Za-z0-9._:-]+/cancel|interactions/[A-Za-z0-9._:-]+/(?:response|decision)|actions/continue-[A-Za-z0-9._:-]+)",
                path,
            )
            is not None
        )
        desktop_operation = desktop is not None and (
            path.startswith("/api/desktop/")
            or process_operation
            or input_upload
            or workflow_transfer
        )
        if agent_call or (
            request.method not in {"GET", "HEAD", "OPTIONS"}
            and not source_edit
            and not (desktop is not None and template_copy)
            and not browser_auth
            and not desktop_operation
        ):
            return JSONResponse(
                status_code=503,
                content={
                    "detail": {
                        "code": "DESKTOP_BRIDGE_NOT_CONNECTED",
                        "message": "Use the desktop conversation for reasoning; this action is unavailable through the desktop runtime.",
                    }
                },
            )
        if desktop is not None and process_operation and request.method == "POST":
            # Keep dependent gateway/application capabilities gated until their
            # dedicated qualification. Normal service validation still follows.
            from fastapi import HTTPException

            try:
                await desktop.qualify_digital_source(
                    await request.json(), operation=path
                )
            except HTTPException as error:
                return JSONResponse(
                    status_code=error.status_code, content={"detail": error.detail}
                )
            except json.JSONDecodeError:
                return JSONResponse(
                    status_code=400,
                    content={"detail": "Process requests require valid JSON"},
                )
        return await call_next(request)
