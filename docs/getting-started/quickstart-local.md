# Quick Start: PC Local Setup

Use this path when you want to run Wright directly on a normal Windows, macOS,
or Linux development PC instead of using Docker. It is the best path for editing
the FastAPI API, React UI, Hermes plugin, or MCP catalog locally.

Wright is alpha software and bring-your-own-AI. A local checkout does not bundle
an LLM, model weights, hosted provider account, API key, or paid engineering
backend. Configure an OpenAI-compatible endpoint yourself with `LLM_API_URL`,
`LLM_API_KEY`, and `LLM_API_MODEL`.

MCP-specific host software is also selected-server work. Do not install FreeCAD,
OpenSCAD, CalculiX, Blender, vendor CAD systems, license managers, or hardware
drivers globally just to make the catalog look green. Install only the host
dependency required by the MCP server you are validating, following the
[MCP server testing process](../mcp-catalog/mcp-server-testing-process.md).

## Prerequisites

- Python 3.11 or newer.
- `uv` for Python workspace management.
- Node.js 22 or newer with npm.
- Git.
- A reachable OpenAI-compatible LLM endpoint if you want inference checks to be
  connected.

Install `uv` if needed:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

On Windows, use the official `uv` PowerShell install command from Astral's
installer docs, then open a new terminal so `uv` is on `PATH`.

## Sync Dependencies

From the repository root:

```bash
uv sync --all-packages --all-groups
npm ci
```

## Configure Your LLM

Set environment variables in the terminal that will launch Wright, or place them
in your normal shell/profile manager:

```bash
export LLM_API_URL=http://127.0.0.1:8001/v1
export LLM_API_KEY=not-needed
export LLM_API_MODEL=local-model-name
```

Hosted OpenAI-compatible provider example:

```bash
export LLM_API_URL=https://api.openai.com/v1
export LLM_API_KEY=provider-token
export LLM_API_MODEL=gpt-4.1-mini
```

PowerShell example:

```powershell
$env:LLM_API_URL = "http://127.0.0.1:8001/v1"
$env:LLM_API_KEY = "not-needed"
$env:LLM_API_MODEL = "local-model-name"
```

## Run the API

Start the FastAPI gateway from the repository root:

```bash
uv run uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload
```

Open the API docs:

```text
http://127.0.0.1:8000/docs
```

Check health:

```bash
curl http://127.0.0.1:8000/api/health
curl http://127.0.0.1:8000/api/agent/health
curl http://127.0.0.1:8000/api/inference/health
```

The inference check reports `disconnected` until the configured LLM endpoint is
reachable from the PC.

## Run the Web UI

In a second terminal:

```bash
npm run dev --workspace=apps/web -- --host 127.0.0.1
```

Open:

```text
http://127.0.0.1:5173/
```

## Run Focused Verification

Use the same commands CI relies on for this alpha slice:

```bash
uv run pytest
npm run test --workspace=apps/web
npm run build --workspace=apps/web
uv run --with mkdocs-material mkdocs build --strict
```

For a smaller docs-only check while editing getting-started pages:

```bash
uv run pytest tests/test_getting_started_paths.py
```

## Hermes on the Same PC

If you use Hermes Desktop or Hermes CLI on the same machine, keep its API server
enabled and reachable. Wright reads Hermes settings from the Hermes environment
file when possible, and `HERMES_API_BASE_URL` remains the explicit override for
non-standard deployments.

For the plugin-first path, use [Existing Hermes Plugin](hermes-plugin.md). For
Windows Desktop-specific load paths and gateway setup, use
[Wright with Hermes Desktop](../hermes-desktop-wright.md).
