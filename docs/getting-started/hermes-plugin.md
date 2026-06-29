# Quick Start: Existing Hermes Plugin

Use this path when you already run Hermes Desktop or Hermes CLI and want Wright
as a Hermes slash-command plugin. This is the most direct route for Hermes users
who want `/wright start`, `/wright status`, and the engineering MCP catalog
without learning Docker first.

Wright is alpha software and bring-your-own-AI. The plugin does not bundle an
LLM, model weights, provider credentials, paid engineering tools, or
MCP-specific host software. Configure your Hermes model provider and Wright's
`LLM_API_URL`, `LLM_API_KEY`, and `LLM_API_MODEL` values for the endpoint you
want to use.

## Prerequisites

- Hermes Desktop or Hermes CLI installed.
- Wright available on disk.
- `uv`, Python 3.11 or newer, Node.js 22 or newer, and npm available to the user
  running Hermes.
- Hermes API server enabled when you want Wright to show a connected Hermes
  status.

## Install the Plugin

From the Wright repository root, install the Hermes Agent CLI with the local
Wright plugin package:

```bash
uv tool install hermes-agent --with ./hermes-plugin-wright/
```

For editable development inside an existing Python environment:

```bash
pip install -e ./hermes-plugin-wright
```

Hermes Desktop may load plugins from application data instead of a profile
plugin folder. For Windows Desktop paths and cache behavior, see
[Wright with Hermes Desktop](../hermes-desktop-wright.md).

## Enable the Hermes API Server

Use Hermes' normal configuration path, or set these environment values for the
same user that runs Hermes:

```bash
export API_SERVER_ENABLED=true
export API_SERVER_HOST=127.0.0.1
export API_SERVER_PORT=8642
export API_SERVER_KEY=wright-local-dev
```

PowerShell:

```powershell
setx API_SERVER_ENABLED true
setx API_SERVER_HOST 127.0.0.1
setx API_SERVER_PORT 8642
setx API_SERVER_KEY wright-local-dev
```

Wright resolves Hermes through Hermes' own env file when possible. Use
`HERMES_API_BASE_URL` only for non-standard deployments:

```bash
export HERMES_API_BASE_URL=http://127.0.0.1:8642
export HERMES_API_KEY=wright-local-dev
```

Start the gateway if it is not already running:

```bash
hermes gateway run
```

## Configure Wright's LLM Status

Set Wright's inference endpoint separately from the Hermes API server:

```bash
export LLM_API_URL=http://127.0.0.1:8001/v1
export LLM_API_KEY=not-needed
export LLM_API_MODEL=local-model-name
```

The Wright UI may still open if inference is disconnected, but the LLM status
light will remain red until that endpoint is reachable.

## Run Wright from Hermes

In Hermes:

```text
/wright start
/wright status
/wright catalog cad
```

The `/wright start` command builds the web assets, starts the FastAPI server with
`uv run uvicorn`, and opens the Wright UI. `/wright status` checks the Wright API,
workspace, Hermes connection, and active MCP tool status.

Useful direct checks:

```bash
curl http://127.0.0.1:8000/api/health
curl http://127.0.0.1:8000/api/agent/health
curl http://127.0.0.1:8000/api/inference/health
```

## Selected MCP Tools

Use `/wright catalog`, `/wright info <id>`, and `/wright install <id>` to inspect
and register MCP servers. Install selected MCP host dependencies only when the
catalog entry says they are required and you are validating that server.

Do not add MCP-specific host software to the base Docker image or a shared
workstation image just to make the catalog look complete. Record validation
results and setup recipes under `docs/mcp-catalog/`.
