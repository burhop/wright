# Tasks: Port Nous Fixes

**Input**: Design documents from `/specs/036-port-nous-fixes/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Targeted tests are required for accepted backend/package/frontend change areas when practical.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm branch, review inputs, and exclusion boundaries.

- [X] T001 Confirm current branch and working tree state in repository root
- [X] T002 [P] Review candidate manifest in scratch/nous_hackathon_candidates/MANIFEST.md
- [X] T003 [P] Scan scratch/nous_hackathon_candidates/ for excluded prototype/payment/demo terms
- [X] T004 Document candidate classification in scratch/nous_hackathon_candidates/REVIEW_NOTES.md

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish extraction rules before live source edits.

- [X] T005 Confirm no whole-branch merge or cherry-pick from nous_hackathon has been applied
- [X] T006 [P] Verify excluded path list against git diff dev...nous_hackathon
- [X] T007 Mark mixed-risk candidates that require hunk-level review in scratch/nous_hackathon_candidates/REVIEW_NOTES.md

**Checkpoint**: Candidate set is classified and ready for selective porting.

---

## Phase 3: User Story 1 - Review Good Candidate Changes (Priority: P1) MVP

**Goal**: Maintainers can inspect a curated candidate set without production source changes.

**Independent Test**: Candidate files are present with original paths, excluded artifacts are absent, and mixed files are documented.

### Implementation for User Story 1

- [X] T008 [US1] Verify copied backend/package candidates under scratch/nous_hackathon_candidates/apps and scratch/nous_hackathon_candidates/packages
- [X] T009 [US1] Verify copied frontend candidates under scratch/nous_hackathon_candidates/apps/web
- [X] T010 [US1] Update scratch/nous_hackathon_candidates/MANIFEST.md with any classification findings from REVIEW_NOTES.md

**Checkpoint**: Review folder is ready for one-by-one extraction.

---

## Phase 4: User Story 2 - Port Verified Fixes Safely (Priority: P2)

**Goal**: Apply only reusable fixes and leave prototype expansions behind.

**Independent Test**: Each accepted live-code diff is scoped and traceable to reviewed candidates.

### Tests for User Story 2

- [X] T011 [P] [US2] Inspect backend/package candidate diffs for apps/api and packages paths
- [X] T012 [P] [US2] Inspect frontend candidate diffs for apps/web paths

### Implementation for User Story 2

- [X] T013 [US2] Port accepted backend API fixes into apps/api/src/api and apps/api/tests
- [X] T014 [US2] Port accepted package fixes into packages/agent_adapters, packages/core, and packages/tool_registry
- [X] T015 [US2] Port accepted frontend service/store/viewer fixes into apps/web/src/services and apps/web/src/store
- [X] T016 [US2] Port accepted frontend component/test fixes into apps/web/src/components, apps/web/src/test, and apps/web/tests
- [X] T017 [US2] Port accepted MCP catalog documentation updates into docs/mcp-catalog/testing-problem-log.md
- [X] T018 [US2] Record rejected or partially applied candidates in scratch/nous_hackathon_candidates/REVIEW_NOTES.md

**Checkpoint**: Accepted fixes are applied without excluded prototype artifacts.

---

## Phase 5: User Story 3 - Validate The Extracted Work (Priority: P3)

**Goal**: Prove extracted work fits the current branch and document any blockers.

**Independent Test**: Targeted tests pass or failures are documented with next actions.

### Validation for User Story 3

- [X] T019 [US3] Run targeted backend/package tests with uv run pytest for touched API/package areas
- [X] T020 [US3] Run targeted frontend tests with npm run test --workspace=apps/web for touched frontend areas
- [X] T021 [US3] Run exclusion checks over final git diff to verify no Stripe, nemoclaw, hackathon, generated-output, or paid-demo files were applied
- [X] T022 [US3] Document validation results in scratch/nous_hackathon_candidates/REVIEW_NOTES.md

**Checkpoint**: Extraction is validated or blockers are clearly recorded.

---

## Final Phase: Polish & Cross-Cutting Concerns

**Purpose**: Make Spec Kit artifacts and implementation state easy to review.

- [X] T023 Update specs/036-port-nous-fixes/tasks.md task statuses as work completes
- [X] T024 Review final git status and summarize changed files
- [X] T025 Confirm AGENTS.md points to specs/036-port-nous-fixes/plan.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies
- **Foundational (Phase 2)**: Depends on Setup completion and blocks source edits
- **User Story 1 (Phase 3)**: Depends on Foundational classification
- **User Story 2 (Phase 4)**: Depends on User Story 1
- **User Story 3 (Phase 5)**: Depends on accepted changes from User Story 2
- **Polish**: Depends on validation

### User Story Dependencies

- **User Story 1 (P1)**: No source edits; verifies review material
- **User Story 2 (P2)**: Depends on classified candidates from US1
- **User Story 3 (P3)**: Depends on accepted applied changes from US2

### Parallel Opportunities

- T002 and T003 can run in parallel.
- T008 and T009 can run in parallel.
- T011 and T012 can run in parallel.
- Backend/package and frontend test commands can run separately after their respective changes are applied.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete setup and foundational classification.
2. Confirm the copied candidate folder is safe to review.
3. Stop if excluded files are present as port-ready candidates.

### Incremental Delivery

1. Port backend/package fixes first.
2. Port frontend/service/viewer fixes second.
3. Port documentation updates last.
4. Run targeted validation and exclusion checks.

### Notes

- `[P]` tasks are parallelizable because they touch different files or are read-only.
- Mixed-risk candidates must be partially applied or rejected.
- Do not add new branch creation, prototype Docker stack changes, generated outputs, or payment/demo features.
