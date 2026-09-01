# T054 durable workflow execution evidence

**Date**: 2026-09-01

**Decision**: [ADR 0004](../decisions/0004-durable-workflow-execution-records.md)

**Stable contract**: `workflow-run` / `1.0.0`

**Exact stable definition subject**: revision 1 / `cf89b3b0c0875bc691e901b3ec9ac2b2170fc508e0d356e9040200f4049cc73a`

**Historical recovery subject retained**: revision 1 / `57ed2b7caacc9b3a779d9e960a681a9b8fe6dc1cfc9c3d48fa6ddd5e184be889`

**Execution schema migration checksum**: `1816813c50437ca2278c9a66612375c28cc282ff45139fa8c72b4ca9890bd640`

## Verified behavior

- Run creation binds exact workflow identity, revision, and semantic digest without changing definition bytes.
- Complete projection transitions retain active block/relationship identity and material/output facts while using state compare-and-set.
- Needs-input/resume and both queued and running cancellation paths append complete ordered activities atomically.
- Step attempts retain input/output artifact IDs, diagnosis codes, and validated component-internal addresses.
- Artifact records validate contract/type/media/producer/actions and retain content digest, storage reference, and upstream lineage.
- Reconnect returns the current run, all step/artifact records, only activities after the requested cursor, and the latest cursor.
- Cleanup is terminal-only and idempotent. It advances ephemeral artifacts to cleaned while preserving retained artifacts and every lineage fact.
- Exact historical recovery-run bytes and their original recovery semantic digest are archived immutably rather than rewritten to the stable digest.
- The independent `workflow-runs.sqlite3` sidecar does not create or mutate the primary, definition, or layout databases.
- Stored envelope/column mismatches and forged identity mutations fail closed.
- The checksum-bound schema upgrades transactionally, rolls back only while empty, and refuses rollback if either canonical or archived recovery runs exist.

Focused execution verification:

```text
pytest packages/core/tests/test_canonical_workflow_runs.py
       packages/data_vault/tests/test_canonical_workflow_run_repository.py
16 passed in 1.42s
```

Broad retained production verification:

```text
pytest packages/core/tests packages/data_vault/tests
243 passed, 1 skipped, 8 warnings in 21.02s
```

Ruff format/check and `git diff --check` pass. The retained skip is unchanged. The eight warnings are pre-existing Python 3.16 deprecation notices from `core/tracing.py:72`, not execution-boundary warnings.

This task adds durable records and lifecycle behavior only. It does not invoke a runner, MCP tool, external write, customer action, package, release, or benchmark, and it does not change customer readiness.

The refreshed dashboard verifier passed at `2026-09-01T04:22:37.803Z` with
54/60 recovery tasks, the visible T054 lifecycle/lineage checkpoint, exact
approved product subject metadata, eight loaded evidence images, zero browser
diagnostics, zero desktop/mobile overflow, evidence HTTP checks at 200,
traversal checks at 403, and customer readiness still false.
