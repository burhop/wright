# Tasks: Rivet Run Inspector

**Input**: Design documents from `specs/075-rivet-run-inspector/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/](contracts/), [quickstart.md](quickstart.md)

**Tests**: Required by the approved specification and Wright constitution. Write each listed test first and confirm it fails for the intended reason before implementing its paired behavior.

**Organization**: Tasks are grouped by user story so each increment can be implemented and verified independently. Preserve all unrelated working-tree changes.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it changes different files and has no dependency on an incomplete task in the same phase
- **[Story]**: Maps the task to User Story 1, 2, 3, or 4 from [spec.md](spec.md)
- Every task names its target file or directory

## Phase 1: Setup and Test Fixtures

**Purpose**: Establish deterministic local fixtures without touching live MCP servers, OAuth, CAD hosts, or provider/model configuration.

- [x] T001 Create reusable persisted run, event, output, and child-call fixture builders in `packages/workspace_service/tests/fixtures/rivet_run_inspection.py`
- [x] T002 [P] Create typed running, succeeded, failed, cancelled, empty, large, redacted, and historical inspection fixtures in `apps/web/src/components/workflows/rivet-run-inspector.fixtures.ts`
- [x] T003 [P] Create shared mocked workspace/run route helpers in `tests/ui-integration/workspace-surfaces/fixtures/rivet-run-inspector.ts`

---

## Phase 2: Foundational Run Evidence and Inspection Projection

**Purpose**: Build the secure, durable, typed foundation required by every user story.

**Critical**: No user-story UI implementation begins until this phase passes its focused tests.

- [x] T004 Add failing tests for typed result normalization, recursive redaction, safe links/artifacts, nulls, oversized previews, digests, and backward compatibility in `packages/workspace_service/tests/test_rivet_run_evidence.py`
- [x] T005 Implement bounded final/intermediate result projection without converting oversized successful runs into failures in `packages/workspace_service/src/workspace_service/rivet_evidence.py`
- [x] T006 [P] Add failing tests for running timestamps, existing trace columns, terminal immutability, event cursors, and scoped query ordering in `packages/data_vault/tests/test_data_vault_workflow_runs.py`
- [x] T007 [P] Extend the optional child-call evidence model with a backward-compatible safe result projection and completeness fields in `packages/core/src/core/rivet_mcp.py`
- [x] T008 Implement complete run-record projection, running timestamps, trace persistence, latest-sequence lookup, and scoped repository queries in `packages/data_vault/src/data_vault/workflow_runs.py`
- [x] T009 Add failing persistence tests for old and new child-call JSON records with bounded result summaries in `packages/data_vault/tests/test_rivet_run_manifest.py`
- [x] T010 Verify the existing JSON evidence repository persists and returns the optional safe child result fields without a parallel table in `packages/data_vault/tests/test_rivet_run_manifest.py`
- [x] T011 Add failing gateway tests proving only the already-sanitized result is retained and secrets/raw transport values never reach evidence in `packages/workspace_service/tests/test_rivet_gateway_bridge.py`
- [x] T012 Retain the bounded sanitized child result, redaction count, artifacts, timing, and reason at the gateway boundary in `packages/workspace_service/src/workspace_service/rivet_gateway_bridge.py`
- [x] T013 Add failing reducer tests for authoritative state, event cursors, step correlation, final/intermediate outputs, completeness, old records, and deterministic ordering in `packages/workspace_service/tests/test_workflow_inspection.py`
- [x] T014 Implement typed run summary, progress, execution-step, result, diagnostic, and completeness projections in `packages/workspace_service/src/workspace_service/workflow_inspection.py`
- [x] T015 Add failing service tests for workspace/session scoping and inspection assembly in `packages/workspace_service/tests/test_workflow_operations.py`
- [x] T016 Expose scoped run inspection and recent-run domain methods while preserving existing start/cancel/history/evidence behavior in `packages/workspace_service/src/workspace_service/workflow_operations.py`

**Checkpoint**: Safe persisted run/output/step evidence can be reconstructed after process or browser refresh without frontend inference.

---

## Phase 3: User Story 1 — Understand the Workflow Result (Priority: P1) — MVP

**Goal**: A user runs the saved workflow and sees live state, elapsed time, progress, and complete retained named outputs in a collapsible bottom inspector.

**Independent Test**: Run a fixture workflow with text and structured outputs, observe live progress, inspect every retained named output, then collapse the inspector and verify the canvas regains its area.

### Tests for User Story 1

- [x] T017 [P] [US1] Add failing API contract tests for the inspection snapshot, incremental events, output completeness, `no-store`, scope isolation, and validation errors in `apps/api/tests/test_workflow_run_inspection_api.py`
- [x] T018 [P] [US1] Add failing client tests for typed inspection polling and retained existing run/cancel/history/evidence methods in `apps/web/src/services/workspace-service.spec.ts`
- [x] T019 [P] [US1] Add failing component tests for collapsed, running, succeeded, empty-output, null, text, structured, list, link, artifact, large, and redacted result states in `apps/web/src/components/workflows/RivetRunInspector.spec.tsx`

### Implementation for User Story 1

- [x] T020 [US1] Define Pydantic run summary, progress, step, result, diagnostic, completeness, and inspection response schemas in `apps/api/src/api/schemas/workspace.py`
- [x] T021 [US1] Add the thin scoped `GET /workflows/runs/{run_id}/inspection` route and `Cache-Control: no-store` response behavior in `apps/api/src/api/routers/workspace.py`
- [x] T022 [US1] Add typed inspection models and `getRivetRunInspection` event-cursor client method in `apps/web/src/services/workspace-service.ts`
- [x] T023 [P] [US1] Create the token-driven, non-color-only run state primitive with stable test IDs in `apps/web/src/components/common/RunStateBadge.tsx`
- [x] T024 [P] [US1] Implement bounded typed result rendering, expand, copy, JSON export, safe link, and authorized artifact actions in `apps/web/src/components/workflows/RivetRunResult.tsx`
- [x] T025 [US1] Compose the accessible collapsible bottom summary, Outputs, and Steps regions using design tokens in `apps/web/src/components/workflows/RivetRunInspector.tsx` and `apps/web/src/components/workflows/rivet-run-inspector.css`
- [x] T026 [US1] Implement active polling, elapsed-time updates, event cursors, terminal stop, and transient-error backoff in `apps/web/src/hooks/useRivetRunInspection.ts`
- [x] T027 [US1] Replace the 220-character result banner with the bottom inspector while preserving immediate Run, separate Run Options, Cancel, Lint, and save-before-run behavior in `apps/web/src/components/surfaces/DirectRivetSurface.tsx`
- [x] T028 [US1] Update direct-surface component tests for immediate Run, options dialog, output selection, collapse/expand, and retained toolbar controls in `apps/web/src/components/surfaces/DirectRivetSurface.spec.tsx`
- [x] T029 [US1] Add a mocked running-to-success page journey with complete outputs and collapse behavior in `tests/ui-integration/workspace-surfaces/rivet-run-inspector.spec.ts`
- [x] T030 [US1] Add a local FastAPI/fixture-run smoke proving start-to-inspection state and output parsing in `tests/e2e/test_rivet_run_inspector.py`

**Checkpoint**: The MVP makes a successful workflow's status and complete retained results understandable without Logs.

---

## Phase 4: User Story 2 — Diagnose and Recover from a Failed Step (Priority: P2)

**Goal**: A failed run identifies the node/tool, explains the reason and safe next action, preserves upstream results, and offers full rerun without unsafe partial retry.

**Independent Test**: Run a fixture with one successful MCP step followed by an invalid MCP argument and verify automatic failure focus, upstream result retention, plain guidance, technical evidence, residue truth, and safe rerun controls.

### Tests for User Story 2

- [x] T031 [P] [US2] Add diagnostic-map and call-lifetime tests for runner, gateway, binding, approval, timeout, user cancellation, generation replacement, transport cancellation, restart, and residue reason codes; prove routine lifecycle polling preserves a healthy remote MCP runner in `packages/workspace_service/tests/test_workflow_inspection.py`, `packages/workspace_service/tests/test_rivet_gateway_bridge.py`, and `packages/tool_registry/tests/test_lifecycle_coordinator.py`
- [x] T032 [P] [US2] Add failing component tests for failure auto-open, upstream success, technical details, cancellation, residue warning, and absence of partial retry in `apps/web/src/components/workflows/RivetRunInspector.spec.tsx`

### Implementation for User Story 2

- [x] T033 [US2] Preserve healthy remote MCP calls across routine observation in `packages/tool_registry/src/tool_registry/lifecycle.py`, retain precise user/generation/transport cancellation provenance in `packages/workspace_service/src/workspace_service/rivet_gateway_bridge.py`, and implement deterministic plain-language recovery projections with failed-step/tool/trace correlation in `packages/workspace_service/src/workspace_service/workflow_inspection.py`
- [x] T034 [US2] Project cancellation acknowledgement, residue state, technical identifiers, and full-rerun eligibility through inspection schemas/routes in `apps/api/src/api/schemas/workspace.py` and `apps/api/src/api/routers/workspace.py`
- [x] T035 [US2] Add Diagnosis and Technical details views, upstream step results, residue warning, and full-rerun action in `apps/web/src/components/workflows/RivetRunInspector.tsx`
- [x] T036 [US2] Wire failure auto-open, cancelled-state behavior, generation-safe cancel, and full rerun of the current saved revision in `apps/web/src/components/surfaces/DirectRivetSurface.tsx`
- [x] T037 [US2] Reuse the shared inspection/diagnostic presentation in the existing workflow run panel without retaining duplicate error wording in `apps/web/src/components/chat/RivetWorkflowRun.tsx`
- [x] T038 [US2] Add mocked failed-child, cancelled, residue-possible, technical-details, and safe-rerun journeys in `tests/ui-integration/workspace-surfaces/rivet-run-inspector.spec.ts`

**Checkpoint**: Failed and cancelled runs can be diagnosed and safely retried without opening Logs or approving an unsafe partial replay.

---

## Phase 5: User Story 3 — Inspect Execution Flow on the Canvas (Priority: P2)

**Goal**: Inspector steps correlate to accessible node execution states, and selecting a step focuses the matching node without changing workflow bytes.

**Independent Test**: Display a multi-node run, select running/succeeded/failed steps, verify the corresponding nodes are focused and labeled, then select a historical missing node and verify an explicit explanation.

### Tests for User Story 3

- [x] T039 [P] [US3] Add protocol contract coverage for exact-origin version 3 messages, state bounds, malformed input guards, run-state replacement, focus, clear, and missing-node responses in `integrations/rivet/editor/tests/test_rivet2_editor_artifact.py`, `apps/web/src/components/surfaces/DirectRivetSurface.spec.tsx`, and `tests/ui-integration/workspace-surfaces/rivet-run-inspector.spec.ts`
- [x] T040 [P] [US3] Add failing direct-surface bridge tests for protocol fallback, bounded state synchronization, focus requests, missing historical nodes, and a visible focus-current-workflow action while the passive status announcement remains non-interactive in `apps/web/src/components/surfaces/DirectRivetSurface.spec.tsx`

### Implementation for User Story 3

- [x] T041 [US3] Add validated `set-run-state` and `clear-run-state` protocol version 3 handling in `integrations/rivet/editor/wrapper/WrightEditorBridge.tsx`
- [x] T042 [US3] Add a maintained Rivet host patch for presentation-only accessible node status and viewport focus in `integrations/rivet/editor/patches/rivet2-run-state-overlay.patch`
- [x] T043 [US3] Add ordered keyboard-selectable execution steps and focus/missing-node callbacks in `apps/web/src/components/workflows/RivetRunStepList.tsx` and `apps/web/src/components/workflows/RivetRunInspector.tsx`
- [x] T044 [US3] Synchronize selected run node states with the exact-origin iframe, clear overlays on workflow/run changes, and provide a visible keyboard-operable Focus workflow action that focuses the current canvas without turning the passive `aria-live` status into a control in `apps/web/src/components/surfaces/DirectRivetSurface.tsx`
- [x] T045 [US3] Register the new patch/wrapper test inputs, rebuild the pinned editor, and verify wrapper/patch/dist hashes in `integrations/rivet/editor/scripts/build-rivet2.mjs`, `integrations/rivet/editor/manifest.json`, and `integrations/rivet/editor/dist/`
- [x] T046 [US3] Add mocked accessible node-state, keyboard focus, explicit Focus workflow, focus-node, protocol fallback, passive-status, and missing-node journeys in `tests/ui-integration/workspace-surfaces/rivet-run-inspector.spec.ts`

**Checkpoint**: Users can move between execution evidence and the visual graph without DOM scraping or project mutation.

---

## Phase 6: User Story 4 — Resume Observation and Review Run History (Priority: P3)

**Goal**: Refresh reattaches to the same active run, and users can inspect bounded recent runs with immutable revision identity.

**Independent Test**: Start a delayed run, refresh during execution, verify the same run ID resumes without another start request, then inspect that run alongside a historical run from another revision.

### Tests for User Story 4

- [x] T047 [P] [US4] Add failing repository tests for workspace/session/workflow-scoped recent runs, active inclusion, null start times, deterministic ordering, and 20/50 limits in `packages/data_vault/tests/test_data_vault_workflow_runs.py`
- [x] T048 [P] [US4] Add failing API tests for the recent-run list, current revision, cross-scope denial, and old-record compatibility in `apps/api/tests/test_workflow_run_inspection_api.py`
- [x] T049 [P] [US4] Add failing hook tests for initial reattachment, no duplicate POST, event-cursor recovery, terminal stop, and historical selection in `apps/web/src/hooks/useRivetRunInspection.spec.tsx`

### Implementation for User Story 4

- [x] T050 [US4] Implement bounded scoped recent-run lookup and effective-start ordering in `packages/data_vault/src/data_vault/workflow_runs.py` and `packages/workspace_service/src/workspace_service/workflow_operations.py`
- [x] T051 [US4] Add typed `GET /workflows/{slug}/runs` response and thin route with current revision and `no-store` headers in `apps/api/src/api/schemas/workspace.py` and `apps/api/src/api/routers/workspace.py`
- [x] T052 [US4] Add recent-run client types/method and reattach/select behavior without run mutation in `apps/web/src/services/workspace-service.ts` and `apps/web/src/hooks/useRivetRunInspection.ts`
- [x] T053 [US4] Add the bounded History view with revision mismatch, evidence unavailable, and historical missing-node states in `apps/web/src/components/workflows/RivetRunInspector.tsx`
- [x] T054 [US4] Add mocked refresh-while-running, no-duplicate-start, recent-history, and revision-aware journeys in `tests/ui-integration/workspace-surfaces/rivet-run-inspector.spec.ts`
- [x] T055 [US4] Extend the local system smoke to recreate the UI client, reattach by run ID, and inspect a terminal historical run in `tests/e2e/test_rivet_run_inspector.py`

**Checkpoint**: Active and recent run truth survives browser refresh and remains tied to the exact workflow revision.

---

## Phase 7: Polish and Cross-Cutting Verification

**Purpose**: Close accessibility, documentation, performance, security, and regression gates across all stories.

- [x] T056 [P] Document Run Inspector outputs, completeness, refresh reattachment, diagnostics, and history in `docs/rivet-workflows.md`
- [x] T057 [P] Document child-result evidence, redaction, cancellation/residue guidance, and retained technical export behavior in `docs/rivet/mcp-gateway.md`
- [x] T058 Add keyboard, accessible-name, non-color status, narrow-layout, maximized-surface, and collapse-space assertions in `tests/ui-integration/workspace-surfaces/rivet-run-inspector.spec.ts`
- [x] T059 Add browser diagnostics assertions proving secrets and raw authority/OAuth values do not appear in DOM, clipboard stubs, downloads, console, or failed requests in `tests/ui-integration/workspace-surfaces/rivet-run-inspector.spec.ts`
- [x] T060 Run the focused backend, component, mocked Playwright, and local E2E commands from `specs/075-rivet-run-inspector/quickstart.md` and record any host limitation in that file
- [x] T061 Run the web build and lint, then repair only Run Inspector regressions in `apps/web/` and `tests/ui-integration/workspace-surfaces/rivet-run-inspector.spec.ts`
- [x] T062 Run `scripts/check-dev-merge.sh` before any merge to `dev`, or document the exact local host limitation and failing gate in `specs/075-rivet-run-inspector/quickstart.md`

---

## Dependencies and Execution Order

### Phase dependencies

- **Phase 1 — Setup**: Starts immediately.
- **Phase 2 — Foundation**: Depends on fixture availability and blocks all user stories.
- **Phase 3 — US1 MVP**: Depends on Phase 2 and delivers the first complete user-visible result experience.
- **Phase 4 — US2**: Depends on the inspector shell and projection from US1; its diagnostics remain independently testable with failed fixtures.
- **Phase 5 — US3**: Depends on the step model and inspector shell; editor-patch work is isolated from backend diagnostic work.
- **Phase 6 — US4**: Depends on the inspection client/hook but not on node highlighting; history remains independently testable.
- **Phase 7 — Polish**: Depends on all selected story phases.

### User story dependency graph

```text
Setup -> Foundation -> US1 (MVP)
                         |---> US2 (diagnosis/recovery)
                         |---> US3 (canvas correlation)
                         `---> US4 (refresh/history)
US2 + US3 + US4 -> Polish and full gates
```

### Within each story

1. Add the listed failing tests.
2. Implement domain models and projections before API routes.
3. Implement API/client contracts before composed UI behavior.
4. Add the mocked page journey after component behavior passes.
5. Run the independent checkpoint before advancing.

### Parallel opportunities

- T002 and T003 can proceed alongside T001.
- T006 and T007 can proceed while T004/T005 establish result semantics.
- API, client, and component failing tests T017-T019 can be authored in parallel after Phase 2.
- T023 and T024 can be implemented in parallel before composition in T025.
- US2 diagnostic-domain work and US3 bridge test authoring can proceed in parallel after US1.
- Repository/API/hook tests T047-T049 can be authored in parallel for US4.
- Documentation tasks T056-T057 can proceed in parallel after contracts stabilize.

## Parallel Example: User Story 1

```text
Task T017: API contract tests in apps/api/tests/test_workflow_run_inspection_api.py
Task T018: Frontend client tests in apps/web/src/services/workspace-service.spec.ts
Task T019: Inspector component tests in apps/web/src/components/workflows/RivetRunInspector.spec.tsx

After contracts pass:
Task T023: RunStateBadge primitive
Task T024: RivetRunResult component
```

## Parallel Example: User Story 4

```text
Task T047: Recent-run repository tests
Task T048: Recent-run API tests
Task T049: Refresh/reattachment hook tests
```

## Implementation Strategy

### MVP first

1. Complete Setup and Foundation.
2. Complete US1 through T030.
3. Stop and verify the successful-run experience independently.
4. Continue only after the bottom inspector reliably shows live state and complete retained outputs.

### Incremental delivery

1. **US1** replaces the unusable short banner with a functional result inspector.
2. **US2** makes failures diagnosable and recoverable.
3. **US3** links execution evidence to the visual graph.
4. **US4** makes observation durable across refresh and revisions.
5. Cross-cutting gates confirm accessibility, secrecy, performance, and packaging integrity.

### Fast feedback rules

- Use local fixtures and focused test files during implementation; do not wait on real Onshape, OAuth, Hermes, or CAD hosts.
- Do not rebuild the pinned Rivet artifact until the maintained source bridge and patch tests are ready.
- Preserve graph/run evidence on failures and report the exact failing layer: MCP lifecycle/transport cancellation, result projection, persistence, inspection reducer, API projection, React state, or editor bridge.
- Do not broaden this feature into workflow authoring, MCP installation, model selection, or provider configuration.

## Notes

- Every interactive control receives a stable `data-testid`.
- Styling flows through existing design tokens; new hardcoded color systems are prohibited.
- Full rerun is the only guaranteed recovery mode in schema version 1.
- Existing start, cancel, history, evidence, and export routes remain backward compatible.
- Optional SpecKit commit hooks remain skipped until the user explicitly requests a commit of the intentionally dirty working tree.
