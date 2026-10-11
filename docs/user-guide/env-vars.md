# Environment Variables Reference

Wright reads environment variables at startup to adjust network connections, API tokens, model names, and system parameters.

---

## 1. Core LLM Configuration

These variables decouple the agent adapters from static API calls.

| Variable Name | Required | Default | Description |
| :--- | :--- | :--- | :--- |
| `LLM_API_URL` | For an OpenAI-compatible endpoint | None | Base URL for chat completions (e.g. `https://api.openai.com/v1`). Docker can instead use Model Setup, `WRIGHT_LLM_PROVIDER` or `WRIGHT_LLM_CONFIG_FILE`; an endpoint URL alone does not qualify model routing. |
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
| `API_SERVER_KEY` | No | Resolved from the running gateway; generated for Docker when neither key is supplied | Bearer key used by Wright to authenticate to the Hermes API server. Docker generates a unique key rather than using a shared development credential. |
| `HERMES_API_KEY` | No | Falls back to `API_SERVER_KEY` | Compatibility alias for the Hermes API server key in container bootstrap. |
| `WRIGHT_WORKFLOW_MODEL_TRANSPORT` | No | `hermes-http` on source/native hosts; `hermes-model-sdk` in Docker | Explicit text/tool-decision transport. SDK mode reuses the installed resolver/client and verifies the frozen provider, model, profile and SDK identity before submission. It does not execute tools or fall back to HTTP after failure. Existing HTTP runs retain their route; an unavailable or changed route holds readiness/continuation. |
| `HERMES_ROLE_PYTHON` | For an explicitly installed SDK | Official native installation discovery; `/opt/hermes/.venv/bin/python` in Docker | Trusted installed Hermes Python used by the confined worker. Configure together with its runtime root. |
| `HERMES_ROLE_RUNTIME_ROOT` | With an explicit SDK Python | Official native installation discovery; `/opt/hermes/.venv/lib/python3.13/site-packages` in Docker | Trusted Hermes package root containing the qualified resolver/client. This is installation configuration, never a workflow-supplied executable/path. |

SDK model discovery reports the configured model resolved by Hermes. It does not
advertise an inferred catalog or support remote model switching; use Model Setup
before starting a new run. Resolver qualification establishes the selected route,
not provider reachability, model quality or engineering acceptance. Invalid
credentials or unavailable inference produce a bounded execution diagnostic.

The confined SDK worker resolves `WRIGHT_HERMES_PROFILE`, then `HERMES_PROFILE`,
defaulting to `wright`, through the installed Hermes profile resolver. It loads
that profile's credentials through Hermes's environment loader before resolving
the model. It does not read a workspace/project dotenv, change the parent service's
environment or substitute root defaults for a missing named profile. The profile
and loader implementation are included in the frozen routing qualification.

---

## 3. API Gateway Server Settings

Configure host binding ports and security parameters for the FastAPI service.

| Variable Name | Required | Default | Description |
| :--- | :--- | :--- | :--- |
| `WRIGHT_API_HOST` | No | `127.0.0.1` | Binding address for gateway. |
| `WRIGHT_API_PORT` | No | `8000` | Target port number. |
| `PUBLIC_BASE_URL` | No | None | Public URL to advertise in docs, redirects, or reverse-proxy deployments when a local default is not enough. |
| `WRIGHT_ALLOWED_ORIGINS` | No | `http://127.0.0.1:5173,http://localhost:5173` | Exact browser origins allowed by control-plane authentication and CORS. Include the actual scheme, host and published port when serving the packaged UI. Docker's example env file includes ports 8000 and 8080; add the exact origin if you choose another port. Wildcards are rejected. |
| `WRIGHT_API_TOKEN` | When authentication is enforced | Managed for native; required for Docker | Opaque control-plane bearer credential; browser sessions are derived from it. Native lifecycle manages this value; Docker requires a unique installation value from the operator. |
| `WRIGHT_AUTH_MODE` | No | `enforced` | Require local bearer or browser-session authentication. The `compat` mode is restricted by the local bind/origin policy; tests default to `compat`. |

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
| `WRIGHT_WORKSPACES_DIR` | No | `/home/agent/workspace` | Base directory on disk where workspaces reside. |
| `WRIGHT_WORKSPACE_PATH` | No | value of `WRIGHT_WORKSPACES_DIR` | Backward-compatible alias for the workspace directory. |
| `RHINO_MCP_ALLOW_REMOTE` | No | `0` | If set to `1`, allows RhinoMCP socket connection to bind to non-loopback addresses. |

MCP-specific host software, credentials, license managers, and hardware drivers
are intentionally configured per selected MCP server. Do not add them to the base
Docker image just to make catalog validation pass.
