import time
import httpx
import sqlite3
import os
from fastapi import APIRouter, Request, HTTPException, status, Query
from pydantic import BaseModel
from typing import Optional
from api.config import DATABASE_PATH

router = APIRouter()


class SetupStatusResponse(BaseModel):
    is_configured: bool
    llm_api_url: Optional[str]
    active_agent: str
    theme: str


class ConfigureRequest(BaseModel):
    llm_api_url: str = ""
    active_agent: str


class ConfigureResponse(BaseModel):
    success: bool
    message: str


class HealthCheckResponse(BaseModel):
    status: str
    latency_ms: float
    error: Optional[str] = None


@router.get("/status", response_model=SetupStatusResponse)
async def get_setup_status(request: Request):
    llm_api_url = None
    active_agent = "hermes"

    # 1. Check DB first
    try:
        if os.path.exists(DATABASE_PATH):
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT key, value FROM system_settings")
            rows = cursor.fetchall()
            conn.close()
            for key, value in rows:
                if key == "llm_api_url":
                    llm_api_url = value
                elif key == "active_agent":
                    active_agent = value
    except Exception:
        pass

    # 2. Check environment if DB is empty
    if not llm_api_url:
        llm_api_url = os.getenv("LLM_API_URL")

    # 3. Fallback to explicit runtime configuration if database/env config is not set.
    if not llm_api_url:
        from api.config import get_llm_api_url
        llm_api_url = get_llm_api_url()

    # If active_agent in app state is different, sync it
    sync_manager = getattr(request.app.state, "agent_sync_manager", None)
    if sync_manager:
        # Sync active_agent back and forth
        if active_agent != sync_manager.active_agent:
            sync_manager.active_agent = active_agent

    launched_by_hermes = os.getenv("WRIGHT_LAUNCHED_BY_HERMES", "").strip().lower() in {
        "1",
        "true",
        "yes",
    }
    is_configured = bool(llm_api_url and llm_api_url.strip()) or (
        active_agent == "hermes" and launched_by_hermes
    )
    from api.config import get_ui_theme

    theme = get_ui_theme()

    return SetupStatusResponse(
        is_configured=is_configured,
        llm_api_url=llm_api_url,
        active_agent=active_agent,
        theme=theme,
    )


@router.post("/configure", response_model=ConfigureResponse)
async def configure_system(body: ConfigureRequest, request: Request):
    url = body.llm_api_url.strip()
    agent = body.active_agent.strip().lower()

    if not url and agent != "hermes":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="LLM API URL cannot be empty.",
        )

    if agent not in ["hermes", "openclaw", "pi"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported agent selected.",
        )

    # Save to database
    try:
        os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
        conn = sqlite3.connect(DATABASE_PATH)
        conn.execute(
            "INSERT OR REPLACE INTO system_settings (key, value) VALUES ('llm_api_url', ?)",
            (url,),
        )
        conn.execute(
            "INSERT OR REPLACE INTO system_settings (key, value) VALUES ('active_agent', ?)",
            (agent,),
        )
        conn.commit()
        conn.close()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save settings: {str(e)}",
        )

    # Sync with app state
    sync_manager = getattr(request.app.state, "agent_sync_manager", None)
    if sync_manager:
        sync_manager.active_agent = agent

    return ConfigureResponse(success=True, message="System configured successfully.")


@router.get("/health", response_model=HealthCheckResponse)
async def check_custom_health(url: str = Query(..., description="LLM URL to test")):
    url = url.strip()
    if not url:
        return HealthCheckResponse(
            status="unhealthy", latency_ms=0.0, error="URL is empty"
        )

    urls_to_try = [url]
    # If it doesn't end with /health, try appending it as a fallback
    if not url.endswith("/health") and not url.endswith("/health/"):
        base_url = url[:-1] if url.endswith("/") else url
        urls_to_try.append(f"{base_url}/health")

    last_error = None
    start_time = time.perf_counter()

    for test_url in urls_to_try:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(test_url, timeout=5.0)
                latency = (time.perf_counter() - start_time) * 1000.0
                if response.status_code == 200:
                    return HealthCheckResponse(status="healthy", latency_ms=latency)
                else:
                    last_error = f"HTTP {response.status_code}: {response.text[:100]}"
        except Exception as e:
            last_error = str(e)

    latency = (time.perf_counter() - start_time) * 1000.0
    return HealthCheckResponse(status="unhealthy", latency_ms=latency, error=last_error)


@router.delete("/reset", response_model=ConfigureResponse)
async def reset_setup(request: Request):
    """Reset system configuration. Used by E2E tests to ensure a clean state."""
    try:
        if os.path.exists(DATABASE_PATH):
            conn = sqlite3.connect(DATABASE_PATH)
            conn.execute(
                "DELETE FROM system_settings WHERE key IN ('llm_api_url', 'active_agent')"
            )
            conn.commit()
            conn.close()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset settings: {str(e)}",
        )

    return ConfigureResponse(success=True, message="Setup reset successfully.")
