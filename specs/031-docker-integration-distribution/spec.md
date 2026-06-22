# Feature Specification: Docker Integration & Distribution Packaging

**Feature Branch**: `031-docker-integration-distribution`

**Created**: 2026-06-22

**Status**: Draft

**Input**: User description: "Create the Docker integration and distribution packaging for hermes-plugin-wright so the plugin works in both Docker appliance and local install scenarios. (1) Docker: Modify the existing docker/Dockerfile to COPY the hermes-plugin-wright/ directory into the image and pip install it during the build stage. The existing docker/supervisord.conf already starts both wright-api (uvicorn on port 8000) and hermes-gateway (hermes -p wright gateway run on port 8642). In Docker, /wright start should detect that the API is already running (supervisord manages it) and just open the browser / report status. The existing docker/entrypoint.sh bootstraps the Hermes profile — the plugin should be automatically available after image build. (2) Local install: The plugin should be installable via "pip install hermes-plugin-wright" or "pip install -e ./hermes-plugin-wright" for development. Update pyproject.toml with proper entry points so Hermes auto-discovers the plugin. (3) Context injection: Wire the register(ctx) function in __init__.py to load the catalog, register the /wright slash command, and inject workspace context into the Hermes session. The existing hermes_sync.py already writes .hermes.md files and the wrightgateway config.yaml entry — the plugin should not duplicate this. (4) README: Create hermes-plugin-wright/README.md with installation instructions (pip install, Docker), quick start guide (/wright start, /wright catalog, /wright install), and link to the full plan. Reference: docs/wright-hermes-plugin-plan.md sections 11 (Distribution), 12 (Docker Integration), 13 (Existing-Install Integration)."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Docker Appliance Execution (Priority: P1)

Users run the Wright full-stack application as a single-container Docker appliance. During the container build, the plugin is copied into the image and registered into the Hermes Agent isolated tool environment. Inside the container, supervisord automatically spins up both the uvicorn API server and the Hermes gateway. When the user enters `/wright start`, the plugin detects that it is executing inside a Docker environment, confirms that the backend API is already healthy under supervisor, and reports the status without trying to launch a nested or redundant uvicorn subprocess.

**Why this priority**: Core production delivery flow for the virtual mechanical engineering appliance.

**Independent Test**:
- Build the production Docker container, start it, attach to the container bash shell, and execute the slash command dispatcher `/wright start`. Assert that it detects the healthy API, opens the UI browser endpoint (or prints the active URL), and does not spawn new background python processes.

**Acceptance Scenarios**:

1. **Given** the Wright stack is running under supervisord inside Docker, **When** the user runs `/wright start`, **Then** the plugin verifies the API connection is active, opens the default browser (if graphics server is running) or outputs connection success status, and does not start any new uvicorn processes.
2. **Given** the supervisord-managed uvicorn server is stopped or unhealthy, **When** the user runs `/wright start` inside Docker, **Then** the plugin does not attempt to launch uvicorn manually and instead returns a warning directing the user to inspect container/supervisor log outputs.

---

### User Story 2 - Local Install & Auto-Discovery (Priority: P2)

Developers or users with standalone Hermes installations want to run the Wright command suite. They install the plugin package locally. The plugin registers as a standard python entry point so that the Hermes Agent loader automatically discovers it on startup.

**Why this priority**: Essential for manual local setup, debugging, and third-party integrations outside the Docker container.

**Independent Test**:
- Run a package installation (`pip install ./hermes-plugin-wright`) in a clean virtual environment and run the verification loader script. Verify the entry point resolves and commands register.

**Acceptance Scenarios**:

1. **Given** a local Python environment, **When** the user runs `pip install -e ./hermes-plugin-wright`, **Then** the package successfully installs and registers entry points under the `hermes_agent.plugins` group.
2. **Given** the plugin is installed, **When** the Hermes Agent starts, **Then** it auto-discovers and registers the `/wright` slash commands namespace.

---

### User Story 3 - Integrated Context Synchronization (Priority: P2)

When the plugin registers, it initializes the engineering catalog and slash commands. To prevent file conflicts, write races, and duplicate work, the plugin delegates workspace `.hermes.md` instruction file compilation and configuration updates to the existing `hermes_sync.py` service.

**Why this priority**: Prevents redundant config file manipulation and sync errors between the plugin and the core API services.

**Independent Test**:
- Activate a workspace via the Wright API, inspect the target folder to verify the sync daemon generates the appropriate `.hermes.md` file, and verify the loaded plugin reads active parameters without duplicating metadata write calls.

**Acceptance Scenarios**:

1. **Given** a running Hermes session, **When** a workspace is activated in Wright, **Then** the sync service generates the `.hermes.md` context file, and the plugin reads the active workspace directory path without duplicate file writes.

---

### User Story 4 - Onboarding Documentation (Priority: P2)

Users or developers view the plugin's README file to understand the architecture, package installation, Docker setup steps, and command references.

**Why this priority**: Critical for onboarding, developer documentation, and package usability.

**Independent Test**:
- Verify the README format and links render correctly in a markdown viewer.

**Acceptance Scenarios**:

1. **Given** the `hermes-plugin-wright` repository, **When** opening the `README.md`, **Then** it lists step-by-step instructions for local pip installs, Docker container copy-mount instructions, slash command references, and references the master implementation plan.

---

### Edge Cases

- **Container Header Detection**: If container boundaries are not detected (e.g. no `/.dockerenv` file exists but running under a custom container runtime), the plugin must fall back to standard local checks.
- **Root-Ownership Conflict**: In Docker, if configuration writes run as `root`, future agent runs will hit permission locks. All bootstrap commands in `entrypoint.sh` must execute under the `agent` user context.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The `docker/Dockerfile` MUST copy the `hermes-plugin-wright/` directory to `/opt/hermes-plugins/wright/` during build.
- **FR-002**: The `docker/Dockerfile` MUST install/inject the plugin package into the `hermes-agent` tool environment via `uv tool inject` or `pip install` during the build stage.
- **FR-003**: The plugin `/wright start` handler MUST detect if it is running inside the Docker container by checking if `/.dockerenv` is present.
- **FR-004**: If executing in Docker, `/wright start` MUST check if the API is already healthy; if healthy, it reports status and does not start uvicorn. If unhealthy, it MUST return a diagnostic warning rather than spawning a detached process.
- **FR-005**: The plugin's `pyproject.toml` MUST declare the `wright = "hermes_plugin_wright:register"` entry point in the `"hermes_agent.plugins"` namespace.
- **FR-006**: The plugin `register(ctx)` function MUST load the catalog and register slash commands, delegating all static config files and `.hermes.md` generation to `hermes_sync.py`.
- **FR-007**: The package README file MUST document manual pip installation, Docker usage, command listings, and link back to the main implementation plan.

### Key Entities

- **Docker Runtime Boundary**: The container environment indicator (`/.dockerenv`) that controls launcher process spawning.
- **Plugin Entry Point (`hermes_agent.plugins`)**: The standard Python packaging hook allowing Hermes to detect and load the plugin.
- **Workspace Context File (`.hermes.md`)**: The Markdown instruction file written by the Wright API sync service and consumed by Hermes.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Docker build compiles successfully with the plugin injected, and verification script running inside the image returns 0.
- **SC-002**: Inside the container, `/wright start` completes in under 2 seconds.
- **SC-003**: The `README.md` is complete and renders all command options and master plan link with correct markdown syntax.

## Assumptions

- The Docker container uses an Ubuntu base image with `uv` and Python 3.13 installed.
- Hermes Agent loader can discover the plugin through Python's standard `importlib.metadata.entry_points`.
- The `agent` user has correct permissions to read files in `/opt/hermes-plugins/wright/`.
- No raw secrets are stored in the code or baked into the image.
