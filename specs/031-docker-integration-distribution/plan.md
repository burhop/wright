# Implementation Plan: Docker Integration & Distribution Packaging

**Branch**: `031-docker-integration-distribution` | **Date**: 2026-06-22 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/031-docker-integration-distribution/spec.md`

## Summary

This feature adds Docker integration and PyPI packaging support for `hermes-plugin-wright`. 
1. **Docker Integration**: Updates `docker/Dockerfile` to copy and install the plugin into the `hermes-agent` isolated environment using `uv tool install --with`. Configures uvicorn checking to prevent manual process spawning inside Docker if the API server is already healthy, degrading to supervisor warnings if uvicorn is unhealthy.
2. **Local Install & Entry Points**: Defines standard python packaging parameters inside `pyproject.toml` so that the entry point `wright = "hermes_plugin_wright:register"` is discoverable.
3. **Context Integration**: Cleans up the `__init__.py` plugin registry script to register commands and load the catalog, delegating `.hermes.md` files and gateway config setup to `hermes_sync.py`.
4. **Documentation**: Creates a complete `README.md` document covering user commands, local pip setup, and Docker container packaging.

## Technical Context

**Language/Version**: Python >= 3.11

**Primary Dependencies**: `httpx`, `pyyaml`, `pydantic`, `structlog`

**Storage**: Local files (config, PID, logs, `.hermes.md`)

**Testing**: `pytest`, `pytest-asyncio` using `unittest.mock`

**Target Platform**: Linux (Docker appliance and local development)

**Project Type**: Python Package / Hermes Agent Plugin

**Performance Goals**: Sub-second start/check times when running inside Docker.

**Constraints**: No duplicate uvicorn background processes running in Docker containers.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Modular Monorepo Boundaries**: The plugin codebase is structured as an isolated python package `hermes-plugin-wright` and acts as an interface caller to the main API package. (Pass)
- **Container Strategy**: The plugin is copied and injected during Docker image build, running seamlessly alongside uvicorn under supervisor control. (Pass)
- **Structured Logging**: Uses `structlog` for command dispatcher tracing logs. (Pass)

## Project Structure

### Documentation (this feature)

```text
specs/031-docker-integration-distribution/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    └── distribution_contracts.md
```

### Source Code (repository root)

```text
hermes-plugin-wright/
├── __init__.py          # Modified: loads catalog, registers commands
├── pyproject.toml       # Modified: package entry points and metadata
├── README.md            # [NEW] Installation and usage instructions
docker/
├── Dockerfile           # Modified: copies and installs plugin in image
```

**Structure Decision**: Modify `docker/Dockerfile`, `hermes-plugin-wright/pyproject.toml`, and `hermes-plugin-wright/__init__.py`. Create `hermes-plugin-wright/README.md`.

## Complexity Tracking

*No violations of Constitution identified.*
