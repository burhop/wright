# Slice 057 verification evidence

**Branch:** `057-rivet-headless-runner`
**Umbrella base:** `af7c54a`
**Recorded:** 2026-08-03

## Passing checks

- Focused runner, core, and API-gate tests: `11 passed` (one unrelated
  FastAPI/TestClient deprecation warning).
- Runner live fixture: included in the focused result and executed through the
  Windows Job Object adapter. It launches a long-running Node child, cancels it
  with the two-second deadline, and verifies the adapter reports complete
  cleanup.
- Broader regression: `packages/workspace_service/tests` plus
  `apps/api/tests/test_workspace_api.py`: `230 passed, 5 skipped`. The skips
  are existing platform capability skips.
- Ruff: passed for every changed Python source and test file.
- Focused mypy: passed for `core.workflow_runs` and
  `workspace_service.workflow_runner`.

## Required behavior covered

| Requirement | Evidence |
|---|---|
| Default-disabled and missing optional runtime | feature-flag and runner absence tests |
| Immutable workflow identity/revision/digest snapshot | runner unit test and launch event |
| Generation/session-scoped start/status/cancel | runner unit tests and typed API contracts |
| Bounded lifecycle events and bounded raw logs | runner limit test; `ProcessSupervisor` log buffer |
| Process-tree cleanup and cancellation deadline | live Node fixture through Windows Job Object |
| Concurrency and restart reconciliation | runner unit test |
| No graph/tool/debugger authority | inert fixture source review and no authority inputs |

## Known limitations and rollback

- Slice 055's Windows offline Yarn cache lacks upstream platform artifacts.
  Accordingly, this slice proves a Node lifecycle fixture only; it does **not**
  claim an installed/offline `@ironclad/rivet-node` execution bundle. Release
  hardening must close that packaging gate.
- A full repository mypy invocation remains red from pre-existing untyped
  packages, missing third-party stubs, and unrelated Surface annotations. The
  added runner/core modules pass their focused check; no broad type-cleanliness
  claim is made.
- The Spec Kit prerequisite script auto-selected historical `055` on this host
  despite the active `057` branch, so the cross-artifact review used the
  explicit slice paths below. This is tooling discovery behavior, not a runner
  failure.
- Roll back by setting `WRIGHT_RIVET_RUNNER_ENABLED=0`; no authored workflow
  file or migration is changed. Service shutdown cancels owned runner children.

## Cross-artifact review

`spec.md`, `plan.md`, `tasks.md`, data model, contracts, and research were
reviewed against the constitution and umbrella plan. The only material
alignment decision was to make durable run history explicitly deferred to the
workflow-operations slice; task T003 and the data model now state that scope.
There are no unresolved core-requirement coverage gaps for this lifecycle-only
slice.
