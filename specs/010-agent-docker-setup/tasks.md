# Tasks: Agent Docker Container Setup

**Input**: Design documents from `specs/010-agent-docker-setup/`

**Prerequisites**: plan.md (✅), spec.md (✅), research.md (✅), data-model.md (✅), contracts/ (✅)

**Tests**: Smoke test scripts are included as they are integral to the Docker CI/CD workflow (not optional testing).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Docker infrastructure**: `docker/`
- **CI/CD workflows**: `.github/workflows/`
- **Host-side scripts**: `scripts/`
- **Root configs**: `docker-compose.yml`, `docker-compose.test.yml`, `Makefile`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the foundational Docker files and project structure

- [x] T001 Create the container manifest file at docker/container-manifest.md with filesystem rules, install decision tree, and behavioral constraints per the architecture document
- [x] T002 [P] Create the .env.example template at docker/.env.example documenting LLM_API_URL (required), LLM_API_KEY, LLM_API_MODEL environment variables
- [x] T003 [P] Create the entrypoint script at docker/entrypoint.sh that validates LLM_API_URL, exports CONTAINER_MANIFEST, creates backup dirs, logs startup, and exec's the main process per contracts/entrypoint.md

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Production Dockerfile and compose configuration that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 Create the production Dockerfile at docker/Dockerfile based on Ubuntu 24.04 with Python 3.13, Node.js 22, uv, pipx, micromamba, git, common CLI tools, agent user with sudo, container manifest (444 perms), entrypoint, and the built Wright frontend + API
- [x] T005 Modify docker-compose.yml to add the 7 named volumes (wright_home, wright_local, wright_opt, wright_varlib, wright_varcache, wright_etc, wright_logs), expose ports 8000 and 5173, configure env_file, health check, and recovery mount per data-model.md
- [x] T006 [P] Create docker-compose.test.yml at project root for dedicated container testing/debugging with bind mounts for apps/ and packages/ alongside the named volumes
- [x] T007 [P] Create Makefile at project root with targets: docker-build, docker-test, docker-clean, docker-logs, docker-shell for developer convenience commands
- [x] T008 [P] Update .dockerignore to verify coverage for new files (docker/.env, state.db, .specify/, specs/, vault/)

**Checkpoint**: Foundation ready — Docker image builds and container starts with all volumes and environment variables configured

---

## Phase 3: User Story 1 — Dockerfile and Compose Build Validation (Priority: P1) 🎯 MVP

**Goal**: Docker image builds successfully from a clean checkout with all required components

**Independent Test**: Run `docker build -t wright-agent:test -f docker/Dockerfile .` and verify exit code 0, agent user exists, manifest exists at /container-manifest.md, entrypoint is executable

### Implementation for User Story 1

- [x] T009 [US1] Create scripts/docker-smoke-test.sh that builds the image, inspects it for agent user, container-manifest.md (444 perms), entrypoint.sh, and runs a basic `echo ok` test
- [x] T010 [US1] Run docker build locally and verify all acceptance scenarios from spec.md US1 pass via scripts/docker-smoke-test.sh

**Checkpoint**: Docker image builds and passes smoke tests independently

---

## Phase 4: User Story 2 — Volume Strategy and Persistence (Priority: P1)

**Goal**: Named volumes correctly persist data across container restarts while ephemeral paths reset

**Independent Test**: Start container, write files to /home/agent/ and /usr/bin/, restart, verify only volume-mounted file persists

### Implementation for User Story 2

- [x] T011 [US2] Verify docker-compose.yml volume definitions match the 7-volume model in data-model.md by starting the container and confirming all volumes appear in `docker volume ls`
- [x] T012 [US2] Test persistence by writing to /home/agent/test.txt (should persist) and /usr/bin/ephemeral-test (should reset) across a `docker compose restart`

**Checkpoint**: Volume persistence verified — data survives restarts, ephemeral paths self-heal

---

## Phase 5: User Story 3 — Environment Variable Injection (Priority: P1)

**Goal**: LLM API credentials are injected via .env file, never baked into the image, and available inside the container

**Independent Test**: Start with test .env, exec into container, verify all env vars present

### Implementation for User Story 3

- [x] T013 [US3] Test environment injection by creating a test .env from docker/.env.example, starting the container, and verifying LLM_API_URL, LLM_API_KEY, LLM_API_MODEL are available via `docker compose exec`
- [x] T014 [US3] Verify no secrets in image layers by running `docker history wright-agent:test` and confirming no API keys appear

**Checkpoint**: Environment injection verified — secrets stay out of the image, .env changes take effect on restart

---

## Phase 6: User Story 4 — Container Manifest and Agent Awareness (Priority: P2)

**Goal**: Container manifest is baked in as read-only, exported to CONTAINER_MANIFEST env var at startup

**Independent Test**: Start container, verify /container-manifest.md is readable (444), $CONTAINER_MANIFEST is non-empty

### Implementation for User Story 4

- [x] T015 [US4] Verify manifest integration by starting the container and confirming: `cat /container-manifest.md` returns content, `ls -la /container-manifest.md` shows 444 permissions, `echo $CONTAINER_MANIFEST` is non-empty

**Checkpoint**: Agent awareness infrastructure verified

---

## Phase 7: User Story 5 — CI/CD Pipeline Docker Build (Priority: P2)

**Goal**: GitHub Actions workflow builds, tests, and pushes Docker image on every push to main/dev

**Independent Test**: Push a commit to dev, verify the CI job runs, produces a tagged image, and pushes to Docker Hub

### Implementation for User Story 5

- [x] T016 [US5] Create .github/workflows/docker-build.yml with: checkout, buildx setup, Docker Hub login (DOCKERHUB_USERNAME, DOCKERHUB_TOKEN secrets), metadata-action for tags (<sha>, latest/dev), build-push-action with gha cache, and smoke test step per contracts/ci-docker-build.md
- [x] T017 [US5] Validate the workflow YAML syntax locally using `act` dry-run or manual review of the workflow structure against GitHub Actions schema

**Checkpoint**: CI/CD pipeline ready — Docker images built and pushed automatically on push

---

## Phase 8: User Story 6 — Backup and Restore Workflow (Priority: P2)

**Goal**: Host-side scripts create timestamped volume backups and restore specific volumes from backup

**Independent Test**: Run backup script, verify 7 .tar.gz archives, restore a single volume, verify data integrity

### Implementation for User Story 6

- [x] T018 [P] [US6] Create scripts/backup-volumes.sh that archives all 7 named wright_ volumes to /backups/wright-volumes/<timestamp>/ with 7-day retention pruning per architecture doc Section 6.1
- [x] T019 [P] [US6] Create scripts/restore-volume.sh that restores a single named volume from a timestamped backup archive per architecture doc Section 6.3

**Checkpoint**: Backup and restore scripts ready for host-side deployment

---

## Phase 9: User Story 7 — Recovery Runbook Validation (Priority: P2)

**Goal**: All 5 recovery scenarios from the architecture doc are documented as executable procedures

**Independent Test**: Simulate each failure scenario in a test environment and follow the documented recovery steps

### Implementation for User Story 7

- [x] T020 [US7] Add recovery validation instructions to scripts/docker-smoke-test.sh covering: Scenario A (restart self-healing), Scenario B (entrypoint bypass for /etc repair), and Scenario E (file restore from backup)

**Checkpoint**: Recovery procedures are documented and testable

---

## Phase 10: User Story 8 — Development Mode Isolation (Priority: P3)

**Goal**: Docker is NOT used during normal development; dedicated commands exist for explicit container testing

**Independent Test**: Verify npm run dev and uv run uvicorn work without Docker; verify make docker-test starts the container

### Implementation for User Story 8

- [x] T021 [US8] Verify existing dev workflows still work: run `npm run dev` and `PYTHONPATH=src uv run uvicorn api.main:app` without Docker and confirm identical behavior
- [x] T022 [US8] Test the docker-compose.test.yml and Makefile docker-test target: confirm the container builds, starts with all volumes, and stops cleanly without affecting the host dev environment

**Checkpoint**: Development isolation verified — Docker is opt-in for testing only

---

## Phase 11: User Story 9 — Health Check and Monitoring (Priority: P3)

**Goal**: Container health check verifies agent runtime status via docker compose ps

**Independent Test**: Start container, wait for start_period, verify docker compose ps shows "healthy"

### Implementation for User Story 9

- [x] T023 [US9] Verify health check by starting the container, waiting 30s (start_period), and confirming `docker compose ps` shows healthy status

**Checkpoint**: Health monitoring verified

---

## Phase 12: User Story 10 — Agent Change Logging (Priority: P3)

**Goal**: Change log at /var/log/agent-changes.log persists across restarts and is populated by the entrypoint

**Independent Test**: Write to change log, restart, verify entry persists

### Implementation for User Story 10

- [x] T024 [US10] Verify change logging by writing a test entry to /var/log/agent-changes.log, restarting the container, and confirming the entry persists
- [x] T025 [US10] Verify entrypoint startup logging by confirming /var/log/agent-startup.log contains a timestamped entry with LLM_API_URL after container start

**Checkpoint**: Change logging infrastructure verified

---

## Phase 13: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, cleanup, and final validation

- [x] T026 [P] Update docs/agent-docker-architecture.md with any deviations or decisions made during implementation (lean base vs heavy, Docker Hub choice, full-stack container)
- [x] T027 [P] Update README.md to document Docker setup, available Makefile targets, and link to the container manifest
- [x] T028 Run full end-to-end validation: build image, start container, verify all 7 volumes, test env injection, verify health check, run backup/restore cycle, verify smoke test passes
- [x] T029 Clean up any temporary test artifacts and ensure .gitignore covers docker-related generated files (.env, docker volume data)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Stories (Phase 3–12)**: All depend on Foundational phase completion
  - P1 stories (US1–3) can proceed in priority order or in parallel
  - P2 stories (US4–7) can start after P1 or in parallel with P1 if capacity allows
  - P3 stories (US8–10) can start after P2 or in parallel
- **Polish (Phase 13)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (Build Validation)**: Starts after Foundational — no other story dependencies
- **US2 (Volume Persistence)**: Starts after Foundational — no other story dependencies
- **US3 (Env Injection)**: Starts after Foundational — no other story dependencies
- **US4 (Container Manifest)**: Independent — can parallel with US1–3
- **US5 (CI/CD Pipeline)**: Depends on US1 (needs working Dockerfile) and T009 (smoke test)
- **US6 (Backup/Restore)**: Depends on US2 (needs working volumes)
- **US7 (Recovery Runbook)**: Depends on US6 (needs backup scripts)
- **US8 (Dev Mode Isolation)**: Independent — verifies existing workflows are unaffected
- **US9 (Health Check)**: Depends on US1 (needs working container)
- **US10 (Change Logging)**: Depends on US2 (needs working volumes for /var/log/)

### Within Each User Story

- Foundation must be complete before story tasks begin
- Smoke tests verify each story's acceptance scenarios
- Commit after each story completion

### Parallel Opportunities

- T002 and T003 can run in parallel (different files, no dependencies)
- T006, T007, T008 can run in parallel within Phase 2
- T018 and T019 can run in parallel (independent scripts)
- T026 and T027 can run in parallel (different doc files)
- US1, US2, US3 can all start in parallel after Foundation
- US4, US8 are fully independent and can run anytime after Foundation

---

## Parallel Example: Foundation Phase

```bash
# After T004 and T005 are complete, these can run in parallel:
Task: "T006 Create docker-compose.test.yml"
Task: "T007 Create Makefile with docker targets"
Task: "T008 Update .dockerignore"
```

## Parallel Example: P1 User Stories

```bash
# After Foundation, all P1 stories can start simultaneously:
Task: "T009-T010 User Story 1: Build Validation"
Task: "T011-T012 User Story 2: Volume Persistence"
Task: "T013-T014 User Story 3: Env Injection"
```

---

## Implementation Strategy

### MVP First (User Stories 1–3 Only)

1. Complete Phase 1: Setup (T001–T003)
2. Complete Phase 2: Foundational (T004–T008)
3. Complete Phase 3: US1 — Build Validation (T009–T010)
4. **STOP and VALIDATE**: Image builds, smoke test passes
5. Complete Phases 4–5: US2–3 — Volumes and Env
6. **STOP and VALIDATE**: Container runs with persistence and credentials

### Incremental Delivery

1. Setup + Foundational → Image builds ✅
2. US1–3 → Container works end-to-end (MVP!) ✅
3. US4–5 → Agent awareness + CI/CD automation ✅
4. US6–7 → Backup/restore + recovery runbook ✅
5. US8–10 → Dev isolation + monitoring + logging ✅
6. Polish → Docs updated, full validation ✅

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Docker is NOT used during normal development — all docker commands are explicit opt-in
- Total: 29 tasks across 13 phases (1 setup + 1 foundation + 10 user stories + 1 polish)
