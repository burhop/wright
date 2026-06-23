import os

# Hermes Native API port and base URL configuration for the 'wright' profile
HERMES_API_PORT = int(os.getenv("HERMES_API_PORT", "8642"))
HERMES_API_BASE_URL = os.getenv(
    "HERMES_API_BASE_URL", f"http://127.0.0.1:{HERMES_API_PORT}"
)
HERMES_API_KEY = os.getenv("HERMES_API_KEY", "wright-dev-key")


# LLM inference host and health check endpoint
LLM_HEALTH_URL = os.getenv("LLM_HEALTH_URL", "http://promaxgb10-5c88:8000/health")


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
    return os.getenv("LLM_HEALTH_URL", "http://promaxgb10-5c88:8000/health")


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
    health_url = os.getenv("LLM_HEALTH_URL", "http://promaxgb10-5c88:8000/health")
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
