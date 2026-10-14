"""Authenticated, loopback-only editor preview over isolated probe state.

This phase permits source editing and reading existing results. All agent calls,
run starts and other mutations are explicitly unavailable until MCP integration.
"""

import argparse
import json
import os
from pathlib import Path
import secrets
import re


class DetachedDesktopConnection:
    async def check_health(self):
        return {
            "state": "disconnected",
            "latencyMs": 0,
            "error": "Desktop plugin connection is not yet qualified",
        }


async def unavailable_model():
    return {
        "available": False,
        "reason": "Desktop plugin connection is not yet qualified",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-dir", type=Path, required=True)
    parser.add_argument("--port", type=int, default=8097)
    parser.add_argument("--web-port", type=int, default=5197)
    parser.add_argument("--enable-desktop-bridge", action="store_true")
    parser.add_argument("--enable-confined-inspection", action="store_true")
    parser.add_argument("--enable-native-editor", action="store_true")
    parser.add_argument("--enable-native-working-view", action="store_true")
    args = parser.parse_args()
    if args.enable_native_editor and not args.enable_desktop_bridge:
        parser.error("Native editor requires the opt-in desktop bridge")
    if args.enable_native_working_view and not args.enable_native_editor:
        parser.error("Native working view requires the opt-in native editor")
    if args.enable_confined_inspection and not args.enable_desktop_bridge:
        parser.error("Confined inspection requires the opt-in desktop bridge")
    state = args.state_dir.resolve()
    database = state / "wright.sqlite"
    if args.enable_desktop_bridge and not database.exists():
        from data_vault import upgrade_database

        state.mkdir(parents=True, exist_ok=True)
        upgrade_database(database)
    info = (
        json.loads((state / "probe.json").read_text())
        if (state / "probe.json").is_file()
        else {}
    )
    if not database.is_file():
        parser.error("Use existing isolated probe state")
    token_file = state / ".preview-api-token"
    if not token_file.exists():
        fd = os.open(token_file, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w") as stream:
            stream.write(secrets.token_urlsafe(48))
    os.environ.update(
        {
            "DATABASE_PATH": str(database),
            "WRIGHT_DATA_ROOT": str(state),
            "WRIGHT_SECRETS_PATH": str(state / "credentials.json"),
            "WRIGHT_BIND_HOST": "127.0.0.1",
            "WRIGHT_AUTH_MODE": "enforced",
            "WRIGHT_API_TOKEN": token_file.read_text(),
            "WRIGHT_ALLOWED_ORIGINS": f"http://127.0.0.1:{args.web_port},http://localhost:{args.web_port}",
            "WRIGHT_API_MCP_AUTOSTART": "0",
        }
    )

    import uvicorn
    from starlette.responses import JSONResponse
    from api.main import app
    from api.composition import workspace_service

    app.state.agent_engine = DetachedDesktopConnection()
    workspace_service().workflow_model_capabilities = unavailable_model
    desktop = None
    if args.enable_desktop_bridge:
        from desktop_backend import DesktopBackend

        service = workspace_service()
        service.parent_dir_provider = lambda: str(state / "workspaces")
        if args.enable_confined_inspection:
            service.workflow_integration_policies.enabled = True
        desktop = DesktopBackend(
            service,
            state,
            args.web_port,
            confined_inspection=args.enable_confined_inspection,
            native_editor=args.enable_native_editor,
            native_working_view=args.enable_native_working_view,
        )
        app.state.agent_engine = desktop
        app.state.mcp_authorization_presenter = desktop.oauth.present
        app.include_router(desktop.router())
        # The normal app already ends with a GET frontend fallback. Newly
        # included API routes must precede it rather than returning HTML 200.
        app.router.routes.sort(
            key=lambda route: (
                0 if getattr(route, "path", "").startswith("/api/desktop/") else 1
            )
        )

    @app.middleware("http")
    async def preview_boundary(request, call_next):
        path = request.url.path
        agent_call = path.startswith("/api/agent") and path != "/api/agent/health"
        source_edit = path == "/api/workspace/workflow-sources" and request.method in {
            "POST",
            "PUT",
        }
        browser_auth = path == "/api/auth/session"
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
                r"/api/workspace/process-interfaces/(?:runs/[A-Za-z0-9._:-]+/cancel|interactions/[A-Za-z0-9._:-]+/response)",
                path,
            )
            is not None
        )
        desktop_operation = desktop is not None and (
            path.startswith("/api/desktop/") or process_operation
        )
        if agent_call or (
            request.method not in {"GET", "HEAD", "OPTIONS"}
            and not source_edit
            and not browser_auth
            and not desktop_operation
        ):
            return JSONResponse(
                status_code=503,
                content={
                    "detail": {
                        "code": "DESKTOP_BRIDGE_NOT_CONNECTED",
                        "message": "This preview supports workflow editing and results. Desktop-driven execution is not yet connected.",
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
        return await call_next(request)

    descriptor = {
        "api_url": f"http://127.0.0.1:{args.port}",
        "web_url": f"http://127.0.0.1:{args.web_port}/workspace/{info['workspace_id']}?host=openai-desktop"
        if info.get("workspace_id")
        else f"http://127.0.0.1:{args.web_port}/?host=openai-desktop",
        "state_dir": str(state),
        "workspace_id": info.get("workspace_id"),
        "capabilities": "experimental desktop reasoning bridge; connection required"
        if desktop is not None
        else "source editing and existing results; execution unavailable",
    }
    (state / "preview.json").write_text(json.dumps(descriptor, indent=2))
    print(json.dumps(descriptor), flush=True)
    uvicorn.run(app, host="127.0.0.1", port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
