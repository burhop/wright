# Feature Specification: Rivet Run Inspector

**Feature Branch**: `codex/live-qa-20260821-112046`
**Created**: 2026-08-19
**Updated**: 2026-08-21
**Status**: Draft
**Input**: User description: "Give mechanical engineers a five-section Run Inspector that retains safe inputs, artifact-first outputs, one truthful row per Rivet box, useful failure diagnosis, and recent history; promised document or file deliverables must be created as authoritative workspace artifacts by an approved producing capability."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Understand the workflow result (Priority: P1)

As a mechanical engineer, I can see whether a run is queued, running, succeeded, failed, or was cancelled; how long it has taken; which step is active; and the complete named outputs when it finishes, so I can understand the result without opening Logs or guessing from a short status banner.

The Run Inspector opens as a collapsible bottom panel so it can present detailed information without permanently taking horizontal space from the workflow canvas.

**Why this priority**: Running a workflow has little user value if the result is hidden, truncated, or difficult to interpret.

**Independent Test**: Run a workflow with a known text and structured output, observe live progress, then verify that the completed run exposes each full named output and that collapsing the inspector restores the canvas area.

**Acceptance Scenarios**:

1. **Given** a saved, runnable workflow, **When** the user starts it, **Then** the interface shows the run state, elapsed time, active step, and completed-step count without requiring another page.
2. **Given** a successful run with multiple named outputs, **When** the run finishes, **Then** the inspector shows every output with its name, type-appropriate presentation, and access to the complete value.
3. **Given** an open Run Inspector, **When** the user collapses it, **Then** the workflow canvas regains the occupied space while a compact run summary remains available.
4. **Given** a successful run that produces no visible output, **When** it finishes, **Then** the interface explicitly states that the run succeeded with no visible output rather than appearing blank or stalled.
5. **Given** a run with supplied graph inputs, **When** the user opens the inspector, **Then** an Inputs section shows the safe retained values and discloses any value that was redacted, truncated, expired, or not retained.
6. **Given** a run with authoritative file artifacts, **When** the user opens Outputs, **Then** those artifacts are presented before ordinary values with verified identity and an available open or download action; a value is never described as a file without an authoritative artifact reference.

---

### User Story 2 - Diagnose and recover from a failed step (Priority: P2)

As a mechanical engineer, I can identify the failed node or MCP tool, see a plain-language reason and safe next action, inspect technical details when needed, and retry appropriately without losing successful upstream evidence.

**Why this priority**: MCP and workflow failures are inevitable; useful diagnosis and recovery determine whether users can continue independently.

**Independent Test**: Run a workflow with an intentionally invalid MCP argument and verify that the inspector identifies the failing step, preserves prior successful steps, explains the problem, and offers only recovery actions that are safe for the run.

**Acceptance Scenarios**:

1. **Given** a workflow whose child operation fails, **When** the failure is reported, **Then** the inspector opens automatically and identifies the node, tool, duration, reason, and recommended next action.
2. **Given** a failed run with diagnostic evidence, **When** the user expands technical details, **Then** the interface shows the error code, run identity, trace identity when available, and relevant evidence without exposing secrets.
3. **Given** successful upstream steps followed by a failed step, **When** the run is inspected, **Then** the successful steps remain visible and distinguishable from the failed and unstarted steps.
4. **Given** a run for which partial retry cannot be proven safe, **When** recovery actions are shown, **Then** the interface offers a full rerun and does not imply that an unsafe partial retry is available.
5. **Given** a healthy remote MCP call is in progress, **When** routine workspace health polling or lifecycle observation occurs, **Then** the call continues unless the user cancels it, its configured timeout expires, or its server generation is explicitly replaced; if it is cancelled, the retained diagnostic identifies which of those boundaries caused the cancellation.
6. **Given** any run reaches a failed terminal state, **When** the user opens Diagnosis, **Then** it contains a useful failure category, plain-language explanation, recovery guidance, and either the failed workflow box or an explicit statement that the failed box is unknown.

---

### User Story 3 - Inspect execution flow on the canvas (Priority: P2)

As a mechanical engineer debugging a visual workflow, I can correlate inspector steps with nodes on the workflow canvas so I can quickly understand where execution is occurring or failed.

**Why this priority**: A list of step names is less useful when users cannot connect it to the visual workflow they created.

**Independent Test**: Run a multi-node workflow, select steps in the inspector, and verify that the corresponding nodes are highlighted with accessible running, succeeded, failed, cancelled, or not-run states.

**Acceptance Scenarios**:

1. **Given** a running multi-node workflow, **When** execution advances, **Then** affected canvas nodes reflect their current execution states without relying on color alone.
2. **Given** an inspector step associated with a current canvas node, **When** the user selects the step, **Then** the matching node is brought into view and highlighted.
3. **Given** a historical run whose node was edited or removed, **When** the user selects that historical step, **Then** the inspector explains that the original node is no longer present instead of highlighting an unrelated node.
4. **Given** the workflow is already open in the editor, **When** the user activates the visible focus-workflow action, **Then** the current workflow canvas receives focus; passive status announcements remain non-interactive and are not presented as controls.
5. **Given** a workflow run with ordinary and MCP-backed boxes, **When** the user opens Steps, **Then** each observed Rivet box appears once in execution order with its human title, state, duration, and compact safe inputs and outputs; MCP call evidence is subordinate detail on the owning box rather than a duplicate step.

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
- A remote MCP operation is cancelled by its caller, by an explicit server-generation replacement, or by its transport while the workspace remains healthy.
- The workflow is already loaded and a user needs an explicit way to return focus to its canvas.
- Run-input or node-port evidence was not captured by an older product version.
- A node value is a typed null, excluded control flow, nested object, binary payload, image, audio, or vector.
- Evidence capture or projection fails after execution has started.
- A graph contains up to 100 observed boxes with a mixture of retained, redacted, truncated, and unavailable values.
- A generated workflow promises a document or file but contains no approved artifact-producing box.
- A value names a file path but no authoritative artifact reference exists.
- A workflow requests a native CAD or mesh format through a generic text-document capability.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The workspace MUST present a compact run summary containing state and elapsed or completed duration for the current or most recently selected run.
- **FR-002**: The workspace MUST provide a collapsible Run Inspector that does not permanently consume horizontal canvas space.
- **FR-002A**: The Run Inspector MUST present the sections in this order: Inputs, Outputs, Steps, Diagnosis, and History.
- **FR-003**: While a run is active, the Run Inspector MUST show elapsed time, the current step when known, and completed-step progress when known.
- **FR-003A**: The Inputs section MUST show the safe retained inputs supplied to the exact saved workflow revision used by the run, including a digest and completeness state for each value.
- **FR-004**: For a completed run, the Run Inspector MUST show all available named final outputs and clearly distinguish final outputs from intermediate step results.
- **FR-004A**: Authoritative artifact outputs MUST appear before ordinary final values and MUST show verified artifact identity and available actions. The inspector MUST NOT claim that a value is a file or artifact unless the run evidence contains an authoritative artifact reference.
- **FR-005**: Result presentation MUST support readable text, structured data, lists, links, and artifact references with appropriate view, copy, download, or open actions when those actions are available.
- **FR-006**: Large results MUST use a bounded initial rendering while retaining a clear way to inspect or export the complete available value.
- **FR-007**: The Run Inspector MUST show exactly one ordered row for each Rivet graph box observed in the run, with its human title, state, duration, and compact safe input and output projections when available.
- **FR-007A**: MCP child-call evidence MUST be merged into and presented as subordinate detail for its owning graph-box row and MUST NOT create a duplicate primary step.
- **FR-007B**: Primary step labels MUST prefer retained human-authored titles and meaningful operation names. UUIDs and other transport identities MAY appear only in technical details.
- **FR-008**: Selecting an execution step MUST highlight and bring the corresponding current canvas node into view; if the original node is absent, the interface MUST explain that condition.
- **FR-009**: Canvas execution states MUST communicate running, succeeded, failed, cancelled, and not-run conditions without relying on color alone.
- **FR-010**: On every terminal failure, the Run Inspector MUST open automatically and present a useful Diagnosis containing a stable failure category, plain-language summary, recommended recovery action, and the failing graph box when known; when it is not known, Diagnosis MUST say so explicitly.
- **FR-011**: Failure details MUST optionally expose the run identity, tool or operation identity, reason code, trace identity when available, and relevant diagnostic evidence.
- **FR-012**: A failed run MUST retain and display available successful upstream step results and distinguish them from failed or unstarted steps.
- **FR-013**: The interface MUST always allow an eligible workflow to be rerun from the start and MUST offer partial retry only when the system can determine that retrying from that point is safe.
- **FR-014**: Refreshing or reopening a workspace during an active run MUST reconnect to the existing run and MUST NOT create a duplicate run solely because the page reloaded.
- **FR-015**: The workspace MUST provide bounded recent-run history with revision, start time, final state, duration, and result or diagnostic availability.
- **FR-016**: Historical run inspection MUST identify the workflow revision used and distinguish it from the currently open revision.
- **FR-017**: Outputs, copies, exports, diagnostics, and error summaries MUST apply the product's redaction rules before information is shown or transferred.
- **FR-018**: If result data was truncated, omitted, expired, or unavailable, the interface MUST disclose that limitation and MUST NOT present partial data as complete.
- **FR-018A**: Run inputs, node inputs, node outputs, and final outputs MUST use bounded, recursive redaction before retention or presentation and MUST preserve type, digest, completeness, and one explicit evidence state: available, no-value, not-run, not-retained, redacted, truncated, expired, or unavailable.
- **FR-018B**: Binary bodies, raw base64, secret values, credentials, and authorization material MUST never be retained or presented by the inspector. Safe metadata such as media type, byte count, and digest MAY be retained when known.
- **FR-018C**: Evidence for not-run boxes MUST be based only on the immutable workflow revision executed by the run. The current edited canvas MUST NOT be used to invent historical membership or execution state.
- **FR-018D**: Failure to capture, retain, or project inspector evidence MUST NOT change a workflow run's execution state or turn an otherwise successful run into a failure; the inspector MUST instead disclose the unavailable evidence.
- **FR-018E**: Runs retained before this inspector contract MUST remain inspectable. Missing historical fields MUST be presented as not retained or unavailable rather than guessed from current data.
- **FR-019**: Run status, inspector controls, execution steps, outputs, and recovery actions MUST be keyboard operable and understandable with assistive technology.
- **FR-020**: The feature MUST preserve existing workflow Run, Run Options, Cancel, save-before-run, and lint behavior while improving their status and result presentation.
- **FR-021**: Automated UI coverage MUST include default, running, succeeded, failed, cancelled, refreshed, historical, empty-output, large-output, and redacted-output states.
- **FR-022**: A healthy in-flight MCP call MUST NOT be cancelled by routine status polling or observation; cancellation evidence MUST distinguish user cancellation, configured timeout, explicit server-generation replacement, and transport cancellation when the source is known.
- **FR-023**: The editor surface MUST provide a visible keyboard-operable action to focus the currently open workflow, while accessibility status announcements MUST remain passive and non-interactive.
- **FR-024**: Inputs, outputs, steps, diagnosis, and history MUST remain responsive and understandable for a run with at least 100 observed graph boxes without dropping, combining, or duplicating box rows.
- **FR-025**: When a generated workflow promises a document or file deliverable, the saved graph MUST contain an approved artifact-producing box before Graph Output, and a successful value-only response MUST NOT satisfy that deliverable.
- **FR-026**: A workspace text-document producer MUST be confined to approved relative workspace paths and text formats, require the applicable write approval, avoid overwrite by default, and return an authoritative artifact reference containing digest, media type, and byte count.
- **FR-027**: Native CAD documents, STL meshes, and other domain-native formats MUST be created and exported only through an approved domain capability; a generic workspace text-document producer MUST reject those formats.
- **FR-028**: Graph generation, save validation, and run validation MUST identify the requested deliverable effect and block a graph whose producing capability, artifact output, dependency path, or required approval is missing. Validation MUST name the intended deliverable and the corrective action.
- **FR-028A**: Graph Builder deliverable intent MUST come from an explicit host-owned user selection retained with the preview and exact workflow revision. Free-text heuristics, model omission, tool titles, and output path strings MUST NOT be treated as deliverable authority.

### Key Entities *(include if feature involves data)*

- **Workflow Run Summary**: The user-facing identity and lifecycle of one execution, including workflow, revision, state, timestamps, duration, progress, and availability of results or diagnostics.
- **Execution Step**: A node or operation observed during a run, including ordering, node association, tool or operation identity, state, duration, attempts, and available result or error evidence.
- **Run Input**: A named value supplied to the immutable workflow revision, retained only as a bounded and recursively redacted type-aware projection with digest and completeness state.
- **Graph Box Evidence**: The one-per-observed-box execution record containing immutable node identity, a human title, order, state, timing, compact safe input and output projections, and subordinate MCP child-call details when applicable.
- **Run Result**: A named final or intermediate value with type, display metadata, redaction state, completeness, and optional artifact or link actions.
- **Run Artifact**: An authoritative workspace-confined deliverable reference with stable identity, digest, media type, byte count, producer provenance, and authorized open or download behavior. A plain value or path string is not a Run Artifact.
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
- **SC-009**: A deterministic delayed-remote-MCP regression test completes successfully while routine status polling occurs, and each simulated cancellation boundary produces a distinct retained diagnostic.
- **SC-010**: For tested runs containing up to 100 graph boxes, the Steps section shows one row per observed box in the recorded order, with no duplicate MCP rows, and remains ready for interaction within one second of receiving the inspection data.
- **SC-011**: Every tested terminal failure presents a non-empty Diagnosis, including failures with no identifiable box, and every tested legacy run discloses missing evidence without borrowing data from the current workflow revision.
- **SC-012**: Automated evidence tests confirm that raw binary data, base64 bodies, secrets, credentials, and authorization material never appear in retained inputs, node-port values, outputs, copies, exports, or captured screens.
- **SC-013**: Every tested workflow that promises a file is rejected before execution when its approved artifact producer is absent, and every accepted file-producing workflow returns an authoritative digest-verified artifact reference.
- **SC-014**: Confinement, traversal, hidden-path, overwrite-conflict, media allowlist, authorization, and native-format tests prevent generic document production outside its approved workspace text boundary.

## Assumptions

- A bottom inspector is the preferred default because the Agent control pane already consumes horizontal space; users may collapse it whenever they need maximum canvas area.
- Existing run, history, evidence, artifact, and cancellation records remain the authoritative sources; this feature organizes and exposes them rather than creating a second execution system.
- The first release guarantees full rerun from the start. Partial retry appears only where existing execution evidence and operation semantics can prove it safe.
- Recent history is bounded according to existing retention and performance limits and remains local to the relevant workspace and workflow context.
- Existing output-size and evidence-retention limits remain in force, but the interface clearly discloses when they affect completeness.
- Existing runs may lack input, graph-box, or port-value projections; honest compatibility states are preferable to reconstructing evidence from a changed workflow.
- Rivet typed values remain the semantic source for type-aware projections, including explicit null and excluded-control-flow states, but the inspector retains only bounded safe representations.
- Rivet terminology in this specification names the saved workflow compatibility boundary; the user-facing experience uses mechanical-engineering language such as boxes, inputs, outputs, created artifacts, and recovery actions.
- Workspace text documents and native engineering files have different authority boundaries. The first may use a confined Wright-owned document capability; the latter require the appropriate reviewed engineering-domain capability.
- Graph Builder asks the user to classify each request as value-only, workspace document, native CAD, or STL before generation; it does not silently default file intent from the prompt.
- This feature does not redesign workflow authoring, MCP installation, or the Agent control pane.
