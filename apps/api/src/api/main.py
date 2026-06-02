import time
import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agent_adapters import HermesAdapter
from api.config import HERMES_WEBUI_BASE_URL, LLM_HEALTH_URL
from api.routers.agent import router as agent_router

app = FastAPI(title="Wright API", version="0.1.0")

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

# Mount the agent router
app.include_router(agent_router, prefix="/api/agent")

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
