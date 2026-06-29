# Docker Deployment and Filesystem Map

Wright's public-alpha Docker appliance is a local-first way to run the Wright
API, static web UI, Hermes profile/bootstrap, and general validation tooling in
one container. It is intended for testing, MCP porting, demos, and early
developer feedback.

The appliance is bring-your-own-AI. It does not bundle an LLM, API key, local
model, hosted model, or paid engineering backend. Configure `LLM_API_URL`,
`LLM_API_KEY`, and `LLM_API_MODEL` in `docker/.env` for a local or hosted
OpenAI-compatible endpoint.

The base image also does not include MCP-specific host software. FreeCAD,
OpenSCAD, CalculiX, Blender, vendor CAD systems, license managers, GPU drivers,
and hardware interfaces are installed only for the selected MCP server being
validated or used. For catalog validation, follow
`docs/mcp-catalog/mcp-server-testing-process.md` and do not add MCP-specific
host software to the base image just to make catalog validation pass.

## Compose Entry Points

| Purpose | Command | Host URL | Notes |
| --- | --- | --- | --- |
| Minimal alpha appliance | `docker compose -f docker-compose.minimal.yml up -d --build` | `http://localhost:8080` | Recommended first run. |
| Full local stack | `docker compose up -d --build` | `http://localhost:8000` | Adds Jaeger tracing. |
| Test/dev stack | `docker compose -f docker-compose.test.yml up -d --build` | `http://localhost:8080` | Bind-mounts source for iteration. |

The minimal compose file maps `127.0.0.1:8080:8000`, keeping the service bound
to localhost by default. The Hermes gateway port remains internal to the
container unless you deliberately create a local override.

## LLM Connectivity

Copy the environment template:

```bash
cp docker/.env.example docker/.env
```

Hosted provider example:

```env
LLM_API_URL=https://api.openai.com/v1
LLM_API_KEY=sk-your-key
LLM_API_MODEL=gpt-4.1-mini
```

Local model server example:

```env
LLM_API_URL=http://host.docker.internal:8000/v1
LLM_API_KEY=not-needed
LLM_API_MODEL=local-model-name
```

On Linux, `host.docker.internal` may require a local compose override with an
`extra_hosts` entry:

```yaml
services:
  agent:
    extra_hosts:
      - "host.docker.internal:host-gateway"
```

The Wright UI may show setup-pending or degraded LLM status until the endpoint
is reachable from inside the container.

## Persistent Filesystem

Docker images are read-only layer stacks with a writable container overlay.
Anything written only to the overlay disappears when the container is recreated.
Wright uses named volumes for paths that should survive restart or image
replacement.

| Volume | Container path | Purpose |
| --- | --- | --- |
| `wright_home` | `/home/` | Workspaces, Hermes state, sessions, and user configuration. |
| `wright_local` | `/usr/local/` | Selected tool installs and command-line utilities. |
| `wright_opt` | `/opt/` | Self-contained runtimes and larger selected toolchains. |
| `wright_varlib` | `/var/lib/` | SQLite databases and application state. |
| `wright_varcache` | `/var/cache/` | Package and runtime caches. |
| `wright_etc` | `/etc/` | Configuration that must persist across container recreation. |
| `wright_logs` | `/var/log/` | Supervisor, gateway, and application logs. |

Prefer `/home`, `/usr/local`, or `/opt` for selected MCP setup work that needs
to persist. Avoid relying on ad hoc changes under `/usr/bin`, `/usr/lib`, `/bin`,
or `/lib`; those paths are image-owned and should be treated as disposable.

## Selected MCP Dependencies

When validating or using an engineering MCP server:

1. Start from a clean Wright container.
2. Read the selected server's catalog metadata.
3. Install only that server's package and the free/open host dependencies needed
   for a safe probe.
4. Skip proprietary, unsafe, license-bound, credential-bound, or hardware-bound
   dependencies unless the operator has explicitly provided them.
5. Run `initialize`, `notifications/initialized`, `tools/list`, and at least one
   safe backend-touching probe before marking the server fully tested.
6. Record reusable setup steps in
   `docs/mcp-catalog/mcp-server-setup-recipes.md` and chronological failures in
   `docs/mcp-catalog/testing-problem-log.md`.

## LAN Access

Checked-in compose files bind to localhost. For a trusted LAN demo, create an
uncommitted override such as:

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

Use TLS and authentication for anything beyond a private demo network.

## Cleanup

Stop the minimal appliance while preserving named volumes:

```bash
docker compose -f docker-compose.minimal.yml down
```

Remove the minimal appliance and its named volumes:

```bash
docker compose -f docker-compose.minimal.yml down -v
```

Remove a locally built image when you no longer need it:

```bash
docker image rm wright-agent:latest
```
