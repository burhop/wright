# Feature Specification: Rivet Workspace MCP Gateway Execution

**Feature Branch**: `069-rivet-mcp-gateway`

**Created**: 2026-08-13

**Status**: Draft

**Input**: User description: "Enable Rivet workflows to discover and invoke workspace-enabled MCP tools only through short-lived, run-bound Wright gateway authority, with reviewed bindings, approvals, progress, cancellation, audit, and deterministic coverage for multiple child MCPs."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Bind workspace tools while reviewing a workflow (Priority: P1)

An engineer opens a Rivet workflow in a Wright workspace and can inspect the exact MCP capabilities available to that workspace. The engineer resolves each workflow requirement to a namespaced tool, sees the tool's current schema and risk information, and submits the exact workflow revision and bindings for review.

**Why this priority**: A workflow cannot safely execute an MCP call until the user can see which workspace capability it means and approve an exact, reproducible binding.

**Independent Test**: Enable two deterministic MCP servers for one workspace, author a workflow that requires one tool from each, resolve both bindings, and verify that the review shows exact server, tool, schema, workspace, and workflow identities without invoking either tool.

**Acceptance Scenarios**:

1. **Given** two servers expose the same unqualified tool name, **When** an engineer reviews discovery, **Then** both tools appear with distinct stable namespace-qualified identities and current schemas.
2. **Given** a workflow requirement has one compatible workspace-enabled tool, **When** the engineer resolves it, **Then** the binding records the concrete server, tool, schema, capability evidence, and workflow revision.
3. **Given** no current workspace-enabled tool satisfies a requirement, **When** review begins, **Then** execution is blocked and the missing or incompatible requirement is explained without changing the workspace.
4. **Given** a binding exists, **When** the server, tool schema, workspace grant, selected graph, or workflow revision changes, **Then** the prior review becomes stale and cannot authorize a run.

---

### User Story 2 - Execute a reviewed multi-MCP workflow (Priority: P1)

An engineer starts an exact reviewed Rivet workflow that calls multiple workspace-enabled MCP tools. Wright grants that one run only the reviewed bindings, mediates every call through the workspace gateway, applies the same policy and approval rules used by other Wright clients, and returns structured results to the workflow.

**Why this priority**: This is the core outcome: Rivet can drive engineering applications and services without becoming a second MCP manager or bypassing Wright controls.

**Independent Test**: Run a deterministic graph through Wright that calls one tool on each of two fake MCP servers and verify ordered child calls, results, approvals, audit records, artifacts, and exact run provenance.

**Acceptance Scenarios**:

1. **Given** an exact reviewed revision with two current bindings, **When** the engineer starts it, **Then** both calls travel through Wright under one run-bound authority and their structured outputs return to the correct Rivet nodes.
2. **Given** a bound call is read-only and policy permits it, **When** the node executes, **Then** Wright records the decision and result without asking for a broader workflow-level permission.
3. **Given** a bound call requires approval, **When** the node reaches it, **Then** the run pauses for the existing per-call approval decision and continues only if that exact call is approved.
4. **Given** the graph attempts an unbound, disabled, cross-workspace, schema-changed, or unreviewed call, **When** it executes, **Then** Wright denies it before child invocation and attributes the failure to the exact node and policy reason.
5. **Given** a run finishes, **When** its result is inspected, **Then** the record identifies the workflow revision, selected graph, bindings, schema snapshots, approvals, child calls, outputs, artifacts, and terminal state.

---

### User Story 3 - Cancel and recover a long MCP call (Priority: P2)

An engineer can cancel a running workflow from Wright and see cancellation propagate to the active MCP call. Wright revokes the run authority, prevents later nodes or late child responses from taking effect, and preserves a useful partial run record.

**Why this priority**: Engineering calls can be expensive or long-running; stopping them must not leave hidden authority or ambiguous results.

**Independent Test**: Start a deterministic slow child call, cancel it while active, and verify child cancellation, authority revocation, no subsequent calls, ignored late completion, cleanup status, and durable partial provenance.

**Acceptance Scenarios**:

1. **Given** a child tool is running, **When** the engineer cancels the workflow, **Then** Wright requests child cancellation, revokes the run authority, blocks later nodes, and reports whether cleanup completed.
2. **Given** a child returns after cancellation, **When** Wright receives the late result, **Then** it cannot change the terminal run state or publish an artifact as successful.
3. **Given** cancellation cannot stop an external operation immediately, **When** the cancellation deadline expires, **Then** the run records bounded residue and actionable recovery without claiming the child stopped.
4. **Given** the application restarts after a terminal or interrupted run, **When** the engineer inspects history, **Then** no prior ephemeral authority can be reused and the recorded state remains reproducible.

---

### User Story 4 - Use specialized application lifecycles through the same boundary (Priority: P2)

An engineer can run a workflow against BREP and Solid Edge, or an available substitute, while Wright preserves each integration's specialized startup, visible-panel, host-connection, progress, and shutdown behavior behind the same gateway-facing call contract.

**Why this priority**: A generic fake path is insufficient if real engineering integrations require lifecycle coordination; specialization must remain inside Wright rather than leak into Rivet.

**Independent Test**: Exercise deterministic lifecycle doubles for a panel-backed BREP server and a host-bridge server, then optionally run explicitly enabled live probes without making proprietary software a normal prerequisite.

**Acceptance Scenarios**:

1. **Given** a bound tool needs a specialized Wright-managed lifecycle, **When** Rivet calls it, **Then** Wright prepares and monitors that lifecycle without exposing child configuration or credentials to the workflow.
2. **Given** lifecycle preparation fails or the host is unavailable, **When** the node executes, **Then** the run receives a stable attributed error and no later call assumes the application started.
3. **Given** credentials or proprietary applications are unavailable in normal validation, **When** deterministic tests run, **Then** all control-boundary assertions still pass and the live path remains an explicit deferred test.

---

### User Story 5 - Diagnose and reproduce a run (Priority: P3)

An engineer or administrator can inspect a bounded timeline that connects each Rivet node to its capability binding, approval, gateway call, child progress, result, artifact, and failure reason, without exposing credentials or unrestricted child output.

**Why this priority**: Multi-application engineering workflows need evidence that explains what ran and why a result can or cannot be trusted.

**Independent Test**: Complete one successful and one denied multi-tool run, export their bounded manifests, and verify that another reviewer can identify every binding and failure boundary without access to secret values.

**Acceptance Scenarios**:

1. **Given** a completed run, **When** its timeline is opened, **Then** events are ordered and correlated by run, node, call, server, tool, and trace identity.
2. **Given** child output contains secret-like or oversized content, **When** evidence is stored or displayed, **Then** it is redacted and bounded while retaining diagnostic reason codes.
3. **Given** the same workflow is prepared later, **When** any pinned identity differs, **Then** Wright reports the exact reproducibility difference and requires a new review rather than silently rebinding.

### Edge Cases

- The tool list changes between authoring, review, authority issuance, and the first call.
- Two child servers use the same server name or tool name, or a server exposes duplicate/invalid schemas.
- A workspace grant is removed or a server is disabled after a run starts but before a later node calls it.
- A reviewed binding points to a server that is installed but stopped, unhealthy, reconnecting, or awaiting a specialized host lifecycle.
- A workflow requests a capability alias that resolves to several equally valid tools or to a tool with incompatible units or semantics.
- A malicious project attempts to inject child connection settings, credentials, arbitrary headers, an unrestricted tool name, or another workspace identity.
- A request replays an expired authority, reuses it for a different run/node/tool, or races cancellation and completion.
- A child emits progress out of order, never completes, ignores cancellation, returns an oversized payload, or disconnects after producing an artifact.
- Approval is granted for one argument set but the workflow attempts different arguments or repeats a non-idempotent call.
- The runner, Wright API, gateway, or child MCP restarts during discovery or execution.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Rivet workflows MUST discover MCP tools only from the capabilities currently enabled for their bound Wright workspace.
- **FR-002**: Discovered tools MUST use stable namespace-qualified identities that prevent collisions across child servers.
- **FR-003**: Discovery MUST expose a bounded schema snapshot, risk/approval metadata, current validation identity, and compatibility state without exposing credentials or child configuration.
- **FR-004**: The system MUST support requirement-based resolution and deliberate exact implementation pinning, and MUST make ambiguous resolution block review.
- **FR-005**: Every executable MCP node MUST have a concrete Capability Binding covering workspace, server, tool, schema, validation, capability, workflow revision, selected graph, and binding digest.
- **FR-006**: Review MUST bind the exact workflow revision, graph, node set, capability bindings, tool-schema snapshots, units policy, and material argument defaults that can affect MCP calls.
- **FR-007**: A change to any review-bound identity or policy-relevant value MUST invalidate or block the prior review before execution.
- **FR-008**: Starting a reviewed workflow MUST mint a short-lived authority for one run, one workspace, one workflow revision, and the exact approved binding set.
- **FR-009**: Run authority MUST be least-privilege, non-exportable in ordinary UI or logs, time-bounded, revocable, and unusable for discovery or calls outside its claims.
- **FR-010**: Rivet MUST NOT own or persist child MCP connection definitions, credential values, long-lived gateway credentials, workspace authorization, or application lifecycle configuration.
- **FR-011**: Every Rivet MCP call MUST traverse Wright's provider-neutral workspace gateway and existing policy, approval, lifecycle, progress, result, and audit boundaries.
- **FR-012**: The runner MUST submit only a bound node/call identity and arguments; it MUST NOT be able to supply arbitrary server URLs, commands, environment variables, authorization headers, or tool namespaces.
- **FR-013**: Wright MUST revalidate the run authority, workspace grant, server state, tool identity, schema binding, review, node identity, and argument binding before each child invocation.
- **FR-014**: Disabled, cross-workspace, unreviewed, unbound, stale, expired, replayed, or policy-denied calls MUST fail before a child MCP receives them.
- **FR-015**: Approval aggregation MAY reduce duplicate prompts only when existing policy declares the calls equivalent; it MUST NOT broaden per-call scope, arguments, duration, or destructive authority.
- **FR-016**: Non-idempotent or destructive calls MUST retain exact per-call policy and approval evidence even when a workflow-level review exists.
- **FR-017**: Child progress MUST be projected to the correct Rivet run and node using ordered, bounded events and stable phases.
- **FR-018**: Structured child results and errors MUST return to the correct node with bounded content, stable reason codes, and artifact references rather than unrestricted filesystem paths.
- **FR-019**: Cancellation MUST propagate from the Wright run to the runner and active child call, revoke run authority, block later calls, and record cleanup or residue truthfully.
- **FR-020**: Late results after cancellation or terminal failure MUST NOT change the terminal state or publish success artifacts.
- **FR-021**: A timeout, gateway disconnect, child crash, or application-lifecycle failure MUST be attributed to the exact node and boundary and MUST NOT silently retry a non-idempotent call.
- **FR-022**: The system MUST preserve specialized BREP visible-panel and Solid Edge or host-bridge lifecycle behavior behind the same gateway call contract used for ordinary MCPs.
- **FR-023**: Specialized lifecycle preparation, health, progress, cancellation, and cleanup MUST remain Wright-owned and MUST NOT appear as embedded child configuration in a workflow.
- **FR-024**: A Run Manifest MUST record exact workflow, graph, review, authority, binding, schema, server revision, validation, approval, child-call, result, artifact, timing, and terminal-state identities.
- **FR-025**: Stored and displayed run evidence MUST be size-bounded and redact credential values, tokens, authorization material, secret-like arguments, and sensitive child output.
- **FR-026**: Run and node events MUST carry correlated trace identities and remain durably inspectable after restart without preserving usable ephemeral authority.
- **FR-027**: The system MUST provide actionable recovery for stale binding, removed grant, unavailable server, expired authority, denied approval, cancellation residue, and specialized host failure.
- **FR-028**: Deterministic normal tests MUST prove a workflow calling at least two fake child MCP servers through Wright, including discovery, review, execution, results, progress, approval, cancellation, and audit.
- **FR-029**: Deterministic negative tests MUST prove that disabled, cross-workspace, unreviewed, unbound, stale-schema, changed-server, expired, replayed, and post-cancellation calls never reach a child.
- **FR-030**: Optional live validation MUST define an explicitly gated BREP path and a Solid Edge or other available application path without requiring proprietary software, credentials, paid services, GPUs, network access, or hardware in normal gates.
- **FR-031**: Workflow review and execution MUST remain usable offline when all bound child capabilities are local.
- **FR-032**: Existing workflows without MCP nodes MUST retain their current review, execution, result, and rollback behavior.
- **FR-033**: Existing agent-manager and chat clients MUST continue to use the same gateway policy and workspace boundaries; Rivet MUST not introduce a privileged parallel path.
- **FR-034**: No workflow or test in this feature may start physical machinery, motion, heat, a spindle, a printer, a robot, or a PLC.

### Key Entities

- **Capability Requirement**: A portable workflow need expressed independently of one provider where practical, including semantic and units constraints.
- **Capability Binding**: The exact reviewed mapping from one workflow node and requirement to a workspace-enabled server/tool and its current evidence and schema identities.
- **Tool Schema Snapshot**: The bounded immutable input/output and annotation view reviewed for one namespaced tool revision.
- **Run Authority**: A short-lived, revocable, least-privilege grant covering one run and its exact workspace, workflow, nodes, and bindings.
- **Gateway Call Record**: One mediated node invocation with arguments digest, approval decision, child request identity, progress, result or error, and timing.
- **Run Manifest**: The durable reproducibility and diagnosis record for an exact workflow run; it records authority identity and expiry but never a reusable bearer value.
- **Cancellation Record**: The ordered request, propagation, child acknowledgement, revocation, terminal state, cleanup, and residue evidence for a stopped run.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: An engineer can discover, bind, review, and run a deterministic workflow that calls two workspace-enabled MCP servers in under five minutes without entering child connection settings in Rivet.
- **SC-002**: In the normal deterministic suite, 100% of reviewed calls reach the intended namespaced child tool and 100% of disabled, cross-workspace, unreviewed, unbound, stale, expired, replayed, and post-cancellation attempts are blocked before child invocation.
- **SC-003**: A tool or schema change is visible and invalidates the affected review within one discovery refresh or attempted run, with the exact changed identity identified.
- **SC-004**: Cancellation revokes the run authority and prevents all later node calls within two seconds in deterministic tests; the record never claims an unacknowledged external operation stopped.
- **SC-005**: Every completed, denied, failed, or cancelled test run has a bounded manifest that accounts for 100% of MCP nodes, bindings, approvals, child calls, artifacts, and terminal reasons without containing secret values.
- **SC-006**: The deterministic BREP-style and host-bridge-style lifecycle tests produce the same gateway-facing progress, result, cancellation, and failure contracts as ordinary child MCPs.
- **SC-007**: Existing non-MCP workflow, agent-manager, workspace, and gateway regression suites retain their prior pass rate.
- **SC-008**: Normal validation completes without proprietary applications, paid accounts, credentials, external services, GPUs, hardware, or physical actuation.
- **SC-009**: At least 90% of five representative engineers can identify the bound tool, approval state, active node, and failure boundary from the review/run UI without assistance; this human study may remain explicitly deferred while automated accessibility and journey evidence is completed.

## Assumptions

- Loop 068 has already supplied validated per-workspace capability enablement and honest current tool evidence.
- Wright's provider-neutral gateway remains the single authority for workspace tool discovery, invocation policy, child lifecycle, and audit.
- The safest reversible Gate B default is a Wright-issued opaque, short-lived run capability whose usable value is held only by the local runner process and whose durable record stores only identifiers and digests.
- Capability requirements resolve during review; execution never silently substitutes a different provider or changed schema.
- Existing per-call approval policy remains authoritative. Workflow review confirms bindings and intent but is not itself blanket approval for destructive calls.
- Deterministic fake MCPs are the normal acceptance path. BREP and Solid Edge or another application are optional live paths enabled only when their prerequisites are already available and explicitly authorized.
- Cancellation is best-effort at an external child boundary; Wright can guarantee authority revocation and suppression of later effects, but it reports rather than fabricates physical or remote cleanup.
- Existing run retention and workspace deletion policies remain unchanged unless planning identifies a necessary additive record.
- Gate E remains closed; this feature cannot start or actuate machinery.
