import os
from dataclasses import dataclass
from urllib.parse import urlparse
from agent_adapters import resolve_agent_api_settings

# Hermes Native API port and base URL configuration for the 'wright' profile
_HERMES_API_SETTINGS = resolve_agent_api_settings("hermes")
HERMES_API_BASE_URL = _HERMES_API_SETTINGS.base_url
HERMES_API_KEY = _HERMES_API_SETTINGS.api_key
HERMES_API_PORT = urlparse(HERMES_API_BASE_URL).port or 8642


# LLM inference host and health check endpoint
LLM_HEALTH_URL = os.getenv("LLM_HEALTH_URL", "")


# UI theme configuration (defaulting to "dark")
def get_ui_theme() -> str:
    return os.getenv("UI_THEME", "dark")


def get_llm_health_url() -> str:
    """Dynamically get LLM health URL from the database system_settings or env var."""
    import sqlite3

    try:
        if os.path.exists(DATABASE_PATH):
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT value FROM system_settings WHERE key = 'llm_api_url'"
            )
            row = cursor.fetchone()
            conn.close()
            if row and row[0]:
                url = row[0]
                if not url.endswith("/health") and not url.endswith("/health/"):
                    # Strip trailing slash if present
                    if url.endswith("/"):
                        url = url[:-1]
                    if url.endswith("/v1"):
                        url = url[:-3]
                    return f"{url}/health"
                return url
    except Exception:
        pass
    health_url = os.getenv("LLM_HEALTH_URL")
    if health_url:
        return health_url
    api_url = os.getenv("LLM_API_URL")
    if api_url:
        api_url = api_url.rstrip("/")
        if api_url.endswith("/v1"):
            api_url = api_url[:-3]
        return f"{api_url.rstrip('/')}/health"
    return ""


def get_llm_api_url() -> str:
    """Dynamically get the base LLM API URL."""
    import sqlite3

    try:
        if os.path.exists(DATABASE_PATH):
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT value FROM system_settings WHERE key = 'llm_api_url'"
            )
            row = cursor.fetchone()
            conn.close()
            if row and row[0]:
                return row[0]
    except Exception:
        pass
    env_url = os.getenv("LLM_API_URL")
    if env_url:
        return env_url
    health_url = os.getenv("LLM_HEALTH_URL", "")
    if not health_url:
        return ""
    if health_url.endswith("/health"):
        return health_url[:-7]
    return health_url


# Local SQLite database path for state and config persistence
DATABASE_PATH = os.getenv(
    "DATABASE_PATH",
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "state.db",
    ),
)


@dataclass(frozen=True)
class McpTransportSettings:
    maximum_body_bytes: int = 1_048_576
    maximum_concurrency: int = 16
    requests_per_minute: int = 120
    operation_timeout_seconds: float = 30.0
    maximum_timeout_seconds: float = 120.0
    session_idle_timeout_seconds: float = 1800.0

    @classmethod
    def from_env(cls) -> "McpTransportSettings":
        settings = cls(
            maximum_body_bytes=int(os.getenv("WRIGHT_MCP_MAX_BODY_BYTES", "1048576")),
            maximum_concurrency=int(os.getenv("WRIGHT_MCP_MAX_CONCURRENCY", "16")),
            requests_per_minute=int(os.getenv("WRIGHT_MCP_REQUESTS_PER_MINUTE", "120")),
            operation_timeout_seconds=float(os.getenv("WRIGHT_MCP_TIMEOUT", "30")),
            maximum_timeout_seconds=float(os.getenv("WRIGHT_MCP_MAX_TIMEOUT", "120")),
            session_idle_timeout_seconds=float(
                os.getenv("WRIGHT_MCP_SESSION_IDLE_TIMEOUT", "1800")
            ),
        )
        if (
            min(
                settings.maximum_body_bytes,
                settings.maximum_concurrency,
                settings.requests_per_minute,
            )
            <= 0
        ):
            raise RuntimeError(
                "MCP body, concurrency, and rate limits must be positive"
            )
        if (
            not 0
            < settings.operation_timeout_seconds
            <= settings.maximum_timeout_seconds
        ):
            raise RuntimeError("MCP operation timeout must not exceed its maximum")
        if settings.session_idle_timeout_seconds <= 0:
            raise RuntimeError("MCP session idle timeout must be positive")
        return settings


# Dynamically resolve and set default OPENSCAD_PATH for headless execution
API_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(API_DIR)))
DEFAULT_OPENSCAD_HEADLESS_PATH = os.path.join(
    WORKSPACE_ROOT, "scripts", "openscad-headless.sh"
)

if "OPENSCAD_PATH" not in os.environ:
    os.environ["OPENSCAD_PATH"] = DEFAULT_OPENSCAD_HEADLESS_PATH

# Reload trigger to pick up core package modifications
# Reload trigger version 3
