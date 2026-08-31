# Proposed Decision 0001: Provisional Draft Authoring Boundary

- **Status**: Proposed; requires exact human planning and implementation approval
- **Date**: 2026-08-31
- **Feature**: EPP-F02B / spec 079
- **Related**: `DEC-P0-002`, ADR 0021, LL-010, LL-017, LL-025

## Context

ADR 0021 approved only an immutable EPP-F02 definition and explicitly excluded editing, persistence, round-trip, migration, and Apply. EPP-F02B needs a small authoring slice without presenting a provisional syntax or renderer as the permanent platform.

## Proposed decision

Use a distinct, closed `workflow-draft` `1.0.0-draft.1` contract with separate semantic and integer-grid layout identities. Accept edits only after complete candidate validation. Save immutable revisions atomically in a feature-owned SQLite sidecar using compare-and-set revision identity. Expose a distinct default-off API and browser route. Render through a projection-and-intent adapter with one first-party SVG/HTML renderer and complete text fallback.

The released EPP-F02 schema, bytes, GET endpoint, ETag, source identity, page, and feature flag remain unchanged. There is no release, publish, execution, MCP, LLM, benchmark, or Rivet authority.

## Compatibility and rollback

- Reader and writer support exactly `1.0.0-draft.1`; unknown versions fail safely and are never rewritten.
- Disabling/removing the feature hides navigation, rejects draft API access, and leaves the sidecar inert.
- The prior Wright binary ignores the sidecar because the main database schema is unchanged.
- Update, rollback, and uninstall do not delete drafts or touch released definitions.
- User-facing revision restore and draft migration are deferred.

## Consequences

This adds a small feature-specific persistence boundary but avoids main-schema rollback coupling, renderer lock-in, and Rivet reuse. It does not close `DEC-P0-002`; permanent syntax, Apply/release, LLM editing, and migration remain blocked pending their required studies and superseding decision.

## Rejected alternatives

- Mutate or extend the released EPP-F02 contract.
- Reuse Rivet or frozen prototype implementation/types.
- Store authoritative drafts only in the browser.
- Add a main-database migration for this bounded slice.
- Add React Flow or a generic renderer/plugin registry now.

