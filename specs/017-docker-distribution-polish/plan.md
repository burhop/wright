# Implementation Plan: Docker Distribution Polish

**Branch**: `017-docker-distribution-polish` | **Date**: 2026-06-05 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/017-docker-distribution-polish/spec.md`

## Summary

Improve the Docker image metadata, registry profile discoverability, and deployment profiles by declaring OCI annotation labels, configuring build-arg injections in GitHub Actions workflows, writing a dedicated Docker Hub README, automating its description sync via a release workflow step, pre-push vulnerability checks in CI, and creating a lightweight `docker-compose.minimal.yml` deployment variant.

## Technical Context

**Language/Version**: Docker (Dockerfile v1.4+), Bash (scripts), YAML (GitHub Actions)

**Primary Dependencies**: `peter-evans/dockerhub-description@v4` action, `aquasecurity/trivy-action@master` (or equivalent, non-blocking check), Docker Buildx

**Storage**: N/A

**Testing**: Local Docker image build check via `make docker-build`, YAML safe loader check, and local dry-run of minimal compose profile.

**Target Platform**: GitHub Actions CI/CD pipelines, Docker Hub Registry.

**Project Type**: Devops & Infrastructure Engineering

**Performance Goals**: Docker image builds utilizing buildx cache under 5 minutes; Docker Hub description updates within 30 seconds.

**Constraints**:
- Do not modify application source code or core runtime behavior.
- Pinned GHA action versions.
- OCI labels must not expose any build environment secrets.
- Multi-architecture is configuration preparation only (ARM64 support comments, setup-buildx-action, no amd64-specific binary fetches).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Framework (FastAPI)**: N/A (Compliant)
- **Architecture (Modular Monorepo)**: N/A (Compliant)
- **Offline-First Mandate**: N/A (Compliant)
- **Container Strategy (Thick Base / Thin Code)**: Compliant. The Dockerfile base dependencies and code mounts remain unchanged.
- **Zero-Server Databases**: N/A (Compliant)
- **Local Authentication**: N/A (Compliant)
- **Engineering Tooling Protocol**: N/A (Compliant)
- **UI & Testing**: Compliant. No changes to application UI.
- **Observability**: Compliant. The minimal compose file disables Jaeger but remains fully documented.
- **Autonomous Agent Workflow Rules**: Compliant. Planning is conducted on feature branch `017-docker-distribution-polish` and submitted for review.
- **Governance**: Compliant. No violations.

## Project Structure

### Documentation (this feature)

```text
specs/017-docker-distribution-polish/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Research decisions
├── data-model.md        # OCI metadata fields mapping
└── quickstart.md        # Build, inspect, and launch commands guide
```

### Source Code

```text
docker/
├── Dockerfile                # [MODIFY] Production Dockerfile declaring OCI labels and build-args
└── DOCKER_HUB_README.md      # [NEW] Rich profile description for Docker Hub

.github/
└── workflows/
    ├── docker-build.yml      # [MODIFY] Update to pass version/revision build args and Trivy scanner
    └── release.yml           # [MODIFY] Add step to sync DOCKER_HUB_README.md to Docker Hub

docker-compose.minimal.yml    # [NEW] Minimal compose configuration (agent only, no Jaeger)
```

**Structure Decision**: Place `DOCKER_HUB_README.md` under `docker/` and `docker-compose.minimal.yml` in the root of the project. Modify Dockerfile and GHA workflows in place.

## Complexity Tracking

> *No violations of the Constitution Check.*
