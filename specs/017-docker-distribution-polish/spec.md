# Feature Specification: Docker Distribution Polish

**Feature Branch**: `017-docker-distribution-polish`

**Created**: 2026-06-05

**Status**: Draft

**Input**: User description: "Create the plan for @[docs/community-features/017-docker-distribution.md]"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Self-Documenting OCI Metadata & Build-arg injection (Priority: P1)

Developers and automated indexers pulling the Wright Docker image can inspect standard labels inside the image layer to verify metadata, sources, licensing, and exact build revisions.

**Why this priority**: Highly critical for image validation, transparency, and packaging standards in enterprise/defense registries.

**Independent Test**: Build the image locally or in CI with custom arguments and run `docker inspect` to verify that OCI labels org.opencontainers.image.* are present and correctly filled.

**Acceptance Scenarios**:

1. **Given** a production Dockerfile with OCI label annotations, **When** the image is built passing revision SHA and version arguments, **Then** `docker inspect` shows the corresponding organization labels successfully populated.
2. **Given** the `docker-build.yml` workflow run, **When** a PR is processed, **Then** build variables are passed as arguments to buildx step without failing the action.

---

### User Story 2 - Docker Hub Profile & Automatic README Sync (Priority: P1)

Operators viewing the Wright Docker Hub profile are presented with a rich, up-to-date description of the project, compose instructions, and environmental configuration parameters.

**Why this priority**: Establishes discoverability and ease of use for new developers discovering Wright on Docker Hub.

**Independent Test**: Merge a change to `docker/DOCKER_HUB_README.md` and verify that the sync step in GitHub Actions successfully publishes the updated file as the repository description on Docker Hub.

**Acceptance Scenarios**:

1. **Given** a change in `docker/DOCKER_HUB_README.md`, **When** the release workflow completes, **Then** the Docker Hub page description is updated dynamically.

---

### User Story 3 - Production & Minimal Compose Variants (Priority: P2)

Operators want choices for deploying Wright: a full production compose setup with Jaeger/observability services, or a lightweight setup containing only essential services to minimize RAM/CPU footprints.

**Why this priority**: Essential to support resource-constrained hardware deployments.

**Independent Test**: Boot `docker-compose.minimal.yml` on a clean machine and confirm it starts correctly without Jaeger/OpenTelemetry exporter containers, while standard application routes remain functional.

**Acceptance Scenarios**:

1. **Given** a request to start a lightweight instance, **When** `docker compose -f docker-compose.minimal.yml up -d` is executed, **Then** only API and web services start, mounting essential volumes.

---

### User Story 4 - Pre-Push Scanning & Multi-Architecture Readiness (Priority: P3)

The project needs automated vulnerability reviews in CI, along with configuration preparation to build future ARM64 architecture support.

**Why this priority**: Ensures future-proofing and early vulnerability identification before public image releases.

**Independent Test**: Verify that the CI workflow runs setup-buildx-action, includes commented platform settings, and logs vulnerability scanner findings.

**Acceptance Scenarios**:

1. **Given** a push to `main`, **When** the docker-build workflow triggers, **Then** buildx is initialized and the security scanner runs.

---

### Edge Cases

- **Broken Docker Hub Sync**: How does the system handle changes to Docker Hub credentials or API throttling during README sync?
  - The workflow should fail gracefully with warnings rather than blocking the codebase release tag creation.
- **Missing Build Arguments**: What happens if git revision or created timestamps are empty during local manual builds?
  - The Dockerfile default values (`unknown` or empty string) prevent build failure.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Dockerfile MUST declare standard OCI labels (title, description, source, documentation, vendor, licenses).
- **FR-002**: CI workflow MUST pass version, revision, and created timestamp as `--build-arg` options during image builds.
- **FR-003**: The project MUST provide `docker/DOCKER_HUB_README.md` summarizing compose steps, environment parameters, volumes list, and ports mapping.
- **FR-004**: CI release workflow MUST automate pushing `DOCKER_HUB_README.md` to Docker Hub description on release tagging.
- **FR-005**: The project MUST include `docker-compose.minimal.yml` setting up basic containers (API and web) without Jaeger or telemetry backends.
- **FR-006**: Build workflows MUST configure setup-buildx-action and include commented platforms settings for future ARM64 builds.
- **FR-007**: System MUST perform pre-push vulnerability checks using `trivy` or `docker scout` (configured as a non-blocking step that reports warnings in the console without failing build or release runs).

---

### Key Entities

- **Docker Image Metadata**: Custom layer metadata holding organization and revision variables.
- **Compose Service Variants**: Configuration definitions matching minimal and production stacks.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Built image contains OCI labels verifiable via `docker inspect` showing exact matching revision and build timestamp.
- **SC-002**: Sync pipeline updates the Docker Hub description under 30 seconds upon release completion.
- **SC-003**: Minimal Compose stack launches using under 50% of the memory required by the full observability stack.

## Assumptions

- Target environment supports Docker and Docker Compose v2+.
- The repository owner configures `DOCKERHUB_TOKEN` secret in GitHub.
- Pinned actions are used for all pipeline additions.
