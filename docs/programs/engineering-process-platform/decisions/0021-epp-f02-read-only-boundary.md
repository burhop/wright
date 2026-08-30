# ADR 0021: EPP-F02 read-only interchange boundary

- Decision ID: `DEC-P0-002` (bounded EPP-F02 disposition only)
- Status: accepted for the removable EPP-F02 read-only boundary
- Date: 2026-08-30
- Owner / human approver: human architecture approver
- Exact subject and evidence digests: `APR-EPP-F02-MC-001` and `APR-EPP-F02-IMPL-001` bind reconciled commit `fd93daf6d5826da436f394ab1afb9298f5e8a32b`, tree `38cbb5c63b1f11303b6c9569de0c3c0e6f9b0b93`, program tree `09dc3d4506119e755504223fcf32586e28290cf3`, and the 20 reviewed planning artifacts; original approved planning identity `5f2aa529f28dccde9eb797afa33af2b5d8f47440` / `fac8ffde45bc88989956346babff80b28fa911bf` remains an ancestor
- Decision due gate: EPP-F02 material-change and feature-implementation approval

## Context and claims affected

The original question combines two decisions: an immutable representation that a read-only product view can consume, and a future editable syntax/validation/Apply experience. Requiring authoring studies before a read-only customer view delays customer learning without reducing authoring risk.

## Decision drivers

- Put a customer-visible process view in Wright before building an editor.
- Keep text and diagram on one semantic identity.
- Avoid persistence, migration, Apply, round-trip, or syntax commitments.
- Use existing dependencies and preserve removability.

## Options considered

1. Wait for the full edit/round-trip study before any process view.
2. Treat JSON as both permanent authoring syntax and interchange.
3. Use one versioned immutable JSON document only as EPP-F02's bundled read-only interchange contract; defer all authoring choices.

## Evidence and contradictions

The prototype supplies read-only experimental evidence but cannot choose production architecture. The initial architecture and commercial audits failed the broader JSON-plus-Apply proposal because the required authoring studies were absent. Their smallest safe correction was to narrow EPP-F02 to option 3 or obtain the full studies first. This ADR adopts that proposed correction; it does not convert the failed audit into a pass or close the remaining authoring decision.

## Decision

Accept option 3. EPP-F02 may read one immutable packaged `1.0.0` JSON definition and derive text/diagram projections. It may not edit, round-trip, persist, migrate, or Apply. Acceptance of the exact EPP-F02 subject removes only EPP-F02 from `DEC-P0-002.blocks`; `DEC-P0-002` remains open and blocks EPP-F06 until its human/LLM edit study, invalid-edit/round-trip evidence, compatibility/migration analysis, and a superseding accepted ADR exist.

## Consequences and residual risks

The first product increment can be demonstrated quickly. The JSON structure may later be adapted or migrated by EPP-F06; EPP-F02 creates no user-authored or persisted data, so replacement is deletion plus route removal. The read-only schema must not be advertised as permanent authoring syntax.

## Compatibility, migration, rollback, and expiry

No migration exists. Rollback removes the feature flag, route, packaged sample, reader, and API. This disposition expires if EPP-F02 adds any authoring or persistence behavior.

## Gate, roadmap, risk, and approval invalidation

On exact acceptance, T001 updates the decision register, EPP-F02 roadmap eligibility, program state, source catalog, work registry, and dashboard atomically. Readiness and benchmark results do not change. The residual authoring risk stays controlled by open `DEC-P0-002`; no separate risk row is needed unless EPP-F06 planning starts or scope expands.
