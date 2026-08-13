# Gate B Decision: Rivet Gateway Boundary

**Status**: Approved under the Engineering Capability Program's recorded advance authority

**Date**: 2026-08-13

## Decision

1. Rivet graphs keep native `mcpDiscovery` and `mcpToolCall` nodes. Wright injects the runtime `MCPProvider`; reviewed runs never use Rivet's direct Node HTTP/stdio provider.
2. The project file is not an MCP authority. Direct endpoint, command, environment, header, credential, and dynamic tool-name configuration is rejected. Wright verifies the workflow digest and rewrites eligible nodes in memory to reserved node handles and exact bound namespaced tools.
3. Capability bindings live outside the graph and pin workspace, workflow revision/digest, selected graph, node, server revision, validation evidence, schemas, grant/policy facts, engineering assumptions, and material defaults. Any material change invalidates review.
4. One opaque 256-bit token grants one run access to one exact loopback Wright bridge origin, workspace/session, review, binding set, node-handle map, and short expiry. Raw tokens are memory-only, audience-bound, never forwarded, and revoked on cancel/terminal/restart.
5. Every operation revalidates authority, run generation, review, binding, workspace grant, server/tool/schema/validation identity, and current gateway policy before a child receives a call. The runner submits only the bound handle/digest, request identity, and arguments; Wright resolves the server/tool.
6. Workflow review does not satisfy tool approval gates. Wright owns exact-call approval records; the runner cannot grant approval and its client hint remains false.
7. Progress is bounded and correlated. Cancellation revokes authority, explicitly cancels active gateway requests, then terminates the runner. Late results cannot change terminal state; unconfirmed external residue is reported.
8. Run evidence is a bounded/redacted draft finalized exactly once as an immutable terminal manifest, plus append-only child-call records and Wright-authorized vault/resource artifact references. It contains authority digests, not usable authority.
9. Specialized BREP panel and Solid Edge/host-bridge lifecycles remain behind Wright's gateway/lifecycle contract. Deterministic doubles are required; live probes are opt-in.

## Boundary

```text
reviewed native Rivet MCP node
  -> injected Wright MCPProvider
  -> exact-origin loopback bridge + run token
  -> in-memory authority and bound node lookup
  -> current review/grant/schema/policy revalidation
  -> existing GatewayService
  -> Wright-owned child lifecycle
  -> MCP child / engineering application
```

Rivet owns graph evaluation only. Wright owns authorization, workspace scope, exact binding, credentials, MCP connections, child processes, specialized application lifecycle, approval, audit, cancellation, and durable evidence.

## Primary evidence

- The pinned Rivet `createProcessor` accepts an injected provider.
- The pinned upstream Node provider otherwise connects directly to HTTP/SSE or spawns stdio from project configuration.
- The current Wright gateway already provides namespaced discovery, policy, lifecycle, progress, cancellation, normalized results, and audit.
- MCP authorization guidance requires audience-bound least privilege and forbids token passthrough; MCP transport disconnect is not cancellation.

See [research.md](../research.md) for links and alternatives.

## Risks and controls

| Risk | Control |
|------|---------|
| Token theft from logs/process metadata | Token enters only one-shot stdin/body headers, is registered as a secret value for process redaction, never persisted, and expires with the run. |
| Graph calls arbitrary child | No direct provider; static exact node handle maps to server/tool in authority memory. |
| Stale review after schema/server/grant change | Per-call current-state comparison against canonical binding digest; fail before lifecycle start. |
| Workflow review broadens destructive authority | Exact-call approvals remain separate and argument-bound. |
| Runner kill leaves child active | Explicit gateway cancellation precedes process termination; residue is durable and visible. |
| Loopback route used by unrelated local process | High-entropy audience-bound token, exact origin/path, short TTL, constant-time check, request/body limits, run/node claims, no CORS, no token in URL. |
| MCP annotations misrepresent safety | Annotations remain displayed hints; Wright policy and reviewed evidence are authoritative. |
| Protocol/provider upgrade changes semantics | Runner source/package/build/output digests are pinned and verified; protocol v2 contract tests fail closed. |

## Rollback

- Disable MCP discovery/binding/authority issuance through the feature setting.
- Keep protocol v1/non-MCP execution available and all durable history readable.
- Restarting Wright revokes every outstanding token automatically.
- Do not fall back to direct Rivet MCP configuration.
- Migration 14 is additive; older readers ignore new tables/nullable columns, while new code treats legacy reviews as non-MCP-only.

## Exit evidence required

- One real Rivet graph calls two deterministic fake MCP children through `GatewayService`.
- Negative cases prove disabled, cross-workspace, unreviewed, unbound, stale, expired/replayed, and post-cancel calls never reach a child.
- Exact-call approval, progress, explicit cancellation, late-result rejection, audit, artifacts, and Run Manifest evidence pass.
- BREP-panel and host-bridge doubles prove specialized lifecycle parity.
- Optional live BREP and Solid Edge/available-app outcomes are labeled separately and never gate routine builds.
