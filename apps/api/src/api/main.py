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
    get_llm_health_url,
)
from api.routers.agent import router as agent_router
from api.routers.mcp import router as mcp_router
from api.routers.vault import router as vault_router
from api.routers.workspace import router as workspace_router
from api.routers.setup import router as setup_router
from api.routers.logs import router as logs_router
from api.routers.settings import router as settings_router
from api.routers.gateway import router as gateway_router
from api.middleware.tracing import TracingMiddleware
from api.schemas.common import ErrorResponse, ErrorCodes
from core.logging import configure_logging, get_logger
from tool_registry import McpEngine
from core import AgentSyncManager

# Configure structured JSON logging globally (Constitution Section 7)
configure_logging()
logger = get_logger("api.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Run database migrations to initialize the schema and seed the catalog
    try:
        from api.database.migrate import run_migrations

        run_migrations()
    except Exception as e:
        logger.exception("database_migration_failed", error=str(e))

    # Startup initializes the MCP engine only. MCP server processes are started
    # when an active workspace has those installed servers assigned to it.
    app.state.mcp_engine = McpEngine(DATABASE_PATH)
    yield
    # Shutdown: Stop active subprocesses/runners
    try:
        await app.state.mcp_engine.shutdown()
    except Exception as e:
        logger.exception("mcp_shutdown_failed", error=str(e))


app = FastAPI(title="Wright API", version="0.1.0", lifespan=lifespan)

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    error_code = status_map.get(exc.status_code, ErrorCodes.INTERNAL_ERROR)
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error_code=error_code,
            message=str(exc.detail),
            trace_id=trace_id,
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


# Instantiate and store the default agent engine in the app state.
app.state.agent_engine = create_agent_engine(db_path=DATABASE_PATH)
app.state.agent_sync_manager = AgentSyncManager(DATABASE_PATH)

# Mount the routers
app.include_router(workspace_router, prefix="/api/workspace", tags=["Workspace"])
app.include_router(agent_router, prefix="/api/agent", tags=["Agent"])
app.include_router(mcp_router, prefix="/api/mcp", tags=["MCP"])
app.include_router(vault_router, prefix="/api/vault", tags=["Vault"])
app.include_router(setup_router, prefix="/api/setup")
app.include_router(logs_router, prefix="/api/logs", tags=["Logs"])
app.include_router(settings_router, prefix="/api/settings", tags=["Settings"])
app.include_router(gateway_router, prefix="/api/gateway", tags=["Gateway"])


@app.websocket("/api/webmcp/ws")
async def webmcp_websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
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


@app.get("/api/health", response_model=HealthResponse)
async def check_api_health():
    return HealthResponse(state="connected", latencyMs=1.5)


@app.get("/api/agent/health", response_model=HealthResponse)
async def check_agent_health():
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
async def proxy_onshape():
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
    except Exception as e:
        logger.error(f"Failed to proxy onshape: {e}")
        return HTMLResponse(
            content=f"<h3>Failed to connect to Onshape</h3><p>{e}</p>", status_code=502
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
    except Exception as e:
        logger.error(f"Failed to proxy onshape path {path}: {e}")
        return Response(content=f"Error: {e}", status_code=502)


# Serve frontend static files in production if the dist directory exists

dist_dir = os.environ.get("FRONTEND_DIST_DIR", "/workspace/apps/web/dist")
if os.path.exists(dist_dir):
    # Mount static assets (js, css, images) under /assets
    assets_dir = os.path.join(dist_dir, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="static-assets")

    # SPA catch-all: serve index.html for any non-API route so client-side
    # routing works for paths like /tool-registry, /workspace/*, etc.
    index_html = os.path.join(dist_dir, "index.html")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # If the requested file exists in dist, serve it directly
        # Guard against path traversal (CWE-22)
        file_path = os.path.realpath(os.path.join(dist_dir, full_path))
        real_dist = os.path.realpath(dist_dir)
        if (
            full_path
            and os.path.isfile(file_path)
            and file_path.startswith(real_dist + os.sep)
        ):
            return FileResponse(file_path)
        # Otherwise serve the SPA entry point
        return FileResponse(index_html)
else:

    @app.get("/")
    async def root():
        return {"message": "Wright API is running"}

# Reload trigger comment to refresh workspace packages - v2
