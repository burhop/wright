# T053 durable layout persistence evidence

**Date**: 2026-09-01

**Decision**: [ADR 0003](../decisions/0003-durable-workflow-layout-boundary.md)

**Scope**: local stable layout model/migration plus an independent append-only layout sidecar; no user database, renderer authority, run authority, push, merge, packaging, release, or customer action

## Exact contract and migration facts

| Fact | Value |
|---|---|
| Recovery source | `workflow-layout` / `1.0.0-recovery.1` |
| Stable target | `workflow-layout` / `1.0.0` |
| Exact recovery envelope SHA-256 | `d9a00d06b1e17c9110b00ffde84f1615727f8153ecbf5e11f849f97d44bd141c` |
| Canonical recovery layout SHA-256 | `da7ff235ea589595c81891b14cb1d258bfd32cb0f6e243a5f71b93c7ac6998f1` |
| Stable layout SHA-256 | `d72651396a9704227edd0d22bb897b0259fd0b08a65da20207f21cf48b23c6a1` |
| Layout schema migration checksum | `ba8776cfddec03bdd3bcac86e8e2a5e5070b949cadc6519142730292010c0937` |

The committed `mounting-bracket.layout.json` fixture is the exact layout used by the approved React Flow subject. Promotion preserves all workflow, revision, position, and viewport facts while changing only the version boundary. The source bytes remain exactly recoverable while the target digest is unchanged.

## Verified behavior

- Complete subject validation rejects workflow/revision mismatch and unknown semantic IDs before storage.
- Stable reopen verifies the exact envelope, layout digest, row identity, ancestry, and current head.
- Unknown versions reopen as structured diagnostics with the exact original bytes and no rewrite.
- Layout revisions are append-only and advance through compare-and-set; a stale writer fails without adding a revision.
- Layout-only edits leave the stable definition bytes unchanged.
- Forged promotion digests and corrupted stable or recovery envelopes fail closed.
- `workflow-layouts.sqlite3` is independent from the primary, draft, and definition databases.
- The schema migration is checksum-bound and transactional; rollback succeeds only while the sidecar is empty.

Focused layout verification:

```text
pytest packages/core/tests/test_workflow_layouts.py
       packages/data_vault/tests/test_workflow_layout_repository.py
11 passed in 0.65s
```

Broad retained production verification:

```text
pytest packages/core/tests packages/data_vault/tests
227 passed, 1 skipped, 8 warnings in 15.47s
```

Ruff format/check and `git diff --check` pass. The retained skip is unchanged. The eight warnings are pre-existing Python 3.16 deprecation notices from `core/tracing.py:72`, not layout-boundary warnings.

The refreshed dashboard verifier passed at `2026-09-01T04:08:46.156Z` with
53/60 recovery tasks, the visible T053 checkpoint, exact approved product
subject metadata, eight loaded evidence images, zero browser diagnostics, zero
desktop/mobile overflow, evidence HTTP checks at 200, traversal checks at 403,
and customer readiness still false. The desktop capture was visually inspected.
