# Tasks: Canonical Workflow Recovery

**Input**: Design documents from `specs/080-canonical-workflow-recovery/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`

**Scope rule**: Tasks T001–T050 form the recovery evidence slice. T051 is the mandatory product/visual approval stop. T052–T060 are explicitly deferred and MUST NOT start until T051 records an approved exact subject.

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
- [x] T005 Add the lazy guarded `/workflow-recovery` route and navigation in `apps/web/src/App.tsx`, `apps/web/src/components/layout/Sidebar.tsx`, and `apps/web/src/components/pages/WorkflowRecoveryPage.tsx`

---

## Phase 2: Canonical Recovery Foundation

**Purpose**: Establish one complete IR, separate authority boundaries, exhaustive source coverage, and a shared conformance rule before product-story work.

**Critical gate**: No user-story claim is valid unless the canonical fixture round-trips through every adapter without semantic loss.

- [x] T006 [P] Inventory all 555 uniquely keyed requirement, gate, story, lesson, and prior-spec sources in `scripts/recovery/audit_capability_coverage.py` and `specs/080-canonical-workflow-recovery/capability-source-map.csv`
- [x] T007 [P] Define the canvas-first product authority and supersession boundary in `specs/080-canonical-workflow-recovery/north-star.md`
- [x] T008 Define canonical IR, layout, proposal, renderer, and run decisions in `specs/080-canonical-workflow-recovery/decisions/0001-canonical-workflow-ir-vnext.md` and `specs/080-canonical-workflow-recovery/data-model.md`
- [x] T009 [P] Publish the complete vNext wire schema and contracts in `specs/080-canonical-workflow-recovery/contracts/canonical-workflow-ir.schema.json` and `specs/080-canonical-workflow-recovery/contracts/`
- [x] T010 [P] Create semantically identical JSON, YAML, and workflow-DSL fixtures in `specs/080-canonical-workflow-recovery/fixtures/`
- [x] T011 Measure identical syntax tasks and preserve the non-permanent syntax conclusion in `scripts/recovery/evaluate_workflow_syntaxes.py` and `specs/080-canonical-workflow-recovery/evidence/syntax-evaluation.md`
- [x] T012 Implement the strict renderer-neutral Python conformance kernel in `scripts/recovery/workflow_conformance.py`
- [x] T013 [P] Prove Python parse/format/validate/apply/diff invariants in `tests/recovery/test_workflow_conformance.py`
- [x] T014 Build the lossless snake_case wire adapter, ergonomic view, DSL, and shared command bridge in `apps/web/src/prototypes/workflow-recovery/canonical-wire.ts`, `model.ts`, `recovery-dsl.ts`, and `command-system.ts`
- [x] T015 [P] Prove the TypeScript view equals the committed wire and DSL fixtures in `apps/web/src/prototypes/workflow-recovery/command-system.spec.ts` and `model.spec.ts`

**Checkpoint**: Canonical fixture, syntax evidence, adapters, and atomic command boundary are independently testable.

---

## Phase 3: User Story 1 — Build a Mechanical Workflow Graphically (Priority: P1) — MVP

**Goal**: Let an engineer understand and manipulate a typed mounting-bracket workflow on the canvas without opening Code.

**Independent Test**: Search and add a block, move it, connect and disconnect typed ports, preview/replace the brief, inspect a gate and feedback path, delete a safe block, and undo/redo while stable identities remain visible.

### Tests for User Story 1

- [x] T016 [P] [US1] Add page-level palette, add/delete, undo/redo, attachment, configuration, pointer-handle, and keyboard-handle coverage in `tests/ui-integration/workflow-recovery.spec.ts`
- [x] T017 [P] [US1] Add adapter gate/feedback and unphased-component projection tests in `apps/web/src/prototypes/workflow-recovery/model.spec.ts`

### Implementation for User Story 1

- [x] T018 [US1] Implement the provisional React Flow renderer behind the retained adapter in `apps/web/src/prototypes/workflow-recovery/ReactFlowRecoveryCanvas.tsx`
- [x] T019 [US1] Implement typed left/right handles, canonical relationship labels, gate/feedback notation, and separate artifact actions in `apps/web/src/prototypes/workflow-recovery/ReactFlowRecoveryCanvas.tsx`
- [x] T020 [US1] Route add, move, connect, disconnect, configure, delete, undo, and redo gestures through atomic host commands in `apps/web/src/prototypes/workflow-recovery/WorkflowRecoveryConcept.tsx`
- [x] T021 [P] [US1] Implement searchable engineering blocks and the brief preview/replace fixture in `apps/web/src/prototypes/workflow-recovery/WorkflowRecoveryConcept.tsx` and `apps/web/public/recovery-concept/`
- [x] T022 [P] [US1] Build the three-treatment interactive port laboratory and evidence record in `apps/web/src/prototypes/workflow-recovery/WorkflowRecoveryConcept.tsx` and `specs/080-canonical-workflow-recovery/evidence/block-port-lab.md`
- [x] T023 [US1] Apply responsive, focus, non-color, selected, and phase-secondary visual language in `apps/web/src/prototypes/workflow-recovery/workflow-recovery.css`

**Checkpoint**: User Story 1 works independently in Diagram view; implementation bindings remain progressive disclosure.

---

## Phase 4: User Story 2 — Edit One Workflow in Diagram and Code (Priority: P1)

**Goal**: Make Diagram, Code, Split, and Inspector lossless views of one accepted definition.

**Independent Test**: Move a block without changing semantic digest, apply a valid Code title change, select concepts in both directions, then apply invalid source and confirm the last-valid graph/revision remains authoritative.

### Tests for User Story 2

- [x] T024 [P] [US2] Prove exact golden wire/DSL round trips, parsed text commands, layout isolation, stale bases, and invalid atomic containment in `apps/web/src/prototypes/workflow-recovery/command-system.spec.ts`
- [x] T025 [P] [US2] Add graph-to-source, source-to-inspector, valid edit, invalid containment, and digest-isolation browser assertions in `tests/ui-integration/workflow-recovery.spec.ts`

### Implementation for User Story 2

- [x] T026 [US2] Implement deterministic format/parse/source-map behavior for the disposable Code treatment in `apps/web/src/prototypes/workflow-recovery/recovery-dsl.ts`
- [x] T027 [US2] Canonicalize semantic equality and digest input with stable snake_case wire keys in `apps/web/src/prototypes/workflow-recovery/command-system.ts` and `WorkflowRecoveryConcept.tsx`
- [x] T028 [US2] Implement Diagram, Code, Split, last-valid source containment, and shared selection in `apps/web/src/prototypes/workflow-recovery/WorkflowRecoveryConcept.tsx`
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

**Independent Test**: Capture an immutable six-block run subject, advance through queued/running/needs-input/recovered/succeeded, inspect active flow and tabs, open/download the static STEP/report fixtures, then project failure and confirm downstream/output invalidation.

### Tests for User Story 4

- [x] T036 [P] [US4] Add queued, active, needs-input, recovery, success, output, failure, downstream-blocking, and immutable-revision browser assertions in `tests/ui-integration/workflow-recovery.spec.ts`
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
- [x] T045 [P] [US5] Verify capability coverage remains 555/555 with current recovery completion gates retained in `scripts/recovery/audit_capability_coverage.py` and `specs/080-canonical-workflow-recovery/evidence/capability-coverage.json`
- [x] T046 [US5] Run and record conformance, focused Vitest, web build, full recovery Chromium, accessibility, responsive, and package-lock dry-run gates in `specs/080-canonical-workflow-recovery/quickstart.md`
- [ ] T047 [US5] Capture the complete raw/annotated Playwright walkthrough, trace, browser diagnostics, manifest, status, and traffic-light report in `artifacts/ui-walkthrough/workflow-recovery/<timestamp>/`
- [ ] T048 [US5] Bind exact walkthrough paths into `specs/080-canonical-workflow-recovery/capability-inventory.md` and create frozen-versus-recovery evidence in `specs/080-canonical-workflow-recovery/evidence/prototype-side-by-side.md`
- [ ] T049 [US5] Refresh the reachable progress dashboard with recovery goal, tasks, artifacts, screenshot gallery, newest-first history, pending product approval, and incomplete customer readiness in `C:/Users/markb/.codex/visualizations/2026/08/30/01a054ae-39b1-7c40-8d8a-d4dc5af9c45f/wright-status-dashboard/`
- [ ] T050 [US5] Validate program-roadmap dependency, freeze immutability, Spec Kit consistency, and agent context; record results in `specs/080-canonical-workflow-recovery/evidence/specification-analysis.md` and `AGENTS.md`

**Checkpoint**: Recovery evidence is complete and the exact subject is ready for product review; customer readiness is still incomplete.

---

## Phase 8: Mandatory Product / Visual Approval Stop

**Purpose**: Stop all broader work until a human reviews the exact recovery subject.

- [ ] T051 Conduct and record explicit product/visual approval for the digest-bound walkthrough and recovery commit in `specs/080-canonical-workflow-recovery/evidence/product-approval.md`

**STOP**: T052–T060 are blocked unless T051 records an approved exact commit, tree, walkthrough manifest digest, reviewer, decision, and allowed next action. Rejection or requested changes create a new bounded recovery iteration instead.

---

## Phase 9: Post-Approval Production Work — Deferred

**Purpose**: Preserve remaining capability work without implying authorization or readiness.

- [ ] T052 Promote only approved IR/kernel/renderer concepts into production boundaries with migrations and rollback in `packages/core/src/core/` and `packages/data_vault/src/data_vault/`
- [ ] T053 [P] Implement durable layout persistence, reopen, unknown-version recovery, and compare-and-set tests in `packages/data_vault/src/data_vault/` and `tests/`
- [ ] T054 [P] Implement durable run/step/activity/artifact records, cancellation, reconnect, and cleanup in `packages/core/src/core/`, `packages/data_vault/src/data_vault/`, and `tests/`
- [ ] T055 Implement approved component/collapsed-graph and large-graph behavior in `apps/web/src/components/workflow-composer/` and `tests/ui-integration/`
- [ ] T056 Complete representative keyboard-only, 200% zoom, focus-order, screen-reader, and moderated engineer-usability gates in `tests/ui-integration/` and `specs/080-canonical-workflow-recovery/evidence/`
- [ ] T057 Complete security, RBAC, secret-redaction, resource-isolation, and offline qualification in `tests/security/` and `tests/e2e/`
- [ ] T058 Complete independent engineering-oracle and benchmark qualification without changing the current `0/100` result until evidence passes in `benchmarks/` and `test-results/dataset-evaluation/`
- [ ] T059 Run packaging, rollback, native lifecycle, Docker, and release-candidate hardening through the authoritative scripts in `scripts/` and `docs/release/release-runbook.md`
- [ ] T060 Run dev-push/merge/release gates only under separate authorization; do not push, merge, publish, or release from this recovery checkpoint in `docs/contributing/dev-push-runbook.md` and `docs/release/release-runbook.md`

---

## Dependencies & Execution Order

### Phase dependencies

- **Phase 1** establishes the immutable baseline and isolated route.
- **Phase 2** depends on Phase 1 and blocks every user-story claim.
- **US1 and US2** both depend on Phase 2 and together form the P1 recovery MVP.
- **US3** depends on the shared command/revision boundary from US2, but remains independently testable by proposal reject/accept.
- **US4** depends on the canonical definition from Phase 2, but run records remain authority-separated and independently testable.
- **US5** consumes completed US1–US4 evidence and must close before product review.
- **T051** depends on T046–T050.
- **T052–T060** depend on an approved T051 exact subject and separate implementation authorization.

### User-story completion order

```text
Setup → Canonical foundation → {US1, US2} → {US3, US4} → US5 → T051 approval STOP
                                                                   |
                                                                   └─ approved + separately authorized → T052–T060
```

### Parallel opportunities

- T006/T007/T009/T010 and T013 can be performed in parallel after setup.
- US1 renderer tests, attachment fixtures, and port-lab evidence touch separate files.
- US2 kernel tests and browser correspondence tests can run in parallel after the adapter exists.
- US3 proposal unit tests and graphical-candidate implementation can proceed in parallel against the same frozen command contract.
- US4 fixture verification and run-projection tests can proceed in parallel.
- T044 and T045 can run in parallel; T047 walkthrough capture must use the fully verified subject from T046.
- Post-approval T053/T054 may run in parallel only after T052 fixes the promoted version/migration boundary.

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
5. Stop at T051 for human product/visual review.
6. Start no production, accessibility-hardening, packaging, push, merge, or release task unless T051 and a later control-plane transition explicitly authorize it.

## Notes

- `[P]` means different-file parallel work, not permission for multiple writers to mutate shared state.
- Every interaction keeps a stable `data-testid`; no test ID is semantic authority.
- The recovery DSL, React Flow renderer, in-memory host, and static output fixtures remain disposable until approved and deliberately promoted.
- The STEP/report fixtures prove recognizable actions and truthful labeling, not generated geometry correctness.
- No task in this file authorizes push, merge, publication, customer action, or release.
