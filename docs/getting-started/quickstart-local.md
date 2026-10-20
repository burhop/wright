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
- Node.js **22.22.2+ within 22.x**, **24.15.0+ within 24.x**, or **26+**, with npm.
  These ranges follow the locked frontend/test dependencies; Node 25 is not
  supported. Select a compatible runtime for this checkout without replacing
  other projects' runtimes. `npm ci --engine-strict` enforces the declared
  engine requirements instead of treating incompatibility as a warning.
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
npm ci --engine-strict
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

`/api/runtime/identity` is a native-manager lifecycle challenge, not a general
health check. Direct Uvicorn launches intentionally return HTTP 503 with
`native_lifecycle_unavailable` there. `WRIGHT_NATIVE_RUNTIME=1` selects local
workspace paths; it does not create lifecycle-manager ownership. Do not invent
a challenge to make that endpoint pass.

### Browser access with enforced authentication

Keep `WRIGHT_AUTH_MODE=enforced` and supply an instance-specific
`WRIGHT_API_TOKEN` to the API process. The browser's **Unlock Wright** field
expects that Wright token, never an AI provider API key. A source launch uses
the token you supplied; it need not print it in its logs. Use your launcher's
private token store, enter it locally, and do not put it in chat or screenshots.

The Windows engineering pilot launcher retains its token at
`state/data/api-token.txt`. In a private PowerShell terminal, copy it without
printing it using `Get-Content -Raw <absolute-token-file> | Set-Clipboard`,
paste into **Access Token**, unlock, then clear the clipboard with
`Set-Clipboard -Value ''`. Keep the file accessible only to your Windows account.
Normal tool, session and settings initialization begins after authentication.

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
uv run --extra runtime --extra engineering-models python -m pytest
npm run test --workspace=apps/web
npm run build --workspace=apps/web
uv run --with mkdocs-material mkdocs build --strict
```

For a smaller docs-only check while editing getting-started pages:

```bash
uv run python -m pytest tests/test_getting_started_paths.py
```

## Hermes on the Same PC

If you use Hermes Desktop or Hermes CLI on the same machine, keep its API server
enabled and reachable. Wright reads Hermes settings from the Hermes environment
file when possible, and `HERMES_API_BASE_URL` remains the explicit override for
non-standard deployments.

For the plugin-first path, use [Existing Hermes Plugin](hermes-plugin.md). For
Windows Desktop-specific load paths and gateway setup, use
[Wright with Hermes Desktop](../hermes-desktop-wright.md).
## Local Program Status

To refresh the read-only `/program-status` page from the current committed
program subject, publish into the API database parent's stable data root:

```powershell
$env:WRIGHT_DATA_ROOT = ".wright-data"
python scripts/publish-engineering-program-status.py --repository . --source HEAD --data-root .wright-data/program-status
```

For automatic refresh after each committed `HEAD` change, keep this local
watcher running (the default poll interval is two seconds):

```powershell
python scripts/publish-engineering-program-status.py --repository . --source HEAD --data-root .wright-data/program-status --watch-committed
```

See [Program status](program-status.md) for identity, fallback, refresh, and
rollback semantics. The publisher observes committed Git evidence only.
