# Returning to work that needs attention

Source batch based on 52b81061190ac251f2c624acecff5fbc7f71c7e1; see the commit containing this record for the integrated changes. C02/C04/C08 now have a compact workspace-file entry for recorded input/review waits. It uses the existing continuation and terminal-review repositories through the existing scoped workspace API; the app-only bridge projects navigation fields. The button opens the exact existing run snapshot, never approves or resumes it.

Three rows are shown initially, with additional rows available on request. Separate owner pagination avoids losing old pending records to recent-history limits. Expired, answered and approved-but-unconsumed records stay distinct. Actual eligibility and subject validity are reconciled by the existing run owner on opening. No new executor, review authority, automatic retry or notification system.

## Evidence and limits

- 10 repository tests passed: old waits beyond recent-history bounds, pagination, workspace isolation, state preservation and exclusion of execution payloads.
- 4 API tests passed against real review service classes and an actual registered HTTP route with private SQLite fixtures. Resolving a terminal review removes its list entry without changing another wait. The earlier mocked API test missed a private repository attribute; corrected before qualification.
- 13 bridge/history tests passed: exact scope, app-only read metadata, bounded projection, invalid/foreign response rejection, and denied session without any read.
- Component tests exercise visible labels, exact-run identity, delayed-response suppression after workspace switch, paging and error visibility. Final log retained privately.
- Compiled native panel screenshots at1100px and480px show all three Open run buttons and workspace files in the viewport, with no horizontal overflow. The public report records exact resource hash and fixture calls. A simulated changed-review failure is visible, refresh removes resolved fixture entries, and no execution/approval tool is called.
- Independent usability reviewer found no visual blocker at either width; changed the ambiguous second Refresh label to Refresh attention list.

**These screenshots use a simulated Linux desktop host and labeled fixture data.** They do not establish actual Windows acceptance or a complete real engineering review/continuation journey. The installed plugin was not updated. Actual handle engineering, personal sign-in, real reviews, rerun and remaining goal acceptance still require qualification.

## Repository gate context

The cumulative gate at52b81061 passed all Python suites and232frontend test files/2137tests, then failed strict docs on a Blender usage-guide evidence link outside the documentation root. Fixed to a pinned evidence commit; strict docs recheck passed. Browser gates were not reached. This batch still requires the applicable final gate; do not call the earlier cumulative gate a pass. Generated packaged web assets from that gate remain preserved separately.
