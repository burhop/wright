import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Wright API", version="0.1.0")

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class HealthResponse(BaseModel):
    state: str
    latencyMs: float

@app.get("/api/health", response_model=HealthResponse)
async def check_api_health():
    return HealthResponse(state="connected", latencyMs=1.5)

@app.get("/api/agent/health", response_model=HealthResponse)
async def check_agent_health():
    return HealthResponse(state="connected", latencyMs=5.0)

@app.get("/api/inference/health", response_model=HealthResponse)
async def check_inference_health():
    return HealthResponse(state="connected", latencyMs=12.0)

@app.get("/")
async def root():
    return {"message": "Wright API is running"}
