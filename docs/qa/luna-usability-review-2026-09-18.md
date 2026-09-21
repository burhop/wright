# Review of the Luna workflow usability pass

Review date: 2026-09-18. Scope: current uncommitted changes and their implementation dependencies. This is a source review; the previous test results were inspected as historical evidence, not rerun or independently certified. Product code was not changed during this review.

## Findings

1. **P1: Server-scoped AI MCP tasks are incorrectly marked unbound and unavailable.** `AuthoringControls.tsx:55` requires both `mcp_server` and `mcp_tool`, and its availability check compares an exact tool name. `createMcpServerBlock` deliberately creates `mcp-task` with only a server, and `McpTaskOptions` lets the AI choose operations from that server. This is a distinct supported mode, not a legacy spelling of `mcp-tool`. A correctly configured ordinary MCP task therefore receives false corrective guidance. Test the actual server-block factory through readiness and the inspector.

2. **P2: Canvas binding labels do not identify the executing tool reliably.** `ReactFlowRecoveryCanvas.tsx:459` displays an internal binding ID rather than resolving `workflow.bindings[].toolId`, labels server-scoped MCP tasks `Not bound`, and also labels human review components `Not bound`. Engineers still cannot determine the actual integration from the card. Resolve the execution mode and its saved target explicitly, with human review and internal execution labeled appropriately.

3. **P2: Qualification refresh can overwrite the current workflow's readiness with an old request.** `WorkflowRecoveryPage.tsx:243` has no request-generation or scope guard for manual refresh, unlike the effect above it. A slow refresh for workflow A can resolve after workflow B is opened, changing B's readiness or client run block. Multiple refreshes can also resolve out of order. Bind results to workspace/session/path/source identity and invalidate prior requests.

4. **P2: Preflight rejection still implies execution in the run drawer.** `WorkflowRecoveryConcept.tsx:2694` captures the first AI prompt and assigns a start time before the run API accepts execution. `NativeRunPanel` renders `Prompt sent to` at line 935 whenever that time exists, including after an HTTP preflight rejection. Only the newly added early template check avoids this path. The drawer also calls early template rejection `Run failed`. Preserve separate requested, rejected, accepted, step-started, failed and cancelled states, driven by execution evidence.

5. **P2: The added API regression test uses the wrong public error envelope.** `test_workflow_sources_api.py:702` indexes `detail.code`, but the application exception handler at `main.py:383` emits `error_code` at the top level. Once the Python environment is restored this test should fail with a key error. Python compilation cannot verify this contract.

6. **P2: MCP readiness becomes stale after server enable/disable changes.** The effect at `AuthoringControls.tsx:73` refreshes only when the bound block IDs/server/tool strings or session change. Returning from Tool Registry without editing those values retains the old inventory. Provide a refresh/invalidation mechanism; inventory membership must not be described as proof that the host application works.

## Verification and reporting gaps

- `tests/ui-integration/workflow-recovery-bindings.spec.ts` is referenced by prior verification commands but is absent in this checkout. A command matching the other two files does not establish that a binding journey ran. Inventory actual test names and scenarios before claiming coverage.
- The progress checklist still leaves authoring/recovery and API checks incomplete despite the goal having been marked complete. Host preflight was parked. These are remaining work, not completed acceptance criteria.
- The previous transcript contains repeated clock polling and unchanged checks. The wall-clock window is evidence of elapsed time, not 60 minutes of substantive engineering. Future reports must distinguish those claims.
- Screenshots must be opened and inspected; recording a Playwright trace alone does not establish visual review. Preserve evidence outside transient test-results directories.
- Duplicate-start prevention during asynchronous save needs a dedicated delayed-save test. The handler awaits save before setting run pending; source review alone does not establish a user-reachable duplicate, so this is a verification target rather than a confirmed defect.
- Error ownership currently uses substring matching on error codes. Audit actual backend codes before asserting a responsible maintainer; missing user inputs and invalid output content are not automatically maintainer or capture failures.

## Test-runner error

The previous logs show all 970 assertions passing, with an `onUserConsoleLog` RPC teardown error in one-worker runs; the two-worker run exited successfully, and the named ChatLayout test passed alone. This supports investigating test-runner teardown. It does not establish the root cause or suggest a system reboot. Do not relabel the one-worker error as fixed merely by changing worker count.
