# Feature Specification: Agent Docker Container Setup

**Feature Branch**: `010-agent-docker-setup`

**Created**: 2026-06-04

**Status**: Draft

**Input**: User description: "Set up a Docker system based on the agent-docker-architecture.md document. Build the image as part of the CI/CD process. Do not use the Docker container in development unless explicitly testing and debugging the Docker container. Capture all use cases and user stories for developing the Docker setup."

## Clarifications

### Session 2026-06-04

- Q: Should the Dockerfile use a full CUDA/PyTorch/FreeCAD/CalculiX base image (per constitution §2) or a lean Ubuntu 24.04 image (per architecture doc)? → A: Lean base first (Ubuntu 24.04 + CLI tools). GPU/CUDA layer will be added as a follow-up feature.
- Q: What network access policy should the container enforce (air-gapped, full outbound, or allowlisted)? → A: Full outbound access. Container can reach any external endpoint (LLM API, PyPI, GitHub, apt repos). The offline-first mandate applies to the application's core features, not the container's ability to download dependencies.
- Q: What application components should run inside the Docker container (agents only, full stack, or separate containers)? → A: Full stack. The container runs agents (Hermes, OpenClaw, Pi) AND the Wright API server and web frontend as a single deployable unit.
- Q: Which CI/CD platform should the pipeline target? → A: GitHub Actions with Docker Buildx and layer caching (`.github/workflows/docker-build.yml`).
- Q: Where should CI push the built Docker image? → A: Docker Hub (`docker.io`) as the default registry. GHCR (`ghcr.io`) support will be added as a follow-up.

## User Scenarios & Testing

### User Story 1 — Dockerfile and Compose Build Validation (Priority: P1)

A developer pushes code to the repository. The CI/CD pipeline automatically builds the Docker image from the `Dockerfile`, verifying that all base packages, the agent user, the container manifest, and the entrypoint script are correctly assembled. The developer sees a clear pass/fail result without needing to build locally.

**Why this priority**: If the image cannot build, nothing else in the Docker story works. This is the foundation of the entire containerization effort.

**Independent Test**: Run `docker build -t wright-agent:test .` in CI and verify exit code 0. Verify the entrypoint is executable and the manifest file exists at `/container-manifest.md`.

**Acceptance Scenarios**:

1. **Given** a clean checkout of the repository, **When** a CI pipeline triggers on push/PR, **Then** the Docker image builds successfully with no errors and is tagged with the commit SHA.
2. **Given** a Dockerfile with a syntax error or missing dependency, **When** the CI pipeline runs, **Then** the build fails with a clear error message and the pipeline is marked as failed.
3. **Given** a successful build, **When** the built image is inspected, **Then** it contains: the `agent` user, the container manifest at `/container-manifest.md` (read-only), and the entrypoint script at `/entrypoint.sh`.

---

### User Story 2 — Volume Strategy and Persistence (Priority: P1)

An operator deploys the Docker container using `docker compose up`. Named volumes are correctly mounted to all paths that agents write to (`/home/`, `/usr/local/`, `/opt/`, `/var/lib/`, `/var/cache/`, `/etc/`, `/var/log/`). When the container restarts, all work in volume-mounted paths persists while ephemeral paths (`/bin`, `/usr/bin`, `/usr/lib`, `/tmp`) reset to image state.

**Why this priority**: Volume strategy is the foundation of the entire persistence and recovery model. If volumes are misconfigured, agents lose work silently.

**Independent Test**: Start the container, create a file in `/home/agent/test.txt` and `/usr/bin/test.txt`, restart the container, and verify only the volume-mounted file persists.

**Acceptance Scenarios**:

1. **Given** a running container with all volumes mounted, **When** a file is written to `/home/agent/work.txt`, **Then** the file persists after `docker compose restart`.
2. **Given** a running container, **When** a file is written to `/usr/bin/ephemeral-test`, **Then** the file is gone after `docker compose restart`.
3. **Given** the `docker-compose.yml` defines 7 named volumes, **When** `docker volume ls` is run on the host, **Then** all 7 volumes are listed.

---

### User Story 3 — Environment Variable Injection for LLM API (Priority: P1)

An operator configures the LLM API endpoint, key, and default model via a `.env` file on the host machine. These values are injected at container startup and are never baked into the image. Changing the LLM provider or model requires only editing `.env` and restarting the container.

**Why this priority**: Secrets must never be in the image. The LLM backend must be swappable without rebuilds.

**Independent Test**: Start the container with `LLM_API_URL=https://test.example.com`, exec into the container, and verify `echo $LLM_API_URL` outputs the correct value.

**Acceptance Scenarios**:

1. **Given** a `.env` file with `LLM_API_URL`, `LLM_API_KEY`, and `LLM_API_MODEL`, **When** the container starts, **Then** all three values are available as environment variables inside the container.
2. **Given** the LLM endpoint changes, **When** the operator edits `.env` and runs `docker compose restart`, **Then** agents pick up the new endpoint without rebuilding the image.
3. **Given** the Docker image, **When** inspected with `docker history` or layer analysis, **Then** no API keys or secrets are present in any image layer.

---

### User Story 4 — Container Manifest and Agent Awareness (Priority: P2)

The container includes a read-only manifest file at `/container-manifest.md` that documents the filesystem layout, persistence rules, and behavioral constraints. The entrypoint script exports this manifest into the `CONTAINER_MANIFEST` environment variable so agents can inject it into their system prompts.

**Why this priority**: Agent awareness of what persists and what doesn't is critical to preventing silent data loss and corruption.

**Independent Test**: Start the container and verify `$CONTAINER_MANIFEST` is non-empty and contains the expected sections (filesystem rules, install decision tree, behavioral rules).

**Acceptance Scenarios**:

1. **Given** a running container, **When** `cat /container-manifest.md` is run, **Then** the file is readable and contains filesystem persistence rules.
2. **Given** a running container, **When** `echo $CONTAINER_MANIFEST` is run, **Then** the environment variable contains the full manifest text.
3. **Given** the manifest file inside the container, **When** `ls -la /container-manifest.md` is run, **Then** the file has read-only permissions (444).

---

### User Story 5 — CI/CD Pipeline Docker Build Integration (Priority: P2)

The Docker image is built automatically as part of the CI/CD pipeline on every push to `main` or `dev`. The build produces a tagged image (`wright-agent:<sha>` and `wright-agent:latest`) and caches layers for fast incremental builds. The image is not deployed automatically — it is available for manual pull and deployment.

**Why this priority**: Automated builds ensure the Docker image is always in sync with the codebase, catching Dockerfile regressions early.

**Independent Test**: Push a commit to `dev`, verify the CI job runs, produces a tagged image, and the image passes basic smoke tests (container starts, entrypoint runs, manifest exists).

**Acceptance Scenarios**:

1. **Given** a push to `main` or `dev`, **When** the CI pipeline runs, **Then** a Docker image is built and tagged with `wright-agent:<commit-sha>` and `wright-agent:latest`.
2. **Given** no changes to the Dockerfile or its dependencies, **When** the CI pipeline runs, **Then** Docker layer caching reduces build time to under 2 minutes.
3. **Given** a CI-built image, **When** a smoke test runs `docker run --rm wright-agent:latest /entrypoint.sh echo "ok"`, **Then** the output is `ok` and exit code is 0.

---

### User Story 6 — Backup and Restore Workflow (Priority: P2)

An operator runs a nightly backup script on the host machine that creates timestamped archives of all 7 Docker volumes. When data loss occurs, the operator uses the restore script to recover specific volumes from a backup without affecting other volumes.

**Why this priority**: Backup/restore is the safety net. Agents will inevitably corrupt state, and the recovery path must be proven and rehearsed.

**Independent Test**: Run the backup script, verify all 7 `.tar.gz` archives are created, then restore a single volume and verify data integrity.

**Acceptance Scenarios**:

1. **Given** the backup script and a running container, **When** the backup script runs, **Then** it produces 7 timestamped `.tar.gz` archives under `/backups/agent-volumes/<timestamp>/`.
2. **Given** a backup from a previous day, **When** the restore script is run for a single volume (`agent_home`), **Then** that volume is restored to the backup state while other volumes remain untouched.
3. **Given** backups older than 7 days, **When** the backup script runs, **Then** old backups are automatically pruned.

---

### User Story 7 — Recovery Runbook Validation (Priority: P2)

An operator can recover from five defined failure scenarios: (A) ephemeral path corruption (restart), (B) broken `/etc` (manual fix or restore), (C) container won't start (entrypoint bypass), (D) cascading volume corruption (selective restore), and (E) agent deleted its own work (file restore from backup). Each scenario has a documented, tested procedure.

**Why this priority**: Recovery procedures are only reliable if they've been tested before they're needed. This story ensures the runbook from the architecture document is executable.

**Independent Test**: In a test environment, simulate each failure scenario and follow the documented recovery steps to verify they work.

**Acceptance Scenarios**:

1. **Given** a binary incorrectly written to `/usr/bin`, **When** the container is restarted, **Then** the ephemeral path is automatically reset to the clean image state.
2. **Given** a corrupted `/etc/sudoers`, **When** the operator uses `docker compose run --entrypoint /bin/bash agent`, **Then** the operator can access the container and repair the file manually.
3. **Given** a backup of the `agent_home` volume exists, **When** `restore-volume.sh agent_home <date>` is run, **Then** the deleted files are recovered.

---

### User Story 8 — Development Mode Isolation (Priority: P3)

During normal development, engineers work directly on the host (or via SSH) using the existing `uv run uvicorn` and `npm run dev` workflows. Docker is NOT used for day-to-day development. A developer may optionally start the Docker container for explicit testing and debugging of the container setup itself, using a dedicated `make docker-test` or `docker compose -f docker-compose.test.yml up` command.

**Why this priority**: The team's existing development workflow must not be disrupted. Docker is a deployment and packaging concern, not a development concern.

**Independent Test**: Verify that `npm run dev` and `uv run uvicorn` still work without Docker running. Verify that `make docker-test` starts the container for container-specific testing.

**Acceptance Scenarios**:

1. **Given** no Docker containers running, **When** a developer runs the existing dev commands (`npm run dev`, `PYTHONPATH=src uv run uvicorn ...`), **Then** the development environment works identically to today.
2. **Given** a developer wants to test the Docker setup, **When** they run the dedicated Docker test command, **Then** the container builds and starts with all volumes and environment variables configured.
3. **Given** the Docker test container is running, **When** the developer stops it, **Then** no changes are made to the host development environment.

---

### User Story 9 — Health Check and Monitoring (Priority: P3)

The Docker container includes a health check that verifies the agent runtime is operational. The health check is defined in `docker-compose.yml` and reports status via `docker compose ps`.

**Why this priority**: Health checks enable automated restart on failure and provide quick status visibility.

**Independent Test**: Start the container and verify `docker compose ps` shows a `healthy` status after the start period.

**Acceptance Scenarios**:

1. **Given** a running container, **When** `docker compose ps` is run, **Then** the container shows `healthy` status.
2. **Given** the agent startup log exists at `/var/log/agent-startup.log`, **When** the health check runs, **Then** it passes.
3. **Given** the container enters an unhealthy state, **When** the restart policy triggers, **Then** the container restarts automatically.

---

### User Story 10 — Agent Change Logging (Priority: P3)

All three agents (Hermes, OpenClaw, Pi) log significant system changes to `/var/log/agent-changes.log` with timestamps and action descriptions. This log persists across restarts (via the `agent_logs` volume) and is the first resource consulted during any recovery scenario.

**Why this priority**: The change log is the recovery lifeline — without it, diagnosing corruption takes hours instead of minutes.

**Independent Test**: Write a test entry to the change log, restart the container, and verify the entry persists.

**Acceptance Scenarios**:

1. **Given** a running container, **When** an agent writes to `/var/log/agent-changes.log`, **Then** the entry includes a UTC timestamp and action description.
2. **Given** the container is restarted, **When** `/var/log/agent-changes.log` is read, **Then** all previous log entries are intact.
3. **Given** `agent-startup.log`, **When** the container starts, **Then** a startup entry is automatically logged with the LLM API URL.

---

### Edge Cases

- What happens when the `.env` file is missing or incomplete at startup? The container should fail fast with a clear error message listing the missing variables.
- What happens when a Docker volume is corrupted beyond repair? The operator should be able to delete the volume entirely and let the image layer re-initialize the path from scratch.
- What happens when an agent writes to `/etc/passwd` and breaks authentication? The recovery runbook (Scenario B/C) must be followed; the operator uses a rescue container to repair the file.
- What happens when disk space on the host fills up from volume growth? The backup script should report disk usage, and the operator should monitor volume sizes.
- What happens when two agents write to the same volume path simultaneously? Docker volumes support standard POSIX locking; agents should use atomic operations for shared paths.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST provide a `Dockerfile` that builds a lean base image from Ubuntu 24.04 with Python 3, pip, pipx, micromamba, Node.js, git, and common CLI tools pre-installed. The container MUST run the full Wright stack (API server, web frontend, and all three agents) as a single deployable unit. GPU/CUDA support is explicitly out of scope for the initial image and will be added in a follow-up feature.
- **FR-002**: The system MUST provide a `docker-compose.yml` that defines 7 named volumes covering all agent-writable paths (`/home/`, `/usr/local/`, `/opt/`, `/var/lib/`, `/var/cache/`, `/etc/`, `/var/log/`).
- **FR-003**: The system MUST provide a `.env.example` template documenting all required environment variables (`LLM_API_URL`, `LLM_API_KEY`, `LLM_API_MODEL`).
- **FR-004**: The system MUST provide an `entrypoint.sh` that exports the container manifest into the `CONTAINER_MANIFEST` environment variable and logs the startup event.
- **FR-005**: The system MUST provide a `container-manifest.md` file baked into the image at `/container-manifest.md` with read-only permissions (444).
- **FR-006**: The system MUST provide host-side backup and restore scripts (`backup-volumes.sh`, `restore-volume.sh`) that operate on named Docker volumes.
- **FR-007**: A GitHub Actions workflow (`.github/workflows/docker-build.yml`) MUST build the Docker image on every push to `main` or `dev` branches using Docker Buildx with layer caching, tagged with the commit SHA and `latest`, and push to Docker Hub. GHCR support is deferred to a follow-up.
- **FR-008**: The system MUST NOT require Docker for day-to-day development. All existing development workflows (`npm run dev`, `uv run uvicorn`) MUST continue to work without Docker.
- **FR-009**: The system MUST provide a dedicated command for container testing/debugging that is separate from the normal development workflow.
- **FR-010**: The system MUST include a `docker-compose.yml` health check that verifies agent runtime status.
- **FR-011**: The recovery directory (`/recovery/`) MUST be mounted read-only inside the container, containing backup scripts and the recovery runbook.
- **FR-012**: The entrypoint MUST create the agent backup directory (`/home/agent/.backups/etc`) on every startup.
- **FR-013**: The backup script MUST automatically prune backups older than 7 days.
- **FR-014**: The `docker-compose.yml` MUST expose the Wright API port (8000) and web frontend port (5173) so operators can access the full application from the host.

### Key Entities

- **Docker Image**: The built artifact containing the base OS, pre-installed packages, container manifest, and entrypoint. Immutable once built.
- **Named Volumes**: 7 Docker-managed persistent storage locations that survive container restarts and hold all mutable agent state.
- **Container Manifest**: A read-only file describing the filesystem rules, install decision tree, and behavioral constraints for agents.
- **Recovery Scripts**: Host-side shell scripts for backing up, restoring, and inspecting volume data.
- **CI/CD Pipeline**: The automated build process that produces tagged Docker images from the repository.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Docker image builds successfully from a clean checkout in under 10 minutes.
- **SC-002**: Container starts and reaches `healthy` status within 30 seconds.
- **SC-003**: All 7 Docker volumes persist data across container restarts with zero data loss.
- **SC-004**: Recovery from ephemeral path corruption takes under 1 minute (a single restart).
- **SC-005**: Recovery from a broken `/etc` file takes under 15 minutes using the documented runbook.
- **SC-006**: Full volume backup completes in under 5 minutes for typical workloads.
- **SC-007**: Existing development workflows (`npm run dev`, `uv run uvicorn`) work identically with or without Docker running.
- **SC-008**: CI/CD pipeline produces a tagged, buildable Docker image on every push to `main` or `dev`.
- **SC-009**: No secrets (API keys, tokens) are present in any Docker image layer.

## Assumptions

- The host machine runs Docker Engine 24+ with Docker Compose v2 (plugin) installed.
- The CI/CD platform is GitHub Actions. The repository is hosted on GitHub with Actions enabled and Docker Buildx available in the runner environment.
- Docker Hub is the primary image registry. Docker Hub credentials (`DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN`) must be stored as GitHub Actions secrets. GHCR will be added as a secondary registry in a follow-up.
- The host filesystem has sufficient storage for 7 Docker volumes plus 7 days of backup archives.
- The three agents (Hermes, OpenClaw, Pi), the Wright API server, and the web frontend all run inside the same container as a single deployable unit.
- The LLM API endpoint is external to the container and accessible via network from the container.
- The `.env` file is managed by the operator and excluded from version control (`.gitignore`).
- The container has full outbound network access (no firewall restrictions). Agents can reach PyPI, GitHub, apt repositories, and the LLM API endpoint without allowlisting.
- Ubuntu 24.04 LTS is the base OS for the Docker image, consistent with the architecture document. GPU/CUDA, PyTorch, FreeCAD, and CalculiX (referenced in constitution §2) are deferred to a follow-up heavy image variant.
- The existing modular monorepo structure (`apps/`, `packages/`, `scripts/`) is mounted as a live volume during container testing but NOT during normal development.
