# Research: Wright Architecture Refactoring Phase 2

## Decision: Introduce `packages/workspace_service` As A Facade First

**Rationale**: `apps/api/src/api/routers/workspace.py` and `packages/core/src/core/workspace.py` still own a mix of route translation, filesystem, SQLite, subprocess, session, and Hermes context behavior. A facade lets routes delegate immediately while preserving the existing response contract and avoiding a big-bang rewrite.

**Alternatives considered**:

- Move all workspace storage and git behavior into the new package immediately. Rejected because the route surface is large and API compatibility risk is high.
- Keep using `core.workspace` directly. Rejected because Phase 2 needs a package boundary that future services and import-boundary tests can enforce.

## Decision: Agent Context Materialization Lives In `agent_adapters`

**Rationale**: Agent-specific workspace context files belong to provider code. Hermes materializes `.hermes.md`; OpenClaw may materialize a different file or no file. The contract should expose provider ID, support level, written files, and safe warnings without forcing generic code to know provider paths.

**Alternatives considered**:

- Keep `.hermes.md` writes in `core.workspace`. Rejected because it makes Hermes the generic workspace model.
- Put materializers in `workspace_service`. Rejected because provider-specific context is an adapter responsibility.

## Decision: MCP Safety Policy Is A `tool_registry` Domain Service

**Rationale**: Install/start/call decisions depend on catalog risk, installability, credentials, network requirements, and approval state. Those fields are owned by registry models, and policy must be enforced outside the UI.

**Alternatives considered**:

- Enforce only in API routes. Rejected because gateway and package callers could bypass policy.
- Enforce only in frontend. Rejected because local tools and API clients need the same safety boundary.

## Decision: Validation CLI Ships With Mock And Docker Executor Seams

**Rationale**: Fast tests must stay offline and Docker-free. The CLI can build plans, run a mock executor in tests, and write redacted evidence. The Docker clean-container executor remains explicit and must not report success unless it actually runs.

**Alternatives considered**:

- Run Docker from API routes. Rejected because validation can involve package installs, network, credentials, cancellation, and proprietary dependency diagnostics.
- Treat metadata preflight as final validation. Rejected by the clean-container process.

## Decision: JSON Evidence Is Canonical, Markdown Is A Review Summary

**Rationale**: Automation needs structured records; maintainers need readable problem summaries. Both outputs must be redacted from the same shared helper.

**Alternatives considered**:

- Markdown only. Rejected because it is harder to contract-test and consume from API/UI.
- JSON only. Rejected because the current catalog process uses human-readable follow-up records.

## Decision: `X-Trace-Id` Remains A Wright Correlation ID

**Rationale**: Existing API clients use `X-Trace-Id` for support and UI correlation. OpenTelemetry already has canonical trace/span identifiers. Phase 2 clarifies that `trace_id` and `span_id` are OTel fields, while `wright.correlation_id` is the user-visible request correlation value.

**Alternatives considered**:

- Treat `X-Trace-Id` as the OTel trace ID. Rejected because Wright has not adopted full W3C trace-context propagation and existing values may not be valid OTel trace IDs.

## Decision: Generated TypeScript Contracts Start As Checked-In Domain Types

**Rationale**: The fastest drift guard is a deterministic offline generator that emits TypeScript interfaces for selected Pydantic models and policy/evidence contracts. After the generated contracts land, targeted component extraction can reduce the largest UI hotspots without a broad redesign.

**Alternatives considered**:

- Rewrite all UI components first. Rejected because broad UI work is higher blast radius; Phase 2 uses targeted extractions for high-churn sections.
