# Makefile CLI Command Reference

Wright provides a central developer `Makefile` to handle build automation, container orchestrations, and code quality controls.

---

## 1. Docker Appliance Operations

Use these targets to build, debug, and clear the containerized appliance stack.

### `make docker-build`
*   **Action**: Builds the production Docker image `wright-agent:latest` from `docker/Dockerfile`.
*   **Purpose**: Validates production bundle layers.

### `make docker-test`
*   **Action**: Spins up the container stack using the local test configuration `docker-compose.test.yml`.
*   **Note**: Automatically generates `docker/.env` if not present. Enables live local code mounts.

### `make docker-clean`
*   **Action**: Discards all running test containers and wipes local Docker volumes.
*   **Warning**: Destroys active container test states.

### `make docker-logs`
*   **Action**: Streams stdout/stderr outputs from running compose containers.

### `make docker-shell`
*   **Action**: Spawns an interactive bash shell within the active running `agent` container.

---

## 2. Testing & Quality Gates

Use these targets to validate mock integrations and local source logic.

### `make docker-test-e2e`
*   **Action**: Builds a clean stack, initializes the DB, and executes automated **Playwright UI integration tests**.
*   **Note**: Runs the local wizard installation and post-configuration chat screens sequentially.

### `make docker-test-live`
*   **Action**: Launches unmocked, live tests against real, configured local engines.

---

## 3. Local Host Development (Non-Docker)

Use these targets when editing Python or Node.js packages directly on the host computer.

### `make lint`
*   **Action**: Dispatches `ruff check` on the FastAPI gateway and core modules, and `eslint` on the React package.

### `make format`
*   **Action**: Formats Python code using `ruff format` and React code using `prettier --write`.

### `make typecheck`
*   **Action**: Runs `mypy` strict type checking on Python packages and `tsc --noEmit` on frontend files.

### `make test`
*   **Action**: Executes local backend unit tests via `pytest` and React component tests via `vitest`.

### `make check`
*   **Action**: Runs all quality gates sequentially (lint, format verification, typecheck, pytest, vitest).
