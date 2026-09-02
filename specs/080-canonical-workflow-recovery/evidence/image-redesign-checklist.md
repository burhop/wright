# Image-led catch-up: design-to-implementation checklist

Status: implementation authorized; acceptance pending. Created 2026-09-02.

The exact user goal is attachment `690b7c98-cea6-44cc-bb49-9e5c4b726a85/pasted-text.txt`.
Selected image: `D:/repos/wright/artifacts/ui-redesign/wright-workflow-editor-object-palette-v2.png`.
Decision session: **Redesign crowded Wright UI**, task `01a05edc-f82b-7990-b49e-12b93b24d146`.
Prior code/evidence checkpoint: `7e95b0c748975df247effb4bc70f1f67f92a8e81`.

| Outcome | Baseline gap | Implementation | Required new evidence | State |
|---|---|---|---|---|
| Compact Create rail | Permanent input cards, only two downstream buttons | Host + authoring-objects | All seven categories, independent click/keyboard additions | Pending |
| Inputs navigator | Persistent duplicated source presentation | Host transient popover | Focus source, configured/missing counts, no second value editor | Pending |
| Dominant canvas | Two fixed side columns plus agent pane | CSS + workspace + renderer | Matched target image and bounded viewport captures | Pending |
| Contextual Inspector | Fixed five-tab detail column | Host input/settings/port UI | Collapse/reopen, real text/files/settings, visible error buffers | Pending |
| Clear compact nodes/ports | Partial decluttering only | Renderer + CSS | Readable names, small targets, exact multi-I/O and path focus | Pending |
| Compact toolbar/bottom details | Separate bars and floating run overlay | Host + CSS | Reachable actions; truthful states; no graph occlusion | Pending |
| Real authored input | Filename substitution and ephemeral demo state | Helpers + page file adapter + source | Type text/select permitted file; save/reload persists | Pending |
| Complete native authoring | Generic additions/reopen not proven | Helpers + source + commands | Add/configure/connect/delete/undo/source/CAS round trips | Pending |
| Truthful proposal/run | Existing bounded simulations | Host + tests | Unsupported topology blocked, no fake execution/binding | Pending |
| Actual delivery | Old tests/dashboard imply catch-up | Capture + docs/dashboard | New exact subject, served code, validated report, working URL | Pending |

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

## Completion subject / application / report

Pending. Do not substitute the old 24-step walkthrough or 77/80 ledger.

## Implementation checkpoint — 2026-09-02

The early integrated shell has been inspected in a real browser. The report at
`artifacts/ui-walkthrough/image-redesign/20260902T220022Z-early-shell-continuation-1/`
records four shell/navigation actions and four viewport captures. It is working-tree
evidence, not final acceptance. `image-redesign-review.md` records independent
findings and repairs; those visual repairs still require a fresh capture.

Focused helper tests passed 65/65 across authoring objects, Source parsing and
atomic command suites. Host tests passed 15/15, including real company-context
input editing. An integrated production build passed (858 modules). These are
implementation checks, not substitutes for the complete browser journey.

The first browser launch was denied by the process sandbox (`spawn EPERM`), before
navigation. Its initial artifact directory remains preserved; a permitted launch
created the separate continuation above. No user workflow data was changed by
the early shell walkthrough.
