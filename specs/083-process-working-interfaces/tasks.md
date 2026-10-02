# Tasks: Process working interfaces

**Input:** [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md),
[data-model.md](data-model.md), contracts and [acceptance-cases.md](acceptance-cases.md).
**Authority:** Execute after submission of [implementation-goal.md](implementation-goal.md).
Task checkboxes below record implementation progress. Test tasks are required by
this feature specification; none were added or run during planning. New source
paths are intended ownership.

## Phase 1 — Setup / M0

- [x] T001 Create `codex/083-process-working-interfaces` safely, record dirty-file/runtime/context baselines in `specs/083-process-working-interfaces/progress.md`, then activate `.specify/feature.json` and managed `AGENTS.md` context for 083 while retaining 082 history and stable guidance.
- [x] T002 Inspect served editor/source/native boundaries and current source-run/agent/surface contracts; record exact extension map and build/flags in `specs/083-process-working-interfaces/evidence/baseline.md` without replacing the refined editor.
- [x] T003 Preflight default model/scoped adapter, authoring compiler, gateway and selected engineering providers; record actual capabilities/missing resources and owned ports/roots in `specs/083-process-working-interfaces/evidence/prerequisites.md`.
- [x] T004 Freeze isolated proof inputs/bindings and exact test-only decision policy in `examples/process-interfaces/proof-bindings.json`, preserving original assignments and protected campaign subjects; record artifact digests in `specs/083-process-working-interfaces/evidence/proof-scope.md`.

## Phase 2 — Foundation / M1 prerequisites

- [x] T005 Define shared versioned interaction/input/UI/role shapes and generated schema fixtures in `packages/core/src/core/process_interactions.py`, `packages/core/src/core/process_interfaces.py` and `packages/core/tests/test_process_interface_contracts.py` from the three feature contracts.
- [x] T006 Add additive snapshots/start/response receipts and UI/job repositories in `packages/data_vault/src/data_vault/process_input_repository.py`, `process_interface_repository.py` and `migrations.py`; cover old database/record migration in `packages/data_vault/tests/test_process_interface_migrations.py`.
- [x] T007 Establish service boundaries/trace/error/redaction/limits in `packages/workspace_service/src/workspace_service/process_interfaces/` and wire owning services through `packages/workspace_service/src/workspace_service/service.py` without transport imports.
- [x] T008 Add pure projection/currentness tests for source/results/082 reviews/permitted actions and missing evidence in `packages/workspace_service/tests/test_process_interaction_projection.py`.
- [x] T009 Implement interaction projection over existing authorities in `packages/workspace_service/src/workspace_service/process_interfaces/projection.py`, preserving exact subjects, observed freshness and unsupported capabilities.
- [x] T010 Register thin authenticated route/schema composition in `apps/api/src/api/routers/process_interfaces.py`, `apps/api/src/api/schemas/process_interfaces.py` and `apps/api/src/api/main.py`; preserve existing workspace mount/auth/origin/RBAC.

**Checkpoint:** Versioned projections/storage/API authority exist without a new executor.

## Phase 3 — US1: Prepare and carry out a process / M1–M2

**Independent verification:** Common view runs a prepared supported process, shows
real outputs and reattaches after close/disconnect without dispatch replay.

- [x] T011 [US1] Add missing-later-input/upstream-producer/file/schema/option-staleness tests in `packages/workspace_service/tests/test_process_input_readiness.py`.
- [x] T012 [US1] Implement immutable run input overlays and supported-path readiness in `packages/workspace_service/src/workspace_service/process_interfaces/inputs.py`, `readiness.py`, `workflow_run_preparation.py` and `workflow_source_execution.py` without rewriting accepted source.
- [x] T013 [US1] Add durable start/lost-ack/disconnect/explicit-cancel/restart fixtures in `apps/api/tests/test_process_interface_run_lifecycle.py` and `packages/workspace_service/tests/test_process_run_supervisor.py`.
- [x] T014 [US1] Implement bounded backend-owned source-run task/lease supervision, durable start receipts and event attachment in `packages/workspace_service/src/workspace_service/process_interfaces/runs.py`; call the existing executor/recorder and reconstruct interrupted/waiting state safely.
- [x] T015 [US1] Adapt legacy source-start stream and new start/status/event/cancel routes in `apps/api/src/api/routers/workspace.py` and `process_interfaces.py` to detach observers without cancelling execution; reuse existing reviews/validation/result reads.
- [x] T016 [US1] Map finite external-operation observations/reconciliation in `packages/workspace_service/src/workspace_service/workflow_async_operations.py` and `process_interfaces/projection.py`, retaining null unavailable metrics and actual cancellation outcome.
- [x] T017 [US1] Build typed public client with native transport, cursor reconciliation and schema fixtures in `packages/process_client/`; add npm local dependency/lock wiring in `apps/web/package.json` without a new package manager.
- [x] T018 [US1] Extract themed accessible inputs/image thumbnails/progress/findings/review/actions/results/navigation patterns into `packages/ui_kit/`, adapting existing tokens and format viewers without private `apps/web` imports.
- [x] T019 [US1] Implement native common working view in `apps/web/src/components/process-interfaces/CommonProcessView.tsx` using the public client/kit, including required reasons, exact evidence and optional-capability fallback.
- [x] T020 [US1] Integrate typed process tabs/restore/deep links in `apps/web/src/components/chat/WorkspacePanel.tsx`, `EditorTabs.tsx` and `apps/web/src/store/viewer.tsx`; preserve existing workflow/file/editor state and close-without-cancel.
- [ ] T021 [US1] Verify common-view component states, mocked journey and reconnect/navigation in `apps/web/src/components/process-interfaces/CommonProcessView.spec.tsx` and `tests/ui-integration/process-common-view.spec.ts`, recording actual served-workspace checks in `specs/083-process-working-interfaces/evidence/common-view.md`.

## Phase 4 — US2: Deliberate interaction / M1 completion

**Independent verification:** Two declared barriers survive service reopen and
consume responses once on the same run; undeclared questions never create forms.

- [x] T022 [US2] Add source round-trip/schema/dependency tests for declared structured input and unsupported arrangements in `packages/workspace_service/tests/test_process_human_input_source.py`.
- [x] T023 [US2] Implement accepted-source input metadata and `human-input` declaration/compiler barriers in `packages/workspace_service/src/workspace_service/workflow_source_execution.py` and `workflow_sources.py`, preserving source grammar/port validation.
- [x] T024 [US2] Implement v3 checkpoint/response persistence and same-run consumption in `packages/workspace_service/src/workspace_service/workflow_execution_continuation.py`, `process_interfaces/interactions.py` and `packages/data_vault/src/data_vault/workflow_continuation_repository.py`; preserve v2 approval restoration.
- [x] T025 [US2] Enforce undeclared-question diagnostics and unattended step policy in `packages/workspace_service/src/workspace_service/workflow_mcp_execution.py` and `workflow_source_execution.py`, retaining bounded existing 082 repair scope.
- [x] T026 [US2] Add bounded approved `mcp-operation` dispatch through current gateway/consume authority in `packages/workspace_service/src/workspace_service/workflow_approval_execution.py` and `workflow_external_actions.py`; test rejection/unknown outcome with a nonphysical isolated provider.
- [x] T027 [US2] Wire declared input/review/action forms and inspector/source edits through `apps/web/src/components/process-interfaces/` and `apps/web/src/prototypes/workflow-recovery/`, retaining exact checkpoint and subject context.
  Scoped review/action owners, native client/transport, supervised continuation,
  common-view forms and durable explicit-request reconciliation are implemented.
  Inspector declarations are implemented and component/source checks pass;
  served inspector acceptance and actual saved-source compiler/readiness checks
  now pass. Later authoring/live acceptance obligations remain separate.
- [x] T028 [US2] Verify two-checkpoint reopen/duplicate/stale/schema/unknown-outcome/undeclared-question paths in `apps/api/tests/test_process_interface_checkpoints.py`, `packages/workspace_service/tests/test_process_interface_continuation.py` and `tests/ui-integration/process-declared-interactions.spec.ts`; record scope in `specs/083-process-working-interfaces/evidence/interactions.md`.

## Phase 5 — US3: Wright creates and maintains the UI / M3

**Independent verification:** Actual default-model generation through Wright,
isolated preview/save/update/rollback and second-run reuse with no fresh build.

- [x] T029 [US3] Add backward-compatible scoped invocation context/capability reporting in `packages/agent_adapters/src/agent_adapters/base.py` and `hermes.py`; verify effective instructions every turn/default model/no broad tool activation in `packages/agent_adapters/tests/test_process_ui_author_role.py`.
- [x] T030 [US3] Package versioned role/API/kit instructions, structured output schema and a useful reference template in `packages/workspace_service/src/workspace_service/process_interfaces/resources/`, with actual resolved provenance and no arbitrary authoring tools.
- [x] T031 [US3] Implement durable generate/update/cancel job with bounded diagnostic repair budget in `packages/workspace_service/src/workspace_service/process_interfaces/authoring.py`, invoking BaseAgentEngine without changing global model/gateway configuration.
- [x] T032 [US3] Implement fixed static-app binding/path/import validator and compiler envelope in `packages/workspace_service/src/workspace_service/process_interfaces/build.py` with packaged public client/kit distributions; reject model scripts/plugins/backends/launch commands.
- [x] T033 [US3] Implement immutable source/bundle/report revisions, save/compatibility/activate/rollback in `packages/workspace_service/src/workspace_service/process_interfaces/artifacts.py` and `compatibility.py`; distinguish layout edits from engineering input invalidation.
  Owner-level controlled checks pass. The preview observation is synthetic;
  actual managed browser authority and preview/save/update proof remain T034–T042.
  T032's packaged public client/kit sources and installed fixed compiler now pass
  native wheel/source-archive checks; see `evidence/live-ui-authoring.md`.
- [ ] T034 [US3] Add installed generic static asset runtime and internal manifest generation in `packages/workspace_service/src/workspace_service/surfaces/`, using existing isolated origins/bootstrap/limits and no model-selected process launch.
- [x] T035 [US3] Extend closed managed capability/grant contracts in `packages/core/src/core/surfaces/live_app_manifest.py` and existing surface grant services for bounded process operations, preserving MCP App same-server grants.
- [x] T036 [US3] Implement reserved presentation-bound `/__wright/process` bridge in `apps/api/src/api/routers/surface_preview.py` and `apps/api/src/api/surface_route_authority.py`; derive process/UI/run/workspace scope on server and delegate owning services.
  Exact immutable artifact/grant/native-owner API checks pass; see
  `evidence/surface-bridge.md`. T034/T037 remain pending managed presenter creation,
  native handshake and actual browser integration; T040 retains the broader audit.
- [ ] T037 [US3] Add preview-origin transport/theme/navigation handshake in `packages/process_client/` and `apps/web/src/services/surfaces/`, exposing no bearer credentials or generic invokeTool.
- [x] T038 [US3] Expose authoring capability/generation/status/preview/save/update/rollback routes through `apps/api/src/api/routers/process_interfaces.py` with durable request identities and exact revision validation.
  Native API and existing managed presentation/grant owners pass controlled
  checks, including two durable-run reuse and close-without-cancel. T034/T037
  retain actual managed browser and host handshake obligations; T039–T042
  retain workspace controls and live-model authoring acceptance.
- [x] T039 [US3] Implement Create/Update interface progress, preview/save controls and compatibility fallback in `apps/web/src/components/process-interfaces/InterfaceAuthoringPanel.tsx`, explicitly using current document tabs/LiveAppSurface rather than a new browser window. Source/component integration is checked in `evidence/workspace-authoring-controls.md`; actual served/browser and live-model acceptance remains T034/T037/T041/T042.
- [x] T040 [US3] Add scope/build/binding/malformed-source/revocation/cross-workspace/run/UI tests in `packages/workspace_service/tests/test_process_ui_authoring.py` and `apps/api/tests/test_process_ui_surface_authority.py`.
  The resumed combined owner/build/API/surface-security group passes 149 tests,
  no skips. Exact identities, revoked/expired grants, preview mutations,
  malformed inputs, corrupt bundles and bounded repair/build/cancellation are
  checked. This is controlled boundary verification; broader served engineering,
  installed distribution and T053 acceptance remain separate obligations. See
  `evidence/verification.md`.
- [ ] T041 [US3] Verify generation/preview/save/update/reuse/theme/accessibility/loading/error states in `apps/web/src/components/process-interfaces/InterfaceAuthoringPanel.spec.tsx` and `tests/ui-integration/process-ui-authoring.spec.ts`.
- [x] T042 [US3] Run an actual configured-model authoring smoke through Wright and retain prompts/role/model/build/preview/save/update evidence in `specs/083-process-working-interfaces/evidence/live-ui-authoring.md`; reference app alone cannot complete this task.
  Actual model/compiler/managed browser smoke passed with fresh generation,
  loaded preview/save, focused update, saved reopen, theme/reload and rollback.
  Workspace chrome/source discovery were controlled; engineering execution and
  the two tailored live tool-chain proofs remain separate T043–T047 obligations.

## Phase 6 — US4: Different engineering jobs / M4

**Independent verification:** Two live digital tool chains and distinct tailored
interfaces use the same foundation, with honest engineering checks and limits.

- [ ] T043 [US4] Freshly discover/qualify selected existing Blender/geometry/slicer and AgentCAD/OASiS provider bindings through the normal clean-container/host process; record actual schemas/options/artifact limits in `specs/083-process-working-interfaces/evidence/provider-qualification.md` without public promotion or new vendor implementation.
- [x] T044 [US4] Add bounded vendor-neutral STL/3MF/G-code toolpath and numerical result presentation/readers in `packages/ui_kit/` and `packages/workspace_service/src/workspace_service/process_interfaces/representations.py`, retaining parser provenance, true layers and unsupported classification fallback.
  Passive exact-subject readers and common/public-kit integration pass 110
  backend/API checks and 157 component/client checks. Actual external slicer and
  solver artifacts were read; full engineering/browser proof remains T047.
  See `evidence/representation-readers.md` for limits and scope.
- [ ] T045 [US4] Migrate printed-preparation saved workflow/bindings and entry to common/scoped interfaces in `examples/process-interfaces/printed-replacement-part/` and `apps/web/src/components/chat/WorkspacePanel.tsx`, retaining assignment/requirements and exact 082 gates.
- [x] T046 [US4] Provide heat-analysis saved workflow/bindings and comparison/evidence composition in `examples/process-interfaces/heat-spreader-sizing/`, retaining original stages/limits/critic status and actual STEP-to-analysis mapping.
  Declarative preparation now preserves the original three stages, full profile,
  fresh provider schemas, explicit CAD/solver calls and actual-file dependencies.
  Seven fixture preparation checks pass; live accepted workflow/readiness and
  common/tailored engineering presentation are still pending.
  Later live evidence verifies accepted source, basis wait/continuation, actual
  CAD/solver outputs, full assessment and common results. An initial actual-model
  tailored comparison is previewed/saved/opened. Focused correction, actual
  evidence navigation and unchanged saved-bundle reuse on a second waiting run
  are checked. Eleven final served checks now verify shared preparation (Start
  denied before readiness, permitted afterward), the second run's exact pending
  review and saved-bundle reuse/reload. Source/build and authoring records are
  unchanged, and no Start/review response is submitted. See `evidence/heat-proof.md`.
  The second run remains undecided; T047 still retains the complete two-process proof.
- [ ] T047 [US4] Execute both fresh isolated digital tool chains; generate/save/update/reuse each UI through Wright and inspect actual handoffs/common-tailored parity; retain evidence in `specs/083-process-working-interfaces/evidence/printed-proof.md` and `heat-proof.md` without touching campaign checkpoints.
- [ ] T048 [US4] Migrate all active demo callers/startup/API/UI operations, remove embedded vendor protocols/Studio automation after migration, and preserve old URLs through a read-only historical adapter in `packages/workspace_service/src/workspace_service/process_interfaces/legacy_results.py`; update the inventory in `docs/architecture/workflow-platform-refactoring-plan.md` with each disposition.
- [ ] T049 [US4] Audit shared packages for provider/process coupling and stale/missing/effect errors; record two-process comparison and active-code retirement evidence in `specs/083-process-working-interfaces/evidence/generality-and-migration.md`, preserving immutable historical catalog/campaign data.

## Phase 7 — Polish and cross-cutting completion / M5

- [ ] T050 Package public kit/client/instructions/template/asset runtime and offline resources through existing wheel/native/Docker build paths in `pyproject.toml` and `packages/workspace_service/pyproject.toml`; add installed-resource tests in `tests/test_process_interface_installed_resources.py`.
- [ ] T051 Verify installed native and clean Docker saved-UI/open/common-view behavior without checkout/model/compiler/network installs; record exact artifact/platform and authoring capability limits in `specs/083-process-working-interfaces/evidence/distribution.md`.
- [ ] T052 Run served normal-workspace walkthrough preserving refined editor controls and both working/preview journeys at realistic viewport/zoom/accessibility; retain screenshots/build/flags/report in `artifacts/process-interfaces/083/` and `specs/083-process-working-interfaces/evidence/workspace-acceptance.md`.
- [ ] T053 Run targeted unit/API/component/mocked/browser/security/package-boundary and prior affected continuation/082/editor regression checks; record commands/results/limits in `specs/083-process-working-interfaces/evidence/verification.md`, fixing failures within this feature.
- [ ] T054 Add runnable neutral authoring/reference examples and operator/developer/API/role-provider documentation in `examples/process-interfaces/`, `docs/workflows/process-working-interfaces.md` and `docs/architecture/agent-adapters.md`, using actual verified routes/commands/URLs.
- [ ] T055 Refresh vision/refactoring/contributor guidance and docs navigation in `docs/design/process-apps.md`, `docs/architecture/workflow-platform-refactoring-plan.md`, `docs/contributing/workflow-ui-integration.md` and `mkdocs.yml` to distinguish implemented/verified/unsupported scope without rewriting historical evidence.
- [ ] T056 Check every FR/SC against task/evidence coverage and publish status/limitations/reproducible evidence index in `specs/083-process-working-interfaces/completion.md`; distinguish fixture/live model/MCP/browser/engineering/test-decision/physical/user acceptance claims.
- [ ] T057 Finish focused local commits of owned work, verify unrelated dirty baselines and protected campaign/context history, and update `specs/083-process-working-interfaces/progress.md` with final task IDs/commit/evidence/resources still needed; no push/merge/release is implied.

## Dependencies and execution order

T001–T004 → T005–T010 → US1 → US2 → US3 → US4 → M5. M1 spans
contracts/backend work and US2; M2 is the common/client/kit/tab slice in US1.
Each story has an independently observable increment but shares prerequisites.
T043 provider discovery may start after T004 and continue alongside independent
platform work; live proofs require US1–US3, fresh qualification and actual providers.

T029 adapter and T032 fixed builder can proceed independently after their contracts
are frozen; T033/T034 require build identity; T035/T036 require reviewed grant
contracts; T037–T042 integrate them. Parallel research/edits are optional, not
authority to create subagents automatically. Avoid concurrent edits to shared
source/schema/service/UI files. No [P] marks are used because this delivery should
keep shared contracts and integration changes sequential and reviewable.

## Implementation strategy and completion

Useful first increment: US1 after foundation. Requested completion: **all 57 tasks**,
including real AI authoring and both engineering proofs. Do not stop at the kit or
reference app. Keep progress/evidence current and make local milestone commits.
Tests and synthetic decisions prove their recorded scope only. Missing live model,
provider or installed evidence leaves its task pending with a specific dependency;
do not replace it with fixture data or declare the entire feature complete.

No device/supplier effects or external publication are authorized. Actual human
engineering reviews remain waiting unless separately decided; isolated test-only
actors are governed by the submitted goal and acceptance-case enrollment rules.
