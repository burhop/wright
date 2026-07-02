# Phase 0 Research: Architecture Refactoring Audit Implementation

## Decision: Agent runtime registry lives in `packages/agent_adapters`

**Rationale**: The constitution already identifies `agent_adapters` as the adapter-pattern boundary for Hermes, OpenClaw, PI, and future engines. API boot should depend on provider metadata and factories, not on concrete Hermes imports.

**Alternatives considered**: Keeping selection in `apps/api` preserves current behavior but continues the hardcoding problem. Creating a new package would add overhead before there is evidence that `agent_adapters` cannot own the surface.

## Decision: Hermes remains the default provider

**Rationale**: Hermes is the only fully implemented runtime in this feature. Defaulting through the registry preserves current behavior while making future runtime support additive.

**Alternatives considered**: Requiring explicit runtime configuration would be a user-facing behavior change and would weaken existing setup flows.

## Decision: Wright gateway contracts live in `agent_adapters`, with MCP protocol runtime support in `tool_registry`

**Rationale**: Gateway profiles describe how an agent consumes Wright's gateway. The actual MCP server/proxy mechanics already live in `tool_registry.gateway` and API gateway routes.

**Alternatives considered**: Keeping contracts in Hermes plugin would overfit to Hermes. Putting all gateway code in `tool_registry` would blur agent runtime profile ownership.

## Decision: API routes stay backward compatible and service extraction is incremental

**Rationale**: `apps/api/src/api/routers/mcp.py` currently owns many behaviors. Moving one operation group at a time keeps review small and lets existing route tests guard public contracts.

**Alternatives considered**: A full rewrite would reduce duplication faster but creates unacceptable production and migration risk.

## Decision: Shared catalog normalization starts in `packages/tool_registry`

**Rationale**: `tool_registry` already owns MCP models, database persistence, installability sorting, validation classification, runners, and gateway proxy behavior. It is the most natural shared package for API and plugin consumers.

**Alternatives considered**: Making `hermes-plugin-wright` canonical would keep plugin behavior strong but make the whole product Hermes-shaped. Keeping both sources independent keeps drift risk.

## Decision: Validation evidence is structured first, Markdown second

**Rationale**: Structured validation plans/evidence can be tested, persisted, normalized, and consumed by UI/API later. Existing Markdown follow-up records remain useful for human-readable problem logs.

**Alternatives considered**: Markdown-only evidence is easy to review but hard to validate automatically. JSON-only evidence loses the narrative problem log required by the testing process.

## Decision: Default tests remain local and network-free

**Rationale**: Offline-first behavior is a constitutional requirement. Clean-container, package-manager, network, credentialed, and proprietary host validation must be explicit opt-in workflows.

**Alternatives considered**: Running Docker validation by default would increase confidence but would break fast local development and many offline machines.

## Decision: No breaking API changes are planned

**Rationale**: The audit requests route thinning and service boundaries, not response redesign. Existing API tests and plugin bridge tests define the compatibility baseline.

**Alternatives considered**: Introducing new route response envelopes would simplify some service errors but would require explicit contract approval and coordinated UI/plugin changes.

