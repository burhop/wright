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
