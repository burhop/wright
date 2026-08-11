# Feature Specification: Rivet Hermes AI and MCP Execution

**Feature Branch**: `067-rivet-hermes-ai`

**Created**: 2026-08-05

**Status**: Draft

**Input**: User description: "Enable Rivet's AI functionality through the Codex subscription already used by Hermes, make workflows executable, and add a new MCP so Wright chat can create and run the same workflows. Do not modify Hermes."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Build a workflow with Rivet AI (Priority: P1)

An engineer opens a workspace workflow in the embedded Rivet canvas, selects the sparkle action, describes a workflow, and receives a usable graph without entering an OpenAI API key. The AI request uses the Codex subscription already available through Wright's configured Hermes service.

**Why this priority**: The embedded editor's advertised AI controls are incomplete unless they can build and revise a graph in Wright's supported subscription-based configuration.

**Independent Test**: Open an empty workflow, ask the sparkle action to create a deterministic two-node graph, apply the proposal, save it, reload it, and verify the generated nodes and connections remain present.

**Acceptance Scenarios**:

1. **Given** Hermes is running with a usable Codex subscription, **When** the engineer submits a valid sparkle prompt, **Then** Rivet shows streamed progress and produces a graph proposal that can be applied.
2. **Given** the proposal has been applied, **When** the engineer saves and reloads the workflow, **Then** Wright loads the same generated graph from the authoritative workspace file.
3. **Given** Hermes is unavailable or not configured, **When** the engineer opens or uses the sparkle action, **Then** Wright reports that AI is unavailable without requesting or exposing an OpenAI API key.
4. **Given** an AI response is malformed or interrupted, **When** Rivet processes it, **Then** the existing graph remains recoverable and the engineer receives an actionable error.

---

### User Story 2 - Create and run workflows from Wright chat (Priority: P1)

An engineer asks the Wright chat agent to list templates, create or inspect a Rivet workflow, validate it, and run it. Hermes fulfills the request by using a new Wright-managed Rivet MCP whose authority is restricted to the current workspace.

**Why this priority**: This is the agent-facing counterpart to the visual editor and makes workflows operable through the normal Wright-to-Hermes conversation path.

**Independent Test**: In a clean workspace, prompt Wright chat to create the basic template as `chat-basic`, validate it, run it with known inputs, and report the bounded output; verify the file opens unchanged in the Rivet canvas.

**Acceptance Scenarios**:

1. **Given** a Wright workspace and an active Hermes session, **When** the engineer asks chat to list Rivet templates, **Then** Hermes can discover and call the Rivet MCP and return the workspace-visible template choices.
2. **Given** a selected template and safe workflow slug, **When** chat requests creation, **Then** the MCP creates one authoritative workspace workflow that opens in the Rivet canvas.
3. **Given** an existing workflow, **When** chat requests validation, **Then** the MCP returns graph identities, input/output declarations, and actionable validation errors without returning an unbounded project payload.
4. **Given** an approved runnable workflow revision, **When** chat requests execution with valid inputs, **Then** the MCP runs that exact revision and returns its outputs and run identity.
5. **Given** a workflow file outside the active workspace or an unsafe path-like identifier, **When** a tool call attempts to access it, **Then** the MCP rejects the request without reading or changing the target.

---

### User Story 3 - Run the same workflow from the canvas (Priority: P2)

An engineer can run a reviewed workflow from Wright's Rivet toolbar and see useful progress and output for the exact saved revision. AI nodes use the same Hermes-backed subscription route as the sparkle action.

**Why this priority**: Visual authoring is only complete when the engineer can execute and diagnose the graph without switching to chat.

**Independent Test**: Open a saved workflow containing deterministic nodes and an AI node, approve its current revision, run it from the toolbar against a controlled compatible provider, and verify progress, output, cancellation, and revision identity.

**Acceptance Scenarios**:

1. **Given** an approved saved revision, **When** the engineer selects Run, **Then** Wright executes that exact revision and exposes queued, running, and terminal status.
2. **Given** a graph containing an AI node, **When** it executes, **Then** the node uses Hermes and the Codex subscription without a browser-visible upstream credential.
3. **Given** a run is active, **When** the engineer cancels it, **Then** child execution is stopped within the configured deadline and the run becomes terminal.
4. **Given** the open canvas has unsaved changes, **When** the engineer selects Run, **Then** Wright clearly requires save or identifies that the saved revision, not the draft, will run.

---

### User Story 4 - Verify subscription-backed AI safely (Priority: P2)

A maintainer can test the complete behavior deterministically without consuming a subscription, and can opt into a clearly labeled live test using the locally configured Hermes/Codex subscription.

**Why this priority**: AI and streaming behavior are otherwise prone to regressions, while mandatory live subscription calls would make routine test runs slow, costly, and unreliable.

**Independent Test**: Run the deterministic suites against controlled AI and MCP doubles, then enable the live marker and verify one sparkle-style tool-call response and one Wright chat MCP workflow journey against local Hermes.

**Acceptance Scenarios**:

1. **Given** no live subscription is available, **When** the normal test suites run, **Then** AI graph building, streaming, execution, failure, and cancellation contracts are verified using deterministic local doubles.
2. **Given** an explicitly enabled live-test environment with Hermes available, **When** the live smoke suite runs, **Then** it verifies both Rivet-originated AI behavior and a Wright-chat-originated Rivet MCP call.
3. **Given** the live-test opt-in is absent, **When** tests run, **Then** no request is sent to a subscription-backed model.

### Edge Cases

- Hermes is healthy at editor startup but stops during an AI stream.
- Hermes returns plain text when Rivet expects a structured tool call, multiple tool calls, or an incomplete streamed tool call.
- The browser attempts to reuse the local Rivet bridge credential from another origin or send an oversized request.
- A workflow changes after approval but before a queued run starts.
- A graph has no main graph, names a missing graph, has missing required inputs, or produces a very large output.
- Two chat requests attempt to create the same slug or save against the same revision.
- A workflow requests network, filesystem, code, MCP, or native capabilities beyond the run's approved authority.
- The Node runtime, Rivet runtime artifact, Wright gateway, or new MCP is unavailable.
- A process exits without a final result, ignores cancellation, or leaves partial output.
- A workflow or template contains invalid Rivet project content.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Wright MUST configure Rivet's embedded AI controls to use the existing Hermes service and its Codex subscription without requiring an OpenAI API key from the engineer.
- **FR-002**: Wright MUST NOT add a direct Codex client, a second agent route, or a required Hermes modification for this feature.
- **FR-003**: Browser-originated Rivet AI requests MUST be mediated by a Wright-owned local boundary that keeps Hermes credentials out of browser state, workflow files, logs, and error messages.
- **FR-004**: The local AI boundary MUST accept only the minimum request shape and route needed by the embedded Rivet client, enforce origin-independent authorization, bound request sizes and timeouts, and preserve compatible streaming responses.
- **FR-005**: Rivet's sparkle workflow MUST support the structured response or tool-call behavior required to propose and apply graph changes through Hermes.
- **FR-006**: AI availability and failures MUST be reported in the Rivet UI without damaging the last saved workflow or silently changing providers.
- **FR-007**: Wright MUST provide one new Rivet MCP server through the existing Wright MCP gateway; Hermes MUST discover it through the normal workspace tool path.
- **FR-008**: The Rivet MCP MUST derive its workspace authority from the server launch context and MUST NOT accept an arbitrary workspace root or unrestricted file path from a tool caller.
- **FR-009**: The Rivet MCP MUST provide bounded tools to list templates, list workflows, inspect a workflow, create a workflow from a template or valid project, validate a workflow, and run a workflow.
- **FR-010**: Workflow creation and updates through the MCP MUST use the existing authoritative workspace store and revision-conflict behavior so canvas and chat cannot create divergent copies.
- **FR-011**: Validation MUST identify the selected/main graph, declared inputs and outputs, unsupported requirements, and actionable structural errors before execution.
- **FR-012**: The workflow runner MUST execute actual Rivet 2 graphs rather than the current lifecycle-only fixture.
- **FR-013**: Runs MUST bind to an immutable workflow identifier, revision, and digest, and MUST refuse stale, missing, or unapproved revisions.
- **FR-014**: Runs MUST support an explicitly selected graph, bounded input and context values, streamed lifecycle progress, bounded output capture, cancellation, concurrency limits, and terminal error reporting.
- **FR-015**: AI nodes executed inside a workflow MUST use the same Hermes-backed subscription route as the embedded AI controls and MUST NOT require graph-stored Hermes credentials.
- **FR-016**: Workflow capabilities that can mutate files, invoke tools, run code, or use the network MUST remain denied unless explicitly represented by existing Wright approval and gateway policy.
- **FR-017**: The editor toolbar and MCP MUST observe the same review requirement before executing a workflow revision.
- **FR-018**: Wright chat MUST be able to invoke the Rivet MCP through Hermes and relay MCP progress, results, and failures through the existing chat stream.
- **FR-019**: Normal automated tests MUST use local deterministic doubles and MUST make no subscription-backed calls.
- **FR-020**: An opt-in live suite MUST verify one Rivet AI graph-building interaction and one Wright-chat-to-Rivet-MCP interaction against locally configured Hermes/Codex access.
- **FR-021**: Health and diagnostic responses MUST distinguish editor, AI bridge, runtime, and MCP availability without exposing secrets.
- **FR-022**: The shipped native and container artifacts MUST include the Rivet runtime and MCP entry point without requiring a Wright source checkout.

### Key Entities

- **Rivet AI Bridge Session**: A short-lived, local authorization context connecting one embedded editor host to the configured Hermes service; includes availability and expiry but no browser-visible Hermes credential.
- **Workflow Document**: The existing authoritative workspace-owned Rivet project, identified by workflow ID, slug, revision, and digest.
- **Workflow Template**: A reviewed catalog item that can seed a new authoritative workflow.
- **Workflow Validation Result**: A bounded report of graph identity, declarations, warnings, errors, and runtime requirements for one immutable revision.
- **Workflow Run Request**: A request bound to workspace, session, workflow revision, graph, inputs, context, and approved capabilities.
- **Workflow Run Result**: Bounded outputs and lifecycle evidence tied to the run identity, workflow revision, and terminal state.
- **Rivet MCP Server**: A Wright-managed, workspace-confined tool server exposed to Hermes through the existing gateway.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In the live opt-in smoke test, an engineer can submit a sparkle prompt and receive the first visible progress event within 5 seconds of Hermes accepting the request, excluding model queue time recorded separately.
- **SC-002**: The deterministic sparkle contract applies the expected graph proposal and retains it after save/reload in 100% of test runs.
- **SC-003**: A Wright chat prompt can create, validate, and run a deterministic template through the Rivet MCP with no manual tool selection after the server is enabled.
- **SC-004**: The same saved workflow revision produces the same deterministic output whether started from the canvas or the MCP.
- **SC-005**: All path traversal, cross-workspace, stale-revision, wrong-authorization, and oversized-payload tests are rejected before execution or upstream forwarding.
- **SC-006**: Cancellation reaches a terminal state within the configured two-second graceful deadline in the controlled integration test, with forced cleanup reported when required.
- **SC-007**: Routine unit, contract, UI, packaging, and E2E suites make zero live subscription requests; the live suite runs only with explicit opt-in.
- **SC-008**: Static inspection and tests find no Hermes credential in browser storage, project files, captured logs, MCP results, health responses, or generated artifacts.
- **SC-009**: Existing Wright chat behavior and existing non-Rivet MCP servers pass their regression suites without Hermes source changes.

## Assumptions

- Hermes remains the configured Wright agent manager and already has functioning Codex subscription access.
- The existing Hermes OpenAI-compatible chat endpoint remains the only model ingress used by this feature.
- Existing Wright workflow files, review records, gateway approvals, process supervision, and template catalog remain authoritative.
- A compatible Node.js runtime is a supported prerequisite for local Rivet graph execution and will be included or validated by Wright's supported packaging paths.
- Deterministic tests may emulate Hermes responses, including streaming tool calls; live subscription behavior is verified only by explicit opt-in smoke tests.
- Changes to Hermes, direct OpenAI API credentials, multi-provider routing, remote/shared editor hosting, and autonomous approval of high-authority workflow capabilities are out of scope.
