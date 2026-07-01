# Feature Specification: Architecture Refactoring Audit Implementation

**Feature Branch**: `codex/refactoring-audit-2026-07-01`

**Created**: 2026-07-01

**Status**: Draft

**Input**: User description: "Implement the 2026-07-01 architecture refactoring audit in small, reviewable phases while preserving Hermes, offline-first behavior, API compatibility, clean-container MCP validation boundaries, and Spec Kit phase isolation."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Select Agent Runtimes Without Hermes Coupling (Priority: P1)

Wright operators need the system to choose the active agent runtime through an agent-neutral runtime boundary so Hermes remains the default working engine while future engines can be introduced without changing API boot behavior.

**Why this priority**: Agent abstraction is the first dependency for every later gateway and OpenClaw-facing change. The system must stop treating Hermes as the architecture boundary before broader refactors proceed.

**Independent Test**: Can be fully tested by selecting the default runtime, selecting Hermes explicitly, and attempting an unsupported runtime while verifying health responses still match the existing contract.

**Acceptance Scenarios**:

1. **Given** a fresh Wright startup with no active runtime override, **When** the API reports agent health and active agent state, **Then** Hermes is selected through the runtime boundary and existing health response fields are preserved.
2. **Given** a configured supported runtime, **When** the active runtime is read or updated, **Then** the system uses registry metadata rather than route-local hardcoded lists.
3. **Given** an unsupported runtime name, **When** configuration is saved, **Then** the request is rejected with the existing unsupported-agent behavior and no runtime state is changed.

---

### User Story 2 - Share A Wright Gateway Contract Across Agents (Priority: P2)

Wright maintainers need a generic Wright gateway contract that Hermes can keep using and OpenClaw can later implement through the same MCP gateway protocol.

**Why this priority**: The gateway is the next cross-agent integration point. Naming and contract ownership must become agent-neutral before adding another concrete engine.

**Independent Test**: Can be tested with fake gateway profiles and a Hermes-compatible profile to prove gateway setup and workspace context writing do not require Hermes-specific API services.

**Acceptance Scenarios**:

1. **Given** the Hermes runtime profile, **When** gateway sync runs, **Then** Hermes remains compatible with the existing Wright gateway MCP protocol.
2. **Given** a fake future runtime profile, **When** the gateway contract is exercised, **Then** no Hermes file paths or Hermes configuration names are required by the shared contract.
3. **Given** workspace tools change, **When** gateway notification behavior runs, **Then** the same Wright gateway event semantics remain available to agents.

---

### User Story 3 - Keep MCP API Routes Thin (Priority: P3)

API maintainers need MCP route handlers to validate HTTP input, delegate business operations to service-layer code, and return the same public response shapes.

**Why this priority**: Thin routes are a constitutional requirement and reduce production risk as install, validation, credential, and catalog behavior grows.

**Independent Test**: Can be tested by moving one MCP operation group at a time behind services while existing route tests continue to verify status codes and response bodies.

**Acceptance Scenarios**:

1. **Given** existing MCP list, install, validate, credential, version-check, and report-missing requests, **When** route behavior is exercised, **Then** successful response bodies remain backward compatible.
2. **Given** existing not-found, duplicate, blocked-install, and validation-failure cases, **When** route behavior is exercised, **Then** HTTP status codes and error messages remain compatible.
3. **Given** MCP business logic needs test coverage, **When** services are tested directly, **Then** route tests can stay focused on HTTP translation.

---

### User Story 4 - Normalize MCP Catalog Boundaries (Priority: P4)

Catalog maintainers need one shared catalog schema and normalization boundary that the API and Hermes plugin both consume while the Hermes plugin remains a first-class package.

**Why this priority**: Catalog drift can produce contradictory installability, validation, and display behavior across the API, UI, and plugin.

**Independent Test**: Can be tested with golden normalization fixtures and parity checks that compare shared model output with Hermes plugin catalog behavior.

**Acceptance Scenarios**:

1. **Given** a catalog entry from the Hermes plugin catalog, **When** it is normalized through the shared boundary, **Then** metadata such as installability, platform support, credentials, and validation summary is preserved.
2. **Given** API seed behavior, **When** catalog data is loaded, **Then** the API receives normalized records without requiring a separate divergent schema definition.
3. **Given** the Hermes plugin package, **When** its catalog APIs are exercised, **Then** the plugin remains installable and its public catalog behavior remains compatible.

---

### User Story 5 - Plan Clean-Container MCP Validation Evidence (Priority: P5)

Engineering MCP validators need a local clean-container validation harness seam that preserves metadata classification as a fast preflight and introduces explicit validation plan and evidence records.

**Why this priority**: The documented validation process requires repeatable evidence and must not be confused with host-local dependency checks.

**Independent Test**: Can be tested in the fast suite with a lightweight mock MCP server path and no Docker or network dependency, while Docker validation remains opt-in.

**Acceptance Scenarios**:

1. **Given** a blocked or missing-dependency server, **When** validation is planned, **Then** metadata classification remains available as preflight output.
2. **Given** a lightweight mock MCP server, **When** a validation plan is generated, **Then** the plan records initialize, initialized notification, tools list, optional safe tool call, and Wright gateway probe steps.
3. **Given** validation that requires Docker or network, **When** the default fast suite runs, **Then** those checks are documented as opt-in and are not required for fast local validation.

---

### User Story 6 - Add Constitution-Required System Smoke Coverage (Priority: P6)

Maintainers need minimal system smoke coverage for API health, default agent runtime behavior, MCP listing, and one Wright gateway happy path so architecture refactors have an end-to-end safety net.

**Why this priority**: The constitution requires system E2E coverage and the current smoke folder does not cover these backend workflows.

**Independent Test**: Can be tested with local mocks or fakes that start the API in a controlled environment without live agents, Docker, or network services.

**Acceptance Scenarios**:

1. **Given** a local test environment, **When** the system smoke suite runs, **Then** API health and agent default behavior are verified.
2. **Given** seeded or fake MCP data, **When** the smoke suite requests MCP listing, **Then** the response shape is verified without network dependencies.
3. **Given** a fake installed MCP server and tool, **When** the Wright gateway happy path is exercised, **Then** prefixed tool listing and a safe mocked call are verified.

### Edge Cases

- Active runtime configuration references a known future agent without an implemented engine.
- Runtime selection changes while existing session and workspace records still reference Hermes-created sessions.
- Wright gateway sync runs without any active workspace or without installed MCP servers.
- MCP install/update flows encounter blocked, non-working, credential-missing, or host-dependent catalog metadata.
- Catalog entries contain plugin-only fields, API-only fields, duplicate IDs, or missing platform-support records.
- Clean-container validation requires unavailable Docker, network, credentials, proprietary software, or hardware-bound backends.
- System smoke tests run in an offline development environment.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST select agent runtimes through an agent-neutral registry or factory boundary.
- **FR-002**: System MUST keep Hermes as the default working runtime when no other supported runtime is configured.
- **FR-003**: System MUST reject unsupported runtime names without changing active runtime state.
- **FR-004**: System MUST preserve existing agent health and inference health response fields.
- **FR-005**: System MUST use "Wright gateway" as the generic gateway term.
- **FR-006**: System MUST define shared Wright gateway profile and sync contracts that are not Hermes-specific.
- **FR-007**: System MUST keep Hermes gateway behavior compatible through the new shared gateway contracts.
- **FR-008**: System MUST prepare an OpenClaw-compatible gateway seam using the same MCP gateway protocol without implementing a full OpenClaw engine.
- **FR-009**: System MUST move MCP route business behavior into service-layer code in small increments.
- **FR-010**: System MUST preserve existing MCP API response shapes unless a breaking change is explicitly planned and approved.
- **FR-011**: System MUST keep package-manager install and update flows free of new approval gates beyond existing catalog safety defaults and blocked/non-working restrictions.
- **FR-012**: System MUST preserve offline-first behavior for core workflows and default fast tests.
- **FR-013**: System MUST keep `hermes-plugin-wright` as a first-class package and consumer of shared Wright concepts.
- **FR-014**: System MUST introduce shared MCP catalog schema or normalization behavior that can be consumed by API and plugin boundaries.
- **FR-015**: System MUST preserve metadata classification as a validation preflight rather than treating it as full clean-container validation evidence.
- **FR-016**: System MUST introduce explicit validation plan and validation evidence concepts for local clean-container MCP validation.
- **FR-017**: System MUST NOT add MCP-specific host software to the base Docker image solely to pass catalog validation.
- **FR-018**: System MUST make Docker, network, credentialed, proprietary, or hardware-bound validation opt-in outside the default fast suite.
- **FR-019**: System MUST add focused tests for every touched contract, including agent selection, Hermes default behavior, invalid runtime handling, gateway contracts, MCP services, catalog normalization, validation planning, and smoke coverage.
- **FR-020**: System MUST include a migration and rollback note before implementation proceeds.

### Key Entities

- **Agent Runtime Provider**: A selectable agent implementation with identity, health capabilities, configuration behavior, and engine factory.
- **Agent Runtime Registry**: The agent-neutral source for runtime lookup, default selection, validation, and factory creation.
- **Wright Gateway Profile**: Agent-facing gateway metadata describing how an agent consumes the Wright MCP gateway protocol.
- **Gateway Sync Adapter**: Runtime-specific behavior that syncs gateway configuration, workspace context, and tool-change notifications.
- **MCP Service Operation**: A service-layer operation that owns MCP catalog, install, validation, credential, version, or report-missing behavior.
- **Catalog Record**: A normalized MCP catalog item with installability, platform support, risk, dependency, credential, and validation metadata.
- **Validation Plan**: A repeatable ordered plan for preflight checks, MCP protocol probes, safe backend probes, and gateway proxy probes.
- **Validation Evidence**: A recorded outcome from a validation plan with environment, commands, statuses, diagnostics, and follow-up links.
- **System Smoke Scenario**: A local, repeatable end-to-end verification path for constitution-required behavior.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of agent runtime selection tests pass for default Hermes selection, explicit Hermes selection, and unsupported runtime rejection.
- **SC-002**: API health and inference health tests continue to return the same top-level fields as before the refactor.
- **SC-003**: At least one Hermes compatibility test proves the shared Wright gateway path preserves existing gateway behavior.
- **SC-004**: MCP route response-shape tests continue to pass for list, register, install, uninstall, validate, credentials, version check, update, delete, and report-missing operations touched by the refactor.
- **SC-005**: Catalog parity or normalization tests cover at least one tested entry, one might-work entry, one blocked entry, and one non-working entry.
- **SC-006**: Validation planning tests cover blocked, missing-dependency, passed metadata, and lightweight mock MCP probe paths without Docker or network.
- **SC-007**: A local smoke suite covers API health, default agent behavior, MCP listing, and one Wright gateway happy path.
- **SC-008**: Default targeted test runs complete without requiring Docker, network, hosted agents, credentials, proprietary software, or hardware-bound tools.
- **SC-009**: Every implementation phase can be reviewed as an isolated change group with its own tests and rollback path.

## Assumptions

- Hermes remains the only fully implemented production runtime during this feature.
- OpenClaw support in this feature is limited to contracts, stubs, and seams needed to prevent Hermes-specific overfitting.
- Existing public API response shapes are the compatibility baseline.
- Service extraction may keep some temporary compatibility wrappers while routes are made thinner incrementally.
- Structured validation evidence is preferred as the canonical record, with Markdown follow-up records remaining useful for human-readable problem logs.
- Docker-based clean-container validation is opt-in and documented separately from fast local tests.
- The migration/rollback note may live in this feature spec and plan unless maintainers request a separate architecture document update.
