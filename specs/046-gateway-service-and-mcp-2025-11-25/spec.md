# Feature Specification: Gateway Service and MCP 2025-11-25

**Feature Branch**: `codex/046-gateway-service-and-mcp-2025-11-25`

**Created**: 2026-07-11

**Status**: Complete

**Input**: Implement the approved roadmap's provider-neutral GatewayService, immutable workspace/session binding, owned MCP lifecycle and catalog, MCP 2025-11-25 STDIO and authenticated Streamable HTTP transports, structured tools/resources, notifications, cancellation, policy enforcement, and audit semantics.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Use Wright Directly from an MCP Host (Priority: P1)

An engineer connects an MCP-compatible host directly to Wright and discovers and calls the engineering tools authorized for one explicitly selected workspace without depending on Hermes.

**Why this priority**: Direct, provider-neutral MCP is the feature's primary value and removes a fragile mandatory intermediary.

**Independent Test**: Start a local Wright MCP connection with an explicit workspace, negotiate the supported protocol, list tools, call a safe tool, and observe a structured result.

**Acceptance Scenarios**:

1. **Given** an authenticated engineer and explicit workspace binding, **When** the host initializes and lists tools, **Then** only tools authorized for that workspace are returned.
2. **Given** a listed safe tool, **When** the host calls it with valid input, **Then** Wright returns structured content matching the advertised output contract and records the decision.
3. **Given** no explicit workspace binding, **When** a host requests tools or calls a tool, **Then** Wright fails closed without selecting a recent or globally active workspace.

---

### User Story 2 - Keep Concurrent Sessions Isolated (Priority: P1)

Two engineers or host processes use Wright concurrently without seeing or invoking each other's workspace tools, resources, approvals, tasks, or notifications.

**Why this priority**: Cross-session fallback is a security defect and must be closed before direct host support is credible.

**Independent Test**: Bind two simultaneous sessions to different workspaces, configure disjoint tool sets, and prove list, call, resource, notification, cancellation, and reconnect behavior remains isolated.

**Acceptance Scenarios**:

1. **Given** two sessions bound to different workspaces, **When** both list tools and resources concurrently, **Then** each receives only its own authorized view.
2. **Given** one session names another session's tool, resource, task, or request, **When** it attempts access or cancellation, **Then** Wright rejects or ignores the request without disclosing foreign state.
3. **Given** an HTTP transport reconnect, **When** the authenticated principal and session resume, **Then** the original immutable workspace binding is retained and cannot be rebound in place.

---

### User Story 3 - Operate MCP Servers Reliably (Priority: P1)

An operator can reconcile, restart, stop, and shut down configured MCP servers without duplicate processes, stale generations, leaked tasks, or partially applied catalog state.

**Why this priority**: A compliant gateway cannot be reliable while lifecycle operations race or leak subprocesses.

**Independent Test**: Exercise concurrent starts, restarts, failures, cancellation, timeout, reconciliation, and shutdown while tracking runner generations and background tasks.

**Acceptance Scenarios**:

1. **Given** concurrent start or restart requests for one server, **When** reconciliation completes, **Then** exactly one current generation is active.
2. **Given** a superseded or failed generation, **When** its work completes late, **Then** it cannot overwrite the current generation's status or tools.
3. **Given** application shutdown, **When** the grace period expires, **Then** all owned runners and tasks are stopped or reported with bounded failure diagnostics.

---

### User Story 4 - Receive Accurate Catalog and Change Information (Priority: P2)

An engineer sees a single, provenance-bearing catalog with reviewed safety metadata and receives scoped change notifications when their available tools or resources change.

**Why this priority**: Hosts need trustworthy descriptions and list-change signals, while Wright policy—not client hints—must remain authoritative.

**Independent Test**: Load the packaged catalog, verify schema and parity, change one workspace's configuration, and observe only that session's relevant list-change notification.

**Acceptance Scenarios**:

1. **Given** the packaged catalog, **When** any Wright surface loads it, **Then** IDs, counts, descriptions, provenance, validation state, annotations, and schemas are identical.
2. **Given** incomplete clean-container evidence, **When** catalog validation state is evaluated, **Then** the entry is not represented as passed.
3. **Given** a workspace-specific change, **When** notifications are emitted, **Then** unrelated sessions receive no change signal.

### Edge Cases

- Unsupported or missing protocol versions and missing initialization completion.
- Malformed JSON-RPC, duplicate request IDs, notifications with IDs, batches, and unknown methods.
- Cancellation before dispatch, during startup, during a tool call, after completion, and from a foreign session.
- HTTP requests with missing or invalid Origin, bearer/session identity, protocol header, or stale session identifier.
- STDIO partial reads, concurrent notifications and responses, client EOF, broken stdout, and shutdown escalation.
- Catalog resource corruption, duplicate IDs, unknown metadata, legacy IDs, and wheel/resource omission.
- Server start/stop races, timeout, crash, late completion, and application shutdown during reconciliation.
- Tool results containing binary artifacts, validation errors, provider failures, secret-like diagnostics, or output that does not match the advertised schema.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Wright MUST provide one provider-neutral gateway service used by every MCP transport and compatibility surface.
- **FR-002**: Every connection MUST bind to one explicit immutable workspace and authenticated session or process identity before workspace-scoped discovery or execution.
- **FR-003**: Wright MUST NOT use recent activity, a process-global active workspace, or another session's state as an authorization or routing fallback.
- **FR-004**: Concurrent sessions MUST isolate tools, resources, approvals, audit records, in-flight requests, tasks, notifications, and cancellation authority.
- **FR-005**: Wright MUST negotiate MCP protocol versions and support the approved 2025-11-25 lifecycle and capability semantics while returning stable errors for unsupported versions.
- **FR-006**: Wright MUST provide a standards-compliant STDIO transport with serialized writes, clean EOF handling, bounded shutdown, and no protocol bytes written to diagnostic output.
- **FR-007**: Wright MUST expose authenticated Streamable HTTP on `/mcp` with origin validation, protocol headers, session/principal binding, reconnect behavior, request limits, and loopback-safe defaults.
- **FR-008**: Existing REST/SSE gateway behavior MUST remain available only through an explicit one-release compatibility switch and MUST delegate to the same gateway service.
- **FR-009**: Wright MUST support initialize, ping, tools list/call, resources list/read, list-change notifications, cancellation, progress-compatible execution, and stable JSON-RPC errors required by the supported host matrix.
- **FR-010**: All request execution MUST have configurable operation and maximum timeouts; cancellation MUST target only an in-progress request owned by the same session.
- **FR-011**: Tool discovery MUST return only installed, enabled, workspace-authorized tools with stable names, reviewed descriptions, input schemas, output schemas, and safety annotations.
- **FR-012**: Tool calls MUST validate inputs and outputs, return structured results plus compatible human-readable content, and use stable redacted failure results.
- **FR-013**: Client approval and MCP safety annotations MUST be treated as hints; Wright's server-side policy MUST independently authorize every start and call.
- **FR-014**: Every policy decision and tool execution MUST produce a redacted audit record correlated to principal, session, workspace, server, tool, request, outcome, and duration.
- **FR-015**: Wright MUST expose task-oriented management tools for safe server/catalog/workspace operations rather than mechanically exposing internal CRUD endpoints.
- **FR-016**: Wright MUST expose catalog, workspace, and artifact resources without allowing path escape or cross-workspace access.
- **FR-017**: Tool and resource changes MUST emit session-scoped list-change notifications without interleaving or corrupting concurrent transport writes.
- **FR-018**: MCP server lifecycle MUST be owned by a coordinator with per-server locking, monotonically increasing generations, awaitable reconciliation, cancellation, bounded timeouts, and graceful shutdown.
- **FR-019**: Late results from superseded lifecycle generations MUST NOT mutate current status, runner ownership, or discovered tools.
- **FR-020**: The existing manager API MUST delegate to the coordinator during one compatibility release without exposing coordinator internals to routes.
- **FR-021**: Catalog data MUST have one schema-validated packaged source consumed by API, gateway, and optional integrations; duplicated Python and YAML catalogs MUST be removed or generated from that source.
- **FR-022**: Catalog entries MUST include stable identity, provenance, reviewed safety metadata, validation date/evidence status, and migration aliases where legacy IDs exist.
- **FR-023**: Validation status MUST fail closed: incomplete clean-container evidence MUST never be presented as passed.
- **FR-024**: Host configuration updates MUST merge atomically, preserve unrelated entries and supported comments, and never replace an entire configuration map.
- **FR-025**: The implementation MUST remain offline-first and MUST NOT add engineering host applications to the base image or require Hermes for Codex use.
- **FR-026**: Startup MUST fail closed when the gateway service, catalog resource, lifecycle coordinator, or required security binding cannot be constructed.
- **FR-027**: Shutdown MUST close HTTP/STDIO sessions, cancel owned work, stop child runners, and report bounded cleanup failures without leaking secrets.
- **FR-028**: Compatibility claims MUST record exact Codex, SDK, protocol, OS, and verification-date evidence and MUST not claim untested hosts.

### Key Entities

- **Gateway Session**: Authenticated connection identity with immutable workspace binding, transport, principal, negotiated protocol, capabilities, and lifecycle state.
- **Gateway Request**: Session-owned request with ID, method, deadline, cancellation state, correlation data, and terminal outcome.
- **Gateway Tool/Resource**: Workspace-authorized protocol projection with schemas, annotations, provenance, and stable identity.
- **Lifecycle Generation**: One serialized server-runner ownership epoch whose late work cannot supersede a newer epoch.
- **Catalog Entry**: Canonical packaged description of a server and its tools, including provenance and validation evidence.
- **Audit Decision**: Redacted record of policy input identity, decision, reason, execution outcome, and duration.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In 100 repeated two-session concurrency trials, no session can list, read, call, cancel, or receive notifications for the other session's workspace.
- **SC-002**: All supported initialization, discovery, execution, cancellation, reconnect, notification, and error fixtures pass against both STDIO and HTTP transports.
- **SC-003**: One hundred concurrent protocol responses and notifications are individually decodable with zero interleaved or malformed messages.
- **SC-004**: Concurrent start/restart/stop trials leave exactly one current runner generation and zero leaked owned tasks or processes after shutdown.
- **SC-005**: The canonical catalog has exact ID/count/metadata parity across every consuming surface and is present in built wheel and source artifacts.
- **SC-006**: One hundred percent of advertised tools have reviewed input/output contracts, safety annotations, provenance, and fail-closed authorization coverage.
- **SC-007**: Invalid authentication, origin, workspace binding, protocol version, session, schema, policy, or cancellation requests fail closed with stable redacted errors.
- **SC-008**: Codex CLI 0.144.1 on Windows completes initialize, tools/list, a safe tools/call, list-change, concurrency, and error smoke scenarios with recorded evidence.
- **SC-009**: Graceful shutdown completes within the configured bound and reports zero live coordinator tasks or runners.

## Assumptions

- The approved target protocol is MCP 2025-11-25 even if a newer protocol exists; later versions require a separately verified compatibility change.
- The official stable MCP Python SDK line is used with an upper bound before its next major release; prerelease SDK behavior is out of scope.
- Existing Feature 042 authentication and Feature 045 composition/path boundaries remain authoritative.
- The first HTTP mode is local-first bearer/session authenticated; deployment-grade remote OAuth remains a later deployment feature, but the interface must not prevent it.
- MCP experimental durable tasks are not required for this feature; request cancellation and task-oriented Wright management tools are required.
- The optional Hermes integration is a consumer of this service and remains Feature 049 scope.
- The Codex plugin/config installer and public CLI bridge remain Features 047–048 scope.
