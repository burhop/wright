import sqlite3
import os
import re
import subprocess
import threading
import time
import uuid
from pathlib import Path
from fastapi import APIRouter, Request, HTTPException, status, Query
from pydantic import BaseModel
from typing import Optional
from api.config import DATABASE_PATH
from agent_adapters import (
    UnsupportedAgentRuntimeError,
    create_agent_engine,
    default_agent_registry,
    probe_health,
)
from agent_adapters.hermes_config import hermes_config_path
from agent_adapters.llm_seed import apply_llm_seed, provider_presets, read_llm_summary

router = APIRouter()


class SetupStatusResponse(BaseModel):
    is_configured: bool
    llm_api_url: Optional[str]
    active_agent: str
    theme: str
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    llm_configured: bool = False
    llm_auth_configured: bool = False


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


class LlmProviderPreset(BaseModel):
    id: str
    label: str
    auth_type: str
    requires_api_key: bool
    default_base_url: str
    supports_seed_file: bool
    notes: str


class LlmProvidersResponse(BaseModel):
    providers: list[LlmProviderPreset]


class LlmConfigureRequest(BaseModel):
    provider: str
    base_url: str = ""
    model: str = ""
    api_key: str = ""
    custom_provider_name: str = "wright-llm"


class LlmConfigureResponse(BaseModel):
    success: bool
    configured: bool
    auth_configured: bool
    provider: Optional[str] = None
    base_url: Optional[str] = None
    model: Optional[str] = None
    message: str


class CodexLoginResponse(BaseModel):
    session_id: str
    status: str
    verification_url: Optional[str] = None
    user_code: Optional[str] = None
    message: str
    error: Optional[str] = None


class _CodexLoginJob:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.status = "starting"
        self.verification_url: str | None = None
        self.user_code: str | None = None
        self.message = "Starting Codex login."
        self.error: str | None = None
        self.started_at = time.time()
        self.completed_at: float | None = None
        self.return_code: int | None = None
        self._lock = threading.Lock()

    def update(self, **changes):
        with self._lock:
            for key, value in changes.items():
                setattr(self, key, value)

    def as_response(self) -> CodexLoginResponse:
        with self._lock:
            return CodexLoginResponse(
                session_id=self.session_id,
                status=self.status,
                verification_url=self.verification_url,
                user_code=self.user_code,
                message=self.message,
                error=self.error,
            )


_CODEX_LOGIN_JOBS: dict[str, _CodexLoginJob] = {}
_CODEX_LOGIN_JOBS_LOCK = threading.Lock()
_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def _settings_rows() -> dict[str, str]:
    values: dict[str, str] = {}
    if not os.path.exists(DATABASE_PATH):
        return values
    conn = sqlite3.connect(DATABASE_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT key, value FROM system_settings")
        rows = cursor.fetchall()
    finally:
        conn.close()
    for key, value in rows:
        values[str(key)] = "" if value is None else str(value)
    return values


def _upsert_settings(settings: dict[str, str]) -> None:
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    try:
        for key, value in settings.items():
            conn.execute(
                "INSERT OR REPLACE INTO system_settings (key, value) VALUES (?, ?)",
                (key, value),
            )
        conn.commit()
    finally:
        conn.close()


def _hermes_profile_paths() -> tuple[str | None, str | None]:
    config_path = hermes_config_path()
    if not config_path:
        return None, None
    return config_path, str(Path(config_path).with_name("auth.json"))


def _clean_cli_line(line: str) -> str:
    return _ANSI_RE.sub("", line).strip()


def _run_codex_login_job(job: _CodexLoginJob) -> None:
    profile = os.getenv("HERMES_PROFILE", "wright").strip() or "wright"
    command = ["hermes", "-p", profile, "auth", "add", "openai-codex", "--no-browser"]
    env = {
        **os.environ,
        "PYTHONUNBUFFERED": "1",
    }
    if "HERMES_HOME" not in env:
        env["HERMES_HOME"] = str(Path.home() / ".hermes")

    expecting_code = False
    output_tail: list[str] = []
    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            text=True,
            bufsize=1,
            env=env,
            cwd=os.getenv("HOME") or None,
        )
    except OSError as exc:
        job.update(
            status="failed",
            error=f"Could not start Hermes Codex login: {exc}",
            message="Hermes Codex login could not be started.",
            completed_at=time.time(),
        )
        return

    job.update(status="running", message="Hermes Codex login is running.")

    assert process.stdout is not None
    for raw_line in process.stdout:
        line = _clean_cli_line(raw_line)
        if not line:
            continue
        output_tail = [*output_tail, line][-12:]
        if line.startswith("https://") and "/codex/device" in line:
            job.update(
                verification_url=line,
                status="awaiting_user",
                message="Open the verification URL and enter the code.",
            )
        elif "Open this URL" in line:
            job.update(message="Waiting for the Codex verification URL.")
        elif "Enter this code" in line:
            expecting_code = True
        elif expecting_code:
            expecting_code = False
            job.update(
                user_code=line,
                status="awaiting_user",
                message="Open the verification URL and enter the code.",
            )
        elif "Waiting for sign-in" in line:
            job.update(
                status="awaiting_user",
                message="Waiting for Codex sign-in to complete.",
            )
        elif "Existing Codex credentials found" in line:
            job.update(status="running", message="Existing Codex credentials found.")
        elif "Login successful" in line or "Credentials imported" in line:
            job.update(status="succeeded", message="Codex login succeeded.")

    return_code = process.wait()
    job.return_code = return_code
    if return_code == 0:
        if job.status != "succeeded":
            job.update(status="succeeded", message="Codex login completed.")
        job.update(completed_at=time.time())
        try:
            _upsert_settings(
                {
                    "llm_provider": "openai-codex",
                    "llm_api_url": "https://chatgpt.com/backend-api/codex",
                    "active_agent": "hermes",
                }
            )
        except Exception:
            pass
        return

    job.update(
        status="failed",
        error="\n".join(output_tail) or f"Hermes exited with code {return_code}",
        message="Codex login failed.",
        completed_at=time.time(),
    )


def _start_codex_login_job() -> _CodexLoginJob:
    job = _CodexLoginJob(str(uuid.uuid4()))
    with _CODEX_LOGIN_JOBS_LOCK:
        _CODEX_LOGIN_JOBS[job.session_id] = job
    thread = threading.Thread(target=_run_codex_login_job, args=(job,), daemon=True)
    thread.start()
    return job


@router.get("/status", response_model=SetupStatusResponse)
async def get_setup_status(request: Request):
    llm_api_url = None
    active_agent = "hermes"
    registry = default_agent_registry()
    settings = {}

    # 1. Check DB first
    try:
        settings = _settings_rows()
        llm_api_url = settings.get("llm_api_url")
        active_agent = settings.get("active_agent") or active_agent
    except Exception:
        pass

    config_path, auth_path = _hermes_profile_paths()
    llm_summary = read_llm_summary(config_path, auth_path=auth_path)

    # 2. Check environment if DB is empty
    if not llm_api_url:
        llm_api_url = os.getenv("LLM_API_URL")

    # 3. Fallback to explicit Hermes/runtime configuration if DB/env config is not set.
    if not llm_api_url:
        llm_api_url = llm_summary.get("base_url")

    # 4. Fallback to explicit runtime configuration if database/env config is not set.
    if not llm_api_url:
        from api.config import get_llm_api_url

        llm_api_url = get_llm_api_url()

    try:
        active_agent = registry.resolve_provider(active_agent).name
    except UnsupportedAgentRuntimeError:
        active_agent = registry.default_provider().name

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
    llm_configured = bool(llm_summary.get("configured"))
    requires_llm_auth = llm_summary.get("provider") == "openai-codex"
    is_configured = (
        llm_configured
        if requires_llm_auth
        else bool(llm_api_url and llm_api_url.strip())
    ) or (
        active_agent == "hermes" and launched_by_hermes
    )
    from api.config import get_ui_theme

    theme = get_ui_theme()

    return SetupStatusResponse(
        is_configured=is_configured,
        llm_api_url=llm_api_url,
        active_agent=active_agent,
        theme=theme,
        llm_provider=llm_summary.get("provider"),
        llm_model=llm_summary.get("model"),
        llm_configured=llm_configured,
        llm_auth_configured=bool(llm_summary.get("auth_configured")),
    )


@router.post("/configure", response_model=ConfigureResponse)
async def configure_system(body: ConfigureRequest, request: Request):
    url = body.llm_api_url.strip()
    agent = body.active_agent.strip().lower()
    registry = default_agent_registry()

    try:
        provider = registry.resolve_provider(agent)
    except UnsupportedAgentRuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    agent = provider.name

    if not url and agent != "hermes":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="LLM API URL cannot be empty.",
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
    request.app.state.agent_engine = create_agent_engine(
        agent, db_path=DATABASE_PATH, registry=registry
    )

    return ConfigureResponse(success=True, message="System configured successfully.")


@router.get("/llm/providers", response_model=LlmProvidersResponse)
async def list_llm_providers():
    return LlmProvidersResponse(providers=provider_presets())


@router.post("/llm/configure", response_model=LlmConfigureResponse)
async def configure_llm_provider(body: LlmConfigureRequest, request: Request):
    provider = body.provider.strip().lower()
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="LLM provider cannot be empty.",
        )
    if provider not in {
        "custom",
        "openai-compatible",
        "openai_api",
        "openai-api",
        "openai",
        "ollama",
        "lmstudio",
        "docker-model-runner",
        "openai-codex",
        "codex",
        "chatgpt",
    }:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported LLM provider: {provider}",
        )
    if (
        provider not in {"openai-codex", "codex", "chatgpt"}
        and not body.base_url.strip()
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OpenAI-compatible providers require a base URL.",
        )

    config_path, auth_path = _hermes_profile_paths()
    if not config_path:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Hermes configuration path is not available.",
        )

    seed = {
        "provider": provider,
        "base_url": body.base_url.strip(),
        "model": body.model.strip(),
        "api_key": body.api_key.strip(),
        "custom_provider_name": body.custom_provider_name.strip() or "wright-llm",
    }
    try:
        result = apply_llm_seed(config_path, auth_path=auth_path, seed=seed)
        _upsert_settings(
            {
                "llm_provider": result.provider or provider,
                "llm_api_url": result.base_url or "",
                "llm_model": result.model or "",
                "active_agent": "hermes",
            }
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to configure Hermes LLM provider: {exc}",
        )

    sync_manager = getattr(request.app.state, "agent_sync_manager", None)
    if sync_manager:
        sync_manager.active_agent = "hermes"
    request.app.state.agent_engine = create_agent_engine(
        "hermes", db_path=DATABASE_PATH, registry=default_agent_registry()
    )

    if result.provider == "openai-codex" and not result.auth_configured:
        message = (
            "Codex provider selected. Add Hermes Codex credentials through the "
            "startup seed file or Hermes auth flow."
        )
    else:
        message = "Hermes LLM provider configured successfully."

    return LlmConfigureResponse(
        success=True,
        configured=result.configured,
        auth_configured=result.auth_configured,
        provider=result.provider,
        base_url=result.base_url,
        model=result.model,
        message=message,
    )


@router.post("/llm/codex/start", response_model=CodexLoginResponse)
async def start_codex_login():
    job = _start_codex_login_job()
    return job.as_response()


@router.get("/llm/codex/status/{session_id}", response_model=CodexLoginResponse)
async def get_codex_login_status(session_id: str):
    with _CODEX_LOGIN_JOBS_LOCK:
        job = _CODEX_LOGIN_JOBS.get(session_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Codex login session not found.",
        )
    return job.as_response()


@router.get("/health", response_model=HealthCheckResponse)
async def check_custom_health(url: str = Query(..., description="LLM URL to test")):
    from api.config import get_llm_api_url, get_llm_health_url

    result = await probe_health(
        url,
        trusted_local_origins=(get_llm_api_url(), get_llm_health_url()),
    )
    return HealthCheckResponse(
        status=result.status,
        latency_ms=result.latency_ms,
        error=result.error,
    )


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
