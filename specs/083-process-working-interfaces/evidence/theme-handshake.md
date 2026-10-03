# T037: scoped transport, theme and exact navigation

T037 is complete within its transport/theme/navigation task scope. Full UI,
editor/accessibility, engineering, migration and final Feature 083 acceptance
remain open. This record supersedes earlier pending T037 statements only for
the inspected obligations below; original evidence and failures are retained.

| Obligation | Owning implementation and inspected evidence |
| --- | --- |
| Scoped preview/working transport | Public presentation client and existing server-derived presentation bridge; 94 current client tests and 71 current backend host/authority tests. Read-only previews reject mutations; exact source/run/grant checks and closed operations remain authority. |
| Theme transmission | Native host and fixed embedded runtime share a bounded token allowlist. `color-scheme` accepts only `light` or `dark`; existing unsafe CSS rejection remains. Current sender tests and execution of the shipped receiver check supported/unsupported values and nonce rejection. |
| Actual theme/reconnect | Eight served checks on both saved model-created engineering interfaces: exact 18/19 results, light scheme/colors, frame reload, dark restore. The visible frame's own context is inspected. |
| Exact navigation | Retained [two-process navigation](../../../artifacts/process-interfaces/083/20261003-two-process-exact-navigation/checked-scope.json) proves exact producing blocks and held assessments in the workspace. No foreign run can be selected by a frame locator. Current host/client tests retain those guards. |
| No credentials or generic invocation | Frame messages carry exact locators and bounded tokens. Existing API presentation grants own capabilities; unknown keys, foreign subjects, read-only mutations and generic tool calls are rejected by current tests. Authenticated traces remain private. |
| Current distribution | Three passing packaging checks compare fixed runtime/manifest source bytes with the new wheel, verify shipped public resources, offline saved hosting and installed compilation. Older installed browser builds are not relabelled as current. |

## Correction and actual checks

The first actual browser check found a product defect: selected light colors
arrived, but the embedded browser-control scheme stayed dark. The native sender
and fixed receiver now include the existing CSS property in their allowlist with
an exact two-value check. Protocol version, origins, source window, nonce,
presentation, generation and backend action authority are unchanged. An older
runtime ignores the extra token and continues its handshake; it needs an upgrade
for the new control styling.

The second check passed Heat, then stopped because a global last-response test
assertion picked a retained hidden Heat tab's context during the wheel journey.
The fresh continuation inspects the visible frame's actual backend context and
passes all eight checks with empty browser error/failed-response diagnostics.
All 57 retained run/output/bundle files and UI authoring records remain unchanged.
No generation, process start, review response or saved preference change occurred.
Three remaining exact owned proof views were closed through the normal owner API;
no limits or database records were edited.

Current checks: 47 affected frontend tests, 94 scoped client tests, 71 backend
host/authority tests, three packaging tests, app TypeScript exit 0 and Ruff pass.
Counts overlap retained suites and must not be added to previous totals. The
initial 70 backend setup errors were a temporary-directory permission failure;
the fresh workspace-scoped root passed. All three browser reports pass the
walkthrough structure validator.

See the [walkthrough](../../../artifacts/process-interfaces/083/20261003-theme-handshake-verified/workspace-walkthrough/report.html),
[scope and limits](../../../artifacts/process-interfaces/083/20261003-theme-handshake-verified/checked-scope.json)
and [evidence inventory](../../../artifacts/process-interfaces/083/20261003-theme-handshake-verified/inventory.json).
Abrupt browser/OS termination remains unqualified; BFcache and late-open cleanup
have component scope only. This is neither human engineering acceptance nor a
physical printer test.
