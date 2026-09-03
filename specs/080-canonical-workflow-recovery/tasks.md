# Tasks: Canonical Workflow Recovery

**Input**: Design documents from `specs/080-canonical-workflow-recovery/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`

**Scope rule**: Tasks T001–T050 form the original recovery evidence slice. T051 is the mandatory product/visual approval stop. T052–T060 were dependency-ordered post-approval work. T061–T067 record the first mechanical-engineer correction. T068–T080 supersede the remaining obsolete global-route/source, missing-file, and overloaded-canvas treatments with the approved workspace-owned engineer-authoring correction; a fresh exact subject is required before the approval/evidence loop may close.

**Tests**: The specification requires conformance, component, browser, accessibility, responsive, and human-repeatable evidence, so test tasks are included in each user-story phase.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it writes a different file and has no incomplete-task dependency.
- **[US#]**: Maps the task to the numbered user story in `spec.md`.
- Checked tasks are already completed in this recovery worktree; unchecked tasks are current or approval-gated work.

## Phase 1: Setup and Freeze Control

**Purpose**: Preserve the exact Checkpoint D subject and create an isolated, default-off recovery surface.

- [x] T001 Freeze EPP-F02B at commit `b4a7e996f10ec95f7d24185a43fd1401843db66d` with T028–T038 paused in `docs/programs/engineering-process-platform/evidence/transitions/TR-0095.json`
- [x] T002 Record feature 080 metadata and branch authority in `.specify/feature.json` and `specs/080-canonical-workflow-recovery/spec.md`
- [x] T003 [P] Add the default-off recovery feature flag in `apps/web/src/config/workflow-recovery.ts`
- [x] T004 [P] Add exact provisional `@xyflow/react` 12.11.3 dependency metadata in `apps/web/package.json` and `package-lock.json`
- [x] T005 Add the original lazy guarded `/workflow-recovery` route and navigation in `apps/web/src/App.tsx`, `apps/web/src/components/layout/Sidebar.tsx`, and `apps/web/src/components/pages/WorkflowRecoveryPage.tsx` (historical implementation, superseded and removed by T069)

---

## Phase 2: Canonical Recovery Foundation

**Purpose**: Establish one complete IR, separate authority boundaries, exhaustive source coverage, and a shared conformance rule before product-story work.

**Critical gate**: No user-story claim is valid unless the canonical fixture round-trips through every adapter without semantic loss.

- [x] T006 [P] Inventory all 881 uniquely keyed requirement, gate, story, lesson, and prior-spec sources—including adjacent specs 055, 064, and 068–080—in `scripts/recovery/audit_capability_coverage.py` and `specs/080-canonical-workflow-recovery/capability-source-map.csv`
- [x] T007 [P] Define the canvas-first product authority and supersession boundary in `specs/080-canonical-workflow-recovery/north-star.md`
- [x] T008 Define canonical IR, layout, proposal, renderer, and run decisions in `specs/080-canonical-workflow-recovery/decisions/0001-canonical-workflow-ir-vnext.md` and `specs/080-canonical-workflow-recovery/data-model.md`
- [x] T009 [P] Publish strict canonical-definition, command-batch, layout, and run-projection schemas plus explicit supported-version and unknown-version contracts in `specs/080-canonical-workflow-recovery/contracts/`
- [x] T010 [P] Create semantically identical JSON, YAML, and workflow-DSL fixtures in `specs/080-canonical-workflow-recovery/fixtures/`
- [x] T011 Measure identical syntax tasks and preserve the non-permanent syntax conclusion in `scripts/recovery/evaluate_workflow_syntaxes.py` and `specs/080-canonical-workflow-recovery/evidence/syntax-evaluation.md`
- [x] T012 Implement the strict renderer-neutral Python conformance kernel in `scripts/recovery/workflow_conformance.py`
- [x] T013 [P] Prove 23 Python parse/format/validate/apply/diff/project/schema invariants, including all four published wire schemas, fail-closed command/layout/run versions, and scoped reusable-component addresses, in `tests/recovery/test_workflow_conformance.py`
- [x] T014 Build the lossless snake_case wire adapter, ergonomic view, DSL, and shared command bridge in `apps/web/src/prototypes/workflow-recovery/canonical-wire.ts`, `model.ts`, `recovery-dsl.ts`, and `command-system.ts`
- [x] T015 [P] Prove the TypeScript view equals committed wire/DSL fixtures, history restores revalidate atomically, versions fail closed, scoped component identities survive projection, and a renderer replacement fake cannot change canonical bytes in `apps/web/src/prototypes/workflow-recovery/command-system.spec.ts` and `model.spec.ts`

**Checkpoint**: Canonical fixture, syntax evidence, adapters, and atomic command boundary are independently testable.

---

## Phase 3: User Story 1 — Build a Mechanical Workflow Graphically (Priority: P1) — MVP

**Goal**: Let an engineer understand and manipulate a typed mounting-bracket workflow on the canvas without opening Code.

**Independent Test**: Search and add a downstream block, move it, connect and disconnect typed ports, add/view/replace the design-intent text or document, inspect a gate and feedback path, delete a safe block, and undo/redo while stable identities remain visible.

### Tests for User Story 1

- [x] T016 [P] [US1] Add page-level palette, add/delete, validated undo/redo, attachment, configuration, pointer/keyboard-handle coverage and local default/loading/error/test-ID component coverage in `tests/ui-integration/workflow-recovery.spec.ts`, `WorkflowRecoveryConcept.spec.tsx`, and `ReactFlowRecoveryCanvas.spec.tsx`
- [x] T017 [P] [US1] Add adapter gate/feedback and unphased-component projection tests in `apps/web/src/prototypes/workflow-recovery/model.spec.ts`

### Implementation for User Story 1

- [x] T018 [US1] Implement the provisional React Flow renderer behind the retained adapter in `apps/web/src/prototypes/workflow-recovery/ReactFlowRecoveryCanvas.tsx`
- [x] T019 [US1] Implement typed left/right handles, canonical relationship labels, gate/feedback notation, and separate artifact actions in `apps/web/src/prototypes/workflow-recovery/ReactFlowRecoveryCanvas.tsx`
- [x] T020 [US1] Route add, move, connect, disconnect, configure, delete, undo, and redo gestures through versioned atomic host commands, including isolated validated history restores, in `apps/web/src/prototypes/workflow-recovery/WorkflowRecoveryConcept.tsx`
- [x] T021 [P] [US1] Implement the three explicit input-source controls, design-intent text/common-document preview and replacement, and contextual downstream engineering block library in `apps/web/src/prototypes/workflow-recovery/WorkflowRecoveryConcept.tsx` and `apps/web/public/recovery-concept/`
- [x] T022 [P] [US1] Build the three-treatment interactive port laboratory and evidence record in `apps/web/src/prototypes/workflow-recovery/WorkflowRecoveryConcept.tsx` and `specs/080-canonical-workflow-recovery/evidence/block-port-lab.md`
- [x] T023 [US1] Apply shared-token-only responsive, focus, non-color, and selected-state visual language; keep phase metadata non-decorative; and give every authored interaction a stable test identity in `apps/web/src/prototypes/workflow-recovery/workflow-recovery.css` and the recovery components

**Checkpoint**: User Story 1 works independently in Diagram view; implementation bindings remain progressive disclosure.

---

## Phase 4: User Story 2 — Edit One Workflow in Diagram and Source (Priority: P1)

**Goal**: Make Diagram, Source, Side by side, and Inspector lossless views of one accepted definition.

**Independent Test**: Move a block without changing semantic digest, apply a valid Code title change, select concepts in both directions, then apply invalid source and confirm the last-valid graph/revision remains authoritative.

### Tests for User Story 2

- [x] T024 [P] [US2] Prove exact golden wire/DSL round trips, parsed text commands, layout isolation, stale bases, and invalid atomic containment in `apps/web/src/prototypes/workflow-recovery/command-system.spec.ts`
- [x] T025 [P] [US2] Add graph-to-source, source-to-inspector, valid edit, invalid containment, digest-isolation, and graph↔text transition-under-one-second browser assertions in `tests/ui-integration/workflow-recovery.spec.ts`

### Implementation for User Story 2

- [x] T026 [US2] Implement deterministic format/parse/source-map behavior for the original full-IR Code treatment in `apps/web/src/prototypes/workflow-recovery/recovery-dsl.ts` (retained as an internal projection and superseded publicly by T070)
- [x] T027 [US2] Canonicalize semantic equality and digest input with stable snake_case wire keys in `apps/web/src/prototypes/workflow-recovery/command-system.ts` and `WorkflowRecoveryConcept.tsx`
- [x] T028 [US2] Implement Diagram, Code, Split, last-valid source containment, and shared selection in `apps/web/src/prototypes/workflow-recovery/WorkflowRecoveryConcept.tsx` (public labels superseded by T070)
- [x] T029 [US2] Bind diagnostics to stable semantic IDs and current source spans in `apps/web/src/prototypes/workflow-recovery/recovery-dsl.ts` and `WorkflowRecoveryConcept.tsx`

**Checkpoint**: User Story 2 proves one accepted definition; source text, renderer state, and layout never become independent authority.

---

## Phase 5: User Story 3 — Review an AI-Proposed Workflow Change (Priority: P2)

**Goal**: Preview a multi-block AI candidate graphically and textually, then reject or explicitly accept it through the same command boundary.

**Independent Test**: Request the drawing/review proposal, inspect candidate-only blocks and source read-only, reject without revision change, request again, accept once, and verify the bounded simulation refuses the unbound expanded topology.

### Tests for User Story 3

- [x] T030 [P] [US3] Add proposal base, candidate validation, rejection, acceptance, read-only inspection, and single-revision browser coverage in `tests/ui-integration/workflow-recovery.spec.ts`
- [x] T031 [P] [US3] Add atomic AI candidate and non-synthesized-gate unit coverage in `apps/web/src/prototypes/workflow-recovery/command-system.spec.ts` and `model.spec.ts`

### Implementation for User Story 3

- [x] T032 [US3] Define the drawing/review proposal as a stable command batch with assumptions and warnings in `apps/web/src/prototypes/workflow-recovery/command-system.ts`
- [x] T033 [US3] Render the full candidate graph with dashed AI-only blocks and an exact candidate Code projection in `apps/web/src/prototypes/workflow-recovery/WorkflowRecoveryConcept.tsx` and `ReactFlowRecoveryCanvas.tsx`
- [x] T034 [US3] Keep candidate inspector facts read-only and accepted host authority unchanged until explicit accept in `apps/web/src/prototypes/workflow-recovery/WorkflowRecoveryConcept.tsx`
- [x] T035 [US3] Fail closed on stale, invalid, unauthorized, or unsupported simulation candidates in `apps/web/src/prototypes/workflow-recovery/command-system.ts` and `WorkflowRecoveryConcept.tsx`

**Checkpoint**: User Story 3 demonstrates AI proposal value without mutation, approval, binding inference, or execution authority.

---

## Phase 6: User Story 4 — Understand and Recover a Workflow Run (Priority: P2)

**Goal**: Project truthful simulated run facts, recovery, and recognizable local fixture outputs without changing the definition.

**Independent Test**: Capture an immutable canonical run subject, advance through queued/running/needs-input/recovered/succeeded, inspect active flow and tabs, open/download the static STEP/report fixtures, then project failure and confirm downstream/output invalidation.

### Tests for User Story 4

- [x] T036 [P] [US4] Add queued, active, needs-input, recovery, success, output, failure, downstream-blocking, immutable-revision, run-version rejection, and run-overlay-under-one-second assertions in `tests/ui-integration/workflow-recovery.spec.ts` and `ReactFlowRecoveryCanvas.spec.tsx`
- [x] T037 [P] [US4] Verify the committed STEP fixture digest and explicit static-fixture identity in `apps/web/public/recovery-concept/mounting-bracket.step` and `tests/ui-integration/workflow-recovery.spec.ts`

### Implementation for User Story 4

- [x] T038 [US4] Bind each simulated run projection to workflow ID, captured revision, semantic SHA-256, timestamps, steps, and artifact records in `apps/web/src/prototypes/workflow-recovery/model.ts` and `WorkflowRecoveryConcept.tsx`
- [x] T039 [US4] Render queued/running/needs-input/succeeded/failed/blocked/stale state and non-color active-flow cues in `apps/web/src/prototypes/workflow-recovery/ReactFlowRecoveryCanvas.tsx` and `workflow-recovery.css`
- [x] T040 [US4] Implement bounded 6061-T6 needs-input recovery and Inputs/Outputs/Activity/Diagnosis inspection in `apps/web/src/prototypes/workflow-recovery/WorkflowRecoveryConcept.tsx`
- [x] T041 [US4] Expose exact binding argument/result maps and declared artifact lineage in `apps/web/src/prototypes/workflow-recovery/WorkflowRecoveryConcept.tsx`
- [x] T042 [US4] Add recognizable local bracket, report, and STEP fixtures with honest simulated/static provenance in `apps/web/public/recovery-concept/`
- [x] T043 [US4] Invalidate output readiness, artifact records, and downstream package state after failed or stale export projection in `apps/web/src/prototypes/workflow-recovery/WorkflowRecoveryConcept.tsx`

**Checkpoint**: User Story 4 is a truthful product-grammar simulation, not an executor or mechanical-correctness claim.

---

## Phase 7: User Story 5 — Trust Versioning, Authority, and Compatibility (Priority: P3)

**Goal**: Make retained foundations, provisional concept code, evidence quality, program status, and the approval boundary reviewable as one exact subject.

**Independent Test**: Run conformance/unit/build/browser gates, inspect a human-repeatable walkthrough and diagnostics, compare frozen and recovery evidence, verify program/dashboard truth, and confirm all production hardening is downstream of product approval.

### Tests and Evidence for User Story 5

- [x] T044 [P] [US5] Document retained foundations, provisional choices, limitations, and frozen-prototype parity in `specs/080-canonical-workflow-recovery/research.md`, `prototype-parity.md`, and `evidence/react-flow-recovery.md`
- [x] T045 [P] [US5] Verify capability coverage remains 881/881 with current recovery completion gates retained in `scripts/recovery/audit_capability_coverage.py` and `specs/080-canonical-workflow-recovery/evidence/capability-coverage.json`
- [x] T046 [US5] Run and record conformance, focused Vitest, web build, full recovery Chromium, accessibility, responsive, schema, capability, program, freeze, and package-lock dry-run gates against the final source in `specs/080-canonical-workflow-recovery/quickstart.md`
- [x] T047 [US5] Capture the complete raw/annotated Playwright walkthrough, trace, browser diagnostics, manifest, status, and traffic-light report against the exact committed review subject in `artifacts/ui-walkthrough/workflow-recovery/<timestamp>/`
- [x] T048 [US5] Bind the final exact walkthrough paths into `specs/080-canonical-workflow-recovery/capability-inventory.md` and update frozen-versus-recovery evidence in `specs/080-canonical-workflow-recovery/evidence/prototype-side-by-side.md`
- [x] T049 [US5] Refresh the reachable progress dashboard with recovery goal, exact tasks/artifacts, final screenshot gallery, newest-first history, product-direction approval state, and incomplete customer readiness in the active Codex visualization workspace
- [x] T050 [US5] Validate program-roadmap dependency, freeze immutability, Spec Kit consistency, and agent context; record results in `specs/080-canonical-workflow-recovery/evidence/specification-analysis.md` and `AGENTS.md`

**Checkpoint**: Recovery evidence is complete and the exact subject is ready for product review; customer readiness is still incomplete.

---

## Phase 8: Mandatory Product / Visual Approval Stop

**Purpose**: Stop all broader work until a human reviews the exact recovery subject.

- [x] T051 Conduct and record explicit product/visual approval for the digest-bound walkthrough and recovery commit in `specs/080-canonical-workflow-recovery/evidence/product-approval.md`

**STOP**: T052–T060 are blocked unless T051 records an approved exact commit, tree, walkthrough manifest digest, reviewer, decision, and allowed next action. Rejection or requested changes create a new bounded recovery iteration instead.

---

## Phase 9: Post-Approval Production Work

**Purpose**: Preserve remaining capability work without implying authorization or readiness.

- [x] T052 Promote only approved IR/kernel/renderer concepts into production boundaries with migrations and rollback in `packages/core/src/core/` and `packages/data_vault/src/data_vault/`
- [x] T053 [P] Implement durable layout persistence, reopen, unknown-version recovery, and compare-and-set tests in `packages/data_vault/src/data_vault/` and `tests/`
- [x] T054 [P] Implement durable run/step/activity/artifact records, cancellation, reconnect, and cleanup in `packages/core/src/core/`, `packages/data_vault/src/data_vault/`, and `tests/`
- [x] T055 Implement approved component/collapsed-graph and large-graph behavior in `apps/web/src/components/workflow-composer/` and `tests/ui-integration/`
- [ ] T056 Complete representative keyboard-only, 200% zoom, focus-order, screen-reader, and moderated engineer-usability gates in `tests/ui-integration/` and `specs/080-canonical-workflow-recovery/evidence/`
- [x] T057 Complete security, RBAC, secret-redaction, resource-isolation, and offline qualification in `tests/security/` and `tests/e2e/`
- [ ] T058 Complete independent engineering-oracle and benchmark qualification without changing the current `0/100` result until evidence passes in `benchmarks/` and `test-results/dataset-evaluation/`
- [x] T059 Run packaging, rollback, native lifecycle, Docker, and release-candidate hardening through the authoritative scripts in `scripts/` and `docs/release/release-runbook.md`
- [ ] T060 Run dev-push/merge/release gates only under separate authorization; do not push, merge, publish, or release from this recovery checkpoint in `docs/contributing/dev-push-runbook.md` and `docs/release/release-runbook.md`

---

## Phase 10: Mechanical-Engineer Usability Correction

**Goal**: Apply the requesting mechanical engineer's hands-on feedback without claiming completion of the wider moderated-usability or assistive-technology gates.

- [x] T061 Preserve a failed-first raw/annotated walkthrough checkpoint for the seven reported usability issues in `artifacts/ui-walkthrough/workflow-recovery-usability/20260901T135322Z/`
- [x] T062 Replace the fictional single PDF-brief input with three explicit sources—reference images, design intent as text/common document, and approved company context—feeding one reviewed design specification in the canonical model and UI
- [x] T063 Repair live drag projection, give the minimap an explicit current-view frame, remove decorative phase backdrops, use contextual downstream additions, move internal terminology behind progressive disclosure, and replace the oversized hero with a compact single-workflow-file/status bar
- [x] T064 Synchronize the revision-2 JSON, YAML, workflow-language, and layout fixtures and update browser, TypeScript, Python kernel, repository, security, and offline tests without rewriting historical revision-1 evidence
- [x] T065 Capture a fresh complete raw/annotated Playwright walkthrough, trace, diagnostics, status, manifest, and validated report against the exact committed correction subject
- [x] T066 Bind the user's direction approval and correction feedback honestly to that exact subject; refresh capability, parity, quickstart, analysis, dashboard, and approval evidence without inventing reviewer facts
- [x] T067 Run focused and broad validation, record the current one-engineer result, and leave T056 open for representative moderated participants and real screen-reader evidence

---

## Phase 11: Workspace-Owned Engineer Authoring Correction

**Purpose**: Apply the requesting mechanical engineer's workspace-ownership, single-page, and code-literate vocabulary direction without weakening the canonical model, typed commands, atomic persistence, or evidence gates.

**Independent Test**: Enter the canonical editor only by choosing Workflows from a real workspace; verify that a missing friendly `.workflow.wflow` file is idempotently bootstrapped and opened immediately, that repeated entry opens existing source unchanged, then edit the same definition in Diagram and Source, save and reopen it, preserve local edits across a stale compare-and-set failure, verify that the nine-step graph has no low-value search or phase backdrop, and complete the exact 1070×791 journey without document scrolling.

- [x] T068 Update `spec.md`, `plan.md`, `tasks.md`, and the requirements checklist so engineer-facing source vocabulary, optional groups, workspace ownership, host-managed metadata, atomic CAS persistence, fixed-height layout, and compatibility are explicit without weakening internal software-development terminology
- [x] T069 Remove global recovery/composer routes and navigation; expose canonical workflows only through an active workspace while preserving ordinary Rivet behavior in `apps/web/src/App.tsx`, `apps/web/src/components/layout/Sidebar.tsx`, `apps/web/src/components/chat/WorkspacePanel.tsx`, and their tests
- [x] T070 Split the friendly contextual public source from the full internal IR projection; lower valid source edits through the closed canonical command set, reject host-managed fields and unresolved structural edits, and synchronize exact TypeScript/Python fixtures and conformance evidence in `recovery-authoring.ts`, `command-system.ts`, and `specs/080-canonical-workflow-recovery/fixtures/`
- [x] T071 Implement path-confined, size-bounded, atomic compare-and-set storage for one visible workspace `.workflow.wflow` file with hidden host metadata and no creation from plain read or ordinary workspace entry in `packages/workspace_service/`, `apps/api/`, and focused tests
- [x] T072 Integrate typed load, the original explicit-create boundary, semantic save, saved/unsaved state, ordinary failure, stale-conflict containment, and read-only technical details in `workspace-service.ts`, `WorkflowRecoveryPage.tsx`, `WorkflowRecoveryConcept.tsx`, and focused tests (missing-file interaction superseded by T079)
- [x] T073 Remove low-value search from the nine-step graph, retain bounded search at 26 or more tasks, keep optional groups non-decorative, compact the file/status bar, and enforce the no-document-scroll 1070×791 workbench in the canvas, concept, and CSS component tests
- [x] T074 Update the workspace-entered Playwright journey and accessibility checks for the original missing-file create interaction, existing-file load, Diagram/Source correspondence, save, conflict containment, proposal/run/output behavior, exact viewport containment, and browser diagnostics in `tests/ui-integration/workflow-recovery*.spec.ts` (missing-file interaction superseded by T079)
- [x] T075 Run focused and broad API/service, Python conformance, Vitest, production build, mocked Playwright, accessibility, responsive, capability, freeze, and completion-audit gates; repair failures without changing the approved direction
- [x] T076 Create a coherent local implementation commit, then capture a fresh complete raw/annotated Playwright walkthrough, trace, diagnostics, status, manifest, and validated clickable report against that exact committed subject
- [x] T077 Bind the requesting user's recorded direction approval and subsequent workspace/vocabulary feedback honestly to the exact subject; refresh capability, parity, quickstart, Spec Kit analysis, dashboard, and approval evidence without inventing reviewer facts
- [x] T078 Record the current one-mechanical-engineer result and internal-versus-visible vocabulary boundary, keep T056 and T058 open, and leave push/merge/publication/release/customer actions unperformed
- [x] T079 Replace the missing-file confirmation state with workspace-scoped idempotent default bootstrap: entering Workflows creates and immediately opens the validated default only when absent, re-entry and first-entry races preserve existing source without identity advance, ordinary workspace/global entry creates nothing, and focused service/API/component/browser tests prove the boundary in `packages/workspace_service/`, `apps/api/`, `apps/web/src/components/pages/WorkflowRecoveryPage.tsx`, `apps/web/src/services/workspace-service.ts`, and their tests
- [x] T080 Apply the requesting engineer's latest graph-density correction: make the nine-step canvas overview-first, reduce connection-point chrome, hide edge and port metadata until focus/selection/inspection, collapse reusable-component internals behind one Details action, compact the layout, and pass focused component plus the complete 14-journey Chromium suite without weakening the accessible typed-port contract

---

## Phase 12: Approved Image-led UI and Functional Catch-up

**Authority**: Full user goal of 2026-09-02, attachment `690b7c98-cea6-44cc-bb49-9e5c4b726a85/pasted-text.txt`. This is implementation approval for the selected image and existing native foundation; it does not reopen T056/T058/T060 or rewrite their evidence.

**Independent acceptance**: Real input/object creation, exact connection, source/graph editing, invalid containment, undo/redo and save/reopen in the image-aligned workspace shell; truthful separate proposal/run simulation; matched-viewport visual review and fresh exact-subject walkthrough.

- [x] T081 Reconcile recovered image decisions and approval into `spec.md`, `plan.md`, `tasks.md`, and `evidence/image-redesign-checklist.md`; record a new baseline without claiming prior recovery counts prove the redesign
- [x] T082 [P] [US1] Add tested native object-template, deterministic placement, input-configuration/readiness and removal-impact helpers in `apps/web/src/prototypes/workflow-recovery/authoring-objects.ts` and `authoring-objects.spec.ts`
- [x] T083 [US1] Replace the permanent Inputs panel with Create rail, temporary input navigator, contextual collapsible Inspector, compact toolbar and bottom run panel in `WorkflowRecoveryConcept.tsx` and its focused tests
- [x] T084 [P] [US1] Implement image-aligned tokens, fixed-height responsive shell, compact icon-led nodes, distinct named connection disclosure, focus paths and minimap in `workflow-recovery.css`, `ReactFlowRecoveryCanvas.tsx` and focused renderer tests
- [x] T085 [P] [US1] Supply authorized workspace-file choices to input editing and default canonical editing to a collapsed agent pane in `WorkflowRecoveryPage.tsx`, `WorkspacePanel.tsx`, dedicated input adapter components and focused page/workspace tests
- [x] T086 [US2] Complete real persistent text/file configuration, generic draft template creation, safe deletion and graph/source round-trip of new objects through `authoring-objects.ts`, `recovery-authoring.ts`, `command-system.ts` and focused tests without a second model
- [x] T087 [US3] Preserve review-only proposal acceptance/rejection and explicit unbound/simulated limitations in `WorkflowRecoveryConcept.tsx` and focused tests; remove misleading control labels and fabricated status claims
- [x] T088 [US4] Preserve supported simulated run/recovery/output lineage and implement non-overlay bottom details in `WorkflowRecoveryConcept.tsx` and browser tests
- [x] T089 [US5] Capture early shell and final matched-image/1537×791/1070×791/narrow/200%-zoom visual states, repair legibility and interaction failures, and obtain independent internal review in `artifacts/ui-walkthrough/image-redesign/` and `evidence/image-redesign-review.md`
- [x] T090 Run focused and proportionate broader conformance/API/service/web/build/browser/accessibility/freeze checks; record exact commands and outcomes in `evidence/image-redesign-validation.md`
- [x] T091 Create coherent local implementation commit and fresh exact-subject raw/annotated walkthrough, trace, diagnostics, manifest and validated report with the served-code/workspace identity verified in `scripts/recovery/` and `artifacts/ui-walkthrough/image-redesign/`
- [x] T092 Refresh capability/parity/quickstart/Spec Kit analysis and live dashboard for the actual redesign; leave the verified application running and record exact URL, screenshots, remaining limitations and delivery state in `evidence/image-redesign-checklist.md`

T081 precedes product changes. T082/T083/T084/T085 use disjoint files and may
proceed in parallel; an early integrated T083/T084 shell is inspected before
broad validation. T086 integrates helper/source/storage behavior; T087/T088
preserve the existing bounded simulations. T089–T092 consume the integrated
candidate, with failed evidence kept and final claims bound to its exact subject.

## Dependencies & Execution Order (historical phases)

### Phase dependencies

- **Phase 1** establishes the immutable baseline and isolated route.
- **Phase 2** depends on Phase 1 and blocks every user-story claim.
- **US1 and US2** both depend on Phase 2 and together form the P1 recovery MVP.
- **US3** depends on the shared command/revision boundary from US2, but remains independently testable by proposal reject/accept.
- **US4** depends on the canonical definition from Phase 2, but run records remain authority-separated and independently testable.
- **US5** consumes completed US1–US4 evidence and must close before product review.
- **T051** depends on T046–T050.
- **T052–T060** depend on an approved T051 exact subject and separate implementation authorization.
- **T061–T067** form the first bounded correction loop triggered by the requesting mechanical engineer's hands-on feedback; their remaining evidence work is superseded by the more complete T068–T080 loop.
- **T068–T073** implement the workspace/source correction and may proceed in dependency-safe parallel slices; T074 follows their integrated interfaces, T075 validates the whole subject, T079 applies the first-entry correction, and T080 applies the latest hands-on graph-density correction. T076 may commit and capture the exact subject only after the T079–T080 implementation and rerun gates pass; only then may T077–T078 close.

### User-story completion order

```text
Setup → Canonical foundation → {US1, US2} → {US3, US4} → US5 → T051 approval STOP
                                                                   |
                                                                   ├─ approved + separately authorized → T052–T060
                                                                   └─ hands-on correction → T061–T067
                                                                                              ↓
                                                               workspace/source correction → T068–T075 → T079–T080 → T076–T078 → refreshed exact subject
```

### Parallel opportunities

- T006 and T007 can run in parallel after setup. T009 and T010 can run in parallel only after T008. T013 starts after T012. T014 starts after T009, T010, and T012; T015 starts after T014.
- US1 renderer tests, attachment fixtures, and port-lab evidence touch separate files.
- US2 kernel tests and browser correspondence tests can run in parallel after the adapter exists.
- US3 proposal unit tests and graphical-candidate implementation can proceed in parallel against the same frozen command contract.
- US4 fixture verification and run-projection tests can proceed in parallel.
- T044 and T045 can run in parallel; T047 walkthrough capture must use the fully verified subject from T046.
- Post-approval T053/T054 may run in parallel only after T052 fixes the promoted version/migration boundary.
- T074 can run after T069–T073 stabilize; T075 validation may overlap independent stacks. T079's first-entry correction and T080's overview-density correction plus their focused tests must pass before T076 exact-subject capture. Documentation/dashboard/approval work in T077–T078 may proceed only against the captured exact subject.

## Parallel examples

```text
US1: T016 browser journey || T017 adapter projection tests || T021 attachment fixtures || T022 port lab
US2: T024 kernel/command tests || T025 correspondence browser assertions
US3: T030 browser proposal review || T031 atomic candidate unit tests
US4: T036 run browser journey || T037 fixture digest verification
US5: T044 parity documentation || T045 capability audit
```

## Implementation strategy

1. Preserve the frozen Checkpoint D subject and do not resume spec 079 T028–T038.
2. Treat Phase 2 plus US1/US2 as the minimum product-recovery foundation.
3. Add AI review and simulated run evidence without granting either authority.
4. Complete T046–T050 against one exact worktree subject.
5. Bind an exact subject to the user's recorded product-direction approval at T051 only when it remains materially equivalent to the reviewed experience.
6. Apply the user's subsequent hands-on corrections through T061–T080, preserving failed-first evidence and producing a new exact-subject walkthrough rather than treating the earlier approval as proof of the changed implementation.
7. Continue only dependency-ordered locally safe work explicitly covered by the user's authorization; push, merge, publication, release, destructive external actions, and materially different product direction remain prohibited.

## Notes

- `[P]` means different-file parallel work, not permission for multiple writers to mutate shared state.
- Every interaction keeps a stable `data-testid`; no test ID is semantic authority.
- The recovery DSL, React Flow renderer, in-memory host, and static output fixtures remain disposable until approved and deliberately promoted.
- The STEP/report fixtures prove recognizable actions and truthful labeling, not generated geometry correctness.
- No task in this file authorizes push, merge, publication, customer action, or release.
