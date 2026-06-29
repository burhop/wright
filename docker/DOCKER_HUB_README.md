# Wright Docker Appliance

Wright is a local-first agent orchestration platform for physical engineering
workflows. This image is public-alpha software for testing, MCP porting, demos,
and early developer feedback.

Wright is bring-your-own-AI. The image does not bundle an LLM, API key, hosted
model, local model weights, or paid engineering backend. Point it at an
OpenAI-compatible endpoint with environment variables.

The base image also does not bundle MCP-specific host software such as FreeCAD,
OpenSCAD, CalculiX, Blender, vendor CAD systems, license managers, or hardware
drivers. Install and validate those only for the selected MCP server.

## Image Names

Public alpha images are intended to be published with matching immutable tags on
both registries:

- `ghcr.io/burhop/wright-agent:<tag>`
- `<dockerhub-username>/wright-agent:<tag>`

Stable tags may also move `latest`. Alpha, beta, and release-candidate tags do
not move `latest`.

## Quick Start

From a source checkout:

```bash
cp docker/.env.example docker/.env
# Edit docker/.env and set LLM_API_URL, LLM_API_KEY, and LLM_API_MODEL.

docker compose -f docker-compose.minimal.yml up -d --build
```

Open:

```text
http://localhost:8080/
```

The full compose stack also starts Jaeger and maps Wright to
`http://localhost:8000/`:

```bash
docker compose up -d --build
```

## Environment Configuration

| Variable | Required | Default | Description |
| :--- | :--- | :--- | :--- |
| `LLM_API_URL` | Yes | None | OpenAI-compatible base endpoint, such as `https://api.openai.com/v1` or a local server URL. |
| `LLM_API_KEY` | No | None | Provider token. Do not paste secrets into bug reports. |
| `LLM_API_MODEL` | No | `default` | Model id passed to the configured provider. |
| `UI_THEME` | No | `dark` | Initial Wright UI theme. |
| `API_SERVER_KEY` | No | `wright-dev-key` | Key for Wright-to-Hermes API server communication inside the container. |

## Ports

| Host mapping | Container port | Purpose |
| :--- | :--- | :--- |
| `8080:8000` in `docker-compose.minimal.yml` | `8000` | Wright FastAPI gateway and web UI. |
| `8000:8000` in `docker-compose.yml` | `8000` | Wright FastAPI gateway and web UI with the full local stack. |
| Internal only | `8642` | Hermes gateway API used by Wright. |

All checked-in compose files bind host ports to `127.0.0.1` by default.

## Volumes

| Volume | Target Path | Purpose |
| :--- | :--- | :--- |
| `wright_home` | `/home/` | Workspaces, `.hermes`, sessions, and user configuration. |
| `wright_local` | `/usr/local/` | Selected tool installs and local binaries. |
| `wright_opt` | `/opt/` | Conda/micromamba and self-contained runtimes. |
| `wright_varlib` | `/var/lib/` | SQLite and system/app state. |
| `wright_varcache` | `/var/cache/` | Package cache. |
| `wright_etc` | `/etc/` | Local system configuration. |
| `wright_logs` | `/var/log/` | Supervisor and application logs. |

Use `docker compose down` to stop the appliance while keeping volumes. Use
`docker compose down -v` only when you want to delete local state.

## Health Checks

```bash
curl http://localhost:8080/api/health
curl http://localhost:8080/api/agent/health
```

For selected MCP server validation, follow
`docs/mcp-catalog/mcp-server-testing-process.md` from the source repository.
