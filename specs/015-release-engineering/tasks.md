# Tasks: Release Engineering & Versioning

**Input**: Design documents from `/specs/015-release-engineering/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project verification and clean environment checks

- [x] T001 Verify active git branch is `015-release-engineering` and workspace is clean
- [x] T002 Verify that `specs/015-release-engineering/spec.md` and `plan.md` are completed

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core configuration setup before release automation is coded

- [x] T003 Ensure root `pyproject.toml` exists and verify `docker-build.yml` is present under `.github/workflows/`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Adopt Semantic Versioning & Source of Truth (Priority: P1) 🎯 MVP

**Goal**: Establish SemVer source of truth at v0.1.0 in pyproject.toml.

**Independent Test**: Verify `pyproject.toml` version matches, git tag runs, and configuration has no errors.

### Implementation for User Story 1

- [x] T004 [P] [US1] Set `version` field to `0.1.0` in root `pyproject.toml`
- [x] T005 [US1] Run dry-run git tag command locally to verify tagging permissions and setup

**Checkpoint**: Versioning source of truth is established.

---

## Phase 4: User Story 2 - Adopt Keep a Changelog & Document Policy (Priority: P1)

**Goal**: Create CHANGELOG.md file and versioning guidelines documentation.

**Independent Test**: Verify CHANGELOG.md exists in root and versioning policy is documented under docs/versioning.md.

### Implementation for User Story 2

- [x] T008 [P] [US2] Create `CHANGELOG.md` in repository root, pre-populating with changelog notes from features 001-010
- [x] T009 [P] [US2] Create versioning strategy documentation at `docs/versioning.md` explaining SemVer rules and release tags

**Checkpoint**: Changelog and versioning policy are documented.

---

## Phase 5: User Story 3 - Automate Version Tagged Releases (Priority: P2)

**Goal**: Create release workflow to automate Docker Hub builds and GitHub Releases on tag pushes.

**Independent Test**: Verify `.github/workflows/release.yml` triggers on version tag pushes and executes building and release creation.

### Implementation for User Story 3

- [x] T010 [P] [US3] Create GHA release workflow file at `.github/workflows/release.yml` executing tag check, container build/push, and GitHub Release creation
- [x] T011 [US3] Validate `release.yml` syntax using local safe loader check

**Checkpoint**: Tag-driven releases are automated.

---

## Phase 6: User Story 4 - Automated Release Drafting on PR Merge (Priority: P2)

**Goal**: Configure Release Drafter to draft release notes automatically on PR merges.

**Independent Test**: Verify release-drafter config files exist and parse cleanly.

### Implementation for User Story 4

- [x] T012 [P] [US4] Create Release Drafter configuration file at `.github/release-drafter.yml` mapping labels to category headers
- [x] T013 [P] [US4] Create GHA Release Drafter workflow at `.github/workflows/release-drafter.yml` triggering on pushes to main
- [x] T014 [US4] Validate `.github/release-drafter.yml` and workflow YAML syntax using local safe loader check

**Checkpoint**: Release drafting is automated.

---

## Phase 7: User Story 5 - Versioned Docker Builds on dev/main pushes (Priority: P2)

**Goal**: Modify the existing docker-build.yml to handle pushes to dev, main, and version tags.

**Independent Test**: Verify modified GHA config parses successfully and contains correct branch-to-tag conditions.

### Implementation for User Story 5

- [x] T015 [US5] Modify existing `.github/workflows/docker-build.yml` workflow to implement branch stability tagging (latest for main, dev for dev, vX.Y.Z for tag) and validate builds on PRs
- [x] T016 [US5] Validate `docker-build.yml` syntax using local safe loader check

**Checkpoint**: Docker builds are branch-versioned.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Cleanup, validation, and documentation tasks

- [x] T017 Verify all generated GHA workflow configurations parse cleanly without syntax errors
- [x] T018 Run final checks and verify all checklist items are completed

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phases 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2)
- **User Story 2 (P1)**: Can start after Foundational (Phase 2)
- **User Story 3 (P2)**: Can start after Foundational (Phase 2)
- **User Story 4 (P2)**: Can start after Foundational (Phase 2)
- **User Story 5 (P2)**: Can start after Foundational (Phase 2)

### Parallel Opportunities

- Creation of configs (`release.yml`, `release-drafter.yml`, `CHANGELOG.md`, `docs/versioning.md`) can run in parallel since they create distinct files.
- Safe loader validations can run in parallel.
- User Stories can run in parallel after foundational checks pass.
