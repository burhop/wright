# ADR 0004: Persist canonical workflow execution as durable lineage

- **Status**: Accepted
- **Date**: 2026-09-01
- **Depends on**: ADR 0002 stable workflow definition; ADR 0003 independent layout authority

## Decision

Adopt `workflow-run` / `1.0.0` as the stable execution-record boundary. A run captures one exact stable workflow ID, revision, and semantic digest. Its mutable projection is limited to lifecycle state, active semantic identities, material/output facts, completion, and cleanup state; it cannot rewrite the definition or layout.

Persist canonical runs in an independent `workflow-runs.sqlite3` sidecar with normalized durable records for:

- immutable run subject identity;
- immutable step attempts, including component-internal semantic scope;
- append-only contiguous activity events and reconnect cursors;
- immutable artifact identity, type, digest, producer, storage reference, and upstream lineage;
- explicit lifecycle-aware artifact cleanup state.

State transitions use compare-and-set expectations and append their activity in the same transaction. The production lifecycle covers queued/running, needs-input/resume, cancellation request/completion, success/failure/block/stale termination, cursor reconnect, and terminal-only idempotent cleanup. Complete projection candidates are revalidated against the exact definition before acceptance.

Cleanup removes only ephemeral artifact storage authority; retained artifact lineage remains retained. Even after cleanup, artifact identity, content digest, producer, upstream lineage, and the cleanup event remain queryable.

## Historical recovery runs

Recovery `workflow-run` / `1.0.0-recovery.1` records are historical evidence, not silently migrated stable subjects. Their exact original bytes, recovery definition revision, and recovery semantic digest are stored in a separate immutable envelope table and returned byte-for-byte. This preserves the pre-promotion definition relation rather than falsely rewriting it to the stable definition digest.

## Schema and rollback

The sidecar schema is checksum-bound and transactional. Run, activity, and step identities are trigger-protected; artifact content identity is immutable while cleanup state may advance. Empty schema rollback is supported. Any canonical or archived recovery run prevents destructive schema rollback.

## Consequences

Execution, reconnect, cancellation, and cleanup are now locally durable without making a runner, MCP binding, external write, or simulated recovery path production-authoritative. The existing primary-database workflow-run tables remain untouched for compatibility. No user database, released installation, package, or customer environment is migrated by this task.
