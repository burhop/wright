---

description: "Dependency-ordered implementation tasks for Capability Library and MCP onboarding"
---

# Tasks: Capability Library and MCP Onboarding

**Input**: Design documents from `specs/068-capability-library/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, and completed requirements-quality checklists

**Tests**: Tests are mandatory. Each story starts with failing contract/unit/journey coverage and ends with an independently testable checkpoint.

**Organization**: Tasks are grouped by user story. P1 preservation story US6 is scheduled before P2 stories even though it appears later in the specification.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can proceed concurrently because it uses different files and has no incomplete dependency
- **[Story]**: Maps to a numbered user story in `spec.md`
- Every task names the exact repository path it changes or validates

## Phase 1: Setup and Contract Fixtures

**Purpose**: Establish dependencies, packaged schemas, and deterministic fixture boundaries without changing product behavior.

- [X] T001 Add an explicit bounded `cryptography` dependency for standalone signature verification in `packages/tool_registry/pyproject.toml` and synchronize `uv.lock`
- [X] T002 [P] Copy the approved catalog envelope, import preview, and install plan JSON Schemas plus a versioned public-only trust-root resource with no default network channel into `packages/tool_registry/src/tool_registry/catalog/` and declare them as packaged resources in `packages/tool_registry/pyproject.toml`
- [ ] T003 [P] Add deterministic Ed25519 test-key helpers and a prior 69-record snapshot without Onshape plus signed 70-record Onshape candidate, tampered, expired, and replayed fixtures in `packages/tool_registry/tests/fixtures/catalog_updates.py`
- [X] T004 [P] Add Claude, VS Code, plain-server, adversarial, and oversized import fixtures in `packages/tool_registry/tests/fixtures/mcp_imports.py`
- [X] T005 [P] Add deterministic fake local-package, remote-endpoint, and host-bridge adapter fixtures in `packages/tool_registry/tests/fixtures/onboarding_adapters.py`

---

## Phase 2: Foundational Domain and Storage Contracts

**Purpose**: Add shared immutable records, additive storage, stable diagnostics, and dependency injection required by every story.

**Critical**: No user-story implementation starts until this phase passes focused tests.

- [X] T006 Write migration definition, upgrade, restart, compatibility, and failure-recovery tests for catalog/onboarding tables in `packages/data_vault/tests/test_migrations.py`
- [X] T007 Implement additive migration 13 for snapshots, state, previews, activations, observations, plans, runs, validation evidence, missing reports, and `mcp_servers.transport_variant` in `packages/data_vault/src/data_vault/migrations.py`
- [X] T008 [P] Write Pydantic model and JSON Schema conformance tests for snapshot, capability, import, observation, plan, run, evidence, and report records in `packages/tool_registry/tests/test_capability_models.py`
- [X] T009 Implement evidence classes and immutable domain records with secret-rejecting validators in `packages/tool_registry/src/tool_registry/capability_models.py`
- [X] T010 Extend canonical catalog models/schema with `evidence_class`, exact `streamable_http` versus legacy `sse` catalog values, internal network-runner normalization, and conservative legacy mapping in `packages/tool_registry/src/tool_registry/catalog_models.py`, `packages/tool_registry/src/tool_registry/models.py`, and `packages/tool_registry/src/tool_registry/catalog/schema.json`
- [X] T011 [P] Add stable redacted catalog/import/plan/onboarding diagnostic codes and error types in `packages/tool_registry/src/tool_registry/capability_errors.py`
- [X] T012 Add repository/service construction seams for database path, clock, trust roots, detectors, and adapters in `packages/tool_registry/src/tool_registry/capability_services.py`
- [X] T013 Extend `McpApiService` dependency injection without adding route business logic in `apps/api/src/api/services/mcp_services.py`
- [X] T014 [P] Add shared TypeScript capability, snapshot, import, observation, plan, run, evidence, and report interfaces in `apps/web/src/services/mcp-service.ts`
- [X] T015 Run migration, model, schema-resource, Ruff, and formatting checks over `packages/data_vault` and `packages/tool_registry`

**Checkpoint**: The database upgrades additively, all public records reject secret-bearing fields, schemas ship in the package, and fake adapters can be injected without side effects.

---

## Phase 3: User Story 1 - Find a Compatible Engineering Capability (Priority: P1) - MVP

**Goal**: Provide trustworthy offline discovery, evidence, current-machine reasons, details, and alternatives.

**Independent Test**: With networking disabled and only a bundled catalog, search CAD, inspect compatible/uncertain/blocked/no-public-MCP entries, and see exact evidence, requirements, and recovery or alternatives without any process or user-state mutation.

### Tests for User Story 1

- [X] T016 [P] [US1] Write evidence taxonomy, official-source, legacy-mapping, alias, and Onshape-record tests in `packages/tool_registry/tests/test_catalog_evidence.py`
- [X] T017 [P] [US1] Write read-only machine observation and compatible/incompatible/uncertain/blocked reason tests in `packages/tool_registry/tests/test_machine_compatibility.py`
- [X] T018 [P] [US1] Write capability projection tests that merge catalog metadata with existing install/credential/workspace state without leaking values in `packages/tool_registry/tests/test_capability_views.py`
- [X] T019 [P] [US1] Write API contract/filter/pagination/alias/offline/error tests for capability discovery in `apps/api/tests/test_capability_library_api.py`
- [X] T020 [P] [US1] Write service/component state tests for search, filters, evidence badges, compatibility reasons, details, offline state, and empty state in `apps/web/src/components/tools/CapabilityLibrary.spec.tsx`
- [X] T021 [P] [US1] Write mocked offline discovery, keyboard, narrow-layout, and accessibility journey tests in `tests/ui-integration/capability-library.spec.ts`

### Implementation for User Story 1

- [X] T022 [US1] Add the distinct Onshape Labs FeatureScript MCP official-preview record to the final bundled recovery catalog with vendor evidence while preserving community identities in `packages/tool_registry/src/tool_registry/catalog/engineering-catalog.yaml`
- [X] T023 [US1] Implement conservative evidence-class derivation and official-source validation in `packages/tool_registry/src/tool_registry/catalog_evidence.py`
- [X] T024 [US1] Implement allowlisted read-only runtime, executable, platform, architecture, container, and host observations with stable digests in `packages/tool_registry/src/tool_registry/compatibility.py`
- [X] T025 [US1] Implement reason-coded capability compatibility policy and recovery guidance in `packages/tool_registry/src/tool_registry/compatibility.py`
- [X] T026 [US1] Implement paginated/searchable `CapabilityView` projection while retaining uncataloged custom rows in `packages/tool_registry/src/tool_registry/capability_views.py`
- [X] T027 [US1] Add thin capability list/detail/observe routes and response models in `apps/api/src/api/routers/mcp.py`
- [X] T028 [US1] Implement capability discovery/detail/observation client methods in `apps/web/src/services/mcp-service.ts`
- [X] T029 [P] [US1] Create token-based evidence and compatibility badges in `apps/web/src/components/tools/CapabilityBadges.tsx`
- [X] T030 [P] [US1] Create keyboard-operable multi-dimension filters with URL-stable state in `apps/web/src/components/tools/CapabilityFilters.tsx`
- [X] T031 [P] [US1] Create comparison-friendly capability result cards/list in `apps/web/src/components/tools/CapabilityCard.tsx`
- [X] T032 [P] [US1] Create progressive-disclosure evidence, compatibility, requirement, validation, alternative, and user-state details in `apps/web/src/components/tools/CapabilityDetails.tsx`
- [X] T033 [US1] Refactor the existing registry page into the Capability Library information architecture in `apps/web/src/components/pages/ToolRegistryPage.tsx`
- [X] T034 [US1] Run focused catalog, capability view/API, component, and mocked Playwright tests for US1

**Checkpoint**: US1 works fully offline and makes evidence/compatibility honest without offering unsafe actions.

---

## Phase 4: User Story 2 - Preview and Apply a Trusted Catalog Update (Priority: P1)

**Goal**: Verify, preview, activate, survive restart, and roll back signed catalog data without changing user-owned state or invoking installers.

**Independent Test**: A valid higher-sequence signed fixture adds a distinct official capability and rolls back; tampered, expired, replayed, downgraded, invalid-schema, alias-conflicting, and interrupted fixtures all fail closed with the prior catalog readable.

### Tests for User Story 2

- [ ] T035 [P] [US2] Write canonical-byte, key-id, signature, digest, issue/expiry, sequence, and envelope-schema tests in `packages/tool_registry/tests/test_catalog_signing.py`
- [ ] T036 [P] [US2] Write snapshot repository bootstrap/candidate/active/previous/retention/recovery tests in `packages/tool_registry/tests/test_catalog_snapshots.py`
- [ ] T037 [P] [US2] Write exact identity/field provenance diff and preview binding tests in `packages/tool_registry/tests/test_catalog_update_preview.py`
- [ ] T038 [P] [US2] Write atomic prior-69-to-signed-Onshape-70 activation/reconciliation/restart/rollback tests with install/custom/disable/credential/workspace sentinels in `packages/tool_registry/tests/test_catalog_activation.py`
- [ ] T039 [P] [US2] Write catalog state, preview, activation, stale-preview, RBAC, rollback, and redacted-error API tests in `apps/api/tests/test_catalog_update_api.py`
- [ ] T040 [P] [US2] Write component tests for no-channel, checking, verified diff, failed verification, activating, history, rollback, and rollback-failed states in `apps/web/src/components/tools/CatalogUpdatePanel.spec.tsx`
- [ ] T041 [P] [US2] Extend the mocked Playwright journey with activation/restart projection/rollback and zero install requests in `tests/ui-integration/capability-library.spec.ts`

### Implementation for User Story 2

- [ ] T042 [US2] Implement canonical JSON, SHA-256 binding, Ed25519 verification, trust-window, sequence, expiry, and size validation in `packages/tool_registry/src/tool_registry/catalog_signing.py`
- [ ] T043 [US2] Implement bundled bootstrap and immutable snapshot/state/retention repository operations in `packages/tool_registry/src/tool_registry/catalog_snapshots.py`
- [ ] T044 [US2] Implement sorted identity/field/provenance diffs and actor/expiry-bound preview digests in `packages/tool_registry/src/tool_registry/catalog_updates.py`
- [ ] T045 [US2] Refactor catalog reconciliation to accept a validated document and an existing transaction while preserving user-owned columns in `packages/tool_registry/src/tool_registry/catalog_reconcile.py`
- [ ] T046 [US2] Implement transactional activate/rollback/recovery audit behavior in `packages/tool_registry/src/tool_registry/catalog_updates.py`
- [ ] T047 [US2] Replace unsafe direct URL loading with bounded approved-channel fetching that rejects unsafe redirects/ambient credentials in `packages/tool_registry/src/tool_registry/canonical_catalog.py`
- [ ] T048 [US2] Add thin catalog state/preview/activate/rollback API routes and administrator authorization dependencies in `apps/api/src/api/routers/mcp.py`
- [ ] T049 [US2] Implement catalog update client methods and redacted typed errors in `apps/web/src/services/mcp-service.ts`
- [ ] T050 [US2] Create administrator catalog state/history/diff/activation/rollback panel in `apps/web/src/components/tools/CatalogUpdatePanel.tsx`
- [ ] T051 [US2] Integrate update status and offline recovery source into `apps/web/src/components/pages/ToolRegistryPage.tsx`
- [ ] T052 [US2] Add structured trace events for fetch, verify, preview, activate, rollback, and recovery in `packages/tool_registry/src/tool_registry/catalog_updates.py`
- [ ] T053 [US2] Run signature, adversarial snapshot, transaction, API, component, and mocked Playwright tests for US2

**Checkpoint**: A new official server can arrive as signed data and be rolled back, with no install/enable/credential/process side effect.

---

## Phase 5: User Story 3 - Add an MCP Through a Guided Flow (Priority: P1)

**Goal**: Normalize supported configuration forms and provide exact, read-only, approval-bound plans for catalog, remote, local, and host-bridge paths.

**Independent Test**: Deterministic local-package, remote-endpoint, and host-bridge fixtures produce exact plans; invalid or secret-bearing imports are redacted; no import or preflight executes, contacts vendors, or registers a server.

### Tests for User Story 3

- [ ] T054 [P] [US3] Write Claude `mcpServers`, VS Code `servers`/`inputs`, and plain-server grammar tests in `packages/tool_registry/tests/test_config_import.py`
- [ ] T055 [P] [US3] Write adversarial secret, header, shell, duplicate, mixed-validity, unknown-field, invalid-URL, oversized, and no-persistence tests in `packages/tool_registry/tests/test_config_import_security.py`
- [ ] T056 [P] [US3] Write Install Plan completeness, canonical digest, expiry, license/terms state and no-Wright-acceptance blocker, material-change, and no-secret tests in `packages/tool_registry/tests/test_install_plans.py`
- [ ] T057 [P] [US3] Write local-package, remote-endpoint, host-bridge, and advanced-local-command adapter contract/rollback/residue tests in `packages/tool_registry/tests/test_onboarding_adapters.py`
- [ ] T058 [P] [US3] Write import preview, plan creation, approve/apply, stale/conflict, role, and redaction API tests in `apps/api/tests/test_mcp_onboarding_api.py`
- [ ] T059 [P] [US3] Write wizard source/normalize/observe/review/credentials/apply/failure state component tests in `apps/web/src/components/tools/OnboardingWizard.spec.tsx`
- [ ] T060 [P] [US3] Write mocked catalog/import/remote/local/host/changed-plan keyboard journeys in `tests/ui-integration/mcp-onboarding.spec.ts`

### Implementation for User Story 3

- [ ] T061 [US3] Implement bounded JSON detection and normalized no-execution drafts with field diagnostics in `packages/tool_registry/src/tool_registry/config_import.py`
- [ ] T062 [US3] Implement secret/header/environment redaction and credential-requirement extraction in `packages/tool_registry/src/tool_registry/config_import.py`
- [ ] T063 [US3] Implement immutable exact Install Plan generation including license/terms state and independent-completion blocker plus digest/expiry/material-change validation in `packages/tool_registry/src/tool_registry/install_plans.py`
- [ ] T064 [US3] Implement adapter protocols and effect/result/rollback contracts in `packages/tool_registry/src/tool_registry/onboarding.py`
- [ ] T065 [P] [US3] Implement isolated local-package/local-command adapter using reviewed literal recipes only in `packages/tool_registry/src/tool_registry/installers/local.py`
- [ ] T066 [P] [US3] Implement bounded remote HTTP/SSE registration and probe adapter in `packages/tool_registry/src/tool_registry/installers/remote.py`
- [ ] T067 [P] [US3] Implement allowlisted proprietary-host detection/add-on/handshake/read-only-probe adapter without host installation in `packages/tool_registry/src/tool_registry/installers/host_bridge.py`
- [ ] T068 [US3] Implement plan repository, approval, idempotent apply, progress, cancellation, rollback, and residue recording in `packages/tool_registry/src/tool_registry/onboarding.py`
- [ ] T069 [US3] Add thin import/plan/approval/apply/run/cancel API routes with request-size limits in `apps/api/src/api/routers/mcp.py`
- [ ] T070 [US3] Implement import, plan, and onboarding-run client methods in `apps/web/src/services/mcp-service.ts`
- [ ] T071 [US3] Replace the custom-server modal with the multi-source guided wizard in `apps/web/src/components/tools/OnboardingWizard.tsx`
- [ ] T072 [US3] Integrate the wizard and current plan/run state into `apps/web/src/components/pages/ToolRegistryPage.tsx`
- [ ] T073 [US3] Add structured redacted traces for import, observation, plan, approval, effects, cancellation, rollback, and residue in `packages/tool_registry/src/tool_registry/onboarding.py`
- [ ] T074 [US3] Run parser/security/plan/adapter/API/component/mocked Playwright tests for US3

**Checkpoint**: All guided sources reach an exact preflight; deterministic backends prove lifecycle and rollback; parsing and preflight have zero effects.

---

## Phase 6: User Story 6 - Preserve Existing User State (Priority: P1)

**Goal**: Prove idempotent forward migration and catalog changes preserve every existing user-owned state class.

**Independent Test**: A legacy database fixture upgrades, activates, restarts, rolls back, and re-runs migration with identical custom entries, install state, disablement, credential references/flags, workspace grants, tools, and legacy aliases.

### Tests for User Story 6

- [ ] T075 [P] [US6] Build a version-12 legacy database fixture containing catalog/custom/install/disable/error/credential/workspace/tool sentinels in `packages/data_vault/tests/fixtures/capability_library_v12.py`
- [ ] T076 [P] [US6] Write migration idempotency, backup, failure recovery, and downgrade-tolerance tests in `packages/data_vault/tests/test_capability_library_migration.py`
- [ ] T077 [P] [US6] Write activate/restart/rollback exact-preservation and removed-catalog-entry tests in `packages/tool_registry/tests/test_catalog_user_state_preservation.py`
- [ ] T078 [P] [US6] Write API compatibility tests for existing server/tool/credential/install/toggle endpoints after migration in `apps/api/tests/test_mcp_backward_compatibility.py`

### Implementation for User Story 6

- [ ] T079 [US6] Add migration backup/diagnostic integration for new capability tables without transforming existing rows in `packages/data_vault/src/data_vault/migrations.py`
- [ ] T080 [US6] Preserve legacy canonical aliases and unresolved/custom identities in active capability projection and reconciliation in `packages/tool_registry/src/tool_registry/capability_views.py`
- [ ] T081 [US6] Preserve existing API models/endpoints and adapt legacy list responses from the active projection where safe in `apps/api/src/api/services/mcp_services.py`
- [ ] T082 [US6] Add restart/bootstrap recovery behavior that never overwrites newer user state in `apps/api/src/api/main.py`
- [ ] T083 [US6] Run legacy migration, exact preservation, API compatibility, and rollback tests for US6

**Checkpoint**: Existing users can adopt or revert catalog snapshots without losing or silently changing user-owned state.

---

## Phase 7: User Story 4 - Validate and Enable for a Workspace (Priority: P2)

**Goal**: Record honest protocol/read-only evidence, collect credentials through the secret boundary, and explicitly enable one workspace without granting invocation authority.

**Independent Test**: A deterministic MCP initializes, lists tools, passes a read-only probe, and is enabled for workspace A only; failed/stale evidence blocks or limits enablement, and raw credentials appear nowhere outside the test secret provider.

### Tests for User Story 4

- [ ] T084 [P] [US4] Write validation transition, required-step, partial, failed, blocked, stale, schema-change, and redaction tests in `packages/tool_registry/tests/test_validation_evidence.py`
- [ ] T085 [P] [US4] Write deterministic initialize/notifications/tools-list/read-only-probe and cancellation tests in `packages/tool_registry/tests/test_validation_runner.py`
- [ ] T086 [P] [US4] Write validation-run and single-workspace enablement scope/role/staleness API tests in `apps/api/tests/test_capability_enablement_api.py`
- [ ] T087 [P] [US4] Write credential-boundary negative scans across snapshot/import/plan/evidence/workspace/workflow/log serialization in `tests/security/test_capability_secret_boundary.py`
- [ ] T088 [P] [US4] Extend wizard/detail component tests for validation evidence and workspace selection in `apps/web/src/components/tools/OnboardingWizard.spec.tsx`
- [ ] T089 [P] [US4] Extend mocked Playwright with validate/credential/workspace-A-versus-B/no-invocation-authority journey in `tests/ui-integration/mcp-onboarding.spec.ts`

### Implementation for User Story 4

- [ ] T090 [US4] Implement append-only ValidationEvidence repository and strict transition/staleness policy in `packages/tool_registry/src/tool_registry/validation_evidence.py`
- [ ] T091 [US4] Implement MCP initialize/discovery and optional catalog-approved read-only probe runner using existing lifecycle boundaries in `packages/tool_registry/src/tool_registry/validation_runner.py`
- [ ] T092 [US4] Add thin validation-run and workspace capability enablement routes while preserving existing workspace authority in `apps/api/src/api/routers/mcp.py`
- [ ] T093 [US4] Integrate configured/not-configured credential booleans without reading values back in `apps/web/src/components/tools/OnboardingWizard.tsx`
- [ ] T094 [US4] Add validation evidence, staleness, limitations, and choose-workspace completion UI in `apps/web/src/components/tools/CapabilityDetails.tsx`
- [ ] T095 [US4] Run validation, gateway lifecycle, secret boundary, workspace isolation, component, and mocked Playwright tests for US4

**Checkpoint**: Honest evidence supports explicit single-workspace availability and never becomes blanket tool-call approval.

---

## Phase 8: User Story 5 - Report a Missing Capability (Priority: P2)

**Goal**: Replace browser prompts with a structured user-owned report kept outside trusted/installable catalog data.

**Independent Test**: Submit vendor/source/domain/task/platform/host/notes from an empty search, preserve visible search context, export/review it separately, and prove refresh cannot promote it to trusted/installable status.

### Tests for User Story 5

- [ ] T096 [P] [US5] Write missing-report validation, storage, idempotency, export, match, and non-promotion tests in `packages/tool_registry/tests/test_missing_capability_reports.py`
- [ ] T097 [P] [US5] Write structured report role, validation, redaction, and no-server-row API tests in `apps/api/tests/test_missing_capability_report_api.py`
- [ ] T098 [P] [US5] Write form validation, preserved search context, success, and failure component tests in `apps/web/src/components/tools/MissingCapabilityForm.spec.tsx`
- [ ] T099 [P] [US5] Extend mocked Playwright with empty-result structured reporting and no prompt usage in `tests/ui-integration/capability-library.spec.ts`

### Implementation for User Story 5

- [ ] T100 [US5] Implement missing-capability report repository and explicit review-state transitions in `packages/tool_registry/src/tool_registry/missing_reports.py`
- [ ] T101 [US5] Replace legacy report-to-server-row behavior with a thin structured report endpoint while keeping a compatibility response where needed in `apps/api/src/api/routers/mcp.py`
- [ ] T102 [US5] Implement typed report client method and remove browser prompt handling in `apps/web/src/services/mcp-service.ts`
- [ ] T103 [US5] Create accessible structured missing-capability form/drawer in `apps/web/src/components/tools/MissingCapabilityForm.tsx`
- [ ] T104 [US5] Integrate report action with empty results and current search/filter context in `apps/web/src/components/pages/ToolRegistryPage.tsx`
- [ ] T105 [US5] Run report repository/API/component/mocked Playwright tests for US5

**Checkpoint**: Missing needs become reviewable user-owned evidence, never an implicitly trusted or installable capability.

---

## Phase 9: Cross-Cutting Hardening and Feature Verification

**Purpose**: Package the feature, document it, prove performance/accessibility/security/recovery, and run the authoritative merge process.

- [ ] T106 [P] Add package-resource and standalone wheel/sdist assertions for schemas, trust metadata, catalog, and cryptographic dependency in `tests/packaging/test_wheel_contents.py` and `tests/test_public_python_distribution.py`
- [ ] T107 [P] Add 1,000-record search and 100-server import bounded-performance tests in `packages/tool_registry/tests/test_capability_performance.py`
- [ ] T108 [P] Add unsafe-channel redirect, size/timeout, no-ambient-credential, replay, and concurrent-writer security tests in `packages/tool_registry/tests/test_catalog_update_security.py`
- [ ] T109 [P] Add local FastAPI plus deterministic child MCP system smoke for the complete add/validate/workspace journey in `tests/e2e/test_capability_onboarding.py`
- [ ] T110 [P] Add live-local Capability Library Playwright smoke to `tests/ui-integration/capability-library.spec.ts` and `tests/ui-integration/mcp-onboarding.spec.ts`
- [ ] T111 Add Onshape Labs source/evidence, signed update operation, rollback, import, compatibility, onboarding, and external-validation follow-up documentation in `docs/mcp-catalog/dynamic-engineering-catalog.md` and `docs/mcp-catalog/mcp-server-setup-recipes.md`
- [ ] T112 Add administrator and engineer Capability Library journeys plus clear discovery/install/enable/invocation terminology in `docs/getting-started/capability-library.md` and `mkdocs.yml`
- [ ] T113 Update `docs/engineering-capability-program-progress.md` with implementation checkpoints, test evidence, commits, rollback proof, and deferred Onshape live validation
- [ ] T114 Run Ruff check/format, focused Python tests, catalog bundle verifiers, web ESLint/Prettier/TypeScript/Vitest, focused Playwright, packaging, strict docs, and `git diff --check`
- [ ] T115 Re-run every acceptance step in `specs/068-capability-library/quickstart.md` and record deterministic versus deferred-live evidence in `docs/engineering-capability-program-progress.md`
- [ ] T116 Re-run `speckit-analyze`, remediate all critical/high findings without changing the constitution, and record any justified medium/low deferrals in `specs/068-capability-library/analysis.md`
- [ ] T117 Mark every completed task in `specs/068-capability-library/tasks.md` and require both checklists in `specs/068-capability-library/checklists/` to remain fully checked
- [ ] T118 Fetch current `origin/dev`, integrate it into `068-capability-library`, resolve conflicts, and rerun `scripts/check-dev-merge.sh` against the exact resulting tree
- [ ] T119 Require a clean worktree, commit intentionally, push `068-capability-library`, merge with `--no-ff` into current `dev`, verify matching feature/merged tree hashes, push `dev`, and verify local/remote commit ids

---

## Dependencies and Execution Order

### Phase dependencies

- Phase 1 has no dependency beyond the committed plan.
- Phase 2 depends on Phase 1 and blocks all stories.
- US1 depends on Phase 2 and supplies the capability projection used by later UI.
- US2 depends on Phase 2; it may proceed independently of US1 domain work but its final UI integration uses US1's page.
- US3 depends on Phase 2 and the capability identity/compatibility contracts from US1.
- US6 depends on US2 activation/reconciliation and must pass before workspace enablement changes.
- US4 depends on US3 plans/adapters and US6 preservation guarantees.
- US5 depends only on Phase 2 for storage and can proceed independently, but final page integration follows US1.
- Phase 9 depends on all desired stories.

### Story completion order

```text
Setup -> Foundation -> US1
                    |-> US2 -> US6
                    `-> US3 ------> US4
                    `-> US5
US1 + US2 + US3 + US6 + US4 + US5 -> Hardening -> Merge
```

### Within each story

1. Add tests and observe the intended failure.
2. Implement models/repositories.
3. Implement domain service behavior.
4. Add thin API routes.
5. Add typed web client and components.
6. Run the independent story checkpoint before moving on.

## Parallel Opportunities

- T002-T005 are independent setup fixtures/resources.
- T008, T011, and T014 are independent foundational contracts after the migration shape is known.
- Within US1, T016-T021 can be authored concurrently; T029-T032 are independent components after response types stabilize.
- Within US2, signing, repository, diff, API, and UI tests are independent; implementation converges at T046.
- Within US3, parser, plan, adapter, API, and UI tests are independent; backend adapters T065-T067 are separate.
- US5 repository/form work can proceed while US4 validation work proceeds.
- Packaging, performance, security, system, and documentation hardening T106-T113 use separate files.

## Parallel Example: User Story 3

```text
Task T054: common-client import grammar tests
Task T056: Install Plan digest/expiry tests
Task T057: onboarding adapter lifecycle tests
Task T059: wizard component-state tests
Task T060: mocked end-to-end onboarding journeys
```

After core contracts pass:

```text
Task T065: local installer adapter
Task T066: remote endpoint adapter
Task T067: host bridge adapter
```

## Implementation Strategy

### MVP first

1. Complete setup and foundation.
2. Complete US1 offline discovery and compatibility.
3. Validate US1 independently before catalog mutation or installer work.

### Incremental delivery

1. US1 delivers trustworthy offline discovery.
2. US2 adds signed data updates and rollback without execution.
3. US3 adds import and exact preflight with deterministic adapters.
4. US6 proves existing users are safe.
5. US4 connects validation to explicit workspace use.
6. US5 closes the missing-capability feedback loop.
7. Cross-cutting gates package and merge the exact feature tree.

## Requirements traceability

| Requirement range | Primary tasks |
|-------------------|---------------|
| FR-001-FR-006 | T016-T034 |
| FR-007-FR-015 | T035-T053, T075-T083 |
| FR-016-FR-025 | T054-T074 |
| FR-026-FR-030 | T084-T095 |
| FR-031 | T096-T105 |
| FR-032-FR-035 | T006-T015, T106-T119 |
| SC-001 | T019-T034, T107 |
| SC-002-SC-003 | T035-T053, T075-T083, T108 |
| SC-004-SC-008 | T054-T095, T107-T110 |
| SC-009 | T112-T115; moderated study remains explicitly deferred |
| SC-010 | T020-T021, T040-T041, T059-T060, T088-T089, T098-T099, T110, T114 |

## Notes

- Keep `.local-run/`, downloaded MCP repositories, build output, caches, credentials, test private keys outside production resources, and model artifacts untracked.
- Test signing keys are fixtures only; production private signing material never enters the repository.
- Live Onshape validation remains optional and externally authorized; deterministic local fixtures are the normal gate.
- Physical actuation remains outside all adapters and tests.
- Commit at logical checkpoints and update the progress log with real commit/test evidence only.
