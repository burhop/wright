# Feature 046 Completion Audit

Audited against the implemented tree on 2026-07-12. “Proved” means the named
source and executable test/gate directly exercise the requirement; a passing
neighboring test was not used as a substitute.

## Functional requirements

| Requirement | Result | Authoritative evidence |
| --- | --- | --- |
| FR-001 | Proved | `GatewayService`; API composition, SDK server, STDIO, HTTP, and legacy delegates all use the same instance; architecture fitness test. |
| FR-002 | Proved | Immutable `GatewaySessionContext`, exact repository binding, unique HTTP transport sessions; model/repository/HTTP/STDIO tests. |
| FR-003 | Proved | Production call search has no global/recent gateway reader/writer; explicit legacy and foreign-binding tests. |
| FR-004 | Proved | Composite request ownership, workspace notifier queues, unique HTTP managers; 100-trial isolation and foreign cancellation tests. |
| FR-005 | Proved | Official SDK negotiation, fixed `2025-11-25` service check, stable `unsupported_protocol`; SDK/model tests. |
| FR-006 | Proved | SDK `stdio_server`, serialized SDK writer, real split-frame/EOF subprocess, 100 concurrent response test. |
| FR-007 | Proved | `/mcp` controller plus control-plane auth, Origin/DNS rebinding, body/rate/concurrency/session limits; API and SDK HTTP tests. |
| FR-008 | Proved | `WRIGHT_LEGACY_GATEWAY` defaults off; REST/SSE and launcher explicitly bind and delegate; compatibility tests. |
| FR-009 | Proved | SDK server handlers/capabilities, built-in ping, list/call/read, cancellation and list-change tests; SDK supplies stable JSON-RPC method errors. |
| FR-010 | Proved | Configured operation/maximum bounds and same-session request map; timeout, protocol cancellation, and foreign cancellation tests. |
| FR-011 | Proved | Database catalog adapter filters installed/enabled/workspace tools and supplies stable names, input/output schemas, conservative reviewed annotations and provenance. |
| FR-012 | Proved | JSON Schema input/output validation, structured plus text content, stable redacted errors; result/server/HTTP tests. |
| FR-013 | Proved | `GatewayPolicy` and lifecycle safety independently authorize; approval-hint denial test. |
| FR-014 | Proved | Discovery and execution decisions append redacted correlated audit rows; repository, service, and policy tests. |
| FR-015 | Proved | Three read-only task-oriented Wright status tools; management tests. |
| FR-016 | Proved | Catalog/bound-workspace/artifact resources, foreign workspace refusal, decoded traversal/backslash rejection; resource tests. |
| FR-017 | Proved | Workspace-keyed hub, SDK notification pump, production API change publishing; scoped notification and 100-message tests. |
| FR-018 | Proved | Per-server locks, generations, reconciliation, timeout/cancellation/shutdown; lifecycle suites. |
| FR-019 | Proved | Generation-current checks guard runner, status and tool publication; late-completion tests. |
| FR-020 | Proved | `McpEngine` delegates coordinated transports/lifecycle while routes use service ports; manager/API regressions and boundary test. |
| FR-021 | Proved | One packaged YAML plus JSON Schema; Python/plugin are loaders/projections; parity and distribution tests. |
| FR-022 | Proved | Canonical model contains identity/source, risk/approval, dated evidence status and aliases; schema/catalog tests. |
| FR-023 | Proved | Passed validation requires environment, date and recorded evidence; fail-closed Pydantic test. |
| FR-024 | Proved | Existing Feature 043 merge-only atomic configuration writer remains the only update path; provider/Hermes sync regression suites pass in the dev gate. |
| FR-025 | Proved | Local STDIO/loopback HTTP require no Hermes; no image/host dependency change; real Codex direct smoke. |
| FR-026 | Proved | Migration/catalog/security/composition occur before readiness; startup ordering/failure tests. |
| FR-027 | Proved | Session-owned cancellation, SDK EOF/DELETE, coordinator bounded stop and zero live runner/task assertions; shutdown tests. |
| FR-028 | Proved | Research and Codex compatibility document record exact CLI/SDK/protocol/Windows/date and explicitly disclaim untested hosts. |

## Success criteria

| Criterion | Result | Authoritative evidence |
| --- | --- | --- |
| SC-001 | Proved | `test_gateway_isolation.py`: 100 two-session list/read/call/cancel trials; notification isolation separately exercises foreign workspace signals. |
| SC-002 | Proved | Official SDK in-memory, real STDIO, API HTTP, and SDK HTTP suites cover initialization, discovery, execution, cancellation handler, reconnect identity, notification pump and stable errors through the shared server. |
| SC-003 | Proved | `test_gateway_concurrency.py` and STDIO stress: 100 responses amid 100 notifications, all decoded. |
| SC-004 | Proved | Lifecycle concurrent generation/late result suites and bounded shutdown assert one current runner then zero runner/task ownership. |
| SC-005 | Proved | 42-entry canonical/plugin byte parity; wheel and sdist archive tests plus clean-install distribution build. |
| SC-006 | Proved | Production child and built-in tool adapters attach input/output contracts, annotations and provenance; discovery always passes server policy; focused schema/policy tests. |
| SC-007 | Proved | Auth/Origin/binding/session/body, unsupported protocol, schema, policy, foreign tool/resource/cancellation and redaction tests. |
| SC-008 | Proved | Ephemeral real `codex-cli 0.144.1` Windows x64 / `gpt-5.6-sol` run: initialize/list, one stable invalid-input failure, two concurrent successful calls, list-change delivery, exact workspace/session result, exit 0. |
| SC-009 | Proved | Bounded coordinator shutdown test completes under 0.1 seconds with zero live runners and owned tasks; API lifespan awaits service shutdown. |

## Required gates

- Focused Feature 046 regression scope: 313 passed, 2 skipped (the live Codex
  pytest switch and an existing platform-specific path case), one existing
  Starlette deprecation warning.
- Tool-registry suite after test packaging: 82 passed.
- Focused mypy: 17 production files, zero findings.
- Core/tool-registry wheel and sdist build plus exact-wheel clean install: passed.
- Strict MkDocs, public-alpha scan, import-boundary suite and `git diff --check`: passed.
- Real Codex expanded compatibility harness: all summary fields passed, three
  calls observed, maximum in-flight two.
- Final `scripts/check-dev-merge.sh`: passed all configured sub-gates without
  skips in 441 seconds; 473 Python tests were collected, frontend lint/type/unit/
  build and live Playwright passed. Repository-wide mypy remains warning-mode and
  reported only the known duplicate `conftest` module-name discovery issue;
  focused mypy for all 17 Feature 046 production modules passed with zero findings.
