# Tasks: Gateway Service and MCP 2025-11-25

## Phase 1: Setup

- [X] T001 Add the stable official MCP SDK dependency and package-resource includes in packages/tool_registry/pyproject.toml and uv.lock
- [X] T002 Record exact Codex, MCP SDK, protocol, OS, and verification-date evidence in specs/046-gateway-service-and-mcp-2025-11-25/research.md
- [X] T003 Add Feature 046 progress baseline and roadmap mapping to docs/gpt5-6-implementation-status.md
- [X] T004 [P] Add MCP/gateway pytest markers and shared fixtures in pyproject.toml and packages/tool_registry/tests/conftest.py

## Phase 2: Foundational Models and Ports

- [X] T005 Write immutable session/request state tests in packages/tool_registry/tests/test_gateway_models.py
- [X] T006 Implement GatewaySessionContext, GatewayRequest, results, tools, resources, and stable errors in packages/tool_registry/src/tool_registry/gateway_models.py
- [X] T007 Define gateway workspace, repository, audit, notifier, clock, and runner ports in packages/tool_registry/src/tool_registry/gateway_ports.py
- [X] T008 Add data-vault explicit gateway-session binding/audit repository tests in packages/data_vault/tests/test_gateway_repository.py
- [X] T009 Implement explicit session-binding and append-only audit repository methods in packages/data_vault/src/data_vault/gateway_repository.py
- [X] T010 Wire repository/adapter construction without routes selecting infrastructure in apps/api/src/api/composition.py
- [X] T011 Extend architecture manifest/tests for the new gateway surfaces in architecture/python-packages.toml and tests/test_import_boundaries.py

## Phase 3: User Story 3 — Reliable MCP Lifecycle (P1)

**Independent test**: Concurrent start/restart/stop/failure/shutdown trials leave one current generation and no leaked owned tasks or runners.

- [X] T012 [P] [US3] Add per-server generation and late-completion tests in packages/tool_registry/tests/test_lifecycle_coordinator.py
- [X] T013 [P] [US3] Add reconciliation, cancellation, timeout, and graceful-shutdown tests in packages/tool_registry/tests/test_lifecycle_shutdown.py
- [X] T014 [US3] Implement LifecycleSlot and generation-safe McpLifecycleCoordinator in packages/tool_registry/src/tool_registry/lifecycle.py
- [X] T015 [US3] Move runner construction and tool discovery behind lifecycle adapters in packages/tool_registry/src/tool_registry/lifecycle_adapters.py
- [X] T016 [US3] Make McpEngine delegate start/stop/reconcile/shutdown without exposing _active_runners in packages/tool_registry/src/tool_registry/manager.py
- [X] T017 [US3] Update API lifespan to await reconciliation and bounded shutdown in apps/api/src/api/main.py and apps/api/src/api/services/mcp_services.py

## Phase 4: User Story 4 — Canonical Catalog and Scoped Changes (P2)

**Independent test**: One packaged resource validates, has exact parity across consumers, fails closed on incomplete evidence, and emits only session-scoped changes.

- [X] T018 [P] [US4] Add canonical schema, duplicate/alias, evidence, and parity tests in packages/tool_registry/tests/test_catalog_resource.py
- [X] T019 [P] [US4] Add wheel/sdist resource-content tests in packages/tool_registry/tests/test_catalog_distribution.py
- [X] T020 [US4] Create schema-validated canonical catalog resources in packages/tool_registry/src/tool_registry/catalog/engineering-catalog.yaml and schema.json
- [X] T021 [US4] Replace authored Python catalog literals with packaged-resource loading and alias migration in packages/tool_registry/src/tool_registry/catalog_loader.py and engineering_catalog.py
- [X] T022 [US4] Generate or consume plugin catalog projection from the canonical resource in hermes-plugin-wright/catalog.yaml and its tests
- [X] T023 [US4] Add reviewed safety/provenance/output metadata normalization in packages/tool_registry/src/tool_registry/catalog_models.py
- [X] T024 [US4] Implement session-scoped tool/resource list-change publisher in packages/tool_registry/src/tool_registry/gateway_notifications.py

## Phase 5: User Story 1 — Direct Provider-Neutral MCP (P1)

**Independent test**: An explicit workspace-bound session initializes, lists authorized tools/resources, calls one safe tool, receives structured output, and audits the decision without Hermes.

- [X] T025 [P] [US1] Add service discovery/call/resource/policy tests in packages/tool_registry/tests/test_gateway_service.py
- [X] T026 [P] [US1] Add schema, annotation, structured-result, and stable-error tests in packages/tool_registry/tests/test_gateway_results.py
- [X] T027 [P] [US1] Add server-authoritative policy and redacted audit tests in packages/tool_registry/tests/test_gateway_policy.py
- [X] T028 [US1] Implement workspace-authorized projection and server-side policy in packages/tool_registry/src/tool_registry/gateway_policy.py
- [X] T029 [US1] Implement GatewayService sessions, discovery, calls, resources, cancellation, audit, and shutdown in packages/tool_registry/src/tool_registry/gateway_service.py
- [X] T030 [US1] Implement catalog, workspace, and confined artifact resources in packages/tool_registry/src/tool_registry/gateway_resources.py
- [X] T031 [US1] Implement task-oriented server/catalog/workspace management tools in packages/tool_registry/src/tool_registry/gateway_management.py
- [X] T032 [US1] Build official SDK server handlers/capabilities/instructions in packages/tool_registry/src/tool_registry/mcp_server.py
- [X] T033 [US1] Add protocol lifecycle, list/call/read, cancellation, notification, and error fixtures in packages/tool_registry/tests/test_mcp_server.py
- [X] T034 [US1] Implement serialized explicit-workspace STDIO entry point in packages/tool_registry/src/tool_registry/mcp_stdio.py
- [X] T035 [US1] Convert packages/tool_registry/src/tool_registry/gateway.py into the feature-flagged one-release compatibility delegate
- [X] T036 [US1] Add STDIO partial-read, concurrent-write, EOF, timeout, and shutdown tests in packages/tool_registry/tests/test_mcp_stdio.py

## Phase 6: User Story 2 — Concurrent Session Isolation (P1)

**Independent test**: One hundred two-session trials prove disjoint list/call/read/cancel/notification/reconnect state for STDIO and HTTP.

- [X] T037 [P] [US2] Add 100-trial service isolation and foreign cancellation tests in packages/tool_registry/tests/test_gateway_isolation.py
- [X] T038 [P] [US2] Add 100-message serialized response/notification stress tests in packages/tool_registry/tests/test_gateway_concurrency.py
- [X] T039 [P] [US2] Add HTTP principal/session/workspace/reconnect isolation tests in apps/api/tests/test_mcp_transport.py
- [X] T040 [US2] Implement authenticated Origin-checked Streamable HTTP `/mcp` mount in apps/api/src/api/routers/mcp_transport.py
- [X] T041 [US2] Add protocol/session/rate/body limit settings and secure loopback defaults in apps/api/src/api/config.py
- [X] T042 [US2] Bind SDK transport sessions to authenticated principals and immutable workspace contexts in apps/api/src/api/composition.py
- [X] T043 [US2] Register `/mcp`, enforce startup/readiness failure, and close sessions in apps/api/src/api/main.py
- [X] T044 [US2] Make legacy REST/SSE gateway routes explicit-session delegates behind WRIGHT_LEGACY_GATEWAY in apps/api/src/api/routers/gateway.py
- [X] T045 [US2] Remove process-global/recent gateway workspace selection and route calls to private runner state in packages/workspace_service/src/workspace_service/adapters/runtime.py and apps/api/src/api/services/wright_gateway_sync.py

## Phase 7: Integration, Compatibility, and Documentation

- [X] T046 Add SDK client STDIO and Streamable HTTP contract tests in tests/e2e/test_gateway_mcp_smoke.py
- [X] T047 Add Codex CLI 0.144.1 Windows list/call/listChanged/concurrency/error harness in tests/e2e/test_codex_mcp_compatibility.py
- [X] T048 Run and record executable Codex compatibility evidence without claiming untested hosts in docs/integrations/codex-mcp-compatibility.md
- [X] T049 Document GatewayService, session binding, policy authority, transports, and legacy removal in docs/architecture/gateway-service.md
- [X] T050 Document authenticated STDIO/HTTP operation, timeouts, cancellation, shutdown, and rollback in docs/operations/mcp-gateway.md
- [X] T051 Update package/API READMEs and MkDocs navigation in packages/tool_registry/README.md, apps/api/README.md, and mkdocs.yml
- [X] T052 Update docs/gpt5-6-implementation-status.md with files, exact results, migration/rollback, risks, and Feature 047 next action

## Phase 8: Completion Audit and Gates

- [X] T053 Run focused Ruff, mypy, lifecycle, gateway, catalog, API, and package-resource tests and record exact results
- [X] T054 Run actual wheel/sdist clean-install imports and packaged catalog inspection through scripts/build-python-distributions.sh
- [X] T055 Run strict documentation, public-alpha leak, import-boundary, and secret/redaction checks
- [X] T056 Run scripts/check-dev-merge.sh with no skips or document a precise host limitation and separately execute every available sub-gate
- [X] T057 Audit every FR-001–FR-028 and SC-001–SC-009 against authoritative evidence and mark tasks complete only when proved

## Dependencies

- Setup and foundational phases block all stories.
- US3 lifecycle and US4 catalog block US1 service construction.
- US1 blocks US2 transports/isolation.
- Integration and completion gates require all stories.

## Parallel Opportunities

- T012/T013; T018/T019; T025/T026/T027; T037/T038/T039 can run in parallel after their shared prerequisites.
- Documentation T048–T051 can proceed independently after contracts stabilize.

## Implementation Strategy

Deliver lifecycle and catalog foundations first, then a direct STDIO service as the independently testable MVP. Add HTTP and cross-session stress only after the same service is authoritative. Retain the legacy route solely as a disabled-by-default delegate and remove every global/recent authorization fallback before completion.
