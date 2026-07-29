# Tasks: Native Agent-Manager Installation

**Input**: Design documents from `/specs/050-native-hermes-install/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/](contracts/), [quickstart.md](quickstart.md)

**Tests**: Mandatory. Every story lists failing contract/integration tests before
the corresponding implementation work. No native acceptance skip is permitted.

**Organization**: Tasks are grouped by independently testable user story and
carry requirement IDs for complete Spec Kit coverage.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it changes different files and has no
  dependency on an incomplete task.
- **[USn]**: Maps the task to the numbered user story in `spec.md`.
- Every task includes an exact repository path.

## Phase 1: Setup and Spec Kit Portability

**Purpose**: Establish reliable cross-platform tooling and the native-runtime
test/build skeleton before feature behavior.

- [X] T001 Add LF checkout rules for Bash/Spec Kit scripts and Windows regression coverage in `.gitattributes` and `tests/test_speckit_script_portability.py` (Research Decision 12)
- [X] T002 Fix Windows Python interpreter probing in `.specify/extensions/agent-context/scripts/powershell/update-agent-context.ps1` and add tests in `tests/test_speckit_agent_context_update.py` (Research Decision 12)
- [X] T003 Create the native runtime package/test directory skeleton in `hermes-plugin-wright/`, `src/wright_engineering/runtime/`, `src/wright_engineering/static/`, and `tests/native_runtime/`
- [X] T004 [P] Add native candidate build/test command entry points in `scripts/build-native-runtime.py` and `scripts/test-native-hermes-install.py` with explicit not-yet-implemented failures
- [X] T005 [P] Add candidate output/cache patterns without broad user-data ignores in `.gitignore` and `.dockerignore`

---

## Phase 2: Foundational Runtime Contracts

**Purpose**: Define and implement shared artifact, path, compatibility, state,
process, and redaction primitives. This phase blocks every user story.

### Tests first

- [X] T006 [P] Add application wheel content, base-import isolation, private-distribution exclusion, and packaged-resource tests in `tests/native_runtime/test_package_contents.py` (FR-004, FR-025, FR-027-FR-030, SC-010)
- [X] T007 [P] Add contained Windows/POSIX `WRIGHT_HOME`, manager-state independence, runtime/data separation, symlink, root, and external-workspace path tests in `tests/native_runtime/test_layout.py` (FR-021-FR-024, FR-046, SC-008)
- [X] T008 [P] Add manifest schema, atomic write, corrupt snapshot, lock contention, transition, and interrupted-operation tests in `tests/native_runtime/test_state.py` (FR-007, FR-008, FR-014-FR-016)
- [X] T009 [P] Add manager-adapter/runtime/protocol/Python/platform/data-schema compatibility accept/reject tests in `tests/native_runtime/test_compatibility.py` (FR-017-FR-020, FR-028, FR-035, FR-046-FR-048, SC-009)
- [X] T010 [P] Add exact artifact/version/hash/channel, local wheelhouse, runtime-extra isolation, and forbidden source dependency tests in `tests/native_runtime/test_artifacts.py` (FR-002-FR-005, FR-029-FR-032)
- [X] T011 [P] Add PID reuse, port collision, executable containment, challenge mismatch, graceful stop, and unrelated-process protection tests in `tests/native_runtime/test_process.py` (FR-007, FR-008, FR-014-FR-016, SC-004)
- [X] T012 [P] Add secret/log/result redaction and bounded diagnostic payload tests in `tests/native_runtime/test_security.py` (FR-025, FR-026, SC-010)

### Implementation

- [X] T013 Implement lifecycle enums, runtime/operation/process/result models, schema validation, and stable error codes in `src/wright_engineering/runtime/models.py` (FR-009, FR-014-FR-017)
- [X] T014 Implement canonical manager-neutral `WRIGHT_HOME` layout, legacy-state migration, and owned-data scope resolution in `src/wright_engineering/runtime/layout.py` (FR-021-FR-024, FR-046)
- [X] T015 Implement atomic JSON manifest persistence, bounded cross-process locking, recovery snapshots, and transition validation in `src/wright_engineering/runtime/state.py` (FR-014-FR-016)
- [X] T016 Add manager-neutral runtime compatibility metadata plus adapter-protocol fail-closed checks in `src/wright_engineering/compatibility.json`, `src/wright_engineering/runtime/compatibility.py`, and adapter-specific compatibility modules (FR-017, FR-028, FR-035, FR-046-FR-048)
- [X] T017 Implement exact-version artifact resolution, hash verification, channel policy, isolated environment creation, and runtime-extra install in `src/wright_engineering/runtime/artifacts.py` and `src/wright_engineering/runtime/installer.py` (FR-002-FR-005, FR-029-FR-032)
- [X] T018 Implement challenged process launch/probe/identity/stop primitives with structured redaction in `src/wright_engineering/runtime/process.py` and `src/wright_engineering/runtime/diagnostics.py` (FR-007-FR-010, FR-025, FR-026)

**Checkpoint**: Foundational contracts pass without importing application runtime
dependencies into the test Hermes process.

---

## Phase 3: User Story 1 - Install and Start Wright from Hermes (Priority: P1) MVP

**Goal**: Install the public plugin and automatically start the packaged isolated
runtime/UI without repository or forbidden tools.

**Independent Test**: The clean contract in `clean-install-contract.md` succeeds
through first healthy UI after real Hermes Git adapter installation; the
post-adapter Wright runtime phase has no Git/Docker/Node/source access.

### Tests first

- [X] T019 [P] [US1] Add real Hermes Git-plugin discovery, stdlib-only adapter-import, and runtime-dependency absence tests in `tests/native_runtime/test_hermes_entrypoint.py`, `hermes-plugin-wright/tests/test_plugin_metadata.py`, and `hermes-plugin-wright/tests/test_bootstrap.py` (FR-001, FR-002, FR-006, SC-001)
- [X] T020 [P] [US1] Add packaged API/static UI/catalog/database bootstrap tests in `tests/native_runtime/test_server.py` (FR-004, FR-005, FR-011-FR-013)
- [X] T021 [P] [US1] Add start idempotency, automatic install, failed install, health challenge, and actionable result tests in `tests/native_runtime/test_lifecycle_start.py` (FR-002-FR-007, FR-012, FR-016)
- [X] T022 [P] [US1] Add Hermes `/wright start` adapter projection and bootstrap tests with no runtime repo detection/build calls in `tests/native_runtime/test_commands_start.py` and `hermes-plugin-wright/tests/test_bootstrap.py` (FR-003, FR-005, FR-006)
- [X] T023 [US1] Add subprocess-audited clean first-install/start integration test in `tests/native_runtime/test_clean_install.py` that uses real Hermes Git installation, then removes Git and forbids Docker, Node/npm, source checkout, `WRIGHT_REPO_DIR`, and preinstalled Wright during Wright bootstrap/start (FR-031-FR-033, SC-001-SC-003)

### Implementation

- [X] T024 [US1] Keep root metadata as the complete managed Wright runtime with a `runtime` extra, bundled modules/resources, and no requirement that Hermes import runtime dependencies in `pyproject.toml` (FR-001, FR-004, FR-027-FR-030)
- [X] T025 [US1] Implement the release-only frontend build/copy/manifest and application wheel assembly in `scripts/build-native-runtime.py` and `pyproject.toml` (FR-004, FR-005, FR-029)
- [X] T026 [US1] Implement packaged data/static/catalog bootstrap before API import in `src/wright_engineering/runtime/server.py`, `apps/api/src/api/config.py`, and `apps/api/src/api/main.py` (FR-004, FR-005, FR-011-FR-013)
- [X] T027 [US1] Implement a stdlib-only Hermes Git plugin bootstrap and thin `/wright` dispatcher in `hermes-plugin-wright/bootstrap.py`, `hermes-plugin-wright/__init__.py`, and `hermes-plugin-wright/commands.py` (FR-001-FR-003, FR-006)
- [X] T028 [US1] Make install-on-start, compatibility, activation, challenge, failure recovery, and UI result orchestration manager-neutral in `src/wright_engineering/runtime/lifecycle.py` (FR-002-FR-007, FR-012, FR-014-FR-017, FR-046)
- [X] T029 [US1] Expose stable manager-neutral runtime serve/lifecycle/MCP dispatch without importing runtime extras in `src/wright_engineering/cli.py` (FR-004-FR-006, FR-047)
- [X] T030 [US1] Convert `hermes-plugin-wright/` into the supported production Git adapter, remove repository/build behavior and unsupported hooks, and declare the real Hermes compatibility contract in `hermes-plugin-wright/plugin.yaml`, `hermes-plugin-wright/README.md`, and `hermes-plugin-wright/pyproject.toml` (FR-001, FR-003, FR-005, FR-017, FR-027, FR-028)

**Checkpoint**: User Story 1 independently reaches a healthy packaged UI from a
clean candidate install with no forbidden tool invocation.

---

## Phase 4: User Story 2 - Operate Wright Reliably from Hermes (Priority: P1)

**Goal**: Provide truthful start/status/doctor/stop and existing catalog/workspace
behavior for multiple Hermes sessions.

**Independent Test**: Start twice, inspect status/doctor, use catalog/MCP and two
sessions, create/reopen a workspace, stop twice, and restart without duplicate or
orphan processes.

### Tests first

- [X] T031 [P] [US2] Add structured manager-neutral status and doctor state/health/remediation tests in `tests/native_runtime/test_status_doctor.py` (FR-009, FR-010, FR-046, SC-005)
- [X] T032 [P] [US2] Add idempotent stop, stale PID, identity mismatch, forced timeout, and unrelated Hermes/process safety tests in `tests/native_runtime/test_lifecycle_stop.py` (FR-008, FR-014-FR-016, SC-004)
- [X] T033 [P] [US2] Add concurrent multi-session start/status/stop and lifecycle-busy tests in `tests/native_runtime/test_concurrency.py` (FR-007, FR-014, SC-004)
- [X] T034 [P] [US2] Add packaged catalog, MCP transport/progress/cancellation, workspace creation/reopen, and invoking-manager connectivity integration tests in `tests/native_runtime/test_packaged_integration.py` (FR-011-FR-013, FR-018, FR-047, SC-011)
- [X] T035 [US2] Add slash-command results for start/status/doctor/stop/open/catalog/info/install in `tests/native_runtime/test_commands_operate.py` (FR-006, FR-009-FR-013)

### Implementation

- [X] T036 [US2] Implement read-only status and bounded doctor checks across adapter/runtime/process/API/UI/manager/MCP/catalog/data/config/workspaces in `src/wright_engineering/runtime/diagnostics.py` (FR-009, FR-010, FR-025, FR-026, FR-046)
- [X] T037 [US2] Implement idempotent safe stop and interrupted-operation reconciliation in `src/wright_engineering/runtime/lifecycle.py` (FR-008, FR-014-FR-016)
- [X] T038 [US2] Project lifecycle results and existing open/catalog commands through the thin Hermes adapter in `hermes-plugin-wright/commands.py` (FR-006, FR-009-FR-013)
- [X] T039 [US2] Remove repository-relative Hermes gateway/runtime assumptions from `apps/api/src/api/services/hermes_sync.py`, `apps/api/src/api/services/wright_gateway_sync.py`, and `packages/agent_adapters/src/agent_adapters/hermes_config.py` (FR-003, FR-006, FR-013)
- [X] T040 [US2] Add structured lifecycle operation/correlation events without secrets in `src/wright_engineering/runtime/logging.py` and integrate them in `src/wright_engineering/runtime/lifecycle.py` (FR-025, FR-026)

**Checkpoint**: User Stories 1 and 2 pass independently and existing
provider-neutral MCP behavior remains green.

---

## Phase 5: User Story 3 - Upgrade and Roll Back Safely (Priority: P1)

**Goal**: Upgrade from previous stable with retained data and recover or refuse
rollback safely according to schema compatibility.

**Independent Test**: Install previous stable, create data, update to candidate,
inject failures, roll back where compatible, and prove no silent data loss.

### Tests first

- [X] T041 [P] [US3] Add previous-stable artifact acquisition and representative retained-data fixture tests in `tests/native_runtime/test_previous_stable.py` (FR-018, FR-030, FR-033)
- [X] T042 [P] [US3] Add stage/backup/migrate/activate/update success and idempotency tests in `tests/native_runtime/test_update.py` (FR-016-FR-020, SC-006)
- [X] T043 [P] [US3] Add interrupted download, hash failure, migration failure, failed health, and predecessor restoration tests in `tests/native_runtime/test_update_failures.py` (FR-016, FR-019, FR-034, SC-007)
- [X] T044 [P] [US3] Add compatible rollback, incompatible schema refusal, unavailable artifact, and no-implicit-backup-restore tests in `tests/native_runtime/test_rollback.py` (FR-017-FR-020, FR-034, SC-007, SC-009)
- [X] T045 [US3] Add `/wright update` and `/wright rollback` command contract tests in `tests/native_runtime/test_commands_update.py` (FR-006, FR-017-FR-020)

### Implementation

- [X] T046 [US3] Add runtime data-schema bounds and backup/migration preflight integration in `src/wright_engineering/runtime/migrations.py` and `packages/data_vault/src/data_vault/migrations.py` (FR-018-FR-020)
- [X] T047 [US3] Implement staged exact-version update, atomic activation, retained predecessor, and safe failure recovery in `src/wright_engineering/runtime/lifecycle.py` (FR-016-FR-020)
- [X] T048 [US3] Implement compatibility-gated runtime rollback and explicit backup recovery diagnostics in `src/wright_engineering/runtime/lifecycle.py` and `src/wright_engineering/runtime/diagnostics.py` (FR-017-FR-020)
- [X] T049 [US3] Expose manager-neutral update/rollback through the public CLI and thin Hermes adapter projection in `src/wright_engineering/cli.py` and `hermes-plugin-wright/commands.py` (FR-006, FR-017-FR-020, FR-046)

**Checkpoint**: Previous-stable upgrade and both rollback outcomes pass without
workspace/config/catalog loss.

---

## Phase 6: User Story 4 - Uninstall Without Accidental Data Loss (Priority: P2)

**Goal**: Remove executable/plugin state safely, preserve data by default, and
purge only explicitly confirmed Wright-owned data.

**Independent Test**: Uninstall, prove data preserved, reinstall/reopen, purge,
and prove exact deletion boundaries.

### Tests first

- [X] T050 [P] [US4] Add running/stopped uninstall, runtime/cache removal, preserved data, and explicit manager-adapter removal-sequence tests in `tests/native_runtime/test_uninstall.py` (FR-021, FR-024, SC-008)
- [X] T051 [P] [US4] Add reinstall discovery and workspace/config recovery tests in `tests/native_runtime/test_reinstall.py` (FR-021, FR-024, SC-006, SC-008)
- [X] T052 [P] [US4] Add confirmation, symlink, broad-root, external-workspace, unrelated-Hermes, partial failure, and exact deletion tests in `tests/native_runtime/test_purge.py` (FR-022, FR-023, FR-025, SC-008)
- [X] T053 [US4] Add `/wright uninstall` and `/wright purge` command tests plus Hermes remove-after-runtime-uninstall contract tests in `tests/native_runtime/test_commands_remove.py` (FR-006, FR-021-FR-024)

### Implementation

- [X] T054 [US4] Implement stop-and-remove runtime/cache/state with default data preservation in `src/wright_engineering/runtime/lifecycle.py` (FR-021, FR-024)
- [X] T055 [US4] Implement confirmation-bound contained purge and deletion evidence in `src/wright_engineering/runtime/purge.py` (FR-022, FR-023, FR-025)
- [X] T056 [US4] Remove the unsupported Hermes `pre_remove` hook and implement the documented `/wright uninstall` then `hermes plugins remove wright` sequence in `hermes-plugin-wright/commands.py`, `hermes-plugin-wright/plugin.yaml`, and `docs/getting-started/hermes-plugin.md` (FR-006, FR-021-FR-024)
- [X] T057 [US4] Add reinstall/adopt-preserved-data reconciliation in `src/wright_engineering/runtime/lifecycle.py` (FR-018, FR-024)

**Checkpoint**: Default uninstall deletes zero user files; explicit purge deletes
all and only the approved Wright-owned test data.

---

## Phase 7: User Story 5 - Publish a Complete Native Release (Priority: P1)

**Goal**: Make native plugin/runtime distribution and public lifecycle verification
terminal requirements beside all existing Docker/Python/release artifacts.

**Independent Test**: Rehearse entirely from local candidates with zero public
mutation, then validate workflow policy/evidence showing no final release path can
bypass native or Docker published-artifact checks.

### Tests first

- [X] T058 [P] [US5] Update Python artifact tests for complete application contents, UI manifest, runtime extra, base isolation, and single public distribution in `tests/release/test_python_artifacts.py` and `tests/test_public_python_distribution.py` (FR-027-FR-030, FR-038)
- [X] T059 [P] [US5] Add native evidence schema/assembly/verification pass and missing-field failure tests in `tests/release/test_native_release_evidence.py` (FR-036-FR-040)
- [X] T060 [P] [US5] Add workflow policy tests for candidate matrix, no PR publication, build-once Python subject, stable Hermes activation, public lifecycle verification, Docker preservation, docs, and GitHub-Release-last dependencies in `tests/release/test_native_workflow_policy.py` (FR-036-FR-041)
- [X] T061 [P] [US5] Add clean platform matrix harness unit/integration tests and forbidden executable audit tests in `tests/native_runtime/test_harness.py` (FR-031-FR-035, SC-002, SC-013)
- [X] T062 [P] [US5] Add real Hermes Git lifecycle tests plus Codex direct-MCP profile contract tests in `tests/native_runtime/test_harness.py`, `tests/native_runtime/test_hermes_package_plugin_contract.py`, and `tests/native_runtime/test_codex_manager_profile.py` (FR-001, FR-003, FR-036, FR-037, FR-047, FR-048)
- [X] T063 [P] [US5] Add release rehearsal tests proving zero stable registry/channel mutation from feature/PR events in `tests/release/test_native_release_rehearsal.py` (FR-030, FR-041)

### Implementation

- [X] T064 [US5] Extend Python artifact inspection/evidence for bundled modules, static UI, compatibility, and runtime-extra lock in `scripts/release/python_artifacts.py`, `scripts/build-python-distributions.sh`, and `scripts/build-native-runtime.py` (FR-027-FR-030, FR-038)
- [X] T065 [US5] Implement clean real-Hermes-Git adapter/lifecycle matrix plus the Codex direct-MCP profile with subprocess audit and source isolation in `scripts/test-native-hermes-install.py` (FR-031-FR-035, FR-047, FR-048)
- [X] T066 [US5] Add mandatory native candidate workflow on claimed platforms with real Hermes Git adapter installation, Codex profile checks, local wheelhouse, and no publish permissions in `.github/workflows/native-hermes-pr.yml` (FR-030-FR-035, FR-041, FR-047)
- [X] T067 [US5] Add native candidate jobs to ordinary Python/Windows quality dependencies in `.github/workflows/python-quality.yml` and `.github/workflows/test-windows.yml` (FR-033-FR-035, FR-045)
- [X] T068 [US5] Extend release evidence model/schema/assembler/verifier for native subjects in `scripts/release/evidence.py`, `specs/047-python-oci-release-train/contracts/release-evidence.schema.json`, `scripts/assemble-release-evidence.py`, and `scripts/verify-release-evidence.py` (FR-036-FR-040)
- [X] T069 [US5] Add build-once runtime-extra validation, immutable Hermes Git adapter validation, Codex connection checks, and published native lifecycle jobs to `.github/workflows/release.yml` while retaining mandatory PyPI/GHCR/Docker Hub/docs/GitHub Release gates (FR-036-FR-040, FR-047)
- [X] T070 [US5] Make `.github/workflows/sync-hermes-plugin-mirror.yml` publish the supported thin Hermes Git adapter identity while preventing the mirror alone from satisfying runtime release evidence (FR-027, FR-036-FR-040)
- [X] T071 [US5] Add native recovery/channel rollback steps without weakening immutable Python or OCI recovery in `docs/release/release-recovery.md` and `docs/release/release-runbook.md` (FR-036-FR-040)
- [X] T072 [US5] Add native acceptance to `scripts/check-dev-merge.sh`, `scripts/check-prod-merge.sh`, and `CONTRIBUTING.md` with no native skip flag (FR-045, SC-015)
- [X] T073 [US5] Validate and record the real Hermes Git plugin protocol plus the Codex direct-MCP protocol in `src/wright_engineering/compatibility.json`, adapter manifests, and `docs/getting-started/`; mark complete only when real manager interfaces pass immutable-adapter install/connection and Wright lifecycle tests (FR-001, FR-003, FR-017, FR-035-FR-037, FR-047, FR-048)

**Checkpoint**: No feature/PR workflow can publish, and no production workflow can
reach final docs/GitHub Release without both native and Docker terminal evidence.

---

## Phase 8: User Story 6 - Understand Installation and Package Roles (Priority: P2)

**Goal**: Make Hermes the clear primary manager path, document direct Codex
connections, preserve Docker as turnkey, and document exact
lifecycle/data/package behavior.

**Independent Test**: Documentation contract tests and a clean evaluator can
follow either public path without repository-development instructions.

### Tests first

- [X] T074 [P] [US6] Update documentation release-gate tests for Hermes, direct Codex, one runtime role, exact lifecycle commands, data semantics, platform evidence, mandatory Docker, and explicit OpenClaw deferral in `tests/test_docs_release_gate.py` and `tests/test_hermes_plugin_mirror_docs.py` (FR-027, FR-028, FR-039, FR-042-FR-044, FR-047, SC-014)
- [X] T075 [P] [US6] Add command/example drift checks between manager profiles, compatibility metadata, package metadata, plugin help, install docs, and release runbook in `tests/test_native_docs_contract.py` (FR-017, FR-027, FR-028, FR-042, FR-047)

### Implementation

- [X] T076 [US6] Replace helper-only and Docker-primary claims with verified manager-neutral native runtime, Hermes-primary, direct Codex, mandatory Docker, and explicit OpenClaw-future language in `README.md`, `docs/getting-started/overview.md`, and `docs/getting-started/install-matrix.md` (FR-027, FR-028, FR-039, FR-042, FR-047, SC-014)
- [X] T077 [US6] Document real Hermes Git install and exact Wright lifecycle flows plus direct Codex MCP configuration in `docs/getting-started/hermes-plugin.md`, `docs/getting-started/codex.md`, and `docs/hermes-desktop-wright.md` (FR-001-FR-010, FR-017-FR-024, FR-042, FR-047, FR-048)
- [X] T078 [US6] Document managed-runtime, manager-adapter, runtime-extra, and private-package roles and compatibility policy in `docs/release/community-release-readiness.md` and `docs/release/hermes-plugin-mirror.md` (FR-027-FR-030, FR-042)
- [X] T079 [US6] Document per-manager prerequisites, offline cache/index operation, platform support boundaries, external MCP prerequisites, and Docker coexistence in `docs/getting-started/prerequisites.md`, `docs/getting-started/quickstart-docker.md`, and `docs/mcp-catalog/mcp-server-testing-process.md` (FR-035, FR-039, FR-042-FR-044, FR-048)

**Checkpoint**: Public documentation contains no source-checkout requirement for
native users and no claim unsupported by the compatibility/evidence matrix.

---

## Phase 9: User Story 7 - Use the Same Wright Runtime from Other Agent Managers

**Goal**: Connect Codex directly to the same provider-neutral Wright
MCP service and lifecycle without routing through Hermes or adding
manager-specific branches to Wright core.

**Independent Test**: Generate or load Hermes and Codex profiles for one
`WRIGHT_HOME`; prove identical runtime identity and MCP tools while each
manager's configuration and prerequisites stay in its adapter.

### Tests first

- [X] T080 [P] [US7] Add manager-profile schema, shared-runtime identity, no-Hermes-intermediary, and prerequisite-isolation tests in `tests/native_runtime/test_manager_profiles.py` (FR-017, FR-046-FR-048, SC-016)
- [X] T081 [P] [US7] Add direct Codex STDIO/Streamable-HTTP MCP configuration contract tests in `tests/native_runtime/test_codex_manager_profile.py` (FR-047, SC-016)
- [X] T082 [US7] Record OpenClaw as future work and exclude it from current compatibility, release evidence, CI, and acceptance gates (FR-048)

### Implementation

- [X] T083 [US7] Implement manager-neutral Wright lifecycle/MCP profile generation in `src/wright_engineering/manager_profiles.py` without importing Hermes or Codex runtimes (FR-046-FR-048)
- [X] T084 [US7] Add a thin Codex integration descriptor/example in `integrations/codex/` that resolves the shared Wright MCP endpoint (FR-027, FR-047, FR-048)
- [X] T085 [US7] Integrate manager profile identities and connection results into compatibility and release evidence in `src/wright_engineering/compatibility.json`, `scripts/release/evidence.py`, and `scripts/verify-release-evidence.py` (FR-017, FR-036-FR-038, FR-047)

**Checkpoint**: Hermes and Codex use the same Wright runtime and MCP contract
without making Wright core depend on any manager; OpenClaw remains future work.

---

## Phase 10: Cross-Cutting Validation and Delivery

**Purpose**: Prove every requirement against exact artifacts, remediate all
findings, and deliver a clean feature branch and green PR without merging.

- [X] T086 Run `/speckit-analyze`, remediate all CRITICAL/HIGH findings in `specs/050-native-hermes-install/spec.md`, `plan.md`, and `tasks.md`, and rerun until coverage is complete
- [X] T087 [P] Run focused Python unit/contract/integration/security suites including `uv run pytest -q tests/native_runtime hermes-plugin-wright/tests tests/release` and record results in `specs/050-native-hermes-install/validation.md`
- [X] T088 [P] Run frontend Vitest/build and packaged UI/Playwright integration, recording results in `specs/050-native-hermes-install/validation.md`
- [X] T089 [P] Run provider-neutral MCP, workspace/session, gateway/rebinding suites plus `scripts/docker-smoke-test.sh` while retaining the separate server process in `docs/mcp-catalog/mcp-server-testing-process.md`, recording results in `specs/050-native-hermes-install/validation.md`
- [X] T090 Run the complete real-Hermes-Git adapter, Codex connection, and Wright install/update/rollback/uninstall/purge matrix with no forbidden tools or acceptance skips and record immutable identities/results in `specs/050-native-hermes-install/validation.md`
- [X] T091 Run secret, dependency, artifact, manager-boundary, and workflow policy scans and record results in `specs/050-native-hermes-install/validation.md`
- [X] T092 Run `scripts/check-dev-merge.sh` without native acceptance skips and remediate every failure
- [X] T093 Run `scripts/check-prod-merge.sh` without native acceptance skips and remediate every failure
- [X] T094 Verify implementation and local-validation tasks T001-T093 are `[X]`, all requirements have evidence, no unexpected worktree changes exist, and update `specs/050-native-hermes-install/validation.md` with the completion audit
- [ ] T095 Execute the configured Spec Kit after-implement commit hook from repository root `D:/repos/wright`, verify a clean worktree, and push `050-native-hermes-install` to origin
- [ ] T096 On pull request #79 from `050-native-hermes-install` to `dev`, monitor every required GitHub check, remediate failures, and stop only when all checks are green without merging

---

## Requirement Coverage

| Requirement | Tasks |
| --- | --- |
| FR-001 | T019, T023, T027, T030, T062, T065, T070, T073, T090 |
| FR-002 | T010, T017, T019, T021, T023, T027, T028 |
| FR-003 | T022, T023, T027, T030, T062, T065 |
| FR-004 | T006, T020, T024-T026, T029 |
| FR-005 | T020, T022, T025, T026, T030 |
| FR-006 | T019, T027-T029, T035, T038, T045, T049, T053, T056 |
| FR-007 | T008, T011, T021, T028, T033 |
| FR-008 | T011, T032, T037 |
| FR-009 | T013, T031, T035, T036, T038 |
| FR-010 | T031, T035, T036 |
| FR-011 | T020, T034, T038 |
| FR-012 | T020, T021, T028, T034, T038 |
| FR-013 | T020, T034, T039, T080-T084, T089 |
| FR-014 | T008, T011, T013, T015, T021, T028, T032, T033, T037 |
| FR-015 | T008, T013, T015, T021, T028, T032, T037 |
| FR-016 | T008, T013, T015, T021, T028, T032, T037, T042-T044, T047 |
| FR-017 | T009, T016, T042, T044, T047-T049, T073, T075, T077, T080, T085 |
| FR-018 | T034, T041, T042, T046, T047, T057 |
| FR-019 | T042-T044, T046-T048 |
| FR-020 | T042, T044, T046-T049 |
| FR-021 | T007, T014, T050, T051, T053, T054, T056 |
| FR-022 | T007, T014, T052, T053, T055 |
| FR-023 | T007, T014, T052, T055 |
| FR-024 | T007, T014, T050, T051, T053, T054, T056, T057 |
| FR-025 | T006, T012, T031, T036, T040, T052, T055, T091 |
| FR-026 | T012, T031, T036, T040 |
| FR-027 | T006, T024, T030, T058, T064, T070, T074-T078, T084 |
| FR-028 | T006, T009, T016, T024, T030, T058, T074-T078 |
| FR-029 | T006, T010, T017, T024, T025, T058, T064 |
| FR-030 | T010, T017, T024, T025, T041, T058, T063-T066 |
| FR-031 | T010, T023, T061, T065, T090 |
| FR-032 | T010, T023, T061, T062, T065, T073, T090 |
| FR-033 | T023, T034, T041, T061, T065-T067, T090 |
| FR-034 | T023, T033, T043, T044, T052, T061, T065, T090 |
| FR-035 | T009, T016, T061, T065-T067, T073, T079, T090 |
| FR-036 | T059, T060, T062, T068-T073, T085, T093, T096 |
| FR-037 | T059, T060, T062, T068, T069, T073, T085, T090 |
| FR-038 | T058, T059, T064, T068, T069, T085, T091 |
| FR-039 | T060, T068-T071, T074, T076, T079, T089, T093 |
| FR-040 | T059, T060, T068-T071, T089, T090, T093, T096 |
| FR-041 | T060, T063, T066, T069, T091 |
| FR-042 | T071, T074-T079 |
| FR-043 | T060, T069, T074, T076, T079, T089, T093 |
| FR-044 | T074, T079, T089 |
| FR-045 | T067, T072, T086-T096 |
| FR-046 | T007, T009, T014, T016, T028, T029, T031, T036, T080, T083, T090 |
| FR-047 | T029, T034, T062, T065, T066, T069, T073-T077, T080-T085, T089, T090 |
| FR-048 | T009, T019, T023, T027, T062, T065, T073, T077, T079, T080, T082-T084, T090, T091 |
| SC-001 | T019, T023, T027-T030, T065, T090 |
| SC-002 | T023, T061, T065-T067, T090 |
| SC-003 | T021, T023, T028, T061, T065, T090 |
| SC-004 | T011, T021, T028, T032, T033, T037, T090 |
| SC-005 | T012, T031, T035, T036, T040, T090 |
| SC-006 | T034, T041, T042, T046-T048, T051, T057, T090 |
| SC-007 | T043, T044, T047, T048, T090 |
| SC-008 | T007, T014, T050-T057, T090 |
| SC-009 | T009, T016, T044, T048, T062, T073, T090 |
| SC-010 | T006, T010, T012, T024, T025, T058, T064, T065, T091 |
| SC-011 | T020, T034, T039, T083, T089 |
| SC-012 | T059, T060, T068-T070, T073, T085, T090, T093, T096 |
| SC-013 | T009, T016, T061, T065-T067, T073, T079, T090 |
| SC-014 | T074-T079 |
| SC-015 | T067, T072, T086-T096 |
| SC-016 | T062, T065, T073-T077, T080-T085, T090 |

Hermes Git is an adapter prerequisite and is exercised only during the real
Hermes plugin install/update phase. T023, T062, T065, T073, and T090 must prove
that the subsequent Wright lifecycle is independent of Git and that Codex
connects to the same manager-neutral runtime without Hermes.

---

## Dependencies and Execution Order

### Phase dependencies

- Phase 1 has no dependency.
- Phase 2 depends on Phase 1 and blocks all user stories.
- User Story 1 depends on Phase 2 and is the MVP.
- User Story 2 depends on the packaged start path from User Story 1.
- User Story 3 depends on the installed/operable runtime from User Stories 1-2.
- User Story 4 depends on the runtime/data separation from User Stories 1-3.
- User Story 5 consumes the exact artifact and lifecycle built by User Stories
  1-4 and verifies each claimed manager through its real supported interface.
- User Story 6 depends on executable contracts from User Stories 1-5 so docs do
  not make premature claims.
- User Story 7 depends on the manager-neutral runtime and public MCP contract
  from User Stories 1-5.
- Phase 10 depends on all stories and remains incomplete until real manager
  interfaces and public-artifact evidence exist.

### Test-first ordering

- T006-T012 fail before T013-T018.
- T019-T023 fail before T024-T030.
- T031-T035 fail before T036-T040.
- T041-T045 fail before T046-T049.
- T050-T053 fail before T054-T057.
- T058-T063 fail before T064-T073.
- T074-T075 fail before T076-T079.
- T080-T082 fail before T083-T085.

### Parallel opportunities

- T006-T012 may run in parallel after the skeleton exists.
- Within each user story, tasks marked `[P]` use separate test files and may run
  together before sequential implementation.
- T058-T063 may run together; workflow/release implementations T064-T073 remain
  ordered where they edit shared workflows/evidence.
- Final focused Python, frontend, and provider-neutral/Docker validations
  T087-T089 may run in parallel before the full matrix and merge gates.

## Parallel Examples

### User Story 1

```text
T019: Hermes entry-point isolation tests
T020: Packaged API/UI/catalog tests
T021: Lifecycle start tests
T022: Slash-command start tests
```

### User Story 5

```text
T058: Python application-artifact tests
T059: Native release-evidence tests
T060: Workflow terminal-dependency tests
T061: Platform harness tests
T062: Real manager adapter contract tests
T063: No-public-mutation rehearsal tests
```

## Implementation Strategy

1. Complete setup and foundational safety contracts.
2. Deliver User Story 1 as the independently testable native MVP.
3. Add operational, update/rollback, and uninstall/purge stories in priority
   order, preserving a green prior story at each checkpoint.
4. Add release orchestration only after local exact-artifact lifecycle passes.
5. Update public documentation only after the executable contracts are green.
6. Add a Codex direct MCP profile without adding manager branches to runtime
   core; defer OpenClaw to a future feature.
7. Run the complete completion audit and delivery phase; do not substitute
   fixtures for evidence from real manager interfaces.

## Task Summary

- **Total tasks**: 96
- **Setup/foundational**: 18
- **US1**: 12
- **US2**: 10
- **US3**: 9
- **US4**: 8
- **US5**: 16
- **US6**: 6
- **US7**: 6
- **Cross-cutting delivery**: 11
- **Suggested MVP**: Phases 1-3 (T001-T030), while retaining the full goal as the
  completion boundary.
