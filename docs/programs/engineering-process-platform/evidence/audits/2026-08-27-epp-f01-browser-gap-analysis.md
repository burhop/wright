# EPP-F01 browser-gap analysis

**Date:** 2026-08-27

**Method:** read-only `speckit-analyze` cross-artifact review plus program-control comparison

**Subject entering review:** preserved implementation WIP commit `40458d19e53882638e791339f7f3303053412795`, tree `8daaa99c6707188a28309753903baa7bdec6d461`, program tree `ec4db749ca1755e037b8d4d9c2e360c085195adc`

## Result

One material HIGH boundary ambiguity was confirmed. EPP-F01 was titled a “live readiness dashboard,” but its specification assumptions and plan explicitly add no product UI, and none of its 68 dependency-ordered tasks creates a browser route, frontend adapter, page, component, refresh behavior, or browser accessibility verification. Wright's existing workspace `DashboardPage.tsx` is a different landing surface and is not evidence-derived program status.

The 24 EPP-F01 functional requirements and 10 buildable success criteria remain covered by the 68 validator/snapshot/CLI tasks. Five Phase 1 tasks are complete at the preserved WIP commit; 63 tasks remain and no Phase 2 task is claimed. The browser outcome must not be inserted into those tasks under the stale implementation lease.

## Resolution

- `DEC-P0-015` keeps EPP-F01 bounded to validator, provenance, governed machine snapshot and CLI reporting.
- Dependency-ordered `EPP-F01B` becomes the independent browser program-status feature after EPP-F01 and before EPP-F02.
- EPP-F01B consumes validated committed evidence read-only; it never hand-sets status, mutates evidence, or becomes authority.
- Product, benchmark, commercial and program-health areas remain non-substitutable, including when benchmark count reaches `100/100`.
- The prior exact EPP-F01 approvals are stale because the bound program/specification subject changed materially. The implementation lease is released and work stops at a new exact human approval gate.

## Constitution and scope check

No constitution exception is requested. EPP-F01 remains offline repository tooling. EPP-F01B will need its own Spec Kit specification, plan, tasks, atomic-design UI work, component tests, mocked Playwright page journey, compatibility/rollback evidence and exact implementation approval. This analysis authorizes none of that implementation.

No dependencies were added; no product or benchmark code ran; no browser code changed; and no push, PR, merge, dev integration, external mutation, publication or release occurred.

## Post-remediation validation

- Spec Kit cross-artifact rerun: no active critical/high/medium finding after the machine-only EPP-F01 boundary and EPP-F01B dependency are explicit; 34/34 buildable requirements remain covered by the same 68 tasks.
- Task boundary: 68 total, 5 Phase 1 complete, 63 remaining, and the only browser wording is the explicit exclusion note.
- JSON Schema: roadmap, program state, decision register and risk register pass Draft 2020-12 validation with format checking.
- Roadmap: 12 unique items, unique priorities, no cycle, `EPP-F01B -> EPP-F01`, and `EPP-F02 -> EPP-F01B` dependency checks pass.
- State history: current revision 22 and its append-only archive are byte-identical.
- Planning-contract tests: 16 passed, 1 deliberately deselected. The deselected implementation-path test dereferences an active lease and is inapplicable after the required material stop released that lease; the unfiltered run recorded this expected failure rather than hiding it. Pytest's first sandboxed attempt also recorded a host temp-directory access error before the bounded outside-sandbox rerun passed.
- Optional `speckit-analyze` Git auto-commit hooks were not run because reviewed allowlist staging remains mandatory.
