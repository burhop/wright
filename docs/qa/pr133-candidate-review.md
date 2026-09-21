# PR 133 candidate review

Reviewed September 21, 2026 on promaxgb10-9666. Scope: workflow recovery
usability, not engineering-output qualification or the Feature 082 campaign.
PR remains open for the owner's merge decision.

## Earlier findings reconciled

| Finding from September 18 | Current implementation and verification |
| --- | --- |
| Server-scoped MCP tasks marked unbound | Server-only tasks and exact tool calls have separate binding/availability predicates; factory and discovery regressions cover both. |
| Canvas hides execution identity | Cards resolve MCP server/tool, human review and saved binding capability; long labels retain their full title. |
| Old readiness refresh overwrites new results | Request-generation invalidation guards effects and manual refresh; delayed-response regression retained. |
| Rejection implies execution | Dispatch display requires execution events. Final review also corrected summary/drawer labels for starts rejected before confirmation. |
| Wrong API error envelope | Source API tests now assert the actual top-level error_code. |
| Stale MCP inventory | Explicit Recheck MCP availability refreshes discovery; catalog availability is not a claim of host qualification. |
| Duplicate Save & run | Synchronous in-flight guard and delayed-save test prevent duplicate dispatch. |
| Missing binding-test evidence | Actual factory/discovery/concept tests replace the previously cited nonexistent bindings spec. |
| Lost corrective guidance | Streamed failures retain both their backend correction field and visible next-action text. |

The served workspace Workflows entry is the browser acceptance path. Authoring
tests retain typed ports, source/diagram synchronization, undo/redo, keyboard
deletion, conflict handling, save/reopen and responsive controls. Explicit New
workflow is blank; opening Workflows for the first time still seeds the existing
mounting-bracket example. This distinction is not new user acceptance.

Visual review found that expanded readiness resized the toolbar and displaced
the canvas. It is now a bounded, scrollable overlay; browser regressions assert
stable canvas dimensions and mobile containment.

## CI corrections and local gates

The saved metrics fix replaces SELECT-then-INSERT with atomic conflict handling.
New controlled-interleaving tests cover identical and conflicting replays. The
regression was also executed against the old implementation and reproduced the
exact UNIQUE constraint failure. Native API tests allow 15 seconds for terminal
state: Windows CI's failed five-second assertion preceded a successful execution
at approximately nine seconds, not a failed product operation.

The runtime dependency audit is now included in both local gates using the CI
policy; fail-closed tests cover findings, empty/missing reports and tool errors.
The earlier executor polling workaround was removed: standard executor/shield
completion passes outside the restricted tool sandbox, including real source
creation. Sandbox wakeup behavior is not a supported-runtime defect.

## Host limits and acceptance boundaries

The local full merge gate uses SKIP_PLAYWRIGHT=1 because this ARM64 host lacks
WebKit system libraries libgstreamer-plugins-bad1.0-0 and libavif16. The earlier
cross-browser attempt failed at WebKit launch, before assertions. Focused
Chromium workspace tests run locally; the final PR's provisioned cross-browser
CI must be green before recommending merge. This is not a waiver for browser
assertion failures. Final command results and exact candidate/CI links are
recorded on the PR after validation completes.

Live CAD/CFD/MCP/printer execution, BREP host installation, broad registry policy
and report-presentation acceptance are not established by this PR. Template
setup/qualification remains an explicit prerequisite, not a simulated pass.
