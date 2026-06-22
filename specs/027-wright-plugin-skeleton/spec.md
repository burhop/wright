# Feature Specification: Hermes Wright Plugin Skeleton & Registration

**Feature Branch**: `027-wright-plugin-skeleton`

**Created**: 2026-06-22

**Status**: Draft

**Input**: User description: "/speckit-specify Create the hermes-plugin-wright Python package that registers as a Hermes Agent plugin. The package lives at the repo root in a new hermes-plugin-wright/ directory. It contains: plugin.yaml (Hermes plugin manifest with name "wright", version, min_hermes_version, description), __init__.py with a register(ctx) entry point that Hermes calls on load, pyproject.toml for PyPI distribution (package name hermes-plugin-wright, Python >=3.11, dependencies: httpx, pyyaml, pydantic), and an empty tests/ directory with conftest.py. The register() function should log "Wright plugin loaded" using structlog and do nothing else for now — it will be extended by later features. The plugin.yaml should declare the /wright slash command namespace. Reference: docs/wright-hermes-plugin-plan.md sections 5 (Plugin Structure) and 11 (Distribution Strategy). The Wright project repo is https://github.com/burhop/wright."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Plugin Discovery and Registration (Priority: P1)

An operator or user runs the Hermes Agent with the Wright plugin installed. On startup, the Hermes plugin manager automatically discovers the `hermes-plugin-wright` package via its defined entry point. It loads the plugin and invokes the registration hook. During this initialization, the plugin emits a structured log message via `structlog` stating "Wright plugin loaded", confirming it is active and ready without attempting to perform heavier initialization.

**Why this priority**: Correct discovery and loading are prerequisites for all subsequent capabilities (commands, catalog, bridge, and Docker integration).

**Independent Test**: Can be tested by executing a build, installing the package in a python virtual environment, starting a minimal runner or mock loader that loads the plugin, and verifying the "Wright plugin loaded" message appears in the structured logs.

**Acceptance Scenarios**:

1. **Given** the `hermes-plugin-wright` package is installed in the target Python environment, **When** the Hermes plugin manager scans for plugins, **Then** the plugin is successfully discovered and loaded.
2. **Given** the plugin is loaded, **When** its registration entry point is invoked, **Then** a structured log containing the message "Wright plugin loaded" is emitted using the standard logging configuration.

---

### User Story 2 - Slash Command Namespace Availability (Priority: P1)

An end user interacts with the Hermes Agent in a chat session. When they request a list of available command namespaces or use auto-complete, they see the `/wright` slash command namespace. This namespace is registered during the plugin loading phase via the manifest capabilities declarations.

**Why this priority**: The `/wright` namespace is the user-facing interface for launcher, catalog, and status operations in later features. It must be declared during registration.

**Independent Test**: Can be verified by loading the plugin manifest in Hermes and checking that the `/wright` namespace is active and registered.

**Acceptance Scenarios**:

1. **Given** the plugin is loaded by Hermes, **When** inspecting the registered capabilities, **Then** the `/wright` slash command namespace capability is active and recognized.

---

### User Story 3 - Package Distribution & Installation (Priority: P2)

An engineer wishes to distribute or install the Wright integration plugin. They should be able to build a standard Python wheel/source distribution using standard build backends and install it using standard package management tooling. The package must clearly declare its requirements and dependencies so they are resolved automatically.

**Why this priority**: Ensures clean integration in both local development environments and Docker production image layers.

**Independent Test**: Can be tested by running a package build command (e.g. `pip install -e .` or `python -m build`) and verifying that dependencies are resolved and the package is correctly installed.

**Acceptance Scenarios**:

1. **Given** the plugin directory, **When** building a distribution package, **Then** a standard Python package is successfully produced without errors.
2. **Given** the package metadata, **When** installing the package, **Then** dependencies (`httpx`, `pyyaml`, `pydantic`) are resolved, and the package is correctly installed for Python environments >=3.11.

---

### Edge Cases

- **Hermes version mismatch**: What happens if the plugin is loaded in a Hermes version below `min_hermes_version`? -> The Hermes plugin manager should prevent loading the plugin and log a version incompatibility error.
- **Missing runtime dependencies**: What happens if one of the dependencies (e.g., `structlog`, `pydantic`) is missing? -> The import/registration fails gracefully, outputting a clear error message.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The plugin source package MUST reside in the `hermes-plugin-wright/` directory at the repository root.
- **FR-002**: The directory MUST contain a `plugin.yaml` manifest defining the metadata for the Hermes plugin (name: `"wright"`, version, min_hermes_version, description, capabilities, etc.).
- **FR-003**: The plugin manifest `plugin.yaml` MUST declare the `/wright` slash command namespace under capabilities.
- **FR-004**: The package module entry point MUST be defined in `hermes-plugin-wright/__init__.py` as `register(ctx)`.
- **FR-005**: The `register(ctx)` function MUST log the message `"Wright plugin loaded"` using `structlog` and perform no other action.
- **FR-006**: The package MUST include a `pyproject.toml` file configuration specifying PyPI packaging metadata, using `hatchling` as the build backend, requiring Python version `>=3.11`, and declaring dependencies: `httpx`, `pyyaml`, `pydantic`.
- **FR-007**: The `pyproject.toml` file MUST register the entry point `wright = "hermes_plugin_wright:register"` under the `"hermes_agent.plugins"` group.
- **FR-008**: The package MUST contain a `tests/` directory containing a `conftest.py` file to serve as a base for unit tests.

### Key Entities

- **Plugin Manifest (`plugin.yaml`)**: The configuration file parsed by Hermes on discovery, declaring name, version, and the `/wright` slash command capability.
- **Plugin Entry Point**: The `register(ctx)` hook inside the module's `__init__.py` which receives the Hermes context upon loading.
- **Distribution Package**: The build metadata configured in `pyproject.toml` that makes the plugin discoverable and installable as a Python library.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The package can be successfully built (`python -m build`) and installed in development mode (`pip install -e .`) within 10 seconds in a clean virtual environment.
- **SC-002**: On plugin load, exactly one structured log event with the message `"Wright plugin loaded"` is recorded using `structlog`.
- **SC-003**: The entry point registration makes the plugin auto-discoverable under the `hermes_agent.plugins` entry points group, which can be verified programmatically in Python.

## Assumptions

- The target runtime environment runs Python >= 3.11.
- `structlog` is available in the target python environment (either as a pre-installed framework or provided by Hermes).
- Hermes Agent supports standard Python entry point registration under the `"hermes_agent.plugins"` namespace.
- No actual slash command logic is required in this feature; only the registration of the `/wright` command namespace via `plugin.yaml` capability.
