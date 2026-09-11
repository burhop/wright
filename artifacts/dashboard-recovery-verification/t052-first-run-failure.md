# T052 dashboard verifier first-run failure

- Checked at: `2026-09-01T03:58:40.780Z`
- Result: `fail`
- Product/API checks: recovery 52/60, approval complete, exact commit/tree/manifest, customer readiness false, eight images loaded, zero horizontal overflow, zero browser diagnostics, all intended HTTP evidence links 200, traversal checks 403.
- Failed assertion: `productionBoundary` on desktop and mobile.
- Cause: the new verifier searched for `Stable workflow-ir 2.0.0`, wording not rendered on the goal view. The dashboard correctly rendered the materially stronger active-step statement that T052 stable definition/kernel/projection promotion and append-only definition persistence are complete.
- Repair: bind the assertion to that exact visible active-step statement and rerun the complete verifier. No dashboard product behavior or evidence claim was weakened.

The first repaired rerun at `2026-09-01T03:59:04.145Z` proved the new visible
assertion on both viewports but exposed a second stale verifier literal: the
final API predicate still required 51 completed tasks even though its captured
API evidence correctly reported 52. The predicate was updated to 52 and the new
production-boundary field was added to the required-field loop before the final
complete rerun.
