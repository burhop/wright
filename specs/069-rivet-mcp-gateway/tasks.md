# Tasks: Rivet Workspace MCP Gateway Execution

**Input**: Design documents from `specs/069-rivet-mcp-gateway/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`

**Tests**: Required. The specification explicitly requires deterministic positive, negative, cancellation, lifecycle, UI, system, performance, security, compatibility, and optional-live evidence. Write each listed test before its implementation and demonstrate the intended failure.

**Organization**: Tasks are grouped by user story so each review, execution, cancellation, lifecycle, and evidence increment remains independently testable.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it changes different files and does not depend on an incomplete task.
- **[Story]**: Maps the task to one specification user story.
- Every task names the exact repository path it changes.

## Phase 1: Setup and deterministic fixtures

**Purpose**: Establish fail-closed protocol fixtures and local child MCPs without external services.

- [x] T001 Inventory the schema-13 workflow review/run baseline and add preservation assertions for migration 14 in `packages/data_vault/tests/test_migrations.py`
- [x] T002 [P] Add two deterministic MCP child fixtures with colliding unqualified names, structured output, progress, approval, slow-call cancellation, receipt counters, and late-result modes in `packages/workspace_service/tests/fixtures/rivet_mcp_servers.py`
- [x] T003 [P] Add valid and hostile protocol-v2 request/project fixtures covering exact bindings, direct child configuration, dynamic tool names, missing/extra handles, and secret-like values in `integrations/rivet/runner/tests/fixtures/`
- [x] T004 [P] Add explicit optional-live environment markers for BREP and Solid Edge/available-host validation in `pyproject.toml` and `docs/rivet/testing.md`

---

## Phase 2: Foundational authority, persistence, and runner contract

**Purpose**: Implement the shared exact-identity and authority boundary that blocks every user story until complete.

**CRITICAL**: No user-story implementation begins until this phase passes its focused tests.

- [x] T005 [P] Add model/digest/secret-rejection contract tests for CapabilityBinding, WorkflowBindingSet, review v2, PendingRivetCallApproval, RunManifest, and child-call evidence in `packages/core/tests/test_rivet_mcp_contracts.py`
- [x] T006 [P] Add migration-14 upgrade, idempotency, rollback, legacy non-MCP review, and repository round-trip tests in `packages/data_vault/tests/test_rivet_mcp_persistence.py`
- [x] T007 [P] Add authority entropy, audience, expiry, run/generation/workspace/node scope, constant-time lookup, replay, revocation, restart, and concurrent-call tests in `packages/workspace_service/tests/test_rivet_authority.py`
- [x] T008 [P] Extend Node contract tests for protocol-v1 non-MCP compatibility and protocol-v2 validation/network-guard/provider-injection failures in `integrations/rivet/runner/tests/runner-contract.test.mjs`
- [x] T009 Add additive migration 14 tables/columns/indexes and schema-version compatibility in `packages/data_vault/src/data_vault/migrations.py`
- [x] T010 Implement canonical Rivet MCP binding, review, approval, child-call, artifact, and manifest values with bounded/redacted serialization in `packages/core/src/core/rivet_mcp.py`
- [x] T011 Implement immutable binding-set, review-v2, pending-approval, manifest, and child-call repositories with legacy adapters in `packages/data_vault/src/data_vault/rivet_mcp_repository.py` and export them from `packages/data_vault/src/data_vault/__init__.py`
- [x] T012 Implement memory-only `RivetRunAuthorityService` mint/validate/activate/revoke/terminal lifecycle with raw-token exclusion in `packages/workspace_service/src/workspace_service/rivet_authority.py`
- [x] T013 [P] Add shared secret-like field rejection, safe summaries, byte ceilings, and redaction counters in `packages/workspace_service/src/workspace_service/rivet_evidence.py`
- [x] T014 Extend the governed bridge with authoritative node-handle lookup, current-binding revalidation seam, active-request registry, progress projection, and stable denial reasons in `packages/workspace_service/src/workspace_service/rivet_gateway_bridge.py`
- [x] T015 Wire authority/repository/gateway dependencies and MCP feature settings into application composition without adding route business logic in `apps/api/src/api/composition.py`
- [x] T016 Upgrade request types, strict validation, exact-origin network guard, static binding map, and injected-provider shell for runner protocol v2 in `integrations/rivet/runner/src/wright-runner.ts`
- [x] T017 Rebuild the pinned Rivet worker deterministically and update source/build/output integrity metadata in `integrations/rivet/runner/dist/wright-runner.mjs` and `integrations/rivet/runner/manifest.json`
- [x] T018 Run and record the focused foundational migration, model, authority, runner-contract, manifest-integrity, Ruff, TypeScript, formatting, and diff checks in `docs/engineering-capability-program-progress.md`

**Checkpoint**: Migration 14 preserves schema-13 state, protocol v2 fails closed, raw authority is memory-only, and a bound bridge call cannot choose its own workspace/server/tool.

---

## Phase 3: User Story 1 - Bind workspace tools while reviewing (Priority: P1) - MVP

**Goal**: Discover only current workspace capabilities, resolve each MCP node to an exact implementation, and approve an exact reproducible binding set without invoking a child.

**Independent Test**: In one workspace, expose two fake servers with colliding unqualified tool names; preview exact bindings, approve them, and prove workflow/graph/node/schema/server/validation/grant/policy changes make the review stale before any child receipt.

### Tests for User Story 1

- [x] T019 [P] [US1] Add requirement extraction, direct-config rejection, MCP-prompt rejection, dynamic-tool rejection, duplicate-node, selected-graph, and exact binding validation tests in `packages/workspace_service/tests/test_rivet_capabilities.py`
- [x] T020 [P] [US1] Add discovery namespacing, eligibility, bounded schema, validation/grant identity, ambiguity, refresh, and zero-child-start tests in `packages/workspace_service/tests/test_rivet_capability_discovery.py`
- [x] T021 [P] [US1] Add review-v2 API contract tests for preview, exact digest approval, stale conflicts, cross-workspace denial, and legacy non-MCP compatibility in `apps/api/tests/test_rivet_mcp_review_api.py`
- [x] T022 [P] [US1] Add component tests for binding rows, ambiguity, risk/schema details, stale reasons, keyboard operation, narrow layout, and secret-free text in `apps/web/src/components/chat/RivetWorkflowCapabilities.spec.tsx`
- [x] T023 [P] [US1] Add mocked authoring/review journey and serious/critical accessibility scan in `tests/ui-integration/rivet-mcp-gateway.spec.ts`

### Implementation for User Story 1

- [x] T024 [P] [US1] Implement MCP-node extraction, selected-graph constraints, prohibited project-config detection, static tool-name enforcement, and binding requirements in `packages/workspace_service/src/workspace_service/rivet_validation.py`
- [x] T025 [US1] Implement workspace gateway discovery projection, canonical schema/grant/policy digests, exact resolution, ambiguity, binding-set creation, and stale comparison in `packages/workspace_service/src/workspace_service/rivet_capabilities.py`
- [x] T026 [US1] Extend review operations to preview/rebuild/compare/store exact binding sets and keep legacy non-MCP review behavior in `packages/workspace_service/src/workspace_service/workflow_operations.py`
- [x] T027 [P] [US1] Add typed capability, binding-preview, review-digest, stale-diff, and error schemas in `apps/api/src/api/schemas/workspace.py`
- [x] T028 [US1] Add thin authenticated discovery, binding-preview, and v2 review routes to `apps/api/src/api/routers/workspace.py`
- [x] T029 [P] [US1] Add capability/binding/review TypeScript contracts and service calls in `apps/web/src/services/workspace-service.ts`
- [x] T030 [US1] Implement accessible capability binding, exact-review summary, stale-diff, and recovery UI in `apps/web/src/components/chat/RivetWorkflowCapabilities.tsx`
- [x] T031 [US1] Integrate the capability/review step without changing non-MCP behavior in `apps/web/src/components/chat/RivetWorkflowsPanel.tsx`
- [x] T032 [US1] Add two-workspace API integration proof that discovery and reviews cannot cross grants and do not start fake children in `apps/api/tests/test_rivet_mcp_review_api.py`
- [x] T033 [US1] Run the US1 package/API/web/mocked-browser suite and record the independently testable MVP evidence in `docs/engineering-capability-program-progress.md`

**Checkpoint**: Exact binding/review works without invocation; stale or ambiguous scope blocks Start; non-MCP workflows remain compatible.

---

## Phase 4: User Story 2 - Execute a reviewed multi-MCP workflow (Priority: P1)

**Goal**: Execute native Rivet MCP nodes through one short-lived Wright authority and the existing gateway, including exact-call approval, structured results, artifacts, and audit.

**Independent Test**: Run one real pinned Rivet graph through the Node worker and Wright gateway to Alpha and Beta fake children; prove ordered calls/results, an exact Beta approval, audit/provenance, and zero direct child configuration.

### Tests for User Story 2

- [x] T034 [P] [US2] Add injected-provider discovery/call/structured-result/progress/token-redaction, MCP-prompt denial, no-tool-namespace submission, and exact-origin tests in `integrations/rivet/runner/tests/runner-contract.test.mjs`
- [x] T035 [P] [US2] Add dedicated-loopback bridge authentication, bind isolation, audience, request/body/event limits, handle lookup, current-state revalidation, policy denial, trace/log correlation, and NDJSON result tests in `apps/api/tests/test_rivet_runner_bridge.py`
- [x] T036 [P] [US2] Add exact-call approval digest, expiry, changed-argument, one-shot consumption, deny, and no-client-hint tests in `packages/workspace_service/tests/test_rivet_call_approvals.py`
- [x] T037 [P] [US2] Add real Node plus two-fake-child gateway integration coverage with colliding names, progress, structured outputs, authorized gateway/vault artifact references, raw-path/URI rejection, audit, and ordered node attribution in `packages/workspace_service/tests/test_rivet_mcp_execution.py`
- [x] T038 [P] [US2] Add public run/approval API role, workspace, stale-start, response-redaction, and compatibility tests in `apps/api/tests/test_rivet_mcp_run_api.py`
- [x] T039 [P] [US2] Add approval-modal and executing-timeline component states with keyboard/focus/live-region coverage in `apps/web/src/components/chat/RivetWorkflowRun.spec.tsx`

### Implementation for User Story 2

- [x] T040 [US2] Complete the injected Rivet `MCPProvider`, in-memory node transform, reserved discovery handle, bound tool call, NDJSON parsing, and safe result mapping in `integrations/rivet/runner/src/wright-runner.ts`
- [x] T041 [US2] Rebuild and integrity-pin the protocol-v2 worker after provider completion in `integrations/rivet/runner/dist/wright-runner.mjs` and `integrations/rivet/runner/manifest.json`
- [x] T042 [P] [US2] Implement exact pending-call approval lifecycle and argument/gate digest validation in `packages/workspace_service/src/workspace_service/rivet_approvals.py`
- [x] T043 [US2] Implement bridge discovery/call streams that accept no caller tool namespace, resolve authoritative bindings, revalidate current state, delegate to `GatewayService` with `client_approval_hint=False`, accept only Wright-authorized gateway/vault artifacts, and emit structured logs/OpenTelemetry spans in `packages/workspace_service/src/workspace_service/rivet_gateway_bridge.py`
- [x] T044 [US2] Implement the separately owned `127.0.0.1` ephemeral-port runner bridge application with exact bearer audience/path, no external mounting or CORS, bounded NDJSON, safe errors, active-call registration, and deterministic shutdown in `apps/api/src/api/rivet_runner_bridge.py`
- [x] T045 [US2] Extend `RivetRuntimeHost` protocol-v2 request creation, secret registration, exact MCP origin allowance, binding grant, and event validation in `packages/workspace_service/src/workspace_service/rivet_runtime_host.py`
- [x] T046 [US2] Extend `WorkspaceWorkflowRunner` start lifecycle to verify review/bindings, create an immutable-identity manifest draft, reconcile orphaned drafts as interrupted without recreating authority, mint current authority, grant MCP only when required, and terminalize/revoke safely in `packages/workspace_service/src/workspace_service/workflow_runner.py`
- [x] T047 [US2] Add exact-call approval list/decision and manifest-safe run response orchestration in `packages/workspace_service/src/workspace_service/workflow_operations.py`
- [x] T048 [P] [US2] Extend public approval/run schemas and safe artifact/manifest projections in `apps/api/src/api/schemas/workspace.py`
- [x] T049 [US2] Add thin authenticated pending-approval and decision routes while extending start/status/history in `apps/api/src/api/routers/workspace.py`
- [x] T050 [US2] Add approval and active-call service methods plus accessible approval modal/timeline integration in `apps/web/src/services/workspace-service.ts` and `apps/web/src/components/chat/RivetWorkflowRun.tsx`
- [x] T051 [US2] Run the real pinned runner/two-fake-child/API/web integration slice and record child receipts, gateway audits, approval scope, outputs, and exact provenance in `docs/engineering-capability-program-progress.md`

**Checkpoint**: A reviewed graph calls two child MCPs only through Wright; exact approval works; unbound/disabled/cross-workspace/stale attempts have zero child receipt.

---

## Phase 5: User Story 3 - Cancel and recover a long MCP call (Priority: P2)

**Goal**: Revoke authority, explicitly cancel the active gateway child call, block later effects, ignore late results, and preserve truthful cleanup/residue evidence.

**Independent Test**: Cancel the slow fake child after progress, then run both acknowledgement and ignored-cancellation modes and prove the terminal record distinguishes clean cancellation from possible residue.

### Tests for User Story 3

- [x] T052 [P] [US3] Add cancellation-order, concurrent completion, active-request cleanup, post-revoke denial, and restart-revocation tests in `packages/workspace_service/tests/test_rivet_mcp_cancellation.py`
- [x] T053 [P] [US3] Add runner abort/provider-fetch cancellation and late-result suppression tests in `integrations/rivet/runner/tests/runner-contract.test.mjs`
- [x] T054 [P] [US3] Add API idempotent cancel/generation conflict/residue projection tests in `apps/api/tests/test_rivet_mcp_run_api.py`
- [x] T055 [P] [US3] Add cancellation, acknowledgement, unconfirmed residue, and recovery UI states in `apps/web/src/components/chat/RivetWorkflowRun.spec.tsx`

### Implementation for User Story 3

- [x] T056 [US3] Implement authority-first cancellation, explicit `GatewayService.cancel(session_id, request_id, reason)`, bounded acknowledgement, runner termination, and late-result rejection in `packages/workspace_service/src/workspace_service/workflow_runner.py`
- [x] T057 [US3] Add bridge/provider abort propagation and terminal suppression in `packages/workspace_service/src/workspace_service/rivet_gateway_bridge.py` and `integrations/rivet/runner/src/wright-runner.ts`
- [x] T058 [US3] Persist cancellation acknowledgement, residue, recovery code, and immutable terminal manifest evidence in `packages/data_vault/src/data_vault/rivet_mcp_repository.py`
- [x] T059 [US3] Project cancelling/clean/residue/recovery states through run APIs and `apps/web/src/components/chat/RivetWorkflowRun.tsx`
- [x] T060 [US3] Run both deterministic cancellation variants and record timing, child acknowledgement, zero later calls, late-result rejection, and residue truth in `docs/engineering-capability-program-progress.md`

**Checkpoint**: Cancellation reaches the child and revokes authority within required thresholds; late success is impossible; residue is never hidden.

---

## Phase 6: User Story 4 - Specialized application lifecycle parity (Priority: P2)

**Goal**: Preserve BREP panel and Solid Edge/host-bridge startup, health, progress, cancellation, failure, and cleanup behind the same gateway contract.

**Independent Test**: Execute deterministic panel-backed and host-bridge doubles through one bound workflow and compare their gateway-facing event/result/error contract with ordinary fake MCP children.

### Tests for User Story 4

- [x] T061 [P] [US4] Add panel-backed BREP lifecycle double integration tests in `packages/workspace_service/tests/test_rivet_brep_lifecycle.py`
- [x] T062 [P] [US4] Add proprietary-free Solid Edge/host-bridge lifecycle double integration tests in `packages/workspace_service/tests/test_rivet_host_bridge_lifecycle.py`
- [x] T063 [P] [US4] Add explicitly skipped-by-default live BREP and Solid Edge/available-app probes with evidence labels in `tests/e2e/test_rivet_mcp_live_apps.py`

### Implementation for User Story 4

- [x] T064 [US4] Preserve BREP panel single-flight preparation, visible-panel status, progress, cancellation, and cleanup when calls originate from Rivet in `apps/api/src/api/brep_gateway.py`
- [x] T065 [US4] Add a provider-neutral specialized lifecycle projection seam without child config leakage in `packages/tool_registry/src/tool_registry/gateway_service.py` and `packages/tool_registry/src/tool_registry/lifecycle.py`
- [x] T066 [US4] Add stable specialized-host failure/residue/recovery mapping to the bridge and run evidence in `packages/workspace_service/src/workspace_service/rivet_gateway_bridge.py`
- [x] T067 [US4] Run deterministic lifecycle parity plus any already-authorized available live probe, labeling external prerequisites and limitations in `docs/engineering-capability-program-progress.md`

**Checkpoint**: Specialized applications remain Wright-owned and indistinguishable from ordinary MCPs at the Rivet provider contract; no proprietary prerequisite enters normal gates.

---

## Phase 7: User Story 5 - Diagnose and reproduce a run (Priority: P3)

**Goal**: Present a bounded, redacted, durable timeline and manifest that explain every binding, approval, child call, artifact, cancellation, failure, and reproducibility difference.

**Independent Test**: Inspect/export one successful and one denied run after restart and account for every MCP node/call/approval/artifact/terminal reason without a secret or reusable authority.

### Tests for User Story 5

- [x] T068 [P] [US5] Add manifest-draft immutable identity, exactly-once terminal finalization, orphaned-restart interruption, canonical digest, truncation, authorized artifact reference, and secret-pattern tests in `packages/data_vault/tests/test_rivet_run_manifest.py`
- [x] T069 [P] [US5] Add correlated event ordering, denied-before-child, stale-diff, and recovery projection tests in `packages/workspace_service/tests/test_rivet_run_evidence.py`
- [x] T070 [P] [US5] Add run-manifest/history/export API bounds and RBAC tests in `apps/api/tests/test_rivet_mcp_run_api.py`
- [x] T071 [P] [US5] Add complete timeline, stale comparison, artifact, redaction, responsive, and accessibility component tests in `apps/web/src/components/chat/RivetWorkflowRun.spec.tsx`
- [x] T072 [P] [US5] Complete mocked success/denial/restart/recovery browser journeys with secret scans in `tests/ui-integration/rivet-mcp-gateway.spec.ts`

### Implementation for User Story 5

- [x] T073 [US5] Finalize the canonical Run Manifest exactly once from its immutable-identity draft and complete append-only call/event/approval/authorized-artifact persistence with bounded projections in `packages/data_vault/src/data_vault/rivet_mcp_repository.py`
- [x] T074 [US5] Implement reproducibility comparison and actionable stale/recovery summaries in `packages/workspace_service/src/workspace_service/rivet_evidence.py`
- [x] T075 [US5] Add authenticated manifest/history/export orchestration and thin API routes in `packages/workspace_service/src/workspace_service/workflow_operations.py` and `apps/api/src/api/routers/workspace.py`
- [x] T076 [US5] Implement the accessible correlated run timeline, artifact references, stale comparison, residue, and recovery UI in `apps/web/src/components/chat/RivetWorkflowRun.tsx`
- [x] T077 [US5] Run success/denial/restart evidence acceptance and record 100% node/call/approval/artifact accounting plus zero secret findings in `docs/engineering-capability-program-progress.md`

**Checkpoint**: Durable evidence is complete, bounded, redacted, correlated, reproducible, and unable to resume an old authority.

---

## Phase 8: Polish and cross-cutting acceptance

**Purpose**: Close performance, security, accessibility, compatibility, packaging, documentation, and authoritative integration gates.

- [ ] T078 [P] Add deterministic 500-tool discovery, authority issuance, bridge overhead, progress projection, and cancellation latency measurements for NFR-002/NFR-003 in `packages/workspace_service/tests/test_rivet_mcp_performance.py`
- [ ] T079 [P] Add cross-surface token/credential/header/environment/raw-child-path/arbitrary-URI/secret-like scans for workflow files, SQLite, structured logs, traces, events, API responses, runner output, and UI text in `tests/security/test_rivet_mcp_secret_boundary.py`
- [ ] T080 [P] Add hostile local-client, token replay, origin/path/method/content-type, oversized payload, malformed stream, and concurrent revocation tests in `apps/api/tests/test_rivet_runner_bridge_security.py`
- [ ] T081 [P] Add regression coverage for non-MCP workflows, agent-manager/chat gateway clients, BREP panel ownership, and schema-13 fixture upgrade in `tests/e2e/test_rivet_mcp_compatibility.py`
- [ ] T082 [P] Add standalone wheel/sdist assertions for protocol-v2 runner artifacts, JSON contracts, and migration/repository modules in `tests/packaging/test_rivet_mcp_distribution.py`
- [ ] T083 Complete the local FastAPI plus pinned Node runner plus two-real-stdio-fixture MCP system smoke in `tests/e2e/test_rivet_mcp_gateway.py`
- [ ] T084 Complete wide/narrow keyboard-only binding, review, exact approval, execution, cancellation, residue, recovery, and serious/critical accessibility Playwright acceptance in `tests/ui-integration/rivet-mcp-gateway.spec.ts`
- [ ] T085 Update operator, security-boundary, troubleshooting, optional-live, rollback, and no-direct-child documentation in `docs/rivet/mcp-gateway.md`, `docs/rivet/testing.md`, and `mkdocs.yml`
- [ ] T086 Run all quickstart sections and record deterministic versus optional-live results and the deferred five-engineer study honestly in `specs/069-rivet-mcp-gateway/quickstart.md` and `docs/engineering-capability-program-progress.md`
- [ ] T087 Run focused Python, Node, web, Playwright, packaging, docs, bundle-verifier, formatting, type, lint, security, performance, and `git diff --check` suites; remediate every in-scope failure in the owning files
- [ ] T088 Fetch latest `origin/dev`, integrate it without losing catalog-aware bundle validation, and run `scripts/check-dev-merge.sh` on the exact final feature tree; record any host-limited gate exactly in `docs/engineering-capability-program-progress.md`
- [ ] T089 Re-run the authoritative exact-tree gate after final documentation changes, push `069-rivet-mcp-gateway`, merge `--no-ff` to `dev`, push `dev`, and verify local/remote commit and feature/merged tree synchronization in `docs/engineering-capability-program-progress.md`

---

## Dependencies and execution order

### Phase dependencies

- **Phase 1 Setup**: Starts immediately.
- **Phase 2 Foundation**: Depends on Phase 1 and blocks every story.
- **US1 Binding/review**: Depends on Phase 2; delivers the independently testable MVP.
- **US2 Execution**: Depends on the exact review/binding output of US1.
- **US3 Cancellation**: Depends on US2 active-call/authority integration.
- **US4 Specialized lifecycle**: Depends on US2 bridge execution; its deterministic doubles can be authored in parallel with US3.
- **US5 Evidence**: Depends on US2 durable calls and integrates US3/US4 terminal evidence.
- **Polish**: Depends on every desired story; T088-T089 are strictly last.

### User story dependency graph

```text
Foundation -> US1 Bind/review -> US2 Execute -> US3 Cancel
                                      |          |
                                      +-> US4 Lifecycle
                                      |          |
                                      +----------+-> US5 Evidence -> Polish/Gate/Merge
```

### Parallel opportunities

- T002-T004 establish independent fixtures/docs.
- T005-T008 establish model, migration, authority, and runner test contracts independently.
- Within US1, T019-T023 can be written in parallel; T027 and T029 can follow model contracts independently.
- Within US2, T034-T039 can be written in parallel; T042 and T048 are independent after foundational contracts.
- US3 test tasks T052-T055 and US4 tests T061-T063 are independent once US2 passes.
- US5 tests T068-T072 can be authored in parallel after the durable US2 call shape exists.
- Polish tasks T078-T082 can run in parallel; integration T083-T087 follows, and T088-T089 remain serial.

## Parallel examples

### User Story 1

```text
T019 capability extraction tests
T020 gateway discovery tests
T021 review API contract tests
T022 binding component tests
T023 mocked authoring journey
```

### User Story 2

```text
T034 injected provider tests
T035 internal bridge tests
T036 exact approval tests
T037 two-child integration test
T038 public API tests
T039 approval/timeline component tests
```

### Cancellation and specialized lifecycle

```text
US3: T052-T055 cancellation contracts
US4: T061-T063 panel/host/live-gate contracts
```

## Implementation strategy

### MVP first

1. Complete Setup and Foundation.
2. Complete US1 discovery, binding, and exact review.
3. Validate US1 independently: two namespaced tools bind without child startup, and every material change makes review stale.
4. Keep MCP execution disabled until US2 passes Gate B runtime tests.

### Incremental delivery

1. US1 provides safe authoring/review.
2. US2 enables exact reviewed multi-MCP execution.
3. US3 proves cancellation and residue truth.
4. US4 proves specialized application lifecycle parity.
5. US5 completes durable diagnosis/reproduction.
6. Cross-cutting gates establish performance, secrecy, accessibility, compatibility, packaging, and merge safety.

### Safety and commit discipline

- Demonstrate each test's intended failure before implementation, then keep focused evidence current.
- Commit each completed phase or coherent story checkpoint; do not mix unrelated catalog or downloaded/build output.
- Keep `.local-run/`, downloaded MCP sources, model weights, caches, proprietary application data, and transient build output untracked.
- Never accept licenses, provide credentials, contact paid services, mutate proprietary hosts, actuate hardware, merge `dev` to `main`, or publish a release in this loop.
