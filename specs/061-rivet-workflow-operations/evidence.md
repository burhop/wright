# Evidence — Rivet Workflow Operations

## Traceability

| Requirement | Evidence |
|---|---|
| RQ-01 file authority | `WorkspaceWorkflowStore` is read before review/start; `WorkflowReviewRepository` has no project or dataset columns. |
| RQ-02 exact approval | `test_operations_require_current_approved_review_and_preserve_scope` and `test_saved_workflow_invalidates_previous_review`. |
| RQ-03 optional behavior | `WorkflowOperationsSettings` and API config default off; `test_operations_are_default_disabled`; API flag test. |
| RQ-04 isolation | Operations checks workspace and session before status/history/cancel; focused scope assertion. |
| RQ-05 migration safety | Migration 11 plus `test_workflow_review_migration_preserves_prior_workflow_metadata`. |
| RQ-06 workspace UI | `RivetWorkflowsPanel` catalog/review/run/history/cancel controls; `npm --prefix apps/web run build`. |

## Commands and results

On 2026-08-03:

- `uv run ruff check …` — passed.
- Focused data-vault/workspace-service/API tests — 27 passed, one upstream
  Starlette deprecation warning.
- `npm --prefix apps/web run lint` — no errors; one pre-existing
  `ModelSetupPage` hook-dependency warning.
- `npm --prefix apps/web run build` — passed; existing Vite large-chunk warning.
- `npm --prefix apps/web run test` — 58 files / 223 tests passed; two unrelated
  `AuthGate` tests fail under Node 25 because `localStorage` requires a
  `--localstorage-file` path. This is a host test-environment limitation,
  not a Rivet assertion failure.

## Rollback and remaining risks

Disabling `WRIGHT_RIVET_WORKFLOW_OPERATIONS_ENABLED` removes the API surface
without changing ordinary workspace behavior. The additive migration can remain
unused on rollback; it does not alter authored files or existing workflow index
records. The runner still executes only the supervised fixture until release
hardening supplies a verified packaged Rivet runtime. The editor remains
unavailable until a verified local bundle is installed. Durable run/audit
retention and production Rivet-node execution remain release-hardening work.
