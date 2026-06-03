import time
import httpx
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agent_adapters import HermesAdapter
from api.config import HERMES_WEBUI_BASE_URL, LLM_HEALTH_URL, DATABASE_PATH
from api.routers.agent import router as agent_router
from api.routers.mcp import router as mcp_router
from api.routers.workspace import router as workspace_router
from tool_registry import McpEngine

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize McpEngine and sync servers configured as active in DB
    app.state.mcp_engine = McpEngine(DATABASE_PATH)
    try:
        await app.state.mcp_engine.sync_active_servers()
        # Sync database server states into Hermes configs on startup
        from api.routers.mcp import sync_mcp_server_to_hermes, get_servers
        for s in get_servers(DATABASE_PATH):
            sync_mcp_server_to_hermes(s)
    except Exception as e:
        print(f"Error syncing active MCP servers on startup: {e}")
    yield
    # Shutdown: Stop active subprocesses/runners
    try:
        await app.state.mcp_engine.shutdown()
    except Exception as e:
        print(f"Error shutting down MCP engine: {e}")

app = FastAPI(title="Wright API", version="0.1.0", lifespan=lifespan)

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instantiate and store the Hermes adapter engine in the app state
app.state.agent_engine = HermesAdapter(HERMES_WEBUI_BASE_URL)
from core import AgentSyncManager
app.state.agent_sync_manager = AgentSyncManager(DATABASE_PATH)

# Mount the agent router
app.include_router(agent_router, prefix="/api/agent")

# Mount the MCP router
app.include_router(mcp_router, prefix="/api/mcp")

# Mount the workspace router
app.include_router(workspace_router, prefix="/api/workspace")

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
        import logging
        logging.getLogger("api.main").error("WebMCP WebSocket connection error: %s", e)
    finally:
        await mcp_engine.unregister_webmcp_connection(websocket)

class HealthResponse(BaseModel):
    state: str
    latencyMs: float

@app.get("/api/health", response_model=HealthResponse)
async def check_api_health():
    return HealthResponse(state="connected", latencyMs=1.5)

@app.get("/api/agent/health", response_model=HealthResponse)
async def check_agent_health():
    res = await app.state.agent_engine.check_health()
    return HealthResponse(state=res["state"], latencyMs=res["latencyMs"])

@app.get("/api/inference/health", response_model=HealthResponse)
async def check_inference_health():
    start_time = time.perf_counter()
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(LLM_HEALTH_URL, timeout=5.0)
            latency = (time.perf_counter() - start_time) * 1000.0
            if response.status_code == 200:
                # Also accept json status if available
                return HealthResponse(state="connected", latencyMs=latency)
    except Exception:
        pass
    return HealthResponse(state="disconnected", latencyMs=0.0)

@app.get("/")
async def root():
    return {"message": "Wright API is running"}
