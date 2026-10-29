# Candidate 0.38 qualification checkpoint

Product source: `7d87cfb44bedc5fabb915d9314d88abb5368cb4a`.
Test-only bridge inventory correction: `60f332d6`.

The frozen UI and bridge use matching installed wheel packages with fresh isolated
storage. Installed module bytes, scoped pending-navigation owners, actual MCP
create/read/open, foreign-session rejection, and visible narrow readiness →
Connections → same inspector return pass. The screenshot uses the compiled UI
against that backend in a **simulated Linux host**. It is not Windows acceptance.
No engineering task, review, physical action or historical run was executed.

The supported browser matrix passed 161 tests, skipped five. The first attempt's
two Chromium `ERR_NETWORK_CHANGED` failures and traces remain in private evidence;
the clean rerun is additional evidence, not deletion of those failures. WebKit
remains unavailable because this host lacks required ABI libraries.

The full gate first stopped at an obsolete tool count. The two additions are
app-only, read-only pending-work and editor discovery tools; the corrected complete
bridge suite passes. Remaining Python, Hermes-plugin and frontend suites pass.
Strict docs then found two out-of-tree evidence links, corrected to repository
paths. A final gate receipt is still required before delivery.

`qualification.json` records counts and identities. `readiness-480.png` shows the
actual bounded UI check. Full private evidence is under
`.local-run/experience-review/candidate-038/` in the feature worktree.

The live plugin remains 0.33. Actual Windows display/download/chat return, the full
replacement-handle engineering chain with human reviews and rerun, and the full
Robot Tracking Diagnosis chain remain unqualified. These are completion gaps,
not implied successes from automated UI checks.
