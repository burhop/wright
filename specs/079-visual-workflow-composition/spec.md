# Feature Specification: Visual Workflow Composition Foundation

**Feature Branch**: `codex/079-visual-workflow-composition`

**Created**: 2026-08-31

**Status**: Planning; implementation approval pending

**Input**: User description: "Deliver EPP-F02B as a bounded first-party visual workflow composition foundation: an engineer creates a four-block engineering workflow, connects and validates it, corrects an invalid edit, saves and reopens the draft, and inspects matching semantic identities in text and diagram without Rivet or execution."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Compose and Reopen a Four-Block Workflow (Priority: P1)

As an engineer starting from an empty draft, I can add four engineering-work blocks, arrange them into phases, connect their typed ports, declare a gate, feedback path, and intended artifacts, save the draft, close it, and reopen the same composition without losing its semantic identities or layout.

**Why this priority**: This is the smallest complete customer journey that proves Wright can author an inspectable engineering workflow instead of only displaying a released definition.

**Independent Test**: Start an empty draft; create Capture requirements, Define product, Review product definition, and Release product definition; connect them; add the approval gate and revision feedback path; save, close, and reopen; then verify the four blocks, their layout, and every stable identity are unchanged.

**Acceptance Scenarios**:

1. **Given** an empty draft, **When** an engineer creates and arranges the representative four-block workflow, **Then** the canvas distinctly presents phases, blocks, typed input/output ports, gates, feedback paths, and intended artifacts.
2. **Given** a connected valid draft, **When** the engineer saves, closes, and reopens it, **Then** every semantic identity, relationship, declared concept, and saved layout is preserved.
3. **Given** the reopened draft, **When** the engineer compares its text and diagram views, **Then** both expose the same complete set of stable semantic identities and relationships.

---

### User Story 2 - Edit Safely with Understandable Validation (Priority: P2)

As an engineer refining a workflow, I can select, move, connect, edit, and delete blocks and relationships, and I receive specific guidance when an edit would make the draft invalid.

**Why this priority**: A visual authoring surface is trustworthy only when routine changes are direct and invalid relationships fail visibly without corrupting the last valid draft.

**Independent Test**: On the representative draft, move a block, add and remove a valid connection, attempt an incompatible port connection and a dangling deletion, observe the diagnostic, correct the edit, and confirm the valid draft remains usable.

**Acceptance Scenarios**:

1. **Given** a workflow block, **When** the engineer selects, moves, or edits it, **Then** the canvas and inspection surface identify the same block and reflect the change without changing unrelated identities.
2. **Given** compatible typed ports, **When** the engineer connects them, **Then** the new relationship is shown in both the canvas and engineer-readable text.
3. **Given** an incompatible, duplicate, dangling, or otherwise invalid edit, **When** the engineer attempts it, **Then** Wright rejects or isolates the invalid change, identifies the affected concepts, explains why it is invalid, and provides a bounded correction direction.
4. **Given** a displayed validation failure, **When** the engineer corrects the named cause, **Then** the diagnostic clears and the corrected draft can be saved.

---

### User Story 3 - Distinguish Draft Authoring from Released Definition (Priority: P3)

As an engineer, I can tell that I am editing a versioned working draft, not silently changing the released EPP-F02 definition, and I can inspect the draft with keyboard-accessible primary actions on desktop or a readable narrow layout.

**Why this priority**: Clear authority, accessibility, and compatibility boundaries prevent a promising canvas from creating accidental release, migration, or lock-in behavior.

**Independent Test**: Open the released definition and a draft, verify only the draft has authoring actions, complete the primary draft journey by keyboard, inspect it at narrow width, and remove or disable the authoring surface without changing the released definition.

**Acceptance Scenarios**:

1. **Given** a released definition, **When** the engineer opens it while draft authoring is available, **Then** it remains read-only and unchanged unless an explicitly separate future release action is authorized.
2. **Given** a working draft, **When** the engineer uses keyboard-only primary actions, **Then** create, select, edit, connect, delete, validate, save, close, reopen, and inspection controls remain operable with visible focus and non-color cues.
3. **Given** a narrow viewport, **When** the draft is inspected, **Then** its text, properties, diagnostics, and relationship information remain reachable even if full canvas authoring is explicitly desktop-oriented.
4. **Given** the authoring feature is disabled or removed, **When** existing Wright and released-definition journeys run, **Then** they behave as before and no released data requires migration or cleanup.

### Edge Cases

- A connection joins an output to an output, uses incompatible value types, duplicates an existing relationship, or targets a missing port.
- Deleting a block would leave gates, feedback paths, artifacts, or connections dangling.
- Two blocks, ports, gates, paths, or artifacts are given the same semantic identity.
- A saved draft is reopened after the supported draft contract has advanced, is missing, is malformed, or contains a content-identity mismatch.
- A save is interrupted or rejected; the prior valid saved revision remains reopenable and is not silently replaced.
- A workflow is larger than the representative four-block journey; navigation and inspection remain understandable without claiming unlimited canvas scale.
- Canvas layout is dense at 200% zoom or a narrow viewport; the complete engineer-readable projection remains available.
- The renderer is unavailable; the draft remains inspectable through its canonical text/properties projection with an honest diagnostic.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Wright MUST provide a first-party workflow composition surface that does not embed, extend, or require Rivet.
- **FR-002**: An engineer MUST be able to create, select, move, connect, edit, and delete workflow blocks and their declared relationships within a working draft.
- **FR-003**: The composition experience MUST present phases, blocks, typed input/output ports, gates, feedback paths, and intended artifacts as distinct, named concepts.
- **FR-004**: Every authorable concept MUST have a stable semantic identity that is independent of its visual position and remains stable across supported edits and save/reopen.
- **FR-005**: Wright MUST validate draft structure, identity uniqueness, references, port direction and type compatibility, gates, feedback paths, and artifact relationships before a draft is accepted as valid.
- **FR-006**: Invalid edits MUST produce understandable, non-sensitive diagnostics that identify the affected concepts, explain the violated rule, and provide a bounded correction direction without corrupting the last valid saved revision.
- **FR-007**: Wright MUST save a versioned working draft and reopen the same semantic content and saved layout after the draft is closed.
- **FR-008**: Save behavior MUST preserve the prior valid revision when a replacement fails or is interrupted, and MUST expose which revision is current.
- **FR-009**: The draft MUST have an engineer-readable text projection derived from the same canonical semantic model as the canvas, with exactly matching semantic identities and relationships.
- **FR-010**: The released EPP-F02 definition MUST remain read-only; creating or editing a draft MUST NOT silently mutate, replace, migrate, or claim release of that definition.
- **FR-011**: Primary authoring and recovery actions MUST be keyboard accessible, expose visible focus and stable test identities, and communicate status without relying on color alone.
- **FR-012**: Desktop authoring MUST support the representative journey without document-level overflow; narrow layouts MUST preserve complete inspection and diagnostics even when authoring is intentionally limited.
- **FR-013**: Renderer-specific behavior MUST remain replaceable without changing the canonical draft semantics, persistence identity, validation rules, or engineer-readable projection.
- **FR-014**: The feature MUST be additive, feature-bounded, independently shippable, and removable without migrating or cleaning up released-definition data.
- **FR-015**: EPP-F02B MUST NOT execute workflows, invoke MCP, invoke an LLM, author with AI, populate or qualify benchmarks, or migrate a working draft into production/released status.
- **FR-016**: Material deviations from the approved visual north star MUST be recorded as retained, revised, rejected, or deferred decisions with a reason before they are treated as accepted behavior.
- **FR-017**: Automated and human-repeatable acceptance MUST cover the empty-to-four-block journey, valid and invalid edit recovery, save/close/reopen, text/canvas identity equivalence, keyboard use, narrow inspection, feature removal, and released-definition non-interference.
- **FR-018**: Each implementation checkpoint MUST produce visible or runnable evidence at least every second increment, with raw and annotated screenshots, browser diagnostics, and a repeatable report.
- **FR-019**: The authoring draft contract, validation/apply boundary, compatibility behavior, and rollback behavior MUST be explicitly documented as bounded decisions; provisional choices MUST NOT be represented as permanent platform commitments.
- **FR-020**: EPP-F02B MUST provide no governed benchmark evidence and MUST leave benchmark qualification exactly `0/100` unless a separately authorized benchmark run produces accepted evidence.

### Key Entities

- **Working Draft**: A versioned, editable workflow composition with a stable draft identity, revision, semantic content identity, saved layout, and lifecycle distinct from any released definition.
- **Workflow Block**: A bounded unit of engineering work with a stable identity, phase membership, declared typed ports, and intended artifacts.
- **Phase**: An ordered grouping of workflow blocks that communicates a customer-readable stage of work.
- **Typed Port**: A stable input or output identity whose direction and value type constrain valid connections.
- **Connection**: A directed relationship between compatible typed ports.
- **Gate**: A named acceptance condition associated with a workflow decision and its pass/fail targets.
- **Feedback Path**: A directed, explained return from a decision or block to an earlier semantic target.
- **Intended Artifact**: A declared expected result and producing block; it is not evidence that an artifact exists.
- **Saved Layout**: Replaceable presentation state associated with stable semantic identities, not part of execution or release authority.
- **Validation Diagnostic**: A stable reason, affected identities, explanation, and correction direction for an invalid draft or edit.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A representative engineer can create, connect, validate, save, close, reopen, and inspect the required four-block workflow in 10 minutes or less without facilitator intervention.
- **SC-002**: Save/reopen acceptance proves 100% equality of semantic identities and relationships and preservation of all four saved block positions within the documented layout tolerance.
- **SC-003**: Automated acceptance proves 100% equality between canonical draft, text projection, and canvas semantic identity sets for the representative journey.
- **SC-004**: Every incompatible, duplicate, dangling, and identity-conflict fixture produces the expected stable diagnostic, and every documented recovery yields a valid save without loss of the prior valid revision.
- **SC-005**: The complete primary journey passes keyboard-only use with visible focus, no inaccessible primary action, and zero serious or critical automated accessibility findings.
- **SC-006**: At 200% zoom and a 390 CSS-pixel viewport, complete draft inspection and diagnostics remain reachable with no document-level horizontal overflow; desktop canvas authoring limitations are stated honestly.
- **SC-007**: Disabling or removing the authoring feature leaves the released definition byte-identical and all selected existing Wright journeys passing without migration or cleanup.
- **SC-008**: The renderer can be replaced by a contract fixture while canonical semantics, validation results, persistence identities, and text projection outputs remain unchanged.
- **SC-009**: Checkpoints C, D, and E each provide a validated clickable walkthrough with raw and annotated screenshots and no unresolved console errors, page errors, failed requests, lost state, or semantic-ID disagreement.
- **SC-010**: Governed benchmark qualification remains exactly `0/100` and no workflow execution or external tool/model call occurs during this slice.

## Assumptions

- EPP-F02's released read-only process supplies semantic concepts and customer language but is not itself used as a mutable draft.
- The first editable contract is explicitly versioned and provisional; a required decision record defines its compatibility and rollback limits before implementation approval.
- One local engineer owns a draft at a time in this slice; collaboration and concurrent merge behavior are future work.
- Saving targets Wright's existing local data boundary and does not require a network service, external database, MCP server, model, or new credential.
- Full authoring is desktop-oriented; narrow layouts prioritize safe inspection, diagnostics, and recovery.
- The representative workflow uses Capture requirements, Define product, Review product definition, and Release product definition with one approval gate, one revision feedback path, typed ports, and intended artifacts.

## Explicitly Out of Scope

- Workflow execution, live MCP discovery or invocation, run evidence, retry, cancellation, or recovery orchestration.
- AI/LLM authoring, generated workflow changes, or automatic application of suggestions.
- Benchmark population, qualification, or release-readiness claims.
- Multi-user collaboration, concurrent draft merging, comments, approvals, or production migration.
- Reusing, embedding, or extending Rivet or silently adopting the frozen prototype's implementation architecture.
- A general-purpose rendering framework, permanent draft syntax, or permanent renderer commitment.
- Mutating or releasing the canonical EPP-F02 definition.

