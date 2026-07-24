# Tasks: Solid Edge Creation Visibility

**Input**: Design documents from `/specs/048-solid-edge-creation-visibility/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Required by the feature specification. Write policy, stream, transport, ownership, and live-smoke tests before completing the corresponding implementation tasks. The current uncommitted prototype is not authoritative evidence until these tasks pass.

**Organization**: The checked merge-scope list below is authoritative for the
production-test stabilization delivered by this branch. The original
full-architecture task design is retained afterward as a deferred backlog; its
unchecked boxes are not claims about the narrower merge scope.

## Reconciled Merge Scope (2026-07-24)

- [x] M001 Project a reviewed creation-oriented Solid Edge tool set and deny hidden direct calls.
- [x] M002 Add canonical one-call, new-document, visible-result Hermes guidance.
- [x] M003 Emit immediate planning progress, friendly Solid Edge labels, and elapsed heartbeats.
- [x] M004 Preserve reconnectable in-process progress and terminal events.
- [x] M005 Queue or steer prompts submitted while a chat turn is busy.
- [x] M006 Prevent API MCP lifecycle actions when Hermes is the configured owner.
- [x] M007 Rebind the Hermes gateway when the active workspace changes.
- [x] M008 Propagate Wright bearer authentication from the Hermes bridge.
- [x] M009 Cover gateway policy, progress, ownership, workspace sync, and bridge behavior.
- [x] M010 Stabilize Linux CI authentication and private secret-store test paths.
- [x] M011 Document setup, progress, failure recovery, scope, and deferred work.
- [x] M012 Pass the authoritative dev merge gate; require green PR checks before merge.

## Deferred Original Full-Architecture Backlog

The following draft tasks describe the immutable profile, provider-neutral
progress and diagnostics services, created-artifact binding, benchmark tooling,
and 20-run Windows evidence that were intentionally moved out of this merge.
They remain available for a follow-up specification and have not been silently
marked complete.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Reconcile the existing prototype, establish fixtures/evidence locations, and make the feature's scope explicit.

- [ ] T001 Record the Feature 048 scope change, current uncommitted prototype, Feature 047 baseline, and review state in docs/gpt5-6plan.md and docs/gpt5-6-implementation-status.md
- [ ] T002 [P] Create reviewed SolidEdgeMCP creation/inspection tool-name and schema fixtures in tests/fixtures/solid_edge_creation_profile/
- [ ] T003 [P] Add `solid_edge_creation` and `solid_edge_live` pytest markers and focused suite paths in pyproject.toml
- [ ] T004 [P] Exclude Solid Edge live outputs, timing evidence scratch data, and lifecycle lock residue in .gitignore and apps/api/.gitignore
- [ ] T005 [P] Add deterministic fake creation results, failure reports, progress streams, audit events, and owner-process counters in tests/fixtures/solid_edge_creation_visibility/
- [ ] T006 Create the requirement-to-task evidence ledger with an explicit prototype gap inventory in specs/048-solid-edge-creation-visibility/checklists/completion-audit.md

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Define shared profile, progress, diagnostic, path-authorization, and runtime-owner contracts used by every story.

**CRITICAL**: No user story is complete until this foundation passes; existing route-local prototype logic must be treated as temporary.

- [ ] T007 [P] Add failing creation-profile/session-state and created-artifact-binding tests in packages/tool_registry/tests/test_solid_edge_creation_models.py
- [ ] T008 [P] Add failing phase/progress/replay-buffer value-model tests in packages/agent_adapters/tests/test_progress.py
- [ ] T009 [P] Add failing diagnostic-record/summary and runtime-owner value-model tests in packages/tool_registry/tests/test_gateway_diagnostics.py and apps/api/tests/test_mcp_runtime_ownership.py
- [ ] T010 Implement `CreationProfile`, `CreationRequestPolicy`, and `CreatedArtifactBinding` values in packages/tool_registry/src/tool_registry/solid_edge_creation.py and add immutable profile identity to packages/tool_registry/src/tool_registry/gateway_models.py
- [ ] T011 Implement stable phase, progress-update, and bounded replay-buffer values in packages/agent_adapters/src/agent_adapters/progress.py and export them from packages/agent_adapters/src/agent_adapters/__init__.py
- [ ] T012 Implement diagnostic record/summary values and an aggregation service skeleton in packages/tool_registry/src/tool_registry/gateway_diagnostics.py
- [ ] T013 Extend the gateway workspace port for output-path authorization in packages/tool_registry/src/tool_registry/gateway_ports.py and implement the adapter with workspace_service.workspace_path.WorkspacePath in apps/api/src/api/composition.py
- [ ] T014 Implement typed API/external runtime-owner configuration with backward-compatible `WRIGHT_API_MCP_AUTOSTART` parsing in apps/api/src/api/config.py
- [ ] T015 Run the foundational model/config suites and record exact commands and results in specs/048-solid-edge-creation-visibility/quickstart.md

**Checkpoint**: Profile identity, path authorization, progress/replay, diagnostics, and ownership are explicit reusable contracts.

---

## Phase 3: User Story 1 - Create a New Visible Solid Edge Artifact (Priority: P1) MVP

**Goal**: Create one new confined Solid Edge artifact, leave it open and visible, and never inspect or alter a document that predated the request.

**Independent Test**: With Solid Edge blank and again with a known document already open, request a 20 mm x 20 mm x 10 mm part and prove one creation call produces a separate saved/open/visible `.par` file while the prior document is unchanged; invalid recipe/path/overwrite cases stop before mutation.

### Tests for User Story 1

- [ ] T016 [P] [US1] Add failing exact allowlist, hidden/direct-call denial, and immutable-profile tests in packages/tool_registry/tests/test_solid_edge_creation_profile.py
- [ ] T017 [P] [US1] Add failing new-document, provider, visible/open, output-confinement, overwrite, recipe-mode, and `positive_normal` argument tests in packages/tool_registry/tests/test_solid_edge_creation_policy.py
- [ ] T018 [P] [US1] Add failing creation-result verification and same-session created-artifact follow-up tests in packages/tool_registry/tests/test_solid_edge_created_artifact.py
- [ ] T019 [P] [US1] Add an official MCP client integration test proving one fake-provider creation call and no inspection calls in tests/integration/test_solid_edge_creation_profile.py
- [ ] T020 [P] [US1] Add an operator-gated blank/pre-existing-document live acceptance harness in tests/e2e-live/test_solid_edge_creation_visibility.py

### Implementation for User Story 1

- [ ] T021 [US1] Classify authoritative SolidEdgeMCP tool names into validation, creation, bound follow-up, inspection, and unknown groups in packages/tool_registry/src/tool_registry/solid_edge_creation.py
- [ ] T022 [US1] Apply profile-aware discovery and fail-closed direct-call authorization in packages/tool_registry/src/tool_registry/gateway_policy.py and packages/tool_registry/src/tool_registry/gateway_service.py
- [ ] T023 [US1] Enforce provider, new-document, visible/open, confined output, exact overwrite authorization, commit recipe, and simple-call-budget rules in packages/tool_registry/src/tool_registry/solid_edge_creation.py and packages/tool_registry/src/tool_registry/gateway_service.py
- [ ] T024 [US1] Create and enforce session-scoped `CreatedArtifactBinding` records from successful structured results in packages/tool_registry/src/tool_registry/gateway_service.py
- [ ] T025 [US1] Replace advisory-only prototype text with canonical creation-profile and box-recipe guidance in .hermes.md and docs/integrations/solid-edge-creation.md
- [ ] T026 [US1] Implement the repeatable Windows smoke runner and redacted evidence writer in scripts/run-solid-edge-creation-smoke.ps1
- [ ] T027 [US1] Run the fake-provider independent test and one available live smoke, then record US1 evidence or the exact host limitation in specs/048-solid-edge-creation-visibility/checklists/completion-audit.md

**Checkpoint**: A bounded new-part request is safe, confined, visible, independently testable, and does not touch ambient Solid Edge documents.

---

## Phase 4: User Story 2 - Understand Long-Running Work (Priority: P2)

**Goal**: Show immediate planning status, human-readable Solid Edge phases, elapsed time, and reconnectable liveness throughout a long turn.

**Independent Test**: Use an intentionally delayed fake creation phase, disconnect/reconnect after an event index, and verify the first event arrives within 1 second, gaps never exceed 10 seconds, labels contain no internal-only tool name, and progress/result/completion replay in order.

### Tests for User Story 2

- [ ] T028 [P] [US2] Add failing immediate-planning, monotonic elapsed, phase transition, 10-second heartbeat, cancellation, failure, and terminal-fallback tests in packages/agent_adapters/tests/test_progress.py
- [ ] T029 [P] [US2] Add failing bounded replay, reconnect cursor, expiration/reset, and terminal-retention tests in apps/api/tests/test_agent_stream_progress.py
- [ ] T030 [P] [US2] Add failing typed parsing and user-visible Solid Edge phase/elapsed rendering tests in apps/web/tests/agent-service.spec.ts and apps/web/tests/ChatTranscript.spec.tsx

### Implementation for User Story 2

- [ ] T031 [US2] Move progress labels, phase state, heartbeat scheduling, monotonic timing, redaction, and no-text terminal fallback into packages/agent_adapters/src/agent_adapters/progress.py
- [ ] T032 [US2] Replace the unbounded route-local event list with the bounded indexed `ChatTurnProgressBuffer` in apps/api/src/api/routers/agent.py
- [ ] T033 [US2] Reduce apps/api/src/api/routers/agent.py to authenticated job orchestration and SSE translation over the agent-adapter progress service
- [ ] T034 [P] [US2] Extend typed progress/replay event parsing with phase, labels, elapsed values, event indices, and reset handling in apps/web/src/services/agent-service.ts and apps/web/src/store/types.ts
- [ ] T035 [US2] Preserve ordered reconnectable progress messages in apps/web/src/store/sessions.tsx
- [ ] T036 [US2] Render current phase and elapsed time without internal MCP-only identifiers in apps/web/src/components/chat/ChatTranscript.tsx
- [ ] T037 [US2] Add reconnect/long-phase API integration coverage in apps/api/tests/test_agent_api.py
- [ ] T038 [US2] Run the delayed-turn API/frontend independent test and record US2 timing/replay evidence in specs/048-solid-edge-creation-visibility/checklists/completion-audit.md

**Checkpoint**: A user can distinguish a healthy long-running turn from a hang and can reconnect without losing terminal context.

---

## Phase 5: User Story 3 - Diagnose Slow or Failed Creation (Priority: P3)

**Goal**: Attribute end-to-end latency, summarize active/completed/slow calls, preserve protocol framing, authenticate bridge reads, and maintain one runtime owner.

**Independent Test**: Execute a delayed creation through the gateway and verify paired redacted audit records, phase attribution, authenticated diagnostics, stderr-only STDIO logs, and one child process while repeated API/UI polling occurs in external-owner mode.

### Tests for User Story 3

- [ ] T039 [P] [US3] Add failing paired started/succeeded/failed/timed-out/cancelled/denied audit tests in packages/tool_registry/tests/test_gateway_service.py
- [ ] T040 [P] [US3] Add failing active/completed/outcome/total/average/max/slowest/phase-attribution summary tests in packages/tool_registry/tests/test_gateway_diagnostics.py
- [ ] T041 [P] [US3] Add failing authenticated session/turn-scoped diagnostics endpoint and cross-session denial tests in apps/api/tests/test_gateway_api.py
- [ ] T042 [P] [US3] Add failing request/response-size, slow-call threshold, redaction, and stderr-versus-protocol-stdout tests in packages/tool_registry/tests/test_stdio_runner.py and apps/api/tests/test_logging_config.py
- [ ] T043 [P] [US3] Add failing API-owned/external-owned startup, agent preparation, workspace reconciliation, polling, and owner-transition tests in apps/api/tests/test_mcp_runtime_ownership.py
- [ ] T044 [P] [US3] Add failing bearer propagation, missing-token, invalid-token, and token-redaction tests in hermes-plugin-wright/tests/test_bridge.py
- [ ] T045 [P] [US3] Add an end-to-end fake turn timing test that attributes at least 95 percent of elapsed time in tests/integration/test_solid_edge_turn_diagnostics.py

### Implementation for User Story 3

- [ ] T046 [US3] Carry turn/correlation/request identity and record exactly one started plus terminal audit event for every outcome in packages/tool_registry/src/tool_registry/gateway_service.py
- [ ] T047 [P] [US3] Instrument child STDIO request duration, method/tool identity, request/response sizes, outcome, and slow-call classification without payload capture in packages/tool_registry/src/tool_registry/runners/stdio.py
- [ ] T048 [US3] Implement bounded pairing, active-call detection, phase totals, slowest calls, and non-overlapping attribution in packages/tool_registry/src/tool_registry/gateway_diagnostics.py
- [ ] T049 [US3] Add limited session/turn audit queries with repository redaction in packages/data_vault/src/data_vault/gateway_repository.py
- [ ] T050 [US3] Make apps/api/src/api/routers/gateway.py a thin authenticated translator over the diagnostics service wired in apps/api/src/api/composition.py
- [ ] T051 [P] [US3] Route structured STDIO server diagnostics to stderr and reserve stdout for MCP frames in apps/api/src/api/logging_config.py and apps/api/src/api/gateway_stdio.py
- [ ] T052 [US3] Apply runtime-owner policy to API lifespan, agent preparation, workspace activation/update, and passive status in apps/api/src/api/main.py, apps/api/src/api/routers/agent.py, and apps/api/src/api/routers/workspace.py
- [ ] T053 [P] [US3] Preserve Wright bearer authentication for protected Hermes bridge queries in hermes-plugin-wright/bridge.py
- [ ] T054 [US3] Run the diagnostics/ownership independent test and record US3 redaction, framing, attribution, and process-count evidence in specs/048-solid-edge-creation-visibility/checklists/completion-audit.md

**Checkpoint**: Operators can locate delay or failure without leaking payloads, corrupting MCP stdout, or starting a competing Solid Edge subprocess.

---

## Phase 6: User Story 4 - Avoid Unnecessary Work (Priority: P4)

**Goal**: Minimize the Solid Edge model-visible surface and prove bounded creation never invokes inspection or oversized inventory operations.

**Independent Test**: List tools in a creation-profile session and run the simple-part smoke; document/face/feature/dimension/variable/measurement/capability/semantic operations are absent, guessed calls fail before the child, and the audit shows one creation call with zero inspection calls.

### Tests for User Story 4

- [ ] T055 [P] [US4] Add an exhaustive allowlist-versus-current-SolidEdgeMCP-inventory contract test with unknown-tool fail-closed behavior in packages/tool_registry/tests/test_solid_edge_creation_inventory.py
- [ ] T056 [P] [US4] Add schema-size, projected-tool-count, hidden-tool audit, and oversized-result metadata tests in packages/tool_registry/tests/test_solid_edge_creation_profile.py
- [ ] T057 [P] [US4] Add a bounded planning/call-budget integration test proving one creation and zero inspection operations in tests/integration/test_solid_edge_creation_call_budget.py

### Implementation for User Story 4

- [ ] T058 [US4] Project only reviewed creation-profile tools and their required schemas/descriptions from packages/tool_registry/src/tool_registry/gateway_adapters.py and packages/tool_registry/src/tool_registry/gateway_service.py
- [ ] T059 [US4] Audit hidden/denied attempts by stable classification without returning excluded schemas or descriptions in packages/tool_registry/src/tool_registry/gateway_policy.py
- [ ] T060 [US4] Add deterministic tool-count, schema-byte, discovery-time, and call-budget measurements in scripts/benchmark-solid-edge-creation-profile.py
- [ ] T061 [US4] Run the inventory/call-budget independent test and record US4 zero-inspection evidence in specs/048-solid-edge-creation-visibility/checklists/completion-audit.md

**Checkpoint**: The agent sees a compact, creation-only surface and cannot invoke inspection even by guessing a name.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Reconcile documentation, live evidence, existing prototype residue, full regression gates, and feature status.

- [ ] T062 [P] Document owner configuration, creation profile, progress/reconnect behavior, diagnostics, and operator recovery in docs/integrations/solid-edge-creation.md and docs/operations/solid-edge-diagnostics.md
- [ ] T063 [P] Add the feature docs and executable examples to mkdocs.yml and tests/test_docs_solid_edge_creation.py
- [ ] T064 Reconcile or remove superseded route-local prototype logic, stale progress mappings, and generated apps/api/state.db.lifecycle.lock; verify the final diff with git status and git diff --check
- [ ] T065 Run Ruff, format, focused mypy, all Feature 048 pytest slices, Hermes plugin tests with local reinstall, frontend unit tests, lint, and production build; record exact results in docs/gpt5-6-implementation-status.md
- [ ] T066 Run at least 20 operator-gated Windows live trials and store redacted SC-001 through SC-008 evidence under test-results/solid-edge-creation-visibility/
- [ ] T067 Verify no catalog status/evidence was changed without the clean-container process and record the boundary check in specs/048-solid-edge-creation-visibility/checklists/completion-audit.md
- [ ] T068 Complete requirement-by-requirement and success-criterion evidence in specs/048-solid-edge-creation-visibility/checklists/completion-audit.md
- [ ] T069 Run scripts/check-dev-merge.sh before any merge to dev and resolve every failure or document the exact local host limitation required by AGENTS.md
- [ ] T070 Mark Feature 048 review-ready only after all required evidence passes and record migration, rollback, remaining external prerequisites, and the next roadmap action in docs/gpt5-6-implementation-status.md

---

## Dependencies & Execution Order

### Phase Dependencies

- Setup has no dependencies and preserves the existing prototype while establishing evidence.
- Foundational depends on Setup and blocks every user story.
- US1 depends on Foundational and is the MVP safety/creation slice.
- US2 depends only on Foundational and can be developed in parallel with US1, although the live demo combines them.
- US3 depends on Foundational; its final attribution integration consumes US2 phase events and its live owner evidence consumes US1.
- US4 depends on the US1 profile/policy and adds exhaustive inventory/performance proof.
- Polish depends on all selected user stories.

### User Story Dependencies

- **US1 (P1)**: Foundational only; establishes the authoritative profile and safe visible creation.
- **US2 (P2)**: Foundational only; independently testable with a delayed fake engine.
- **US3 (P3)**: Foundational for unit work; final end-to-end attribution depends on US2 and final live ownership evidence depends on US1.
- **US4 (P4)**: US1; validates and optimizes the complete creation-only projection.

### Within Each User Story

- Write the story's failing tests before completing implementation.
- Models/classification precede policy and service behavior.
- Package services precede FastAPI/frontend adapters.
- Fake-provider evidence precedes operator-gated live evidence.
- A task remains unchecked until its authoritative command/evidence passes.

### Parallel Opportunities

- Setup fixtures, markers/ignore rules, and the audit checklist touch different files.
- Foundational profile, progress, diagnostic, and owner tests can be authored in parallel.
- US1 policy tests and live-harness scaffolding are independent before integration.
- US2 backend progress/replay tests and frontend rendering tests are parallel.
- US3 audit, STDIO logging, owner, Hermes-auth, and endpoint tests touch separate components.
- US4 inventory/schema tests and benchmark scaffolding can run in parallel.
- Documentation and docs tests are parallel after contracts stabilize.

## Parallel Example: User Story 1

```text
Task T016: Profile projection and direct-call denial tests
Task T017: Creation argument/path policy tests
Task T018: Created-artifact binding tests
Task T019: Fake MCP integration test
Task T020: Operator-gated live harness
```

## Parallel Example: User Story 2

```text
Task T028: Progress/heartbeat tests
Task T029: Replay/reconnect tests
Task T030: Frontend parsing/rendering tests
```

## Parallel Example: User Story 3

```text
Task T039: Gateway audit outcome tests
Task T040: Diagnostic aggregation tests
Task T042: STDIO framing/redaction tests
Task T043: Runtime-owner tests
Task T044: Hermes authentication tests
```

## Parallel Example: User Story 4

```text
Task T055: Exhaustive current-inventory contract
Task T056: Projection/schema-size tests
Task T057: One-call/zero-inspection integration test
```

## Implementation Strategy

### MVP First

1. Complete Setup and Foundational.
2. Complete US1 through the fake-provider independent test.
3. Run the available blank and pre-existing-document live smokes.
4. Stop for operator review before treating the prototype as a safe creation workflow.

### Incremental Delivery

1. US1 delivers safe new visible artifacts.
2. US2 makes long work understandable and reconnectable.
3. US3 makes latency/failure/ownership diagnosable.
4. US4 minimizes the final planning surface and proves zero inspection.
5. Polish supplies repeated live evidence and the authoritative merge gate.

## Notes

- Actual Solid Edge live tests are Windows/operator-gated and must never become a fake catalog-validation claim.
- Do not add Solid Edge, SolidEdgeMCP, vendor SDKs, or license software to the Wright base image.
- Prompts and MCP annotations are advisory; GatewayService policy remains authoritative.
- `WRIGHT_API_MCP_AUTOSTART=0` is the current compatibility selector for external/Hermes ownership.
- Generated outputs, evidence scratch data, and lifecycle locks are not source artifacts.
