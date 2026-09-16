# Tasks: Engineering Workflow Templates

**Testing supplement (2026-09-12):** Track the thirty-dataset unattended
integration cycle in [dataset-campaign/tasks.md](dataset-campaign/tasks.md).
Its file-presence completion does not check off engineering-correctness or
live printer/supplier qualification tasks below.

**Approved recovery supplement (September 12, recorded September 13 UTC):**
Use campaign DC012–DC025 for operation probes, pilot-first recovery, native
application lifecycle, resource scheduling and efficiency diagnostics. Existing
checked parent tasks retain their historical meaning; documentation updates do
not claim implementation or additional completed engineering runs.

**Input**: Design documents from `specs/081-engineering-workflow-templates/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`

**Tests**: Required by FR-010, FR-019, FR-021, FR-023–FR-025 and SC-002–SC-010. Contract/component/system tests precede their implementation tasks.

**Organization**: Tasks are grouped by user story. User Story 1 is the UI-first milestone; User Story 2 contains the shared execution foundation and three flagship workflows; User Story 3 promotes the seven follow-on workflows one at a time; User Story 4 adds local social capture.

## Phase 1: Setup and Baseline

**Purpose**: Freeze the correct editor/runtime baseline and prepare bounded feature resources.

- [X] T001 Record the current branch, relevant dirty paths, recovered feature-080 editor source/evidence identity, and implementation ownership in `specs/081-engineering-workflow-templates/implementation-log.md`
- [X] T002 Verify existing root, Docker, ESLint and Prettier ignore rules cover Python/TypeScript/test/capture outputs without changing unrelated files; record the result in `specs/081-engineering-workflow-templates/implementation-log.md`
- [X] T003 [P] Create the engineering template package skeleton and resource README in `packages/workspace_service/src/workspace_service/engineering_workflow_templates/README.md`
- [X] T004 [P] Create shared template test fixture helpers in `packages/workspace_service/tests/engineering_workflow_template_fixtures.py`

---

## Phase 2: Foundational Contracts

**Purpose**: Implement the immutable catalog and fresh-instance domain boundaries used by every story.

**CRITICAL**: Complete before user-story implementation.

- [X] T005 [P] Write catalog/domain tests for exact ten IDs, versions, resource digests, safe paths, rights metadata, source validity, fresh semantic identities and deterministic order in `packages/workspace_service/tests/test_engineering_workflow_templates.py`
- [X] T006 [P] Write workspace instance service tests for atomic exclusive creation, idempotency, collision, no imported runs/approvals/credentials and separate layout/provenance in `packages/workspace_service/tests/test_engineering_workflow_template_instances.py`
- [X] T007 Implement immutable catalog values, validation and readiness fact types in `packages/core/src/core/engineering_workflow_templates.py`, plus packaged-resource loading and fresh-instance transformation in `packages/workspace_service/src/workspace_service/engineering_workflow_templates/__init__.py`
- [X] T008 Implement workspace-scoped list/detail/readiness/instantiate use cases over canonical workflow source/layout services in `packages/workspace_service/src/workspace_service/engineering_workflow_template_service.py`
- [X] T009 Wire the template service through existing workspace composition in `packages/workspace_service/src/workspace_service/service.py`
- [X] T010 Run the Phase 2 tests and record exact command/results in `specs/081-engineering-workflow-templates/implementation-log.md`

**Checkpoint**: The catalog can be loaded and validated, and a template can become a fresh canonical workspace source without a UI.

---

## Phase 3: User Story 1 — Start from a real engineering example (Priority: P1) MVP

**Goal**: Show exactly ten truthful engineering templates inside the established Workflows editor and create a fresh editable copy without reducing authoring capability.

**Independent Test**: From a normal workspace, inspect all ten templates, create each under a fresh name, cancel without mutation, exercise setup/reference states, and verify edit/save/reopen/drag/connect/source/undo/redo/conflict behavior through the served build.

### Tests for User Story 1

- [X] T011 [P] [US1] Write API contract tests for list/detail/readiness/instantiate, workspace/RBAC failures, digest/version mismatch and idempotency in `apps/api/tests/test_engineering_workflow_template_api.py`
- [X] T012 [P] [US1] Write frontend client tests for catalog and instance endpoints/error mapping in `apps/web/src/services/workspace-service.spec.ts`
- [X] T013 [P] [US1] Write template dialog component tests for ten options, details, readiness states, keyboard/focus behavior, name validation, cancellation, collision and success in `apps/web/src/prototypes/workflow-recovery/EngineeringTemplateDialog.spec.tsx`
- [X] T014 [P] [US1] Add mocked workspace journey tests for Start from template and preserved editor entry in `tests/ui-integration/engineering-workflow-templates.spec.ts`

### Implementation for User Story 1

- [X] T015 [P] [US1] Author the exact ten reviewed catalog entries with truthful initial readiness and attribution in `packages/workspace_service/src/workspace_service/engineering_workflow_templates/catalog.yaml`
- [X] T016 [P] [US1] Author ten valid canonical starter definitions and separate layouts in `packages/workspace_service/src/workspace_service/engineering_workflow_templates/templates/` and `packages/workspace_service/src/workspace_service/engineering_workflow_templates/layouts/`
- [X] T017 [P] [US1] Add ten local preview assets and their rights/alt-text manifest in `packages/workspace_service/src/workspace_service/engineering_workflow_templates/previews/`
- [X] T018 [US1] Add template request/response models to `apps/api/src/api/schemas/workspace.py`
- [X] T019 [US1] Add thin canonical template list/detail/readiness/instance routes to `apps/api/src/api/routers/workspace.py`
- [X] T020 [US1] Add typed template/readiness/instance clients to `apps/web/src/services/workspace-service.ts`
- [X] T021 [US1] Implement the accessible ten-option detail/create dialog in `apps/web/src/prototypes/workflow-recovery/EngineeringTemplateDialog.tsx`
- [X] T022 [US1] Add token-based dialog and readiness styling in `apps/web/src/prototypes/workflow-recovery/engineering-template-dialog.css`
- [X] T023 [US1] Integrate Start from template beside New/Open and open the created canonical file in `apps/web/src/components/pages/WorkflowRecoveryPage.tsx`
- [X] T024 [US1] Run backend/frontend/component/UI-integration tests, resolve regressions in the Phase 3 files, and record local performance bounds in `specs/081-engineering-workflow-templates/implementation-log.md`
- [X] T025 [US1] Verify the served UI through a normal workspace Workflow/Workflows control, preserve all required authoring actions, and record exact browser evidence in `specs/081-engineering-workflow-templates/evidence/ui-milestone.md`

**Checkpoint**: User Story 1 is a reviewable UI-first increment. All ten templates are editable; their live readiness remains truthful.

---

## Phase 4: User Story 2 — Run the three flagship workflows (Priority: P2)

**Goal**: Add generic evidence, approvals and safe continuation, then make the three flagship workflows produce real independently checked outputs and stop at exact external-action gates.

**Independent Test**: Run each flagship chain with its distributable fixture and selected qualified integrations; inspect every declared artifact; exercise one meaningful negative/correction path; mutate every approval subject component; and prove no printer/supplier action occurs without a fresh exact decision.

### Tests for shared execution foundation

- [X] T026 [P] [US2] Write repository/migration tests for checkpoints, continuations and external-action records, including state races and recovery in `packages/data_vault/tests/test_workflow_continuation_repository.py`
- [X] T027 [P] [US2] Write service tests for exact subject digests, actor/workspace authorization, stale/expired/denied/consumed decisions, safe resume and unknown-outcome reconciliation in `packages/workspace_service/tests/test_workflow_approval_resume.py`
- [X] T028 [P] [US2] Write engineering assertion tests for artifact identity, geometry/units/topology, field-derived values, convergence/balance and sensitivity in `packages/workspace_service/tests/test_workflow_engineering_assertions.py`
- [X] T029 [P] [US2] Write API/UI tests for awaiting-approval detail, decision, resume and external-action outcome states in `apps/api/tests/test_workflow_approval_resume_api.py` and `apps/web/src/prototypes/workflow-recovery/WorkflowRecoveryConcept.spec.tsx`

### Shared execution foundation

- [X] T030 [US2] Add additive checkpoint/continuation/external-action schema and repositories in `packages/data_vault/src/data_vault/workflow_continuation_repository.py` and `packages/data_vault/src/data_vault/migrations.py`
- [X] T031 [US2] Implement canonical approval subjects, decisions, resume validation, one-shot dispatch and reconciliation in `packages/workspace_service/src/workspace_service/workflow_external_actions.py`
- [X] T032 [US2] Implement generic versioned engineering assertions and artifact roles in `packages/workspace_service/src/workspace_service/workflow_engineering_assertions.py` and `packages/workspace_service/src/workspace_service/workflow_results.py`
- [ ] T033 [US2] Extend canonical compile/run recording for durable awaiting-approval and safe continuation without weakening existing terminal review in `packages/workspace_service/src/workspace_service/workflow_source_execution.py` and `packages/workspace_service/src/workspace_service/workflow_run_record.py` — reopened 2026-09-12: prior checkpoint persistence evidence did not prove actual execution through multiple approvals to the terminal step; campaign DC006 supplies the missing runtime evidence.
- [X] T034 [US2] Add thin decision/resume/reconcile endpoints and schemas in `apps/api/src/api/routers/workspace.py` and `apps/api/src/api/schemas/workspace.py`
- [X] T035 [US2] Surface exact approval subjects, stale/unknown outcomes and resume actions in `apps/web/src/prototypes/workflow-recovery/WorkflowRecoveryConcept.tsx` and `apps/web/src/services/workspace-service.ts`
- [ ] T036 [US2] Run shared approval/assertion/restart/cancel tests and record evidence in `specs/081-engineering-workflow-templates/evidence/execution-foundation.md` — reopened 2026-09-12: retain earlier passing evidence, but require actual resumed multi-checkpoint execution and crash-boundary coverage before closing this broader task.

### 3D Printed Replacement Part

- [X] T037 [P] [US2] Create distributable original image/scale fixture and input-rights record in `packages/workspace_service/src/workspace_service/engineering_workflow_templates/inputs/printed-replacement-part/`
- [ ] T038 [US2] Qualify and record the selected image-to-mesh, repair/orientation, support/slicer and P1S transfer adapters under `docs/mcp-catalog/evidence/engineering-workflow-templates/printed-replacement-part/` following the clean-container/selected-host process
- [X] T039 [US2] Implement generic mesh/slice/package verification and printer-transfer external action in `packages/workspace_service/src/workspace_service/workflow_additive_manufacturing.py`
- [ ] T040 [US2] Replace the starter definition with the qualified complete 3D-print workflow and exact assertions in `packages/workspace_service/src/workspace_service/engineering_workflow_templates/templates/printed-replacement-part.workflow.wflow`
- [ ] T041 [US2] Add real-chain, wrong-scale/non-manifold/build-volume and stale-printer-approval tests in `tests/external/engineering_workflow_templates/test_printed_replacement_part.py`

### Sheet-Metal Supplier Handoff

- [X] T042 [P] [US2] Curate distributable sheet-metal image/text/context fixtures from the recovered workspace without copying credentials/private state in `packages/workspace_service/src/workspace_service/engineering_workflow_templates/inputs/sheet-metal-supplier-handoff/`
- [X] T043 [US2] Port the recovered design/check/two-revision/CAD/export/DXF/supplier/user-handoff definition into `packages/workspace_service/src/workspace_service/engineering_workflow_templates/templates/sheet-metal-supplier-handoff.workflow.wflow`
- [X] T044 [US2] Extend supplier-preview assertions and exact no-order handoff action in `packages/workspace_service/src/workspace_service/workflow_supplier_handoff.py`
- [ ] T045 [US2] Qualify the selected current Solid Edge and browser supplier-preview path and record refreshed source conflicts/results in `docs/mcp-catalog/evidence/engineering-workflow-templates/sheet-metal-supplier-handoff/`
- [ ] T046 [US2] Add real-chain, two-revision, failed-DXF, stale-package, inconclusive-quote and no-order tests in `tests/external/engineering_workflow_templates/test_sheet_metal_supplier_handoff.py`

### Vented Raspberry Pi Enclosure

- [X] T047 [P] [US2] Add the attributable Raspberry Pi 5 manufacturer reference fixture and extraction expectations in `packages/workspace_service/src/workspace_service/engineering_workflow_templates/inputs/raspberry-pi-enclosure/`
- [ ] T048 [US2] Qualify AgentCAD D001 and Foam-Agent D040 or contract-equivalent replacements and record exact setup/backend/Wright/artifact evidence in `docs/mcp-catalog/evidence/engineering-workflow-templates/raspberry-pi-enclosure/`
- [X] T049 [US2] Implement manufacturer-reference, CAD/domain identity and CFD field/convergence/balance/sensitivity assertions in `packages/workspace_service/src/workspace_service/workflow_enclosure_cfd.py`
- [X] T050 [US2] Replace the starter definition with the complete sourced-document/AgentCAD/CFD comparison workflow in `packages/workspace_service/src/workspace_service/engineering_workflow_templates/templates/raspberry-pi-enclosure.workflow.wflow`
- [ ] T051 [US2] Add real-chain, conflicting-source, substituted-domain and theoretical-only-result tests in `tests/external/engineering_workflow_templates/test_raspberry_pi_enclosure.py`

### Flagship integration

- [ ] T052 [US2] Run all three flagship workflows through API and served workspace UI, verify artifacts/negative paths/capture-ready lineage, and record exact subjects in `specs/081-engineering-workflow-templates/evidence/flagship-workflows.md`

**Checkpoint**: User Story 2 is complete only when all three chains have current real evidence. Simulator or source-backed-only evidence keeps the affected template in setup-required state and the task open.

---

## Phase 5: User Story 3 — Explore seven more engineering demonstrations (Priority: P3)

**Goal**: Promote each additional template from a truthful reference definition to independently verified runnable status.

**Independent Test**: Instantiate every template, verify its contracted inputs/outputs/assertions, and for each promoted workflow run one real positive chain plus one negative/recovery case under its exact qualified integration subject.

### Tests and implementation for User Story 3

- [X] T053 [P] [US3] Add shared promotion-gate tests proving fixture/discovery/protocol-only evidence cannot set ready/verified in `packages/workspace_service/tests/test_engineering_template_promotion.py`
- [ ] T054 [US3] Qualify and complete Parametric Drill Jig inputs, definition, output assertions and negative keepout case in `packages/workspace_service/src/workspace_service/engineering_workflow_templates/templates/parametric-drill-jig.workflow.wflow` and `docs/mcp-catalog/evidence/engineering-workflow-templates/parametric-drill-jig/`
- [ ] T055 [US3] Qualify and complete Conduction Heat-Spreader Sizing with analytical/balance/mesh checks in `packages/workspace_service/src/workspace_service/engineering_workflow_templates/templates/heat-spreader-sizing.workflow.wflow` and `docs/mcp-catalog/evidence/engineering-workflow-templates/heat-spreader-sizing/`
- [ ] T056 [US3] Qualify and complete Lightweight Equipment Bracket with actual CAD-to-mesh/stress/mass checks in `packages/workspace_service/src/workspace_service/engineering_workflow_templates/templates/lightweight-equipment-bracket.workflow.wflow` and `docs/mcp-catalog/evidence/engineering-workflow-templates/lightweight-equipment-bracket/`
- [ ] T057 [US3] Qualify and complete Sensor-Interface PCB with connectivity/ERC/DRC/export checks in `packages/workspace_service/src/workspace_service/engineering_workflow_templates/templates/sensor-interface-pcb.workflow.wflow` and `docs/mcp-catalog/evidence/engineering-workflow-templates/sensor-interface-pcb/`
- [ ] T058 [US3] Qualify and complete Robot Tracking Diagnosis with independent alignment/RMSE/event checks in `packages/workspace_service/src/workspace_service/engineering_workflow_templates/templates/robot-tracking-diagnosis.workflow.wflow` and `docs/mcp-catalog/evidence/engineering-workflow-templates/robot-tracking-diagnosis/`
- [ ] T059 [US3] Qualify and complete Sensor-and-Fan Wiring Harness with netlist/rating/drop checks in `packages/workspace_service/src/workspace_service/engineering_workflow_templates/templates/sensor-fan-harness.workflow.wflow` and `docs/mcp-catalog/evidence/engineering-workflow-templates/sensor-fan-harness/`
- [ ] T060 [US3] Qualify and complete Water-Heater Power Sizing with target/energy/timestep checks in `packages/workspace_service/src/workspace_service/engineering_workflow_templates/templates/water-heater-sizing.workflow.wflow` and `docs/mcp-catalog/evidence/engineering-workflow-templates/water-heater-sizing/`
- [ ] T061 [US3] Run all seven through API and served UI, verify status promotion and negative/recovery evidence, and record exact results in `specs/081-engineering-workflow-templates/evidence/follow-on-workflows.md`

**Checkpoint**: All ten workflows are independently verified under their named evidence subjects.

---

## Phase 6: User Story 4 — Capture honest demonstration material (Priority: P4)

**Goal**: Produce local, redacted, lineage-bound visual/caption packages from verified runs without publishing.

**Independent Test**: Capture each flagship run, resolve every claim/visual to run artifacts, reject a secret/private/unlicensed input, and prove no connector or external account is contacted.

### Tests for User Story 4

- [X] T062 [P] [US4] Write capture manifest, rights, redaction, lineage and no-publish tests in `packages/workspace_service/tests/test_workflow_demo_capture.py`
- [X] T063 [P] [US4] Write capture action UI tests for eligible/ineligible runs and local download in `apps/web/src/prototypes/workflow-recovery/WorkflowRecoveryConcept.spec.tsx`

### Implementation for User Story 4

- [X] T064 [US4] Implement local capture manifest/render selection/redaction service in `packages/workspace_service/src/workspace_service/workflow_demo_capture.py`
- [X] T065 [US4] Add thin local capture endpoint and typed client in `apps/api/src/api/routers/workspace.py`, `apps/api/src/api/schemas/workspace.py`, and `apps/web/src/services/workspace-service.ts`
- [X] T066 [US4] Add capture action/status/download to verified run details in `apps/web/src/prototypes/workflow-recovery/WorkflowRecoveryConcept.tsx`
- [ ] T067 [US4] Generate and verify local capture packages for the three flagship evidence runs under `specs/081-engineering-workflow-templates/evidence/captures/`

**Checkpoint**: Verified runs can create honest local material; Wright contains no social publishing path.

---

## Phase 7: Polish and Cross-Cutting Validation

- [X] T068 [P] Update user/developer documentation for template readiness, setup, approvals and capture in `docs/workflows/engineering-workflow-templates.md`
- [X] T069 [P] Add structured trace assertions for list/instantiate/readiness/run/approval/resume/action/assertion/capture in `tests/e2e/test_engineering_workflow_template_tracing.py`
- [X] T070 Run focused Python/TypeScript/UI suites once, resolve only observed failures in feature-owned files, and record commands/results in `specs/081-engineering-workflow-templates/evidence/candidate-validation.md`
- [X] T071 Run packaging, offline, native and Docker acceptance appropriate to the exact candidate and record results in `specs/081-engineering-workflow-templates/evidence/candidate-validation.md`
- [ ] T072 Perform independent code/evidence review, verify all FR/SC coverage and update final task/evidence status in `specs/081-engineering-workflow-templates/evidence/final-review.md`

---

## Dependencies and Execution Order

- Phase 1 precedes Phase 2; Phase 2 blocks every story.
- User Story 1 completes and receives the UI milestone review before runtime-facing User Story 2 integration.
- User Story 2 shared foundation T026–T036 precedes all three flagship chains. Fixture authoring tasks T037, T042 and T047 may run in parallel; integration tasks remain sequential around shared runtime files.
- User Story 3 depends on the readiness/promotion foundation and follows User Story 2 so the first three stay the priority. The seven qualification tasks are sequential in the stated evidence-led order even though their resource files are disjoint.
- User Story 4 depends on at least one verified User Story 2 run and may complete for the three flagships before all User Story 3 qualifications.
- Final validation runs after the desired story scope is complete. Any later authorized push follows `docs/contributing/dev-push-runbook.md` and `scripts/check-dev-push.ps1` outside this implementation task set.

## Parallel Opportunities

- T003/T004; T005/T006; T011–T014; T015–T017; T026–T029; T037/T042/T047; and T062/T063 modify disjoint files and can run concurrently after dependencies.
- Research/fixture preparation for one flagship can overlap test execution for another, but no two tasks edit `workflow_source_execution.py`, `workspace.py`, `workspace-service.ts`, `WorkflowRecoveryConcept.tsx`, migrations, or shared catalog state concurrently.
- External qualification may use separate disposable hosts; results are integrated sequentially and never share mutable workspaces, credentials or devices.

## Implementation Strategy

1. Deliver User Story 1 as the UI-first MVP with all ten honest templates.
2. Add the reusable approval/assertion/continuation foundation.
3. Complete the three flagships in internal risk-reducing order: sheet metal, 3D printing, Raspberry Pi CFD, while retaining equal flagship presentation.
4. Promote the seven follow-ons one at a time; do not hold truthful reference templates hostage to unqualified hosts.
5. Add local capture after verified runs exist.
6. Stop at each constitution/manual gate and before any exact external action lacking authorization.

## Format Validation

All 72 tasks use the required checkbox, sequential ID, optional parallel marker, user-story label where required, an actionable description and an exact file/directory path.
