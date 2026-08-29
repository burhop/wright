import time
import httpx
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel


from agent_adapters import create_agent_engine
from api.config import (
    DATABASE_PATH,
    McpTransportSettings,
    api_mcp_autostart_enabled,
    get_llm_health_url,
    get_workspace_surface_settings,
)
from api.routers.agent import router as agent_router
from api.routers.mcp import router as mcp_router
from api.routers.vault import router as vault_router
from api.routers.workspace import router as workspace_router
from api.routers.setup import router as setup_router
from api.routers.logs import router as logs_router
from api.routers.settings import router as settings_router
from api.routers.gateway import router as gateway_router
from api.routers.engineering_models import router as engineering_models_router
from api.routers.program_status import router as program_status_router
from api.routers.support_diagnostics import router as support_diagnostics_router
from api.routers.surface_events import router as surface_events_router
from api.routers.surface_displays import router as surface_displays_router
from api.routers.live_apps import router as live_apps_router
from api.routers.surface_presentations import router as surface_presentations_router
from api.routers.surface_preview import router as surface_preview_router
from api.routers.surface_mcp_apps import router as surface_mcp_apps_router
from api.routers.surfaces import router as surfaces_router
from api.surface_host_dispatch import SurfaceHostDispatchMiddleware
from api.surface_http_proxy import SurfaceHttpProxy
from api.surface_route_authority import SurfaceRouteAuthority
from api.surface_sse_proxy import SurfaceSseProxy
from api.surface_websocket_proxy import SurfaceWebSocketProxy
from api.middleware.tracing import TracingMiddleware
from api.composition import (
    build_api_gateway_service,
    close_application_services,
    close_surface_application_services,
    surface_application,
    engineering_model_application,
    support_diagnostic_application,
    workspace_service,
)
from api.mcp_transport import AuthenticatedMcpTransport, McpTransportMount
from api.security import (
    ControlPlaneSecurityMiddleware,
    SESSION_COOKIE,
    SecuritySettings,
    authorize_websocket,
)
from api.schemas.common import ErrorResponse, ErrorCodes
from core.logging import get_logger
from api.logging_config import configure_logging
from tool_registry import McpEngine
from workspace_service import AgentSyncManager
from data_vault import install_default_secret_provider

# Configure structured JSON logging globally (Constitution Section 7)
configure_logging()
install_default_secret_provider()
logger = get_logger("api.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Refresh after test/deployment environment setup, before serving requests.
    app.state.security_settings = SecuritySettings.from_env()
    app.state.security_settings.validate()
    app.state.workspace_surface_settings = get_workspace_surface_settings()
    # State must be fully migrated and verified before runtime construction.
    try:
        from api.database.migrate import run_migrations

        run_migrations()
        from api.database.secret_migration import migrate_plaintext_secrets

        migrate_plaintext_secrets(DATABASE_PATH)
        from tool_registry.catalog_reconcile import (
            reconcile_active_engineering_catalog,
            reconcile_installed_bundle,
            reconcile_wright_managed_servers,
        )

        _, catalog_diagnostic = reconcile_active_engineering_catalog(DATABASE_PATH)
        if catalog_diagnostic:
            logger.warning(
                "catalog_recovery_active",
                code=catalog_diagnostic["code"],
                message=catalog_diagnostic["message"],
            )
        reconcile_installed_bundle(DATABASE_PATH)
        reconcile_wright_managed_servers(DATABASE_PATH)
    except Exception as exc:
        logger.error(
            "database_readiness_failed",
            error_type=type(exc).__name__,
            error="Database lifecycle validation failed",
        )
        raise

    # Startup initializes the MCP engine only. MCP server processes are started
    # when an active workspace has those installed servers assigned to it.
    if not hasattr(app.state, "agent_engine"):
        app.state.agent_engine = create_agent_engine(db_path=DATABASE_PATH)
    if not hasattr(app.state, "agent_sync_manager"):
        from api.services.wright_gateway_sync import (
            sync_workspace_tools_to_wright_gateway,
        )

        app.state.agent_sync_manager = AgentSyncManager(
            DATABASE_PATH, sync_workspace_tools_to_wright_gateway
        )
    mcp_settings = McpTransportSettings.from_env()
    app.state.mcp_engine = McpEngine(
        DATABASE_PATH,
        operation_timeout=mcp_settings.operation_timeout_seconds,
    )
    if app.state.workspace_surface_settings.flags.webmcp:
        app.state.surface_webmcp_router = app.state.mcp_engine.webmcp_router
        preview_app.state.surface_webmcp_router = app.state.surface_webmcp_router
    if api_mcp_autostart_enabled():
        await app.state.mcp_engine.sync_active_servers()
    app.state.gateway_service = build_api_gateway_service(
        DATABASE_PATH, app.state.mcp_engine, mcp_settings
    )
    app.state.mcp_transport = AuthenticatedMcpTransport(
        app.state.gateway_service,
        mcp_settings,
        app.state.security_settings,
    )
    try:
        app.state.workspace_service = workspace_service()
        app.state.engineering_model_application = engineering_model_application()
        app.state.support_diagnostic_application = support_diagnostic_application()
        if app.state.workspace_surface_settings.flags.model:
            app.state.surface_application = surface_application()
            await app.state.surface_application.reconcile_startup()
            if app.state.workspace_surface_settings.flags.live_apps:
                app.state.surface_http_proxy = SurfaceHttpProxy()
                app.state.surface_sse_proxy = SurfaceSseProxy()
                app.state.surface_websocket_proxy = SurfaceWebSocketProxy()
                app.state.surface_route_authority = SurfaceRouteAuthority(
                    tokens=app.state.surface_application.presentation_tokens,
                    manager_for_workspace=(
                        app.state.surface_application.runtime_registry.manager_for
                    ),
                )
                for name in (
                    "surface_http_proxy",
                    "surface_sse_proxy",
                    "surface_websocket_proxy",
                    "surface_route_authority",
                ):
                    setattr(preview_app.state, name, getattr(app.state, name))
        async with app.state.mcp_transport.run():
            yield
    finally:
        # Shutdown owns every process and worker constructed during startup.
        try:
            surface_graph = getattr(app.state, "surface_application", None)
            if surface_graph is not None:
                await surface_graph.begin_shutdown()
            for name in ("surface_http_proxy", "surface_sse_proxy"):
                proxy = getattr(app.state, name, None)
                if proxy is not None:
                    await proxy.aclose()
        finally:
            await close_surface_application_services()
        try:
            await app.state.gateway_service.shutdown()
        except Exception as e:
            logger.exception("mcp_shutdown_failed", error=str(e))
        await close_application_services()


app = FastAPI(title="Wright API", version="0.1.0", lifespan=lifespan)
app.state.security_settings = SecuritySettings.from_env()
app.state.workspace_surface_settings = get_workspace_surface_settings()

# Allow only explicitly configured frontend origins.
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(app.state.security_settings.allowed_origins),
    allow_origin_regex=app.state.security_settings.cors_origin_regex(),
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "X-Trace-Id",
        "X-Wright-Workspace-ID",
        "X-Wright-Session-ID",
        "Idempotency-Key",
        "Last-Event-ID",
        "X-Wright-Display-Contract",
    ],
)
app.add_middleware(ControlPlaneSecurityMiddleware)

# Add OpenTelemetry tracing middleware (Constitution Section 7)
app.add_middleware(TracingMiddleware)


# Custom exception handlers for standardized ErrorResponse


def _get_trace_id(request: Request) -> str:
    return getattr(request.state, "trace_id", "unknown")


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    trace_id = _get_trace_id(request)
    status_map = {
        400: ErrorCodes.VALIDATION_ERROR,
        404: ErrorCodes.WORKSPACE_NOT_FOUND,
        500: ErrorCodes.INTERNAL_ERROR,
        502: ErrorCodes.AGENT_UNAVAILABLE,
    }
    structured_detail = exc.detail if isinstance(exc.detail, dict) else None
    error_code = (
        str(structured_detail.get("code"))
        if structured_detail and structured_detail.get("code")
        else status_map.get(exc.status_code, ErrorCodes.INTERNAL_ERROR)
    )
    message = (
        str(structured_detail.get("message"))
        if structured_detail and structured_detail.get("message")
        else str(exc.detail)
    )
    details = (
        {
            key: value
            for key, value in structured_detail.items()
            if key not in {"code", "message", "trace_id"}
        }
        if structured_detail
        else None
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error_code=error_code,
            message=message,
            trace_id=trace_id,
            details=details or None,
        ).model_dump(),
        headers={"X-Trace-Id": trace_id},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    trace_id = _get_trace_id(request)
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            error_code=ErrorCodes.VALIDATION_ERROR,
            message="Request validation failed",
            trace_id=trace_id,
            details={"errors": exc.errors()},
        ).model_dump(),
        headers={"X-Trace-Id": trace_id},
    )


# Mount the routers
app.include_router(workspace_router, prefix="/api/workspace", tags=["Workspace"])
app.include_router(
    support_diagnostics_router,
    prefix="/api/workspace/support-diagnostics",
    tags=["Support Diagnostics"],
)
app.include_router(agent_router, prefix="/api/agent", tags=["Agent"])
app.include_router(mcp_router, prefix="/api/mcp", tags=["MCP"])
app.include_router(vault_router, prefix="/api/vault", tags=["Vault"])
app.include_router(setup_router, prefix="/api/setup")
app.include_router(logs_router, prefix="/api/logs", tags=["Logs"])
app.include_router(settings_router, prefix="/api/settings", tags=["Settings"])
app.include_router(gateway_router, prefix="/api/gateway", tags=["Gateway"])
app.include_router(
    program_status_router, prefix="/api/program-status", tags=["Program Status"]
)
app.include_router(
    engineering_models_router,
    prefix="/api/v1/engineering-models",
    tags=["Engineering Models"],
)
if app.state.workspace_surface_settings.flags.model:
    # Events must be registered before the dynamic /surfaces/{surface_id} path.
    app.include_router(
        surface_events_router, prefix="/api/workspace", tags=["Workspace Surfaces"]
    )
    app.include_router(
        surfaces_router, prefix="/api/workspace", tags=["Workspace Surfaces"]
    )
    if app.state.workspace_surface_settings.flags.live_apps:
        app.include_router(
            live_apps_router,
            prefix="/api/workspace",
            tags=["Workspace Surface Live Apps"],
        )
        app.include_router(
            surface_presentations_router,
            prefix="/api/workspace",
            tags=["Workspace Surface Presentations"],
        )
    if app.state.workspace_surface_settings.flags.mcp_apps:
        app.include_router(
            surface_mcp_apps_router,
            prefix="/api/workspace",
            tags=["Workspace Surface MCP Apps"],
        )
    if app.state.workspace_surface_settings.flags.safe_display:
        app.include_router(
            surface_displays_router,
            prefix="/api/workspace",
            tags=["Workspace Surface Displays"],
        )
app.add_route(
    "/mcp",
    McpTransportMount(),
    methods=["GET", "POST", "DELETE"],
    name="mcp-transport",
)

# Preview origins are a separate data plane. The host dispatcher is added last
# and therefore sits outside control-plane authentication and CORS middleware.
preview_app = FastAPI(
    title="Wright Surface Preview",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)
preview_app.state.surface_sandbox_domain = (
    app.state.workspace_surface_settings.preview.domain
)
preview_app.include_router(surface_preview_router)
if (
    app.state.workspace_surface_settings.flags.live_apps
    or app.state.workspace_surface_settings.flags.mcp_apps
    or app.state.workspace_surface_settings.flags.webmcp
):
    app.add_middleware(
        SurfaceHostDispatchMiddleware,
        preview_app=preview_app,
        preview_domain=app.state.workspace_surface_settings.preview.domain,
    )


@app.websocket("/api/webmcp/ws")
async def webmcp_websocket_endpoint(websocket: WebSocket):
    if os.getenv("WRIGHT_WEBMCP_LEGACY_RELAY_ENABLED") != "1":
        await websocket.close(code=1008, reason="Legacy WebMCP relay is disabled")
        return
    selected_protocol = authorize_websocket(websocket, app.state.security_settings)
    await websocket.accept(subprotocol=selected_protocol)
    mcp_engine = app.state.mcp_engine
    await mcp_engine.register_webmcp_connection(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await mcp_engine.handle_webmcp_message(data)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.exception("webmcp_websocket_error", error=str(e))
    finally:
        await mcp_engine.unregister_webmcp_connection(websocket)


class HealthResponse(BaseModel):
    state: str
    latencyMs: float
    baseUrl: str | None = None
    error: str | None = None


class LocalSessionRequest(BaseModel):
    token: str


class LocalSessionStatusResponse(BaseModel):
    auth_required: bool
    authenticated: bool


@app.post("/api/auth/session", status_code=204)
async def create_local_session(body: LocalSessionRequest, response: Response):
    """Exchange the configured local token for a browser-only session cookie."""
    settings: SecuritySettings = app.state.security_settings
    if settings.enforced and not settings.token_valid(body.token):
        from fastapi import HTTPException

        raise HTTPException(status_code=401, detail="Invalid local token")
    browser_session = settings.browser_session_token()
    if browser_session is not None:
        response.set_cookie(
            SESSION_COOKIE,
            browser_session,
            httponly=True,
            secure=os.getenv("WRIGHT_COOKIE_SECURE", "0") == "1",
            samesite="strict",
            path="/api",
        )


@app.delete("/api/auth/session", status_code=204)
async def delete_local_session(request: Request, response: Response):
    if app.state.workspace_surface_settings.flags.model:
        surface_application().revocation.user_logout(
            user_id=getattr(request.state, "principal_id", "local-user")
        )
    response.delete_cookie(SESSION_COOKIE, path="/api")


@app.get("/api/auth/session/status", response_model=LocalSessionStatusResponse)
async def local_session_status(request: Request):
    settings: SecuritySettings = app.state.security_settings
    if not settings.enforced:
        return LocalSessionStatusResponse(auth_required=False, authenticated=True)
    browser_session = request.cookies.get(SESSION_COOKIE)
    return LocalSessionStatusResponse(
        auth_required=True,
        authenticated=settings.browser_session_valid(browser_session),
    )


@app.get("/api/health", response_model=HealthResponse)
async def check_api_health():
    return HealthResponse(state="connected", latencyMs=1.5)


@app.get("/api/runtime/identity")
async def runtime_identity():
    """Return non-secret process identity used by the native lifecycle challenge."""
    from wright_engineering.runtime.server import runtime_identity_payload

    return runtime_identity_payload()


@app.get("/api/agent/health", response_model=HealthResponse)
async def check_agent_health():
    sync_manager = getattr(app.state, "agent_sync_manager", None)
    if (
        sync_manager is not None
        and getattr(sync_manager, "active_agent", "") == "hermes"
        and getattr(sync_manager, "gateway_refresh_in_progress", False)
    ):
        return HealthResponse(
            state="unknown",
            latencyMs=0.0,
            baseUrl=getattr(app.state.agent_engine, "base_url", None),
            error="Hermes gateway is refreshing workspace tools",
        )
    res = await app.state.agent_engine.check_health()
    return HealthResponse(
        state=res["state"],
        latencyMs=res["latencyMs"],
        baseUrl=res.get("baseUrl"),
        error=res.get("error"),
    )


@app.get("/api/inference/health", response_model=HealthResponse)
async def check_inference_health():
    llm_health_checker = getattr(
        app.state.agent_engine, "check_llm_backend_health", None
    )
    if callable(llm_health_checker):
        res = await llm_health_checker()
        return HealthResponse(
            state=res["state"],
            latencyMs=res.get("latencyMs", 0.0),
            baseUrl=res.get("baseUrl"),
            error=res.get("error"),
        )

    start_time = time.perf_counter()
    try:
        async with httpx.AsyncClient() as client:
            health_url = get_llm_health_url()
            if not health_url:
                return HealthResponse(
                    state="disconnected",
                    latencyMs=0.0,
                    error="LLM API URL is not configured",
                )
            response = await client.get(health_url, timeout=5.0)
            latency = (time.perf_counter() - start_time) * 1000.0
            if response.status_code == 200:
                # Also accept json status if available
                return HealthResponse(
                    state="connected",
                    latencyMs=latency,
                    baseUrl=health_url,
                )
            return HealthResponse(
                state="disconnected",
                latencyMs=latency,
                baseUrl=health_url,
                error=f"HTTP {response.status_code}: {response.text[:200]}",
            )
    except Exception as e:
        return HealthResponse(
            state="disconnected",
            latencyMs=0.0,
            baseUrl=get_llm_health_url() or None,
            error=str(e),
        )


@app.get("/api/proxy/onshape", response_class=HTMLResponse)
async def proxy_onshape(request: Request):
    try:
        async with httpx.AsyncClient() as client:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            response = await client.get(
                "https://www.onshape.com",
                headers=headers,
                follow_redirects=True,
                timeout=10.0,
            )
            html = response.text

            # Rewrite absolute and relative links to point to our proxy
            html = html.replace('href="/', 'href="/api/proxy/onshape/')
            html = html.replace('src="/', 'src="/api/proxy/onshape/')
            html = html.replace('action="/', 'action="/api/proxy/onshape/')
            html = html.replace(
                'href="https://www.onshape.com/', 'href="/api/proxy/onshape/'
            )
            html = html.replace(
                'src="https://www.onshape.com/', 'src="/api/proxy/onshape/'
            )

            # Strip/neutralize frame-busting JS
            html = html.replace("window.top.location", "window.self.location")
            html = html.replace("top.location", "self.location")

            return HTMLResponse(content=html, status_code=response.status_code)
    except Exception as exc:
        trace_id = _get_trace_id(request)
        logger.exception(
            "onshape_proxy_failed",
            trace_id=trace_id,
            error=str(exc),
        )
        return Response(
            content=f"Failed to connect to Onshape. Trace ID: {trace_id}",
            status_code=502,
            media_type="text/plain",
            headers={"X-Trace-Id": trace_id},
        )


@app.get("/api/proxy/onshape/{path:path}")
async def proxy_onshape_path(path: str, request: Request):
    try:
        url = f"https://www.onshape.com/{path}"
        query_params = dict(request.query_params)
        async with httpx.AsyncClient() as client:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            response = await client.get(
                url,
                params=query_params,
                headers=headers,
                follow_redirects=True,
                timeout=10.0,
            )

            content_type = response.headers.get("content-type", "text/html")
            content = response.content

            if "text/html" in content_type:
                html = response.text
                html = html.replace('href="/', 'href="/api/proxy/onshape/')
                html = html.replace('src="/', 'src="/api/proxy/onshape/')
                html = html.replace('action="/', 'action="/api/proxy/onshape/')
                html = html.replace(
                    'href="https://www.onshape.com/', 'href="/api/proxy/onshape/'
                )
                html = html.replace(
                    'src="https://www.onshape.com/', 'src="/api/proxy/onshape/'
                )

                html = html.replace("window.top.location", "window.self.location")
                html = html.replace("top.location", "self.location")

                return HTMLResponse(content=html, status_code=response.status_code)

            return Response(
                content=content,
                media_type=content_type,
                status_code=response.status_code,
            )
    except Exception as exc:
        trace_id = _get_trace_id(request)
        logger.exception(
            "onshape_proxy_path_failed",
            trace_id=trace_id,
            path=path,
            error=str(exc),
        )
        return Response(
            content=f"Failed to connect to Onshape. Trace ID: {trace_id}",
            status_code=502,
            media_type="text/plain",
            headers={"X-Trace-Id": trace_id},
        )


async def _resolve_spa_asset(
    static_files: StaticFiles, full_path: str, request: Request
) -> Response | None:
    """Delegate containment and regular-file validation to Starlette."""
    try:
        return await static_files.get_response(full_path, request.scope)
    except StarletteHTTPException as exc:
        if exc.status_code != 404:
            raise
        return None


# Serve frontend static files in production if the dist directory exists

if "FRONTEND_DIST_DIR" in os.environ:
    dist_dir = os.environ["FRONTEND_DIST_DIR"]
else:
    try:
        from wright_engineering.runtime.server import packaged_static_path

        dist_dir = str(packaged_static_path())
    except Exception:
        dist_dir = "/workspace/apps/web/dist"
if os.path.exists(dist_dir):
    # Mount static assets (js, css, images) under /assets
    assets_dir = os.path.join(dist_dir, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="static-assets")

    # SPA catch-all: serve index.html for any non-API route so client-side
    # routing works for paths like /tool-registry, /workspace/*, etc.
    index_html = os.path.join(dist_dir, "index.html")
    spa_static_files = StaticFiles(directory=dist_dir)

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str, request: Request):
        if full_path:
            response = await _resolve_spa_asset(spa_static_files, full_path, request)
            if response is not None:
                return response
        # Otherwise serve the SPA entry point
        return FileResponse(index_html)
else:

    @app.get("/")
    async def root():
        return {"message": "Wright API is running"}

# Reload trigger comment to refresh workspace packages - v2
