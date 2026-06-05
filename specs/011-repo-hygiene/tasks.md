# Tasks: Repo Hygiene & Legal Foundation

**Input**: Design documents from `/specs/011-repo-hygiene/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project verification and clean environment checks

- [ ] T001 Verify active git branch is `011-repo-hygiene` and workspace is clean

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core directories that MUST exist before user stories are executed

- [ ] T002 Create `docs/images/` directory if it does not exist

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - License and Legal Clarity (Priority: P1) 🎯 MVP

**Goal**: Establish clear, permissive legal terms by adopting the MIT license.

**Independent Test**: Verify that the file `LICENSE` exists in the repository root and contains the full MIT license text with copyright holder `burhop` and year `2026`.

### Implementation for User Story 1

- [ ] T003 [P] [US1] Create LICENSE file in repository root with MIT License text

**Checkpoint**: At this point, User Story 1 is fully functional and legally compliant.

---

## Phase 4: User Story 2 - Contributor Onboarding Guide (Priority: P1)

**Goal**: Provide a detailed guide for potential open-source contributors on local environment setup, speckit workflow, branch conventions, and style tools.

**Independent Test**: Read `CONTRIBUTING.md` and verify it contains development setup steps, spec-kit workflow, branch naming, styling tools, PR checklist, and constitution.md compliance guidelines.

### Implementation for User Story 2

- [ ] T004 [P] [US2] Create CONTRIBUTING.md file in repository root with contributor guidelines

**Checkpoint**: User Story 2 is ready to guide external contributors.

---

## Phase 5: User Story 3 - Community Standards and Safety (Priority: P2)

**Goal**: Establish community behavior standards (Code of Conduct) and a secure reporting channel for vulnerabilities.

**Independent Test**: Verify that both `CODE_OF_CONDUCT.md` and `SECURITY.md` exist, and that `SECURITY.md` specifies private contact info (email `burhop@gmail.com`) and SLA.

### Implementation for User Story 3

- [ ] T005 [P] [US3] Create CODE_OF_CONDUCT.md file in repository root with Contributor Covenant v2.1
- [ ] T006 [P] [US3] Create SECURITY.md file in repository root with security reporting guidelines

**Checkpoint**: Safety guidelines and security response procedures are fully established.

---

## Phase 6: User Story 4 - Support Channel Guidance (Priority: P2)

**Goal**: Guide users seeking support to the appropriate channels to minimize issue tracker noise.

**Independent Test**: Read `SUPPORT.md` and verify it maps usage questions to GitHub Discussions, bugs to Issues, and technical details to docs.

### Implementation for User Story 4

- [ ] T007 [P] [US4] Create SUPPORT.md file in repository root with support channels guide

**Checkpoint**: Support routing is functional.

---

## Phase 7: User Story 5 - Code Ownership and Review Assignment (Priority: P2)

**Goal**: Automate review assignment based on file patterns.

**Independent Test**: Check that `.github/CODEOWNERS` exists and defines reviewer mappings for backend, packages, frontend, infra, and specifications.

### Implementation for User Story 5

- [ ] T008 [P] [US5] Create .github/CODEOWNERS file mapping path patterns to @burhop

**Checkpoint**: Automated review assignment is active.

---

## Phase 8: User Story 6 - Repository Cleanup and Professional Appearance (Priority: P3)

**Goal**: Clean up loose screenshots, log, database, and temporary test files in the repo root and update `.gitignore` rules.

**Independent Test**: Run `git status` to ensure that all loose files are either relocated or ignored.

### Implementation for User Story 6

- [ ] T009 [US6] Move screenshot_*.png files from repository root to docs/images/
- [ ] T010 [US6] Update references to screenshots in docs/community-features/012-readme-branding.md
- [ ] T011 [US6] Update .gitignore file in repository root to ignore state.db, tests_output/, screenshot_*.png, and *.log files
- [ ] T012 [US6] Remove untracked stale logs, db, and txt files from the local repository root (e.g. phase1.log, phase2.log, ps_debug.log, test-*.log, tests_output*.txt)

**Checkpoint**: The repository root is clean and free of build/debug noise.

---

## Phase 9: User Story 7 - Repository Discoverability via Metadata (Priority: P3)

**Goal**: Document description and topic tags configuration for the repository owner to apply.

**Independent Test**: Read `docs/metadata-guide.md` and verify it recommends the 120-character description and all 20 topic tags.

### Implementation for User Story 7

- [ ] T013 [P] [US7] Create docs/metadata-guide.md documenting GitHub About description and 20 topic tags

**Checkpoint**: Metadata configuration is documented and ready for deployment.

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: General validation and project integrity checks.

- [ ] T014 Run quickstart.md validation checklist
- [ ] T015 Verify that no source code, Docker files, or README.md files have been modified

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
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 3 (P2)**: Can start after Foundational (Phase 2)
- **User Story 4 (P2)**: Can start after Foundational (Phase 2)
- **User Story 5 (P2)**: Can start after Foundational (Phase 2)
- **User Story 6 (P3)**: Depends on Phase 2 (Foundational) for `docs/images/` creation
- **User Story 7 (P3)**: Can start after Foundational (Phase 2)

### Parallel Opportunities

- T003 [US1], T004 [US2], T005 [US3], T006 [US3], T007 [US4], T008 [US5], and T013 [US7] can be worked on in parallel.

---

## Parallel Example: User Story 3

```bash
# Generate both community safety documents in parallel:
Task: "Create CODE_OF_CONDUCT.md file in repository root with Contributor Covenant v2.1"
Task: "Create SECURITY.md file in repository root with security reporting guidelines"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1 (License creation)
4. **STOP and VALIDATE**: Verify license is correct
5. Add next priorities incrementally.
