# Luna Usability Acceptance Audit

Date: 2026-09-18

This is the final acceptance record for the scoped workflow-editor and run-
readiness fixes. It distinguishes product evidence from host limitations and
does not authorize live engineering execution.

| Area | Evidence | Result |
| --- | --- | --- |
| MCP identity | 65 focused frontend tests; server-scoped `mcp-task` and exact `mcp-tool` cases | Pass |
| Long execution labels | Canvas regression with a deliberately long qualified server/tool label; full-value `title` retained | Pass |
| Readiness races | Delayed refresh and workspace/path subject guards in component/page tests | Pass |
| Start truthfulness | Rejected starts remain `Run blocked`; dispatch wording requires run/step evidence; delayed Save & run guard covered | Pass |
| Workspace source runtime | 21 workspace-service tests using the production bounded file use cases | Pass |
| Integration run API | 14 tests pass with stubbed execution dependencies | Pass |
| Served workflow editor | 18 Playwright tests through the workspace Workflows control; desktop, mobile, keyboard, 200% scale, save/reopen, conflict and blocked-run paths | Pass |
| Production frontend | `bun run build` passes | Pass, with existing chunk-size warning |
| Combined API TestClient suite | Can stall before the first request in managed Python 3.13; independent slices remain green | Environment blocker; do not call combined suite green |
| Live CAD/CFD/MCP/printer work | Not run | Deliberately out of scope |

The first-open canonical workflow may show the maintained mounting-bracket
fixture. The explicit File > New workflow path creates an authored source with
no task, input, connection, or item records; its regression verifies that it
does not copy the fixture.

The `access_programs.cyber` organization error is external to Wright and is
documented in `codex-access-programs-error-2026-09-18.md`. Rebooting or editing
this repository cannot enable that organization-level parameter.
