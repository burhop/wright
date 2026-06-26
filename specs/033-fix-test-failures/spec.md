# Feature Specification: Fix Test Validation Failures

**Feature Branch**: `033-fix-test-failures`

**Created**: 2026-06-25

**Status**: Draft

**Input**: User description: "Use Spec Kit to fix all bugs causing test cases to fail."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Frontend Tests Pass on Windows (Priority: P1)

A developer running the frontend test suite on Windows can execute the existing web workspace tests without component initialization crashing in the test environment.

**Why this priority**: The current frontend suite is the clearest product-code failure and blocks confidence in the checked-in UI.

**Independent Test**: Run `npm run test --workspace=apps/web`; the command completes successfully with all Vitest tests passing.

**Acceptance Scenarios**:

1. **Given** the current repository on Windows, **When** the developer runs the web test command, **Then** the AppShell component test no longer fails while reading persisted split-view preferences.
2. **Given** browser storage is unavailable or throws, **When** AppShell initializes, **Then** the UI renders with safe default layout preferences.

---

### User Story 2 - Desktop Build Works Cross-Platform (Priority: P1)

A developer on Windows can run the desktop build script using the same documented npm command used on other platforms.

**Why this priority**: The dual-mode desktop feature promises a desktop build target, and the current script fails before the build starts on Windows.

**Independent Test**: Run `npm run build:desktop --workspace=apps/web`; the command completes successfully on Windows.

**Acceptance Scenarios**:

1. **Given** a Windows shell using npm, **When** the developer runs the desktop build command, **Then** the environment target is applied without shell syntax errors.
2. **Given** the desktop build succeeds, **When** the developer inspects the output, **Then** `apps/web/dist-desktop/` exists and contains the built desktop assets.

---

### User Story 3 - Python Test Command Uses the Project Environment (Priority: P2)

A developer can run the repository Python test suite from the project root without collection failing solely because workspace packages or declared dependencies are missing from the active environment.

**Why this priority**: Python collection failures obscure real regressions and make "all tests" status unreliable.

**Independent Test**: Run the documented Python test command from the project root after environment synchronization; tests either pass or report actionable test failures rather than import errors for declared project packages and dependencies.

**Acceptance Scenarios**:

1. **Given** the project dependencies have been synchronized, **When** the developer runs `uv run pytest`, **Then** test collection resolves workspace packages such as `api` and `tool_registry`.
2. **Given** plugin tests import YAML support, **When** the developer runs Python tests, **Then** collection does not fail because `yaml` is absent.

### Edge Cases

- Browser storage APIs may exist but throw security errors in test or embedded contexts.
- Desktop build scripts must work under Windows `cmd.exe`, PowerShell, and POSIX shells.
- Python validation should distinguish environment setup failures from product test failures.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The web UI MUST tolerate unavailable browser storage when reading or writing AppShell split-view preferences.
- **FR-002**: The AppShell fallback state MUST preserve the existing default behavior when no saved preferences are available.
- **FR-003**: The desktop build command MUST set the desktop build target in a shell-independent way.
- **FR-004**: The standard browser build command MUST continue to work unchanged.
- **FR-005**: The Python test workflow MUST use declared workspace packages and dependencies rather than failing during collection due to missing imports.
- **FR-006**: Fixes MUST be validated by rerunning the failing commands captured in the baseline.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `npm run test --workspace=apps/web` completes with 100% of Vitest tests passing.
- **SC-002**: `npm run build --workspace=apps/web` completes successfully.
- **SC-003**: `npm run build:desktop --workspace=apps/web` completes successfully on Windows.
- **SC-004**: Python test collection no longer reports missing declared modules such as `api`, `fastapi`, `httpx`, `yaml`, or `tool_registry`.

## Assumptions

- The active development target for this bugfix is Windows, matching the observed failures.
- Existing tests should be preserved; failures should be fixed by making code and commands robust.
- If Python dependencies are not installed locally, synchronizing the existing lockfile is an acceptable validation setup step.
