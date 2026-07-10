# Tasks: Package Boundaries and Workspace Use Cases

**Input**: Design documents from `/specs/045-package-boundary-and-workspace-use-cases/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Required by the specification. Characterization and contract tests precede each ownership move.

## Phase 1: Setup

**Purpose**: Establish the feature policy and documentation surfaces.

- [x] T001 Create the authoritative package ownership and dependency manifest in architecture/python-packages.toml
- [x] T002 [P] Add the Feature 045 architecture decision and migration rules to docs/architecture/package-boundaries.md
- [x] T003 Update docs/gpt5-6-implementation-status.md with the Feature 045 baseline, scope, state, and exact next action

---

## Phase 2: Foundational

**Purpose**: Add enforcement and shared contracts required by every user story.

**⚠️ CRITICAL**: No ownership move begins until the fitness harness and typed application vocabulary exist.

- [x] T004 Replace tests/test_import_boundaries.py with manifest-driven static, local, relative, dynamic-import, graph-cycle, and package-metadata fitness checks
- [x] T005 [P] Add seeded positive and negative architecture fixtures in tests/architecture_fixtures/
- [x] T006 [P] Add domain identifiers, value objects, and stable error taxonomy in packages/core/src/core/identifiers.py and packages/core/src/core/errors.py
- [x] T007 [P] Add side-effect-neutral shared protocols in packages/core/src/core/ports.py and narrow packages/core/src/core/__init__.py exports
- [x] T008 Add workspace application errors, ports, commands, and results in packages/workspace_service/src/workspace_service/errors.py, ports.py, and models.py
- [x] T009 Add a bounded, cancellable async blocking-work executor in packages/workspace_service/src/workspace_service/executor.py with tests in packages/workspace_service/tests/test_executor.py

**Checkpoint**: The declared graph is executable and use cases can depend on stable contracts.

---

## Phase 3: User Story 1 - Dependable Workspace Operations (Priority: P1) 🎯 MVP

**Goal**: Preserve every workspace workflow while moving behavior behind owned application operations.

**Independent Test**: Run all workspace route contracts plus direct lifecycle/file/Git/context/tool operations against temporary workspaces and compare established responses and effects.

### Tests for User Story 1

- [x] T010 [P] [US1] Add workspace repository characterization tests in packages/data_vault/tests/test_workspace_repository.py
- [x] T011 [P] [US1] Add file, backup, and confinement adapter characterization tests in packages/workspace_service/tests/test_files.py
- [x] T012 [P] [US1] Add credential-safe Git and process adapter characterization tests in packages/workspace_service/tests/test_git.py
- [x] T013 [P] [US1] Expand route response/error compatibility tests in apps/api/tests/test_workspace_api.py

### Implementation for User Story 1

- [x] T014 [US1] Move workspace, session, context, settings, remote, and tool-selection SQL into packages/data_vault/src/data_vault/workspace_repository.py
- [x] T015 [US1] Move confined file, tree, preview, backup, and mutation behavior into packages/workspace_service/src/workspace_service/adapters/filesystem.py
- [x] T016 [US1] Move credential-safe Git behavior into packages/workspace_service/src/workspace_service/adapters/git.py and host execution into adapters/process.py
- [x] T017 [P] [US1] Implement lifecycle and session use cases in packages/workspace_service/src/workspace_service/use_cases/lifecycle.py
- [x] T018 [P] [US1] Implement file, backup, preview/download, and execution use cases in packages/workspace_service/src/workspace_service/use_cases/files.py
- [x] T019 [P] [US1] Implement Git status/diff/revert/commit/history/sync/branch/merge use cases in packages/workspace_service/src/workspace_service/use_cases/git.py
- [x] T020 [P] [US1] Implement context, settings, agent materialization, and tool-selection use cases in packages/workspace_service/src/workspace_service/use_cases/context.py and tools.py
- [x] T021 [US1] Refactor packages/workspace_service/src/workspace_service/service.py into a delegating facade and export the stable application surface from __init__.py
- [x] T022 [US1] Add explicit production wiring in packages/workspace_service/src/workspace_service/composition.py and apps/api/src/api/composition.py
- [x] T023 [US1] Refactor apps/api/src/api/routers/workspace.py to request/response translation only while preserving streaming response construction
- [x] T024 [US1] Route gateway refresh through apps/api/src/api/notifications.py and an injected workspace notification port without route-to-route imports

**Checkpoint**: Every supported workspace operation crosses one application boundary with compatible behavior.

---

## Phase 4: User Story 2 - Enforced Architectural Ownership (Priority: P1)

**Goal**: Make every package edge and forbidden runtime behavior mechanically enforceable.

**Independent Test**: Run the fitness suite against the repository and all seeded forbidden import forms; verify exact edge/file/line diagnostics and metadata parity.

- [x] T025 [US2] Move supported callers off packages/core/src/core/workspace.py and core/agent_sync.py using repository-wide static and dynamic call-graph evidence
- [x] T026 [US2] Relocate local secret-store implementations from core into packages/data_vault/src/data_vault/secret_provider.py while preserving core contracts and Feature 043 tests
- [x] T027 [US2] Remove SQLite/process/filesystem runtime ownership and reverse dynamic imports from packages/core/src/core/ and drive architecture manifest exceptions to zero
- [x] T028 [US2] Align all internal pyproject.toml dependency declarations and uv.lock with architecture/python-packages.toml
- [x] T029 [US2] Add package README ownership/extension guidance in packages/core/README.md, packages/data_vault/README.md, and packages/workspace_service/README.md

**Checkpoint**: The full graph passes with no temporary violations and `core` is side-effect-neutral.

---

## Phase 5: User Story 3 - Replaceable Infrastructure (Priority: P2)

**Goal**: Prove workflows without HTTP, persistent state, real Git, or concrete agents.

**Independent Test**: Construct all use cases with recording adapters and exercise success, failure, timeout, cancellation, and isolation.

- [x] T030 [P] [US3] Add reusable in-memory/recording ports in packages/workspace_service/tests/fakes.py
- [x] T031 [P] [US3] Add direct lifecycle/context/tool use-case tests in packages/workspace_service/tests/test_lifecycle_use_cases.py
- [x] T032 [P] [US3] Add direct file/Git/process use-case tests in packages/workspace_service/tests/test_workspace_use_cases.py
- [x] T033 [US3] Add 100-iteration concurrent workspace isolation and cancellation/leak tests in packages/workspace_service/tests/test_concurrency.py
- [x] T034 [US3] Add API composition tests proving explicit adapter injection and absence of global provider/workspace selection in apps/api/tests/test_workspace_composition.py

---

## Phase 6: User Story 4 - Safe Compatibility Migration (Priority: P2)

**Goal**: Demonstrate a data-format-neutral upgrade and constrained legacy compatibility.

**Independent Test**: Run current state/workspace fixtures through the new graph, verify no migration, and prove every retained shim delegates to one operation with a removal condition.

- [x] T035 [P] [US4] Add previous-release state/workspace compatibility and rollback tests in packages/workspace_service/tests/test_upgrade_compatibility.py
- [x] T036 [US4] Add only evidence-backed one-release delegators in packages/workspace_service/src/workspace_service/adapters/legacy.py and document each live caller/removal condition (no delegators were retained; all supported callers migrated)
- [x] T037 [US4] Remove unused global activation and duplicate business paths after call-graph verification and add non-reintroduction assertions to tests/test_import_boundaries.py

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Validate the complete feature and leave an exact review checkpoint.

- [x] T038 [P] Run and reconcile Ruff, focused mypy, architecture, data-vault, workspace-service, API workspace, and secret/confinement regression suites
- [x] T039 [P] Run package wheel/sdist build and import checks for every changed internal package and verify no new public dependency
- [x] T040 [P] Build strict MkDocs and run public-alpha leak/secret scans including untracked files
- [X] T041 Run the full Python, Hermes, frontend unit/build, and live browser sub-gates through scripts/check-dev-merge.sh with no skips
- [X] T042 Update docs/gpt5-6-implementation-status.md with files, exact commands/results, compatibility, rollback, risks, and the Feature 046 next action
- [X] T043 Complete a requirement-by-requirement audit of specs/045-package-boundary-and-workspace-use-cases/spec.md and mark all tasks only when evidence is present

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Starts immediately.
- **Foundational (Phase 2)**: Depends on T001 and blocks all user stories.
- **US1 (Phase 3)**: Depends on foundational contracts; establishes the working application graph.
- **US2 (Phase 4)**: Depends on US1 so legacy behavior can be removed rather than duplicated.
- **US3 (Phase 5)**: Can begin after ports/use cases exist; final proof depends on US1.
- **US4 (Phase 6)**: Depends on US1 and US2 call-graph evidence.
- **Polish (Phase 7)**: Depends on all stories.

### User Story Dependencies

- **US1 (P1)**: Foundational only; MVP ownership slice.
- **US2 (P1)**: US1, because forbidden legacy owners must first have a destination.
- **US3 (P2)**: Foundational plus relevant US1 use cases.
- **US4 (P2)**: US1 and US2.

### Parallel Opportunities

- T002 and T003 can run alongside T001.
- T005-T007 can run in parallel after the manifest shape is known.
- T010-T013 characterize separate ownership surfaces in parallel.
- T017-T020 implement separate use-case groups after adapters/contracts stabilize.
- T030-T032 cover independent operation groups in parallel.
- T038-T040 are independent final verification streams before the authoritative gate.

## Implementation Strategy

### MVP First (US1)

1. Establish enforceable policy and contracts.
2. Characterize current repository/file/Git/route behavior.
3. Extract adapters and use cases by vertical operation group.
4. Wire the facade and API through the single graph.
5. Verify exact public compatibility.

### Incremental Delivery

1. Use the boundary manifest with exact temporary violations during extraction.
2. Move behavior once; compatibility entry points delegate to that behavior.
3. Drive violations to zero, then prove use cases with recording adapters.
4. Demonstrate no-migration upgrade/rollback compatibility.
5. Run the full merge gate and stop at review.

## Notes

- Every task uses the required checkbox/ID/story/path format.
- Tests precede risky ownership moves as required by the implementation assignment.
- No task includes R2.3 lifecycle, R2.4 catalog consolidation, R2.5 observability, R2.6 frontend contracts, or release work.
