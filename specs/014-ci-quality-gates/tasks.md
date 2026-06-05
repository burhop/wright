# Tasks: CI/CD Quality Gates

**Input**: Design documents from `/specs/014-ci-quality-gates/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project verification and clean environment checks

- [x] T001 Verify active git branch is `014-ci-quality-gates` and workspace is clean
- [x] T002 Verify that `specs/014-ci-quality-gates/spec.md` and `plan.md` are completed

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core directories and packages that MUST exist before user stories are executed

- [x] T003 Verify local package setups (`package.json` exists in `apps/web/` and `pyproject.toml` exists in root)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Continuous Integration Quality Gates (Priority: P1) 🎯 MVP

**Goal**: Implement GHA workflows for Python and TypeScript/Frontend code triggered on pushes/PRs to main and dev.

**Independent Test**: Verify `.github/workflows/python-quality.yml` and `.github/workflows/frontend-quality.yml` exist, contain correct configuration, and parse cleanly.

### Implementation for User Story 1

- [x] T004 [P] [US1] Create Python GHA workflow at `.github/workflows/python-quality.yml` to run `ruff check`, `ruff format --check`, `mypy`, and `pytest` with uv caching
- [x] T005 [US1] Validate `python-quality.yml` YAML syntax locally using Python safe loader check
- [x] T006 [P] [US1] Create Frontend GHA workflow at `.github/workflows/frontend-quality.yml` to run `eslint`, `prettier --check`, and `tsc --noEmit` with node caching
- [x] T007 [US1] Validate `frontend-quality.yml` YAML syntax locally using Python safe loader check

**Checkpoint**: Automated CI quality gates are fully configured.

---

## Phase 4: User Story 2 - Local Developer Tooling & Convenience (Priority: P2)

**Goal**: Implement local Makefile targets and pre-commit hook configuration.

**Independent Test**: Verify `make lint`, `make format`, etc. run locally and pre-commit hooks install/validate correctly.

### Implementation for User Story 2

- [x] T008 [P] [US2] Create pre-commit config at `.pre-commit-config.yaml` to run ruff, eslint, prettier, check-yaml, and whitespace hooks
- [x] T009 [US2] Validate `.pre-commit-config.yaml` structure locally using Python safe loader check
- [x] T010 [US2] Update `Makefile` at repository root with non-Docker developer quality targets (`lint`, `format`, `typecheck`, `test`, `check`)
- [x] T011 [US2] Verify Makefile targets run successfully on local machine

**Checkpoint**: Local verification targets and pre-commit hooks are configured.

---

## Phase 5: User Story 3 - Code Standard Standardization & Gating (Priority: P3)

**Goal**: Create an EditorConfig file and update contributing guidelines for pre-commit.

**Independent Test**: Verify EditorConfig exists and contributing instructions are documented.

### Implementation for User Story 3

- [x] T012 [P] [US3] Create EditorConfig at `.editorconfig` setting indentation rules (4 spaces for Python, 2 spaces for JS/TS/YAML/JSON/CSS)
- [x] T013 [US3] Verify `.editorconfig` formatting rules are correctly set up
- [x] T014 [US3] Modify `CONTRIBUTING.md` to document how developers can install and activate pre-commit hooks

**Checkpoint**: Project standards are standardized.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Cleanup, validation, and documentation tasks

- [x] T015 Verify all generated configuration files parse cleanly and do not modify any application code
- [x] T016 Run final validation and verify all tasks are marked as completed

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2)
- **User Story 2 (P2)**: Can start after Foundational (Phase 2)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2)

### Parallel Opportunities

- Creation of workflow templates (T004, T006) and config files (T008, T012) can run in parallel since they create distinct files.
- YAML syntax validations can run in parallel.
- All three user stories can run in parallel after foundational checks pass.

---

## Parallel Example: Workflow & Config Creation

```bash
# Generate configuration files in parallel:
Task: "Create python-quality.yml"
Task: "Create frontend-quality.yml"
Task: "Create .pre-commit-config.yaml"
Task: "Create .editorconfig"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1 (Python & Frontend CI)
4. **STOP and VALIDATE**: Verify CI YAML workflows validate correctly
5. Complete remaining local developer targets.
