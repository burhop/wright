# Tasks: Community Release Readiness

**Input**: Design documents from `/specs/041-community-release-readiness/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/public-release-artifacts.md, quickstart.md

**Tests**: This feature is primarily documentation, release metadata, and workflow readiness. Validation tasks are included where they prove public install, package, container, docs, and merge-gate readiness.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Inventory current release surfaces and create the documentation structure needed by later stories.

- [X] T001 Inventory current install, package, container, funding, and visibility surfaces in README.md, docs/, docker/, .github/, pyproject.toml, packages/*/pyproject.toml, and hermes-plugin-wright/README.md
- [X] T002 [P] Create release-readiness docs index in docs/release/community-release-readiness.md
- [X] T003 [P] Create user-install docs directory structure or index entries under docs/getting-started/
- [X] T004 [P] Create community docs directory structure or index entries under docs/community/
- [X] T005 Verify docs navigation configuration includes any new docs paths in mkdocs.yml

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Resolve naming, channel, and messaging decisions that all user stories depend on.

**CRITICAL**: No user-story implementation should begin until these decisions are documented.

- [X] T006 Document `wright-engineering` as the single alpha PyPI package and explicitly defer component PyPI packages in docs/release/python-packaging.md
- [X] T007 Document `burhop/wright` and `ghcr.io/burhop/wright` as alpha container image names, with tag and platform-support policy, in docs/release/container-publishing.md
- [X] T008 Document the canonical local-first, public-alpha, BYO-AI, and `wright@makerengineer.com` contact messaging rules in docs/release/community-release-readiness.md
- [X] T009 Document the supported use-case matrix in docs/getting-started/install-matrix.md
- [X] T010 Cross-check public listing contract requirements from specs/041-community-release-readiness/contracts/public-release-artifacts.md against existing README.md and docker/DOCKER_HUB_README.md

**Checkpoint**: Foundation ready. Install, visibility, and funding stories can proceed independently.

---

## Phase 3: User Story 1 - Install Wright for the Right Use Case (Priority: P1) MVP

**Goal**: A prospective user can identify their use case and complete the recommended Wright install path.

**Independent Test**: Choose each use case from docs/getting-started/install-matrix.md and verify it has prerequisites, recommended path, verification step, and limitations.

### Implementation for User Story 1

- [X] T011 [US1] Update Docker quickstart language in README.md to use `burhop/wright` and distinguish published-image usage from source checkout builds
- [X] T012 [US1] Add no-build published-image quickstart guidance to docs/getting-started/quickstart-docker.md
- [X] T013 [P] [US1] Add Windows 11 install guidance in docs/getting-started/windows-11.md
- [X] T014 [P] [US1] Add Linux workstation and Dell GB10-class install guidance in docs/getting-started/linux-gb10.md
- [X] T015 [P] [US1] Add Hermes Desktop integration guidance in docs/getting-started/hermes-desktop.md
- [X] T016 [P] [US1] Add Python developer package guidance in docs/getting-started/python-packages.md
- [X] T017 [P] [US1] Add MCP contributor install and validation entry point in docs/getting-started/mcp-contributors.md
- [X] T018 [P] [US1] Add enterprise evaluator install and security entry point in docs/getting-started/enterprise-evaluation.md
- [X] T019 [US1] Update docker/DOCKER_HUB_README.md with `burhop/wright`, platform, verification, contact, and BYO-AI expectations
- [X] T020 [US1] Update docker-compose.minimal.yml and docker-compose.yml comments or examples if needed to support published-image use without local builds
- [X] T021 [US1] Update .github/workflows/release.yml and .github/workflows/docker-build.yml from `wright-agent` public image names to `wright`, keeping multi-platform publishing deferred unless validation proves it safe
- [X] T022 [US1] Update .github/workflows/publish-python-packages.yml to publish only the root `wright-engineering` alpha package via Trusted Publishing and remove alpha component package publication paths
- [X] T023 [US1] Validate install docs against specs/041-community-release-readiness/quickstart.md sections 1 through 4

**Checkpoint**: User Story 1 should be fully reviewable as the MVP install/distribution readiness increment.

---

## Phase 4: User Story 2 - Discover and Evaluate Wright Publicly (Priority: P2)

**Goal**: New visitors can find Wright, understand its value, and see credible project activity.

**Independent Test**: Start from README.md, package/container listing copy, or docs landing pages and explain Wright's audience, status, install path, contribution path, and support path within five minutes.

### Implementation for User Story 2

- [X] T024 [US2] Refresh first-screen README.md positioning, primary action, screenshots, install pointer, and public-alpha status
- [X] T025 [P] [US2] Add docs/community/visibility-checklist.md with repository metadata, docs, demos, release notes, community, and outreach checklist
- [X] T026 [P] [US2] Add docs/community/demo-gallery.md with planned flagship demo slots and acceptance criteria
- [X] T027 [P] [US2] Add docs/community/launch-indicators.md with at least five visibility indicators and review cadence
- [X] T028 [US2] Update docs index or landing content to route new users to install, contribution, security, and sponsorship paths
- [X] T029 [US2] Update package/container listing copy references for `wright-engineering`, `burhop/wright`, and `ghcr.io/burhop/wright` so public registry pages route to canonical docs, issues, security, releases, funding links, and `wright@makerengineer.com`
- [X] T030 [US2] Add or update GitHub topic recommendations and ecosystem-listing checklist in docs/community/visibility-checklist.md
- [X] T031 [US2] Validate visibility surfaces against specs/041-community-release-readiness/quickstart.md section 5

**Checkpoint**: User Story 2 should be independently reviewable as the visibility/public-discovery increment.

---

## Phase 5: User Story 3 - Fund Wright Application Work (Priority: P3)

**Goal**: Supporters, sponsors, customers, and partners can understand how to fund Wright and what funding supports.

**Independent Test**: Starting from README.md or docs, identify active sponsorship, planned funding structures, commercial support routes, and partner outreach materials.

### Implementation for User Story 3

- [X] T032 [US3] Update README.md sponsorship section to link to detailed funding and support guidance
- [X] T033 [P] [US3] Add docs/community/funding.md with active sponsorship, funding uses, planned structures, and boundaries
- [X] T034 [P] [US3] Add docs/community/commercial-support.md with support and integration engagement types
- [X] T035 [P] [US3] Add docs/community/partner-brief.md covering NVIDIA, Dell, hardware validation, credits, and co-marketing outreach
- [X] T036 [US3] Review .github/FUNDING.yml and document any needed organization, fiscal host, or sponsor profile follow-up in docs/community/funding.md
- [X] T037 [US3] Validate funding and partner materials against specs/041-community-release-readiness/quickstart.md sections 6 and 7

**Checkpoint**: User Story 3 should be independently reviewable as the funding/partner-readiness increment.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Validate public materials, docs build, release gates, and Spec Kit completion.

- [X] T038 [P] Run markdown/link review for changed README.md and docs files
- [X] T039 [P] Run package metadata validation for the root `wright-engineering` package using scripts/build-python-distributions.sh in dry-run or targeted mode
- [X] T040 [P] Run Docker workflow/static tests or smoke validation relevant to the `burhop/wright` and `ghcr.io/burhop/wright` release-name changes
- [X] T041 Run mkdocs build --strict for documentation navigation and link validation
- [X] T042 Run scripts/check-dev-merge.sh before merging to dev, or document the exact local host limitation preventing the gate
- [X] T043 Update specs/041-community-release-readiness/quickstart.md with any final validation notes discovered during implementation
- [X] T044 Mark completed tasks in specs/041-community-release-readiness/tasks.md and summarize release-readiness decisions in specs/041-community-release-readiness/plan.md if decisions changed

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on Setup completion and blocks all user stories.
- **User Story 1 (Phase 3)**: Depends on Foundational phase. MVP scope.
- **User Story 2 (Phase 4)**: Depends on Foundational phase. Can proceed after or alongside US1 if file conflicts are managed.
- **User Story 3 (Phase 5)**: Depends on Foundational phase. Can proceed after or alongside US1/US2 if file conflicts are managed.
- **Polish (Phase 6)**: Depends on all implemented story phases.

### User Story Dependencies

- **US1 Install Wright for the Right Use Case**: No dependency on US2 or US3 after foundation.
- **US2 Discover and Evaluate Wright Publicly**: Depends on foundational messaging and may reference US1 install docs.
- **US3 Fund Wright Application Work**: Depends on foundational messaging and may share README links with US2.

### Parallel Opportunities

- T002, T003, and T004 can run in parallel.
- T013 through T018 can run in parallel because they create separate install-guide files.
- T025, T026, and T027 can run in parallel.
- T033, T034, and T035 can run in parallel.
- T038, T039, and T040 can run in parallel if their target files do not overlap.

---

## Parallel Example: User Story 1

```text
Task: "Add Windows 11 install guidance in docs/getting-started/windows-11.md"
Task: "Add Linux workstation and Dell GB10-class install guidance in docs/getting-started/linux-gb10.md"
Task: "Add Hermes Desktop integration guidance in docs/getting-started/hermes-desktop.md"
Task: "Add Python developer package guidance in docs/getting-started/python-packages.md"
Task: "Add MCP contributor install and validation entry point in docs/getting-started/mcp-contributors.md"
Task: "Add enterprise evaluator install and security entry point in docs/getting-started/enterprise-evaluation.md"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 setup inventory.
2. Complete Phase 2 naming/channel/messaging decisions.
3. Complete Phase 3 install and distribution readiness, including `wright-engineering` and `burhop/wright` alpha wiring.
4. Stop and validate every use case in the install matrix.
5. Review before changing broader visibility or funding surfaces.

### Incremental Delivery

1. Deliver US1 so users can install and verify Wright.
2. Deliver US2 so people can find and evaluate Wright.
3. Deliver US3 so sponsors, customers, and partners can support Wright.
4. Run polish and merge gates before merging to `dev`.

### Manual Gate

Per the project constitution, implementation edits should begin only after human review of this plan and task list.
