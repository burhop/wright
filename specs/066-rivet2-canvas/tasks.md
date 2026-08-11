# Tasks: Modern Rivet Canvas Editor

**Input**: Design documents from `/specs/066-rivet2-canvas/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`

**Tests**: Automated contract, component, host, artifact, offline, and lifecycle verification is required by the specification.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because the task touches different files and has no incomplete dependency
- **[Story]**: Maps the task to a user story in `spec.md`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish the exact upstream source, wrapper, patch, and build layout without changing runtime behavior.

- [x] T001 Create the Rivet 2 source, wrapper, patch, and build-script layout under `integrations/rivet/editor/`
- [x] T002 [P] Record the exact Rivet 2 repository, revision, package version, license, and artifact schema in `integrations/rivet/editor/manifest.json`
- [x] T003 [P] Add source-acquisition and deterministic artifact-build entry points in `integrations/rivet/editor/scripts/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Define and verify the native bridge and canvas visibility seams shared by every story.

**Critical**: No user-story implementation begins until these contracts exist.

- [x] T004 Add failing source-policy tests for the exact revision, bounded patch, local assets, reproducible output, and absence of Rivet 1.25 fallback in `integrations/rivet/editor/tests/`
- [x] T005 [P] Add failing bridge contract tests for ready, set-project, get-project, acknowledgement, errors, source/origin validation, and workspace replacement in `integrations/rivet/editor/tests/`
- [x] T006 [P] Add failing canvas-policy tests for the allowed graph-authoring surface and every disallowed Rivet application surface in `integrations/rivet/editor/tests/`
- [x] T007 Implement the typed Wright/Rivet 2 bridge wrapper and message schema in `integrations/rivet/editor/wrapper/`
- [x] T008 Implement and track the bounded upstream `canvasOnly` host patch in `integrations/rivet/editor/patches/`
- [x] T009 Implement the pinned source acquisition, patch application, build, and manifest verification workflow in `integrations/rivet/editor/scripts/`

**Checkpoint**: The replacement editor has a tested source boundary, visibility policy, and workspace bridge.

---

## Phase 3: User Story 1 - Edit on a Focused Graph Canvas (Priority: P1) MVP

**Goal**: Display the modern Rivet 2 graph canvas and graph-authoring overlays without Rivet application chrome.

**Independent Test**: Open a fixture workflow and add, select, move, connect, configure, duplicate, and remove nodes while all disallowed surfaces remain absent.

### Tests for User Story 1

- [x] T010 [P] [US1] Add component assertions for canvas readiness and absence of Rivet-owned chrome in `apps/web/src/components/surfaces/DirectRivetSurface.spec.tsx`
- [x] T011 [P] [US1] Add artifact-level policy coverage in `integrations/rivet/editor/tests/` and the constitution-required mocked canvas interaction/disallowed-surface journey in `tests/ui-integration/workspace-surfaces/rivet2-canvas.spec.ts`

### Implementation for User Story 1

- [x] T012 [US1] Build the exact pinned Rivet 2 app with the Wright wrapper and canvas-only patch into `integrations/rivet/editor/dist/`
- [x] T013 [US1] Replace the legacy browser-state and DOM-hiding shim with a static verified Rivet 2 canvas host in `integrations/rivet/editor/host.py`
- [x] T014 [US1] Update host lifecycle tests for the native canvas artifact and removal of injected file-picker, storage, CSS, and MutationObserver behavior in `packages/workspace_service/tests/test_rivet_editor_host.py`

**Checkpoint**: The retained surface renders only a functional modern graph-authoring canvas.

---

## Phase 4: User Story 2 - Keep Wright as the Workflow Authority (Priority: P2)

**Goal**: Preserve Wright-owned selection, revisions, save conflicts, lint, run, and workspace isolation around the new canvas.

**Independent Test**: Create, open, edit, save, close, reopen, lint, run, and switch workflows using Wright controls and verify exact project/revision continuity.

### Tests for User Story 2

- [x] T015 [P] [US2] Add component tests for ready/error states, correlated bridge requests, replacement, timeout, and origin filtering in `apps/web/src/components/surfaces/DirectRivetSurface.spec.tsx`
- [x] T016 [P] [US2] Add URL construction tests for passing the exact Wright parent origin to the editor in `apps/web/src/services/rivet-editor.spec.ts`

### Implementation for User Story 2

- [x] T017 [US2] Update `apps/web/src/components/surfaces/DirectRivetSurface.tsx` to wait for bridge readiness, correlate acknowledgements and errors, replace documents safely, and retain Wright toolbar authority
- [x] T018 [US2] Update `apps/web/src/services/rivet-editor.ts` to construct the isolated canvas URL with an exact parent-origin trust parameter
- [x] T019 [US2] Verify workspace save-conflict, lint, run, retained hide/reopen/stop, and cross-workspace behavior in focused API and native runtime tests

**Checkpoint**: Wright remains the sole durable workflow authority while the canvas holds only isolated editing state.

---

## Phase 5: User Story 3 - Use the Modern Editor Reliably Offline (Priority: P3)

**Goal**: Ship and verify the replacement artifact locally with no runtime download, public asset, or retired fallback.

**Independent Test**: Deny network access, launch every supported host path, edit and save, then corrupt the artifact and observe a bounded unavailable error with no legacy launch.

### Tests for User Story 3

- [x] T020 [P] [US3] Add offline/public-origin scanning and exact artifact-integrity tests in `integrations/rivet/editor/tests/`
- [x] T021 [P] [US3] Add missing/corrupt artifact and bounded-unavailability coverage in `packages/workspace_service/tests/test_rivet_editor_host.py` and `tests/native_runtime/test_server.py`

### Implementation for User Story 3

- [x] T022 [US3] Finalize `integrations/rivet/editor/manifest.json` with exact source, patch, entrypoint, file inventory, and deterministic artifact checksum data
- [x] T023 [US3] Remove every executable Rivet 1.25 artifact/reference and update the Rivet spike baseline metadata under `integrations/rivet/spike/baseline/`
- [x] T024 [US3] Enforce artifact identity and integrity before editor launch in the workspace/runtime host path

**Checkpoint**: The modern editor works offline and fails closed if its verified artifact is unavailable.

---

## Phase 6: Polish & Cross-Cutting Verification

**Purpose**: Validate the complete replacement against the approved specification and packaging constraints.

- [x] T025 [P] Update `specs/066-rivet2-canvas/quickstart.md` with the final reproducible build and focused verification commands
- [x] T026 Run the focused web, bridge, artifact, workspace-host, API, and native-runtime tests from `specs/066-rivet2-canvas/quickstart.md`
- [x] T027 Run static scans proving no public editor asset and no executable Rivet 1.25 fallback remains in shipped paths
- [x] T028 Run the applicable `dev` merge gate or record any specific local host limitation without merging the branch

---

## Phase 7: User Story 4 - Packaged Template Loading (Priority: P1)

**Goal**: Create fresh workspace workflows from reviewed Rivet 2 templates while removing duplicate document chrome from the focused toolbar.

**Independent Test**: Instantiate every packaged template, instantiate one twice, and create one through the canvas chooser; verify valid projects, unique identities, the new filename tab, and the streamlined toolbar.

- [x] T029 [P] [US4] Add reviewed Rivet 2 project resources, catalog metadata, and MIT provenance under `packages/workspace_service/src/workspace_service/workflow_catalog/`
- [x] T030 [P] [US4] Add catalog validation, version-4 loading, and fresh project/graph/node/connection identity tests in `packages/workspace_service/tests/test_workflow_templates.py`
- [x] T031 [US4] Add thin workflow-template list and workspace-scoped instantiate APIs in `apps/api/src/api/routers/workspace.py`
- [x] T032 [US4] Add template service methods and a book-icon chooser to `apps/web/src/components/surfaces/DirectRivetSurface.tsx`
- [x] T033 [US4] Remove the duplicate filename, workflow selector, open-workflow action, and visible routine status text from the focused toolbar
- [x] T034 [US4] Add API and component coverage for catalog creation, template selection, tab handoff, and simplified chrome
- [x] T035 [US4] Verify the live template chooser and fresh project on the retained Rivet 2 canvas

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Starts immediately.
- **Foundational (Phase 2)**: Depends on Phase 1 and blocks all user stories.
- **User Story 1 (Phase 3)**: Depends on the foundational wrapper, patch, and build workflow.
- **User Story 2 (Phase 4)**: Depends on the working Story 1 artifact and bridge but remains independently testable through Wright's workflow journey.
- **User Story 3 (Phase 5)**: Depends on the final artifact and host path from Stories 1 and 2.
- **Polish (Phase 6)**: Depends on all selected stories.

### Within Each User Story

- Write the listed tests and confirm the relevant assertions fail before implementation.
- Implement the smallest source or host change that satisfies the contract.
- Re-run story-focused tests before moving to the next phase.
- Mark a task complete only after its change or verification succeeds.

### Parallel Opportunities

- T002 and T003 can proceed after T001 in separate files.
- T005 and T006 are independent test suites after T004 establishes fixtures.
- T010 and T011 can proceed independently.
- T015 and T016 can proceed independently.
- T020 and T021 can proceed independently.
- T025 can proceed while the final focused suites are being assembled.

## Implementation Strategy

1. Establish the exact upstream revision, typed bridge, and bounded patch.
2. Build and independently validate the focused canvas MVP.
3. Connect the canvas to Wright's revision-aware workflow controls.
4. Lock down offline packaging, integrity checks, and failure behavior.
5. Run focused suites, scans, and the merge gate without merging.

## Notes

- The upstream checkout is build-time input only and remains under ignored `.work/`; runtime packages ship only the verified `dist/` artifact.
- Existing unrelated working-tree changes are outside this feature and must not be staged, overwritten, or committed.
- The optional Spec Kit auto-commit hook is intentionally skipped in a mixed dirty worktree because it stages the entire repository.
