# Tasks: GitHub Templates & Issue Automation

**Input**: Design documents from `/specs/013-github-templates/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project verification and clean environment checks

- [x] T001 Verify active git branch is `013-github-templates` and workspace is clean
- [x] T002 Verify that `specs/013-github-templates/spec.md` and `plan.md` are completed

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core directories and configuration that MUST exist before user stories are executed

- [x] T003 Create `.github/` and `.github/ISSUE_TEMPLATE/` directories if they do not exist
- [x] T004 [P] Verify `python-yaml` library is available in dev environment for syntax validation checks

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Structured Bug Reporting (Priority: P1) 🎯 MVP

**Goal**: Implement form-based Bug Report issue template with structured fields and auto-applied labels.

**Independent Test**: Verify that `.github/ISSUE_TEMPLATE/bug_report.yml` exists, conforms to GitHub's issue forms syntax, requires the Wright version, and applies `bug` and `needs-triage` labels.

### Implementation for User Story 1

- [x] T005 [P] [US1] Create `.github/ISSUE_TEMPLATE/bug_report.yml` with structured form fields (description, reproduction, expected/actual, environment, version, OS, logs) and auto-apply labels: `bug`, `needs-triage`
- [x] T006 [US1] Validate `bug_report.yml` syntax using local python validator script

**Checkpoint**: Bug Report template is fully functional.

---

## Phase 4: User Story 2 - Structured Feature Suggestions (Priority: P1)

**Goal**: Implement form-based Feature Request issue template with structured fields and auto-applied labels.

**Independent Test**: Verify that `.github/ISSUE_TEMPLATE/feature_request.yml` exists, collects component details and contributor willingness, and applies `enhancement` and `needs-triage` labels.

### Implementation for User Story 2

- [x] T007 [P] [US2] Create `.github/ISSUE_TEMPLATE/feature_request.yml` with feature summary, use case, proposed solution, component dropdown, and willingness to contribute, and auto-apply labels: `enhancement`, `needs-triage`
- [x] T008 [US2] Validate `feature_request.yml` syntax using local python validator script

**Checkpoint**: Feature Request template is fully functional.

---

## Phase 5: User Story 3 - Issue Redirection & Security Gating (Priority: P2)

**Goal**: Configure issue chooser config to disable blank issues and redirect Q&A to Discussions and security to SECURITY.md.

**Independent Test**: Verify `.github/ISSUE_TEMPLATE/config.yml` exists, disables blank issues, and has active link redirections.

### Implementation for User Story 3

- [x] T009 [P] [US3] Create `.github/ISSUE_TEMPLATE/config.yml` to disable blank issues, specify issue templates, and redirect Q&A queries to GitHub Discussions and security issues to `SECURITY.md`
- [x] T010 [US3] Validate `config.yml` syntax using local python validator script

**Checkpoint**: Issue chooser redirection is configured.

---

## Phase 6: User Story 4 - Standardized Contributions (PR Template) (Priority: P2)

**Goal**: Create a lightweight checklist Pull Request template for self-validation of code and spec compliance.

**Independent Test**: Verify `.github/PULL_REQUEST_TEMPLATE.md` exists and contains standard checklists (docs, tests, CONTRIBUTING.md, and constitution.md).

### Implementation for User Story 4

- [x] T011 [P] [US4] Create `.github/PULL_REQUEST_TEMPLATE.md` containing fields for change descriptions, related issues, CONTRIBUTING.md compliance, and constitution.md checks
- [x] T012 [US4] Verify `PULL_REQUEST_TEMPLATE.md` markdown formatting renders cleanly

**Checkpoint**: Pull Request template is active.

---

## Phase 7: User Story 5 - Automated Dependency Updates (Dependabot) (Priority: P3)

**Goal**: Configure weekly automated dependency updates with grouped updates and open PR limits.

**Independent Test**: Verify `.github/dependabot.yml` exists, targets pip, npm, docker, and actions weekly, and groups minor/patch packages.

### Implementation for User Story 5

- [x] T013 [P] [US5] Create `.github/dependabot.yml` with pip, npm, docker, and github-actions ecosystems scheduled weekly, minor/patch grouping, and limit of 5 open PRs
- [x] T014 [US5] Validate `dependabot.yml` syntax using local python validator script

**Checkpoint**: Dependabot updates are scheduled.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Cleanup, validation, and documentation tasks

- [x] T015 Document recommended label set (20+ standard labels with colors and descriptions) in spec or feature documentation
- [x] T016 Remove any old markdown-based issue templates in `.github/ISSUE_TEMPLATE/`
- [x] T017 Run final syntax validation check on all generated configurations using `quickstart.md` validator script

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
- **User Story 2 (P1)**: Can start after Foundational (Phase 2)
- **User Story 3 (P2)**: Can start after Foundational (Phase 2)
- **User Story 4 (P2)**: Can start after Foundational (Phase 2)
- **User Story 5 (P3)**: Can start after Foundational (Phase 2)

### Parallel Opportunities

- Creation tasks for all templates (T005, T007, T009, T011, T013) can run in parallel since they create distinct files in distinct locations.
- Validation scripts (T006, T008, T010, T014) can run in parallel.

---

## Parallel Example: Template Creation

```bash
# Generate templates in parallel:
Task: "Create bug_report.yml"
Task: "Create feature_request.yml"
Task: "Create config.yml"
Task: "Create PULL_REQUEST_TEMPLATE.md"
Task: "Create dependabot.yml"
```

---

## Implementation Strategy

### MVP First (User Stories 1 & 2 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1 (Bug report)
4. Complete Phase 4: User Story 2 (Feature request)
5. **STOP and VALIDATE**: Verify form-based templates syntax
6. Complete remaining templates incrementally.
