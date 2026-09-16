# Tasks: Process Output Validator

**Status:** Implementation active under the submitted goal. T001–T009 complete; M1 process integration next. This replaces the previous 74-task campaign plan.
**Authority:** [spec.md](spec.md), [plan.md](plan.md), [scope amendment](scope-amendment.md).
**Implementation starts only when the revised goal/plan is approved.**

Paths below are repository-relative. Proposed files may be adjusted to established ownership at T001, with the plan updated. Do not interpret these paths as proof that commands or code already exist.

## Phase 1 — Setup (M0)

- [x] T001 Record exact canonical source/compiler/runner, result events, BaseTool/MCP registration, installed resource packaging and existing authoring integration points in `specs/082-output-content-validation/evidence/runtime-integration.md`; inspect only the relevant runtime, select isolated demonstration data roots, and avoid another branch/campaign audit.
- [x] T002 Inventory the 30 current scenario manifests and source requirements/capabilities into `packages/workspace_service/src/workspace_service/process_validation/profiles/coverage.json`; freeze the simple structured-output demonstration baseline separately; record source hashes and supported/planned status without modifying generation inputs or requiring all outputs.

## Phase 2 — Foundations (M0)

- [x] T003 Implement versioned request/subject/profile/measurement/finding/feedback/assessment contracts and pure state rules in `packages/core/src/core/process_validation.py`; publish generated JSON Schema under `specs/082-output-content-validation/contracts/schemas/` and test identity, finite values, units, status aggregation and incompatible versions in `packages/core/tests/test_process_validation.py`.
- [x] T004 Add additive SQLite WAL migrations and immutable attempt/assessment/review persistence in `packages/data_vault/src/data_vault/process_validation_repository.py`; prove idempotency conflicts, latest-attempt selection, historical retention and terminal retry/resume semantics in `packages/data_vault/tests/test_process_validation_repository.py`.
- [x] T005 Implement exact subject resolution, stable snapshots/readback and bounded reader registry in `packages/workspace_service/src/workspace_service/process_validation/subjects.py` and `readers/base.py`; retain source/reader identities, authorized roots, cancellation and original-file protection.
- [x] T006 Implement packaged and workspace-owned profile loading/validation in `packages/workspace_service/src/workspace_service/process_validation/profiles.py` and resources in `profiles/`; reject executable predicates, unresolved hard-check limits and unsupported required capabilities; pin baseline/profile digests.

**Checkpoint:** Contract/schema, storage and subject/profile foundations are coherent. No corpus-wide gate.

## Phase 3 — US1: Check a previous step (M1)

**Independent acceptance:** A non-MCP producer/check/consumer process releases only its current passing revision; direct and MCP invocation return equivalent assessments.

- [x] T007 [US1] Add meaningful pass/fail/missing/stale/error/mixed/empty-scope controls in `packages/workspace_service/tests/test_process_validation.py` using `tests/datasets/process-validation/structured/`; each defect must reach its intended check.
- [x] T008 [US1] Implement local inline-value, JSON/CSV and bounded text/file readers in `packages/workspace_service/src/workspace_service/process_validation/readers/structured.py`; support required fields/roles, types, ranges, units, table rows and explicit content selectors without inferring unsupported document semantics.
- [x] T009 [US1] Implement measurement/check evaluation and orchestration in `packages/workspace_service/src/workspace_service/process_validation/evaluation.py` and `service.py`; adapt existing registered predicates with explicit error mapping, scope/coverage, finite interval rules and immutable result finalization.
- [ ] T010 [US1] Add and document canonical local-validator configuration/ports and compile-time checks in `packages/workspace_service/src/workspace_service/workflow_source_execution.py` and `specs/082-output-content-validation/contracts/process-source.md`; update shared schema owners identified at T001, preserve legacy syntax and reject invalid/unsafe bindings.
- [ ] T011 [US1] Add thin BaseTool/MCP evaluation/read adapters in `packages/workspace_service/src/workspace_service/process_validation_tools.py` and a packaged `process_validation_cli.py`; register with the existing Wright MCP service, preserve authority and distinguish tool failure from a returned noncompliant result.
- [ ] T012 [US1] Add profile/subject binding and validator state to existing authoring controls in `apps/web/src/prototypes/workflow-recovery/`, including `recovery-dsl.ts`, `model.ts` and `command-system.ts` where appropriate; preserve Diagram/Source round-trip, Undo/Redo and save/reopen. Follow `docs/contributing/workflow-ui-integration.md`.
- [ ] T013 [US1] Execute validators in the canonical runner, persist/publish verification or diagnostic evidence before gate failure, and bind release to the checked revision in `workflow_source_execution.py`, `workflow_results.py` and `workflow_run_record.py`; verify service/MCP/canonical parity and existing design-check regressions in `packages/workspace_service/tests/test_workflow_process_validation.py`.

## Phase 4 — US2: Actionable feedback and bounded correction (M2)

**Independent acceptance:** A real configured AI receives measured findings for a structured output, writes a new revision, passes revalidation and releases the consumer. Exhaustion/no-progress/resume hold safely.

- [ ] T014 [US2] Implement typed correction packets and concise readable explanations in `packages/workspace_service/src/workspace_service/process_validation/feedback.py`; include ownership, constraints to preserve, source/evidence refs, acceptance targets, routing, 20-finding/16-KiB inline bounds and complete-result paging references.
- [ ] T015 [US2] Extend existing rework validation/scheduling in `workflow_design_check.py` and `workflow_source_execution.py` for one safe text/structured/indexed-file producer/check segment alongside existing create-new CAD; persist budgets, delivered feedback, invalidation and no-progress stops without permitting arbitrary back-edges or external actions.
- [ ] T016 [US2] Expose explicit revision target and 0–3 revision limit, default 0, through existing controls in `apps/web/src/prototypes/workflow-recovery/`; preserve canonical settings and show held/repairing/exhausted states using existing run diagnostics.
- [ ] T017 [US2] Prove correction target/identity binding, new-output lineage, mixed failure/unknown behavior, error routing, wrong-owner rejection, no progress, budget persistence, cancellation and stale approval protection in `packages/workspace_service/tests/test_workflow_process_validation_rework.py`; retain existing design-check mixed-verdict and approval-resume tests.
- [ ] T018 [US2] Save and run an isolated ordinary-AI structured-output → local-validator → bounded correction → consumer example under `tests/datasets/process-validation/processes/`; retain actual model/step/attempt/output/feedback evidence in `artifacts/process-validation/structured-loop/`. Mocked scheduling alone does not satisfy this task.

## Phase 5 — US3: Human-readable/report-consumable evidence (M3)

**Independent acceptance:** A schema-only consumer renders JSON/Markdown/RTM with matching verdicts and links, including failures, pending review and stale revisions.

- [ ] T019 [US3] Generate JSON, Markdown and RTM/CSV from one assessment in `packages/workspace_service/src/workspace_service/process_validation/reporting.py`; publish representative pass/fail/mixed/blocked/error/stale/repair records under `specs/082-output-content-validation/contracts/examples/` with assessment/profile/subject identity and scope.
- [ ] T020 [US3] Add authorized get/list-findings/export and authority-backed review operations in `process_validation/service.py` with thin existing-auth routes in `apps/api/src/api/routers/workspace.py`; update MCP/CLI adapters, persist late review as a new assessment and expose query-time currentness without mutating history.
- [ ] T021 [P] [US3] Write a report-branch integration handoff in `specs/082-output-content-validation/contracts/report-consumer.md` describing exact schema/versioning, read/export operations, stable artifact resolution, paging, currentness, Markdown and RTM fields. Do not edit the report branch or build its UI.
- [ ] T022 [US3] Add an independent schema/example consumer and report consistency/security tests in `packages/workspace_service/tests/test_process_validation_reporting.py` and `apps/api/tests/test_process_validation_routes.py`; cover pending authenticated review, stale/latest selection, access control, escaped text and CSV formula injection.

## Phase 6 — US4: Real reusable engineering capabilities (M4)

**Independent acceptance:** Actual jig geometry and heat field data use the same contracts; targeted valid-file defects trigger specific findings, and the CAD producer corrects one defect through the real process.

- [ ] T023 [US4] Freeze source-backed bounded profiles for `parametric-drill-jig-01` and `heat-spreader-sizing-01` under `packages/workspace_service/src/workspace_service/process_validation/profiles/`; include all requirements within each declared check scope, explicit exclusions, required roles/variants, methods, datum/units and tolerances before evaluating candidates.
- [ ] T024 [US4] Implement reusable geometry readback/checks in `packages/workspace_service/src/workspace_service/process_validation/readers/geometry.py` using qualified actual-file/native inspection; measure jig seat centers/diameters in the workpiece frame and retain semantic selectors, original hashes and exact reader/native identities.
- [ ] T025 [US4] Qualify geometry with independent good/alternative/defective/boundary controls in `tests/datasets/process-validation/geometry/` and `tests/external/process_validation/test_geometry.py`; include arc center versus point-on-curve, wrong datum, radial-versus-diametral clearance and missing geometry. Parsing failure is not defect-detector proof.
- [ ] T026 [US4] Implement heat field/table/balance/refinement readers and independent numerical checks in `packages/workspace_service/src/workspace_service/process_validation/readers/thermal.py`; require actual candidate/baseline/refined field lineage, analytical temperature-rise comparison, heat balance and source-derived selection limits.
- [ ] T027 [US4] Qualify numerical checks with analytical references and targeted wrong-load, missing-candidate, fabricated-summary, unit and threshold controls in `tests/datasets/process-validation/thermal/` and `tests/external/process_validation/test_thermal.py`; accurate infeasibility must remain distinct from invalid analysis.
- [ ] T028 [US4] Run isolated canonical jig AI/MCP producer → validator → actual correction → revalidation → consumer and a heat-output validation process; retain real measurements, feedback delivery, old/new output identities and final dispositions under `artifacts/process-validation/engineering/`. Reuse retained source output read-only where appropriate; do not repair the generation campaign.
- [ ] T029 [US4] Reconcile all 30 pack entries against implemented/planned capabilities in `process_validation/profiles/coverage.json` and `specs/082-output-content-validation/acceptance-cases.md`; publish extension recipes and honest unsupported states. Do not claim all 30 designs or all family readers are verified.

## Phase 7 — Closure (M5)

- [ ] T030 Verify confinement, malicious/unbounded input, permission boundaries, duplicate concurrent invocation, cancellation/resource cleanup, trace propagation and output stability in `packages/workspace_service/tests/test_process_validation_security.py` and `tests/security/`; verify native reader ownership using `docs/mcp-catalog/mcp-server-testing-process.md`.
- [ ] T031 Verify installed runtime resources/CLI/MCP without a source checkout, offline local evaluation and supported native/Docker boundaries; retain commands/results in `specs/082-output-content-validation/evidence/distribution.md` and update package metadata only as necessary. Do not add MCP-specific software to the base image.
- [ ] T032 Complete component tests alongside changed process controls, mocked integration in `tests/ui-integration/process-validation.spec.ts`, and served-system evidence in `tests/e2e/test_process_validation.py`; enter through normal Workflow/Workflows, preserve authoring and demonstrate actual run diagnostics/evidence links.
- [ ] T033 Document exact runnable examples, reader prerequisites, profile authoring, correction policy and report consumption in `docs/workflows/process-output-validation.md`; update `specs/082-output-content-validation/quickstart.md` with real commands after implementation and verify links/examples.
- [ ] T034 Run applicable focused regressions/package gates and finish `specs/082-output-content-validation/completion.md` and `progress.md` with completed task IDs, actual demonstration evidence, capability limits and report-branch handoff. Claim completion only when all required initial slices work; keep push/merge/release separately authorized.

## Dependencies and parallel opportunities

Setup → foundations → US1 → US2. US3 depends on stable US1 results and US2 feedback contracts; US4 depends on foundations and US2 for its correction demonstration. Closure depends on all four stories.

T021 can be drafted from the frozen reporting contract while T020 transport wiring progresses; finalize examples after T019. Within US4, thermal reader/controls can proceed independently of geometry reader/controls after T023, with separate native resources. US1/US2 share compiler/UI files and should be sequential. Parallelism describes independent work, not permission to spawn agents beyond current instructions.

## Requirement coverage

| Requirements | Tasks |
|---|---|
| FR-001, FR-008 | T007–T013 |
| FR-002, FR-010, FR-013 | T003–T005, T015, T017, T020, T030 |
| FR-003, FR-004 | T002, T006, T023, T029 |
| FR-005, FR-007 | T005, T007–T009, T024–T027 |
| FR-006, FR-009 | T014–T018 |
| FR-011 | T005, T015, T017, T030 |
| FR-012 | T019–T022 |
| FR-014 | T018, T023–T029 |
| FR-015, FR-016 | T003–T007, T017, T022, T025, T027, T030–T032 |
| FR-017 | T010, T012–T013, T016, T032 |

Success criteria SC-001/002 map to M1/M2/M4; SC-003/004 to M2/M3; SC-005 to M4; SC-006/007 to M2/M5.

## Delivery strategy

Complete one real local correction loop before expanding native capabilities. Publish the report contract early so the other branch can integrate independently. Then prove real CAD and numerical slices. Tests are required for the runtime product's correctness; no corpus campaign is substituted for a running process capability.
