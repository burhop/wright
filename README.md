# wright

> A digital engineer, designer, and mechanical analyst — powered by local-first multi-agent AI.

Wright is a modular, offline-capable mechanical engineering API appliance that runs
on a Dell GB10 (NVIDIA DGX Spark) with 128 GB unified memory. It orchestrates
multiple LLM agents to perform parametric CAD generation, finite element analysis,
and manufacturing pipeline automation — all without requiring cloud connectivity.

## Architecture

```
wright/
├── apps/
│   ├── api/                    # FastAPI — zero business logic, routing only
│   └── web/                    # Frontend UI (atomic design)
├── packages/
│   ├── core/                   # Shared domain models, structured JSON logging
│   ├── agent_adapters/         # Adapter pattern for LLM agents (Hermes, openclaw, PI)
│   ├── tool_registry/          # BaseTool pattern with online/offline fallback
│   └── data_vault/             # SQLite (WAL) + LanceDB (Arrow) + filesystem vault
├── tests/
│   ├── ui-integration/         # Tier 2 — Playwright integration tests
│   └── e2e/                    # Tier 3 — system smoke tests
├── docker/                     # Thick base / thin code Docker strategy
├── docs/                       # Architecture specs and documentation
└── .specify/                   # Spec-kit (Spec-Driven Development) config
```

See [docs/virtual_engineer_architecture.pdf](docs/virtual_engineer_architecture.pdf) for
the full architecture specification and [constitution.md](constitution.md) for project
governance.

## Quick Start

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (package manager)
- [Docker](https://docs.docker.com/engine/install/) (optional, for containerized dev)
- [Antigravity CLI](https://antigravity.google/) (for AI-assisted development)

### Setup

```bash
# Clone
git clone https://github.com/burhop/wright.git
cd wright

# Install dependencies via uv workspace
uv sync

# Run the API (development)
uv run uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload

# Or via Docker
docker compose up
```

### Spec-Kit (Spec-Driven Development)

This project uses [spec-kit](https://github.com/github/spec-kit) with the
Antigravity (`agy`) integration. Available skills:

| Skill | Purpose |
|---|---|
| `$speckit-constitution` | Establish project principles |
| `$speckit-specify` | Define what to build |
| `$speckit-plan` | Create implementation plans |
| `$speckit-tasks` | Generate actionable task lists |
| `$speckit-implement` | Execute implementation |
| `$speckit-clarify` | Clarify ambiguous areas |
| `$speckit-analyze` | Cross-artifact consistency check |

## Docker Production Deployment

Wright provides a production-ready Docker image that packages the entire stack into a single deployable container:

| Component | Version | Purpose |
|-----------|---------|---------|
| Wright API | — | FastAPI backend on port 8000 (external) |
| Wright Web | — | Vite frontend served as static files |
| Hermes Agent | 0.15.2 | AI agent framework (PyPI) |
| Hermes WebUI | 0.51.135 | Agent session manager on port 8788 (internal) |
| OpenSCAD + Xvfb | — | Headless CAD for MCP geometry tools |
| supervisord | — | Process manager (keeps both services running) |

### Quick Start

```bash
# 1. Configure your LLM endpoint
cp docker/.env.example docker/.env
# Edit docker/.env — set LLM_API_URL, LLM_API_KEY, LLM_API_MODEL

# 2. Build and run
make docker-build
docker compose up
# Open http://localhost:8080
```

### Makefile Targets

| Target | Description |
|--------|-------------|
| `make docker-build` | Build the production Docker image |
| `make docker-test` | Start in test/dev mode with bind mounts for live iteration |
| `make docker-clean` | Tear down test containers and delete volumes |
| `make docker-logs` | Follow logs from the running containers |
| `make docker-shell` | Open an interactive shell as the `agent` user |
| `make docker-test-e2e` | Run Playwright UI tests against the built image |

### Process Management

The container runs [supervisord](docker/supervisord.conf) to manage two services:
- **wright-api** — FastAPI + uvicorn on `0.0.0.0:8000`
- **hermes-webui** — Agent session API on `127.0.0.1:8788` (internal only, proxied by Wright API)

Both auto-restart on crash. Check status with:
```bash
make docker-shell
supervisorctl -c /etc/supervisor/conf.d/wright.conf status
```

### First Boot

On first start, [entrypoint.sh](docker/entrypoint.sh) automatically:
1. Creates the Hermes `wright` profile at `~/.hermes/`
2. Generates `config.yaml` from `LLM_API_URL`, `LLM_API_KEY`, `LLM_API_MODEL` env vars
3. Starts supervisord (which launches both services)

Subsequent boots reuse the existing profile (updates LLM config if env vars changed).

### CI/CD

The [GitHub Actions workflow](.github/workflows/docker-build.yml) runs on every push to `main`/`dev`:
1. **Build** — Multi-stage Docker build with GitHub Actions cache
2. **Smoke Test** — Starts the container and verifies:
   - Wright API health endpoint responds
   - Hermes Agent proxy is connected
   - Workspace creation works
   - Both supervisord processes are running
3. **Push** — Tags and pushes to Docker Hub (`latest` on main, `dev` on dev)

### Persistence & Backups

The container uses a 7-volume model to persist all mutable state across restarts.
See [scripts/backup-volumes.sh](scripts/backup-volumes.sh) and [scripts/restore-volume.sh](scripts/restore-volume.sh).

### Agent Awareness
The image contains a read-only manifest at [/container-manifest.md](docker/container-manifest.md) specifying persistent and ephemeral directories, allowing agents to self-adjust tool installation behaviors to prevent data loss.

## Governance

All development is governed by [constitution.md](constitution.md) (v1.0.0).
Key mandates:

- **Offline-first**: The entire appliance runs fully air-gapped
- **Zero-server databases**: SQLite + LanceDB only — no PostgreSQL/Qdrant
- **Agent abstraction**: LLM agents integrated via Adapter Pattern, never hardcoded
- **Branch discipline**: Feature branches only — no direct commits to `main`
- **Phase isolation**: Planning artifacts approved before implementation code is generated

## License

See [LICENSE](LICENSE) for details.
