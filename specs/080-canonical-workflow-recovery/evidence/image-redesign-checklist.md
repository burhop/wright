# Image-led catch-up: design-to-implementation checklist

Status: local image-led UI/authoring catch-up complete; all T081–T092 passed. Created 2026-09-02; final capture UTC2026-09-03 (2026-09-02 EDT).

The exact user goal is attachment `690b7c98-cea6-44cc-bb49-9e5c4b726a85/pasted-text.txt`.
Selected image: `D:/repos/wright/artifacts/ui-redesign/wright-workflow-editor-object-palette-v2.png`.
Decision session: **Redesign crowded Wright UI**, task `01a05edc-f82b-7990-b49e-12b93b24d146`.
Prior code/evidence checkpoint: `7e95b0c748975df247effb4bc70f1f67f92a8e81`.

| Outcome | Baseline gap | Implementation | Required new evidence | State |
|---|---|---|---|---|
| Compact Create rail | Permanent input cards, only two downstream buttons | Host + authoring-objects | Seven categories and independent click/keyboard additions in exact 32-step journey | Passed |
| Inputs navigator | Persistent duplicated source presentation | Host transient popover | Focus source, configured/missing counts, no second value editor | Passed |
| Dominant canvas | Two fixed side columns plus agent pane | CSS + workspace + renderer | Primary image at 1536×1024; 1537/1070/830 widths; actual browser zoom 2.0 | Passed |
| Contextual Inspector | Fixed five-tab detail column | Host input/settings/port UI | Collapse/reopen, real text/files/settings, visible error buffers, Apply reachable at 200% | Passed |
| Clear compact nodes/ports | Partial decluttering only | Renderer + CSS | Readable names, small targets, exact multi-I/O/fan-out/rejection and path focus | Passed |
| Compact toolbar/bottom details | Separate bars and floating run overlay | Host + CSS | Reachable actions, contained text, overlay/focus and actual200% preview checks pass | Passed |
| Real authored input | Filename substitution and ephemeral demo state | Helpers + page file adapter + source | Typed text/permitted file references persist after exact source/layout save and reload | Passed |
| Complete native authoring | Generic additions/reopen not proven | Helpers + source + commands | Add/configure/connect/delete/undo/source/CAS conflict/compare/reload pass | Passed |
| Truthful proposal/run | Existing bounded simulations | Host + tests | Original preserved; unsupported topology blocked; fixture proposal/run explicitly labeled | Passed |
| Actual delivery | Old tests/dashboard imply catch-up | Capture + docs/dashboard | Exact subject/served code, validated report and live desktop/mobile dashboard links verified | Passed |

## Authority and safeguards

- No image status, tool name, generated timestamp, reviewer, or study result is
  execution or approval evidence. Internal review is not representative testing.
- Existing canonical source/file/CAS/command authority is retained. Root 079
  proposed readonly/database choices and old Rivet planning are not adopted.
- Frozen historical spec079/T028–T038, unrelated root changes, and rejected
  implementation stashes remain untouched. No push/merge/release/customer action.
- Optional Spec Kit auto-commit hooks are skipped in favor of scoped coherent
  integration commits. Existing feature/branch is explicitly supplied by the user;
  specification branch creation/template replacement is inapplicable to this
  amendment. AGENTS already references the retained 080 plan in this worktree.
- The implementation checklist is not marked passed before product evidence.
  T056/T058/T060 stay open and outside this bounded goal.

## Preparation log

- Re-read the full user goal, selected implementation skills, recovery
  requirements, command/renderer/source contracts and constitution. Verified
  recovery branch and no tracked baseline modifications. The only pre-existing
  untracked items are test scratch directories and the pending engineer-note file.
- The hardcoded Git Bash candidate is absent. Use available script tooling when
  possible; never claim the Bash prerequisite checks passed when they did not.

## Reviewed subject / application / report

Implementation: `af0691229e39a8b1b80db0ed7eaa44caaf765f31`, tree
`bd308b0bb73c810caead38435944a1314d19a866`.

Application: `http://127.0.0.1:5227/workspace/85cbd6b3-e9d1-474d-add2-36f6e95a7b51?workflow=canonical`.
This is **Wright workflow evidence**, with the original example preserved. The
acceptance journey created a separate named document;
`workflows/image-redesign-acceptance-20260903t000131z.workflow.wflow` retains the
authored configuration and connections.

Report: `http://127.0.0.1:8765/evidence/image-redesign/report.html`.
Artifact root: `artifacts/ui-walkthrough/image-redesign/20260903T000131Z-committed-acceptance-af069122-continuation-1/`.
Manifest SHA-256: `c51638c26a431c0f195027825a69b1fc774bc127b6978200e3070b6366ed65e7`.
Result: 32/32 checks; 87 raw + 87 annotated screenshots; 200 manifest-bound
files; 112,515,138-byte trace; no unexpected browser diagnostics. The deliberately
induced stale-save 409 and its browser resource error remain explicitly recorded.

All 14 required browser-loaded frontend module sources match the commit after
CRLF-to-LF normalization only. API listener60044 was restarted from the same
commit with six verified module origins/backend hashes and eight existing workflow
files unchanged. Backend evidence:
`.local-run/image-redesign-committed-api-af069122/verification.json`.

The earlier five-second second-tab save failures are preserved. Their later
writes do not retroactively count as captured successes. Direct/proxy timing and
stack evidence identified synchronous CLI discovery blocking the API event loop;
offloading and a read-only status endpoint repaired it. The final continuation
passes the unchanged deadline; no timeout increase or false health was introduced.

Dashboard preflight `20260903T001049230Z-preflight` verified the exact implementation,
fresh report/images/app link, zero desktop/mobile overflow, and the honest88/92
pre-closure ledger. Its independent report-control record
`artifacts/dashboard-image-redesign-report-checks/20260903T001137864Z-preflight/`
verified all15 hashes and8 image controls, Close/Escape and zero diagnostics.
Only after that evidence was T092 closed. The post-closure strict89/92 record
`artifacts/dashboard-image-redesign-verification/20260903T001532131Z-complete/`
also passes: zero desktop/mobile overflow or diagnostics; exact subject,
report/images/application links; frozen27/38 and customerReady=false. It is linked
in `image-redesign-delivery.json` without rewriting historical dashboard evidence.

T056/T058/T060 remain open outside this local goal. New templates are configurable
unbound drafts; proposals/runs/output downloads remain explicitly fixed examples.
Five platform-specific storage tests remain skipped, not passed. No push, merge,
release, customer action, new human-study claim or live engineering result occurred.

## Implementation checkpoint — 2026-09-02

The early integrated shell was inspected in a real browser. The report at
`artifacts/ui-walkthrough/image-redesign/20260902T220022Z-early-shell-continuation-1/`
records four shell/navigation actions and four viewport captures. It is historical
working-tree evidence, not final acceptance. `image-redesign-review.md` records the
subsequent independent findings and their separate verification subjects.

Focused helper tests passed 65/65 across authoring objects, Source parsing and
atomic command suites. Host tests passed 15/15, including real company-context
input editing. An integrated production build passed (858 modules). These are
implementation checks, not substitutes for the complete browser journey.

The first browser launch was denied by the process sandbox (`spawn EPERM`), before
navigation. Its initial artifact directory remains preserved; a permitted launch
created the separate continuation above. No user workflow data was changed by
the early shell walkthrough.
