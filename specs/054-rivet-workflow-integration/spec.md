# Feature Specification: Incremental Rivet Workflow Integration

**Feature Branch**: `054-rivet-workflow-integration`

**Created**: 2026-08-03

**Status**: Draft — umbrella planning feature; implementation occurs only in approved slice branches

**Input**: User description: "Integrate Rivet into Wright incrementally so workflow content is stored per workspace and the Rivet UI appears as a retained workspace tab. Use a separate Spec Kit branch and complete specification/design set for every implementable slice."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Keep Visual Workflows With Their Workspace (Priority: P1)

An engineer creates or edits a visual workflow while working in a Wright workspace. The workflow definition, datasets, generated artifacts, and recoverable run records remain associated with that workspace and are restored when the workspace is reopened.

**Why this priority**: Workspace ownership is the portability, privacy, and collaboration boundary for Wright. A visual editor that stores authoritative content in a browser profile or a global application directory would violate that boundary.

**Independent Test**: Create different workflows in two workspaces, restart Wright, reopen both workspaces, and verify that each workspace restores only its own definitions and artifacts.

**Acceptance Scenarios**:

1. **Given** an authenticated engineer in workspace A, **When** the engineer creates and saves a workflow, **Then** the workflow is stored under workspace A and appears in its workflow collection.
2. **Given** saved workflows in workspaces A and B, **When** the engineer switches between the workspaces, **Then** only the active workspace's workflows, datasets, editor state, and run history are visible.
3. **Given** a saved workflow and generated artifacts, **When** Wright restarts, **Then** the workflow and durable run outputs can be restored without trusting a stale process, port, or credential.

---

### User Story 2 - Edit Workflows in a Retained Workspace Tab (Priority: P1)

An engineer opens a Workflows tab beside chat, edits a Rivet graph, switches to another surface or chat, and returns without losing in-memory editor state or reloading the workflow unnecessarily.

**Why this priority**: The visual editor is the primary reason to integrate Rivet rather than only execute graph files headlessly.

**Independent Test**: Open the Workflows tab, make an unsaved change, switch among chat and two other workspace surfaces repeatedly, and verify that the editor remains mounted and the change remains present.

**Acceptance Scenarios**:

1. **Given** a workspace with workflows enabled, **When** the engineer opens Workflows, **Then** an isolated visual editor appears as a workspace surface with normal tab, focus, resize, keyboard, and diagnostics behavior.
2. **Given** an active edit, **When** the engineer switches tabs and returns, **Then** the same editor instance and unsaved state remain available within the configured retention limit.
3. **Given** a workspace without a usable Rivet runtime, **When** the engineer opens Workflows, **Then** Wright shows actionable setup or compatibility guidance without degrading chat or other surfaces.

---

### User Story 3 - Execute Workflows Through Wright Controls (Priority: P1)

An engineer runs a saved workflow and watches its progress in Wright. Any engineering tool call, approval, artifact publication, cancellation, or failure remains bound to the current Wright user, workspace, and session.

**Why this priority**: Rivet must add visual orchestration without becoming a second authorization, tool-lifecycle, or artifact system.

**Independent Test**: Run a workflow that invokes one read-only tool, requests one approval, produces one artifact, and is then cancelled during a second run; verify policy, audit, output, and cleanup behavior.

**Acceptance Scenarios**:

1. **Given** a reviewed workflow, **When** the engineer runs it, **Then** Wright streams bounded progress and records the exact workflow revision and execution context.
2. **Given** a workflow that requests an engineering tool, **When** the request is evaluated, **Then** Wright's gateway repeats workspace authorization and tool policy before the call executes.
3. **Given** a mutating or high-risk operation, **When** approval is required, **Then** the workflow pauses until Wright records an allow, deny, cancel, or timeout outcome.
4. **Given** an active run, **When** the engineer cancels it, **Then** owned work is cancelled and its process, connection, temporary authority, and pending approval state are cleaned up within the bounded lifecycle policy.

---

### User Story 4 - Deliver the Integration as Reviewable Slices (Priority: P1)

A maintainer can review, test, merge, or roll back each integration capability independently. Every slice has its own Spec Kit branch and complete planning artifacts, and no slice assumes that later slices have already shipped.

**Why this priority**: The requested delivery model explicitly rejects a big-bang integration, and Rivet affects storage, runtime, UI, policy, packaging, and release evidence.

**Independent Test**: Inspect the program plan and a selected slice to verify a unique branch, spec directory, requirements checklist, plan/design artifacts, ordered dependencies, targeted tests, rollback, and human approval gate.

**Acceptance Scenarios**:

1. **Given** the approved umbrella plan, **When** a slice begins, **Then** it is branched from the latest umbrella integration branch using the Spec Kit feature workflow.
2. **Given** a slice branch, **When** planning completes, **Then** its specification, checklist, research, plan, data model, contracts, quickstart, tasks, and analysis are owned by that slice rather than the umbrella feature.
3. **Given** a completed slice, **When** it is merged into the integration branch, **Then** incomplete later slices remain disabled or absent and existing Wright workflows continue to operate.

---

### User Story 5 - Reuse Workflows Without Losing Wright Governance (Priority: P2)

An engineer can start a reviewed workflow from a compact Wright workflow catalog, while an authorized agent can invoke selected workflows through the same governed execution contract. Opening the full editor is optional for routine runs.

**Why this priority**: A lightweight operational experience makes visual workflows useful beyond their authors while keeping the full editor available for design and debugging.

**Independent Test**: Run a reviewed workflow once from the Wright UI and once through the agent-facing contract, then compare revision, policy, artifacts, and audit identity.

**Acceptance Scenarios**:

1. **Given** a reviewed workflow, **When** an engineer selects Run from Wright's workflow catalog, **Then** the workflow executes without loading the full editor.
2. **Given** a workflow explicitly published for agent use, **When** an authorized agent invokes it, **Then** Wright validates its input, binds it to the exact workspace/session, and applies the same tool and approval policies as an interactive run.

### Edge Cases

- A workspace is deleted, moved, made read-only, or disconnected while its editor or runner is active.
- Two browser tabs or users save the same workflow revision concurrently.
- The Rivet project or dataset sidecar is malformed, too large, from an unsupported version, or references a missing project.
- A workflow is saved successfully but its dataset, recording, or artifact write fails, or the process stops between staging and atomic replacement.
- An unsaved edit exists when the retained surface is evicted for resource pressure.
- The browser supports neither native file-system pickers nor persistent local storage.
- The optional Node runtime, editor bundle, plugin, or pinned Rivet version is missing or incompatible.
- A workflow attempts to escape the workspace through absolute paths, traversal, symlinks, project references, file nodes, code nodes, HTTP nodes, or direct MCP configuration.
- A workflow attempts to store a secret, durable bearer token, transient presentation credential, or workspace/session identifier in its project file.
- A tool list changes during a workflow run, or a requested tool becomes unhealthy after discovery.
- Approval is denied, expires, is revoked, or belongs to another workspace, user, run, node, or runtime generation.
- Wright restarts while a run is active, or a stale Rivet debugger reconnects to a new workspace generation.
- A workflow produces oversized progress events, logs, recordings, datasets, or artifacts.
- Panel presentation is unavailable because isolated origins, framing policy, or required browser capabilities are not present.
- The system is offline and cannot reach an external package registry, model provider, or plugin source.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Wright MUST treat workflow definitions, dataset sidecars, and user-owned workflow assets as workspace-owned files rather than browser-profile or global application state.
- **FR-002**: Wright MUST prevent a workflow editor or runner bound to one workspace from reading, listing, writing, executing, or restoring content belonging to another workspace.
- **FR-003**: Wright MUST provide deterministic locations for authored workflow content, generated run artifacts, and private editor/runtime metadata, with each class documented separately.
- **FR-004**: Wright MUST save workflow files atomically and detect conflicting or stale revisions before overwriting a newer save.
- **FR-005**: Engineers MUST be able to create, open, save, save as, autosave, recover, rename, and delete workflows within the active workspace subject to existing Wright permissions.
- **FR-006**: Wright MUST restore durable workflow intent after restart without restoring stale process identifiers, ports, sockets, presentation credentials, approval grants, or bearer tokens.
- **FR-007**: Wright MUST keep secrets and reusable credentials out of workflow definitions, datasets, editor state, recordings, URLs, logs, and generated artifacts.
- **FR-008**: Wright MUST expose the visual workflow editor as an isolated workspace surface that participates in existing tab, focus, resize, retention, accessibility, diagnostics, and close/stop semantics.
- **FR-009**: Wright MUST preserve unsaved editor state while the workflow surface remains retained and MUST warn or recover before an unsaved surface is evicted or stopped.
- **FR-010**: Wright MUST provide an actionable degraded experience when the editor or runner is unavailable, without breaking chat, files, existing surfaces, or non-Rivet execution.
- **FR-011**: Wright MUST run saved workflows through an execution boundary explicitly bound to the authenticated principal, workspace, session, workflow revision, and runtime generation.
- **FR-012**: Wright MUST support bounded workflow start, progress, pause/approval wait, cancellation, completion, failure, restart recovery, and cleanup outcomes.
- **FR-013**: Every engineering tool request initiated by a workflow MUST pass through Wright's provider-neutral gateway and server-side policy; client annotations and Rivet configuration MUST NOT authorize a call.
- **FR-014**: Mutating or high-risk workflow operations MUST use Wright's existing approval and revocation semantics with exact run, node, tool, user, workspace, and session scope.
- **FR-015**: Workflow outputs MUST be published through Wright's artifact and surface contracts with provenance linking the workflow revision, run, inputs, effective constraints, tools, approvals, and trace.
- **FR-016**: Administrators MUST be able to restrict or disable executable code, arbitrary network calls, direct MCP servers, unreviewed plugins, filesystem access, graph upload, and agent publication independently.
- **FR-017**: The integration MUST support a fully offline installation and execution path for pinned, prepackaged editor, runner, adapters, and approved plugins.
- **FR-018**: Rivet and Node dependencies MUST remain optional for Wright deployments that do not enable visual workflows.
- **FR-019**: Production artifacts MUST run without a Wright or Rivet source checkout and MUST declare pinned versions, licenses, checksums, dependency inventory, and supported-platform evidence.
- **FR-020**: Wright MUST identify workflow and schema versions, reject unsupported future formats safely, and provide explicit migration and rollback behavior for supported older formats.
- **FR-021**: Wright MUST record structured, redacted diagnostics and traces for workflow storage, editor lifecycle, execution, tool calls, approvals, artifacts, and cleanup.
- **FR-022**: Engineers MUST be able to run a reviewed workflow from a lightweight Wright workflow view without loading the full visual editor.
- **FR-023**: Wright MAY expose explicitly published workflows to agents only through typed, workspace-bound contracts with the same authorization and audit behavior as interactive runs.
- **FR-024**: The program MUST be delivered as independently testable slices; every implementation slice MUST have its own Spec Kit feature branch, feature directory, specification, checklist, research, plan, data model where applicable, contracts where applicable, quickstart, tasks, analysis, implementation evidence, and human planning approval.
- **FR-025**: Slice branches MUST target the umbrella integration branch until the integrated program passes its merge gates; numeric Spec Kit prefixes MUST be assigned when a slice starts rather than reserved in advance.
- **FR-026**: Each slice MUST define prerequisites, scope exclusions, feature flags or absence behavior, migration impact, rollback, targeted tests, packaging impact, and merge evidence so later slices are not required for correctness.
- **FR-027**: The umbrella branch MUST contain coordination documents only until a slice is approved and merged; implementation code MUST NOT be developed directly on the umbrella branch.
- **FR-028**: Before the umbrella branch is merged to `dev`, the complete integration MUST pass the authoritative `scripts/check-dev-merge.sh` gate or document a specific local-host limitation as required by repository policy.

### Key Entities

- **Workflow Definition**: A workspace-owned, versioned visual graph with identity, title, graph inputs/outputs, references, plugin requirements, policy classification, review state, and content revision.
- **Workflow Dataset**: Data associated with one workflow project and stored alongside or below the workspace-owned workflow definition.
- **Workflow Editor Surface**: A retained, isolated presentation bound to one workspace, editor instance, runtime generation, and optional selected workflow.
- **Workflow Run**: One execution of an immutable workflow revision with principal, workspace, session, inputs, context, state, timestamps, trace, cancellation identity, and result.
- **Workflow Node Event**: A bounded progress, output, request, warning, or failure event associated with one run and node.
- **Workflow Artifact**: A durable output indexed by Wright and linked to its producing run, workflow revision, tool calls, approvals, and provenance.
- **Workflow Policy Profile**: The effective restrictions on code, files, network, MCP, plugins, graph upload, agent publication, and resource limits.
- **Workflow Publication**: An explicit mapping that allows a reviewed workflow revision to appear in the Wright catalog or agent-facing tool surface.
- **Delivery Slice**: An independently specified branch with prerequisites, scope, contracts, gates, rollback, and evidence that merges into the umbrella integration branch.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In 100 cross-workspace save, restore, and run trials, zero workflow definitions, datasets, editor state, tools, approvals, or artifacts are visible or usable outside their bound workspace.
- **SC-002**: A saved workflow and its dataset survive Wright restart and can be reopened without a source checkout in 100% of supported-platform acceptance runs.
- **SC-003**: A retained editor preserves an unsaved change across 100 consecutive switches among chat and workspace surfaces with zero unintended reloads.
- **SC-004**: At least 95 of 100 warm supported-host trials make the Workflows tab interactive within 5 seconds; failure produces actionable diagnostics rather than a blank surface.
- **SC-005**: A user can create, save, close, reopen, and run a basic workflow in under 5 minutes using documented UI paths.
- **SC-006**: Cancellation becomes visible to the user within 2 seconds and leaves zero owned workflow processes, ports, pending approvals, temporary credentials, or active tool calls after the configured cleanup bound.
- **SC-007**: Security tests demonstrate zero successful bypasses of workspace confinement or Wright tool policy through code, file, network, project-reference, plugin, direct-MCP, graph-upload, redirect, or debugger paths.
- **SC-008**: Every completed run exposes one coherent provenance view containing workflow revision, inputs, constraints, node/tool outcomes, approvals, artifacts, trace identifier, and terminal status without revealing secrets.
- **SC-009**: Wright starts and its existing non-Rivet user journeys pass when all Rivet features and dependencies are absent or disabled.
- **SC-010**: A clean offline installation can open the packaged editor and execute the reference workflow without downloading editor, runner, plugin, or rendering assets at runtime.
- **SC-011**: Every production implementation slice can be reviewed, tested, merged, disabled, and rolled back independently while all earlier accepted slices remain operational.
- **SC-012**: The final umbrella integration passes the repository's authoritative development merge gate and records native and Docker evidence for every supported platform claim.

## Assumptions

- The long-lived `054-rivet-workflow-integration` branch is an integration and coordination branch based on the latest fetched `dev`; implementation slice branches target it and are merged in dependency order.
- Spec Kit assigns the next available sequential number when each slice begins; the overall plan defines stable short names but does not reserve future numbers.
- The existing Workspace Surface implementation remains the presentation and process-lifecycle foundation; Rivet does not introduce a second iframe, proxy, or process-supervision framework.
- The workspace filesystem is authoritative for user-owned workflow definitions and datasets. SQLite and the Wright file vault index durable metadata, events, provenance, and large/immutable payloads according to existing ownership rules.
- The supported integration uses a pinned Wright-hosted Rivet editor build and a pinned optional Node runner. Direct imports of Rivet's React application into Wright's React tree are out of scope.
- A small Rivet host-adapter patch is acceptable if upstream does not yet expose injectable IO, dataset, and native API providers, but the patch must be isolated, documented, and covered by compatibility evidence.
- Full arbitrary Rivet plugin compatibility is not a version-one goal. Wright-provided and explicitly approved plugins are the supported baseline.
- Existing Wright authentication, RBAC, gateway authorization, approval, audit, observability, workspace confinement, surface isolation, artifact, packaging, and release contracts remain authoritative.
- Agent-callable workflow publication is a later optional slice and is not required for the first user-operable visual workflow MVP.
- Implementation starts only after human approval of this umbrella plan and then separate human approval of each slice plan.
