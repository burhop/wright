# Tasks: Engineering Capability Program Hardening

**Input**: Design documents from `specs/073-program-hardening/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`,
`contracts/`, `quickstart.md`

**Tests**: Required by the user, specification, and Wright constitution. Tests
are written before the corresponding implementation and cover component,
mocked UI integration, system E2E, native lifecycle, Docker persistence,
security, packaging, docs, and the authoritative development gate.

**Branch note**: The user explicitly selected the shared
`codex/rivet-engineering-program` integration branch so Loops 068–073 can be
combined before one merge to `dev`. The Spec Kit numbered-branch helper is
therefore an intentional no-op for this loop; `.specify/feature.json` pins the
numbered feature directory.

## Phase 1: Setup and Baseline

**Purpose**: Establish exact current-state evidence and contract fixtures.

- [x] T001 Record the Loop 073 scope, active branch exception, dependencies, and no-release/no-actuation boundary in `specs/073-program-hardening/plan.md`
- [x] T002 [P] Add schema-validation fixtures for all Loop 073 contracts in `tests/program_hardening/test_contracts.py`
- [x] T003 [P] Inventory current data-vault migration, native manifest, catalog/model cache, scenario-report, and Docker volume roots in `tests/program_hardening/state_inventory.py`
- [x] T004 [P] Capture the current merge-gate and support-claim baseline in `docs/engineering-capability-program-progress.md`

---

## Phase 2: Foundational Safety and Compatibility Boundaries

**Purpose**: Add shared contracts and failing regression tests before any UI or
endpoint implementation.

**Critical**: No story implementation starts until these boundaries exist.

- [x] T005 Add canonical bounded diagnostic models, stable reason/recovery enums, and safe projection limits in `packages/workspace_service/src/workspace_service/support_diagnostics.py`
- [x] T006 [P] Add adversarial redaction, canonical digest, count/string/byte-bound, and fail-closed serialization tests in `packages/workspace_service/tests/test_support_diagnostics.py`
- [x] T007 [P] Add a migration-registry/current-compatibility drift test in `tests/native_runtime/test_program_state_compatibility.py`
- [x] T008 [P] Add exact named-volume persistence contract tests for all supported Compose profiles in `tests/program_hardening/test_docker_persistence.py`
- [x] T009 [P] Add exact artifact/platform evidence schema and support-claim tests in `tests/program_hardening/test_compatibility_evidence.py`
- [x] T010 Correct the packaged data-schema compatibility ceiling in `src/wright_engineering/compatibility.json`
- [x] T011 Reconcile native lifecycle diagnostic redaction limits with the shared diagnostic contract in `src/wright_engineering/runtime/diagnostics.py`

**Checkpoint**: Shared safety, evidence, and compatibility boundaries are
independently testable.

---

## Phase 3: User Story 1 — Complete a Guided Engineering Journey (Priority: P1)

**Goal**: Make the path from capability discovery through Rivet evidence and
recovery understandable without internal architecture knowledge.

**Independent Test**: Complete the deterministic MCP-only journey in at most
five minutes/twenty primary interactions and recover every blocked variant in at
most three interactions.

### Tests for User Story 1

- [x] T012 [P] [US1] Add component tests for next-action, blocker-origin, loading, empty, stale, running, failed, residue, and restored states in `apps/web/src/components/tools/CapabilityLibrary.spec.tsx`
- [x] T013 [P] [US1] Add Rivet report attribution, assertion, cleanup, and safe-recovery component tests in `apps/web/src/components/chat/RivetScenarioReport.spec.tsx`
- [x] T014 [P] [US1] Add deterministic MCP-only and MCP-plus-local-model mocked journeys with separate five-minute/twenty-interaction budgets in `tests/ui-integration/engineering-program-journey.spec.ts`
- [x] T015 [P] [US1] Add local API/UI happy paths for both representative journeys plus one provider-failure system test in `tests/e2e/test_engineering_program_journey.py`

### Implementation for User Story 1

- [x] T016 [US1] Add one-primary-next-action and blocker-origin projection to capability onboarding in `apps/web/src/components/tools/CapabilityLibrary.tsx`
- [x] T017 [US1] Preserve reviewed capability-to-workspace-to-Rivet handoff across refresh without replay in `apps/web/src/components/pages/ToolRegistryPage.tsx`
- [x] T018 [US1] Harden provider attribution, engineering material/observation separation, cleanup truth, and recovery text in `apps/web/src/components/chat/RivetScenarioReport.tsx`
- [x] T019 [US1] Compose the complete first-use handoff in `apps/web/src/components/chat/RivetScenarioLibrary.tsx`
- [x] T020 [US1] Document the human-repeatable MCP-only journey in `docs/testing/engineering-program-usability.md`

**Checkpoint**: User Story 1 is independently complete with deterministic
component, mocked UI, system, and human-repeatable evidence.

---

## Phase 4: User Story 2 — Diagnose and Recover Safely (Priority: P1)

**Goal**: Preview and deliberately export a bounded, local, proprietary-data-safe
diagnostic snapshot with stable provider attribution and recovery.

**Independent Test**: Build diagnostics from at least twenty adversarial value
classes, inspect the manifest, export once with exact scope/digest/principal
binding, reject replay/cross-scope/stale cases, and find no prohibited payload.

### Tests for User Story 2

- [x] T021 [P] [US2] Add preview/export grant expiry, one-use, cross-principal, cross-workspace, changed-digest, restart, and concurrency tests in `packages/workspace_service/tests/test_support_diagnostic_service.py`
- [x] T022 [P] [US2] Add thin-route request, response, authorization, attachment-header, and safe-error tests in `apps/api/tests/test_support_diagnostics_api.py`
- [x] T023 [P] [US2] Add component tests for category manifest, confirmation, expiry, replay, export, and safe failure states in `apps/web/src/components/support/SupportDiagnosticsPanel.spec.tsx`
- [x] T024 [P] [US2] Add bounded fixture performance tests for preview/export in `packages/workspace_service/tests/test_support_diagnostics_performance.py`
- [x] T025 [P] [US2] Add distribution/log/trace/export scans for prohibited values, executable content, reusable authority, and physical-actuation commands/configuration in `tests/program_hardening/test_diagnostic_leaks.py`

### Implementation for User Story 2

- [x] T026 [US2] Implement immutable snapshot assembly plus structured safe logging and local trace correlation from allowlisted capability/model/Rivet/lifecycle projections in `packages/workspace_service/src/workspace_service/support_diagnostic_service.py`
- [x] T027 [US2] Implement process-local expiring principal/workspace/scope-bound single-use export grants in `packages/workspace_service/src/workspace_service/support_diagnostic_service.py`
- [x] T028 [US2] Export the support diagnostic application service from `packages/workspace_service/src/workspace_service/__init__.py`
- [x] T029 [US2] Add preview/export request and response schemas plus a business-logic-free router in `apps/api/src/api/routers/support_diagnostics.py`
- [x] T030 [US2] Register the diagnostics router and application service composition in `apps/api/src/api/main.py`
- [x] T031 [US2] Add typed client contracts and preview/export calls in `apps/web/src/services/workspace-service.ts`
- [x] T032 [US2] Build the accessible local-only preview/confirm/export pattern in `apps/web/src/components/support/SupportDiagnosticsPanel.tsx`
- [x] T033 [US2] Integrate scoped diagnostics into the Rivet report without exposing report payload bodies in `apps/web/src/components/chat/RivetScenarioReport.tsx`
- [x] T034 [US2] Document inclusion, omission, redaction, limits, export, and support interpretation in `docs/operations/engineering-support-diagnostics.md`

**Checkpoint**: User Story 2 is independently complete; diagnostics are useful
for attribution but cannot become an exfiltration or reusable-authority path.

---

## Phase 5: User Story 3 — Upgrade, Roll Back, and Work Offline (Priority: P1)

**Goal**: Preserve or explicitly account for every durable program state class
through native/Docker upgrade, rollback, restart, uninstall, purge, and offline
operation.

**Independent Test**: Seed predecessor state for catalog, custom/disabled
entries, workspace grants, model packages/installs, workflow bindings, run
manifests, scenario reports, caches, and evidence; migrate/restart/rollback/
uninstall offline and compare the state inventory exactly.

### Tests for User Story 3

- [x] T035 [P] [US3] Add the complete predecessor-state seed and current-schema migration assertions in `tests/native_runtime/test_program_state_compatibility.py`
- [x] T036 [P] [US3] Add interrupted upgrade, same-plan idempotency, mixed-version refusal, backup, and newer-state quarantine assertions in `tests/native_runtime/test_program_state_compatibility.py`
- [x] T037 [P] [US3] Extend workspace upgrade compatibility tests through catalog/model/Rivet/scenario state in `packages/workspace_service/tests/test_upgrade_compatibility.py`
- [x] T038 [P] [US3] Add offline catalog/model/scenario persistence and zero-network assertions in `tests/e2e/test_engineering_program_offline.py`
- [x] T039 [P] [US3] Add deterministic Docker profile volume contracts plus an availability-guarded disposable-container replacement/restart persistence lifecycle and destructive-flag refusal tests in `tests/program_hardening/test_docker_persistence.py`

### Implementation for User Story 3

- [x] T040 [US3] Add state-inventory capture/comparison helpers for native lifecycle plans in `src/wright_engineering/runtime/migrations.py`
- [x] T041 [US3] Add explicit incompatible-newer-state quarantine/recovery metadata in `src/wright_engineering/runtime/state.py`
- [x] T042 [US3] Ensure catalog/model/workflow evidence identity changes invalidate readiness while cached bytes remain reference-safe in `packages/workspace_service/src/workspace_service/support_diagnostic_service.py`
- [x] T043 [US3] Align all Compose/profile manifests with the documented persistent state roots in `docker-compose.yml`, `docker-compose.mcp.yml`, and `docker/image-family.yaml`
- [x] T044 [US3] Document native/Docker upgrade, rollback, restart, uninstall, purge, retained state, and offline behavior in `docs/getting-started/program-state-lifecycle.md`
- [x] T045 [US3] Update the install support matrix with exact-evidence versus unverified platform language in `docs/getting-started/install-matrix.md`

**Checkpoint**: User Story 3 is independently complete with byte-stable material
identity and explicit accounting for every seeded state class.

---

## Phase 6: User Story 4 — Accessible Long Operations (Priority: P2)

**Goal**: Keep critical actions, progress, cancellation, evidence, and recovery
operable by keyboard at narrow width/zoom and reduced motion.

**Independent Test**: Run both journeys keyboard-only at 320 CSS pixels, 200%
zoom, and reduced motion; inspect focus/status semantics and obtain zero serious
or critical scoped Axe findings.

### Tests for User Story 4

- [x] T046 [P] [US4] Add keyboard/focus/live-region/reduced-motion component assertions in `apps/web/src/components/support/SupportDiagnosticsPanel.spec.tsx`
- [x] T047 [P] [US4] Add 320 CSS-pixel, 200% zoom, focus restoration, non-color status, and Axe checks in `tests/ui-integration/engineering-program-journey.spec.ts`
- [x] T048 [P] [US4] Add cancellation timing, cleanup timeout, late-success suppression, and honest indeterminate progress tests in `packages/workspace_service/tests/test_engineering_program_recovery.py`

### Implementation for User Story 4

- [x] T049 [US4] Apply reusable responsive/status/action tokens to diagnostics and engineering journey surfaces in `apps/web/src/index.css`
- [x] T050 [US4] Normalize phase/progress/elapsed/cancellation/terminal/recovery semantics in `apps/web/src/components/chat/RivetScenarioReport.tsx`
- [x] T051 [US4] Preserve focus and prevent confirmation replay across reload/restoration in `apps/web/src/components/support/SupportDiagnosticsPanel.tsx`
- [x] T052 [US4] Record the scoped accessibility matrix and any unrelated pre-existing warnings in `docs/testing/engineering-program-usability.md`

**Checkpoint**: User Story 4 is independently complete with repeatable browser
and component evidence.

---

## Phase 7: User Story 5 — Trust the Supported Environment and Merge Gate (Priority: P2)

**Goal**: Make support claims exact and ensure every deterministic program
regression is caught before the one development merge.

**Independent Test**: Validate evidence records for available/unavailable
platforms, build/rehearse immutable candidates without publication, and show the
authoritative development gate catches every recorded deterministic finding.

### Tests for User Story 5

- [x] T053 [P] [US5] Add release-evidence validation for artifact/platform/architecture isolation and unavailable claims in `tests/release/test_program_compatibility_evidence.py`
- [x] T054 [P] [US5] Add packaged contract, schema, diagnostics, docs, and forbidden-executable assertions in `tests/packaging/test_program_hardening_contents.py`
- [x] T055 [P] [US5] Add a program-gate coverage test mapping recorded deterministic findings to merge-gate commands in `tests/program_hardening/test_merge_gate_coverage.py`

### Implementation for User Story 5

- [x] T056 [US5] Add the deterministic program-hardening slice to `scripts/check-dev-merge.sh`
- [x] T057 [US5] Update contributor gate guidance for newly covered regressions in `CONTRIBUTING.md`
- [x] T058 [US5] Record exact local/CI/Docker evidence levels and deferred host checks in `docs/engineering-capability-program-progress.md`
- [x] T059 [US5] Update release rehearsal documentation without adding publish actions in `docs/release/release-runbook.md`

**Checkpoint**: User Story 5 is independently complete; no fixture/skip result
can produce a supported claim and no release action has occurred.

---

## Phase 8: Cross-Cutting Verification and Integration

**Purpose**: Re-analyze, validate the complete program, and perform the one
authorized integration merge.

- [x] T060 Re-run Spec Kit cross-artifact analysis, remediate every critical/high finding, and record the clean result in `specs/073-program-hardening/checklists/analysis.md`
- [x] T061 Run all focused Python, web component, mocked UI, system E2E, packaging, documentation, native lifecycle, Docker contract, security, and performance commands from `specs/073-program-hardening/quickstart.md`
- [x] T062 Run both representative human-repeatable walkthroughs, enforce their separate time/interaction budgets, and record exact deterministic evidence in `docs/testing/engineering-program-usability.md`
- [x] T063 Run local non-publishing native/release rehearsals and record artifact-bound results in `docs/engineering-capability-program-progress.md`
- [ ] T064 Run `scripts/check-dev-merge.sh` on the exact clean integration tree and record its tree hash in `docs/engineering-capability-program-progress.md`
- [ ] T065 Complete all Loop 073 task/checklist/progress artifacts and commit the coherent checkpoint on `codex/rivet-engineering-program`
- [ ] T066 Fetch latest `origin/dev` and `origin/codex/engineering-mcp-dynamic-catalog`, integrate any missing history, and rerun `scripts/check-dev-merge.sh` on the resulting exact tree
- [ ] T067 Push `codex/rivet-engineering-program`, merge it once with `--no-ff` into `dev`, push `dev`, and verify clean local/remote matching tree hashes

---

## Dependencies and Execution Order

- Phase 1 establishes the reviewable baseline.
- Phase 2 blocks all user stories because diagnostic safety and schema/evidence
  drift must be testable before feature code.
- US1 and US2 may proceed after Phase 2; US2 provides the reusable panel used by
  the complete US1/US4 journey.
- US3 depends only on Phase 2 and can be validated independently of UI work.
- US4 depends on the US1 journey and US2 panel.
- US5 depends on deterministic tests produced by US1–US4.
- Phase 8 depends on all stories and is the only phase authorized to push/merge.

## Parallel Opportunities

- Contract/schema, Docker persistence, compatibility drift, and diagnostic
  adversarial tests touch independent files in Phase 2.
- Component, mocked UI, and Python system tests can be prepared independently
  inside each story before implementation.
- Native compatibility and diagnostic UI/service work are independent until the
  final complete-journey integration.
- Documentation for diagnostics, lifecycle, and usability can be updated from
  their respective verified story evidence.

## Implementation Strategy

1. Complete the shared safety/evidence boundary and make its tests fail for the
   known schema-ceiling defect and missing diagnostics workflow.
2. Deliver US1 and US2 as the minimum user-visible hardening increment.
3. Close state compatibility and persistence in US3 before claiming restart,
   rollback, uninstall, or offline behavior.
4. Exercise the complete experience under US4 accessibility constraints.
5. Bind exact evidence and deterministic findings into the authoritative gate,
   then perform one exact-tree integration under Phase 8.

## Format Validation

All 67 tasks use the required checkbox, sequential task ID, optional `[P]`,
required user-story label within story phases, actionable description, and
concrete repository path or exact command.
