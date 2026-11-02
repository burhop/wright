# Tasks: Workflow Trace and Product Review

**Input**: Design documents from `specs/083-workflow-trace-review/`
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`

**Tests**: Required by the specification, constitution, and approved goal. Tests precede the implementation they verify where practical.

## Phase 1: Setup and Integration Inventory

**Purpose**: Freeze shared ownership and the real acceptance inputs before changing runtime contracts.

- [x] T001 Record validation/report ownership and shared-file boundaries in `specs/083-workflow-trace-review/implementation-log.md`
- [x] T002 Inventory retained feature-081 campaign records and create the truthful 24-case availability manifest in `specs/083-workflow-trace-review/evidence/corpus-manifest.json`
- [x] T003 [P] Record real STEP/STL/3MF in-app and offline viewer capability probes in `specs/083-workflow-trace-review/evidence/viewer-capabilities.md`
- [x] T004 [P] Map current run JSON, canonical execution repository, run-history API, result types, viewer registry, and workspace entry ownership in `specs/083-workflow-trace-review/implementation-log.md`
- [x] T005 Verify `.gitignore`, `.dockerignore`, and applicable lint/format ignore configuration cover generated trace reports, archives, Python, TypeScript, and browser evidence without changing unrelated repository policy

---

## Phase 2: Foundational Trace Contracts and Storage

**Purpose**: Provide stable report identities, occurrence/version preservation, evidence references, and source adapters used by every story.

**Critical**: No user-story implementation begins until this phase passes.

- [x] T006 Add contract tests for strict trace records, stable anchors, occurrence identities, availability states, and external evidence subjects in `packages/core/tests/test_workflow_trace.py`
- [x] T007 Implement versioned trace domain models and validation in `packages/core/src/core/workflow_trace.py`
- [x] T008 Add repository tests for idempotent ingest, distinct attempt artifacts, transactional references, restart recovery, pagination, and immutable report revisions in `packages/data_vault/tests/test_workflow_trace_repository.py`
- [x] T009 Implement SQLite WAL trace schema and repository in `packages/data_vault/src/data_vault/workflow_trace_repository.py`
- [x] T010 Add source-adapter tests for completed, failed, blocked, cancelled, interrupted, revised, repeated-path, and legacy-gap run JSON in `packages/workspace_service/tests/test_workflow_trace_sources.py`
- [x] T011 Implement authoritative run-record adapters and bounded legacy projection in `packages/workspace_service/src/workspace_service/workflow_trace/sources.py`
- [x] T012 Add capture tests for definition/input snapshots, prompts, occurrence events, immutable artifact versions, idempotency, and capture failure isolation in `packages/workspace_service/tests/test_workflow_trace_capture.py`
- [x] T013 Implement incremental trace capture and artifact-version storage in `packages/workspace_service/src/workspace_service/workflow_trace/capture.py`
- [x] T014 Wire additive capture through `workflow_runner.py` and canonical snapshots through `workflow_run_record.py` without changing validator ownership or replaying operations
- [x] T015 Add projection tests for bounded summaries, exact-subject evidence, and unavailable historical details in `packages/workspace_service/tests/test_workflow_trace_projection.py`
- [x] T016 Implement trace projection service in `packages/workspace_service/src/workspace_service/workflow_trace/projection.py`
- [x] T017 Export the trace services through `packages/workspace_service/src/workspace_service/workflow_trace/__init__.py` and application composition in `packages/workspace_service/src/workspace_service/service.py`
- [x] T018 Run focused core/data-vault/workspace-service trace tests and record Phase 2 results in `specs/083-workflow-trace-review/implementation-log.md`

**Checkpoint**: Durable facts can be captured and projected independently of the browser and workflow outcome.

---

## Phase 3: User Story 1 - See the Results (Priority: P1)

**Goal**: Open a saved run and immediately see actual deliverables, previews, purpose, and outcome.

**Independent Test**: Open a completed CAD-and-document run through workspace run history and open a primary result without expanding process detail.

- [x] T019 [P] [US1] Add trace/export API contract, authorization, stable-link, and canonical saved-run tests in `apps/api/tests/test_workflow_trace_export_api.py`
- [x] T020 [P] [US1] Add results-first component tests for completed runs, CAD fallback, evidence disclosure, and initial density in `apps/web/src/components/workflow-trace/WorkflowTracePage.spec.tsx`
- [x] T021 [US1] Add typed trace transport schemas in `apps/api/src/api/schemas/workflow_trace.py`
- [x] T022 [US1] Add thin authorized trace summary/detail routes to `apps/api/src/api/routers/workspace.py`
- [x] T023 [US1] Add trace DTOs and lazy client methods to `apps/web/src/services/workspace-service.ts`
- [x] T024 [US1] Implement results-first page, result hierarchy, actual preview routing, viewer/open-file actions, and explicit unsupported-format fallback in `apps/web/src/components/workflow-trace/WorkflowTracePage.tsx`
- [x] T025 [US1] Implement responsive trace presentation with existing design tokens in `apps/web/src/components/workflow-trace/workflow-trace.css`
- [x] T026 [US1] Add the saved-run Trace entry and stable run link through the established Workflows surface in `apps/web/src/prototypes/workflow-recovery/WorkflowRunHistory.tsx`
- [x] T027 [US1] Verify real workspace entry, primary output access, viewer behavior, and editor regression coverage; record evidence in `specs/083-workflow-trace-review/evidence/ui-results.md`

**Checkpoint**: User Story 1 is independently usable and keeps technical detail closed by default.

---

## Phase 4: User Story 2 - Explain an Output or Decision (Priority: P1)

**Goal**: Follow recorded requirements, approvals, assumptions, decisions, inputs, prompts, and external validation to exact subjects.

**Independent Test**: Navigate from an output to its decision, source requirement/input revision, approval, validation producer, and supporting report without running checks.

- [x] T028 [P] [US2] Add evidence-ingest and exact-subject API tests, including superseded records and unsupported producer schemas, in `apps/api/tests/test_workflow_trace_evidence_api.py`
- [x] T029 [P] [US2] Add progressive evidence/prompt inspector and subject-navigation tests in `apps/web/src/components/workflow-trace/WorkflowTracePage.spec.tsx`
- [x] T030 [US2] Implement strict external-evidence ingestion and subject resolution in `packages/workspace_service/src/workspace_service/workflow_trace/evidence.py`
- [x] T031 [US2] Document the implemented producer-neutral evidence contract in `specs/083-workflow-trace-review/contracts/evidence-integration.md`
- [x] T032 [US2] Add authorized evidence routes and pagination to `apps/api/src/api/routers/workspace.py`
- [x] T033 [US2] Implement the contextual evidence, prompt, input, and decision inspector in `apps/web/src/components/workflow-trace/TraceInspector.tsx`
- [x] T034 [US2] Implement stable bidirectional artifact-subject navigation and focus restoration in `apps/web/src/components/workflow-trace/WorkflowTracePage.tsx`
- [x] T035 [US2] Verify Trace never invokes validators or synthesizes acceptance and record evidence in `specs/083-workflow-trace-review/evidence/evidence-ownership.md`

**Checkpoint**: Recorded justification is inspectable and attributable without a Trace-generated engineering verdict.

---

## Phase 5: User Story 3 - Follow the Process and Iterations (Priority: P1)

**Goal**: Inspect the executed workflow graph, blocks, connections, groups, occurrences, traversals, and superseded artifact versions.

**Independent Test**: Select a repeatedly traversed path and open every occurrence's exact outputs while the graph retains one recognizable path.

- [x] T036 [P] [US3] Add graph projection tests for executed definitions, saved/fallback layout, connections, and repeated attempts in `packages/workspace_service/tests/test_workflow_trace_graph.py`
- [x] T037 [P] [US3] Add graph block/connection selection, occurrence-list, and browser interaction coverage in the Trace component and Playwright suites
- [x] T038 [US3] Implement read-only executed graph projection in the established Rivet validation projection and canonical Trace adapter
- [x] T039 [US3] Reuse authorized Rivet inspection and add lazy canonical saved-run Trace endpoints in `apps/api/src/api/routers/workspace.py`
- [x] T040 [US3] Implement the read-only React Flow graph with selectable semantic elements in `apps/web/src/components/workflow-trace/TraceGraph.tsx`
- [x] T041 [US3] Implement accessible process list, ordered attempt display, and exact artifact links in `apps/web/src/components/workflow-trace/TraceProcessDetails.tsx`
- [x] T042 [US3] Verify later definition edits and repeated filename writes cannot replace historical graph/artifact evidence; record results in `specs/083-workflow-trace-review/evidence/iteration-integrity.md`

**Checkpoint**: The process and every recorded iteration are inspectable without duplicating the graph.

---

## Phase 6: User Story 4 - Review Failed or Blocked Runs (Priority: P1)

**Goal**: Preserve and present partial results, errors, blockers, and last durable state for unsuccessful executions.

**Independent Test**: Open failed, blocked, cancelled, and interrupted fixtures and inspect every retained partial output without rerunning a workflow.

- [x] T043 [P] [US4] Add backend regressions for terminal/nonterminal status fidelity, partial results, missing end time, and attempts in Trace source/canonical tests
- [x] T044 [P] [US4] Add failed/stopped run page tests with visible error/blocker and no false success label in the Trace component suite
- [x] T045 [US4] Preserve last-durable status and partial artifact projection in `packages/workspace_service/src/workspace_service/workflow_trace/sources.py`
- [x] T046 [US4] Add compact error/blocker presentation and attempt history to `apps/web/src/components/workflow-trace/WorkflowTracePage.tsx`
- [x] T047 [US4] Verify failure browsing performs no implicit mutation/tool/retry calls and record results in `specs/083-workflow-trace-review/evidence/failure-review.md`

**Checkpoint**: Every supported unsuccessful state remains useful and truthfully labeled.

---

## Phase 7: User Story 5 - Send a Portable Review Package (Priority: P2)

**Goal**: Export report-only or full-data ZIP packages that work offline after extraction and relocation.

**Independent Test**: Move an extracted package, disable networking, open `index.html` under `file://`, and follow report, artifact, iteration, and evidence links.

- [x] T048 [P] [US5] Add exporter tests for report/full modes, repeated filenames, missing/external resources, deterministic membership, and integrity mismatch in `packages/workspace_service/tests/test_workflow_trace_export.py`
- [x] T049 [P] [US5] Add export API authorization and direct-download tests for Rivet and canonical records in `apps/api/tests/test_workflow_trace_export_api.py`
- [x] T050 [P] [US5] Add export-control component tests in `apps/web/src/components/workflow-trace/WorkflowTracePage.spec.tsx`
- [x] T051 [US5] Implement safe static HTML rendering, relative link mapping, manifests, and truthful viewer fallbacks in `packages/workspace_service/src/workspace_service/workflow_trace/export.py`
- [x] T052 [US5] Add thin report/full-data download routes to `apps/api/src/api/routers/workspace.py`
- [x] T053 [US5] Implement report-only/full-data export controls in `apps/web/src/components/workflow-trace/TraceExportMenu.tsx`
- [x] T054 [US5] Add offline file-origin Playwright coverage and generated-link validation in `tests/ui-integration/workflow-trace-export.spec.ts`
- [x] T055 [US5] Extract, relocate, and verify both export modes with networking disabled; record manifest/link/viewer evidence in `specs/083-workflow-trace-review/evidence/offline-export.md`

**Checkpoint**: A third party can review available evidence without Wright or a network connection.

---

## Phase 8: Corpus Acceptance and Cross-Cutting Verification

**Purpose**: Prove the feature across actual retained processes and preserve existing workflow authoring.

- [x] T056 Reconcile all 24 corpus entries against host availability and update `specs/083-workflow-trace-review/evidence/corpus-manifest.json` without counting unavailable or synthetic cases as passed
- [x] T057 [P] Add performance fixture and verify initial result projection for 100 graph elements and 1,000 evidence references in `packages/workspace_service/tests/test_workflow_trace_performance.py`
- [x] T058 [P] Add API and served-browser smoke coverage in the Trace API tests and `tests/ui-integration/workflow-trace-review.spec.ts`
- [x] T059 Run focused and applicable Python/TypeScript/package-boundary checks and record exact commands/results in `specs/083-workflow-trace-review/implementation-log.md`
- [x] T060 Run the required served-workspace authoring regression walkthrough, desktop/mobile/200% layouts, graph interaction, and offline export walkthrough; save evidence under `specs/083-workflow-trace-review/evidence/`
- [x] T061 Review the final diff against FR-001 through FR-024 and SC-001 through SC-008, fix material findings, and record the completion audit in `specs/083-workflow-trace-review/completion-audit.md`
- [x] T062 Start the local API/frontend without replacing occupied services and record the review URL/build identity in `specs/083-workflow-trace-review/implementation-log.md`
- [x] T063 Prepare a normal managed Wright workspace from the transferred campaign without modifying source evidence, then verify all 24 exact run identities through the live API
- [x] T064 Run the unmocked production UI against the managed campaign workspace, verify retained raster imagery and a nonblank STL viewer, and relocate/open both freshly downloaded ZIP modes offline with networking blocked
- [x] T065 Replace the standalone technical-data presentation with one source-backed engineering review: results, clickable swimlanes, readable measurements/settings/documents, and named authorization for printed-part case01
- [x] T066 Regenerate both case01 ZIP modes through the real API; verify relocated offline links, included artifact digests, desktop/mobile layouts, and engineering detail interactions
- [x] T067 Obtain user acceptance of the case01 standalone UI before expanding engineering-specific presentation across the remaining campaign families
- [ ] T068 Implement and verify FR-035 activity-attempt timing capture in runtime producers, including Wright AutoTest authorization, retries, terminal failures/cancellation, and interrupted-process recovery. Test persistence without an attached report and round-trip the timing through standalone export; never backfill missing historical durations with estimates.

---

## Phase 9: Campaign-Wide Standalone Reports

**Goal**: Publish truthful standalone engineering reviews for all 30 retained campaign examples without rerunning engineering work.

**Independent Test**: Generate all full-data packages, move the output directory, block networking, open the catalog and every report under `file://`, and verify archive/resource digests and activity detail interactions.

- [x] T069 Inventory all 30 campaign cases with pinned case/run/attempt/dataset/template identities, retained artifact counts, and known evidence gaps in `specs/083-workflow-trace-review/evidence/campaign-report-inventory.json`
- [x] T070 [P] Add focused inventory, batch export, catalog, integrity, and incomplete-run tests in `packages/workspace_service/tests/test_workflow_trace_campaign_batch.py`
- [x] T071 Implement reusable campaign inventory, filesystem resource loading, atomic ZIP publication, extracted reports, and offline catalog generation in `packages/workspace_service/src/workspace_service/workflow_trace/campaign_batch.py`
- [x] T072 Implement one all/selected and report/full CLI in `scripts/export-workflow-trace-campaign.py` plus byte-integrity verification in `scripts/verify-workflow-trace-campaign.py`
- [x] T073 Generalize the shared review model for all 10 workflow families, meaningful recorded previews, principal deliverables, incomplete outcomes, and evidence-backed tool labels in `packages/workspace_service/src/workspace_service/workflow_trace/review_model.py`
- [x] T074 Generate and inspect a real full-data report for one example in each workflow family, including both incomplete families
- [x] T075 Generate 30 full-data ZIPs and extracted reports plus the portable catalog under ignored local report storage
- [x] T076 Verify all 30 manifests, archive members, extracted bytes, and resource SHA-256 values with zero failures
- [x] T077 Open all 30 reports with networking blocked, exercise activity detail, and save desktop/mobile screenshots for all 10 families with zero browser errors or remote requests
- [x] T078 Update the specification, plan, quickstart, implementation log, and campaign evidence without claiming FR-035 timing-producer completion
- [x] T079 Add family-aware principal STL selection and a bundled offline Three.js STL viewer without promoting CFD domains or surrogate geometry
- [x] T080 Present retained visual inputs and expanded-row evidence thumbnails, and replace raw CAD observation byte tables with engineering verification summaries
- [x] T081 Derive clearly labeled recorded-order connectors and engineering responsibility lanes for campaign records whose authored graph connections were not retained
- [x] T082 Regenerate and integrity-check all 30 full-data packages, then verify every extracted report under `file://` with networking blocked and run direct WebGL pixel checks for both enclosure concepts
- [x] T083 Add a provenance-preserving review-visualization artifact type and package path for data-derived engineering imagery
- [x] T084 Promote the retained Raspberry Pi Variant A/B air-speed and temperature slices into the output gallery and attach compact thumbnails to the recorded CFD results activity
- [x] T085 Add preparation, export, and offline browser regressions for visualization source identities, derivation labels, retained resolution, lane placement, and network isolation
- [x] T086 Regenerate all 30 full-data packages, preserve the 30-report catalog, and visually inspect desktop/mobile output plus the expanded CFD results lane

---

## Dependencies and Execution Order

- Phase 1 establishes shared ownership, actual corpus availability, and viewer facts.
- Phase 2 blocks every user story because exact identity and durable capture are shared invariants.
- US1 provides the results surface used by US2-US5.
- US2 evidence navigation and US3 process navigation can proceed in parallel after US1 and Phase 2, except where they share `WorkflowTracePage.tsx`.
- US4 depends on the source adapter and US1 page but is independent of export.
- US5 depends on the pinned projection and stable artifact/evidence links from US1-US3.
- Corpus and served-workspace acceptance follows all user stories.

## Parallel Examples

- In Phase 1, T003 and T004 can run in parallel after T001 establishes ownership.
- In Phase 2, domain/storage tests and source-adapter fixtures can be prepared in parallel before their implementations.
- For US1, API tests and component tests are independent until route/page integration.
- For US2-US4, backend contract tests and frontend component tests are parallel, while edits to shared API/page files stay sequential.
- For US5, exporter, API, and component tests can be written in parallel before exporter and route integration.

## Implementation Strategy

The first vertical slice is one accessible completed run plus one failed run through durable projection, API, results page, and artifact opening. Next add external evidence, then graph iterations, then offline export. Each slice remains truthful about missing legacy data. Campaign publication extends that same renderer to all 30 retained examples, including six incomplete attempts. Runtime timing capture remains the separate T068 producer requirement.

## Notes

- Mark tasks `[X]` only after their stated implementation or evidence exists.
- Engineering validation remains external; this feature stores and presents producer records.
- Do not activate the deferred feature-081 content-validation plan or rerun campaign workflows.
- Optional Spec Kit commit hooks are intentionally deferred until the implementation is reviewable; push, merge, and release remain outside this feature goal.
