# Feature Specification: Package Boundaries and Workspace Use Cases

**Feature Branch**: `codex/045-package-boundary-and-workspace-use-cases`

**Created**: 2026-07-10

**Status**: Draft

**Input**: User description: "Implement Feature 045 from the approved Wright professionalization roadmap: enforce package boundaries, make the core domain independent of runtime infrastructure, and move workspace operations into owned application use cases while preserving public behavior."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Dependable Workspace Operations (Priority: P1)

An engineer can create, inspect, edit, back up, execute, and use version-control operations in a workspace through the existing product surfaces without behavior changing as responsibilities move behind a stable application boundary.

**Why this priority**: Workspace operations are central to Wright. Preserving their public behavior while isolating ownership is the minimum safe architectural slice.

**Independent Test**: Exercise every existing workspace route and the corresponding application operation against a temporary workspace, and confirm equivalent successful responses, failures, filesystem results, and version-control results.

**Acceptance Scenarios**:

1. **Given** a valid workspace and authenticated session, **When** an engineer performs any supported workspace file, backup, settings, execution, or version-control operation, **Then** the result and visible side effects match the established public contract.
2. **Given** invalid input, a missing workspace, unsafe path, command timeout, or infrastructure failure, **When** an operation is requested, **Then** the engineer receives the same stable category of error without partial unreported changes.
3. **Given** multiple workspace operations, **When** blocking work runs concurrently, **Then** request handling remains responsive and each operation is bounded by a documented timeout.

---

### User Story 2 - Enforced Architectural Ownership (Priority: P1)

A maintainer receives an immediate, actionable failure when a change introduces an unapproved dependency between Wright packages, including imports hidden inside functions or performed dynamically.

**Why this priority**: Without executable enforcement, the same reverse dependencies and route-level business logic will return and future gateway work will inherit two competing service graphs.

**Independent Test**: Run the architectural fitness suite against both the repository and synthetic forbidden static and dynamic imports, confirming every unapproved edge is rejected and every declared edge is accepted.

**Acceptance Scenarios**:

1. **Given** the approved package graph, **When** repository source is analyzed, **Then** every package dependency follows the declared one-way direction.
2. **Given** a forbidden direct, local, aliased, or dynamic import, **When** the fitness check runs, **Then** it fails and identifies the source file and dependency edge.
3. **Given** a new approved dependency, **When** a maintainer updates the single dependency policy and package metadata consistently, **Then** the fitness check accepts it.

---

### User Story 3 - Replaceable Infrastructure (Priority: P2)

A maintainer can test workspace policies and workflows without starting the HTTP application, using a real database, invoking the host version-control executable, or selecting a concrete agent provider.

**Why this priority**: Direct use-case testing makes behavior safer to change and provides the seam needed by later MCP, release, and integration features.

**Independent Test**: Construct application use cases with in-memory or recording implementations for persistence, files, version control, processes, agent context, gateway notification, secrets, and paths; then verify complete workflows and failure behavior directly.

**Acceptance Scenarios**:

1. **Given** recording implementations of external capabilities, **When** a workspace use case runs, **Then** its decisions and requested effects can be asserted without framework or host dependencies.
2. **Given** one infrastructure implementation fails or times out, **When** the use case runs, **Then** it returns a typed application error and does not silently continue.
3. **Given** the production composition root, **When** the application starts, **Then** concrete implementations are supplied explicitly and no use case selects a global provider or workspace implicitly.

---

### User Story 4 - Safe Compatibility Migration (Priority: P2)

An operator can upgrade to the new internal architecture without migrating workspace data or changing client requests, and can roll back to the prior release using the existing state backup procedure.

**Why this priority**: This is an ownership migration, not a public API or data-format migration; operators must not bear conversion risk.

**Independent Test**: Start with current-release state and workspace files, exercise the upgraded product, restore the previous application version against an existing backup, and confirm no new state format is required.

**Acceptance Scenarios**:

1. **Given** existing workspaces and state, **When** the upgraded application starts, **Then** no schema or workspace conversion is required.
2. **Given** a compatibility adapter retained for a still-used legacy caller, **When** that caller executes, **Then** it delegates to the owned application operation and emits no alternate business path.
3. **Given** call-graph evidence that a legacy entry point is unused, **When** the feature is finalized, **Then** that entry point is removed and the fitness suite prevents its reintroduction.

### Edge Cases

- A workspace disappears, is replaced, or becomes inaccessible between lookup and an operation.
- A workspace path is valid but a requested file is missing, a directory, too large for preview, binary, or unsupported for execution.
- Version-control output is empty, non-UTF-8, large, or accompanied by a non-zero exit; credentials must remain redacted.
- A branch or commit name resembles an option, contains whitespace, or is otherwise invalid.
- A blocking operation exceeds its deadline or is cancelled by the requesting client.
- A notification consumer is unavailable after a successful workspace mutation.
- Two operations target the same workspace concurrently while another targets a different workspace.
- A forbidden dependency is expressed through relative imports, aliases, import-from statements, `importlib`, or `__import__`.
- Test-only code or type-checking imports attempt to bypass the production dependency policy.
- Package metadata declares an edge that source does not use, or source uses an edge metadata does not declare.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST define one authoritative package ownership and dependency policy covering the core domain, state storage, tool registry, agent adapters, workspace application service, API application, public client, and integration packages.
- **FR-002**: Automated fitness checks MUST reject every undeclared or reverse dependency, including imports performed locally or dynamically, and MUST report the offending file and edge.
- **FR-003**: The dependency policy and declared package dependencies MUST remain mutually consistent; drift in either direction MUST fail verification.
- **FR-004**: The core domain package MUST contain only domain identifiers, value objects, error taxonomy, and side-effect-neutral contracts; it MUST NOT own state queries, filesystem mutation, process execution, version-control execution, provider configuration, application orchestration, or dynamic loading of higher-level packages.
- **FR-005**: The system MUST expose explicit contracts for workspace repositories, files and paths, version control, bounded processes, agent context, gateway or client notifications, secrets, and time where the application workflow depends on those capabilities.
- **FR-006**: Workspace application operations MUST receive their external capabilities explicitly and MUST NOT select a concrete provider, global workspace, database, or process implementation inside a use case.
- **FR-007**: Workspace create, read, update, delete, list, activation, and session-selection behavior MUST be owned by independently testable application operations.
- **FR-008**: Workspace file listing, reading, preview/download resolution, writing, directory creation, deletion, backup listing/creation/restore, and safe execution behavior MUST be owned by independently testable application operations.
- **FR-009**: Workspace version-control status, diff, revert, commit, history, push, pull, branch, and merge behavior MUST be owned by independently testable application operations.
- **FR-010**: Workspace context, settings, credentials-status, and agent materialization behavior MUST be owned by independently testable application operations.
- **FR-011**: API workspace routes MUST be limited to authentication and dependency resolution, request/response translation, streaming response construction where necessary, and stable application-error-to-transport-error mapping.
- **FR-012**: API workspace routes MUST NOT directly query state, mutate files, run host commands, perform version-control operations, choose an agent provider, or import another route to trigger notifications.
- **FR-013**: Blocking filesystem, version-control, process, and agent operations invoked from asynchronous request handling MUST run through a bounded execution mechanism with configurable deadlines and cancellation behavior.
- **FR-014**: All existing workspace HTTP paths, request fields, response fields, status categories, and externally visible side effects MUST remain compatible unless an existing behavior violates an already-approved security requirement.
- **FR-015**: Application failures MUST use a stable typed taxonomy that distinguishes not-found, invalid input, conflict, forbidden path, unavailable dependency, timeout, cancellation, and internal failure without exposing credentials or raw command details.
- **FR-016**: Successful mutations that require downstream refresh MUST publish through an injected notification contract; notification failure MUST be observable and MUST follow a documented consistency rule.
- **FR-017**: Production implementations MUST preserve the established workspace confinement, secret-provider, migration, and per-session identity guarantees from Features 042-044.
- **FR-018**: Compatibility adapters MAY remain for one release only where current call-graph evidence proves a live caller; each adapter MUST delegate to one owned operation and be documented with a removal condition.
- **FR-019**: The legacy global workspace activation path and any reverse runtime import MUST be removed once repository-wide static and dynamic call-graph checks prove no supported caller remains.
- **FR-020**: Direct application-operation tests MUST cover success, validation rejection, infrastructure failure, timeout, cancellation, and concurrent workspace isolation using replaceable implementations.
- **FR-021**: Route-level contract tests MUST prove public compatibility and MUST also prove routes contain no forbidden infrastructure behavior.
- **FR-022**: Package and architecture documentation MUST describe ownership, approved edges, extension procedure, compatibility adapters, timeout behavior, and rollback expectations.
- **FR-023**: This feature MUST NOT change the state schema, workspace file format, public authentication model, gateway protocol, canonical catalog source, release pipeline, or frontend contract generation.

### Key Entities

- **Dependency Policy**: The authoritative set of source areas, owned responsibilities, approved dependency edges, and prohibited behaviors.
- **Workspace Operation**: One application-level action with validated input, a typed result, explicit external capabilities, and defined failure semantics.
- **Workspace Repository Contract**: The interface for workspace, session, context, and settings state required by application operations.
- **Path and File Contract**: The interface for confined workspace paths, file metadata, content, backups, and safe mutation.
- **Version-Control Contract**: The interface for status, history, branch, merge, synchronization, and credential-safe remote actions.
- **Process Contract**: The interface for bounded host execution, deadlines, cancellation, and redacted results.
- **Agent Context Contract**: The provider-neutral interface for creating and removing agent-specific workspace context.
- **Notification Contract**: The interface through which successful mutations request downstream refresh without importing transport code.
- **Compatibility Adapter**: A temporary delegating entry point preserving a live caller while ownership moves.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: One automated architecture check evaluates 100% of production source files in owned Python packages and applications and rejects all seeded forbidden direct and dynamic dependency examples.
- **SC-002**: Every supported workspace route has both a passing public-contract test and a directly tested application operation; no route performs state queries, file mutation, host execution, provider selection, or version-control work.
- **SC-003**: All supported workspace workflows produce the same request compatibility, response compatibility, and visible workspace effects as the pre-feature baseline across the full regression suite.
- **SC-004**: Direct operation tests complete without an HTTP server, persistent state file, real version-control executable, or concrete agent runtime.
- **SC-005**: Every potentially blocking operation has an enforced deadline; timeout and cancellation tests finish within twice the configured test deadline and leave no unowned worker or child operation.
- **SC-006**: Two concurrent workspace workflows remain isolated in 100 consecutive deterministic test iterations with no cross-workspace state, path, credential, context, or notification leakage.
- **SC-007**: The core domain package has zero imports of application, adapter, state-storage, tool-registry, API, subprocess-execution, or database modules under the authoritative fitness check.
- **SC-008**: A previous-release state and workspace fixture runs under the upgraded application with zero schema or file conversion, and documented rollback requires only the existing backup/restore procedure.
- **SC-009**: The complete development merge gate passes with no skipped sub-gates before the feature is proposed for `dev`.

## Assumptions

- Existing authenticated workspace HTTP contracts remain the compatibility baseline.
- Feature 042 confinement and Feature 043 credential guarantees are invariants, not optional compatibility behavior.
- Feature 044 owns all state lifecycle and schema changes; this feature may add repository implementations but no migration.
- The application remains local-first and single-operator by default, while session identity remains explicit.
- R2.3 lifecycle coordination, R2.4 catalog consolidation, R2.5 observability, and R2.6 frontend contracts remain separate later features.
- Notification delivery after a committed workspace mutation is best-effort but observable; failure does not undo an already successful workspace or version-control change.
- Compatibility adapters are permitted only for demonstrably live callers and do not justify retaining duplicate business logic.
