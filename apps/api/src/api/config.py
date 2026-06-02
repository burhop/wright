import os

# Hermes WebUI port and base URL configuration for the 'wright' profile
HERMES_WEBUI_PORT = int(os.getenv("HERMES_WEBUI_PORT", "8788"))
HERMES_WEBUI_BASE_URL = os.getenv("HERMES_WEBUI_BASE_URL", f"http://127.0.0.1:{HERMES_WEBUI_PORT}")

# LLM inference host and health check endpoint
LLM_HEALTH_URL = os.getenv("LLM_HEALTH_URL", "http://promaxgb10-5c88:8000/health")
