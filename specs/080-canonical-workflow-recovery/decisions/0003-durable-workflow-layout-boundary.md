# ADR 0003: Persist workflow layout as an independent durable authority

- **Status**: Accepted
- **Date**: 2026-09-01
- **Depends on**: ADR 0002 stable workflow definition boundary

## Decision

Promote the approved renderer-neutral layout contract to `workflow-layout` / `1.0.0` and persist it independently from definitions, runs, source text, and renderer-vendor state.

The stable layout contains only `workflow_id`, the exact `semantic_revision` it targets, its independent `layout_revision`, stable block-ID keyed positions, and viewport coordinates/zoom. Every write validates the workflow identity, accepted semantic revision, referenced block IDs, finite bounded coordinates, and positive bounded zoom against a complete stable definition. A layout edit cannot mutate definition bytes or semantic digest.

The approved recovery layout `1.0.0-recovery.1` is an explicit migration source. Migration validates the complete recovery document and target definition, changes only the schema version, and records exact source bytes plus source and target digests. Unsupported versions are returned as recoverable decode results with their original bytes and are never silently rewritten.

## Persistence and concurrency

Layouts use their own `workflow-layouts.sqlite3` sidecar. Immutable revision rows record layout ancestry and semantic-revision binding; a compare-and-set head prevents stale writers. Stored envelope, row identity, ancestry, and head digests are rechecked on reopen. Update and delete triggers protect history.

The sidecar schema upgrades transactionally. An empty sidecar may roll back to version zero. A populated sidecar refuses destructive schema rollback; the initially promoted layout may instead return its exact recovery source envelope after digest verification.

## Consequences

Definitions can advance without rewriting historical layouts, and layout revisions can advance without changing semantic content. Renderers receive stable semantic IDs but do not own layout persistence. Durable run/activity/artifact state remains separate and deferred to T054. No user database or released installation is migrated by this task.
