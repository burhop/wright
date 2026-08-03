# Contract: Governed Rivet Workflow Execution

**Owner slices**: `rivet-headless-runner` for lifecycle; `rivet-wright-nodes` for engineering operations; `rivet-workflow-operations` for human launch; optional `rivet-agent-publication` for agent launch

## Execution Authority

A run is created only by Wright after authenticating the caller and resolving an authorized workflow, exact immutable revision, graph, inputs, review state, plugin manifest, and effective policy. The Node runner receives an execution grant scoped to one run and runtime generation. It is not a general Wright API client.

## Start Request

The public Wright request identifies:

- workflow ID and exact or server-resolved reviewed revision;
- graph ID/name under that revision;
- typed inputs;
- optional human-readable run label;
- expected review/publication identity where the launch surface requires it.

Workspace, principal, session, policy, runner endpoint, filesystem location, secrets, and tool authority are injected server-side. Agent and interactive callers ultimately enter this same contract.

## Start Response

Returns a run ID, accepted revision/digest, initial status, trace ID, effective high-level policy summary, event/status URL or stream identity, and cancel capability appropriate to the caller. It never returns runner-local paths, PID/port, secret values, approval grants, or an unrestricted debugger endpoint.

## Event Envelope

The owning slice publishes a versioned schema containing:

- run ID, runtime generation, monotonic sequence, timestamp, trace ID;
- optional graph/node IDs;
- event kind and bounded status/progress summary;
- inline redacted scalar/summary or an access-controlled artifact reference;
- optional tool request, approval, diagnostic, or terminal reason identity.

Events are idempotent by `(run_id, runtime_generation, sequence)`. Clients resume from a last acknowledged sequence. Backpressure coalesces partial progress but never drops terminal, approval, artifact, policy, or failure events.

## Lifecycle

Supported states and transitions follow [data-model.md](../data-model.md). In addition:

- Start has a bounded readiness timeout.
- Cancellation is idempotent and propagates to the graph abort signal, pending external call, tool invocation where supported, approval wait, and owned process cleanup.
- A denied/revoked/expired approval returns a typed node failure or cancellation according to the graph contract; it never silently proceeds.
- Wright restart reconciles non-terminal records with live owned generations. Stale generations cannot report success after reconciliation.
- Terminalization records cleanup outcome separately so a succeeded graph with leaked owned resources cannot be reported as a clean success.

## Wright External-Call Bridge

The runner may request only operations registered for its compatible build and effective policy. A request contains a logical operation, node identity, typed arguments, and run-scoped correlation identity. Wright reconstructs the complete authorization context from server records.

For engineering tools, the bridge:

1. Resolves the run, generation, workflow revision, user, workspace, session, and policy.
2. Resolves/discovers the current approved tool through `GatewayService`.
3. Revalidates health, RBAC, workspace scope, arguments, constraints, and approval requirement.
4. Pauses the workflow for Wright approval when required.
5. Executes through the provider-neutral gateway.
6. Bounds/redacts the result, persists audit/provenance, and returns a Rivet `DataValue` or typed error.

Direct tool server credentials and reusable Wright tokens are never exposed to Rivet.

## Artifact and Display Publication

- Inline runner outputs are size-limited and sanitized.
- Binary, large, rendered, or durable outputs are ingested through Wright artifact/surface services.
- Publication records workflow revision, run, node, inputs/constraints, tool/approval identities, digest, MIME, and trace.
- A Rivet node cannot choose broader artifact visibility than the caller/workspace policy.

## Resource and Policy Limits

At minimum the effective contract bounds concurrent runs, wall/CPU time where measurable, memory/process tree, event rate/size/count, logs, dataset/project/attachment reads, artifact size/count, remote-debugger clients, user-input/approval wait, retries, HTTP/network, code, filesystem, plugins, direct MCP, and project references. Defaults are safe and versioned; omission never means unlimited.

## Error Categories

- `invalid_request`
- `not_found` without cross-workspace disclosure
- `revision_conflict` or `review_stale`
- `policy_denied`
- `approval_denied`, `approval_expired`, `approval_revoked`
- `runtime_unavailable`, `runtime_incompatible`, `runtime_crashed`
- `resource_limit`
- `cancelled`
- `tool_unavailable`, `tool_failed`
- `artifact_failed`
- `unsupported_format` or `unsupported_plugin`
- `internal_error` with correlation ID and no secret detail

## Required Contract Tests

- Immutable revision despite concurrent editor save.
- Interactive and optional agent launch parity.
- Event ordering, reconnect, coalescing, oversize, replay, and stale generation.
- Cancellation during startup, normal node, tool call, approval wait, artifact write, and debugger connection.
- Runner crash, Wright restart, workspace deletion/disconnect, and timeout cleanup.
- Read-only and mutating gateway calls, current tool-health change, approval deny/revoke/expire/replay/cross-scope.
- Code/HTTP/file/project-reference/plugin/direct-MCP bypass attempts.
- Artifact partial failure and provenance completeness.
- Optional Node absent/disabled plus native/Docker installed-package execution.
