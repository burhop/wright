# Research: Rivet Workspace MCP Gateway Execution

## Scope and method

This research resolves the Gate B decisions required before Rivet MCP nodes can execute. It combines the exact pinned Rivet 2 source used by Wright, Wright's current runner/gateway/lifecycle implementation, and the Model Context Protocol specification. It does not treat community examples, package metadata, or MCP annotations as security authority.

## Decision 1: Native Rivet MCP nodes with an injected Wright provider

**Decision**: Keep native `mcpDiscovery` and `mcpToolCall` graph semantics, but inject a Wright-owned implementation of Rivet's `MCPProvider` into `createProcessor`. Reviewed Wright runs must never instantiate Rivet's `NodeMCPProvider`.

**Evidence**:

- The pinned `MCPProvider` interface separates discovery/call behavior from graph nodes, and `createProcessor` accepts the provider as a host option.
- The pinned Node provider implements direct Streamable HTTP/SSE connections and direct stdio process spawning from project metadata. That behavior is useful for standalone Rivet, but violates Wright's workspace, credential, lifecycle, and audit boundary.
- Native MCP nodes already supply the expected Rivet authoring and data-flow behavior. Reusing them avoids a Wright-only node fork and keeps imported graphs legible.

**Alternatives rejected**:

- **Use `NodeMCPProvider` with a gateway URL**: project metadata would still own connection material, and stdio/direct URL paths would remain representable.
- **Create new Wright-only Rivet nodes**: duplicates upstream node behavior, complicates the editor, and creates a migration burden without improving the host-injection seam.
- **Launch MCP children from the Node runner**: creates a second lifecycle/credential/policy authority and is prohibited.

**Primary sources**:

- [Pinned Rivet MCPProvider](https://github.com/valerypopoff/rivet2.0/blob/4f4a165a03f8da89c3d1cce2cb1a8c6eb6aa2053/packages/core/src/integrations/mcp/MCPProvider.ts)
- [Pinned Rivet createProcessor host options](https://github.com/valerypopoff/rivet2.0/blob/4f4a165a03f8da89c3d1cce2cb1a8c6eb6aa2053/packages/core/src/api/createProcessor.ts)
- [Pinned Rivet NodeMCPProvider](https://github.com/valerypopoff/rivet2.0/blob/4f4a165a03f8da89c3d1cce2cb1a8c6eb6aa2053/packages/node/src/native/NodeMCPProvider.ts)

## Decision 2: External exact bindings and an in-memory graph transform

**Decision**: Treat every stored Rivet MCP server definition as untrusted authoring input. Wright extracts MCP nodes from the exact selected graph and persists bindings outside the `.rivet-project`. After verifying the project digest, the runner rewrites only eligible MCP node data in memory to reserved Wright handles and exact namespaced tool names. Dynamic tool-name inputs and direct HTTP/stdio configuration are invalid for a reviewed run.

**Rationale**:

- Upstream `resolveMCPServer` normally reads URL or command configuration from project metadata. Wright cannot let a workflow choose its own child endpoint, command, environment, headers, or credential carrier.
- `MCPToolCallNode` can accept a dynamic tool name. A reviewed binding cannot remain exact if a data input changes the called tool at runtime.
- Binding outside authored bytes lets Wright invalidate review when workspace enablement, server revision, schema, validation evidence, or policy changes without rewriting the engineer's project.

**Alternatives rejected**:

- **Persist gateway URLs/tokens in the project**: leaks reusable authority and makes review bytes environment-specific.
- **Trust project `serverId` as the child identity**: a malicious or stale graph could redirect a reviewed node.
- **Resolve aliases at call time**: silent rebinding defeats reproducibility and review.

**Primary sources**:

- [Pinned Rivet MCP server resolution](https://github.com/valerypopoff/rivet2.0/blob/4f4a165a03f8da89c3d1cce2cb1a8c6eb6aa2053/packages/core/src/integrations/mcp/MCPUtils.ts)
- [Pinned Rivet MCP tool-call node](https://github.com/valerypopoff/rivet2.0/blob/4f4a165a03f8da89c3d1cce2cb1a8c6eb6aa2053/packages/core/src/model/nodes/MCPToolCallNode.ts)

## Decision 3: Exact-origin loopback bridge and opaque run authority

**Decision**: Add an application-scoped loopback HTTP bridge over the existing async Python gateway. Mint a cryptographically random opaque token for one run and pass it only to the supervised Node worker over its initial stdin request. Store the token digest and claims in memory; persist only a non-usable authority identity/digest and timestamps.

**Rationale**:

- The current runner input is one JSON document and stdin then closes; stdout is already a bounded JSONL event stream. An HTTP bridge reuses the proven AI-bridge/network-guard pattern and avoids redesigning the cross-platform process supervisor for duplex RPC.
- MCP authorization guidance requires audience binding, least privilege, and short-lived tokens, and forbids token passthrough. A Wright token is accepted only by the internal Rivet bridge and is never forwarded to a child MCP.
- MCP session identifiers are not authentication. Run/session IDs remain correlation fields, not proof of authority.

**Authority claims**:

- authority ID and token digest
- run ID and runner generation
- workspace and gateway session
- workflow ID, revision, digest, and selected graph
- review and binding-set digest
- exact node-handle map
- issued, expiry, revoked, and terminal timestamps

**Alternatives rejected**:

- **Long-lived gateway credential**: too broad, replayable, and difficult to revoke.
- **Token per child server**: exposes child topology and multiplies secret handling in the runner.
- **Run/session ID as bearer proof**: predictable identifiers are not authorization.
- **New duplex supervisor protocol**: materially expands platform/process risk for no better confinement.

**Primary sources**:

- [MCP authorization specification](https://modelcontextprotocol.io/specification/2025-06-18/basic/authorization)
- [MCP authorization security best practices](https://modelcontextprotocol.io/docs/tutorials/security/security_best_practices)

## Decision 4: Canonical CapabilityBinding and review invalidation

**Decision**: A binding is immutable and covers all values that can change the security or engineering meaning of a call. A review authorizes the exact binding-set digest, not an alias or current best match.

**Digest material**:

- workspace, workflow, revision/digest, selected graph, and node
- requirement identity and exact namespace-qualified tool
- child server identity/revision, catalog capability digest, local validation evidence, and workspace grant identity
- canonical input/output schemas and annotations/risk/approval policy snapshot
- units/material policy, material defaults, static tool name, and allowed argument constraints

Tool list changes trigger refresh, but they do not silently update an approved binding. A changed field produces a reason-coded stale comparison and requires review again.

**Alternatives rejected**:

- **Bind only server/tool names**: names do not prove schema, implementation revision, validation, or workspace grant.
- **Cache discovery without version identity**: cannot distinguish a usable snapshot from stale authoring data.
- **Auto-upgrade compatible schemas**: compatibility inference can be wrong for units, semantics, or destructive behavior.

**Primary sources**:

- [MCP tools specification](https://modelcontextprotocol.io/specification/2025-06-18/server/tools)
- [MCP schema, including list-changed notifications](https://modelcontextprotocol.io/specification/2025-06-18/schema)

## Decision 5: Wright-owned exact-call approval

**Decision**: Workflow review and tool approval remain separate. Review approves the exact graph/binding set. At invocation, `GatewayPolicy` remains authoritative and `client_approval_hint` is always false. If a tool requires approval, Wright records a pending approval bound to run, node, tool, argument digest, approval gates, actor, and expiry. Only an authenticated Wright action can satisfy it.

**Rationale**:

- Current `GatewayPolicy` treats annotations and client approval hints as descriptive only and compares required gates with server-side workspace approvals.
- A broad workflow approval could unintentionally authorize a different argument set, repeat, duration, or non-idempotent action.
- Exact-call records allow a run to wait and continue without giving the runner approval authority.

**Alternatives rejected**:

- **Treat workflow review as all tool approvals**: broadens destructive authority.
- **Let the runner set `client_approval_hint`**: the client cannot prove user intent.
- **Grant all enabled-server approval gates automatically for Rivet**: server enablement is availability, not invocation approval.

## Decision 6: Bounded progress, explicit cancellation, truthful residue

**Decision**: The bridge streams bounded normalized progress to the injected provider, which emits runner progress correlated to the Rivet node. Cancellation ordering is authority revoke, gateway request cancellation, then runner-tree termination. Late results are ignored after a terminal boundary. If a child cannot confirm cancellation, the Run Manifest records residue rather than claiming it stopped.

**Rationale**:

- MCP supports progress and cancellation notifications, but transport disconnect is not itself cancellation.
- Engineering operations can outlive a UI/network connection. Wright must explicitly cancel the active request and retain recovery information.
- Non-idempotent calls are never silently retried after timeout or disconnect.

**Alternatives rejected**:

- **Kill only the Node runner**: may leave a child application operation running.
- **Disconnect the bridge**: MCP explicitly does not equate disconnect with cancellation.
- **Accept late success**: can publish artifacts after the user cancelled.

**Primary sources**:

- [MCP lifecycle and timeouts](https://modelcontextprotocol.io/specification/2025-06-18/basic/lifecycle)
- [MCP transports and disconnect semantics](https://modelcontextprotocol.io/specification/2025-06-18/basic/transports)
- [MCP schema for progress and cancellation](https://modelcontextprotocol.io/specification/2025-06-18/schema)

## Decision 7: Bounded Run Manifest, child-call evidence, and artifacts

**Decision**: Extend the durable workflow run with one immutable Run Manifest plus append-only child-call/approval/progress/result evidence. Persist canonical identities, digests, stable reason codes, timings, byte counts, and vault artifact references. Redact or omit tokens, authorization headers, credential-like fields, raw environments, unrestricted paths, and oversized child content.

The authority token is unrecoverable after process restart. A restarted application can inspect evidence but cannot resume the old authority. Reproduction means preparing a new reviewed run and comparing pinned identities.

**Alternatives rejected**:

- **Store only the final output**: cannot explain which node/tool/approval produced it.
- **Store raw child messages**: creates secret, size, and proprietary-data risk.
- **Persist the bearer token for resume**: extends authority beyond the reviewed process lifetime.

## Decision 8: Specialized lifecycle stays behind the gateway

**Decision**: BREP panel and Solid Edge/host-bridge behavior remain Wright lifecycle adapters selected by the bound server. The Rivet provider sees the same list/call/progress/error contract as any other server. Deterministic lifecycle doubles are mandatory; live application probes are opt-in and evidence-labeled.

**Rationale**:

- Wright already wraps the BREP panel lifecycle and delegates ordinary servers through the gateway lifecycle.
- Solid Edge is proprietary and Windows-hosted; it cannot be a routine test prerequisite or redistributed by this loop.
- Hiding lifecycle specialization from the graph preserves portable authoring and prevents embedded host configuration.

## Decision 9: Protocol versioning and rollback

**Decision**: Introduce runner protocol v2 with an optional `mcp` tool grant. Protocol v1 remains valid for non-MCP workflows during the transition. An MCP tool graph without a current v2 grant fails closed, and MCP prompt nodes remain denied because this loop has no reviewed prompt contract. A feature switch can stop discovery, binding issuance, and run authority minting while leaving existing non-MCP workflows and durable history readable.

The runner artifact is rebuilt deterministically and its source/build/output digests are updated in the checked-in manifest. Rollback never re-enables direct MCP execution.

## Decision 10: Deterministic validation before live applications

**Decision**: The ordinary test suite launches two local fake MCPs with colliding tool names, schemas, progress, approval requirements, cancellable slow calls, structured outputs, and artifacts. Separate panel and host-bridge doubles prove specialized lifecycle parity. Optional live tests require explicit environment flags, installed/validated workspace capabilities, and user-provided credentials/applications.

**Rationale**: This proves the security and orchestration boundary on every supported build host without making paid accounts, proprietary software, external availability, GPUs, or hardware part of the merge gate.
