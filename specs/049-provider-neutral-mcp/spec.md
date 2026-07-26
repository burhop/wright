# Feature Specification: Provider-Neutral MCP Integration

**Feature Branch**: `049-provider-neutral-mcp`

**Created**: 2026-07-26

**Status**: Draft

**Input**: User description: "Treat SolidEdgeMCP like any other MCP server while preserving its working user workflow and removing provider-specific behavior from Wright core."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Use Any Workspace-Aware MCP Server (Priority: P1)

An engineer enables a local MCP server for a workspace and uses the tools exactly as the server advertises them. Wright supplies only the workspace access explicitly approved by the engineer, regardless of the server's name or vendor.

**Why this priority**: Generic, secure tool execution is Wright's core responsibility and is required to preserve the existing Solid Edge creation workflow without retaining a special-case integration.

**Independent Test**: Configure two differently named synthetic MCP servers with the same workspace-binding requirements, invoke each through Wright, and verify that both receive the authorized workspace, expose their advertised tools unchanged, and produce workspace-confined output.

**Acceptance Scenarios**:

1. **Given** a trusted local server configuration that requests the active workspace, **When** Wright starts the server for that workspace, **Then** the canonical workspace location is supplied through the configured launch binding without shell interpretation.
2. **Given** a server that does not request workspace binding, **When** Wright starts it, **Then** its command and environment remain unchanged.
3. **Given** two servers with different identities but equivalent configurations, **When** users discover and call their tools, **Then** Wright applies identical lifecycle, authorization, timeout, and audit behavior.
4. **Given** SolidEdgeMCP configured through the generic mechanism, **When** an engineer performs the representative part-creation workflow, **Then** the part is saved under the selected workspace without a blocking dialog and Wright uses no provider-specific runtime behavior.

---

### User Story 2 - See Honest Generic Tool Progress (Priority: P2)

An engineer sees progress from any long-running MCP tool using the server's own tool title and progress message, with a useful generic fallback when the server supplies no message.

**Why this priority**: Long-running engineering operations need visible, trustworthy status, but Wright should not interpret provider-specific tool names or claim application states it cannot independently verify.

**Independent Test**: Stream progress from synthetic servers using different tool names, including missing messages, cancellation, failure, and timeout, then verify ordered session-scoped progress and exactly one terminal state for every call.

**Acceptance Scenarios**:

1. **Given** a tool that supplies monotonic progress and messages, **When** it runs, **Then** Wright forwards the values and messages without provider-specific translation.
2. **Given** a tool that supplies no human-readable message, **When** it runs, **Then** Wright displays a fallback based on the advertised tool title or name.
3. **Given** concurrent sessions, **When** both receive progress, **Then** events remain correlated with the correct workspace, session, request, server, and tool.
4. **Given** success, failure, cancellation, or timeout, **When** the call ends, **Then** progress ends with one matching terminal state and does not continue afterward.

---

### User Story 3 - Operate and Migrate Servers Safely (Priority: P3)

An administrator manages Wright-owned and externally owned MCP processes, rebinds workspaces, and migrates existing catalog entries without changing application code for each server.

**Why this priority**: Provider neutrality must not regress runtime ownership, Hermes rebinding, multiple sessions, health reporting, or the recently corrected operation timeout.

**Independent Test**: Exercise managed and externally managed synthetic servers across startup, rebinding, concurrent calls, cancellation, timeout, and shutdown while verifying stable health and configuration behavior.

**Acceptance Scenarios**:

1. **Given** an externally managed server, **When** a workspace is activated or rebound, **Then** Wright does not start a duplicate process and continues to report passive health accurately.
2. **Given** a Wright-managed server, **When** its workspace binding changes, **Then** Wright applies the updated declarative binding using the same generic lifecycle used for every managed server.
3. **Given** a configured operation timeout, **When** any server call exceeds it, **Then** Wright terminates the call with a correlated timeout result at the configured boundary.
4. **Given** an existing catalog configuration, **When** it is migrated to declarative workspace binding, **Then** rollback instructions restore the prior configuration without a state-database migration.

### Edge Cases

- A workspace path contains spaces, Unicode, quotes, percent signs, braces, or shell metacharacters.
- A trusted configuration references an unknown placeholder or attempts to interpolate outside the approved workspace fields.
- A server changes its advertised tool list after startup.
- A server sends decreasing, duplicate, malformed, or late progress updates.
- A tool title is absent or contains untrusted markup-like content.
- A session is cancelled or disconnected while a tool call is active.
- Multiple sessions share one server process while using different workspace bindings.
- Workspace rebinding occurs while the externally owned Hermes gateway is temporarily unavailable.
- A legacy catalog record contains the existing server-specific environment setting but the server-side neutral contract has not yet shipped.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Wright MUST launch and connect to MCP servers without branching on server name, vendor, repository, tool name, or application identity.
- **FR-002**: Trusted server configuration MUST be able to request the active canonical workspace through declarative command-argument or environment-value bindings available to every local MCP server.
- **FR-003**: Workspace bindings MUST be passed as literal process arguments or environment values without shell evaluation.
- **FR-004**: Only trusted local or catalog configuration MUST be permitted to request workspace interpolation; server-supplied tool metadata MUST NOT grant filesystem access or approval capabilities.
- **FR-005**: Unknown, malformed, or unauthorized placeholders MUST fail closed with an actionable configuration error.
- **FR-006**: Servers without workspace bindings MUST retain their existing launch command and environment unchanged.
- **FR-007**: Wright MUST expose the tool set and schemas advertised by each server without provider-specific filtering.
- **FR-008**: Wright MUST retain provider-neutral authorization, user tool enablement, approval, timeout, auditing, and workspace-session controls.
- **FR-009**: Agent guidance supplied by Wright MUST NOT prescribe provider-specific tools, arguments, modeling sequences, or application states.
- **FR-010**: Wright MUST forward server-provided progress using generic server, tool, progress, total, message, elapsed-time, correlation, and terminal-state information.
- **FR-011**: When a server provides no progress message, Wright MUST produce a generic fallback derived from the advertised tool title or name.
- **FR-012**: Wright MUST keep progress monotonic, session-scoped, resumable where already supported, and terminally closed on success, failure, cancellation, or timeout.
- **FR-013**: Runtime ownership MUST remain generic and MUST prevent duplicate subprocess ownership for externally managed servers.
- **FR-014**: Workspace rebinding, health reporting, operation timeouts, cancellation, concurrency, and shutdown MUST behave consistently across server identities.
- **FR-015**: The existing Solid Edge workflow MUST remain operable through ordinary catalog configuration while the external server contract migrates.
- **FR-016**: Required cross-platform Wright validation MUST use synthetic MCP servers and MUST NOT install or depend on Solid Edge or the SolidEdgeMCP repository.
- **FR-017**: Live application compatibility validation MUST remain optional, host-scoped, and distinct from clean-container catalog validation.
- **FR-018**: Migration and rollback guidance MUST identify the declarative configuration changes and every removed provider-specific runtime behavior.
- **FR-019**: Logs and diagnostics MUST redact configured secrets and MUST NOT expose untrusted launch values beyond existing safe diagnostic policy.
- **FR-020**: Existing Hermes gateway rebinding and configured MCP operation-timeout behavior MUST remain covered by regression tests.

### Key Entities

- **Server Launch Configuration**: Trusted configuration describing a local server's executable, literal arguments, environment, transport, ownership, timeout, and optional workspace bindings.
- **Workspace Binding**: An authorized substitution of a canonical active-workspace value into a configured process argument or environment value.
- **Advertised Tool**: A server-provided tool identity, title, description, input/output schemas, and descriptive annotations projected through Wright without provider-specific filtering.
- **Tool Progress Event**: A request-correlated progress update containing server and tool identity, numeric progress, optional total/message, elapsed time, and lifecycle state.
- **Runtime Ownership**: The generic declaration of whether Wright or an external host owns a server process.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Two differently named synthetic MCP servers with equivalent configurations pass the same launch, binding, discovery, call, timeout, cancellation, and progress contract with no identity-dependent result differences.
- **SC-002**: 100% of tested workspace paths containing spaces and shell-significant characters are delivered literally and remain confined to the selected workspace.
- **SC-003**: 100% of progress-enabled test calls produce monotonic, correctly correlated events and exactly one matching terminal state.
- **SC-004**: The representative live Solid Edge creation workflow completes in one advertised high-level tool call, saves the exact requested file under the selected workspace, and displays no blocking save dialog.
- **SC-005**: Required Wright validation completes without installing, cloning, or executing Solid Edge or SolidEdgeMCP.
- **SC-006**: A runtime-source audit finds zero provider-specific branches, prompts, progress mappings, or workspace-injection logic for Solid Edge; ordinary catalog records and operator documentation are excluded from this count.
- **SC-007**: All existing generic MCP, Hermes rebinding, concurrent-session, and operation-timeout regression tests pass with no behavioral regression.
- **SC-008**: Server-provided progress becomes visible to the user within one normal stream update interval, and no progress event appears after terminal completion.

## Assumptions

- SolidEdgeMCP remains an independently installed and versioned local MCP server.
- Its current explicit output-path, allowed-root, overwrite, and structured-result behavior remains available during migration.
- Until its neutral launch contract is released, the existing allowed-root environment setting may remain in ordinary catalog data but not in Wright runtime code.
- Provider-specific modeling semantics, save behavior, tool guidance, and application visibility belong to the external MCP server.
- Wright administrators continue to approve local server installation, credentials, workspace access, and destructive operations.
- Existing state storage and catalog migration mechanisms are sufficient; no destructive database migration is expected.
- The optional Windows live smoke may be blocked when Solid Edge or the matching external server build is unavailable, but that limitation does not weaken generic contract validation.
