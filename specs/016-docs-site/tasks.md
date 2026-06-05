# Tasks: Documentation Site

**Input**: Design documents from `/specs/016-docs-site/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project verification and clean environment checks

- [x] T001 Verify active git branch is `016-docs-site` and workspace is clean
- [x] T002 Verify that `specs/016-docs-site/spec.md` and `plan.md` are completed

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core framework verification before docs are built

- [x] T003 Verify local environment can install dependencies and build static packages on the host

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Adopt MkDocs Material & Organization (Priority: P1) 🎯 MVP

**Goal**: Configure MkDocs Material and setup the folder structure and navigation menus.

**Independent Test**: Verify `mkdocs.yml` exists, theme colors/logo are defined, and navigation sections are mapped.

### Implementation for User Story 1

- [x] T004 [P] [US1] Create root configuration file `mkdocs.yml` specifying Material theme, palettes, search plugin, and navigation menus
- [x] T005 [US1] Create `docs/` directory and populate all empty markdown source pages according to the navigation schema in plan.md

**Checkpoint**: MkDocs layout and skeleton files are created.

---

## Phase 4: User Story 2 - Automated GitHub Pages Deployment (Priority: P1)

**Goal**: Implement GitHub Actions automated publisher to build and deploy to gh-pages branch.

**Independent Test**: Verify `.github/workflows/docs-deploy.yml` triggers on push to main and contains correct configuration.

### Implementation for User Story 2

- [x] T006 [P] [US2] Create automated GHA deployment workflow file at `.github/workflows/docs-deploy.yml` building and deploying docs to `gh-pages` branch
- [x] T007 [US2] Validate `docs-deploy.yml` syntax using local safe loader check

**Checkpoint**: Automated Pages deployment is configured.

---

## Phase 5: User Story 3 - Historical Content Migration & Consolidation (Priority: P2)

**Goal**: Migrate legacy specs and architecture markdown files into target directories under docs.

**Independent Test**: Verify migrated sections match the content and contain valid markdown formatting.

### Implementation for User Story 3

- [x] T008 [P] [US3] Migrate and structure legacy technical analysis from `docs/technical_analysis.md` to `docs/architecture/` subpages
- [x] T009 [P] [US3] Migrate and structure legacy Docker guidelines from `docs/agent-docker-architecture.md` to `docs/user-guide/` and `docs/architecture/`
- [x] T010 [P] [US3] Migrate and structure legacy MCP tool list from `docs/Engineering MCP Tools Discovery.md` to `docs/mcp-catalog/tools-list.md`

**Checkpoint**: Scattered documentation is successfully consolidated.

---

## Phase 6: User Story 4 - Formatting Callouts & Admonitions (Priority: P3)

**Goal**: Enhance documentation styling with admonition boxes and confirm clean compilations.

**Independent Test**: Verify local compilation works without warnings or errors.

### Implementation for User Story 4

- [x] T011 [US4] Format warning, note, tip, and guideline blocks across all markdown docs using Material admonition syntax
- [x] T012 [US4] Run local strict build compilation using `mkdocs build --strict` to verify zero dead links or formatting syntax errors

**Checkpoint**: Styling calls and linkages are validated.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Cleanup and validation tasks

- [x] T013 Verify no core application files are modified and clean up workspace
- [x] T014 Run final checks and verify all checklist items are completed

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
- **User Story 4 (P3)**: Can start after User Story 1 (Phase 3) is completed

### Parallel Opportunities

- Creation of `mkdocs.yml` (T004) and `docs-deploy.yml` (T006) can run in parallel.
- Migrating content (T008, T009, T010) can run in parallel as they target separate files.
