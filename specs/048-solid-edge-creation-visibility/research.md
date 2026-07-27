# Research: Solid Edge Creation Visibility

## Authoritative enforcement point

**Decision**: Enforce the Solid Edge creation profile in `tool_registry` through the existing `GatewayService` and `GatewayPolicy`, with an immutable profile identifier on `GatewaySessionContext`.

**Rationale**: Feature 046 already makes GatewayService the provider-neutral discovery/call authority for Codex, Hermes, STDIO, HTTP, and the compatibility adapter. Filtering only in `.hermes.md` or an agent prompt would still expose inspection tools and would not stop a direct MCP call.

**Alternatives considered**: Prompt-only guidance was rejected as advisory. Filtering only in Hermes was rejected because other hosts would see a different safety boundary. Modifying SolidEdgeMCP globally was rejected because Wright needs a session-specific projection and the external server also serves validation and operator workflows.

## Profile selection and tool classification

**Decision**: Select `solid_edge_creation_v1` explicitly when opening a Solid Edge creation session. Identify the target server from authoritative configured server metadata and classify tools by exact child tool name into creation, validation, created-artifact follow-up, service-status, inspection, or unknown. Unknown Solid Edge tools fail closed.

**Rationale**: Database server records already carry stable server identity, source, host-software requirements, and discovered exact tool names. An allowlist tolerates no accidental exposure when SolidEdgeMCP adds new document, face, variable, dimension, capability, semantic, or repair operations.

**Alternatives considered**: Name-substring blocklists were rejected because new inspection tools would be visible by default. Treating every `cad.*` operation as safe was rejected because the local SolidEdgeMCP currently exposes broad document, measurement, inventory, semantic-resolution, and repair operations.

## Creation profile surface

**Decision**: The profile exposes service status, recipe validation, and new-document creation operations. Rebuild/export operations are available only for an artifact created by the current bound session and are unnecessary for the simple-part smoke. Read-only document/geometry inventories, measurement, capabilities, semantic resolution, close/open, repair, and mutation of selected existing documents are hidden and denied.

**Rationale**: The feature specification names creation, validation, export, rebuild, and service status while requiring zero inspection calls and protection of pre-existing documents. A created-artifact binding makes follow-up operations safe without granting ambient access to the active document.

**Alternatives considered**: Exposing all non-destructive calls was rejected because even read-only active-document queries violate the workflow and add planning cost. Removing all status and validation calls was rejected because actionable preflight errors and availability diagnostics are required.

## New-document and path invariants

**Decision**: Validate creation calls before child execution: `providerId` is `solid_edge`; `outputPath` is explicit and resolves under the session workspace/approved provider root; `visible` is true; `closeAfterSave` is false unless the user explicitly requested closure; overwrite is false unless explicitly authorized for that exact path; and the recipe is commit/new-document work. Use the canonical `centered_rectangle` on `top` followed by an extrusion whose direction is `positive_normal` for the box smoke.

**Rationale**: Local SolidEdgeMCP documentation and tests confirm `cad.create_part_from_recipe`, `outputPath`, `visible`, `closeAfterSave`, commit recipes, and the `positive_normal` direction. Wright must add its own workspace confinement and intent checks before delegating to the provider.

**Alternatives considered**: Relying only on provider allowed roots was rejected because Wright's session workspace is a narrower authorization boundary. Inferring overwrite or closure from a generic creation request was rejected because those actions can destroy evidence or affect unrelated user state.

## Verification without agent inspection

**Decision**: Treat the creation operation's structured result plus confined file evidence as the production success contract. The Windows live test harness, not the agent-visible tool set, records the before/after open-document identities and visible/open state. The agent performs no post-creation inspection call in the bounded smoke.

**Rationale**: Proving that a pre-existing document is unchanged is necessary, but exposing document inventory to the model would violate the creation profile. Test-only host evidence can establish the invariant without broadening production discovery or call counts.

**Alternatives considered**: Letting the agent call `cad.get_active_document`, `cad.list_documents`, or geometry measurements after creation was rejected by FR-005, FR-006, and SC-008. Omitting live evidence was rejected because file existence alone does not prove visibility or document isolation.

## Progress and replay model

**Decision**: Emit a planning event synchronously when a turn starts, use monotonic clocks, emit a heartbeat no later than every 10 seconds, and normalize tool progress into stable phases: planning, capability discovery, Solid Edge creation, saving, verification, result transfer, and final response. Store indexed events in a bounded active/recent-turn buffer so reconnect can resume after an event index.

**Rationale**: The existing chat stream already supports indexed replay and can be extended without a second transport. Stable human labels decouple the UI from internal MCP-prefixed names, and monotonic time avoids wall-clock changes.

**Alternatives considered**: Unstructured text-only updates were rejected because timing attribution and reconnect need typed phases. Persisting every token/event indefinitely in SQLite was rejected as unnecessary for active/recent replay and would increase sensitive-data retention.

## End-to-end timing and diagnostic storage

**Decision**: Reuse append-only `gateway_audit_events`, recording a started event and exactly one terminal event for every call. Carry turn, request, and operation correlation identifiers; store operation/tool identity, outcome, duration, argument count, bounded timeout, request/response byte counts, and phase timestamps, but never arguments, results, credentials, or protocol bodies. Aggregate active, completed, outcomes, total/average/max, and slowest calls in a package service.

**Rationale**: Feature 046 already provides the audit repository and redaction at persistence. Metadata JSON can evolve additively without a database migration. A package-level query/aggregation service keeps FastAPI routes translation-only.

**Alternatives considered**: Log scraping was rejected because it cannot reliably pair concurrent started/terminal events. A new telemetry database was rejected because the existing audit store already has session/correlation identity. Payload capture was rejected due to secrets and large CAD results.

## Protocol-safe structured logging

**Decision**: Keep structured JSON logging, but route diagnostics to stderr for STDIO MCP entry points and reserve stdout exclusively for MCP framing. HTTP processes may continue logging to stdout.

**Rationale**: Any diagnostic line on STDIO stdout can corrupt JSON-RPC. The existing logging factory can accept an explicit stream without introducing file I/O.

**Alternatives considered**: Disabling all STDIO diagnostics was rejected because slow/failing child operations must remain diagnosable. Writing a local log file by default was rejected due to import-time side effects, retention, and workspace ownership concerns.

## Runtime ownership

**Decision**: Represent runtime ownership explicitly as API-owned or external/Hermes-owned. In external mode the API constructs read/query services but performs no startup, reconciliation, stop, or status-poll side effects. Only the owner may manage the child process.

**Rationale**: Current API startup and workspace status paths can reconcile MCP servers. An explicit owner prevents duplicate Solid Edge automation processes while preserving UI visibility and authenticated health queries.

**Alternatives considered**: Process detection and best-effort deduplication were rejected because two components can race. A global lock alone was rejected because lifecycle authority would still be ambiguous across processes.

## Hermes authentication

**Decision**: Every Hermes bridge call to protected Wright routes sends the configured bearer token through an in-memory header helper and fails with the protected endpoint's actionable response when unavailable or invalid.

**Rationale**: Feature 042 protects local control-plane routes. Passive polling must preserve that security boundary and must not fall back to anonymous compatibility behavior.

**Alternatives considered**: Query-string credentials were rejected because they leak through logs/history. Disabling authentication for loopback status routes was rejected due to the established local control-plane threat model.

## Validation boundary

**Decision**: Use fast fake-provider/transport tests for CI and a separate operator-invoked Windows live Solid Edge suite for visibility, isolation, latency, and subprocess-count evidence. Do not change catalog validation status from this suite and do not add Solid Edge or SolidEdgeMCP host dependencies to the base image.

**Rationale**: `docs/mcp-catalog/mcp-server-testing-process.md` requires clean-container evidence for catalog validation and forbids MCP-specific host software in the base image. Proprietary Windows host behavior cannot honestly be represented as a Linux clean-container pass.

**Alternatives considered**: Running Solid Edge in CI/OCI was rejected as unavailable and contrary to the container boundary. Treating a mock pass as live validation was rejected because visibility and COM ownership require the real workstation.

## Local evidence consulted

- Feature 046 GatewayService plan, contracts, and implementation in this repository.
- Feature 042 authentication and workspace-confinement behavior in this repository.
- `docs/mcp-catalog/mcp-server-testing-process.md`.
- Local `D:\repos\SolidEdgeMCP` README, smoke tests, provider capability declarations, and live benchmark fixtures as inspected on 2026-07-16.
