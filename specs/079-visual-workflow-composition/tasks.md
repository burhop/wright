# Tasks: Visual Workflow Composition Foundation

**Input**: [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/](contracts/), [quickstart.md](quickstart.md)

**Gate**: Do not start implementation until EPP-F02 deployment is verified from merged `dev`, the proposed EPP-F02B roadmap order is explicitly approved, and this exact spec/plan/tasks subject receives planning plus implementation approval.

**Authority**: EPP-F02B T001 through T038 and Checkpoints C through E are authorized only for exact subject `871192c2` bound by `APR-EPP-F02B-MC-001`, `APR-EPP-F02B-IMPL-001`, and the active bounded implementation lease; merge and release remain unauthorized.

**Implementation roots**: `packages/core/src/core`, `packages/core/tests`, `packages/data_vault/src/data_vault`, `packages/data_vault/tests`, `packages/workspace_service/src/workspace_service`, `apps/api/src/api`, `apps/api/tests`, `apps/web/src`, `tests/ui-integration/workflow-composer.spec.ts`, `tests/e2e/test_workflow_composer.py`, `tests/native_runtime/test_process_definition_lifecycle.py`, `tests/packaging/test_wheel_contents.py`, `tests/test_docker_smoke_contract.py`, `docs/programs/engineering-process-platform`, `specs/079-visual-workflow-composition`, and `artifacts/ui-walkthrough/workflow-composer`.

## Phase 1: Setup and Program Boundary

- [X] T001 Record the approved proposed EPP-F02B roadmap entry and inactive spec 079 work registration, admit the exact tasks path in both program-status schema copies, and preserve the active EPP-F02 source in docs/programs/engineering-process-platform/{roadmap.json,work-registry.json}, specs/077-browser-program-status/contracts/program-status-bundle.schema.json, src/wright_engineering/static/program-status/program-status-bundle.schema.json, and tests/program_control_plane/test_contract_schemas.py
- [X] T002 [P] Add contract-validation fixtures for the representative workflow and strict rejection cases in packages/core/tests/fixtures/workflow_drafts/ and packages/core/tests/test_workflow_drafts.py
- [X] T003 [P] Add default-off server and browser authoring flags without changing EPP-F02 flags in apps/api/src/api/config.py and apps/web/src/config/workflow-composer.ts

---

## Phase 2: Foundational Model, Validation, and Boundaries

**Purpose**: Complete the canonical draft, store, service, API transport, and browser decode seams required by every story.

- [X] T004 Implement closed immutable draft entities and canonical semantic/layout digests in packages/core/src/core/workflow_drafts.py
- [ ] T005 Implement stable diagnostics and complete graph/layout validation in packages/core/src/core/workflow_draft_validation.py
- [ ] T006 [P] Implement the feature-owned SQLite sidecar with append-only revisions and atomic compare-and-set head updates in packages/data_vault/src/data_vault/workflow_draft_repository.py
- [ ] T007 Implement create/read/validate/save orchestration with last-valid preservation in packages/workspace_service/src/workspace_service/workflow_draft_service.py
- [ ] T008 [P] Implement closed Pydantic transport and support-safe error models in apps/api/src/api/schemas/workflow_drafts.py
- [ ] T009 Implement authenticated default-off create/read/validate/save routes in apps/api/src/api/routers/workflow_drafts.py and compose them in apps/api/src/api/{composition.py,main.py}
- [ ] T010 [P] Implement strict bounded browser decoding, identity verification, and API calls in apps/web/src/services/workflow-drafts.ts
- [ ] T011 [P] Implement renderer-neutral projection, intent, semantic-ID parity, and fake-renderer contracts in apps/web/src/components/workflow-composer/{draft-model.ts,draft-projection.ts,draft-intents.ts,renderer-types.ts}

**Checkpoint**: Pure contract, validation, persistence, API, and renderer seams pass focused tests; no composer UI or released-definition mutation exists.

---

## Phase 3: User Story 1 — Compose and Reopen a Four-Block Workflow (P1)

**Goal**: Create, connect, validate, save, close, reopen, and inspect the representative four-block workflow with exact text/diagram identity parity.

**Independent Test**: Perform Quickstart Journeys 1 and 3; all concepts, relationships, identities, revision/digests, and four positions survive reopen.

### Tests

- [ ] T012 [P] [US1] Add canonical round-trip, graph, layout, store atomicity, stale revision, and reopen tests in packages/core/tests/test_workflow_drafts.py and packages/data_vault/tests/test_workflow_draft_repository.py
- [ ] T013 [P] [US1] Add authenticated create/read/validate/save, ETag, closed-error, feature-disabled, and zero-release-authority API tests in apps/api/tests/test_workflow_drafts_api.py
- [ ] T014 [P] [US1] Add projection/text semantic-ID parity and fake-renderer replacement component tests in apps/web/src/components/workflow-composer/WorkflowComposer.spec.tsx

### Implementation

- [ ] T015 [US1] Implement empty-draft creation, bounded block palette, diagram/text controls, and working-draft authority shell in apps/web/src/components/pages/WorkflowComposerPage.tsx and apps/web/src/components/workflow-composer/WorkflowComposer.tsx
- [ ] T016 [US1] Implement the first-party phase-lane SVG/HTML canvas for blocks, typed ports, connections, gate, feedback, artifacts, zoom, and fit in apps/web/src/components/workflow-composer/FirstPartyDraftCanvas.tsx
- [ ] T017 [US1] Implement text projection and Definition/Ports & relationships/Validation inspector from the same model in apps/web/src/components/workflow-composer/{DraftTextProjection.tsx,DraftInspector.tsx}
- [ ] T018 [US1] Implement save, close, reopen, revision/digest display, and stale-save recovery in apps/web/src/components/workflow-composer/WorkflowComposer.tsx
- [ ] T019 [US1] Add route/navigation exposure under the separate web flag and preserve Process Definition behavior in apps/web/src/{App.tsx,components/layout/Sidebar.tsx}
- [ ] T020 [US1] Publish Checkpoint C rendered-canvas evidence and the first Checkpoint E save/reopen evidence, then refresh docs/programs/engineering-process-platform/dashboard.json and artifacts/ui-walkthrough/workflow-composer/

---

## Phase 4: User Story 2 — Edit Safely with Understandable Validation (P2)

**Goal**: Make routine edits directly while rejecting incompatible, duplicate, dangling, and identity-conflict candidates with specific recovery.

**Independent Test**: Perform Quickstart Journey 2 and then save the corrected draft; invalid intent changes neither last-valid state nor prior saved revision.

### Tests

- [ ] T021 [P] [US2] Add intent-reducer all-or-none tests for create/select/move/edit/connect/delete and invalid recovery in apps/web/src/components/workflow-composer/draft-intents.spec.ts
- [ ] T022 [P] [US2] Add incompatible, duplicate, dangling, gate/feedback, artifact-producer, and identity-conflict fixtures with expected stable diagnostics in packages/core/tests/test_workflow_draft_validation.py
- [ ] T023 [P] [US2] Add mocked Playwright edit/diagnostic/correction/save coverage in tests/ui-integration/workflow-composer.spec.ts

### Implementation

- [ ] T024 [US2] Implement immutable intent reduction and last-valid working-copy containment in apps/web/src/components/workflow-composer/draft-intents.ts
- [ ] T025 [US2] Implement select, move, create/edit/delete, port connection, gate, feedback, and artifact authoring controls in apps/web/src/components/workflow-composer/{FirstPartyDraftCanvas.tsx,DraftInspector.tsx}
- [ ] T026 [US2] Map local and server diagnostics to affected identities, non-color canvas cues, explanation, and bounded correction in apps/web/src/components/workflow-composer/DraftDiagnostics.tsx
- [ ] T027 [US2] Publish Checkpoint D invalid-edit/recovery walkthrough and refresh docs/programs/engineering-process-platform/dashboard.json and artifacts/ui-walkthrough/workflow-composer/

---

## Phase 5: User Story 3 — Draft Authority, Accessibility, and Removal (P3)

**Goal**: Make draft/released authority unmistakable, keep primary actions keyboard accessible and inspection narrow-safe, and prove clean disable/removal.

**Independent Test**: Perform Quickstart Journeys 4 and 5; keyboard and fallback work, serious/critical accessibility findings are zero, and EPP-F02 bytes/ETag/journey remain unchanged.

### Tests

- [ ] T028 [P] [US3] Add keyboard, focus, renderer fallback, 390px, 200% zoom, reduced-motion, and serious/critical Axe checks in tests/ui-integration/workflow-composer.spec.ts
- [ ] T029 [P] [US3] Add native/API lifecycle, feature-disabled, sidecar rollback, no-Rivet/no-MCP/no-model, and released-definition byte/ETag non-interference tests in tests/e2e/test_workflow_composer.py and tests/native_runtime/test_process_definition_lifecycle.py
- [ ] T030 [P] [US3] Add package/wheel and Docker enabled/disabled asset contract tests in tests/packaging/test_wheel_contents.py and tests/test_docker_smoke_contract.py

### Implementation

- [ ] T031 [US3] Complete keyboard command routing, visible focus, non-color cues, narrow inspector, and renderer-failure text fallback in apps/web/src/components/workflow-composer/ and apps/web/src/components/pages/WorkflowComposerPage.tsx
- [ ] T032 [US3] Complete server/browser flag rejection, inert-sidecar rollback, and safe incompatibility handling in apps/api/src/api/routers/workflow_drafts.py and packages/data_vault/src/data_vault/workflow_draft_repository.py
- [ ] T033 [US3] Publish final Checkpoint E evidence and refresh docs/programs/engineering-process-platform/dashboard.json and artifacts/ui-walkthrough/workflow-composer/

---

## Phase 6: Candidate Verification and PR Readiness

- [ ] T034 [P] Reconcile every item in specs/079-visual-workflow-composition/checklists/{requirements.md,ux.md} and record any justified deviation in specs/079-visual-workflow-composition/prototype-parity.md
- [ ] T035 Run focused and consolidated Windows tests, builds, accessibility, deployed walkthrough validation, exact diff review, and dev push gate with evidence in specs/079-visual-workflow-composition/evidence/windows-candidate.md
- [ ] T036 Verify the exact committed candidate on GB10 in an isolated clean worktree, including Linux/aarch64 domain/API/store tests, frontend build/test, Docker smoke, packaging, and independent review in specs/079-visual-workflow-composition/evidence/gb10-candidate.md
- [ ] T037 Run two independent reviews of the frozen exact candidate and remediate only proven in-scope findings in specs/079-visual-workflow-composition/evidence/independent-reviews.md
- [ ] T038 Read docs/contributing/dev-push-runbook.md, run scripts/check-dev-push.ps1, push the feature branch, classify terminal CI, and prepare the dev-targeting PR summary in specs/079-visual-workflow-composition/evidence/pr-readiness.md

## Dependencies and Execution Order

- Phase 1 requires the external program and human approvals named in the gate.
- Phase 2 blocks every user story.
- US1 is the MVP and blocks US2 because safe edits require a visible draft and last-valid state.
- US2 and most US3 tests can proceed in parallel after US1's model/host seam; final US3 non-interference runs after all composer behavior stabilizes.
- Candidate verification begins only after Checkpoints C, D, and E pass and the branch is clean.

## Parallel Examples

- After T001/T003, backend domain tests (T012), API tests (T013), and renderer contract tests (T014) can run on separate files.
- During US2, core diagnostic fixtures (T022) and browser intent tests (T021) can run concurrently before integration (T023).
- During US3, accessibility (T028), lifecycle/non-interference (T029), and packaging (T030) are independent.
- At candidate freeze, Windows (T035) finishes first; GB10 verification (T036) then runs against the exact commit while independent read-only review (T037) proceeds.

## MVP

US1 through T020 is the smallest independently demonstrable slice: four blocks render from one canonical model, save/reopen works, text/diagram IDs match, and the dashboard/walkthrough make progress visible. It does not include full edit recovery until US2.

## Format Validation

All 38 tasks use checkbox, sequential ID, permitted parallel marker, required user-story label within story phases, actionable description, and explicit file path.
