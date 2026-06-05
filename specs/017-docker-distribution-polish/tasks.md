# Tasks: Docker Distribution Polish

**Input**: Design documents from `/specs/017-docker-distribution-polish/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project verification and clean environment checks

- [x] T001 Verify active git branch is `017-docker-distribution-polish` and workspace is clean
- [x] T002 Verify that `specs/017-docker-distribution-polish/spec.md` and `plan.md` are completed

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Verify local Docker environment before making changes

- [x] T003 Verify local Docker daemon is active on the host
- [x] T004 [P] Initialize `docker-compose.minimal.yml` structure at project root

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Self-Documenting OCI Metadata & Build-arg injection (Priority: P1) 🎯 MVP

**Goal**: Add OCI metadata annotations to Dockerfile and pass build-args in GHA.

**Independent Test**: Build locally with build args and inspect image configuration using `docker inspect` for OCI labels.

### Implementation for User Story 1

- [x] T005 [P] [US1] Add OCI metadata `LABEL` declarations to `docker/Dockerfile`
- [x] T006 [US1] Update `.github/workflows/docker-build.yml` to pass VERSION, REVISION, and CREATED build arguments

**Checkpoint**: Docker image OCI labels are successfully integrated.

---

## Phase 4: User Story 2 - Docker Hub Profile & Automatic README Sync (Priority: P1)

**Goal**: Create a profile description for Docker Hub and automate its synchronization.

**Independent Test**: Verify `docker/DOCKER_HUB_README.md` exists and verify the release workflow config holds the description sync step.

### Implementation for User Story 2

- [x] T007 [P] [US2] Create `docker/DOCKER_HUB_README.md` containing compose commands, variables, ports, and volumes reference tables
- [x] T008 [US2] Update `.github/workflows/release.yml` with `peter-evans/dockerhub-description@v4` action step

**Checkpoint**: Docker Hub profile README and auto-sync action are configured.

---

## Phase 5: User Story 3 - Production & Minimal Compose Variants (Priority: P2)

**Goal**: Provide production and lightweight compose profiles.

**Independent Test**: Verify minimal stack launches correctly without Jaeger service container.

### Implementation for User Story 3

- [x] T009 [P] [US3] Create `docker-compose.minimal.yml` in project root declaring API and Web service configurations
- [x] T010 [US3] Add inline documentation comments inside `docker-compose.minimal.yml` and `docker-compose.yml`

**Checkpoint**: Deploy profiles are configured.

---

## Phase 6: User Story 4 - Pre-Push Scanning & Multi-Architecture Readiness (Priority: P3)

**Goal**: Set up non-blocking vulnerability scans in CI and prepare buildx ARM64 build arguments.

**Independent Test**: Verify docker-build CI run includes setup-buildx-action, Trivy logs, and commented platforms parameters.

### Implementation for User Story 4

- [x] T011 [P] [US4] Update `.github/workflows/docker-build.yml` to include a non-blocking `aquasecurity/trivy-action@master` step
- [x] T012 [US4] Configure setup-buildx-action and add commented platforms settings in `.github/workflows/docker-build.yml`

**Checkpoint**: Security scans and multi-arch setup are prepared.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Cleanup and validation tasks

- [x] T013 [P] Add Docker Pulls badge to root `README.md`
- [x] T014 Run local build validation using `specs/017-docker-distribution-polish/quickstart.md` procedures
- [x] T015 Verify no application files have been modified and clean up workspace

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phases 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2)
- **User Story 2 (P1)**: Can start after Foundational (Phase 2)
- **User Story 3 (P2)**: Can start after Foundational (Phase 2)
- **User Story 4 (P3)**: Can start after Foundational (Phase 2)

### Parallel Opportunities

- Verification of Docker daemon (T003) and initializing compose minimal (T004) can run in parallel.
- Dockerfile OCI labels (T005), Docker Hub README (T007), minimal compose setup (T009), and pulls badge (T013) can be created in parallel since they touch different files.

---

## Parallel Example: User Story 1

```bash
# Developer A: Add Dockerfile labels
Task: "Add OCI metadata LABEL declarations to docker/Dockerfile"

# Developer B: Update CI build parameters
Task: "Update .github/workflows/docker-build.yml to pass build arguments"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Run local build test and inspect OCI labels
5. Commit and release if verified

### Incremental Delivery

1. Complete Setup + Foundational
2. Add User Story 1 (OCI Labels) → Test independently → Deploy (MVP)
3. Add User Story 2 (Docker Hub README Sync) → Test independently
4. Add User Story 3 (Minimal Compose variant) → Test independently
5. Add User Story 4 (Security Scans & Multi-Arch prep) → Test independently
