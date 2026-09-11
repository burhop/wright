# T055 Chromium failure and repair record

The first complete six-test recovery run after adding the component card passed
five tests and failed the existing typed-handle journey. The new card changed
node geometry, and the `rel.report-to-package` label intercepted pointer events
intended for `rel.review-to-export` for the full 30-second timeout.

The first repair assigned deterministic, presentation-only edge-label lanes.
Its focused rerun then exposed a second empty `role=status` region added by the
new navigator, making the existing keyboard-connection status query ambiguous.
The navigator now creates its live status output only when it has a message.

No forced click, timeout increase, selector weakening, or semantic/layout
mutation was used. The repaired focused typed-handle test passed, followed by
the complete `6 passed (13.7s)` Chromium recovery suite.
