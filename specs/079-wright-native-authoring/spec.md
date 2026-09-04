# Feature Specification: Wright-native Workflow Authoring

**Feature Branch**: `codex/079-wright-native-authoring`

**Created**: 2026-09-02

**Status**: Proposed; specification and architecture review only. No implementation approval.

**Input**: Replace Rivet with Wright's new engineering-process software, using the approved graph-first design: remove the permanent Inputs panel, provide a compact Create rail, and make multiple inputs and outputs understandable. The user authorized the corrected ADR/spec after the mistaken Rivet implementation was quarantined.

## User Scenarios & Testing _(mandatory)_

### User Story 1 - Understand the Process Without Competing Panels (Priority: P1)

An engineer opens a Wright process and immediately sees its flow, required inputs, and selected step. The graph is the primary workspace; input values are configured once on their source steps, not duplicated in a permanent side panel.

**Why this priority**: The approved redesign's purpose is comprehension, not a cosmetic reskin of the legacy editor.

**Independent Test**: Open the mounting-bracket example, find its three source steps, inspect one step, and trace two named outputs to their consumers without reading raw source.

**Acceptance Scenarios**:

1. **Given** an open process, **When** nothing is selected, **Then** the graph receives the main working area and the Inspector does not reserve an empty full-width panel.
2. **Given** three configured source steps, **When** the engineer uses the compact Inputs summary, **Then** it navigates to those steps without introducing a second value editor.
3. **Given** a selected step, **When** the engineer opens its Inspector, **Then** its purpose, settings, exact inputs, outputs, and connections are available on demand.
4. **Given** the process is a definition rather than a run, **When** any status is displayed, **Then** it distinguishes saved, structurally valid, input configured, unbound, and not executed.

### User Story 2 - Create and Edit Basic Process Objects (Priority: P1)

An engineer adds a few common objects from a compact rail, configures them through understandable fields, and corrects mistakes without losing work.

**Why this priority**: Manual control should be useful without requiring a universal node catalog or an LLM.

**Independent Test**: Create three distinct input steps and two document-producing steps, configure them, rename and move them, delete one, undo and redo, then save and reopen the document.

**Acceptance Scenarios**:

1. **Given** the Create rail, **When** the engineer chooses Input, LLM document, MCP tools, 3D check, Drawing, FDM, or More, **Then** a small named chooser opens; no permanent catalog occupies the graph.
2. **Given** a template choice, **When** Add is activated, **Then** one independently identified object is placed without overlapping existing objects, selected for configuration, and added as one undoable operation.
3. **Given** tool/checker or LLM-document templates, **When** they are added, **Then** they are visibly unbound draft steps; neither a tool nor a model is called. Application names are discovery hints, never proof of availability or an execution binding.
4. **Given** an invalid field edit, **When** it is submitted, **Then** the invalid field text and correction guidance remain visible while the last valid document and saved copy remain unchanged.
5. **Given** a referenced object, **When** deletion would remove connections or feedback, **Then** the complete impact is reviewed before one atomic deletion; cancel leaves everything unchanged.

### User Story 3 - Connect the Exact Input and Output (Priority: P1)

An engineer can distinguish a block's multiple interfaces and knows exactly what feeds each input and which consumers use each output.

**Why this priority**: A shared anonymous connector would reproduce the ambiguity identified in the approved image.

**Independent Test**: Use an example with duplicate display names, three inputs, four outputs, a collection, fan-out, a gate, and a feedback path. Connect, rename, reorder, and inspect them without changing endpoint identity accidentally.

**Acceptance Scenarios**:

1. **Given** a block with multiple ports, **When** it is inspected or connected, **Then** each input and output has its own stable named endpoint; edges do not terminate at a shared catch-all anchor.
2. **Given** an output used by two consumers, **When** the engineer follows it, **Then** both exact destination input ports are identifiable.
3. **Given** a collection port, **When** it is connected, **Then** the collection remains one typed interface, not a variable number of anonymous sockets.
4. **Given** incompatible directions, types, or cardinalities, **When** a connection is attempted, **Then** it is rejected with a reason and no partial graph mutation.
5. **Given** renamed ports or moved blocks, **When** connections are re-inspected, **Then** their identities and meanings remain unchanged. Reordering process steps is a separate validated action, not a side effect of dragging.

### User Story 4 - Save Safely and Work Accessibly (Priority: P1)

An engineer can preserve authored work, recover from conflicts and failures, and perform essential operations without dragging or relying on color.

**Why this priority**: The first persisted native editor must protect user work; it cannot inherit the read-only view's deletion-only rollback assumption.

**Independent Test**: Open the same document in two sessions, save conflicting changes, interrupt a save, reopen, disable the feature, and inspect retained documents. Repeat the essential authoring journey with keyboard-only and click-only input at narrow/zoomed sizes.

**Acceptance Scenarios**:

1. **Given** a valid unsaved document, **When** Save succeeds and the document is reopened, **Then** semantic identities, connections, authored inputs, and layout match the saved state.
2. **Given** a newer stored revision, **When** an older session saves, **Then** it cannot overwrite the newer document; its working copy remains available to save as a new document or discard explicitly before reload.
3. **Given** a failed or interrupted save, **When** the document is reopened, **Then** the reader returns either the old complete document or the new complete document, never a partial mixture.
4. **Given** the authoring feature is disabled or a previous Wright build is used, **When** unsupported authored data is encountered, **Then** it is retained without rewriting and a supported recovery path is explained.
5. **Given** keyboard-only, click-only, forced-color, reduced-motion, 320 CSS-pixel, or 200% zoom usage, **When** essential actions are performed, **Then** controls and complete process information remain reachable and focus remains predictable.

### Edge Cases

- Empty process, no selection, incomplete required input, and an unbound tool or document-generation step.
- Duplicate labels with different identities; many connected ports; optional ports hidden by disclosure; one output consumed by several blocks.
- Type/cardinality changes on connected ports; deletion of referenced objects; invalid gate/feedback pairs; forward-data cycles.
- Save conflict, disk full, lost response after a successful save, interrupted replacement, and reopening unsupported schema versions.
- Feature removal, workspace deletion, and attempts to address documents outside the authorized workspace.
- Dense graph at fit-to-screen scale: fit view must not be claimed as readable; focus and complete text views remain available.

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: The new authoring experience MUST be Wright-owned and independent of Rivet's editor, project format, iframe bridge, and runtime. The new path MUST NOT silently route through the legacy editor.
- **FR-002**: Diagram, readable text, Inspector, and source disclosure MUST describe one validated definition with stable semantic identities; a rendering library MUST NOT define the persisted process.
- **FR-003**: The graph MUST be primary, with compact document actions, an on-demand Inspector, and an Inputs summary that navigates to the only source-value editors.
- **FR-004**: Create MUST expose at most seven top-level groups: Input, LLM document, MCP tools, 3D check, Drawing, FDM, and More. Click and keyboard creation MUST be available without dragging.
- **FR-005**: Initial creation MUST support text and existing workspace-file-reference inputs, document-step templates, generic unbound tool/checker steps, phases, gates, feedback, and expected-artifact declarations. No new file upload or external discovery is required.
- **FR-006**: Every new object MUST receive a distinct identity and a non-overlapping initial position. Renaming, moving, or reordering a displayed port MUST NOT change its identity.
- **FR-007**: Ports MUST expose direction, name, type, requiredness, and single/collection cardinality. A connection MUST resolve exact source and destination port identities; connected and missing-required ports MUST retain distinct visible anchors. Optional unconnected ports may use named disclosure, never a shared connection endpoint. Connection and inspection actions MUST be separate controls.
- **FR-008**: Data/artifact flow and gate/feedback relationships MUST be distinguishable by labels or shape/pattern as well as color. No line style may imply runtime behavior that has not been defined.
- **FR-009**: Each input MUST accept at most one producer; output fan-out is allowed. Combining values requires an explicit collection-building step rather than implicit merging.
- **FR-010**: Step, port, connection, gate, feedback, and artifact edits MUST be atomic and validated together. Incomplete configuration may be a saved draft, but broken references or incompatible connections MUST NOT enter the valid document.
- **FR-011**: One user action MUST be one undo/redo unit, including a completed drag or confirmed cascading deletion. Saving MUST NOT erase session undo history; undo MUST NOT rewind persisted revision identifiers.
- **FR-012**: Save/reopen MUST preserve authored semantics and layout, reject stale writers, preserve invalid field text and unsaved working copies on failure, and never silently overwrite another session.
- **FR-013**: Source MUST initially be inspectable and read-only. Editable text syntax, LLM proposals, and their Apply/acceptance workflow are excluded from this increment.
- **FR-014**: Input configuration, structural validation, tool binding, execution, and engineering correctness MUST have separate visible states. A draft MUST NOT display fabricated run progress, outputs, successful checks, or service availability.
- **FR-015**: Essential interactions MUST support keyboard and non-drag pointer alternatives, visible focus, non-color cues, narrow/zoomed layouts, and reduced motion. The complete readable process view MUST remain available independently of the canvas.
- **FR-016**: Authored documents MUST remain workspace-confined, locally usable without network access, bounded in size, and free of credentials and host execution configuration. Existing input-file references MUST be reauthorized within the workspace before access.
- **FR-017**: Existing packaged process definitions, their read-only route, and pre-existing legacy workflows MUST remain unchanged. No automatic migration, legacy overwrite, or legacy feature enhancement is included.
- **FR-018**: Disabling/removing authoring MUST preserve user-authored documents. Unsupported readers MUST reject without rewrite; no lossy downgrade or in-place migration is allowed.
- **FR-019**: The first increment MUST NOT execute a process, call an MCP tool or LLM, install dependencies at runtime, publish/share documents externally, or claim benchmark/engineering qualification.
- **FR-020**: Planning, design images, passing document checks, or the quarantined 081 tests MUST NOT be represented as implementation, usability, release, or program-gate evidence for this feature.

### Key Entities

- **Authored Process**: A versioned, workspace-owned definition with independently identified phases, steps, ports, gates, feedback, and expected artifacts.
- **Input Configuration**: User-authored text or a permitted existing workspace-file reference; distinct from a port contract and from a runtime-produced value.
- **Port / Connection**: A stable typed interface / an exact directed relationship between two compatible interfaces.
- **Draft Step**: A definition of intended work, including an unbound tool or document-generation intention; not executable authority.
- **Presentation State**: Block positions and disclosure preferences; distinct from semantic order and relationships.
- **Working Copy / Saved Revision**: The currently valid editable document / the last atomically persisted document and its concurrency identity.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: In the preregistered study, at least four of five independent engineers correctly trace every requested producer/consumer endpoint, distinguish collection from single value, and distinguish configured inputs from completed work.
- **SC-002**: At least four of five participants add three inputs and two draft document steps, configure and connect them, undo a mistake, save, and reopen within eight minutes without facilitator instruction or lost work.
- **SC-003**: All tested rename, move, reorder, save/reopen, and undo/redo cases preserve exact endpoint identities; every incompatible connection and structurally invalid edit is rejected without partial mutation.
- **SC-004**: Every tested stale-writer, lost-response, interrupted-save, and unsupported-version case preserves the last complete stored document and offers an explicit recovery choice.
- **SC-005**: The essential journey is operable by keyboard and by pointer without dragging at 320 CSS pixels and 200% zoom; automated accessibility checks find zero serious/critical issues, with separate manual focus/contrast/non-color review.
- **SC-006**: With the new editor enabled, disabled, and removed from navigation, all selected legacy and packaged-read-only regression cases remain unchanged; no new authoring action loads or calls Rivet.
- **SC-007**: On the declared reference machine, opening the 25-step example completes within two seconds in at least 19 of 20 warm observations. A 100-step fixture is a stress check, not a claim that its fit view is readable.

## Assumptions

- The approved [object-palette mockup](../../artifacts/ui-redesign/wright-workflow-editor-object-palette-v2.png) is the layout target, not proof of available execution or literal text/status to copy.
- This is a proposed manual-authoring precursor to EPP-F06. Advancing it ahead of the existing dependencies requires an explicit roadmap amendment; no program status changes in this planning turn.
- The recommendation is structured manual editing first, read-only source, and separately versioned authored documents. These are proposed choices in [the ADR](proposed-adr.md), not accepted decisions.
- Actual exact MCP binding, LLM authoring, runtime execution, legacy migration, reusable subworkflows, and final Rivet retirement are subsequent governed increments. The target architecture replaces Rivet; this first slice does not claim the entire replacement is complete.
- A deterministic starter example and existing workspace files are sufficient; no paid model calls, proprietary tool installs, new benchmark collection, or external writes are needed.
