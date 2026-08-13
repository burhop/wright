# Rivet MCP gateway

Rivet workflows can use the MCP capabilities enabled in their Wright workspace. Rivet does not start, connect to, or configure child MCP servers itself. Wright gives one reviewed run a short-lived private provider, resolves each node to an exact reviewed binding, and sends the call through the same Gateway used by chat and agent clients.

## Execution path

1. Wright discovers namespaced tools already visible in the workspace, such as `cad__inspect` and `fea__solve`.
2. The engineer selects one exact tool for every MCP node and reviews the workflow, graph, server revision, schemas, validation evidence, policy effects, units, and material assumptions.
3. On Start, Wright verifies that review again, starts an ephemeral `127.0.0.1` bridge, and mints a memory-only authority for that run and generation.
4. The pinned Node runner receives opaque node handles, binding digests, the exact bridge address, and the one-run token. It receives no child command, endpoint, environment, header, credential, or application lifecycle configuration.
5. A Rivet MCP node calls the private provider. Wright resolves the reviewed binding, applies exact-call approval when required, and delegates to `GatewayService`.
6. Wright records bounded progress, approvals, child receipts, artifacts, cancellation truth, and the immutable terminal Run Manifest.

This is how Rivet drives BREP, Solid Edge-style host bridges, and ordinary stdio/HTTP MCPs without owning those applications. The child still receives the governed call; Wright remains responsible for starting it, presenting its panel when applicable, cancelling it, and reporting cleanup truthfully.

## Enable the feature

The gateway is off by default. A local operator enables the existing Rivet surfaces and real pinned runner together with the governed MCP path:

```text
WRIGHT_RIVET_WORKFLOWS_ENABLED=1
WRIGHT_RIVET_EDITOR_ENABLED=1
WRIGHT_RIVET_RUNNER_ENABLED=1
WRIGHT_RIVET_REAL_EXECUTION_ENABLED=1
WRIGHT_RIVET_WORKFLOW_OPERATIONS_ENABLED=1
WRIGHT_RIVET_MCP_GATEWAY_ENABLED=1
VITE_RIVET_WORKFLOWS_TAB_ENABLED=true
```

Restart Wright after changing these values. Do not set the four `WRIGHT_RIVET_MCP_WORKSPACE*` launch variables manually in normal operation; Wright supplies those trusted values only when it launches the workspace-confined Rivet operations server.

The defaults are a 300-second exact-call approval lifetime, 1 MiB request limit, 64 KiB event limit, and 2,000 events per child call. The corresponding advanced settings are `WRIGHT_RIVET_MCP_APPROVAL_TTL_SECONDS`, `WRIGHT_RIVET_MCP_REQUEST_BYTES`, `WRIGHT_RIVET_MCP_EVENT_BYTES`, and `WRIGHT_RIVET_MCP_EVENTS_PER_CALL`. Keep the event limit at or below the request limit.

## Operator workflow

In the workspace Workflows pane:

1. Open **Capabilities & Review**.
2. Resolve every MCP node to one namespaced, compatible workspace tool.
3. Inspect revisions, schemas, validation evidence, risk gates, units, and assumptions; then approve the exact revision and graph.
4. Start the workflow. A destructive or otherwise gated child call pauses at **Approve this exact MCP call?** The decision is single-use and bound to the displayed argument digest.
5. Use **Cancel run** when needed. Wright revokes the authority before cancelling active Gateway requests and stopping its runner.
6. Open **Run evidence** to inspect the timeline, accounting, authorized artifacts, reproducibility differences, and recovery guidance. Exported evidence is bounded to 2 MiB and marked `no-store`.

A workflow edit, schema or server-revision change, validation change, policy change, or workspace grant change makes the review stale. Wright requires a new review; it never silently rebinds.

## Security boundary

- The bridge binds an ephemeral loopback port and is not a public FastAPI route. It accepts only POST requests to its exact discovery and call paths, exact Host, no browser Origin, JSON bodies, bounded headers/body/events, and its audience-bound bearer authority.
- Authority tokens are 256-bit values held only in memory. SQLite, workflow files, API responses, logs, traces, events, evidence, and UI text store only non-reusable identities or digests.
- Binding documents reject secret-like keys and credential-bearing URLs. Results and progress are re-redacted. Only verified `wright://artifact/<workspace>/...` references cross the artifact boundary; raw child paths and arbitrary URIs are rejected.
- MCP prompts, dynamic tool names, embedded child configuration, direct stdio/HTTP transports, and calls after expiry, revocation, cancellation, terminalization, or restart fail closed.
- Chat and agent-manager clients keep their own Gateway sessions. Rivet authority does not expand their access, and their sessions cannot reuse a Rivet token.

## Cancellation and recovery

`RIVET_MCP_CANCELLED_CLEAN` means Gateway cancellation cleared and cleanup was acknowledged. `RIVET_MCP_RESIDUE_POSSIBLE` means Wright could not prove rollback; inspect the child application before retrying. A late result after authority revocation cannot change the run to success or publish an artifact.

Specialized application failures retain stable boundaries:

- `RIVET_MCP_PANEL_UNAVAILABLE`: reopen the BREP panel and inspect its status.
- `RIVET_MCP_HOST_BRIDGE_UNAVAILABLE`: inspect the host application and its separately managed bridge.

Other stale/restart reports identify the changed workflow, review, binding set, policy snapshot, runner artifact, or validation evidence and name the required review or verification action.

## Troubleshooting

| Symptom | Check | Safe recovery |
| --- | --- | --- |
| Start is disabled | Workflow review, exact bindings, workspace grants, validation and runner status | Refresh capabilities and review the current graph |
| Authority unavailable, expired, or revoked | Whether the run was cancelled, completed, restarted, or exceeded its lifetime | Start a new reviewed run; never reuse an old token |
| Binding mismatch or stale binding | Node handle, schema/server revision, validation evidence, policy and enabled tools | Re-open Capabilities & Review and approve the new identity |
| Exact call awaits approval | Displayed node, tool, argument summary/digest and gates | Approve once or deny; changed arguments require another decision |
| Panel or host bridge unavailable | Visible application status and its Wright-owned diagnostics | Follow the stable recovery code; do not add child configuration to Rivet |
| Residue possible after cancellation | Child application/process state and authorized artifacts | Inspect and clean the application before a new reviewed run |

## Rollback

Set `WRIGHT_RIVET_MCP_GATEWAY_ENABLED=0` and restart Wright to stop new MCP authority issuance. If necessary, also disable real execution with `WRIGHT_RIVET_REAL_EXECUTION_ENABLED=0`. Existing non-MCP workflows remain available according to their own feature settings. Historical reviews, manifests, and evidence remain readable, but restart invalidates every old in-memory authority. Do not delete the database as a rollback step.

## Optional live validation

Normal acceptance uses local deterministic children. Live BREP or host-application probes are separately authorized and skipped by default; see [Rivet workflow testing](testing.md). Never install proprietary software, accept a license, add paid credentials, contact a paid service, or perform machine/physical actions merely to make a probe pass.
