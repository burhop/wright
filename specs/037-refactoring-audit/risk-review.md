# Pre-Implementation Risk Review

## Production Risk

- **High**: API boot currently instantiates Hermes directly. Mitigation: add registry behind existing Hermes default and verify health behavior before moving any broader agent logic.
- **High**: MCP route extraction touches install, validation, credentials, and update behavior. Mitigation: split by operation group, keep route response models, and add service tests before route rewiring.
- **Medium**: Gateway naming and context writing could break Hermes Desktop workflows. Mitigation: keep Hermes-compatible `wrightgateway` config behind a Hermes adapter and add compatibility tests.
- **Medium**: Catalog normalization could alter sort order or metadata defaults. Mitigation: parity tests across tested, might-work, blocked, and non-working entries before replacing loaders.

## Migration Risk

- Additive interfaces and compatibility wrappers reduce migration risk.
- No database migration is planned for Phase 1 or Phase 2.
- Catalog normalization must not remove existing seed fields until parity is proven.
- Validation evidence abstractions should not mark existing catalog entries newly tested without executed evidence.

## Test Coverage

Required coverage before implementation is considered safe:

- Agent registry unit tests and API health tests.
- Gateway contract tests and Hermes compatibility tests.
- MCP service tests plus existing API route regression tests.
- Catalog normalization/parity tests.
- Validation plan/evidence tests with lightweight mock MCP server.
- System smoke tests for API health, default agent behavior, MCP listing, and Wright gateway happy path.

## Rollback Strategy

Each phase must be revertible as a coherent commit. The highest-risk fallback is to preserve existing Hermes paths and API route behavior while disabling new shared abstractions through local wiring. No phase should require data deletion for rollback.

## API Compatibility

No breaking API changes are planned. If implementation requires changing response fields, HTTP statuses, or public route paths, stop for approval before applying that change.

## Ambiguity Review

No blocking ambiguity remains for Phase 1. For later phases, this plan resolves the audit's ownership questions as follows:

- Gateway profile contracts: `packages/agent_adapters`.
- MCP gateway runtime, catalog normalization, validation plan/evidence: `packages/tool_registry`.
- HTTP translation: `apps/api`.
- Hermes plugin remains first-class and consumes shared contracts where practical.

## Phase Checklist

- [x] Phase 1: registry-backed agent runtime selection with Hermes default.
- [x] Phase 2: Wright gateway contracts with Hermes compatibility and OpenClaw
  seam.
- [x] Phase 3: thin MCP API routes backed by service-layer operations.
- [x] Phase 4: shared catalog normalization with `hermes-plugin-wright` as a
  package consumer.
- [x] Phase 5: validation plan/evidence seam with clean-container execution
  kept opt-in.
- [x] Phase 6: offline E2E smoke coverage for constitution-required flows.

## Implementation Boundary Summary

- Agent runtime selection now lives in `packages/agent_adapters`; API boot asks
  the registry for the default Hermes engine.
- Wright gateway contracts live in `packages/agent_adapters`, with Hermes
  compatibility wrappers preserved in `apps/api`.
- MCP route business logic moved into `packages/tool_registry.services` plus an
  API translation service; route response models remain unchanged.
- Catalog defaults and normalization now live in `packages/tool_registry`;
  `hermes-plugin-wright` consumes that shared loader while keeping its plugin
  APIs.
- Validation plan/evidence abstractions are additive and offline-safe by
  default; Docker/network validation remains operator-invoked.
- E2E smoke coverage uses temporary SQLite state and fake/mock paths only.

Rollback remains commit-scoped: each implemented phase can be reverted
independently. The highest-risk fallback remains restoring the previous Hermes
wrapper and route-local MCP logic while keeping database state intact.
