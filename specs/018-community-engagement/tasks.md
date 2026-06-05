# Tasks: Community Engagement Infrastructure

**Input**: Design documents from `/specs/018-community-engagement/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure checks

- [x] T001 Verify active git branch is `018-community-engagement` and workspace is clean
- [x] T002 Create directories `examples/quickstart/`, `examples/bracket-design/`, `examples/bolt-analysis/`, `docs/community/`, `docs/blog/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core wright api accessibility checks

**⚠️ CRITICAL**: Verification that local backend containers are running must complete before example scripts can be tested.

- [x] T003 Verify local wright backend API container is active and responsive to HTTP request calls on `http://localhost:8000`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel.

---

## Phase 3: User Story 1 - Examples and Getting Started (Priority: P1) 🎯 MVP

**Goal**: Deliver runnable examples demonstrating wright's capabilities.

**Independent Test**: Execute each Python script under `examples/` locally and verify successful output file creation or API integration response.

### Implementation for User Story 1

- [x] T004 [P] [US1] Create `examples/quickstart/README.md` containing run commands and expected verification outputs
- [x] T005 [P] [US1] Create `examples/quickstart/main.py` script to fetch system status and log response from API
- [x] T006 [P] [US1] Create `examples/bracket-design/README.md` with instructions on parameter values and file generation
- [x] T007 [P] [US1] Create `examples/bracket-design/main.py` executing CAD agent parameter design
- [x] T008 [P] [US1] Create `examples/bolt-analysis/README.md` detailing calculator input formats and running instructions
- [x] T009 [P] [US1] Create `examples/bolt-analysis/main.py` executing bolt stress calculations

**Checkpoint**: User Story 1 is fully functional and testable independently.

---

## Phase 4: User Story 2 - Community Communication Channels & Integrations (Priority: P2)

**Goal**: Establish clear pathways for support and discussions across the repo resources.

**Independent Test**: Confirm all invite badges, links, and guidelines render properly and resolve to target Discord and Discussions locations.

### Implementation for User Story 2

- [x] T010 [P] [US2] Create `docs/community/discord-admin.md` documenting server settings, permanent invite generation, and rules
- [x] T011 [US2] Update `README.md` to add Discord badge, GitHub Discussions invitation, and star history badge
- [x] T012 [P] [US2] Update `CONTRIBUTING.md` with Discord server links and contributor recognition policy
- [x] T013 [P] [US2] Update `SUPPORT.md` with Discord support channel instructions and discussions guidelines

**Checkpoint**: User Story 2 is completed and integrated.

---

## Phase 5: User Story 3 - Launch Assets and Contributor Curation (Priority: P3)

**Goal**: Prepare marketing materials, starter issues, and community tooling configs.

**Independent Test**: Verify markdown files have zero placeholder sections and `.all-contributorsrc` can be parsed.

### Implementation for User Story 3

- [x] T014 [P] [US3] Create `docs/blog/introducing-wright.md` containing the 1500-2000 word blog post draft
- [x] T015 [P] [US3] Create `docs/demo-script.md` containing video recording storyboard and scenes
- [x] T016 [P] [US3] Create `docs/good-first-issues.md` with 5-10 curated tasks for new contributors
- [x] T017 [P] [US3] Create `docs/awesome-list-submissions.md` with Awesome list PR templates
- [x] T018 [P] [US3] Create root `.all-contributorsrc` initializing the All Contributors JSON configuration

**Checkpoint**: User Story 3 is completed and verified.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Cleanup, validation, and execution check of examples

- [x] T019 Run all example Python scripts locally to verify correct output generation
- [x] T020 Run git diff checks to verify that no application files under `apps/` or `packages/` have been modified

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

- All examples creation tasks (`T004` through `T009`) are marked `[P]` and can run in parallel since they create separate scripts and READMEs.
- Custom documentation templates under `docs/` (`T010`, `T014`, `T015`, `T016`, `T017`) are also independent.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Verify examples run successfully
5. Commit and merge if verified
