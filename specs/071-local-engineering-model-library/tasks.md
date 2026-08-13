# Tasks: Local Engineering Model Library

**Input**: Design documents from `specs/071-local-engineering-model-library/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Required. Tests are written and observed failing before implementation for contracts, source/storage safety, lifecycle, runtime/gateway behavior, API/UI, recovery, and external evidence boundaries.

**Organization**: Tasks are grouped by independently testable user story. Loop 071 uses focused gates; the authoritative dev merge gate is deferred until Loops 072-073 finish on `codex/rivet-engineering-program`.

## Phase 1: Setup and public contracts

**Purpose**: Establish a separately packaged model domain without adding model weights or runtime frameworks.

- [x] T001 Create `packages/model_registry/pyproject.toml` and `packages/model_registry/src/model_registry/__init__.py` with only bounded domain/runtime-port dependencies.
- [x] T002 Add `packages/model_registry` to the uv workspace and public wheel/sdist package lists in `pyproject.toml`.
- [x] T003 Copy the finalized package, seeded test-vector, complete install-plan, and operation JSON Schemas into `packages/model_registry/src/model_registry/schemas/`.
- [x] T004 [P] Add package-resource discovery and exact contract-copy tests in `packages/model_registry/tests/test_contract_resources.py`.
- [x] T005 [P] Add valid/invalid public contract fixtures under `packages/model_registry/tests/fixtures/contracts/`.
- [x] T006 Add JSON Schema meta-validation, supported-version, bounds, extra-field, and cross-reference tests in `packages/model_registry/tests/test_contract_schemas.py`.
- [x] T007 Update `uv.lock` and assert the new package adds no ML framework, model hub SDK, driver, compiler, or unsafe serialization dependency.

---

## Phase 2: Foundational domain, policy, persistence, and storage

**Purpose**: Shared trust and state infrastructure that blocks every user story.

- [x] T008 Write failing `BaseTool` conformance plus model/package/variant/artifact/task/license/resource/seeded-test-vector validation and canonical-digest tests in `packages/core/tests/test_base_tool.py` and `packages/model_registry/tests/test_models.py`.
- [x] T009 Implement Wright's abstract `BaseTool` contract in `packages/core/src/core/tools.py` plus immutable model-domain values, supported versions, canonical serialization, bounds, and stable failure categories in `packages/model_registry/src/model_registry/models.py`.
- [x] T010 Export the public domain contracts from `packages/model_registry/src/model_registry/__init__.py` without cyclic package imports.
- [x] T011 [P] Write failing path, format, source, redirect, license, access, platform, architecture, accelerator, resource, physical-actuation, and secret-boundary policy tests in `packages/model_registry/tests/test_policy.py`.
- [x] T012 Implement fail-closed package, artifact, source, license, compatibility, resource, physical-actuation, and redaction policy in `packages/model_registry/src/model_registry/policy.py`.
- [x] T013 Write failing migration-16 upgrade, rollback-on-failure, idempotency, contiguous-version, and legacy-state preservation tests in `packages/data_vault/tests/test_model_library_migration.py`.
- [x] T014 Add migration 16 tables/indexes for model snapshots, plans, operations, content objects, installations, tests, bindings, references, leases, and evidence in `packages/data_vault/src/data_vault/migrations.py`.
- [x] T015 Write failing repository tests for immutable identities, optimistic transitions, idempotency, terminal states, bounded JSON, workspace scope, references, and leases in `packages/data_vault/tests/test_model_repository.py`.
- [x] T016 Implement `ModelRepository` and transaction-safe state transitions in `packages/data_vault/src/data_vault/model_repository.py`.
- [x] T017 Export model repository values from `packages/data_vault/src/data_vault/__init__.py` and preserve existing import contracts.
- [x] T018 Write failing content-store tests for safe roots, staging, digest promotion, immutability, deduplication, concurrent writers, quarantine, missing content, atomic activation, and cleanup in `packages/data_vault/tests/test_model_artifact_store.py`.
- [x] T019 Implement Wright-root-confined staging, verified CAS, installation views, quarantine, leases, and atomic promotion in `packages/data_vault/src/data_vault/model_artifact_store.py`.
- [x] T020 Add crash/restart reconciliation tests at every content and database transition in `packages/data_vault/tests/test_model_artifact_recovery.py`.
- [x] T021 Implement database/filesystem reconciliation with truthful missing, quarantine, residue, and recovery projections in `packages/data_vault/src/data_vault/model_artifact_store.py`.
- [x] T022 [P] Add deterministic fixture package/upgrade/archive generation helpers that write only temporary test state in `packages/model_registry/tests/fixture_factory.py`.
- [x] T023 [P] Add shared injected clock, host-observation, disk/resource, secret-reference, and transport doubles in `packages/model_registry/tests/fakes.py`.
- [x] T024 Add cross-package secret/path/authority serialization scans plus structured-log and OpenTelemetry trace contract tests for model records, source/storage/database transitions, adapter/gateway calls, cancellations, cleanup, evidence, and exports in `tests/security/test_engineering_model_boundaries.py`.

**Checkpoint**: Contracts, policy, migration, repository, generated fixtures, and content store work offline and independently.

---

## Phase 3: User Story 1 - Evaluate a model before changing the machine (Priority: P1) MVP

**Goal**: Engineers can browse and understand cached model trust, usefulness, compatibility, resources, and blockers without a download or runtime start.

**Independent Test**: Load a bundled catalog with ready, provisional, gated, unsafe, and incompatible entries; filter/inspect it offline and prove zero source/runtime calls.

### Tests first

- [x] T025 [P] [US1] Write failing catalog schema/resource/duplicate/version/canonical-digest tests in `packages/model_registry/tests/test_catalog.py`.
- [x] T026 [P] [US1] Write failing evidence-facet, readiness, compatibility, blocker/recovery, sorting, filtering, pagination, and offline-freshness tests in `packages/model_registry/tests/test_catalog_views.py`.
- [x] T027 [P] [US1] Write failing API contract/RBAC/zero-side-effect tests for catalog list/detail in `apps/api/tests/test_engineering_model_catalog_api.py`.
- [x] T028 [P] [US1] Write failing web client/filter/state tests in `apps/web/tests/engineering-model-service.spec.ts`.
- [x] T029 [P] [US1] Write failing component tests for task, trust, license, resources, evidence, limitations, blocked recovery, offline, keyboard, and narrow layouts in `apps/web/tests/EngineeringModelLibraryPage.spec.tsx`.

### Implementation

- [x] T030 [US1] Implement package-owned catalog loading, semantic validation, canonical snapshots, and safe readiness projections in `packages/model_registry/src/model_registry/catalog.py`.
- [x] T031 [US1] Add catalog metadata for the generated Wright affine fixture and representative gated/unsafe/incompatible entries in `packages/model_registry/src/model_registry/catalog/catalog.yaml`.
- [x] T032 [US1] Add the provisional exact-revision PointNet metadata and Gate D blockers without weights or installable status in `packages/model_registry/src/model_registry/catalog/catalog.yaml`.
- [x] T033 [US1] Implement filtered/paginated inspection and host-compatibility composition in `packages/workspace_service/src/workspace_service/engineering_model_service.py`.
- [x] T034 [US1] Add bounded catalog/detail response models in `apps/api/src/api/schemas/engineering_models.py`.
- [x] T035 [US1] Add thin authenticated read-only catalog/detail routes that delegate immediately to an injected `EngineeringModelApplicationPort` in `apps/api/src/api/routers/engineering_models.py` and `packages/tool_registry/src/tool_registry/model_library_port.py`.
- [x] T036 [US1] Wire the model catalog and read service into `apps/api/src/api/composition.py` without contacting sources at startup.
- [x] T037 [US1] Implement typed catalog/detail/filter clients in `apps/web/src/services/engineering-model-service.ts`.
- [x] T038 [P] [US1] Implement reusable model trust/readiness/resource/evidence primitives in `apps/web/src/components/models/ModelTrustPrimitives.tsx`.
- [x] T039 [US1] Implement the dedicated library/detail/filter/offline page, including exact generated-fixture recipe/inputs/constraints/digests and honest external source provenance, in `apps/web/src/components/pages/EngineeringModelLibraryPage.tsx`.
- [x] T040 [US1] Add a distinct Engineering Models route/navigation entry while preserving `/setup/model` in `apps/web/src/App.tsx` and `apps/web/src/components/layout/Sidebar.tsx`.

**Checkpoint**: User Story 1 is a useful offline no-mutation MVP and remains separate from conversational model setup.

---

## Phase 4: User Story 2 - Acquire and install a verified model safely (Priority: P1)

**Goal**: An exact preview drives bounded online/offline acquisition, verification, deduplication, and atomic activation; interruption never appears ready.

**Independent Test**: The generated fixture traverses online-style and offline paths; resume/cache/cancel/fault cases are deterministic and leave correct state.

### Tests first

- [x] T041 [P] [US2] Write failing immutable/expiring/principal-bound effect-plan tests for exact network/token/license/runtime requirements, compatibility, prompts, locations, bytes, references, rollback, cleanup, and every invalidation condition in `packages/model_registry/tests/test_planning.py`.
- [x] T042 [P] [US2] Write failing bounded HTTPS/source tests for exact revision/files, redirects, auth stripping, content length, streaming ceiling, truncation, digest, timeout, and cancellation in `packages/model_registry/tests/test_http_source.py`.
- [x] T043 [P] [US2] Write failing range-resume tests for strong validators, `If-Range`, `206 Content-Range`, changed representation, restart, and zero-byte cache reuse in `packages/model_registry/tests/test_http_resume.py`.
- [x] T044 [P] [US2] Write failing offline archive tests for paths, normalization collisions, links, executables, nested archives, undeclared files, expansion, formats, checksums, and license in `packages/model_registry/tests/test_offline_import.py`.
- [x] T045 [P] [US2] Write failing lifecycle tests for plan confirmation, acquire/import, verify, install, cancellation, disk exhaustion, concurrency, atomic activation, idempotency, and cleanup in `packages/model_registry/tests/test_install_lifecycle.py`.
- [x] T046 [P] [US2] Write failing plan/confirm/operation/events/cancel API tests in `apps/api/tests/test_engineering_model_install_api.py`.
- [x] T047 [P] [US2] Write failing plan/progress/cancel/failure/recovery component tests in `apps/web/tests/EngineeringModelInstallFlow.spec.tsx`.

### Implementation

- [x] T048 [US2] Implement canonical expiring effect planning with explicit requirements/compatibility/prompts/rollback/cleanup and digest-bound one-time confirmation in `packages/model_registry/src/model_registry/planning.py`.
- [x] T049 [US2] Define injected source/stream/resume/offline-package ports and bounded transfer records in `packages/model_registry/src/model_registry/sources.py`.
- [x] T050 [US2] Implement approved HTTPS acquisition, safe redirects, validator-bound resume, byte ceilings, digest verification, and opaque token references in `packages/model_registry/src/model_registry/http_source.py`.
- [x] T051 [US2] Implement safe offline package inspection/extraction through the same artifact policy in `packages/model_registry/src/model_registry/offline_source.py`.
- [x] T052 [US2] Implement durable acquire/import/verify/install/cancel/cleanup state machines and cache reuse in `packages/model_registry/src/model_registry/lifecycle.py`.
- [x] T053 [US2] Compose authenticated plan/confirm/operation/cancel/import use cases in `packages/workspace_service/src/workspace_service/engineering_model_service.py`.
- [x] T054 [US2] Add plan, operation, progress, failure, and confirmation schemas in `apps/api/src/api/schemas/engineering_models.py`.
- [x] T055 [US2] Add thin plan/confirm/operation/SSE/cancel/import routes in `apps/api/src/api/routers/engineering_models.py`.
- [x] T056 [US2] Implement typed plan/operation/event/cancel/import methods in `apps/web/src/services/engineering-model-service.ts`.
- [x] T057 [US2] Implement effects review, progress, cancellation, blocker, cleanup, and recovery patterns in `apps/web/src/components/models/EngineeringModelInstallFlow.tsx`.
- [x] T058 [US2] Integrate install/import actions into `apps/web/src/components/pages/EngineeringModelLibraryPage.tsx` without implicit runtime/source effects.

**Checkpoint**: Generated packages install atomically from deterministic sources; every negative acquisition/import case fails closed.

---

## Phase 5: User Story 3 - Prove readiness and use a typed capability (Priority: P1)

**Goal**: Mandatory tests prove an exact adapter/model contract, then one workspace can discover/call it through Wright's gateway while other authority paths fail.

**Independent Test**: A separate deterministic adapter runs positive/negative vectors and one reviewed Rivet call; cross-workspace, stale, invalid, cancelled, and direct attempts fail.

### Tests first

- [x] T059 [P] [US3] Write failing adapter identity/contract/format/task/platform/provider/health/verify/progress tests in `packages/model_registry/tests/test_runtime_adapter.py`.
- [x] T060 [P] [US3] Add a protocol-conformant deterministic child adapter with verify/load/infer/progress/cancel/unload/shutdown and fault profiles in `tests/fixtures/engineering_model_runtime.py`.
- [x] T061 [P] [US3] Write failing runtime-supervisor tests for clean environment, artifact confinement, verification, monotonic redacted progress, message/output bounds, resources, deadlines, crash, cancellation, late output, unload, shutdown, and residue in `packages/model_registry/tests/test_runtime_supervisor.py`.
- [x] T062 [P] [US3] Write failing vector evaluation tests for deterministic seed, limitation coverage, input/output schema digests, units/coordinates, exact/range/absolute/relative/category predicates, finite values, tolerance, timing, and split material/observation evidence digests in `packages/model_registry/tests/test_model_testing.py`.
- [x] T063 [P] [US3] Write failing generic provider collision/discovery/call/cancel/session-close/backward-compatibility tests in `packages/tool_registry/tests/test_gateway_capability_providers.py`.
- [x] T064 [P] [US3] Write failing model provider tests for exact healthy workspace bindings, typed schemas, stale/disabled/cross-workspace hiding, policy, audit, and identity evidence in `packages/model_registry/tests/test_gateway_provider.py`.
- [x] T065 [P] [US3] Write failing installation-test and workspace-binding API tests in `apps/api/tests/test_engineering_model_runtime_api.py`.
- [x] T066 [P] [US3] Write failing component tests for standard test evidence, resource rejection, enablement, stale bindings, and recovery in `apps/web/tests/EngineeringModelRuntimePanel.spec.tsx`.
- [x] T067 [US3] Write a failing real Rivet-worker/system test for typed model discovery/call/cancellation through GatewayService in `tests/e2e/test_rivet_engineering_models.py`.

### Implementation

- [x] T068 [US3] Implement the adapter registry, verify/progress protocol records, supervisor, process ownership, deadlines, cancellation, and cleanup in `packages/model_registry/src/model_registry/runtime.py`.
- [x] T069 [US3] Implement mandatory seeded test-vector validation/evaluation and bounded evidence with deterministic material and variable observation digests in `packages/model_registry/src/model_registry/testing.py`.
- [x] T070 [US3] Add `GatewayCapabilityProvider`, `EngineeringModelApplicationPort`, and progress/cancel protocol types in `packages/tool_registry/src/tool_registry/gateway_ports.py` and `packages/tool_registry/src/tool_registry/model_library_port.py`.
- [x] T071 [US3] Integrate unique provider discovery/call/policy/audit/cancellation/session-close/shutdown in `packages/tool_registry/src/tool_registry/gateway_service.py` without changing existing MCP behavior.
- [x] T072 [US3] Implement `EngineeringModelTool(BaseTool)`, workspace-scoped model tool projection, and runtime invocation in `packages/model_registry/src/model_registry/model_tool.py` and `packages/model_registry/src/model_registry/gateway_provider.py`.
- [x] T073 [US3] Compose standard-test, enable/disable, binding, provider, and supervisor services with structured `structlog` events and OpenTelemetry spans in `packages/workspace_service/src/workspace_service/engineering_model_service.py`.
- [x] T074 [US3] Wire the dynamic provider into the existing gateway composition in `apps/api/src/api/composition.py`.
- [x] T075 [US3] Add test/evidence/binding request and response models in `apps/api/src/api/schemas/engineering_models.py`.
- [x] T076 [US3] Add thin standard-test/evidence/workspace-binding routes in `apps/api/src/api/routers/engineering_models.py`.
- [x] T077 [US3] Implement test/evidence/binding client methods and runtime status patterns in `apps/web/src/services/engineering-model-service.ts` and `apps/web/src/components/models/EngineeringModelRuntimePanel.tsx`.
- [x] T078 [US3] Integrate test and workspace enablement into `apps/web/src/components/pages/EngineeringModelLibraryPage.tsx` with exact evidence and recovery.

**Checkpoint**: Exact ready models become typed workspace capabilities; Rivet calls them only through Wright's governed gateway.

---

## Phase 6: User Story 4 - Update, roll back, remove, and move models predictably (Priority: P2)

**Goal**: Semantic updates preserve the working revision, rollback reuses verified content, export/import works offline, and reference-safe removal never breaks reproducibility.

**Independent Test**: Two generated revisions cover failed/successful update, rollback, deterministic export/import, uninstall, blocked purge, detach/archive, leases, and final cleanup.

### Tests first

- [ ] T079 [P] [US4] Write failing semantic update-diff tests for license, artifacts, adapter, schemas, units, coordinates, resources, vectors, limitations, and redistribution in `packages/model_registry/tests/test_model_updates.py`.
- [ ] T080 [P] [US4] Write failing update failure, atomic successor activation, rollback/retest, and cached-content tests in `packages/model_registry/tests/test_model_updates.py`.
- [ ] T081 [P] [US4] Write failing durable reference/lease, disable, uninstall, purge-blocker, detach/archive, exact reclaimable-byte preview, cancellable cleanup, restart recovery, and cleanup tests in `packages/model_registry/tests/test_model_removal.py`.
- [ ] T082 [P] [US4] Write failing deterministic public export/private exclusion/redistribution and fresh-root re-import tests in `packages/model_registry/tests/test_offline_export.py`.
- [ ] T083 [P] [US4] Write failing update/rollback/reference/export/uninstall/purge API tests in `apps/api/tests/test_engineering_model_maintenance_api.py`.
- [ ] T084 [P] [US4] Write failing compare/update/rollback/reference/removal/export component tests in `apps/web/tests/EngineeringModelMaintenance.spec.tsx`.

### Implementation

- [ ] T085 [US4] Implement semantic revision comparison and update/rollback orchestration in `packages/model_registry/src/model_registry/lifecycle.py`.
- [ ] T086 [US4] Implement reference/lease-aware disable, uninstall, purge, detach/archive, exact reclaimable-byte preview, cancellable cleanup, and restart recovery in `packages/model_registry/src/model_registry/lifecycle.py`.
- [ ] T087 [US4] Implement deterministic policy-aware offline export in `packages/model_registry/src/model_registry/offline_source.py`.
- [ ] T088 [US4] Compose maintenance/reference/export use cases in `packages/workspace_service/src/workspace_service/engineering_model_service.py`.
- [ ] T089 [US4] Add maintenance/reference/export schemas and thin routes in `apps/api/src/api/schemas/engineering_models.py` and `apps/api/src/api/routers/engineering_models.py`.
- [ ] T090 [US4] Implement maintenance client methods and compare/reference/removal/export UI in `apps/web/src/services/engineering-model-service.ts` and `apps/web/src/components/models/EngineeringModelMaintenance.tsx`.
- [ ] T091 [US4] Integrate maintenance journeys into `apps/web/src/components/pages/EngineeringModelLibraryPage.tsx` with blocked purge and rollback focus recovery.

**Checkpoint**: Lifecycle changes are reversible and portable, and content deletion is evidence/reference safe.

---

## Phase 7: User Story 5 - Extend the library without weakening trust (Priority: P2)

**Goal**: Maintainers add packages/adapters through public versioned contracts and deterministic conformance rather than model-specific service code.

**Independent Test**: A test-only package/adapter traverses the normal lifecycle; duplicate, unsupported, unsafe, unknown-license, undeclared, and schema-incompatible extensions fail before acquisition.

- [ ] T092 [P] [US5] Write failing package/adapter full-lifecycle extension, no-lifecycle-service-edit, duplicate identity, unknown version, unsafe format, incomplete license, and schema mismatch tests in `packages/model_registry/tests/test_extensions.py`.
- [ ] T093 [US5] Expose documented duplicate-safe catalog, source, adapter, and predicate registry interfaces in `packages/model_registry/src/model_registry/extensions.py`.
- [ ] T094 [US5] Add a package/adapter conformance runner that uses only generated fixtures in `packages/model_registry/src/model_registry/conformance.py`.
- [ ] T095 [US5] Write command tests first, then add catalog and adapter validation commands to `tests/test_cli.py` and `src/wright_engineering/cli.py` without acquiring content or starting unapproved runtimes.
- [ ] T096 [US5] Document model package authoring, adapter conformance, format/license review, and no-weight fixture generation in `docs/models/local-engineering-models.md`.

**Checkpoint**: New engineering model types follow one safe lifecycle and unknown extensions fail closed.

---

## Phase 8: Cross-story journeys, external evidence, and hardening

- [ ] T097 Add mocked Playwright journeys for an instrumented under-two-minute no-download decision path, offline discovery, blocked candidate, install/cancel/recovery, test/enable, update/rollback, export, and reference-blocked purge in `tests/ui-integration/engineering-model-library.spec.ts`.
- [ ] T098 Add keyboard-only, focus trap/restore, live-region, non-color status, narrow-width, and 200% zoom coverage with no serious/critical findings in `tests/ui-integration/engineering-model-library.spec.ts`.
- [ ] T099 Add local FastAPI + deterministic source + isolated adapter + gateway + real Rivet worker lifecycle coverage in `tests/e2e/test_engineering_model_library.py`.
- [ ] T100 Add hostile manifest/archive/source/adapter/API concurrency, physical-actuation rejection, structured logging/tracing, field-bound, and redaction coverage in `tests/security/test_engineering_model_boundaries.py`.
- [ ] T101 Add performance tests for 1,000-entry discovery under 500 ms p95, 100-file planning/manifest validation under one second p95, 1,000-artifact validation, cancellation delivery, gateway overhead, and bounded evidence in `packages/model_registry/tests/test_performance.py`.
- [ ] T102 Add migration 15-to-16, existing Gateway/MCP/Rivet, conversational model setup, backup/restore, native package, and Docker compatibility regressions in `tests/compatibility/test_engineering_model_compatibility.py`.
- [ ] T103 Resolve Gate D using primary sources and actual artifacts: approve PointNet only if every condition passes, otherwise select and validate a safer public external engineering model; record the decision in `specs/071-local-engineering-model-library/contracts/gate-d-decision.md` and `docs/models/local-engineering-models.md`.
- [ ] T104 Run the goal-authorized bounded exact-revision public external-model probe under `.local-run/`, exercise catalog-through-offline-removal lifecycle with real vectors, and record artifact/runtime/vector/cleanup evidence without staging payloads in `docs/model-evidence/external-model-validation-2026-08-13.md`.
- [ ] T105 Add no-model-weight, unsafe-format, source-code, secret, raw-path, runtime-command, and physical-actuation public artifact scans in `tests/security/test_engineering_model_distribution.py`.
- [ ] T106 Add wheel/sdist/runtime-package assertions for model schemas/catalog/docs-required resources and absence of payloads in `tests/packaging/test_engineering_model_package.py`.

---

## Phase 9: Focused validation and handoff

- [ ] T107 Run affected Python Ruff lint/format and resolve all findings under `packages/model_registry/`, `packages/data_vault/`, `packages/workspace_service/`, `packages/tool_registry/`, and `apps/api/`.
- [ ] T108 Run the model-registry, data-vault, workspace-service, tool-registry, API, E2E, security, compatibility, and packaging focused tests under `packages/`, `apps/api/tests/`, and `tests/`.
- [ ] T109 Run TypeScript, ESLint, Prettier, Vitest, production build, and Loop 071 Playwright journeys from `apps/web/` and `tests/ui-integration/engineering-model-library.spec.ts`.
- [ ] T110 Run JSON Schema, docs strict build, bundle/resource, lock/dependency, public leak, and `git diff --check` validation.
- [ ] T111 Perform Spec Kit cross-artifact analysis across `specs/071-local-engineering-model-library/`, remediate every critical/high finding, and rerun until clean.
- [ ] T112 Update `docs/engineering-capability-program-progress.md`, mark Loop 071 tasks/spec complete, and commit focused evidence on the integration branch.
- [ ] T113 Defer the authoritative `scripts/check-dev-merge.sh`, integration-branch push, no-ff merge to `dev`, and `dev` push until Loop 073 closeout.

## Dependencies and execution order

- Phase 1 precedes Phase 2; Phase 2 blocks every story.
- US1 is the no-mutation MVP. US2 needs shared foundation but not the UI implementation of US1. US3 needs an installed generated fixture from US2. US4 needs lifecycle/install/runtime identities from US2-US3. US5 can begin after Phase 2 and is validated after lifecycle paths exist.
- Cross-story browser/system/security/compatibility work follows stable APIs and UI. Focused validation follows all desired stories.
- Tests in every story are written and observed failing before their corresponding implementation.
- `[P]` tasks touch independent files or test seams and could be split across a future team. This unattended run executes them sequentially on one shared integration branch.

## Parallel examples

- **US1**: catalog policy/view tests, API tests, web client tests, and component tests can be authored in parallel before catalog/service implementation.
- **US2**: planning, HTTP, resume, offline archive, lifecycle, API, and UI test files are independent.
- **US3**: adapter, supervisor, vector, generic gateway, model provider, API, and UI tests can be authored independently before integration.
- **US4**: update, removal, export, API, and UI tests are separable.

## Implementation strategy

1. Establish public contracts and the safe embedded storage foundation.
2. Deliver offline catalog evaluation as a no-mutation MVP.
3. Add generated-fixture acquisition and atomic install.
4. Add the isolated deterministic runtime and gateway-mediated Rivet capability.
5. Add update/rollback/export/reference-safe removal and extension contracts.
6. Complete UI/system/security/package evidence and record the honest external-candidate result.
7. Run Loop 071 focused gates only. Preserve the single expensive authoritative dev gate and merge for Loop 073 program closeout.
