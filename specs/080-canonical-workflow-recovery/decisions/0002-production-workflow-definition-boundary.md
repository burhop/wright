# ADR 0002: Promote the canonical workflow-definition boundary

- **Status**: Accepted
- **Date**: 2026-09-01
- **Supersedes for production promotion**: the no-production-migration decision in ADR 0001
- **Approved source**: commit `f9237763d6fa6e9748dfb7b713e753a7fc4b4d17`, tree `aeca6ab8294dd54112d3e9ac10148537af32b0f0`, walkthrough manifest SHA-256 `f2b4964ec1f599b55a8a8d53704147d2133674baa5db9a28072d4a2808c57347`
- **Human direction**: the requesting user approved the reviewed product and visual direction and authorized T052 in the message recorded by `evidence/product-approval.md`; no reviewer name or review timestamp was supplied and none is inferred.

## Decision

Promote only the approved renderer-neutral definition, validation, atomic command, semantic-diff, and projection concepts into production Python boundaries.

- The stable definition contract is `workflow-ir` / `2.0.0`.
- The stable command contract is `workflow-command-batch` / `1.0.0`.
- `2.0.0-recovery.1` is accepted only as an explicit migration source. It is never silently decoded as stable production input.
- The migration is pure and deterministic. It validates the source kind/version and any declared source semantic digest, changes only the schema version and semantic digest, validates the complete stable candidate, and records source and target digests.
- The stable definition excludes layout, selection, diagnostics, source text, proposal state, renderer-vendor state, and run state.
- Projection models expose only stable semantic IDs and renderer-neutral node, port, and relationship facts. React Flow remains an implementation detail and is not imported into the production authority.
- Atomic command application builds and validates a complete candidate. A stale base, unsupported command, or invalid candidate returns diagnostics without changing the accepted definition. Acceptance creates exactly one child revision.

## Persistence and migration

Canonical definitions use an independent `workflow-definitions.sqlite3` sidecar with an append-only revision table and compare-and-set head. The existing primary database and `workflow-drafts.sqlite3` remain untouched.

The first promoted revision may retain one exact source envelope with its document kind, schema version, and SHA-256:

- recovery `workflow-ir` / `2.0.0-recovery.1` bytes; or
- legacy `workflow-draft` / `1.0.0-draft.1` bytes.

Unknown source versions fail before any database write. Stored definition and source-envelope digests are rechecked when read. Revisions cannot be updated or deleted. A populated definition schema refuses destructive schema rollback; an empty schema may roll back transactionally to version zero.

## Rollback policy

Before the promoted target changes, rollback returns the exact retained source bytes after verifying both source and target digests. Once a stable target has changed, the original migration helper refuses semantic rollback because rewriting newer history into an older contract would be lossy. Ordinary stable revisions remain append-only and are recovered by selecting a known revision, not by mutating history.

No user database is migrated by this task. Tests create temporary sidecars only. Packaging, installation, release, and customer migration remain downstream gates.

## Deferred boundaries

Durable layout and run/activity/artifact stores remain T053 and T054. Historical runs must keep their original definition revision and digest; T054 must prove that invariant rather than rewrite them. The recovery DSL, proposal UI, React Flow renderer, simulated run, large-graph behavior, and accessibility/qualification work are not promoted by this ADR.

## Consequences

Wright now has a stable, fail-closed semantic authority and an exact reversible bridge from the approved recovery subject without granting production authority to its disposable presentation code. Layout and execution can evolve independently behind their own versions and migrations.
