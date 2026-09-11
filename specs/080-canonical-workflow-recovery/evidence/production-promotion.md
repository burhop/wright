# T052 production promotion evidence

**Date**: 2026-09-01

**Decision**: [ADR 0002](../decisions/0002-production-workflow-definition-boundary.md)

**Approved product subject**: `f9237763d6fa6e9748dfb7b713e753a7fc4b4d17` / tree `aeca6ab8294dd54112d3e9ac10148537af32b0f0`

**Scope**: local production definition/kernel/projection boundary and independent definition persistence only; no user database, push, merge, package, release, or customer action

## Promoted boundary

- `core.workflow_definitions` owns the closed stable `workflow-ir` / `2.0.0` models, complete semantic validation, canonical digest, strict decoding, atomic command application, one-revision acceptance, semantic diff, renderer-neutral projection, legacy-draft promotion, recovery-to-stable promotion, and exact-source rollback checks.
- `data_vault.workflow_definition_repository` owns an independent `workflow-definitions.sqlite3` sidecar, checksum-verified transactional schema migration, append-only immutable revisions, compare-and-set heads, bounded envelopes, exact source-envelope retention, corruption containment, and empty-only schema rollback.
- Layout, renderer state, source text, AI proposal state, and run/activity/artifact state are absent from the stable definition. React Flow is absent from the projection and production Python dependencies.
- Existing `workflow-drafts.sqlite3` and the primary database are not opened by definition creation. Test assertions verify this separation.

## Exact migration facts

| Fact                                 | Value                                                              |
| ------------------------------------ | ------------------------------------------------------------------ |
| Recovery source kind/version         | `workflow-ir` / `2.0.0-recovery.1`                                 |
| Stable target kind/version           | `workflow-ir` / `2.0.0`                                            |
| Stable command kind/version          | `workflow-command-batch` / `1.0.0`                                 |
| Exact recovery envelope SHA-256      | `ffea183fc1dfe6dff86ef810930a733202e60a7ae6293ce06af759cd2795a76c` |
| Recovery semantic SHA-256            | `57ed2b7caacc9b3a779d9e960a681a9b8fe6dc1cfc9c3d48fa6ddd5e184be889` |
| Stable semantic SHA-256              | `cf89b3b0c0875bc691e901b3ec9ac2b2170fc508e0d356e9040200f4049cc73a` |
| Definition schema migration checksum | `31cffed83389eaca520491621660f79cd8d7e969e14382cb5222d219454161a1` |

The source and target semantic digests differ because the version is part of canonical definition bytes. The exact source envelope remains byte-for-byte recoverable while the target digest remains unchanged. A false declared source digest, unknown source version, changed target, corrupted stored target, or corrupted rollback envelope fails closed.

## Verification

Focused production and retained-draft suite:

```text
pytest packages/core/tests/test_workflow_definitions.py
       packages/data_vault/tests/test_workflow_definition_repository.py
       packages/data_vault/tests/test_workflow_draft_repository.py
21 passed in 1.32s
```

Broad retained core/data-vault suite:

```text
pytest packages/core/tests packages/data_vault/tests
216 passed, 1 skipped, 8 warnings in 18.05s
```

The skip is retained suite behavior. The eight warnings are existing Python 3.16 deprecation notices from `core/tracing.py:72`; no warning originated in the promoted boundary. Ruff formatting and lint both passed. `git diff --check` passed.

The refreshed dashboard verifier passed at `2026-09-01T03:59:27.914Z` with
52/60 recovery tasks, the visible T052 production-boundary checkpoint, exact
approved subject metadata, eight loaded evidence images, zero desktop/mobile
overflow, zero browser diagnostics, all evidence links returning 200, both
traversal probes returning 403, and customer readiness still false. Two stale
verifier literals encountered during refresh are preserved in
`artifacts/dashboard-recovery-verification/t052-first-run-failure.md`.

The Spec Kit implementation preflight helper could not start Bash on this Windows host (`CreateInstance/E_ACCESSDENIED`). This did not bypass a substantive gate: the feature checklist was read directly and remained 16/16 complete, and all relevant Python checks above ran locally. The optional pre/post implementation hook is a local Git commit; this evidence is included in the coherent T052 checkpoint commit.

## Deferred verification

T053 owns durable layout/reopen/version/CAS behavior. T054 owns durable run, step, activity, artifact, cancellation, reconnect, cleanup, and historical definition-reference behavior. This checkpoint makes no claim that either boundary is complete and does not alter customer readiness.
