# Research: Agent Docker Container Setup

**Date**: 2026-06-04 | **Feature**: 010-agent-docker-setup

## Research Areas

### 1. Docker Multi-Service Container Strategy

**Decision**: Use a process manager (supervisord or a bash entrypoint launching background processes) to run the Wright API, web frontend, and agent runtime inside a single container.

**Rationale**: The user explicitly chose a full-stack single container (clarification Q3). For a self-contained appliance, this simplifies deployment — one `docker compose up` brings up everything. The entrypoint script will launch uvicorn (API), the Vite-built static frontend (served by the API or a lightweight static server), and agent processes.

**Alternatives considered**:
- Separate containers for API/frontend/agents via docker-compose: More complex orchestration, inter-container networking, multiple images to manage. Rejected per user decision.
- Docker-in-Docker for agents: Unnecessary complexity for this use case.

### 2. Existing Docker Infrastructure

**Decision**: Build on top of the existing `docker/` directory and `docker-compose.yml` rather than replacing them.

**Rationale**: The project already has:
- `docker/Dockerfile.base` — skeleton for future GPU/CUDA heavy image (keep as-is)
- `docker/Dockerfile.dev` — lightweight dev image using Python 3.13-slim + uv (reference for dependency resolution patterns)
- `docker-compose.yml` — defines API service + Jaeger, with live-mount volumes and localhost-only ports
- `.dockerignore` — comprehensive exclusion rules already in place

The new `docker/Dockerfile` should follow the `Dockerfile.dev` patterns (uv for Python deps, `pyproject.toml` copy for layer caching) but extend it with Node.js, the full Wright stack, and the container manifest.

### 3. GitHub Actions Docker Build

**Decision**: Use `docker/build-push-action@v6` with Docker Buildx and GitHub Actions cache for fast CI builds. Push to Docker Hub using repository secrets.

**Rationale**: This is the standard GitHub Actions pattern for Docker builds. Buildx enables multi-platform builds (future aarch64 support for Dell GB10) and efficient layer caching via `type=gha` cache backend.

**Alternatives considered**:
- Plain `docker build` in a `run` step: No caching, slower builds. Rejected.
- Self-hosted runner: Not needed yet — GitHub-hosted runners have Docker pre-installed.

### 4. Volume Strategy Alignment

**Decision**: Extend the existing `docker-compose.yml` volume strategy to match the architecture document's 7-volume model, while preserving the existing live-mount pattern for `apps/` and `packages/`.

**Rationale**: The existing compose file already mounts `./apps`, `./packages`, and `./vault` as bind mounts. The architecture document specifies 7 named volumes for agent persistence. For the production compose, we'll use named volumes. For the test compose (`docker-compose.test.yml`), we'll combine named volumes with bind mounts for code iteration.

### 5. Frontend Serving Strategy

**Decision**: Build the Vite frontend at image build time (`npm run build`) and serve the static output via the FastAPI application using `StaticFiles` middleware, or via a lightweight nginx reverse proxy.

**Rationale**: In production (Docker), the frontend should be pre-built static files served alongside the API, not a running dev server. This is the standard pattern for containerized Vite applications. The dev server (`npm run dev`) is only used during host-based development.

**Alternatives considered**:
- Run `npm run dev` inside the container: Not appropriate for production; creates unnecessary process and dependency overhead.
- Separate nginx container for static files: Adds complexity; rejected since we're doing single-container.

### 6. Entrypoint Process Management

**Decision**: Use a simple bash entrypoint script that launches the API server as the main process, with the frontend served as static files by FastAPI. Agent processes will be started by the API application itself (as they already are in the current architecture via agent adapters).

**Rationale**: Since agents are already launched and managed by the API's agent adapter layer, and the frontend will be served as static files, there's no need for a full process manager like supervisord. The entrypoint just needs to: (1) export the manifest, (2) log the startup, (3) exec uvicorn. This aligns with Docker best practices of one main process per container.

### 7. Backup and Restore Scripts

**Decision**: Implement backup/restore as shell scripts on the host machine following the patterns in the architecture document (Section 6).

**Rationale**: Backups must run on the host to access Docker volumes. The architecture document already provides tested script templates. We'll adapt them to the Wright project's naming conventions.
