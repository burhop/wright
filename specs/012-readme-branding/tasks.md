# Tasks: README Overhaul & Branding

**Input**: Design documents from `/specs/012-readme-branding/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project verification and clean environment checks

- [x] T001 Verify active git branch is `012-readme-branding` and workspace is clean

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core directories that MUST exist before user stories are executed

- [x] T002 Create `docs/images/` directory if it does not exist

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Visual Identity and Branding (Priority: P1)

**Goal**: Establish visual branding assets (logos and social preview cards).

**Independent Test**: Verify that the files `docs/images/wright-logo.svg`, `docs/images/wright-logo.png`, and `docs/images/social-preview.png` exist and display the correct dimensions and visual theme.

### Implementation for User Story 1

- [x] T003 [P] [US1] Create docs/images/wright-logo.svg vector logo combining mechanical gear and neural paths
- [x] T004 [P] [US1] Create docs/images/wright-logo.png high-resolution raster logo
- [x] T005 [P] [US1] Create docs/images/social-preview.png social preview image (1280x640px) with logo, tagline, and feature icons

**Checkpoint**: Branding visual assets are fully generated and saved.

---

## Phase 4: User Story 2 - README Hero and Why Wright Narrative (Priority: P1) 🎯 MVP

**Goal**: Present the core tagline, shields.io status indicators, and agent orchestrator value proposition at the top of the README.

**Independent Test**: Open the first sections of `README.md` and confirm that the tagline, 6 badges, and the narrative explaining the vision of bringing developer AI productivity gains to traditional engineering are visible.

### Implementation for User Story 2

- [x] T006 [US2] Update README.md to add Hero section with centered logo and shields.io badge row (Build, License, Docker, Python, Node, Stars)
- [x] T007 [US2] Update README.md to add Why Wright narrative section outlining the orchestrator vision and flexible deployment options

**Checkpoint**: The landing page core presentation (Hero + Narrative) is complete.

---

## Phase 5: User Story 3 - Feature Cards & UI Showcases (Priority: P2)

**Goal**: Showcase the engineering capabilities and user interface of Wright with scannable feature cards and UI screenshots.

**Independent Test**: Read the features and UI sections of `README.md` and verify all 6 emoji cards render and all 4 screenshot images load from the `docs/images/` folder.

### Implementation for User Story 3

- [x] T008 [US3] Update README.md to add emojified cards highlighting Universal Agent Orchestration, Plug-and-Play Tool Registry, Deterministic Tool Actuation, Software-Level Workflow Automation, Flexible & Secure Deployment, and Appliance-in-a-Box Setup
- [x] T009 [US3] Update README.md to embed screenshots from docs/images/ with captions (Chat, Tool Registry, File Vault)

**Checkpoint**: Feature cards and screenshots are embedded.

---

## Phase 6: User Story 4 - Setup and Architecture Diagrams (Priority: P2)

**Goal**: Provide a clean Docker Quick Start terminal block and a Mermaid flowchart explaining system request paths.

**Independent Test**: Verify that the Mermaid diagram renders correctly without errors and the Quick Start block commands are clear and copy-pasteable.

### Implementation for User Story 6

- [x] T010 [US4] Update README.md to add simplified Docker Quick Start block with minimal install instructions
- [x] T011 [US4] Update README.md to add Mermaid architecture request-flow diagram (API -> Agents -> Tools)

**Checkpoint**: Technical setup instructions and component flows are documented.

---

## Phase 7: User Story 5 - Contributing, Footer, and Cleanups (Priority: P3)

**Goal**: Link to onboarding guidelines, add star history visualization, and cleanup leftover files.

**Independent Test**: Verify that the footer links resolve successfully, and no `screenshot_*.png` files remain in the root directory.

### Implementation for User Story 5

- [x] T012 [US5] Update README.md to add Contributing callout linking to CONTRIBUTING.md, and star-history.com footer
- [x] T013 [US5] Verify that the repository root is free of any loose screenshot_*.png files

**Checkpoint**: Footer links are active and repository root is clean.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: General validation and project integrity checks.

- [x] T014 Run quickstart.md validation checklist
- [x] T015 Verify that no source code, Docker files, or CI/CD files have been modified

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

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P1)**: Depends on US1 for logo asset availability in README
- **User Story 3 (P2)**: Can start after Foundational (Phase 2)
- **User Story 4 (P2)**: Can start after Foundational (Phase 2)
- **User Story 5 (P3)**: Can start after Foundational (Phase 2)

### Parallel Opportunities

- T003 [US1], T004 [US1], T005 [US1] can run in parallel as they create separate graphic files.
- US3, US4, and US5 documentation sections in the README can be written in parallel once the template structure is set.

---

## Parallel Example: User Story 1

```bash
# Generate all visual assets in parallel:
Task: "Create docs/images/wright-logo.svg vector logo"
Task: "Create docs/images/wright-logo.png high-resolution logo"
Task: "Create docs/images/social-preview.png social preview image"
```

---

## Implementation Strategy

### MVP First (User Stories 1 & 2 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1 (Create branding assets)
4. Complete Phase 4: User Story 2 (Create Hero and Why Wright sections)
5. **STOP and VALIDATE**: Verify logo and top README sections render correctly
6. Complete remaining sections incrementally.
