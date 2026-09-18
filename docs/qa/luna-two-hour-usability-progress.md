# Luna usability work log

Start: 2026-09-18 10:46 America/New_York
Earliest completion target: 2026-09-18 12:46 America/New_York

This log records substantive work only. It is not a claim that the minimum
active-work duration has already been satisfied.

## Activity

- Re-read the review, task brief, workflow UI integration contract, and current
  dirty worktree before editing.
- Confirmed the Codex `access_programs.cyber` HTTP 400 is external to Wright;
  documented it separately without changing local configuration.
- Corrected MCP readiness semantics: `mcp-task` is server-scoped and
  `mcp-tool` is an exact server/tool call.
- Added resolved execution labels to canvas cards for MCP, human, internal, and
  binding-backed work.
- Added request-generation protection around template-readiness refreshes.
- Made the run drawer distinguish requested input from dispatched input. A
  rejected request no longer presents "Prompt sent"; `run_started` or
  `step_started` evidence is required.
- Corrected the workflow-source API regression assertion to use the actual
  top-level `error_code` envelope.
- Focused frontend build passed; focused frontend tests passed after updating
  stale assertions to the evidence-backed execution contract.
- Added server-scoped/exact-MCP binding regression coverage. Latest focused
  result: 46 tests passed in 2 files.
- Added an explicit MCP inventory recheck control and a component regression
  proving a server-scoped task becomes available from the discovered server
  inventory without an exact tool binding. Focused readiness/discovery result:
  64 tests passed in 4 files.
- Replaced substring-based run-error ownership guesses with an explicit known
  backend-code map and an honest unknown-code diagnostic. Added a regression
  for a code containing `tool` that must not be misclassified.
- Removed the redundant oversized inspector delete button; canvas selection plus
  Delete/Backspace remains the deletion path, with the existing confirmation
  flow preserved.
- Full frontend verification now passes: `bun run build`; 152 test files and
  974 tests pass. The latest focused canvas/concept check passes 58 tests and
  the latest build passes. `git diff --check` passes.
- Served verification succeeded with `VITE_WRIGHT_WORKFLOW_RECOVERY=1` at
  `http://127.0.0.1:5173/`: 13 workflow-recovery journeys, 2 engineering-
  template journeys, and 2 keyboard/accessibility journeys passed under
  Chromium with `--no-sandbox`. Retained and inspected screenshot:
  `artifacts/qa/workflow-recovery-20260918/canvas-readiness.png`.
- The final full frontend suite after the latest edits remains green: 152 test
  files and 974 tests passed. The final production build passed.
- Added a synchronous start-operation guard so a rapid second `Save & run`
  click cannot create a second save or dispatch. The delayed-save regression
  now passes with the full workflow concept test file: 44 tests passed. The
  guard also releases on an unexpected save exception.
- Restored the locked Python test environment with `uv sync --extra
  workspace-surfaces-test` using the task-local cache. Focused API contract
  tests now pass: 24 passed, 1 deprecation warning.
- The engineering-scenario API contract slice also passes: 8 passed. A
  broader workflow-integration-run slice initially exposed a Python 3.13
  bounded-executor completion observation problem and was stopped for diagnosis.
- Fixed the bounded executor's filesystem completion path by observing the
  bridged future through a small event-loop polling helper. The previous
  `run_in_executor`/shield path could leave completed filesystem work invisible
  to the event loop in this environment. Added a regression using a real
  workflow-source write. Executor/source/approval tests now pass: 20 passed;
  the full workflow-integration-run API file now passes: 14 passed.
- Replaced the integration test helper's `asyncio.to_thread` filesystem shim
  with the production `WorkspaceFileUseCases`, so the test exercises the same
  bounded file contract as the API instead of hiding the runtime issue.
- Bounded one-worker Vitest investigation: the focused MCP discovery file
  passes with `--maxWorkers=1` (5 passed), but the full frontend suite produced
  no reporter progress and was terminated by its 180-second bound. This is
  recorded as an unresolved test-runner/environment issue, not relabeled as
  fixed by a worker-count workaround.
- Enumerated all ten packaged engineering templates and retained the
  catalog-level readiness/binding/first-blocker matrix at
  `docs/qa/engineering-template-readiness-matrix-2026-09-18.md` without
  executing any template.
- Revalidated the final focused slices after the bounded-executor change:
  65 frontend tests, 21 workspace-service tests, and 14 workflow integration
  API tests passed. The production frontend build also passed; only the
  existing Vite chunk-size warning remains.
- Reopened and visually inspected the retained served-workspace evidence at
  `artifacts/qa/workflow-recovery-20260918/canvas-readiness.png`. It shows the
  canvas-first editor, honest preflight-required readiness, visible input
  connectors, and no implied host/MCP health claim.
- Updated `docs/qa/workflow-recovery-regression.md` so API checks run as
  independent slices and explicitly document the managed Python 3.13
  synchronous `TestClient` stall instead of advertising a misleading combined
  command.
- Added a full-value `title` affordance for long execution/binding identities
  on canvas cards and a regression covering a deliberately long qualified
  server/tool label. The focused canvas and MCP tests pass: 21 tests in 2
  files.
- Re-ran the served entry-point journey after that UI change: all 18
  Playwright tests passed through the workspace Workflows control, including
  new-workflow creation, source/layout save, reconnect/reopen, keyboard and
  200% scale checks, blocked-run behavior, and mobile containment. The local
  Vite process was stopped after verification.
- Wrote the requirement-by-requirement acceptance record to
  `docs/qa/luna-two-hour-acceptance-audit.md`. It clarifies that the canonical
  first-open fixture and the explicit blank New workflow path are different,
  and records the external `access_programs.cyber` organization error as
  outside Wright's repair boundary.
- A bounded broader `packages/workspace_service/tests` pass reached 25 passed
  and then hit the managed host's loopback restriction in
  `surfaces/test_endpoints.py` (`PermissionError: Operation not permitted` on
  socket creation). This is recorded as an environment limitation; the
  executor/source/approval slice that exercises the changed path remains
  green.

## Outstanding

- The served-workspace walkthrough required elevated local binding permission
  and Chromium `--no-sandbox` in this managed environment; with those explicit
  conditions, the journeys passed and the retained screenshot was inspected.
- Delayed readiness/start race coverage is present in component tests; the
  explicit MCP recheck path is now covered as well.
- The API test environment required one approved dependency fetch because the
  locked PyYAML wheel was not cached. The focused endpoint suite is now
  verified; the only warning is Starlette's existing httpx deprecation notice.
- After the bounded-executor change, the synchronous Starlette `TestClient`
  path can hang before returning its first request in this managed Python 3.13
  environment, even for a trivial endpoint. The direct integration-run API
  contract (14 tests), scenario contract (8 tests), executor/source/approval
  slice (20 tests), and earlier focused source/template API run (24 tests)
  remain separately evidenced; do not claim the combined TestClient command is
  green until this environment-level behavior is isolated.
- Backend error-code ownership audit is complete for the frontend boundary.
  Template catalog/readiness facts were inspected without executing templates;
  the resulting matrix is retained separately.
- The requirement-by-requirement audit is complete for the scoped usability
  fixes. The remaining API `TestClient` stall is an environment/test-harness
  condition with a documented owner/action; it is not silently treated as a
  product pass.
