# Tasks: Canonical Process Definition and Read-Only Engineer View

**Input**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`

**Tests**: Required. Each user story must remain independently demonstrable, and invalid/compatibility behavior is blocking.

**Authority**: EPP-F02 T001 through T019 are authorized only for the exact reconciled subject bound by `APR-EPP-F02-MC-001` and `APR-EPP-F02-IMPL-001` and the active bounded implementation lease.

## Phase 1: Setup and Closed Contract

- [X] T001 Activate EPP-F02 atomically after exact approval: complete EPP-F01B only after green dev evidence; bind `specs/078-process-definition-view/tasks.md`; minimally admit only the exact active `specs/078-process-definition-view/` source in `specs/077-browser-program-status/contracts/program-status-bundle.schema.json`, `specs/077-browser-program-status/contracts/program-status-source-catalog.json`, `src/wright_engineering/static/program-status/program-status-bundle.schema.json`, `src/wright_engineering/static/program-status/program-status-source-catalog.json`, the three `use-case-registry.schema.json` parity copies, the publisher/validator, and focused positive/negative parity tests without adding a source class or relaxing unrelated paths; update program state/roadmap/work registry; create the governed EPP-F02 use-case row with `process_100_id: null`, no implementation/acceptance/verification/qualification evidence, and empty process-100 stage arrays; and publish a truthful planning/0-of-19 dashboard checkpoint with every benchmark funnel stage still `0/100` and readiness unchanged
- [X] T002 Add cross-language ASCII/NFC-Unicode/control/order golden and negative `wright-process-json-v1` vectors, schema, frozen-sample, global-ID, port-source, gate-order, feedback-reciprocity, and artifact-reciprocity tests; then install the exact committed bytes of `contracts/product-definition-v1.sample.json` (raw SHA-256 `6a02f71e35f9c3d9a3184509ddeab2df251cff454b6d6ce66d7244d015eefdef`) under public/package name `process-definitions/product-definition-v1.json` with byte-for-byte source/install equality in `packages/tool_registry/tests/test_process_definition.py` and `src/wright_engineering/static/process-definitions/`

---

## Phase 2: Foundational Validated Read Path

- [X] T003 Add bounded installed/fallback reader, ETag, strict-JSON, identity, and support-safe error tests in `packages/tool_registry/tests/test_process_definition.py`
- [X] T004 Implement and export the immutable validated reader in `packages/tool_registry/src/tool_registry/process_definition.py` and `packages/tool_registry/src/tool_registry/__init__.py`

**Checkpoint**: One exact definition can be validated and read offline; invalid definitions fail before presentation.

---

## Phase 3: User Story 1 — Understand a Versioned Process (P1)

**Independent Test**: Open the bundled process and identify all semantic elements in complete text and the matching diagram.

- [X] T005 [P] [US1] Add authenticated success, unauthorized-role 403/no-leak, ETag/304, exact-envelope, safe logical-source, and trace-header API tests in `apps/api/tests/test_process_definition_api.py`
- [X] T006 [US1] Implement schemas, declarative route, composition wiring, and router registration in `apps/api/src/api/schemas/process_definition.py`, `apps/api/src/api/routers/process_definition.py`, `apps/api/src/api/composition.py`, and `apps/api/src/api/main.py`
- [X] T007 [P] [US1] Add closed-client parsing, identity, and response-state tests in `apps/web/src/__tests__/ProcessDefinitionService.test.ts`
- [X] T008 [US1] Implement the read-only client contract in `apps/web/src/services/process-definition.ts`
- [X] T009 [P] [US1] Add text completeness, text/diagram ID equivalence, empty-category, keyboard, Axe, non-color, 200%-zoom, 320-pixel viewport, reduced-motion, and bounded response/render sampling in `apps/web/src/__tests__/ProcessDefinitionPage.test.tsx`; diagnostic performance evidence uses one warm-up plus 20 serial observations on an otherwise idle declared host, records every observation, and computes nearest-rank p95 without concurrent suites, while only deterministic correctness and functional timeouts gate delivery
- [X] T010 [US1] Implement semantic text, derived diagram, loading, and source-identity components in `apps/web/src/components/process-definition/` and `apps/web/src/components/pages/ProcessDefinitionPage.tsx`
- [X] T011 [US1] Add the default-off build-time `VITE_WRIGHT_PROCESS_DEFINITION_VIEW` removable feature boundary following the existing web feature-flag service pattern, stable route, navigation entry, and deletion fallback without altering existing routes in `apps/web/src/services/surfaces/feature-flags.ts`, `apps/web/src/App.tsx`, and `apps/web/src/components/layout/Sidebar.tsx`
- [X] T012 [US1] Add the mocked customer happy-path and explicit keyboard/Axe/200%-zoom/320-pixel/reduced-motion accessibility journey in `tests/ui-integration/process-definition.spec.ts`

**Checkpoint**: US1 is independently shippable and explains one exact process without execution.

---

## Phase 4: User Story 2 — Inspect Inputs, Outputs, and Constraints (P2)

**Independent Test**: Trace one input through action, gate, output, and expected artifact while observing exact source identity and zero mutation requests.

- [ ] T013 [P] [US2] Add UI trace, exact safe logical-source, zero-mutation request, and accessible visible-boundary notice tests proving the page says it is a definition only and provides no process-run or artifact-existence evidence in `apps/web/src/__tests__/ProcessDefinitionPage.test.tsx`
- [ ] T014 [US2] Complete inspectable relationship details, the fixed internal `process-definitions/product-definition-v1.json` source identity/detail behavior, and the concise accessible visible notice “Definition only — not evidence that a process ran or an artifact exists” in `apps/web/src/components/process-definition/ProcessDefinitionDetails.tsx` and `apps/web/src/components/pages/ProcessDefinitionPage.tsx`

**Checkpoint**: US2 is independently demonstrable and cannot be mistaken for a run or produced artifact.

---

## Phase 5: User Story 3 — Honest Failure and Compatibility (P3)

**Independent Test**: Missing, malformed, unsupported, identity-mismatched, and disabled fixtures give bounded recovery while existing journeys remain unchanged.

- [ ] T015 [US3] After T011, add the exact `contracts/recovery-fixtures.json` missing/invalid/unsupported cases plus closed API/UI failure, traversal/absolute/URL rejection, source non-mutation, disabled-boundary, and existing-route compatibility tests in `apps/api/tests/test_process_definition_api.py` and `apps/web/src/__tests__/ProcessDefinitionFailure.test.tsx`
- [ ] T016 [US3] Implement support-safe error mapping and disabled/unavailable browser states in `apps/api/src/api/routers/process_definition.py` and `apps/web/src/components/pages/ProcessDefinitionPage.tsx`

**Checkpoint**: US3 fails honestly and is removable without migrated state.

---

## Phase 6: Candidate Verification and Delivery Readiness

- [ ] T017 Maintain the recurring EPP-F02 dashboard checkpoint begun by T001: append exact commit/time/task/test evidence after US1 (T012), US2 (T014), and US3 (T016), then close the task at the candidate checkpoint; at every refresh regenerate/validate the dashboard and prove the EPP-F02 row has `process_100_id: null`, empty benchmark evidence, and every benchmark funnel stage remains `0/100` in the program registries and source catalog
- [ ] T018 [P] Add wheel contents, installed fallback, API/browser smoke, and selected workspace/Rivet non-interference coverage in `tests/packaging/test_wheel_contents.py`, `tests/native_runtime/test_process_definition_lifecycle.py`, and `tests/e2e/test_process_definition.py`
- [ ] T019 Run exact focused tests, Wright candidate gate, `quickstart.md` demonstration, accessibility checks, contamination diff (no holdout/oracle/`PROC-*` dispatch), and a path/diff audit proving no wholesale product-code promotion from read-only `076-engineering-workflow-prototype` evidence; run independent verification; append final accepted/tested evidence; then re-prove the EPP-F02 row still has `process_100_id: null`, empty qualification evidence, and every process-100 stage remains `0/100`; regenerate/validate/browser-check the dashboard, record host/tool/timestamp/manifest provenance plus commit/tree/results/rollback, and freeze the local candidate in `specs/078-process-definition-view/quickstart.md`

## Dependencies

- Exact human approval → T001 → T002 → T003 → T004.
- US1 starts after T004; within US1, T005→T006, T007→T008, T009→T010→T011→T012.
- US2 starts after T010 and may proceed while T011–T012 finish: T013→T014.
- US3 starts after T006, T010, and T011: T015→T016.
- T017 becomes eligible immediately after T001, records ordered interim checkpoints after T012, T014, and T016, and closes only after those three observations; T018 requires US1–US3 and may run beside the final T017 refresh; T019 requires both.

## Parallel Opportunities

- T005, T007, and T009 are separate API/service/component test files.
- After T010, T012 and T013 can proceed in separate files with one writer integrating.
- T017 dashboard evidence and T018 packaging/native/E2E files may be prepared in parallel, but suites must not be duplicated concurrently across hosts.

## Implementation Strategy

1. Deliver the validated source boundary first.
2. Complete US1 as the customer-visible MVP.
3. Add US2 inspectability and US3 honest recovery without expanding the model.
4. Run one candidate verification cycle and normally one feature-branch push; consolidate any CI-only correction.

**Total tasks**: 19. **MVP**: T001–T012 (US1). **The exact approval authorizes local T001–T019 only. No task authorizes implementation before exact human approval, feature-branch push, PR, merge/dev integration, benchmark execution, dependencies, publication, release, or direct `dev` changes.**
