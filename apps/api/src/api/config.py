import os

# Hermes WebUI port and base URL configuration for the 'wright' profile
HERMES_WEBUI_PORT = int(os.getenv("HERMES_WEBUI_PORT", "8788"))
HERMES_WEBUI_BASE_URL = os.getenv("HERMES_WEBUI_BASE_URL", f"http://127.0.0.1:{HERMES_WEBUI_PORT}")

# LLM inference host and health check endpoint
LLM_HEALTH_URL = os.getenv("LLM_HEALTH_URL", "http://promaxgb10-5c88:8000/health")

# Local SQLite database path for state and config persistence
DATABASE_PATH = os.getenv("DATABASE_PATH", os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "state.db"))

# Dynamically resolve and set default OPENSCAD_PATH for headless execution
API_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(API_DIR)))
DEFAULT_OPENSCAD_HEADLESS_PATH = os.path.join(WORKSPACE_ROOT, "scripts", "openscad-headless.sh")

if "OPENSCAD_PATH" not in os.environ:
    os.environ["OPENSCAD_PATH"] = DEFAULT_OPENSCAD_HEADLESS_PATH

