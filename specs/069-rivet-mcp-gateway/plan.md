# Implementation Plan: Rivet Workspace MCP Gateway Execution

**Branch**: `069-rivet-mcp-gateway` | **Date**: 2026-08-13 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/069-rivet-mcp-gateway/spec.md`

## Summary

Let reviewed Rivet 2 graphs use their native MCP discovery and tool-call nodes while Wright remains the only MCP authority. The pinned Rivet runtime will receive an injected Wright-owned `MCPProvider`; it will never use Rivet's direct HTTP/stdio provider. Wright will resolve each MCP node to an exact workspace-enabled namespaced tool, bind the workflow digest, selected graph, node, server revision, schema digest, validation evidence, and policy facts into a durable review, and mint an opaque in-memory authority for one run. The provider can contact only an exact loopback Wright bridge origin and can submit only a bound node handle plus arguments. The Python bridge revalidates every claim and delegates to the existing `GatewayService`, preserving policy, approval, specialized lifecycle, progress, cancellation, result normalization, and audit behavior.

Normal validation uses two deterministic fake child MCPs plus BREP-panel and host-bridge lifecycle doubles. Live BREP and Solid Edge or another available application are opt-in evidence only. No workflow stores child commands, URLs, environments, credentials, or reusable gateway authority.

## Technical Context

**Language/Version**: Python 3.11-3.14 for domain/API/runtime orchestration; TypeScript 5 on Node.js 20+ for the pinned Rivet runner; React 19 for the web application

**Primary Dependencies**: Existing FastAPI composition and workspace services, SQLite data-vault repositories, `tool_registry.GatewayService`, Wright MCP lifecycle/process supervisor, pinned `@valerypopoff/rivet2-node` 2.1.9 from Rivet 2.8.9 source revision `4f4a165a03f8da89c3d1cce2cb1a8c6eb6aa2053`, Pydantic 2, JSON Schema, React/Vitest/Playwright

**Storage**: Existing embedded SQLite WAL database extended additively for exact capability bindings, review-bound binding sets, run manifests, child-call evidence, and redacted artifact references; opaque authority tokens and active-call handles remain memory-only

**Testing**: pytest unit/contract/integration/system tests; Node runner protocol tests; two deterministic fake MCP servers; deterministic BREP-panel and host-bridge lifecycle doubles; Vitest component/service tests; mocked Playwright journeys; opt-in live BREP/Solid Edge or available-app probes; `scripts/check-dev-merge.sh`

**Target Platform**: Wright native Windows x64, Linux x64, Linux ARM64/GB10, and macOS where the current runtime is supported; Docker Linux x64/ARM64; browser UI. Solid Edge live validation remains Windows-only and externally provisioned.

**Project Type**: Modular monorepo local desktop/web application with Python domain services, thin FastAPI routes, a supervised Node worker, provider-neutral MCP gateway, React frontend, and native/Docker distributions

**Performance Goals**: Review-time discovery of 500 workspace tools in under 500 ms from cached gateway metadata; authority issuance under 100 ms; bridge overhead under 100 ms p95 excluding child execution on a reference local machine; progress visible within 250 ms of receipt; cancellation begins within 250 ms and reaches the active gateway request within one second

**Constraints**: Offline-first for local children; no workflow-owned child configuration or credentials; one run/workspace/review/binding-set per authority; raw tokens never persisted or logged; no dynamic tool names for reviewed calls; no paid service, proprietary application, credential, GPU, hardware, or network dependency in normal gates; no physical actuation; no silent retry of non-idempotent calls; bounded/redacted events and outputs

**Scale/Scope**: Up to 500 discoverable tools, 100 MCP nodes per reviewed graph, two concurrent Rivet runs by current default, 300-second default run limit, 64 KiB event limit, 1 MiB terminal-output limit, and at least two child MCPs per deterministic end-to-end workflow

## Constitution Check

*GATE: Passed before Phase 0 research and re-checked after Phase 1 design.*

| Principle | Pre-design and post-design evaluation |
|-----------|----------------------------------------|
| Modular monorepo / thin routes | PASS: binding, authority, review, bridge, and manifest logic stays in `workspace_service` and `tool_registry`; API routes validate and delegate. |
| Offline-first | PASS: local MCP discovery and execution need no cloud service; deterministic tests use local fake children. Remote children remain optional capabilities with explicit policy. |
| Native and Docker distribution | PASS: the already packaged Rivet worker is extended and rebuilt with manifest integrity; Python changes enter the shared wheel/runtime. No source checkout is required after installation. |
| Thick base / thin code | PASS: fake servers and clean-container validation do not add vendor MCP software to the base image. |
| Manager neutrality | PASS: Rivet uses the same provider-neutral Wright gateway as agent managers and chat; it receives no privileged child path. |
| Embedded state | PASS: durable review and run evidence use the existing SQLite WAL lifecycle; authority and active-call state are deliberately memory-only. |
| Local authentication / RBAC | PASS: review, start, approval, cancellation, and inspection remain behind existing authenticated workspace/API boundaries. The runner token is an internal run capability, not user identity. |
| Engineering tool isolation | PASS: Wright's lifecycle owns child processes and host preparation. Rivet cannot submit commands, endpoints, environments, credentials, or filesystem paths. |
| UI atomic design / 3-tier tests | PASS: binding/review/status components use tokens and stable test IDs, with component, mocked journey, and local system coverage. |
| Observability and traceability | PASS: review, authority, node, gateway request, child call, progress, approval, artifact, cancellation, and terminal events share bounded correlation identities. |
| Phase isolation and manual gates | PASS WITH RECORDED ADVANCE APPROVAL: the attached long-running program goal explicitly authorizes safest reversible Gate B decisions, analysis remediation, implementation, gating, and integration while the user is away. Gate B is recorded in `contracts/gate-b-decision.md`. |
| Branch discipline | PASS: work is isolated on `069-rivet-mcp-gateway`; no work or merge targets `main`. |

No constitution violation requires a complexity exception.

## Project Structure

### Documentation (this feature)

```text
specs/069-rivet-mcp-gateway/
|-- spec.md
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   |-- capability-binding.schema.json
|   |-- gate-b-decision.md
|   |-- rivet-gateway-api.md
|   |-- run-manifest.schema.json
|   |-- runner-protocol-v2.md
|   `-- ui-journey.md
|-- checklists/
|   |-- requirements.md
|   `-- rivet-mcp-gateway.md
`-- tasks.md
```

### Source Code (repository root)

```text
packages/core/src/core/
|-- workflow_runs.py              # neutral binding/manifest/run values and reason codes
`-- workflows.py                  # workflow identity and graph selection

packages/data_vault/src/data_vault/
|-- migrations.py                 # additive migration 14
|-- workflow_review_repository.py # exact review and binding-set persistence
|-- workflow_runs.py              # manifest and child-call evidence persistence
`-- workflow_binding_repository.py

packages/workspace_service/src/workspace_service/
|-- rivet_capabilities.py         # discovery, exact binding, schema/revision digests
|-- rivet_authority.py            # in-memory mint/validate/revoke service
|-- rivet_gateway_bridge.py       # bound call, progress, result, and cancellation bridge
|-- rivet_runtime_host.py         # protocol-v2 request and exact loopback bridge grant
|-- rivet_validation.py           # native MCP-node restrictions and binding extraction
|-- workflow_operations.py        # review/start invalidation and UI projections
`-- workflow_runner.py            # authority/manifest lifecycle and cancellation ordering

integrations/rivet/runner/
|-- src/wright-runner.ts          # injected MCPProvider, binding handles, guarded bridge fetch
|-- tests/                         # protocol/provider/direct-child denial coverage
|-- manifest.json                 # rebuilt integrity metadata
`-- dist/wright-runner.mjs

apps/api/src/api/
|-- composition.py                # one authority/bridge service per application
|-- routers/workspace.py          # thin discovery/review/run/approval/cancel endpoints
`-- schemas/workspace.py          # typed request/response contracts

apps/web/src/
|-- components/workflows/WorkflowCapabilityBindings.tsx
|-- components/workflows/WorkflowReviewPanel.tsx
|-- components/workflows/WorkflowRunTimeline.tsx
|-- components/workflows/WorkflowRecoveryPanel.tsx
|-- services/workspace-service.ts
`-- **/*.spec.tsx

packages/workspace_service/tests/
packages/tool_registry/tests/
apps/api/tests/
tests/e2e/test_rivet_mcp_gateway.py
tests/ui-integration/rivet-mcp-gateway.spec.ts
docs/rivet/
docs/engineering-capability-program-progress.md
```

**Structure Decision**: Extend the existing workflow review/runner repositories and the current provider-neutral gateway. The Node worker implements only the Rivet-side provider adapter; all authority, policy, lifecycle, and durable evidence remain Python-owned. This avoids a second MCP manager, a separate credential format, a long-lived internal service, and a Rivet fork.

## Phase 0 Research Decisions

The evidence, alternatives, and primary sources are in [research.md](research.md). The implementation consequences are:

1. Use Rivet's native `mcpDiscovery` and `mcpToolCall` nodes with an injected Wright `MCPProvider`; never instantiate upstream `NodeMCPProvider` for reviewed Wright runs.
2. Treat graph MCP server metadata as untrusted authoring data. After exact digest verification, rewrite eligible nodes in memory to reserved Wright handles and exact bound tool names; reject direct HTTP/stdio configuration and dynamic tool-name inputs.
3. Use an exact-origin loopback HTTP bridge with an opaque, high-entropy, run-bound token. The application stores only its digest and claims in memory; durable records store the authority identity/digest but no usable token.
4. Bind review to workflow digest/revision, selected graph, node identity, namespace-qualified tool, server revision, validation identity, schemas, policy/risk metadata, material defaults, and a canonical binding-set digest.
5. Keep approvals authoritative in Wright. Workflow review authorizes the binding set but never satisfies a destructive/tool approval. The bridge passes only server-side approval records for the exact pending call, and `client_approval_hint` stays false.
6. Stream bounded progress through the bridge, correlate it to run/node/call, explicitly cancel the active gateway request, revoke authority before runner termination, and ignore late terminal results.
7. Persist a bounded, redacted Run Manifest and append-only child-call evidence; store artifact IDs and digests, never unrestricted paths or secret-bearing output.
8. Keep BREP panel and Solid Edge/host-bridge preparation behind existing Wright lifecycle adapters. Deterministic doubles prove parity; live probes are opt-in.

## Phase 1 Design

### Review and binding

- Discovery is a Wright API operation over the current gateway session and workspace enablement projection. It does not require a runner token and does not start proprietary children merely to render a cached current schema.
- Validation extracts MCP nodes from the selected graph. Each executable tool-call node must have a static tool name and one exact `CapabilityBinding`. Discovery nodes receive the reserved `wright-workspace` handle and can list the current review snapshot only.
- A binding digest canonicalizes the workspace, workflow revision/digest, graph, node, namespace-qualified tool, child identity/revision, validation evidence, input/output schemas, risk/approval metadata, units/material policy, and material defaults.
- A review stores one binding-set digest. Any workflow, graph, node, schema, server revision, validation, workspace grant, or policy-relevant change produces a stale comparison and blocks start.

### Run authority and bridge

- `RivetRunAuthorityService` mints 256-bit opaque tokens with claims for one run, workspace, session, workflow digest/revision, graph, review, binding set, expiry, and allowed node handles.
- Raw tokens exist only in the API process and the supervised Node process. The request sends the bridge origin, token, authority ID, and non-secret binding handles over the existing one-shot stdin payload. Logs and SQLite receive only token/claim digests.
- The runner network guard permits only the exact Wright AI bridge origin and exact Wright MCP bridge origin. The injected provider adds the token itself; graph HTTP nodes and project data cannot read it.
- Each provider operation includes authority ID, run ID, binding handle, request ID, operation, and bounded arguments. Wright ignores graph-supplied workspace/server/tool identities and resolves the handle from authority claims.
- Before every list or call, Wright rechecks expiry/revocation, active run/generation, exact review/binding digest, workspace membership, server enablement, validation/schema/revision identity, and policy. A failed recheck stops before child invocation.

### Approval, progress, result, and cancellation

- A read-only call proceeds under current gateway policy. If a tool requires approval, the bridge records an exact pending call digest and returns/streams `approval_required`; an existing authenticated Wright approval endpoint can approve only that pending call and argument digest. A workflow review is never converted to a tool approval.
- Gateway progress is normalized to bounded phases and streamed as newline-delimited JSON from the loopback bridge. The Node provider emits correlated runner progress events without exposing raw child logs.
- MCP content and structured content are size-limited and returned to the correct node. Errors preserve stable Wright reason codes. Artifacts are represented by Wright vault IDs, media types, digests, and display labels.
- Cancellation first revokes authority, then cancels every active `(session_id, request_id)` through `GatewayService`, then asks the supervised Node tree to stop. The durable manifest records acknowledged/unconfirmed cleanup and ignores completion received after the terminal boundary.

### Storage and migration

- Additive migration 14 extends workflow reviews with workflow digest, selected graph, binding-set digest, review digest, and policy snapshot identity; it adds immutable binding records, run-manifest records, child-call records, and pending exact-call approvals.
- Existing workflows without MCP nodes remain compatible: their review may be upgraded lazily to a no-binding review digest, and their runner protocol-v1 behavior remains accepted during the migration window.
- Runtime repository `_ensure` methods mirror migration 14 only for independently created test/workspace state and never destructively rewrite existing rows.

### UI

- The workflow review surface adds a capability-binding step showing requirement, exact implementation, server/tool/schema identity, validation freshness, risk/approval implications, ambiguity, and recovery.
- Start is disabled with a specific stale/missing reason. During execution, a run timeline shows node, child, approval, progress, artifact, cancellation, and residue states with stable IDs and non-color text.
- No token, command, endpoint, environment, credential value, or unrestricted path is rendered. Existing workflow UI remains unchanged when a graph has no MCP nodes.

### Test strategy

- Unit/contract: canonical digests, authority claims, expiry/replay/revocation, schema comparison, runner request validation, injected provider behavior, direct-child denial, result bounds, redaction, migrations.
- Integration: one reviewed graph calls two fake MCP servers with colliding unqualified tool names, progress, one exact approval, structured results, artifacts, audit, and deterministic order.
- Negative: disabled, cross-workspace, unreviewed, unbound, dynamic-name, stale schema/revision/validation, expired/replayed token, changed arguments after approval, and post-cancellation calls prove zero child receipt.
- Lifecycle: deterministic panel-backed BREP and host-bridge doubles prove preparation, status, failure, progress, cancellation, and cleanup behind the same bridge contract.
- UI/system: binding/review/start/approval/cancel/recovery journeys plus a local FastAPI/Node/two-child smoke. Live BREP and Solid Edge/available-app tests require explicit environment gates and never run in the ordinary merge gate.

## Gate B Decision

[Gate B](contracts/gate-b-decision.md) is approved under the program goal's advance authority: native Rivet MCP nodes plus an injected Wright provider; exact-origin loopback transport; opaque memory-only run tokens; exact external capability bindings and review invalidation; provider-neutral gateway delegation; explicit cancellation; bounded Run Manifest evidence. Rollback disables MCP issuance and leaves non-MCP workflow execution and prior schema readers intact.

## Post-design Constitution Re-check

The Phase 1 contracts preserve every pre-design PASS. In particular, the internal loopback bridge is not a new user-facing service or identity provider; it is a narrow application-composition adapter over the existing gateway. SQLite remains the only durable relational store, route handlers remain thin, the Node child owns neither credentials nor MCP lifecycle, local fake MCPs cover normal gates, and physical actuation remains excluded by Gate E.

## Complexity Tracking

No constitution violation requires an exception. The added loopback bridge is necessary because the current supervised Node runner has one-shot stdin and async stdout while the gateway lives on the API event loop; replacing it with cross-platform duplex process IPC would enlarge the process-supervisor contract without improving authority confinement.
