# Tasks: Native Engineering Process Milestone

**Authority:** [standing scope](milestone-decision.md). **Plan:** [plan.md](plan.md). Task IDs remain stable; scope changes append a reason. Checked boxes mean the described work is complete; dashboard verification/integration are separate evidence states. Total: 32 tasks.

## Phase 1: Baseline and contracts

- [ ] T001 Reconcile merged F02/current authority, roadmap and worktree pointers with preserved historical evidence in `docs/programs/engineering-process-platform/` and `AGENTS.md`. (FR-001, FR-017, FR-020; AC01)
- [x] T002 Complete spec/plan/contracts, frozen valid/invalid examples, human protocol and independent consistency review in `specs/079-wright-native-authoring/`. (FR-001–020; AC01–10)

## Phase 2: US1 — Useful current dashboard

Independent acceptance: identify current outcome, stage counts, missing quality evidence and next action without reading historical governance details.

- [ ] T003 [US1] Extend typed milestone/task/evidence registry, publisher and strict packaged readers with derived counts and old-bundle compatibility in `scripts/program_status/`, `packages/tool_registry/` and source/package status schemas. (FR-017, FR-018; AC01)
- [ ] T004 [US1] Implement accessible milestone/quality/task/current-work presentation and remove hardcoded feature labels in `apps/web/src/components/program-status/`, `ProgramStatusPage.tsx` and its service/tests. (FR-017–019; AC01)
- [ ] T005 [US1] Publish an honest initial checkpoint and verify actual dashboard browser/freshness/recovery journey in `tests/ui-integration/program-status.spec.ts` and milestone evidence. (FR-017–020; AC01)

## Phase 3: Foundation — Semantics and examples

- [x] T006 Implement native typed definitions, strict parsing/canonical identity, structural validation and readiness with cross-language/negative tests in `packages/core/src/core/native_process.py` and `packages/core/tests/test_native_process.py`. (FR-001–003; AC02)
- [x] T007 Implement bounded canonical quantities and explicit dimensional operations/tests in the native core/runtime value contract. (FR-004; AC02, AC08)
- [x] T008 Create three versioned development definitions and negative fixtures under `src/wright_engineering/static/native-processes/` with independent expected outcomes. (FR-016; AC08)

## Phase 4: US2 — Author and preserve work

Independent acceptance: create/connect/configure/undo/save/reopen; reject invalid edits, interrupted save and stale writer without losing valid data.

- [x] T009 [US2] Add native tables/migration and previous-reader/backup recovery tests in `packages/data_vault/src/data_vault/migrations.py` and native repository tests. (FR-007, FR-020; AC03, AC09)
- [x] T010 [US2] Implement explicit transactional CAS/idempotency/document persistence and concurrent/failure tests in `native_process_repository.py`. (FR-007; AC03)
- [x] T011 [US2] Add authorized native document/check application service, shared language/operation discovery and thin API schemas/routes/tests in `workspace_service/native_process_service.py` and `apps/api/`; enforce the same validation/CAS for UI and programmatic clients. (FR-002, FR-007, FR-008; AC02, AC03)
- [ ] T012 [US2] Implement typed client and atomic commands/undo/invalid-buffer tests against the official language/schema/fixtures in `apps/web/src/services/native-process.ts` and `components/native-process/`; no separate renderer/AI semantics. (FR-002, FR-003, FR-006; AC03)
- [ ] T013 [US2] Review/pin the renderer and implement graph/precise port adapter, keyboard/click creation/connection and layout tests in native components. (FR-005, FR-019; AC03)
- [ ] T014 [US2] Implement contextual Inspector, sole input configuration, readable text/source and deletion impact review in native components. (FR-005, FR-006, FR-019; AC03)
- [ ] T015 [US2] Implement save/reopen/conflict/unsaved navigation UI and isolated route/navigation wiring in `NativeProcessPage.tsx` and supporting tests. (FR-006, FR-007; AC03)
- [ ] T016 [US2] Verify mocked and real editor/browser journeys including programmatic-definition/canvas round trips, layout-independent semantic identity, accessibility and checkpoint evidence. Label simulated AI-client payload tests accurately. (FR-002, FR-019; AC02, AC03)

## Phase 5: US3/US4 — Execute, inspect and recover

Independent acceptance: generate/check actual outputs, inspect provenance, fail/correct/rerun, cancel and refresh, compare headless semantics.

- [ ] T017 [US3] Implement immutable run snapshots, ordered events and terminal-state CAS in native repository/runtime with concurrency tests. (FR-009–011; AC04, AC06)
- [ ] T018 [US3] Implement bounded versioned deterministic operations and output-dependent assertions with negative controls in `native_process_runtime.py`. (FR-004, FR-009, FR-016; AC04, AC08)
- [ ] T019 [US3] Implement staged indexed workspace artifacts and scoped digest-checked retrieval/reconciliation tests in `native_process_artifacts.py` and application service. (FR-008, FR-012; AC05)
- [ ] T020 [US4] Implement deadline/cancel/restart/blocked-dependent/recovery-linked-run behavior and race tests in native runtime/service. (FR-013, FR-014; AC06)
- [ ] T021 [US3] Add native run/history/inspection/cancel/artifact API and headless entrypoint with semantic parity tests. (FR-010–014; AC04–06)
- [ ] T022 [US3] Implement real run inspection/output access and failure/correction/reconnect UI with component tests. (FR-011–014, FR-019; AC05, AC06)
- [ ] T023 [US4] Verify real end-to-end run/artifact/failure/cancel/recovery journeys in `tests/e2e/test_native_process.py` and native browser tests. (FR-010–014; AC04–06)

## Phase 6: US5 — Exact real tool and examples

- [ ] T024 [US5] Implement exact MCP binding/preflight/current-schema/policy revalidation in `native_process_mcp.py`, API/UI and denied/changed-binding tests. (FR-015; AC07)
- [ ] T025 [US5] Execute safe disposable real local MCP through the gateway, retain protocol/tool/artifact evidence and teardown proof. (FR-015; AC07)
- [ ] T026 [US5] Verify all three customer examples and independent positive/negative/recovery assertions; record example maturity without benchmark credit. (FR-016; AC08)

## Phase 7: Verification and integration

- [ ] T027 Perform independent exact-candidate architecture/security/quality review; resolve actionable findings and preserve original results. (FR-001–020; AC10)
- [ ] T028 Execute accessibility/manual usability protocol with real independent participants, record actual results and address acceptance failures. (FR-019; AC03, AC10)
- [ ] T029 Verify packaging, native/Docker/offline, migration/retention/recovery and legacy non-interference; document actual host limitations. (FR-020; AC09)
- [ ] T030 Run required push/merge gates on exact candidates, inspect all terminal CI jobs and consolidate any necessary corrections. (FR-020; AC10)
- [ ] T031 Integrate through dev PRs and verify exact built/deployed commit/image, health and changed browser journeys. (FR-020; AC10)
- [ ] T032 Publish verified final dashboard/task/evidence state, reconcile documentation and report delivered capabilities/limitations/next milestone. (FR-017, FR-018, FR-020; AC01, AC10)

## Dependencies

T001 baseline inspection and T002 contracts precede product implementation. T001's prospective transition/catalog record work may proceed alongside independent native foundation code, but must complete before initial dashboard publication. Dashboard T003→T004→T005 may run independently after contracts; core T006→T007/T008 precedes persistence T009→T010→T011 and client T012→T013/T014→T015→T016. Runtime T017→T018/T019→T020→T021→T022→T023; T024→T025 requires runtime and gateway boundary. T026 requires examples/runtime. T027/T028/T029 require the affected complete candidate. T030→T031→T032 require all applicable acceptance evidence. Recruit T028 participants during planning; do not delay independent work while scheduling.

## Parallel work and implementation strategy

Use separate worktrees for dashboard and native work; one writer owns each. Independent reviewers read immutable candidates. Avoid duplicate suites. Ship dashboard visibility first, then native author/save, then complete runtime/tool journey. Only increment verified/integrated counts when corresponding evidence passes.

September 4 clarification: the process language is official for AI/canvas/runtime, and native work replaces Rivet. Existing IDs remain unchanged (32 tasks); expanded conformance coverage is recorded in milestone-decision.md. Token/component-layer and structured log/trace obligations map to tasks in contracts/implementation-appendix.md. Dashboard completion must distinguish native delivery from subsequent Rivet migration/retirement.
