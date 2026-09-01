# Feature Specification: Canonical Workflow Recovery

**Feature Branch**: `codex/080-canonical-workflow-recovery`

**Created**: 2026-08-31

**Status**: Recovery design and product-approval slice

**Input**: User description: "Regroup Wright around one complete canonical workflow model and recover the intended canvas-first visual engineering experience before hardening or merging the current EPP-F02B UI."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Build a Mechanical Workflow Graphically (Priority: P1)

As a mechanical engineer, I can create a recognizable engineering workflow entirely on a canvas, using friendly blocks with readable typed inputs and outputs, without needing to see or understand a workflow language.

**Why this priority**: The canvas is the primary product experience. If engineers cannot recognize, compose, and inspect the workflow graphically, the underlying platform architecture does not yet deliver customer value.

**Independent Test**: Start from a new workflow, find blocks by engineering name, add and arrange them, attach an input file, connect compatible ports, configure a review gate and feedback path, delete and restore an edit, and verify that the completed workflow remains understandable without opening Code mode.

**Acceptance Scenarios**:

1. **Given** a new workflow, **When** an engineer searches for and adds engineering capabilities, **Then** each block has a friendly name, recognizable purpose, left-side inputs, right-side outputs, and separately discoverable implementation details.
2. **Given** two blocks with compatible typed ports, **When** the engineer connects their visible handles, **Then** the connection has a stable identity and the target used to connect is distinct from the control used to inspect an artifact.
3. **Given** an input port that accepts a file, **When** the engineer attaches, previews, or replaces a file, **Then** the block shows the attachment state and the inspector exposes its origin and intended use.
4. **Given** a composed workflow, **When** the engineer moves, configures, disconnects, deletes, undoes, or redoes an edit, **Then** unrelated workflow identities remain stable and the result is immediately visible.
5. **Given** a decision or approval point, **When** the engineer configures proceed and revise outcomes, **Then** the canvas distinguishes the gate and its feedback path from ordinary data flow without relying only on color.

---

### User Story 2 - Edit One Workflow in Diagram and Code (Priority: P1)

As an engineer who sometimes prefers precise text, I can switch among Diagram, Code, and Split views knowing they edit one authoritative workflow rather than two representations that can drift.

**Why this priority**: Lossless bidirectional editing is the central trust boundary for graphical, textual, and AI-assisted authoring.

**Independent Test**: Open the representative workflow in Split mode, make one graphical edit and observe the corresponding text update, make one valid text edit and observe the graph update, then make one invalid text edit and verify that the last-valid graph remains intact with a precise diagnostic and correction.

**Acceptance Scenarios**:

1. **Given** a valid workflow in Split mode, **When** an engineer changes a block or connection graphically, **Then** the textual form updates without losing any semantic fact or stable identity.
2. **Given** valid workflow text, **When** an engineer changes a supported semantic fact, **Then** the diagram and inspector update to the same new workflow revision while preserved layout remains keyed to stable identities.
3. **Given** invalid or incomplete text, **When** parsing or validation fails, **Then** the last-valid diagram remains authoritative, the invalid draft remains available for correction, and no save, run, or silent replacement occurs.
4. **Given** a selected block, port, connection, diagnostic, or source location, **When** the selection changes in one view, **Then** the corresponding concept is identified in every visible view.
5. **Given** comments or presentation formatting in the selected user-facing syntax, **When** a semantic round trip occurs, **Then** the documented preservation policy is applied predictably and no semantic information is lost.

---

### User Story 3 - Review an AI-Proposed Workflow Change (Priority: P2)

As an engineer, I can ask AI to create or modify a workflow and review its assumptions, warnings, semantic changes, and graphical preview before explicitly accepting or rejecting it.

**Why this priority**: AI assistance is useful only when it shares the same validation and revision boundary as manual editing and cannot bypass human authority.

**Independent Test**: Request a multi-block manufacturability change, inspect its assumptions and warnings, compare the semantic diff and preview, reject it once, request or reopen the proposal, accept it once, and verify that only the accepted candidate advances the workflow revision.

**Acceptance Scenarios**:

1. **Given** a current workflow revision, **When** AI proposes a change, **Then** the proposal identifies its base revision, assumptions, warnings, commands, affected concepts, and validation result.
2. **Given** a valid multi-block proposal, **When** the engineer previews it, **Then** the candidate appears graphically and textually without mutating the accepted workflow.
3. **Given** a proposal, **When** the engineer rejects it, **Then** the accepted workflow and its revision remain unchanged.
4. **Given** a proposal based on the current revision, **When** the engineer accepts it, **Then** the same atomic command and validation boundary used by manual edits advances the workflow once.
5. **Given** an invalid, stale, or unauthorized proposal, **When** it is reviewed, **Then** Wright blocks acceptance with a specific explanation and never executes or approves the workflow on the engineer's behalf.

---

### User Story 4 - Understand and Recover a Workflow Run (Priority: P2)

As an engineer running an accepted workflow, I can see what is active, inspect each block's inputs, outputs, activity, and diagnosis, recover from a needs-input or failed state, and open or download recognizable produced files.

**Why this priority**: A workflow editor becomes an engineering workspace only when execution is legible and produced artifacts remain connected to their lineage.

**Independent Test**: Simulate the representative workflow through queued, running, needs-input, resumed, succeeded, and failed paths; verify active block and connection cues; inspect an input and output; follow lineage; apply the offered recovery; and open or download the final artifact.

**Acceptance Scenarios**:

1. **Given** a run is progressing, **When** a block or connection is active, **Then** motion, text or iconography, and structure identify it without depending on color alone.
2. **Given** any executable block, **When** the engineer opens its inspector, **Then** Inputs, Outputs, Activity, and Diagnosis are available with useful summaries and progressive disclosure for technical evidence.
3. **Given** a queued, running, needs-input, succeeded, failed, blocked, or stale step, **When** the state changes, **Then** the canvas and inspector present the same immutable run facts without altering the workflow definition.
4. **Given** a needs-input or failed block, **When** the engineer asks what to do next, **Then** Wright explains the cause, affected input or binding, and bounded recovery action without requiring raw JSON or log reading.
5. **Given** a produced artifact, **When** the engineer inspects it, **Then** Wright shows its type, producing run and block, upstream lineage, preview availability, and safe open or download actions.

---

### User Story 5 - Trust Versioning, Authority, and Compatibility (Priority: P3)

As an engineer and product owner, I can distinguish workflow definition, layout, proposals, and run records; understand what is provisional; and review evidence before any broad production hardening begins.

**Why this priority**: Clear authority prevents renderer state, source text, runtime overlays, or AI proposals from silently becoming competing workflow definitions.

**Independent Test**: Compare semantic and layout digests, reopen an old supported revision, attempt an unknown-version open, replace the renderer with a contract fixture, inspect a historical run, and remove the recovery concept while verifying that frozen Checkpoint D evidence and existing released behavior remain intact.

**Acceptance Scenarios**:

1. **Given** a workflow definition and layout, **When** only layout changes, **Then** the semantic digest and revision facts remain unchanged while layout persists by stable identity.
2. **Given** a completed run, **When** the underlying workflow later changes, **Then** the historical run still identifies the immutable workflow revision and outputs it actually used.
3. **Given** an unsupported workflow version, **When** it is opened, **Then** Wright refuses unsafe rewriting, preserves the original bytes, and explains supported recovery or migration choices.
4. **Given** a replacement renderer, **When** it receives the same projection, **Then** semantics, text, validation, command application, and persisted identities do not change.
5. **Given** the recovery evidence, **When** the product owner reviews it, **Then** disposable concept code, retained production foundations, deferred production work, and the approval boundary are unmistakable.

### Edge Cases

- A port is missing, duplicated, on the wrong side, has incompatible type or cardinality, or is connected to the wrong direction.
- An artifact-inspection control is mistaken for a connection handle, or a connection gesture lands on inspection UI.
- A delete would leave a gate, condition, feedback path, binding, artifact contract, or component reference dangling.
- A text edit is syntactically incomplete while the engineer continues typing, or is syntactically valid but semantically invalid.
- A source span no longer exists after formatting, while a diagnostic still refers to the same semantic identity.
- A graphical move, selection change, viewport change, or run overlay accidentally changes the semantic digest.
- An AI proposal is valid but based on an old revision, contains a command outside the allowed set, or would require authority the user does not have.
- A manual edit and an AI proposal target the same base revision; only one may advance the accepted state.
- An input file is missing, replaced with an incompatible type, too large to preview, or no longer available when a historical run is inspected.
- A run pauses for input, fails before producing output, succeeds with a partially previewable artifact, or becomes stale after losing its live event source.
- A reusable component is collapsed while a diagnostic or active run step targets a concept inside it.
- A large graph exceeds the demonstrated concept scale; navigation remains usable and the product makes no unsupported production-scale claim.
- An unknown workflow, layout, command, or run-record version is encountered; original data remains intact and unsupported facts are never silently dropped.
- The renderer fails to load; Code and structured inspection remain available and no semantic mutation is attempted.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: One versioned, typed canonical workflow model MUST be the sole semantic authority for graphical, textual, form-based, and AI-assisted authoring.
- **FR-002**: Renderer-native graph state and textual source MUST NOT become independent semantic authorities.
- **FR-003**: The model MUST represent stable workflow, revision, phase, block, port, connection, gate, decision, feedback-path, reusable-component, binding, and intended-artifact identities.
- **FR-004**: Blocks MUST declare typed input and output ports with name, direction, type, requiredness, and cardinality.
- **FR-005**: The model MUST distinguish data, control, decision, and feedback relationships and preserve their conditions, instructions, and configuration.
- **FR-006**: Exact implementation and tool bindings, including argument and result mappings, MUST be representable but revealed through progressive disclosure.
- **FR-007**: The model MUST distinguish deterministic blocks from AI-capable blocks and define the additional review authority required for AI-proposed changes.
- **FR-008**: Reusable components and collapsed graphs MUST preserve addressable internal identities, relationships, diagnostics, and run lineage.
- **FR-009**: Layout MUST be separately persisted presentation metadata keyed by stable semantic identities.
- **FR-010**: Run, step, activity, input, output, and artifact records MUST be immutable records separate from workflow definitions and layout.
- **FR-011**: Workflow, layout, textual form, commands, and run records MUST be versioned with explicit migration and unknown-version behavior.
- **FR-012**: An engineer MUST be able to complete the primary authoring journey entirely graphically.
- **FR-013**: The canvas MUST be block/flow-first; phase lanes MAY group work but MUST NOT dominate navigation or readability.
- **FR-014**: Blocks and connections MUST be readable, with visible left input and right output handles and a separate artifact-inspection target.
- **FR-015**: The capability palette MUST be searchable by friendly engineering names while retaining exact implementation identities behind progressive disclosure.
- **FR-016**: Manual add, move, connect, disconnect, configure, delete, undo, and redo MUST use one atomic, validated command system.
- **FR-017**: File inputs MUST support attachment, preview where safe, replacement, type guidance, and origin inspection.
- **FR-018**: Outputs MUST support inspection, lineage, preview where safe, opening, and downloading according to existing authorization boundaries.
- **FR-019**: Diagram, Code, and Split modes MUST project and edit the same model without semantic loss.
- **FR-020**: Selection MUST synchronize among source locations, blocks, ports, connections, inspector sections, and diagnostics.
- **FR-021**: A valid graphical edit MUST update the textual form, and a valid textual edit MUST update the diagram.
- **FR-022**: Invalid text, graph, form, or AI candidates MUST NOT replace the last-valid accepted state.
- **FR-023**: Diagnostics MUST provide a stable code, semantic identities, source spans when applicable, explanation, and bounded correction.
- **FR-024**: Parsing, formatting, validation, command application, semantic diff, and canvas projection MUST have one documented conformance boundary.
- **FR-025**: Text formatting policy MUST state how comments, user formatting, canonical formatting, and source maps are preserved or intentionally normalized.
- **FR-026**: JSON, YAML, and a purpose-built workflow language MUST be evaluated against identical workflows and edit tasks before a permanent user-facing syntax is selected.
- **FR-027**: AI proposals MUST use the same base-revision command protocol as manual editing and MUST expose assumptions, warnings, semantic diff, and graphical preview.
- **FR-028**: AI MUST NOT directly mutate, execute, approve, or accept a workflow.
- **FR-029**: Execution visualization MUST identify active blocks and connections with non-color-only cues.
- **FR-030**: Queued, running, needs-input, succeeded, failed, blocked, and stale states MUST be distinguishable and consistent across canvas and inspector.
- **FR-031**: Every executable block MUST expose Inputs, Outputs, Activity, and Diagnosis.
- **FR-032**: Recovery guidance MUST identify the affected concept and safe next action without requiring engineers to read raw JSON or logs.
- **FR-033**: The recovery concept MUST demonstrate one coherent mechanical-engineering workflow from attached input through recognizable downloadable output.
- **FR-034**: The renderer adapter MUST remain replaceable and the renderer decision MUST be justified by direct-manipulation, handle, overlay, keyboard, and scale evidence.
- **FR-035**: Automated invariants MUST prove semantic round trips, command atomicity, last-valid containment, layout independence, proposal revision safety, and run-definition separation.
- **FR-036**: The capability inventory MUST trace every previously defined capability to user task, model, text, canvas, manipulation, inspector, run overlay, test, evidence, and disposition with no silent omission.
- **FR-037**: Frozen Checkpoint D at `b4a7e996` and prototype evidence at `e7bb75c1` MUST remain immutable reference subjects and MUST be labeled with known evidence limitations.
- **FR-038**: The progress dashboard MUST show this recovery goal, phase, active work, blockers, decisions, artifacts, screenshots, task/checkpoint trends, and separate feature-slice completion from customer readiness.
- **FR-039**: Product and visual parity MUST be reviewed before accessibility, packaging, release-candidate hardening, broad implementation, merge, or release work resumes.
- **FR-040**: This slice MUST preserve the existing canonical draft model, validation, immutable revisions, compare-and-set persistence, closed API, browser decoding, and renderer-neutral seams unless evidence records a superseding decision.
- **FR-041**: Raw and annotated screenshots, browser diagnostics, a human-repeatable walkthrough, and a clickable report MUST be produced for the complete concept.
- **FR-042**: Disposable recovery code and production foundations MUST be explicitly labeled; completion MUST stop at one product-approval checkpoint.

### Key Entities

- **Canonical Workflow Definition**: The versioned semantic authority containing stable engineering workflow concepts, contracts, conditions, configuration, and implementation bindings.
- **Workflow Revision**: An immutable accepted definition revision with parent/base identity and semantic digest.
- **Layout Document**: Versioned presentation metadata keyed by semantic identities and excluded from the semantic digest.
- **Block**: A unit of engineering work with friendly purpose, deterministic or AI-capable behavior, typed ports, configuration, and optional exact binding.
- **Typed Port**: A stable input or output contract with name, type, requiredness, and cardinality.
- **Relationship**: A stable data, control, decision, or feedback edge between valid endpoints.
- **Artifact Contract**: The intended type, identity, and lineage expectations for an input or output, distinct from an actual produced file.
- **Binding**: The exact implementation, tool, or service mapping plus argument and result transformations used by an executable block.
- **Reusable Component**: A versioned subgraph that can be expanded or collapsed without losing internal addressability.
- **Workflow Command**: A bounded atomic change against an explicit base revision.
- **Candidate**: A validated or invalid unapplied result of text, graph, form, or AI commands; it never silently becomes accepted state.
- **Semantic Diff**: A stable-identity-aware explanation of added, removed, and changed semantic facts.
- **Diagnostic**: A coded issue tied to semantic identities and optional source spans, with explanation and correction.
- **AI Proposal**: A reviewable candidate containing assumptions, warnings, commands, diff, preview, and base revision.
- **Run Record**: An immutable execution instance bound to an exact workflow revision.
- **Step and Activity Record**: Immutable block-level progress and evidence within a run.
- **Artifact Record**: An actual input or produced file with type, lineage, authorization, and preview/open/download metadata.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A product owner can review manual composition, bidirectional text correspondence, AI proposal review, execution visualization, diagnosis, and output delivery in one continuous walkthrough without consulting implementation code.
- **SC-002**: The capability inventory accounts for 100% of capabilities found in the approved requirements and frozen prototype lessons; every row has an explicit retain, revise, defer, or reject disposition and justification.
- **SC-003**: Automated conformance tests pass 100% for `parse(format(IR))`, text-to-diagram preservation, graph-to-text-to-parse preservation, invalid-candidate containment, base-revision proposal safety, layout-digest independence, and run-definition separation.
- **SC-004**: One graphical edit updates text and one valid text edit updates the graph in under one second in the local concept; one invalid text edit leaves the prior graph unchanged and presents a stable diagnostic.
- **SC-005**: The three syntax alternatives use the same golden workflow and at least five identical edit/error tasks, with recorded readability, validity, review, parsing, source-map, preservation, and migration evidence; any provisional choice lists its unresolved risks.
- **SC-006**: The block/port laboratory compares three treatments and the selected treatment receives no unresolved ambiguity between connection handles and artifact-inspection controls in the final walkthrough.
- **SC-007**: The final concept visibly demonstrates add, move, connect, disconnect, configure, delete, undo, redo, file attachment, input/output inspection, all three view modes, selection sync, and a reviewable AI multi-block proposal.
- **SC-008**: The simulated run visibly demonstrates active block and connection cues plus queued, running, needs-input or failed, recovered, and succeeded states using at least one non-color cue each.
- **SC-009**: The successful run exposes one recognizable output with lineage and working open or download behavior; the recovery case explains a bounded correction without raw JSON or log reading.
- **SC-010**: Raw and annotated screenshots exist for every material walkthrough state, the report is clickable and human-repeatable, validation reports zero missing evidence fields, and browser diagnostics distinguish product defects from environment limitations.
- **SC-011**: Changing only layout produces zero semantic-digest change, and changing run state produces zero workflow-definition byte change across all automated fixtures.
- **SC-012**: The dashboard is reachable, names canonical workflow recovery as active, orders checkpoint history newest-to-oldest deterministically, and clearly shows that product approval is pending while overall customer readiness remains incomplete.
- **SC-013**: Revised specification, plan, roadmap, parity, and task artifacts place product/visual approval before accessibility, packaging, candidate hardening, push, merge, or release work.
- **SC-014**: No broad production implementation, merge, release, package publication, or external customer action occurs before explicit product approval.

## Assumptions

- The recovery slice may use disposable concept code to prove interaction and conformance, provided production foundations and provisional choices are labeled clearly.
- The four-block EPP-F02B draft implementation remains useful as a backend and contract foundation, but its current custom canvas is not the accepted product shell.
- The frozen 076 prototype is evidence, not a complete or usability-validated product and not an implementation dependency.
- One mechanical-engineering workflow centered on a mounting-bracket design is sufficient for the integrated recovery demonstration; production domain breadth remains future work.
- Internal canonical JSON may remain the persisted interchange representation even if a different user-facing text syntax is provisionally preferred.
- The local Windows machine is authoritative for interactive evidence; GB10 availability is useful for bounded read-only and parallel tests but is not a completion dependency.
- Existing authentication, authorization, artifact access, immutable revision, and local/offline boundaries continue to apply.

## Explicitly Out of Scope

- Broad production implementation of the recovered architecture beyond the focused conformance and interaction slice.
- Permanent approval of a user-facing workflow syntax without the recorded evaluation and product-owner review.
- Production migration of existing drafts or released definitions to canonical IR vNext.
- Production-scale performance claims beyond the documented large-graph concept evidence.
- Accessibility, packaging, release-candidate, push, merge, publication, or release hardening before the product-approval checkpoint.
- Automatic AI mutation, execution, approval, or acceptance of workflows.
- Treating renderer-native state, source text, layout, proposals, or runs as independent semantic authorities.
