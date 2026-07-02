# Tasks: Hermes Plugin Mirror and PyPI Packages

**Input**: Design documents from `/specs/039-hermes-plugin-mirror-pypi/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/](contracts/), [quickstart.md](quickstart.md)

**Tests**: Included because the feature explicitly requires package publication checks, mirror validation checks, and Hermes install/update/remove lifecycle validation.

**Organization**: Tasks are grouped by user story so each story can be implemented and tested independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it touches different files and has no dependency on incomplete tasks.
- **[Story]**: User-story label for traceability: `[US1]`, `[US2]`, `[US3]`.
- Every task includes an exact file path.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the shared scaffolding needed by release, mirror, and lifecycle work.

- [X] T001 Create release test helper package in `tests/release/conftest.py`
- [X] T002 [P] Create mirror fixture README placeholder in `tests/fixtures/hermes_plugin_mirror/README.md`
- [X] T003 [P] Create package build helper scaffold in `scripts/build-python-distributions.sh`
- [X] T004 [P] Create mirror sync helper scaffold in `scripts/sync-hermes-plugin-mirror.sh`
- [X] T005 [P] Create mirror validation helper scaffold in `scripts/validate-hermes-plugin-mirror.sh`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared release-engineering primitives that must exist before any user story can be completed.

**CRITICAL**: No user story work should begin until these tasks are complete.

- [X] T006 Add subprocess, temp repository, and artifact inspection utilities in `tests/release/conftest.py`
- [X] T007 [P] Add executable and help-output contract tests for release scripts in `tests/test_release_engineering_scripts.py`
- [X] T008 [P] Add minimal mirror fixture manifest and plugin files in `tests/fixtures/hermes_plugin_mirror/plugin.yaml`
- [X] T009 Add mirror/package validation target stubs in `Makefile`
- [X] T010 Document the new release-engineering script entry points in `scripts/README.md`

**Checkpoint**: Release script scaffolding, fixtures, and shared test utilities are ready.

---

## Phase 3: User Story 1 - Install and Update Wright from the Mirror (Priority: P1) MVP

**Goal**: A Hermes user can install, update, remove, and reinstall Wright from a standalone mirror repository root.

**Independent Test**: In a fresh Hermes home, install the plugin from the mirror root, confirm it is listed and command discovery works, update it successfully, remove it, and reinstall it.

### Tests for User Story 1

- [X] T011 [P] [US1] Add mirror sync allowlist and provenance tests in `tests/test_hermes_plugin_mirror_sync.py`
- [X] T012 [P] [US1] Add mirror content, prohibited path, and dependency policy tests in `tests/test_hermes_plugin_mirror_validation.py`
- [X] T013 [P] [US1] Add root-level Hermes lifecycle identifier tests in `tests/test_hermes_plugin_lifecycle_contract.py`
- [X] T014 [P] [US1] Add Docker lifecycle script contract tests for root mirror update behavior in `tests/test_hermes_plugin_lifecycle_contract.py`

### Implementation for User Story 1

- [X] T015 [US1] Implement allowlisted dry-run and export behavior in `scripts/sync-hermes-plugin-mirror.sh`
- [X] T016 [US1] Implement source revision and package provenance generation in `scripts/sync-hermes-plugin-mirror.sh`
- [X] T017 [US1] Implement required root file and prohibited path checks in `scripts/validate-hermes-plugin-mirror.sh`
- [X] T018 [US1] Implement stable and development dependency policy checks in `scripts/validate-hermes-plugin-mirror.sh`
- [X] T019 [US1] Update lifecycle argument parsing for root mirror installs in `scripts/hermes-plugin-lifecycle-common.sh`
- [X] T020 [US1] Update install lifecycle script to support root mirror identifiers in `scripts/test-hermes-plugin-install.sh`
- [X] T021 [US1] Update update lifecycle script to require `.git` metadata for mirror installs in `scripts/test-hermes-plugin-update.sh`
- [X] T022 [US1] Update uninstall lifecycle script to reinstall from root mirror identifiers in `scripts/test-hermes-plugin-uninstall.sh`
- [X] T023 [US1] Add root-mirror lifecycle targets in `Makefile`
- [X] T024 [US1] Add mirror sync and lifecycle validation workflow in `.github/workflows/sync-hermes-plugin-mirror.yml`
- [X] T025 [US1] Run US1 validation commands and record results in `docs/release/hermes-plugin-mirror.md`

**Checkpoint**: User Story 1 is functional and testable as the MVP.

---

## Phase 4: User Story 2 - Publish Wright Dependencies for Clean Installs (Priority: P2)

**Goal**: Wright maintainers can publish the plugin dependencies as clean Python packages before stable mirror releases.

**Independent Test**: In an environment with no Wright monorepo checkout, install the built `wright-core` and `wright-tool-registry` artifacts, import `core` and `tool_registry`, and confirm the mirror release gate blocks missing or workspace-only dependencies.

### Tests for User Story 2

- [X] T026 [P] [US2] Add package metadata contract tests for `wright-core` and `wright-tool-registry` in `tests/test_python_package_metadata.py`
- [X] T027 [P] [US2] Add distribution build and clean-install tests for the package helper in `tests/test_python_package_distribution_build.py`
- [X] T028 [P] [US2] Add publish workflow structure tests for Trusted Publishing in `tests/test_publish_python_packages_workflow.py`
- [X] T029 [P] [US2] Add plugin dependency source policy tests in `hermes-plugin-wright/tests/test_plugin_metadata.py`

### Implementation for User Story 2

- [X] T030 [US2] Add PyPI-ready metadata and project URLs to `packages/core/pyproject.toml`
- [X] T031 [US2] Add package index README for `wright-core` in `packages/core/README.md`
- [X] T032 [US2] Add PyPI-ready metadata and versioned `wright-core` dependency to `packages/tool_registry/pyproject.toml`
- [X] T033 [US2] Add package index README for `wright-tool-registry` in `packages/tool_registry/README.md`
- [X] T034 [US2] Update stable dependency declarations for mirror builds in `hermes-plugin-wright/pyproject.toml`
- [X] T035 [US2] Implement source distribution, wheel, metadata, artifact inspection, and clean-install checks in `scripts/build-python-distributions.sh`
- [X] T036 [US2] Add package publication workflow with TestPyPI and PyPI OIDC environments in `.github/workflows/publish-python-packages.yml`
- [X] T037 [US2] Extend Python quality workflow to run package build dry-runs in `.github/workflows/python-quality.yml`
- [X] T038 [US2] Document TestPyPI, PyPI, package tag order, and manual approval setup in `docs/release/hermes-plugin-mirror.md`
- [X] T039 [US2] Run US2 package build and clean-install validation and record results in `docs/release/hermes-plugin-mirror.md`

**Checkpoint**: Package publication prerequisites and clean-install validation are independently complete.

---

## Phase 5: User Story 3 - Navigate from the Mirror to the Main Wright Project (Priority: P3)

**Goal**: A user who lands on the mirror repository can understand what it is, install/update/remove Wright, migrate from the old monorepo subdirectory path, and reach the main Wright project.

**Independent Test**: Review the mirror README from a fresh checkout and confirm a user can find install, update, remove, migration, source provenance, package, support, docs, issue, and release links in under 60 seconds.

### Tests for User Story 3

- [X] T040 [P] [US3] Add mirror README required-section and required-link tests in `tests/test_hermes_plugin_mirror_readme.py`
- [X] T041 [P] [US3] Add provenance documentation tests in `tests/test_hermes_plugin_mirror_provenance.py`
- [X] T042 [P] [US3] Add release runbook documentation tests in `tests/test_hermes_plugin_mirror_docs.py`

### Implementation for User Story 3

- [X] T043 [US3] Rewrite the plugin README as a mirror-ready customer landing page in `hermes-plugin-wright/README.md`
- [X] T044 [US3] Add source revision and dependency provenance template in `hermes-plugin-wright/PROVENANCE.md`
- [X] T045 [US3] Add migration, channel, release, and support runbook content in `docs/release/hermes-plugin-mirror.md`
- [X] T046 [US3] Add the release runbook to the documentation navigation in `mkdocs.yml`
- [X] T047 [US3] Add README section and link validation to `scripts/validate-hermes-plugin-mirror.sh`
- [X] T048 [US3] Add README/provenance validation summary output to `.github/workflows/sync-hermes-plugin-mirror.yml`
- [X] T049 [US3] Run US3 documentation validation and record results in `docs/release/hermes-plugin-mirror.md`

**Checkpoint**: Mirror README and release docs are customer-testable independently.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, cleanup, and release-readiness hardening across all stories.

- [X] T050 [P] Update lifecycle script documentation for mirror-root usage in `scripts/README.md`
- [X] T051 [P] Update release workflow notes for package-scoped tags in `docs/release/hermes-plugin-mirror.md`
- [X] T052 Run Ruff, package tests, plugin tests, and release-engineering tests and record results in `docs/release/hermes-plugin-mirror.md`
- [ ] T053 Run Docker-backed Hermes install/update/remove lifecycle validation for the development mirror channel and record results in `docs/release/hermes-plugin-mirror.md`
- [X] T054 Run mirror validation against the stable channel and record any blocked-release findings in `docs/release/hermes-plugin-mirror.md`
- [X] T055 Audit generated artifacts for caches, credentials, personal paths, and workspace-only dependencies in `scripts/validate-hermes-plugin-mirror.sh`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on Phase 1 and blocks all user stories.
- **User Story 1 (Phase 3)**: Depends on Phase 2; MVP scope.
- **User Story 2 (Phase 4)**: Depends on Phase 2; can proceed in parallel with US1 after shared scaffolding, but stable plugin release depends on package availability.
- **User Story 3 (Phase 5)**: Depends on Phase 2; can proceed in parallel with US1 and US2, then integrate final command examples after US1/US2 decisions settle.
- **Polish (Phase 6)**: Depends on all desired user stories.

### User Story Dependencies

- **US1**: Independent after Phase 2 and should be delivered first as MVP.
- **US2**: Independent after Phase 2 for package build/publication work; stable mirror release promotion depends on US2 completion.
- **US3**: Independent after Phase 2 for README/runbook content; final link and command validation depends on US1 and US2 outputs.

### Implementation Order Within Stories

- Write validation tests before changing implementation files.
- Create script behavior before wiring workflows to those scripts.
- Complete local validations before enabling CI release gates.
- Validate each story at its checkpoint before moving to the next priority if working sequentially.

---

## Parallel Opportunities

- T002, T003, T004, and T005 can run in parallel after T001 is understood.
- T007 and T008 can run in parallel after T006.
- US1 tests T011, T012, T013, and T014 can run in parallel.
- US2 tests T026, T027, T028, and T029 can run in parallel.
- US3 tests T040, T041, and T042 can run in parallel.
- US2 package metadata work T030/T031 and T032/T033 can be split by package.
- US3 documentation work T043/T044 and T045/T046 can be split once required links are agreed.

---

## Parallel Example: User Story 1

```text
Task: "Add mirror sync allowlist and provenance tests in tests/test_hermes_plugin_mirror_sync.py"
Task: "Add mirror content, prohibited path, and dependency policy tests in tests/test_hermes_plugin_mirror_validation.py"
Task: "Add root-level Hermes lifecycle identifier tests in tests/test_hermes_plugin_lifecycle_contract.py"
Task: "Add Docker lifecycle script contract tests for root mirror update behavior in tests/test_hermes_plugin_lifecycle_contract.py"
```

## Parallel Example: User Story 2

```text
Task: "Add package metadata contract tests for wright-core and wright-tool-registry in tests/test_python_package_metadata.py"
Task: "Add distribution build and clean-install tests for the package helper in tests/test_python_package_distribution_build.py"
Task: "Add publish workflow structure tests for Trusted Publishing in tests/test_publish_python_packages_workflow.py"
Task: "Add plugin dependency source policy tests in hermes-plugin-wright/tests/test_plugin_metadata.py"
```

## Parallel Example: User Story 3

```text
Task: "Add mirror README required-section and required-link tests in tests/test_hermes_plugin_mirror_readme.py"
Task: "Add provenance documentation tests in tests/test_hermes_plugin_mirror_provenance.py"
Task: "Add release runbook documentation tests in tests/test_hermes_plugin_mirror_docs.py"
```

---

## Implementation Strategy

### MVP First: User Story 1 Only

1. Complete Phase 1 setup.
2. Complete Phase 2 foundational scaffolding.
3. Complete Phase 3 User Story 1 tasks.
4. Stop and validate install, update, remove, and reinstall from a root-level mirror fixture or test mirror.
5. Use the result to confirm the Hermes lifecycle problem is solved before package publication or docs polish.

### Incremental Delivery

1. Deliver US1 to prove the mirror shape fixes Hermes update behavior.
2. Deliver US2 to make stable mirror releases clean-installable without monorepo workspace paths.
3. Deliver US3 to make the mirror usable by customer testers without extra guidance.
4. Run Phase 6 gates before announcing the mirror path for broader testing.

### Parallel Team Strategy

1. One person owns scripts and Hermes lifecycle validation from US1.
2. One person owns package metadata, build helper, and PyPI workflow from US2.
3. One person owns README, runbook, and link/provenance validation from US3.
4. Integrate through the shared `scripts/validate-hermes-plugin-mirror.sh` and CI workflows after each story passes independently.

## Notes

- [P] tasks are intentionally limited to different files or independent test files.
- Story labels map directly to the three prioritized user stories in `spec.md`.
- Keep the mirror as generated output from the main repo; do not develop features directly in the mirror.
- Do not publish to PyPI until TestPyPI, clean install, and lifecycle validation have passed.
