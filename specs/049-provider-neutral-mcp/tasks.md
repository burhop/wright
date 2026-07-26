# Tasks: Provider-Neutral MCP Integration

**Input**: Design documents from `/specs/049-provider-neutral-mcp/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Tests are required by the feature specification. Contract tests are written before their corresponding implementation and must demonstrate the missing behavior first.

**Organization**: Tasks are grouped by user story so each story has an independently testable outcome.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it changes different files and has no dependency on an incomplete task
- **[Story]**: Maps the task to a user story from spec.md
- Every task names its concrete file path

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm repository hygiene and create the shared removal inventory used to guard the migration boundary.

- [X] T001 Verify Python, TypeScript, Docker, and generated-output ignore coverage in `.gitignore`, `.dockerignore`, `apps/web/eslint.config.js`, and Prettier configuration; existing repository ignores cover all critical generated/secret paths
- [X] T002 Create the initial provider-specific runtime reference inventory in `specs/049-provider-neutral-mcp/removal-inventory.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Preserve trusted launch configuration and complete advertised tool contracts before changing runtime behavior.

**CRITICAL**: User story implementation begins only after the additive state and tool metadata foundation is complete.

- [X] T003 [P] Add failing additive-migration and round-trip tests for `launch_env`, tool title, output schema, and annotations in `packages/data_vault/tests/test_migrations.py` and `packages/tool_registry/tests/test_registry.py`
- [X] T004 [P] Add failing catalog normalization/reconciliation tests for trusted `launch_env` in `packages/tool_registry/tests/test_catalog_normalization.py` and `packages/tool_registry/tests/test_catalog_reconcile.py`
- [X] T005 Add `launch_env` and complete advertised tool metadata models in `packages/tool_registry/src/tool_registry/models.py` and `packages/tool_registry/src/tool_registry/catalog_models.py`
- [X] T006 Implement additive columns and serialization in `packages/data_vault/src/data_vault/migrations.py` and `packages/tool_registry/src/tool_registry/db.py`
- [X] T007 Project `launch_env` through catalog loading/reconciliation and regenerate the catalog schema in `packages/tool_registry/src/tool_registry/catalog_loader.py`, `packages/tool_registry/src/tool_registry/catalog_reconcile.py`, `packages/tool_registry/src/tool_registry/canonical_catalog.py`, and `packages/tool_registry/src/tool_registry/catalog/schema.json`
- [X] T008 Preserve title, input/output schemas, and annotations during discovery in `packages/tool_registry/src/tool_registry/lifecycle_adapters.py` and `packages/tool_registry/src/tool_registry/manager.py`
- [X] T009 Separate trusted approval requirements from advertised annotations in `packages/tool_registry/src/tool_registry/gateway_models.py`, `packages/tool_registry/src/tool_registry/gateway_adapters.py`, `packages/tool_registry/src/tool_registry/gateway_policy.py`, and `packages/tool_registry/src/tool_registry/mcp_server.py`

**Checkpoint**: Existing rows remain readable, trusted launch data round-trips, and discovered tools retain their full server-advertised contract.

---

## Phase 3: User Story 1 - Use Any Workspace-Aware MCP Server (Priority: P1) MVP

**Goal**: Launch and call any trusted local MCP server with an authorized workspace without provider-name or tool-name behavior.

**Independent Test**: Two differently named synthetic servers with equivalent templates receive the same literal canonical workspace, expose the same advertised tools, and produce identical authorization/lifecycle outcomes.

### Tests for User Story 1

- [X] T010 [P] [US1] Add failing placeholder grammar, canonicalization, metacharacter, unknown-token, and string-command rejection tests in `packages/tool_registry/tests/test_launch_templates.py`
- [X] T011 [P] [US1] Replace provider-identity lifecycle tests with failing two-server launch parity and unchanged-unbound-server tests in `packages/tool_registry/tests/test_lifecycle_adapters.py`
- [X] T012 [P] [US1] Replace provider-filter policy tests with advertised-tool parity and trusted-approval tests in `packages/tool_registry/tests/test_gateway_policy.py` and `packages/tool_registry/tests/test_gateway_service.py`
- [X] T013 [P] [US1] Add regression tests proving the Hermes system hint contains no Solid Edge provider/tool recipe in `packages/agent_adapters/tests/test_hermes_gateway_profile.py`

### Implementation for User Story 1

- [X] T014 [US1] Implement exact trusted `{workspace.path}` rendering for command arrays and launch environments in `packages/tool_registry/src/tool_registry/launch_templates.py`
- [X] T015 [US1] Replace `_workspace_scoped_environment` with the generic renderer during STDIO construction in `packages/tool_registry/src/tool_registry/lifecycle_adapters.py`
- [X] T016 [US1] Remove the Solid Edge source/name detector and creation allowlist while retaining provider-neutral policy in `packages/tool_registry/src/tool_registry/gateway_policy.py`
- [X] T017 [US1] Remove the Solid Edge tool recipe from `WRIGHT_SYSTEM_HINT` while preserving unrelated guidance in `packages/agent_adapters/src/agent_adapters/hermes.py`
- [X] T018 [US1] Document generic local-server workspace binding and current external-server compatibility configuration in `docs/mcp-catalog/mcp-server-setup-recipes.md`

**Checkpoint**: User Story 1 passes without any Solid Edge runtime branch; the existing server can be represented by ordinary trusted configuration data.

---

## Phase 4: User Story 2 - See Honest Generic Tool Progress (Priority: P2)

**Goal**: Relay standard child MCP progress and present provider-neutral, correlated, monotonic chat progress.

**Independent Test**: A synthetic child server emits standard progress through Wright to an outer MCP client and generic agent stream, including fallback, malformed, cancellation, timeout, replay, and terminal cases.

### Tests for User Story 2

- [X] T019 [P] [US2] Add failing child progress-token, notification, monotonicity, unknown-token, and cleanup tests in `packages/tool_registry/tests/test_mcp_child_progress.py`
- [X] T020 [P] [US2] Add failing end-to-end outer progress relay and cancellation-isolation tests in `packages/tool_registry/tests/test_mcp_stdio.py` and `packages/tool_registry/tests/test_gateway_service.py`
- [X] T021 [P] [US2] Add failing generic progress projection, fallback, heartbeat, terminal, and replay tests in `packages/agent_adapters/tests/test_progress.py` and `apps/api/tests/test_agent_stream_progress.py`
- [X] T022 [P] [US2] Update frontend parser/rendering tests for generic server/tool/title/message fields in `apps/web/tests/ChatTranscript.spec.tsx` and `apps/web/tests/agent-service.spec.ts`

### Implementation for User Story 2

- [X] T023 [US2] Add the optional progress callback contract to `packages/tool_registry/src/tool_registry/runners/base.py` and implement child token/notification handling in `packages/tool_registry/src/tool_registry/runners/stdio.py`
- [X] T024 [US2] Propagate request-scoped progress callbacks through `packages/tool_registry/src/tool_registry/lifecycle.py`, `packages/tool_registry/src/tool_registry/manager.py`, `packages/tool_registry/src/tool_registry/gateway_ports.py`, and `packages/tool_registry/src/tool_registry/gateway_adapters.py`
- [X] T025 [US2] Validate and relay progress in `packages/tool_registry/src/tool_registry/gateway_service.py` and send outer SDK progress from `packages/tool_registry/src/tool_registry/mcp_server.py`
- [X] T026 [US2] Implement provider-neutral progress projection/state in `packages/agent_adapters/src/agent_adapters/progress.py` and export it from `packages/agent_adapters/src/agent_adapters/__init__.py`
- [X] T027 [US2] Remove `_CAD_PROGRESS_LABELS` and use the package projection in `apps/api/src/api/routers/agent.py`
- [X] T028 [US2] Consume generic progress fields and safe fallbacks in `apps/web/src/services/agent-service.ts` and `apps/web/src/components/chat/ChatTranscript.tsx`

**Checkpoint**: Standard progress crosses both MCP boundaries, generic chat progress remains resumable, and no provider/tool mapping remains.

---

## Phase 5: User Story 3 - Operate and Migrate Servers Safely (Priority: P3)

**Goal**: Preserve generic ownership, rebinding, concurrency, timeout, cancellation, and rollback behavior through the migration.

**Independent Test**: Managed and externally managed synthetic servers survive workspace activation/rebinding and concurrent sessions without duplicate ownership or timeout regression.

### Tests for User Story 3

- [X] T029 [P] [US3] Extend ownership, rebind, and concurrent-session regression coverage in `packages/tool_registry/tests/test_lifecycle_coordinator.py`, `packages/tool_registry/tests/test_gateway_concurrency.py`, and `apps/api/tests/test_hermes_sync.py`
- [X] T030 [P] [US3] Extend configured operation-timeout and cancellation coverage through the full call path in `packages/tool_registry/tests/test_registry.py` and `packages/tool_registry/tests/test_gateway_service.py`
- [X] T031 [P] [US3] Add a runtime-source boundary test rejecting Solid Edge identifiers outside approved catalog/docs paths in `tests/test_provider_neutral_mcp_runtime.py`

### Implementation for User Story 3

- [X] T032 [US3] Reconcile lifecycle and gateway call signatures so ownership, rebinding, concurrency, timeout, and cancellation remain identity-independent in `packages/tool_registry/src/tool_registry/lifecycle.py`, `packages/tool_registry/src/tool_registry/manager.py`, and `apps/api/src/api/services/wright_gateway_sync.py`
- [X] T033 [US3] Complete migration, rollback, and optional Windows compatibility instructions in `docs/integrations/solid-edge-creation.md`, `docs/operations/solid-edge-diagnostics.md`, and `specs/049-provider-neutral-mcp/quickstart.md`

**Checkpoint**: All three stories work independently, and required Wright CI has no external Solid Edge dependency.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Complete the removal audit, validate the full feature, and prepare a reviewable change set.

- [X] T034 Update `specs/049-provider-neutral-mcp/removal-inventory.md` with every removed runtime path and the final allowed catalog/documentation references
- [X] T035 Run focused Python and frontend suites covering launch templates, registry persistence, gateway policy/service/STDIO, Hermes progress, and chat rendering
- [X] T036 Run runtime-source identifier audits plus Python/TypeScript lint, formatting, and type checks
- [X] T037 Run `scripts/check-dev-merge.sh`; if a host limitation blocks a specific phase, record the exact limitation and run the equivalent isolated gate
- [X] T038 Perform the optional Windows live compatibility smoke only if the matching external SolidEdgeMCP neutral contract and host application are available; record a precise skip reason otherwise in `specs/049-provider-neutral-mcp/removal-inventory.md`
- [ ] T039 Review the complete diff, mark every completed task `[X]`, commit the intentional scope, push `049-provider-neutral-mcp`, and open a draft pull request targeting `dev`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Starts immediately.
- **Foundational (Phase 2)**: Depends on Setup and blocks all user stories.
- **User Story 1 (Phase 3)**: Depends on Foundation; establishes the MVP launch and discovery boundary.
- **User Story 2 (Phase 4)**: Depends on Foundation and stored tool metadata, but is independently testable with a synthetic server.
- **User Story 3 (Phase 5)**: Depends on Foundation and integrates lifecycle signatures from Stories 1 and 2.
- **Polish (Phase 6)**: Depends on all selected user stories.

### User Story Dependencies

- **US1 (P1)**: No dependency on another story after Foundation.
- **US2 (P2)**: Uses the complete advertised tool metadata from Foundation; it does not depend on US1 launch templating.
- **US3 (P3)**: Validates the combined lifecycle after US1 and US2 signatures stabilize.

### Within Each User Story

- Write and run contract tests before implementation.
- Models and ports precede service/adapters.
- Package services precede API/UI translation.
- Complete the story checkpoint before moving to the next priority.

### Parallel Opportunities

- T003 and T004 can run in parallel.
- T010-T013 can run in parallel after Foundation.
- T019-T022 can run in parallel after Foundation.
- T029-T031 can run in parallel after preceding call signatures stabilize.
- Documentation tasks can proceed alongside tests that do not touch the same files.

---

## Parallel Example: User Story 2

```text
Task: "Add child STDIO progress contract tests in packages/tool_registry/tests/test_mcp_transport.py"
Task: "Add outer relay tests in packages/tool_registry/tests/test_mcp_stdio.py"
Task: "Add generic agent progress tests in packages/agent_adapters/tests/test_progress.py"
Task: "Update frontend progress tests in apps/web/tests/"
```

---

## Implementation Strategy

### MVP First (User Story 1)

1. Complete additive state/tool metadata foundation.
2. Implement exact trusted workspace templates.
3. Remove provider-specific policy and prompt code.
4. Validate two-server identity parity and unchanged unbound servers.
5. Stop and verify the existing integration is representable as ordinary configuration.

### Incremental Delivery

1. Foundation preserves all existing rows and advertised contracts.
2. US1 removes launch/policy/prompt coupling.
3. US2 replaces progress mappings with standard relay.
4. US3 proves runtime ownership and timeout stability.
5. Polish completes source audit, documentation, merge gate, and draft PR.

## Notes

- `[P]` tasks touch different files or independent test surfaces.
- Required tests never install or execute Solid Edge/SolidEdgeMCP.
- The optional live smoke does not grant catalog validation status.
- Do not reintroduce provider behavior to compensate for a missing external-server capability; document the external contract gap instead.
