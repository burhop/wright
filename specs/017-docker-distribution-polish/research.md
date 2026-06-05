# Research: Docker Distribution Polish

**Branch**: `017-docker-distribution-polish` | **Date**: 2026-06-05

This document outlines the technical design decisions, tooling choices, and alternatives evaluated for the Docker Distribution Polish feature.

---

## 1. OCI Image Label Schema
*   **Decision**: Adopt the standard **Open Container Initiative (OCI) Image Spec Annotations** (`org.opencontainers.image.*`) directly in the production `Dockerfile`.
*   **Rationale**: 
    - Ensures the built image is fully self-documenting, making project metadata easily queryable via `docker inspect`.
    - Fully compatible with cloud-native tooling and registry indexes.
*   **Alternatives Considered**:
    - *Legacy labels* (e.g. `maintainer`, `version`): Deprecated in modern container packaging specs.
    - *No labels*: Fails basic discoverability standards for enterprise deployment environments.

---

## 2. Docker Hub Description Synchronization
*   **Decision**: Use the community-standard **`peter-evans/dockerhub-description@v4`** action in the GitHub Actions release workflow.
*   **Rationale**:
    - Simplifies authorization using repository credentials (`DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN`) without requiring bespoke CLI curl calls.
    - Robust error handling and rate-limit backing.
*   **Alternatives Considered**:
    - *Custom curl scripts*: Requires maintaining API authentication tokens and PATCH requests in raw bash, which is prone to breaking if Docker Hub's API changes.

---

## 3. Pre-Push Security Scan Rules
*   **Decision**: Integrate **Trivy** in the `docker-build.yml` CI workflow as a **non-blocking diagnostic check** (Option B).
*   **Rationale**:
    - Logs warnings and issues to the console for operator visibility.
    - Prevents sudden release blocking caused by new CVEs discovered in upstream base packages (such as CUDA, Python, or Ubuntu system files) that are out of our immediate control.
*   **Alternatives Considered**:
    - *Blocking scans*: Critical vulnerability alerts fail the pipeline. Rejected because it blocks urgent features releases when third-party libraries have unpatched vulnerabilities.

---

## 4. Compose Configuration Options
*   **Decision**: Create **`docker-compose.minimal.yml`** containing only the essential `agent` (API) service and mapping ports to `8080` (similar to standard test ports). Omit Jaeger tracing containers.
*   **Rationale**:
    - Eliminates significant resource overhead for users who want to run Wright without observability tools.
*   **Alternatives Considered**:
    - *Bespoke run script*: A bash script running `docker run` directly. Rejected because Docker Compose files are more declarative and maintainable.
