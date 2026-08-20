# Feature Specification: Rivet Run Inspector

**Feature Branch**: `codex/075-rivet-run-inspector`  
**Created**: 2026-08-19  
**Status**: Draft  
**Input**: User description: "Add a first-class, collapsible Run Inspector for Rivet workflows that shows complete outputs, live progress, node-level results, errors and recovery guidance, and run history without permanently reducing canvas space."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Understand the workflow result (Priority: P1)

As a workflow author, I can see whether a run is queued, running, succeeded, failed, or was cancelled; how long it has taken; which step is active; and the complete named outputs when it finishes, so I can understand the result without opening Logs or guessing from a short status banner.

The Run Inspector opens as a collapsible bottom panel so it can present detailed information without permanently taking horizontal space from the workflow canvas.

**Why this priority**: Running a workflow has little user value if the result is hidden, truncated, or difficult to interpret.

**Independent Test**: Run a workflow with a known text and structured output, observe live progress, then verify that the completed run exposes each full named output and that collapsing the inspector restores the canvas area.

**Acceptance Scenarios**:

1. **Given** a saved, runnable workflow, **When** the user starts it, **Then** the interface shows the run state, elapsed time, active step, and completed-step count without requiring another page.
2. **Given** a successful run with multiple named outputs, **When** the run finishes, **Then** the inspector shows every output with its name, type-appropriate presentation, and access to the complete value.
3. **Given** an open Run Inspector, **When** the user collapses it, **Then** the workflow canvas regains the occupied space while a compact run summary remains available.
4. **Given** a successful run that produces no visible output, **When** it finishes, **Then** the interface explicitly states that the run succeeded with no visible output rather than appearing blank or stalled.

---

### User Story 2 - Diagnose and recover from a failed step (Priority: P2)

As a workflow author, I can identify the failed node or MCP tool, see a plain-language reason and safe next action, inspect technical details when needed, and retry appropriately without losing successful upstream evidence.

**Why this priority**: MCP and workflow failures are inevitable; useful diagnosis and recovery determine whether users can continue independently.

**Independent Test**: Run a workflow with an intentionally invalid MCP argument and verify that the inspector identifies the failing step, preserves prior successful steps, explains the problem, and offers only recovery actions that are safe for the run.

**Acceptance Scenarios**:

1. **Given** a workflow whose child operation fails, **When** the failure is reported, **Then** the inspector opens automatically and identifies the node, tool, duration, reason, and recommended next action.
2. **Given** a failed run with diagnostic evidence, **When** the user expands technical details, **Then** the interface shows the error code, run identity, trace identity when available, and relevant evidence without exposing secrets.
3. **Given** successful upstream steps followed by a failed step, **When** the run is inspected, **Then** the successful steps remain visible and distinguishable from the failed and unstarted steps.
4. **Given** a run for which partial retry cannot be proven safe, **When** recovery actions are shown, **Then** the interface offers a full rerun and does not imply that an unsafe partial retry is available.

---

### User Story 3 - Inspect execution flow on the canvas (Priority: P2)

As a workflow author, I can correlate inspector steps with nodes on the workflow canvas so I can quickly understand where execution is occurring or failed.

**Why this priority**: A list of step names is less useful when users cannot connect it to the visual workflow they created.

**Independent Test**: Run a multi-node workflow, select steps in the inspector, and verify that the corresponding nodes are highlighted with accessible running, succeeded, failed, cancelled, or not-run states.

**Acceptance Scenarios**:

1. **Given** a running multi-node workflow, **When** execution advances, **Then** affected canvas nodes reflect their current execution states without relying on color alone.
2. **Given** an inspector step associated with a current canvas node, **When** the user selects the step, **Then** the matching node is brought into view and highlighted.
3. **Given** a historical run whose node was edited or removed, **When** the user selects that historical step, **Then** the inspector explains that the original node is no longer present instead of highlighting an unrelated node.

---

### User Story 4 - Resume observation and review run history (Priority: P3)

As a workflow author, I can refresh or reopen the workspace without losing an active run, and I can review recent runs with their revision, state, duration, outputs, and diagnostics.

**Why this priority**: Long-running workflows and intermittent browser sessions require durable visibility, but a useful current-run experience is the first priority.

**Independent Test**: Start a delayed workflow, refresh while it is running, verify reattachment to the same run, then inspect that run from recent history after completion.

**Acceptance Scenarios**:

1. **Given** an active run, **When** the browser is refreshed, **Then** the workspace reconnects to the same run and resumes status updates without starting a duplicate run.
2. **Given** multiple recent runs, **When** the user opens run history, **Then** each entry shows its workflow revision, final state, start time, duration, and whether outputs or diagnostics are available.
3. **Given** a historical run from an older workflow revision, **When** it is inspected, **Then** the interface clearly distinguishes the historical revision from the currently open revision.

### Edge Cases

- A run succeeds with no outputs, null outputs, or only intermediate values.
- An output is very large, deeply nested, binary, an artifact reference, or a URL.
- An output or diagnostic contains a secret, OAuth credential, authorization header, or sensitive MCP payload.
- A backend limit truncates or omits a result before the interface receives it.
- The browser refreshes before the first response event or while a child MCP call is active.
- A run fails before any child step starts, or a child succeeds but a downstream node fails.
- The workflow is edited, saved as a new revision, or a node is removed after a historical run.
- Multiple attempts exist for the same revision and have similar timestamps.
- Historical evidence is missing, expired, or no longer accessible.
- The workspace is narrow, the active surface is maximized, or the user navigates only by keyboard.
- A user cancels a run while a child operation is in progress.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The workspace MUST present a compact run summary containing state and elapsed or completed duration for the current or most recently selected run.
- **FR-002**: The workspace MUST provide a collapsible Run Inspector that does not permanently consume horizontal canvas space.
- **FR-003**: While a run is active, the Run Inspector MUST show elapsed time, the current step when known, and completed-step progress when known.
- **FR-004**: For a completed run, the Run Inspector MUST show all available named final outputs and clearly distinguish final outputs from intermediate step results.
- **FR-005**: Result presentation MUST support readable text, structured data, lists, links, and artifact references with appropriate view, copy, download, or open actions when those actions are available.
- **FR-006**: Large results MUST use a bounded initial rendering while retaining a clear way to inspect or export the complete available value.
- **FR-007**: The Run Inspector MUST show an ordered execution-step view with associated node, MCP tool or operation, state, and duration when available.
- **FR-008**: Selecting an execution step MUST highlight and bring the corresponding current canvas node into view; if the original node is absent, the interface MUST explain that condition.
- **FR-009**: Canvas execution states MUST communicate running, succeeded, failed, cancelled, and not-run conditions without relying on color alone.
- **FR-010**: On failure, the Run Inspector MUST open automatically and present a plain-language summary, the failing node or operation, and a recommended recovery action.
- **FR-011**: Failure details MUST optionally expose the run identity, tool or operation identity, reason code, trace identity when available, and relevant diagnostic evidence.
- **FR-012**: A failed run MUST retain and display available successful upstream step results and distinguish them from failed or unstarted steps.
- **FR-013**: The interface MUST always allow an eligible workflow to be rerun from the start and MUST offer partial retry only when the system can determine that retrying from that point is safe.
- **FR-014**: Refreshing or reopening a workspace during an active run MUST reconnect to the existing run and MUST NOT create a duplicate run solely because the page reloaded.
- **FR-015**: The workspace MUST provide bounded recent-run history with revision, start time, final state, duration, and result or diagnostic availability.
- **FR-016**: Historical run inspection MUST identify the workflow revision used and distinguish it from the currently open revision.
- **FR-017**: Outputs, copies, exports, diagnostics, and error summaries MUST apply the product's redaction rules before information is shown or transferred.
- **FR-018**: If result data was truncated, omitted, expired, or unavailable, the interface MUST disclose that limitation and MUST NOT present partial data as complete.
- **FR-019**: Run status, inspector controls, execution steps, outputs, and recovery actions MUST be keyboard operable and understandable with assistive technology.
- **FR-020**: The feature MUST preserve existing workflow Run, Run Options, Cancel, save-before-run, and lint behavior while improving their status and result presentation.
- **FR-021**: Automated UI coverage MUST include default, running, succeeded, failed, cancelled, refreshed, historical, empty-output, large-output, and redacted-output states.

### Key Entities *(include if feature involves data)*

- **Workflow Run Summary**: The user-facing identity and lifecycle of one execution, including workflow, revision, state, timestamps, duration, progress, and availability of results or diagnostics.
- **Execution Step**: A node or operation observed during a run, including ordering, node association, tool or operation identity, state, duration, attempts, and available result or error evidence.
- **Run Result**: A named final or intermediate value with type, display metadata, redaction state, completeness, and optional artifact or link actions.
- **Run Diagnostic**: A plain-language failure summary plus optional technical identifiers, reason codes, evidence, and recovery guidance.
- **Workflow Run History**: A bounded ordered collection of run summaries that preserves revision identity and supports selecting a run for inspection.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In usability testing, at least 90% of participants can identify whether a run succeeded and open its complete primary result within two interactions after completion.
- **SC-002**: Visible run state and progress update within one second of the workspace receiving new execution information.
- **SC-003**: For tested workflow failures with available evidence, users can identify the failing node or operation and a recommended next action without opening the separate Logs page.
- **SC-004**: In local development tests, refreshing during an active run reconnects to the same run and restores its visible state within three seconds without creating a duplicate execution.
- **SC-005**: Collapsing the Run Inspector restores the canvas space it occupied and does not leave a permanent result sidebar.
- **SC-006**: All run states, inspector actions, execution-step navigation, and result actions pass the project's keyboard and accessible-name checks.
- **SC-007**: The run identity shown in the workspace, recent history, and diagnostic evidence is consistent for every tested execution.
- **SC-008**: Automated redaction tests confirm that configured secrets and credentials never appear in visible outputs, copied text, exported results, diagnostic summaries, or captured screens.

## Assumptions

- A bottom inspector is the preferred default because the Agent control pane already consumes horizontal space; users may collapse it whenever they need maximum canvas area.
- Existing run, history, evidence, artifact, and cancellation records remain the authoritative sources; this feature organizes and exposes them rather than creating a second execution system.
- The first release guarantees full rerun from the start. Partial retry appears only where existing execution evidence and operation semantics can prove it safe.
- Recent history is bounded according to existing retention and performance limits and remains local to the relevant workspace and workflow context.
- Existing output-size and evidence-retention limits remain in force, but the interface clearly discloses when they affect completeness.
- This feature does not redesign workflow authoring, MCP installation, or the Agent control pane.
