# Tasks: UI Redesign and Global Color Schemes

**Input**: Design documents from `/specs/019-ui-theme-redesign/`

**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md

**Tests**: Tests are explicitly requested to ensure UI consistency and layout correctness. Both component unit tests and UI integration tests are specified.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Contains exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and base configuration setup

- [x] T001 Add `UI_THEME` environment variable definition to configuration template `docker/.env.example`
- [x] T002 [P] Configure Vitest test environments for styling validations in `apps/web/package.json`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core variables and configuration foundations

**⚠️ CRITICAL**: Must complete before starting user story implementations

- [x] T003 Define initial layout variables, typography scales, and sizing values inside `apps/web/src/tokens/design-tokens.css`
- [x] T004 [P] Declare `theme` string parameter field in backend SetupStatusResponse router model in `apps/api/src/api/routers/setup.py`

**Checkpoint**: Foundation ready - UI styling and configuration models are set up.

---

## Phase 3: User Story 1 - Consistent Typography, Alignment, and Visual Layout (Priority: P1) 🎯 MVP

**Goal**: Establish consistent font sizing, correct panel overlaps, and align buttons/icons in tool cards.

**Independent Test**: Bounding boxes of tool panels have matching coordinates, text fits cleanly without overflows, and buttons align identically across cards.

### Tests for User Story 1 (TDD)
*Write these tests first and ensure they fail before modifying layout styles.*

- [x] T005 [P] [US1] Write Playwright layout and alignment verification tests in `tests/ui-integration/ui-consistency-theme.spec.ts`
- [x] T006 [P] [US1] Write component rendering and CSS style checks in `apps/web/src/test/ToolRegistryLayout.spec.tsx`

### Implementation for User Story 1

- [x] T007 [US1] Configure standard type scale sizes and text styles inside `apps/web/src/index.css`
- [x] T008 [US1] Update container flexbox/grid dimensions to prevent overlapping inside `apps/web/src/App.css`
- [x] T009 [US1] Clean up badge alignments and update indicators inside `apps/web/src/components/pages/ToolRegistryPage.tsx`
- [x] T010 [US1] Refactor tool card action button shapes and placement patterns inside `apps/web/src/components/pages/ToolRegistryPage.tsx`


**Checkpoint**: At this point, typography and card layouts are visually consistent and free of overlaps.

---

## Phase 4: User Story 2 - Global Theme Customization (Priority: P1)

**Goal**: Bind color schemes to design tokens and toggle theme modes via root document attribute.

**Independent Test**: Changing the API setup theme configuration switches the UI theme dynamically on reload.

### Tests for User Story 2 (TDD)

- [x] T011 [P] [US2] Write Playwright integration tests checking `data-theme` body attributes in `tests/ui-integration/ui-consistency-theme.spec.ts`
- [x] T012 [P] [US2] Write unit tests checking Setup Status API response changes in `apps/api/tests/test_setup_api.py`

### Implementation for User Story 2

- [x] T013 [US2] Define theme CSS properties for both `light` and `dark` styles in `apps/web/src/tokens/design-tokens.css`
- [x] T014 [US2] Load `UI_THEME` variable (defaulting to `"dark"`) inside backend configuration reader `apps/api/src/api/config.py`
- [x] T015 [US2] Resolve and output theme value from `get_setup_status` router handler in `apps/api/src/api/routers/setup.py`
- [x] T016 [US2] Capture setup status `theme` parameter on load and set root `data-theme` attribute inside `apps/web/src/App.tsx`

**Checkpoint**: Application color schemes switch globally based on backend-served data.

---

## Phase 5: User Story 3 - Configuration-driven Theme Selection (Priority: P2)

**Goal**: Enable developer configuration of active theme via configuration file setup.

**Independent Test**: Set `UI_THEME=light` in `.env`, start the app, and verify the app renders in the premium light scheme.

### Implementation for User Story 3

- [x] T017 [US3] Map configuration setup instructions inside setup guide `specs/019-ui-theme-redesign/quickstart.md`
- [x] T018 [US3] Verify configuration fallbacks and default environment configurations in config loader tests `apps/api/tests/test_config.py`


**Checkpoint**: Theme configuration can be set easily inside local configuration files.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Visual polishing, code formatting, and validation sweeps

- [x] T019 [P] Update documentation on typography scales and color themes in repository `README.md`
- [x] T020 Run quality validation gates (lint, check types, format) using `Makefile`
- [x] T021 Run all test suites (Vitest, pytest, Playwright) and confirm passing results

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Can start immediately.
- **Foundational (Phase 2)**: Depends on Setup completion. Blocks User Stories.
- **User Stories (Phases 3 & 4)**: Depend on Foundational completion. Can run in parallel.
- **User Story 3 (Phase 5)**: Depends on User Story 2 completion.
- **Polish (Phase 6)**: Depends on all user stories being completed.

### Parallel Opportunities

- Setup tasks `T001` and `T002` can run in parallel.
- TDD test tasks `T005`/`T006` and `T011`/`T012` can be written in parallel.
- Card styling `T009` and button refactoring `T010` can proceed in parallel.

---

## Parallel Example: User Story 1
```bash
# Writing and running the test templates:
Task: "Write Playwright layout and alignment verification tests in tests/ui-integration/ui-consistency-theme.spec.ts"
Task: "Write component rendering and CSS style checks in apps/web/src/test/ToolRegistryLayout.spec.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)
1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Run layout consistency tests to confirm cards and typography align.

### Incremental Delivery
1. Foundation Complete → Layout Redesign Complete (MVP!)
2. Theme Customization (US2) Complete → Switchable color palette.
3. Configuration overrides (US3) Complete → Simple setting file support.
4. Execute full verification passes.
