# Quick Start: Docker Appliance

Wright's Docker appliance is the fastest public-alpha path for trying the API,
web UI, Hermes integration, and engineering MCP catalog from a clean container.
It is intended for testing, MCP porting, demos, and early developer feedback.

Wright is bring-your-own-AI. The image does not bundle an LLM, model weights, API
key, hosted provider, or paid engineering backend. Configure an
OpenAI-compatible endpoint with `LLM_API_URL`, `LLM_API_KEY`, and
`LLM_API_MODEL`.

The base image also does not bundle MCP-specific host software such as FreeCAD,
OpenSCAD, CalculiX, Blender, vendor CAD systems, license managers, or hardware
drivers. Install and validate those only for the selected MCP server, following
the clean-container process in
[MCP server testing process](../mcp-catalog/mcp-server-testing-process.md).

For deeper Hermes setup and provider configuration, see the official
[Hermes Agent docs](https://hermes-agent.nousresearch.com/docs/) and
[Hermes Desktop docs](https://hermes-agent.nousresearch.com/docs/user-guide/desktop).


## Published Image Path

For tagged alpha releases, Docker Hub and GHCR images use:

```text
burhop/wright:<tag>
ghcr.io/burhop/wright:<tag>
```

Run a published image with your env file:

```bash
docker run --rm -p 127.0.0.1:8080:8000 --env-file docker/.env burhop/wright:<tag>
```

Use the source-build Compose commands below when developing locally or when a
published release image is not available yet.

## Choose a Compose File

| Path | Command | Host URL | Notes |
| --- | --- | --- | --- |
| Minimal alpha appliance | `docker compose -f docker-compose.minimal.yml up -d --build` | `http://localhost:8080` | Recommended first run; Wright only. |
| Full local stack | `docker compose up -d --build` | `http://localhost:8000` | Adds Jaeger tracing on localhost. |
| Test/dev stack | `docker compose -f docker-compose.test.yml up -d --build` | `http://localhost:8080` | Bind-mounts source for iteration. |

All checked-in compose files bind host ports to `127.0.0.1` by default. That is
the safe local-first setting.

## Configure Your LLM

Copy the template:

```bash
cp docker/.env.example docker/.env
```

Generate a unique Wright control-plane token and replace the placeholder in
`docker/.env`:

```bash
openssl rand -hex 32
```

Set the values for your provider:

```env
LLM_API_URL=https://api.openai.com/v1
LLM_API_KEY=sk-your-key
LLM_API_MODEL=gpt-4.1-mini
UI_THEME=dark
WRIGHT_AUTH_MODE=enforced
WRIGHT_API_TOKEN=<generated-value>
```

Local OpenAI-compatible server example:

```env
LLM_API_URL=http://host.docker.internal:8000/v1
LLM_API_KEY=not-needed
LLM_API_MODEL=local-model-name
```

On Linux, `host.docker.internal` may require:

```bash
docker run --add-host=host.docker.internal:host-gateway ...
```

or a compose `extra_hosts` entry if you create a local override file.

Hosted API style example:

```env
LLM_API_URL=https://your-provider.example.com/v1
LLM_API_KEY=provider-token
LLM_API_MODEL=provider-model-id
```

## Run the Appliance

Recommended first run:

```bash
docker compose -f docker-compose.minimal.yml up -d --build
```

Open:

```text
http://localhost:8080
```

Check API health:

```bash
curl http://localhost:8080/api/health
```

Health is public. Other API routes require the token:

```bash
curl -H "Authorization: Bearer ${WRIGHT_API_TOKEN}" \
  http://localhost:8080/api/settings
```

See [Local control-plane security](../security/control-plane.md) for browser
session cookies, origin configuration, remote binding, and compatibility
rollback.

Check Hermes connection state through Wright:

```bash
curl http://localhost:8080/api/agent/health
```

The LLM status may be degraded until your configured endpoint is reachable from
inside the container.

## LAN Access

The committed compose files bind to localhost. For LAN demos, create a local
override file that is not committed:

```yaml
services:
  agent:
    ports:
      - "0.0.0.0:8080:8000"
```

Then run:

```bash
docker compose -f docker-compose.minimal.yml -f docker-compose.lan.yml up -d --build
```

Only expose Wright on trusted networks. Put it behind a reverse proxy with TLS
and authentication for anything beyond a private demo network.

## Persistent Data

The compose files use named volumes for:

- `/home`: workspaces, `.hermes`, sessions, and user configuration.
- `/usr/local` and `/opt`: selected tool installs and self-contained runtimes.
- `/var/lib`: SQLite and application state.
- `/var/log`: startup, supervisor, and application logs.

Use `docker compose down` to stop containers while keeping data. Use
`docker compose down -v` only when you want to delete the named volumes.

## GB10, DGX Spark, and GPU Notes

The current public-alpha appliance is documented as a Linux container path, with
`linux/amd64` as the CI-smoked build target. `linux/arm64`, CUDA-enabled local
AI workstations, NVIDIA Container Toolkit, and `--gpus all` are alpha follow-up
work until the release workflow builds and smokes those variants.

If you run an LLM on the host GPU, keep the model server outside the Wright
container and point `LLM_API_URL` at it. If a selected MCP server needs GPU
passthrough, validate that server in a clean container and record the exact
driver/toolkit assumptions in the MCP setup recipe.

## MCP Validation Smoke

Use the catalog validation process for selected servers:

1. Start from a clean Wright container.
2. Read the selected MCP metadata and blocked/dependency status.
3. Install only the selected server's package and testable free/open host
   dependencies.
4. Do not add unsafe, proprietary, license-bound, hardware-bound, or
   credential-bound software to the base image just to make validation pass.
5. Run `initialize`, `notifications/initialized`, `tools/list`, and one safe
   backend-touching probe before marking a server fully tested.

Problem logs belong in `docs/mcp-catalog/testing-problem-log.md`; reusable setup
recipes belong in `docs/mcp-catalog/mcp-server-setup-recipes.md`.

## Cleanup

Stop the minimal appliance:

```bash
docker compose -f docker-compose.minimal.yml down
```

Remove the appliance and its named volumes:

```bash
docker compose -f docker-compose.minimal.yml down -v
```

Remove the built local image when you no longer need it:

```bash
docker image rm wright:latest
```
