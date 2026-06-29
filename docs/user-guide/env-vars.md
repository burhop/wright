# Environment Variables Reference

Wright reads environment variables at startup to adjust network connections, API tokens, model names, and system parameters.

---

## 1. Core LLM Configuration

These variables decouple the agent adapters from static API calls.

| Variable Name | Required | Default | Description |
| :--- | :--- | :--- | :--- |
| `LLM_API_URL` | **Yes** | None | Base URL path for chat completions API (e.g. `https://api.openai.com/v1` or `http://localhost:11434/v1`). |
| `LLM_API_KEY` | No | None | Authentication token required by LLM providers. |
| `LLM_API_MODEL` | No | `default` in the Docker entrypoint | Default model identifier dispatched for natural language inference. |

---

## 2. Hermes Integration

Wright can talk to Hermes through the API server exposed by a Wright-managed
container profile, a local Hermes CLI/Desktop install, or an explicit override.

| Variable Name | Required | Default | Description |
| :--- | :--- | :--- | :--- |
| `HERMES_API_BASE_URL` | No | Auto-detected from Hermes env files when available | Explicit Hermes API base URL override for non-standard deployments. |
| `API_SERVER_HOST` | No | `127.0.0.1` | Host written into the generated Hermes API server config in the Docker entrypoint. |
| `API_SERVER_PORT` | No | `8642` | Hermes API server port written into the generated profile config. |
| `API_SERVER_KEY` | No | `wright-dev-key` | Bearer key used by Wright to authenticate to the Hermes API server. |
| `HERMES_API_KEY` | No | Falls back to `API_SERVER_KEY` | Compatibility alias for the Hermes API server key in container bootstrap. |

---

## 3. API Gateway Server Settings

Configure host binding ports and security parameters for the FastAPI service.

| Variable Name | Required | Default | Description |
| :--- | :--- | :--- | :--- |
| `WRIGHT_API_HOST` | No | `127.0.0.1` | Binding address for gateway. |
| `WRIGHT_API_PORT` | No | `8000` | Target port number. |
| `PUBLIC_BASE_URL` | No | None | Public URL to advertise in docs, redirects, or reverse-proxy deployments when a local default is not enough. |
| `CORS_ALLOWED_ORIGINS` | No | Local development origins | Comma-separated origins allowed to call the API from a browser, if configured by the deployment. |
| `JWT_SECRET_KEY` | No | None | Signing secret used to authenticate API user access tokens. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `1440` | Duration token is valid before expiration. |

---

## 4. Frontend and Theme Settings

| Variable Name | Required | Default | Description |
| :--- | :--- | :--- | :--- |
| `UI_THEME` | No | `dark` | Initial web UI theme. Supported public-alpha values are `dark` and `light`. |
| `FRONTEND_DIST_DIR` | No | `/workspace/apps/web/dist` in Docker | Directory FastAPI serves as the built SPA. |

---

## 5. Tool Registry Config

Variables that direct the MCP execution pathways.

| Variable Name | Required | Default | Description |
| :--- | :--- | :--- | :--- |
| `WRIGHT_WORKSPACE_PATH` | No | `/home/agent/workspace` | Base directory on disk where workspaces reside. |
| `RHINO_MCP_ALLOW_REMOTE` | No | `0` | If set to `1`, allows RhinoMCP socket connection to bind to non-loopback addresses. |

MCP-specific host software, credentials, license managers, and hardware drivers
are intentionally configured per selected MCP server. Do not add them to the base
Docker image just to make catalog validation pass.
