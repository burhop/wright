# Feature Specification: Wright Architecture Refactoring Phase 2

**Feature Branch**: `codex/refactoring-phase-2-2026-07-01`

**Created**: 2026-07-01

**Status**: Draft

**Input**: User description: "Implement Wright Architecture Refactoring Phase 2 using Spec Kit. Add workspace service boundaries, strengthen agent-neutral context materialization, move MCP catalog and safety ownership into tool_registry, add opt-in clean-container validation seams, generate or contract-test frontend types, strengthen observability and redaction, and update architecture/contributor docs while preserving Hermes, offline-first behavior, and API compatibility."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Activate Workspaces Through A Service Boundary (Priority: P1)

Operators and API maintainers need workspace creation, activation, config updates, tool enablement, and file execution to run through a package-owned service facade so routes remain HTTP translation layers.

**Why this priority**: Workspace lifecycle is the largest remaining route-local orchestration surface and the clearest path to non-Hermes engines.

**Independent Test**: Can be tested by creating and activating a workspace through the API and package service with a fake non-Hermes provider while preserving response shapes.

**Acceptance Scenarios**:

1. **Given** a workspace create request, **When** the route handles it, **Then** workspace lifecycle orchestration is delegated to `workspace_service` and the response shape is unchanged.
2. **Given** a workspace activation request for a fake non-Hermes provider, **When** the service activates the workspace, **Then** no `.hermes.md` or `~/.hermes` path is written by generic workspace code.
3. **Given** a workspace config or tool toggle request, **When** the route handles it, **Then** context refresh and gateway notifications are coordinated by service seams rather than route-local Hermes calls.

---

### User Story 2 - Materialize Agent Context Without Hermes As The Generic Model (Priority: P2)

Agent adapter maintainers need an explicit context materialization contract so Hermes keeps `.hermes.md` compatibility while OpenClaw and future engines can materialize their own context, or no context file, through the same abstraction.

**Why this priority**: Hermes remains default and first-class, but the generic architecture cannot keep treating Hermes file names as the workspace context model.

**Independent Test**: Can be tested with Hermes and fake/OpenClaw materializers: Hermes writes `.hermes.md`; non-Hermes activation does not touch Hermes paths.

**Acceptance Scenarios**:

1. **Given** the Hermes provider, **When** workspace context is refreshed, **Then** `.hermes.md` is materialized through Hermes adapter/profile code.
2. **Given** a non-Hermes provider, **When** workspace context is refreshed, **Then** the generic workspace service succeeds without writing Hermes files.
3. **Given** materialization fails, **When** the service reports the result, **Then** errors are typed and safe for API translation and logs.

---

### User Story 3 - Enforce MCP Safety Policy In The Registry Package (Priority: P3)

MCP operators need install, start, and tool-call decisions to be made by `tool_registry` using catalog risk, blocked status, credentials, network metadata, and local approval state.

**Why this priority**: Safety decisions are domain behavior, not UI or route decoration. They must be enforced even when callers bypass the frontend.

**Independent Test**: Can be tested with blocked, high-risk, missing-credential, and approved servers without Docker, network, or package registry access.

**Acceptance Scenarios**:

1. **Given** a blocked or non-working catalog entry, **When** install is requested, **Then** `tool_registry` rejects it with a typed policy decision.
2. **Given** a high-risk server that requires approval, **When** install/start/call is requested without the required approval, **Then** the policy blocks the operation.
3. **Given** a server with required credentials, **When** start or call is requested before credentials exist, **Then** the policy blocks the operation and reports missing credential names.

---

### User Story 4 - Produce Opt-In Validation Evidence (Priority: P4)

MCP validators need a local CLI and executor seam that can plan validation, run mock validation in fast tests, and write redacted JSON evidence plus Markdown summaries without implying clean-container validation passed unless it actually ran.

**Why this priority**: The catalog validation process depends on reproducible evidence and must stay Docker/network/proprietary-tool opt-in.

**Independent Test**: Can be tested with a mock executor and temp evidence directory in the default fast suite.

**Acceptance Scenarios**:

1. **Given** a cataloged server, **When** validation planning runs, **Then** evidence records include preflight, install steps, MCP protocol probes, safe probe metadata, and gateway probe metadata.
2. **Given** mock validation output containing credentials, environment values, commands, or subprocess output, **When** evidence is written, **Then** JSON and Markdown outputs redact forbidden values.
3. **Given** the clean-container executor is requested but not actually run, **When** the CLI exits, **Then** evidence records a skipped or follow-up-required result rather than claiming success.

---

### User Story 5 - Keep Frontend Contracts In Sync With Backend Schemas (Priority: P5)

Frontend maintainers need generated or contract-tested TypeScript types for MCP policy, validation evidence, agent metadata, and workspace service responses so React code does not duplicate backend/package domain truth.

**Why this priority**: Generated contracts reduce drift while keeping offline builds possible.

**Independent Test**: Can be tested by running an offline contract generation check and frontend tests when generated TypeScript files are touched.

**Acceptance Scenarios**:

1. **Given** backend/package schema models, **When** the contract generator runs, **Then** checked-in TypeScript contracts are current.
2. **Given** generated contracts change, **When** frontend tests run, **Then** the web workspace remains testable offline.
3. **Given** UI display constants remain frontend-owned, **When** contracts are generated, **Then** only domain data shapes are generated.

---

### User Story 6 - Observe Phase 2 Safety Flows Locally (Priority: P6)

Maintainers need logs and traces for workspace activation, agent runtime selection, context materialization, MCP safety decisions, lifecycle operations, tool calls, validation planning/runs, and evidence writing with redaction and clear identity semantics.

**Why this priority**: Observability is part of Wright's safety architecture. Trace identity and redaction must be consistent before more engines and validation runners are added.

**Independent Test**: Can be tested with log-shape, correlation propagation, redaction, and default-off remote export tests.

**Acceptance Scenarios**:

1. **Given** an API request with `X-Trace-Id`, **When** logs and spans are emitted, **Then** `X-Trace-Id` is treated as `wright.correlation_id` and OpenTelemetry owns `trace_id`/`span_id`.
2. **Given** command, environment, credential, tool argument, subprocess output, or validation evidence data, **When** it is logged, traced, or written as evidence, **Then** shared redaction removes sensitive values.
3. **Given** default local development configuration, **When** telemetry is configured, **Then** remote export remains disabled unless explicitly opted in.

### Edge Cases

- Existing workspaces created by Hermes continue to need `.hermes.md` materialization.
- A fake or future provider supports activation but intentionally writes no provider context file.
- Agent session creation fails and the workspace must remain usable with a local fallback session.
- Package-manager based MCP install does not require an extra approval just because a package manager is involved.
- A server is installable but high risk and therefore requires machine/workspace approval before lifecycle or call operations.
- Validation evidence contains secret-looking text in command lines, env vars, subprocess output, diagnostics, or tool arguments.
- Docker is unavailable or not requested during validation.
- Generated contracts are checked on a machine with no network.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST add `packages/workspace_service` as the package boundary for workspace lifecycle orchestration touched by this phase.
- **FR-002**: Workspace API routes touched by this phase MUST delegate create, activate, config update, tool enablement, context refresh, and file execution behavior to services or packages.
- **FR-003**: Generic workspace and API code MUST NOT directly write `.hermes.md` or `~/.hermes` files.
- **FR-004**: Hermes `.hermes.md` and `~/.hermes` behavior MUST remain available through Hermes adapter/profile/materializer code.
- **FR-005**: Agent adapters MUST expose an agent-neutral context materialization contract with support-level metadata.
- **FR-006**: A fake non-Hermes provider activation MUST succeed without Hermes file writes.
- **FR-007**: `tool_registry` MUST own MCP install/start/call policy decisions and typed safety results.
- **FR-008**: Blocked and non-working MCP entries MUST be rejected before install unless a future explicit override mode is added.
- **FR-009**: High-risk or safety-critical MCP entries with approval gates MUST require local approval before install, start, or call.
- **FR-010**: Missing required credentials MUST block MCP start and tool calls with a typed policy decision.
- **FR-011**: Clean-container MCP validation MUST remain opt-in and MUST NOT run from the default fast test suite.
- **FR-012**: Validation evidence MUST be written as canonical JSON and human-readable Markdown summaries with redaction.
- **FR-013**: The validation CLI MUST not claim clean-container success unless the clean-container executor actually ran.
- **FR-014**: Generated or contract-tested TypeScript domain contracts MUST be checked into the repository for touched MCP, validation, agent, and workspace schemas.
- **FR-015**: Telemetry MUST distinguish OpenTelemetry `trace_id`/`span_id` from Wright `wright.correlation_id` and the `X-Trace-Id` header.
- **FR-016**: Logs SHOULD include both OpenTelemetry trace fields and Wright correlation IDs when available.
- **FR-017**: Shared redaction MUST cover commands, environment variables, credentials, tool arguments, subprocess output, validation evidence, and diagnostics.
- **FR-018**: Remote telemetry export MUST be disabled by default and covered by tests.
- **FR-019**: Package import-boundary tests MUST prevent `packages/*` modules from importing `apps/api`.
- **FR-020**: Default verification MUST remain offline and Docker-free.
- **FR-021**: API response compatibility MUST be preserved unless explicitly documented as a breaking change.
- **FR-022**: Architecture and contributor docs MUST describe Hermes as default/first-class, not the generic architecture boundary.

### Key Entities *(include if feature involves data)*

- **Workspace Service Request**: A package-level command for create, activate, config update, tool enablement, context refresh, or file execution.
- **Workspace Activation**: The result of making a workspace current for an agent runtime, including session ID, local path, and materialization result.
- **Agent Context Materializer**: Provider-owned adapter that writes provider-specific context files or reports that no file is required.
- **Context Materialization Result**: Safe result metadata for provider ID, support level, files written, and warnings.
- **MCP Policy Decision**: Typed decision with allowed flag, reason, required approvals, missing credentials, network requirement, blocked state, and diagnostics.
- **Approval Context**: Local machine/workspace approvals available to the policy evaluator.
- **Validation Evidence**: Redacted structured validation record with environment, install/probe results, diagnostics, follow-up state, and redaction metadata.
- **Generated Contract Bundle**: Checked-in TypeScript definitions derived from backend/package schemas.
- **Telemetry Identity**: The combination of OpenTelemetry trace/span identifiers and Wright correlation identifiers.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Targeted package/API tests pass for `packages/agent_adapters`, `packages/tool_registry`, `packages/workspace_service`, `packages/core`, and `apps/api/tests`.
- **SC-002**: Import-boundary tests fail if any `packages/*` Python file imports `apps/api`.
- **SC-003**: At least one fake non-Hermes workspace activation test proves no `.hermes.md` or `~/.hermes` path is written.
- **SC-004**: MCP policy tests cover blocked, high-risk approval-required, missing-credential start/call, and approved paths.
- **SC-005**: Validation evidence tests prove JSON and Markdown outputs redact secret-like command/env/output/evidence fields.
- **SC-006**: Contract generation/check tests prove checked-in TypeScript domain types are current.
- **SC-007**: Telemetry tests prove log shape includes OpenTelemetry trace identity and Wright correlation identity where available.
- **SC-008**: Remote telemetry export defaults to disabled in tests.
- **SC-009**: API workspace create, activate, config, tools, and file-run tests continue to preserve response shapes.
- **SC-010**: Default verification commands complete without Docker, network, credentials, proprietary software, or package registry access.

## Assumptions

- Hermes remains the only production-ready runtime during this implementation slice.
- OpenClaw remains a stub/future provider; this phase proves the seam, not a full engine.
- Workspace service may initially delegate to existing `core.workspace` functions while moving ownership to the new package boundary.
- API response compatibility is more important than deleting every legacy helper in one pass.
- `packages/tool_registry` owns canonical catalog seed data; API migrations may import package-owned seed data while retaining schema and local merge logic.
- Frontend contract generation can begin with domain type files and freshness tests before larger UI decomposition.
- Clean-container Docker execution can be represented by an explicit executor seam and follow-up evidence until a real Docker run is performed by an operator.
