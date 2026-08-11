---

description: "Dependency-ordered implementation tasks for Rivet Hermes AI and MCP execution"
---

# Tasks: Rivet Hermes AI and MCP Execution

**Input**: Design documents from `/specs/067-rivet-hermes-ai/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md), [data-model.md](./data-model.md), [contracts/](./contracts/)

**Tests**: Required by the user and the feature specification. Within each story, write the listed tests first and observe the relevant failure before implementing the behavior.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel with other `[P]` tasks in the same phase because files do not overlap
- **[Story]**: User story from the specification (`US1`-`US4`)
- Every task names its primary file path

## Phase 1: Setup

**Purpose**: Establish feature switches, markers, and artifact entry points without changing runtime behavior.

- [x] T001 Add the opt-in `rivet_live_ai` pytest marker and document its environment guard in `pyproject.toml`
- [x] T002 [P] Add default-off AI bridge and real-runner settings with bounded validation in `packages/workspace_service/src/workspace_service/workflow_editor.py` and `packages/workspace_service/src/workspace_service/workflow_runner.py`
- [x] T003 [P] Add the `wright-rivet-mcp` installed console entry point in `pyproject.toml` and packaging assertions in `tests/packaging/test_wheel_contents.py`
- [x] T004 [P] Create the pinned runner source/build/inventory skeleton in `integrations/rivet/runner/src/wright-runner.ts`, `integrations/rivet/runner/scripts/build-rivet2-runner.mjs`, and `integrations/rivet/runner/manifest.json`

---

## Phase 2: Foundational Services

**Purpose**: Build shared trust, validation, persistence, and execution seams required by both canvas and MCP.

**Critical**: No user-story runtime code begins until this phase passes its focused tests.

### Tests first

- [x] T005 [P] Add failing contract tests for Wright-managed MCP first-seed activation, preserved user disablement, and separation from the public engineering catalog in `packages/tool_registry/tests/test_wright_managed_servers.py`
- [x] T006 [P] Add failing trusted-launch-binding tests proving canonical workspace/database/identity injection cannot be overridden by catalog data or tool arguments in `packages/tool_registry/tests/test_wright_managed_binding.py`
- [x] T007 [P] Add failing migration/repository tests for immutable workflow run identity, bounded events/results, and terminal state transitions in `packages/data_vault/tests/test_workflow_runs.py`
- [x] T008 [P] Add failing Rivet project validation tests for main/selected graph, inputs/outputs, malformed projects, requirement detection, bounded issues, and stale identity in `packages/workspace_service/tests/test_rivet_validation.py`
- [x] T009 [P] Add failing JSONL worker contract tests for digest verification, deterministic graph output, protocol violations, output caps, denied capabilities, and cancellation in `integrations/rivet/runner/tests/runner-contract.test.mjs`

### Implementation

- [x] T010 Implement the built-in `rivet-workflows` registry definition and idempotent reconciler in `packages/tool_registry/src/tool_registry/wright_managed_servers.py` and `packages/tool_registry/src/tool_registry/catalog_reconcile.py`
- [x] T011 Extend gateway/lifecycle launch context with non-catalog trusted environment for Wright-managed servers in `packages/tool_registry/src/tool_registry/gateway_service.py`, `packages/tool_registry/src/tool_registry/gateway_adapters.py`, and `packages/tool_registry/src/tool_registry/lifecycle_adapters.py`
- [x] T012 Implement workflow run records/events and their migration/repository in `packages/data_vault/src/data_vault/migrations.py` and `packages/data_vault/src/data_vault/workflow_runs.py`
- [x] T013 Implement bounded Rivet project parsing, graph summaries, identity checks, and capability requirement detection in `packages/workspace_service/src/workspace_service/rivet_validation.py`
- [x] T014 Bundle the real `@valerypopoff/rivet2-node` worker from the existing pinned source, implement stdin/JSONL execution, and generate its complete manifest in `integrations/rivet/runner/src/wright-runner.ts`, `integrations/rivet/runner/dist/wright-runner.mjs`, and `integrations/rivet/runner/manifest.json`
- [x] T015 Add runner artifact integrity/version checks parallel to the editor checks in `packages/workspace_service/src/workspace_service/workflow_runner.py` and `packages/workspace_service/tests/test_workflow_runner.py`

**Checkpoint**: Built-in server registration, trusted workspace binding, validation, durable run projections, and deterministic real Rivet execution pass independently.

---

## Phase 3: User Story 1 - Build a workflow with Rivet AI (Priority: P1)

**Goal**: Make the embedded sparkle action work through Hermes/Codex without an OpenAI API key or Hermes modification.

**Independent Test**: A deterministic Rivet-shaped tool request produces and applies the expected graph; save/reload preserves it; unavailable/malformed cases preserve the prior graph.

### Tests first

- [x] T016 [P] [US1] Add failing adapter tests for plain completion, SSE, one-tool translation, named/required/none choice, schema validation, malformed/unknown/multiple calls, upstream failures, cancellation, timing, and redaction in `packages/agent_adapters/tests/test_hermes_openai_bridge.py`
- [x] T017 [P] [US1] Add failing host security tests for config/token expiry, wrong bearer, method/path/content-type/body bounds, loopback-only use, health states, and no secret exposure in `packages/workspace_service/tests/test_rivet_editor_host.py`
- [x] T018 [P] [US1] Add failing wrapper tests for exact `ai` hybrid-storage seed keys, unavailable UI, and no provider/key controls in `integrations/rivet/editor/tests/wright-editor-bridge.test.tsx`
- [x] T019 [P] [US1] Add a failing component journey for sparkle progress, apply, interrupted recovery, and save/reload in `apps/web/src/components/surfaces/DirectRivetSurface.spec.tsx`

### Implementation

- [x] T020 [US1] Implement validated OpenAI request models, Hermes structured-decision prompt translation, tool-schema enforcement, standard response/SSE shaping, cancellation, and redaction in `packages/agent_adapters/src/agent_adapters/hermes_openai_bridge.py`
- [x] T021 [US1] Add the same-origin config and Chat Completions routes with ephemeral session tokens to `integrations/rivet/editor/host.py`
- [x] T022 [US1] Resolve the existing Hermes profile through `agent_adapters`, surface non-secret availability, and wire bridge settings into the editor surface launch in `packages/workspace_service/src/workspace_service/workflow_editor.py`
- [x] T023 [US1] Fetch runtime config and seed `selectAssistModel`, custom base URL/model, and runtime credential before mounting `RivetAppHost` in `integrations/rivet/editor/wrapper/WrightEditorBridge.tsx`
- [x] T024 [US1] Rebuild the pinned Rivet 2 wrapper and update the complete editor manifest inventory using `integrations/rivet/editor/scripts/build-rivet2.mjs`
- [x] T025 [US1] Add user-visible AI availability/progress/error state without restoring irrelevant Rivet chrome in `apps/web/src/components/surfaces/DirectRivetSurface.tsx`

**Checkpoint**: The sparkle flow works against deterministic Hermes responses and never exposes or requests an OpenAI key.

---

## Phase 4: User Story 2 - Create and run workflows from Wright chat (Priority: P1)

**Goal**: Let Hermes discover one new workspace-confined Rivet MCP and use it to list, create, inspect, validate, and run authoritative workflows.

**Independent Test**: A Wright chat prompt creates `chat-basic` from the Basic Flow template, validates it, requires review, then runs the approved exact revision and returns bounded outputs.

### Tests first

- [x] T026 [P] [US2] Add failing official-SDK MCP initialize/list/call/cancel tests for all six tools, schemas, annotations, structured errors, and progress in `packages/workspace_service/tests/test_rivet_mcp.py`
- [x] T027 [P] [US2] Add failing workspace confinement and concurrency tests for unsafe slugs, symlinks, cross-workspace attempts, duplicate creation, stale revision/digest, and oversized project/input/output in `packages/workspace_service/tests/test_rivet_mcp_security.py`
- [x] T028 [P] [US2] Add failing gateway discovery/policy tests for namespaced Rivet tools, lazy bound launch, required approvals, progress forwarding, disablement, and other-MCP regression in `packages/tool_registry/tests/test_gateway_rivet_mcp.py`
- [x] T029 [P] [US2] Add a failing Wright chat stream test where controlled Hermes invokes the Rivet MCP and Wright relays correlated running/completed progress plus the grounded result in `apps/api/tests/test_agent_rivet_mcp_progress.py`

### Implementation

- [x] T030 [US2] Implement the low-level stdio MCP server, bounded input/output models, tool annotations, stable errors, and trusted binding startup in `packages/workspace_service/src/workspace_service/rivet_mcp.py`
- [x] T031 [US2] Implement template/list/inspect/create/validate handlers using the existing catalog and `WorkspaceWorkflowStore` in `packages/workspace_service/src/workspace_service/rivet_mcp.py`
- [x] T032 [US2] Implement `RivetRuntimeHost` to start an ephemeral AI bridge, spawn the inventoried Node worker, parse bounded JSONL, relay progress, redact secrets, and clean up the process tree in `packages/workspace_service/src/workspace_service/rivet_runtime_host.py`
- [x] T033 [US2] Replace fixture invocation with the shared real execution service, immutable identity/review checks, durable events/results, timeouts, and cancellation in `packages/workspace_service/src/workspace_service/workflow_runner.py` and `packages/workspace_service/src/workspace_service/workflow_operations.py`
- [x] T034 [US2] Implement MCP `run_workflow` through the shared execution service and durable review repository in `packages/workspace_service/src/workspace_service/rivet_mcp.py`
- [x] T035 [US2] Reconcile the Wright-managed Rivet MCP at API and gateway startup in `apps/api/src/api/main.py` and `apps/api/src/api/gateway_stdio.py`

**Checkpoint**: The deterministic chat-to-Hermes-to-Wrightgateway-to-Rivet-MCP journey creates and runs the same workspace document that the canvas opens.

---

## Phase 5: User Story 3 - Run the same workflow from the canvas (Priority: P2)

**Goal**: Replace the toolbar's lifecycle fixture behavior with exact-revision Rivet execution, including AI nodes, progress, output, review, and cancellation.

**Independent Test**: An approved deterministic workflow produces identical output from the canvas and MCP, while unsaved/stale/unapproved runs are blocked.

### Tests first

- [x] T036 [P] [US3] Extend runner tests for AI-node calls through only the ephemeral bridge, long-lived credential isolation, exact revision/digest, real output events, timeout, process exit, and restart reconciliation in `packages/workspace_service/tests/test_workflow_runner.py`
- [x] T037 [P] [US3] Add failing API contract tests for run inputs/graph selection, review requirement, output/history projection, and cancellation in `apps/api/tests/test_workspace_api.py`
- [x] T038 [P] [US3] Add failing canvas component tests for unsaved draft warning, selected graph/inputs, correlated progress/output, terminal failures, and cancel control test IDs in `apps/web/src/components/surfaces/DirectRivetSurface.spec.tsx`

### Implementation

- [x] T039 [US3] Extend workspace run schemas/routes for graph, inputs, context, bounded output, and runtime progress while keeping routes logic-free in `apps/api/src/api/schemas/workspace.py` and `apps/api/src/api/routers/workspace.py`
- [x] T040 [US3] Extend the frontend workspace service run contract and polling/history projection in `apps/web/src/services/workspace-service.ts`
- [x] T041 [US3] Wire Run/Cancel, save-before-run behavior, selected revision identity, progress, and outputs into `apps/web/src/components/surfaces/DirectRivetSurface.tsx`
- [x] T042 [US3] Add identical-output integration coverage across MCP and canvas service in `packages/workspace_service/tests/test_rivet_execution_parity.py`

**Checkpoint**: Canvas and chat execute one shared reviewed revision with matching deterministic output and lifecycle behavior.

---

## Phase 6: User Story 4 - Verify subscription-backed AI safely (Priority: P2)

**Goal**: Complete the test pyramid and add two explicit live canaries without making subscription calls during normal tests.

- [x] T043 [P] [US4] Add mocked Playwright coverage for sparkle generate/apply/save/reload, unavailable Hermes, and canvas run progress in `tests/ui-integration/workspace-surfaces/rivet-ai.spec.ts`
- [x] T044 [P] [US4] Add installed-wheel/no-source/no-network tests for editor, runner, bridge imports, and MCP entry point in `tests/native_runtime/test_rivet_installed_runtime.py` and `tests/packaging/test_wheel_contents.py`
- [x] T045 [P] [US4] Add the guarded live Rivet-shaped structured tool-call smoke in `tests/e2e/test_rivet_hermes_ai_live.py`
- [x] T046 [P] [US4] Add the guarded live Wright chat prompt smoke asserting `rivet-workflows` MCP progress and grounded validation in `tests/e2e/test_rivet_hermes_ai_live.py`
- [x] T047 [US4] Add a test proving all live tests skip before network access unless both marker and `WRIGHT_RIVET_LIVE_AI=1` are present in `tests/e2e/test_rivet_hermes_ai_live.py`

---

## Phase 7: Polish and Gates

- [x] T048 [P] Document AI availability, MCP tools, review-before-run, latency expectations, live-test opt-in, and rollback in `docs/rivet-workflows.md`
- [x] T049 [P] Add structured timing/redaction assertions for bridge, MCP, and runner spans/logs in `packages/agent_adapters/tests/test_hermes_openai_bridge.py` and `packages/workspace_service/tests/test_rivet_runtime_host.py`
- [x] T050 Run every deterministic command in `specs/067-rivet-hermes-ai/quickstart.md` and record any platform-specific exception in that file
- [x] T051 Run `speckit-analyze` across `spec.md`, `plan.md`, and `tasks.md`; resolve every critical inconsistency before review
- [x] T052 Run `bash scripts/check-dev-merge.sh` before any merge to `dev`, or document the exact local host limitation that blocks a named gate
- [x] T053 Start Wright/Hermes with the completed feature, capture an image of the AI-capable Rivet 2 canvas at the earliest feasible point, and link it from the implementation handoff

---

## Dependencies and Execution Order

### Phase dependencies

- Phase 1 has no dependency.
- Phase 2 depends on Phase 1 and blocks every user story.
- US1 and the non-run portions of US2 can begin after Phase 2; complete US1 bridge support before testing AI-node execution.
- US2 runtime/MCP execution depends on T020, T032, and T033.
- US3 depends on the shared runtime from US2.
- US4 depends on the corresponding deterministic story checkpoints.
- Polish/gates depend on all selected stories.

### Critical path

`T005-T009 -> T010-T015 -> T016-T024 -> T026-T035 -> T036-T042 -> T043-T053`

### Parallel opportunities

- In Phase 2, registry, run repository, validation, and Node contract tests touch separate modules.
- Within each story, adapter/host/wrapper/UI or MCP/security/gateway/chat tests can be authored independently before implementation.
- Live canaries and installed-package tests can be prepared independently after deterministic contracts stabilize.

## Implementation Strategy

1. Preserve the inherited feature-066 work and add only feature-067 changes.
2. Work test-first at each story boundary; record the intended failing assertion before implementation.
3. Deliver US1 first so sparkle behavior proves the Hermes compatibility decision.
4. Deliver US2 next so Wright chat can create/validate/run via one new MCP.
5. Reuse the same execution service for US3; do not add a second runner path.
6. Keep live subscription calls opt-in and limited to the two canaries.
7. Stop for the constitution's human approval gate before beginning T001.
