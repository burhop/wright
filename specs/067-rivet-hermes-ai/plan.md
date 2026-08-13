# Implementation Plan: Rivet Hermes AI and MCP Execution

**Branch**: `067-rivet-hermes-ai` | **Date**: 2026-08-05 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/067-rivet-hermes-ai/spec.md`

## Summary

Complete the embedded Rivet 2 integration without adding an OpenAI key or modifying Hermes. A Wright-owned compatibility bridge will configure Rivet's custom OpenAI-compatible provider and translate the structured AI contract Rivet needs onto Hermes's existing agent API. A checked-in, pinned Rivet 2 Node runtime will replace the lifecycle fixture for real graph execution. A new workspace-confined Rivet MCP, registered as a Wright-managed server behind the existing `wrightgateway`, will let Hermes list templates, create/inspect/validate workflows, and run the same authoritative revisions that the canvas uses.

The implementation is test-first. Mandatory suites use deterministic fake Hermes and model endpoints. A separately marked, explicit opt-in smoke suite exercises the user's live local Hermes/Codex subscription from both the Rivet AI contract and a Wright chat prompt that invokes the Rivet MCP.

## Technical Context

**Language/Version**: Python 3.11-3.14; TypeScript 5.7/React 18; Node.js 22 for the pinned Rivet runtime build and execution

**Primary Dependencies**: FastAPI, `httpx`, official MCP Python SDK, existing Wright gateway/process supervision, `@valerypopoff/rivet2-core`, `@valerypopoff/rivet2-node`, Vite

**Storage**: Existing workspace `workflows/<slug>/workflow.rivet-project` documents and SQLite review/run metadata; no model credentials in project storage

**Testing**: pytest/pytest-asyncio/respx, Vitest, Node test runner, Playwright component/UI integration, packaging tests, opt-in live pytest smoke marker

**Target Platform**: Wright native runtime on Windows, macOS, and Linux plus the supported Docker appliance; loopback-only editor and AI bridge

**Project Type**: Modular web application with Python services, an isolated browser editor artifact, a bundled Node execution worker, and a stdio MCP server

**Performance Goals**: Forward ordinary streaming deltas without buffering; expose first progress within 5 seconds after Hermes accepts a request; add no more than 250 ms local p95 overhead before upstream connection in controlled tests; stop cancelled controlled runs within 2 seconds

**Constraints**: No Hermes source change or fork; no direct Codex/OpenAI client in Wright; no OpenAI API key; no Hermes secret in browser/project/logs; no runtime npm install; all workflow paths confined to the bound workspace; normal tests make zero subscription calls

**Scale/Scope**: One embedded canvas per active workspace surface, up to two concurrent workflow runs by default, projects up to the existing 4 MiB limit, outputs/logs bounded by runner policy, one Wright-managed Rivet MCP child per bound gateway runtime

## Constitution Check

*GATE: Pass before Phase 0 research; re-checked after Phase 1 design.*

- **Modular boundaries**: Pass. Hermes resolution/translation belongs in `agent_adapters`; workflow validation/execution belongs in `workspace_service`; MCP lifecycle and publication remain in `tool_registry`; API routes remain thin.
- **Offline-first**: Pass with graceful degradation. Deterministic workflows, templates, validation, editor persistence, and all mandatory tests remain local. Subscription-backed AI is an optional configured capability and reports unavailable cleanly; no core artifact is downloaded at runtime.
- **Native distribution**: Pass. Editor and Node runner are reproducibly built from the same pinned Rivet 2 source and inventoried in the wheel; no source checkout or npm install is required after installation.
- **Agent abstraction**: Pass. Wright continues to address Hermes only through the existing agent adapter contract. The browser sees a Wright-local compatibility endpoint, never Codex credentials or a second manager route.
- **Security/identity**: Pass. The editor AI endpoint is loopback-only, origin-isolated, session-token protected, bounded, and credential-redacting. MCP workspace authority is injected from the trusted gateway binding rather than tool arguments.
- **Engineering tool protocol**: Pass. The MCP exposes workflow operations, not a new remote engineering solver. Actual external MCP or native actions requested by a graph continue through the Wright gateway and its approval policy.
- **Three-tier testing**: Pass. Component/contract tests cover UI and adapters, mocked Playwright covers page journeys, and opt-in system E2E covers local Hermes/Codex behavior. Interactive additions receive test IDs.
- **Observability**: Pass. Existing run/session correlation IDs flow through bridge, MCP, and execution events. Logs are structured and redact credentials; timings identify local bridge time separately from upstream/model time.
- **Phase isolation/manual gate**: Pass. This plan, contracts, and tasks are delivered for human approval before implementation begins.

### Post-design re-check

Pass. Contracts keep secrets and arbitrary paths out of browser/MCP inputs, preserve the existing review gate, ship pinned artifacts, and do not introduce a second model path or Hermes modification.

## Architecture

### 1. Rivet-compatible Hermes AI bridge

Add a reusable `HermesOpenAICompatibilityBridge` to `agent_adapters`. It resolves the same Hermes base URL and API key as Wright chat and exposes only a local callable service contract. The Rivet editor host publishes a same-origin runtime configuration containing a short-lived editor token, model alias, and relative compatibility URL; it never publishes the Hermes key.

For ordinary Chat Completions requests, the bridge sends messages through Hermes's existing `/v1/chat/completions` route and relays compatible content deltas. Hermes 0.20's API accepts `tools` and `tool_choice` in request fingerprints but does not pass client tools into `_run_agent` or return OpenAI tool-call deltas. Therefore tool-bearing Rivet requests use an explicit compatibility translation: validate and canonicalize the requested tool schemas, instruct Hermes to return one strict structured decision, validate that decision, and emit the OpenAI tool-call response Rivet expects. No Hermes internal file is patched.

The translation supports Rivet's sequential, single-tool graph-builder loop. Unsupported parallel or ambiguous tool calls fail explicitly. The bridge records separate queue/upstream/translation timing and preserves cancellation.

### 2. Editor bootstrap and browser boundary

The Rivet wrapper seeds its in-memory hybrid storage before `RivetAppHost` mounts:

- `ai/selectAssistModel = "custom"`
- `ai/aiAssistCustomProviderBaseURL = <same-origin compatibility base>`
- `ai/aiAssistCustomModel = "wright-hermes"`
- the runtime custom-provider credential is the short-lived editor token

The host accepts only `POST /wright-ai/v1/chat/completions`, `GET /wright-ai/config`, and health/static routes. It validates content type, method, bearer token, JSON shape, body size, and timeout. CORS is unnecessary because the provider is same-origin. The parent/origin postMessage checks already used for project load/save remain unchanged.

### 3. Real Rivet 2 runtime

Replace `fixture-runner.mjs` with a reproducibly bundled Node worker built from the same pinned Rivet 2 revision as the editor. The worker receives a single JSON request over stdin, resolves only the already-confined project path supplied by the Python host, loads the project through `@valerypopoff/rivet2-node`, validates graph selection, converts bounded loose inputs/context, and emits JSON-line progress and a terminal result.

A Python `RivetRuntimeHost` remains the trusted supervisor boundary. It starts an ephemeral loopback instance of the Hermes compatibility bridge, gives the Node worker only the ephemeral bridge URL/token, and relays structured progress/output to Wright. Thus code or graph data cannot read the long-lived Hermes API key. Existing process limits, cancellation, output caps, and process-tree cleanup remain authoritative.

Initial runtime policy denies native file, arbitrary code, network, external function, and MCP provider capabilities unless a later reviewed capability grant supplies them. Deterministic built-in nodes and AI nodes are supported in this slice.

### 4. Wright-managed Rivet MCP

Add a low-level official-SDK stdio server with these tools:

- `list_templates`
- `list_workflows`
- `inspect_workflow`
- `create_workflow`
- `validate_workflow`
- `run_workflow`

The tool process receives the canonical workspace path, workspace ID, session ID, and database path only through a trusted Wright-managed launch binding. These are not tool arguments and are never accepted from the model. The server uses `WorkspaceWorkflowStore`, the reviewed template catalog, shared validation, review repository, and real execution service.

Add a dedicated Wright-managed server reconciler instead of placing this internal server in the public engineering MCP catalog. On first seed it is installed and enabled; later user disablement is preserved. `wrightgateway` publishes its namespaced tools normally, applies existing annotations/approval policy, starts it lazily for the bound workspace, and forwards progress to Hermes/Wright chat.

### 5. Shared revision, review, and results

Canvas and MCP execution both call one execution service. Before spawn it re-reads the workflow and verifies workflow ID, revision, digest, graph, and durable approval. Each run stores bounded terminal metadata and events in SQLite so a run started from either surface can be inspected consistently. Project content remains file-authoritative and is never duplicated into the database.

Changing a workflow invalidates the previous approval by revision identity. MCP creation returns the new identity but cannot self-approve it. Chat can validate and explain that review is required; an approved revision can then run through either route.

## Project Structure

### Documentation (this feature)

```text
specs/067-rivet-hermes-ai/
|-- spec.md
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   |-- ai-bridge.md
|   |-- rivet-mcp.md
|   `-- runner-protocol.md
|-- checklists/requirements.md
`-- tasks.md
```

### Source Code (repository root)

```text
packages/agent_adapters/
|-- src/agent_adapters/hermes_openai_bridge.py
`-- tests/test_hermes_openai_bridge.py

integrations/rivet/editor/
|-- host.py
|-- wrapper/WrightEditorBridge.tsx
|-- scripts/build-rivet2.mjs
`-- tests/test_rivet2_editor_artifact.py

integrations/rivet/runner/
|-- src/wright-runner.ts
|-- dist/wright-runner.mjs
|-- manifest.json
|-- scripts/build-rivet2-runner.mjs
`-- tests/runner-contract.test.mjs

packages/workspace_service/
|-- src/workspace_service/rivet_runtime_host.py
|-- src/workspace_service/rivet_validation.py
|-- src/workspace_service/rivet_mcp.py
|-- src/workspace_service/workflow_runner.py
|-- src/workspace_service/workflow_operations.py
|-- tests/test_rivet_runtime_host.py
|-- tests/test_rivet_validation.py
|-- tests/test_rivet_mcp.py
`-- tests/test_workflow_runner.py

packages/tool_registry/
|-- src/tool_registry/wright_managed_servers.py
|-- src/tool_registry/catalog_reconcile.py
|-- src/tool_registry/lifecycle_adapters.py
|-- tests/test_wright_managed_servers.py
`-- tests/test_gateway_rivet_mcp.py

apps/web/
|-- src/components/surfaces/DirectRivetSurface.tsx
`-- src/components/surfaces/DirectRivetSurface.spec.tsx

tests/
|-- e2e/test_rivet_hermes_ai_live.py
|-- ui-integration/workspace-surfaces/rivet-ai.spec.ts
`-- packaging/test_wheel_contents.py
```

**Structure Decision**: Extend the existing modular package ownership. The compatibility code belongs to the Hermes adapter, persistence/validation/execution/MCP implementation belongs to workspace service, MCP registration and trusted binding belong to tool registry, and the isolated editor/runner artifacts remain under `integrations/rivet` with manifests checked by packaging tests.

## Delivery Phases

1. Add deterministic failing contracts for the Hermes compatibility behavior, exact Rivet hybrid-storage bootstrap, and secret confinement.
2. Implement the adapter and editor-host route; rebuild and inventory the pinned canvas artifact.
3. Add deterministic runner protocol tests; build and inventory the real pinned Rivet Node worker; replace the fixture while retaining supervisor controls.
4. Add workflow validation and durable run result projection shared by canvas and MCP.
5. Implement/register the workspace-confined Rivet MCP and test Wright gateway discovery, policy, progress, and chat stream relay.
6. Add UI integration, packaging/offline, cancellation/security, and opt-in live Hermes/Codex tests.
7. Run focused suites, the Spec Kit consistency analysis, `scripts/check-dev-merge.sh` before any merge to `dev`, and capture a live Rivet canvas image once the AI-capable build is runnable.

## Verification Strategy

### Deterministic mandatory tests

- Adapter contract: plain completion, SSE chunking, sequential tool translation, malformed JSON, wrong tool, schema rejection, timeout, disconnect, upstream 401/429/5xx, and credential redaction.
- Editor host: config/token lifecycle, wrong bearer, invalid method/content type/path, body cap, loopback bind, health availability, no key in config/static/logs, and SPA regression.
- Rivet graph builder: controlled tool response produces the expected nodes/connections; interrupted generation preserves the graph; save/reload retains the applied proposal.
- Runner: deterministic basic graph inputs/outputs, graph selection, missing input, AI-node call via local fake bridge, output cap, cancellation, concurrency, stale revision, changed digest, and denied capabilities.
- MCP protocol: official SDK initialize/list/call/cancel, workspace confinement, template creation, revision conflict, validation summaries, review-required run, approved run output, progress notifications, and bounded error/result bodies.
- Wright chat: a fake Hermes SSE stream containing a Rivet MCP tool lifecycle is relayed through the existing chat endpoint and produces an authoritative workflow.
- Packaging/offline: wheel contains editor and runner inventories plus MCP entry point; installed runtime works without source checkout, npm, or network.

### Opt-in live tests

Use a new `rivet_live_ai` pytest marker plus `WRIGHT_RIVET_LIVE_AI=1`. The test skips unless local Hermes health and Codex subscription readiness are confirmed. It performs exactly:

1. one tool-bearing compatibility request shaped like Rivet Graph Builder and validates the returned OpenAI tool call; and
2. one Wright chat request instructing Hermes to use the namespaced Rivet MCP to list templates and validate a known workflow, asserting tool progress and the final grounded response.

Live tests log timings and identifiers, never prompts containing secrets or credentials. They are excluded from normal CI and merge gates unless the environment explicitly provisions the subscription.

## Rollback

- Disable the Rivet AI bridge and runner feature flags; editor persistence and saved workflow files remain usable.
- Disable the Wright-managed Rivet MCP row without removing public catalog entries or other MCP state.
- Restore the previous fixture runner manifest only for lifecycle diagnostics; never label it as real execution.
- Revoke ephemeral editor/run tokens and stop owned process trees. Durable workflow files and review history are retained.

## Complexity Tracking

No constitution exception is required. The compatibility translator is necessary because the existing Hermes API does not expose client-provided tool calls, and keeping it in Wright avoids both a Hermes fork and a prohibited direct Codex credential path.
