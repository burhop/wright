# ADR 0015: Separate the browser program-status surface

**Status:** decided, pending material-plan approval

**Date:** 2026-08-27
**Decision ID:** `DEC-P0-015`

## Context

The approved program requires a browser-accessible page that stays current as committed evidence changes and visibly tracks the four independent readiness areas plus progress from zero to 100 qualified engineering processes. EPP-F01's amended specification and 68 tasks govern the validator, `dashboard.json`, provenance, CLI reporting and delivery evidence, but they do not implement a browser route or page. Wright's existing workspace landing `DashboardPage.tsx` reports workspace activity and is not an evidence-derived program-status surface.

Expanding EPP-F01 during implementation would violate its digest-bound task boundary and hide a material user-facing omission. Treating the JSON file or CLI output as the browser requirement would be a false completion claim.

## Decision

Keep EPP-F01 bounded to validation, machine snapshot generation, provenance and CLI reporting. Add the independently shippable Spec Kit child feature `EPP-F01B` immediately after EPP-F01 and before EPP-F02. EPP-F01B will render only a validated committed snapshot and external validation envelope as a read-only browser page.

The page must expose:

- product, benchmark, commercial and program-health areas independently;
- counted/target benchmark progress from `0/100` through `100/100` without compensating for another gate;
- active feature and completed/total task and lifecycle-checkpoint progress;
- blockers, the sole next eligible action, exact evidence links and freshness;
- honest empty, loading, stale, blocked, failed and unavailable states;
- accessible traffic-light presentation with non-color text, keyboard use, usable contrast, narrow viewport, 200% zoom and reduced-motion behavior;
- automatic refresh only when committed snapshot/evidence identity changes.

It may not hand-set status, infer authority, mutate evidence, launch product/benchmark work, or become a second approval/transition source. EPP-F02 depends on EPP-F01B.

## Alternatives rejected

1. **Expand EPP-F01 now.** Rejected because the active approval binds 68 local tasks and does not authorize browser product work.
2. **Reuse the workspace landing dashboard.** Rejected because its data model, purpose and authority do not satisfy the program-status contract.
3. **Call JSON/CLI output the web page.** Rejected because it omits the explicit browser-accessible user outcome.

## Consequences

The program roadmap, P0 exit, proposed-feature set, dashboard contract, risk register and catch-up state change materially. The current EPP-F01 material-change and feature-implementation approvals become stale because their exact subject includes affected artifacts. Preserved local EPP-F01 WIP remains evidence only until a replacement exact approval bundle authorizes resumption. No EPP-F01B implementation is authorized by this decision.
