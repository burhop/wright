# Environment Variables Reference

Wright reads environment variables at startup to adjust network connections, API tokens, model names, and system parameters.

---

## 1. Core LLM Configuration

These variables decouple the agent adapters from static API calls.

| Variable Name | Required | Default | Description |
| :--- | :--- | :--- | :--- |
| `LLM_API_URL` | **Yes** | None | Base URL path for chat completions API (e.g. `https://api.openai.com/v1` or `http://localhost:11434/v1`). |
| `LLM_API_KEY` | No | None | Authentication token required by LLM providers. |
| `LLM_API_MODEL` | No | `gemini-3.5-flash` | Default model identifier dispatched for natural language inference. |

---

## 2. API Gateway Server Settings

Configure host binding ports and security parameters for the FastAPI service.

| Variable Name | Required | Default | Description |
| :--- | :--- | :--- | :--- |
| `WRIGHT_API_HOST` | No | `127.0.0.1` | Binding address for gateway. |
| `WRIGHT_API_PORT` | No | `8000` | Target port number. |
| `JWT_SECRET_KEY` | No | None | Signing secret used to authenticate API user access tokens. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `1440` | Duration token is valid before expiration. |

---

## 3. Tool registry config

Variables that direct the MCP execution pathways.

| Variable Name | Required | Default | Description |
| :--- | :--- | :--- | :--- |
| `WRIGHT_WORKSPACE_PATH` | No | `/home/agent/workspace` | Base directory on disk where workspaces reside. |
| `RHINO_MCP_ALLOW_REMOTE` | No | `0` | If set to `1`, allows RhinoMCP socket connection to bind to non-loopback addresses. |
