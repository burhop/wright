# Feature Specification: Engineer Workflow Canvas Prototype

**Feature Branch**: `076-engineering-workflow-prototype`

**Created**: 2026-08-24

**Status**: Draft for prototype approval

**Input**: Create a disposable, incremental prototype for an engineer-readable
workflow canvas. Evaluate MIT-licensed graph modules, phase separators, LLM
authoring, and schema-driven calls through Wright's existing generic MCP
catalog and gateway. Do not reimplement Rivet or create CAD-, FEA-, or other
domain-specific services. Use engineering scenarios only as fixtures, document
lessons from the current code and test process, and produce checkpoint evidence
for a retain, hybrid, or replace decision.

## Scope and Intent

This feature is a learning branch, not a production rearchitecture. It MUST
make uncertain architectural choices cheap to test and easy to reverse. Each
checkpoint MUST yield a demonstrable result and evidence that can be retained
even if every prototype implementation file is later deleted.

The drill-bit-holder workflow is the primary reference scenario because it
exercises visual inputs, contextual knowledge, specification review, iterative
tool calls, verification gates, artifacts, quotation, approval, and
notifications. Those nouns are presentation examples only. The execution
model MUST remain a generic workflow and MCP model.

### Explicitly Out of Scope

- Reimplementing, forking, or replacing Rivet in production.
- Creating separate runtime services, executors, or node classes for CAD, FEA,
  manufacturing, purchasing, email, or any other domain.
- Production database migrations or durable compatibility promises for
  prototype documents.
- Production supplier, purchasing, email, or project-management integrations.
- Full Rivet import/export compatibility or migration of existing workflows.
- Production orchestration, scheduling, scaling, or security certification.
- Choosing a permanent graph library before the bakeoff evidence is reviewed.

## User Scenarios & Testing

### User Story 1 - Understand an Engineering Workflow (Priority: P1)

As an engineer, I can open a workflow and understand its phases, inputs,
decisions, artifacts, tool actions, and feedback loops without learning an
LLM-oriented graph editor.

**Why this priority**: If the visual language is not immediately legible to an
engineer, no runtime or AI capability makes the product useful.

**Independent Test**: Present the drill-bit-holder fixture without explanatory
text and ask a participant to identify the design input, verification gate,
rework loop, released manufacturing artifacts, and approval point.

**Acceptance Scenarios**:

1. **Given** the reference workflow, **When** an engineer scans the canvas,
   **Then** Define, Verify, and Manufacture are visible as phase lanes and the
   main path can be followed left to right.
2. **Given** a block on the canvas, **When** the engineer inspects it, **Then**
   its human purpose, required inputs, produced outputs, status, and whether it
   invokes an external capability are visible without opening implementation
   details.
3. **Given** a failed verification result, **When** it is displayed, **Then**
   the gate, failure reason, and feedback connection to the design work are
   visually distinct from the accepted path.
4. **Given** a different engineering or business process, **When** its template
   defines other phase names, **Then** the canvas displays those phases without
   changing the workflow engine.

---

### User Story 2 - Bind and Call Any MCP Tool (Priority: P1)

As a workflow author, I can add a generic MCP action, select an available
server and tool, configure schema-derived inputs, and review its result without
the UI or runtime categorizing that tool as a special engineering service.

**Why this priority**: Generic MCP interoperability is the stable boundary.
Domain taxonomies would create an unbounded set of services and duplicate
execution logic.

**Independent Test**: Bind three tools with materially different schemas from
a deterministic MCP fixture server and execute each through the same block and
gateway path.

**Acceptance Scenarios**:

1. **Given** the Wright MCP catalog, **When** the author adds an MCP action,
   **Then** the author selects an exact server/tool identity and sees controls
   derived from its declared input schema.
2. **Given** a reviewed binding, **When** it executes, **Then** the call uses
   Wright's existing generic gateway, approvals, scoping, audit, and result
   projection.
3. **Given** a changed or missing tool declaration, **When** the workflow is
   opened or run, **Then** the binding is marked stale or unavailable and no
   substitute tool is silently selected.
4. **Given** a presentation alias such as "Run structural check," **When** the
   block executes, **Then** the alias affects only display; the saved binding
   still identifies the exact generic MCP server and tool.

---

### User Story 3 - Author Incrementally with an LLM (Priority: P2)

As an engineer, I can describe a workflow or a small change in plain language,
review a proposed structured edit, and accept or reject it before the canvas
changes.

**Why this priority**: Prompt-driven creation is valuable only when it produces
bounded, understandable, and reversible changes rather than an opaque graph.

**Independent Test**: Starting from an empty workflow, apply a sequence of
deterministic authoring requests that creates phases, adds blocks, connects
them, and revises one block while preserving stable identities.

**Acceptance Scenarios**:

1. **Given** a natural-language workflow request, **When** the LLM responds,
   **Then** the response is validated as typed workflow commands before any
   state changes.
2. **Given** a valid proposal, **When** it is shown to the author, **Then** the
   author sees a concise semantic diff and can accept or reject it.
3. **Given** an invalid, ambiguous, or unauthorized proposal, **When** it is
   validated, **Then** it is rejected with a specific repair message and the
   current workflow remains unchanged.
4. **Given** no remote model is available, **When** the prototype is tested,
   **Then** deterministic local fixtures exercise every authoring interaction.

---

### User Story 4 - Compare Canvas Foundations Fairly (Priority: P2)

As a product and engineering team, we can compare a small set of MIT-licensed
graph foundations using the same workflow fixture, interactions, and scoring
criteria.

**Why this priority**: A controlled bakeoff reduces the risk of replacing one
hard-to-maintain dependency with another unsuitable one.

**Independent Test**: Render the same immutable workflow specification in each
candidate harness and record capability, accessibility, integration effort,
performance, and maintainability evidence using one rubric.

**Acceptance Scenarios**:

1. **Given** two or three eligible candidates, **When** the reference fixture is
   rendered, **Then** each candidate receives the same data and required visual
   behavior.
2. **Given** a candidate that requires domain-specific workflow state or an
   incompatible execution engine, **When** it is assessed, **Then** that cost
   is recorded rather than hidden in adapter code.
3. **Given** completed bakeoff evidence, **When** the team reviews it, **Then**
   the recommendation may be adopt, hybridize, retain Rivet, or stop; the
   prototype does not predetermine replacement.

---

### User Story 5 - Learn Through Fast Checkpoints (Priority: P2)

As a developer or reviewer, I can see incremental progress, run focused tests
quickly, and understand what was learned at each checkpoint.

**Why this priority**: Long, fragile feedback cycles and large unreviewable
changes are a primary risk identified in the existing implementation.

**Independent Test**: Check out any checkpoint commit, run its documented fast
verification, and open its single demo without requiring later checkpoints or
external engineering applications.

**Acceptance Scenarios**:

1. **Given** a checkpoint, **When** its quickstart is followed, **Then** the
   checkpoint can be demonstrated independently with deterministic data.
2. **Given** a normal UI or model edit, **When** focused verification runs,
   **Then** it does not start the full repository gate or a multi-browser suite.
3. **Given** an experiment that fails its exit criteria, **When** findings are
   recorded, **Then** work stops or changes direction without completing the
   remaining implementation plan.
4. **Given** the final prototype review, **When** the branch is evaluated,
   **Then** a postmortem distinguishes reusable contracts and lessons from code
   that should be discarded.

### Edge Cases

- A tool schema is missing, recursive, very large, or uses unsupported JSON
  Schema constructs.
- A server or tool disappears, changes schema, or changes risk metadata after
  binding review.
- An LLM proposes duplicate identifiers, invalid ports, cycles, disconnected
  required inputs, phase deletion with children, or unauthorized MCP bindings.
- A workflow includes a deliberate loop, a conditional feedback path, or
  multiple phase crossings.
- A phase or block has a long label, localized text, or no presentation alias.
- A graph is empty, very wide, very deep, or exceeds the prototype's bounded
  node/edge limits.
- A tool result is empty, redacted, truncated, failed, cancelled, or contains
  one or more artifact links.
- The prototype is offline, the LLM is unavailable, or the MCP fixture exits
  unexpectedly.
- A user opens prototype data produced by an incompatible checkpoint.
- Keyboard-only, reduced-motion, high-contrast, narrow, and zoomed layouts are
  used.

## Requirements

### Functional Requirements

- **FR-001**: The prototype MUST be isolated behind a prototype-only route or
  flag and MUST NOT change the production Rivet editor, its patches, or its
  persisted project format.
- **FR-002**: The prototype MUST define a versioned, typed Wright workflow
  specification that is independent of every candidate canvas library and of
  Rivet.
- **FR-003**: The workflow specification MUST represent configurable phase
  lanes, blocks, typed ports, connections, gates, feedback paths, artifacts,
  human review points, and presentation metadata.
- **FR-004**: Block roles MAY describe interaction semantics such as input,
  transformation, MCP action, decision, artifact, approval, and notification,
  but MUST NOT select a domain-specific executor.
- **FR-005**: Phase names and presentation aliases MUST be data, so Define,
  Verify, and Manufacture can be retained for the reference scenario and
  replaced for other processes without code changes.
- **FR-006**: The prototype MUST use a single generic MCP binding and execution
  path for every MCP tool.
- **FR-007**: A saved MCP binding MUST include exact server identity, tool
  identity, reviewed declaration or revision identity, input schema identity,
  and risk/approval evidence needed by the existing gateway.
- **FR-008**: MCP block ports and configuration controls MUST be derived from
  the selected tool schema, with explicit handling for unsupported schema
  constructs.
- **FR-009**: All MCP discovery and calls MUST use Wright's existing
  provider-neutral catalog and governed gateway; the prototype MUST NOT call
  domain applications directly.
- **FR-010**: CAD, FEA, fabrication, and supplier actions MUST exist only as
  reference labels, sample tool declarations, and deterministic fixtures. No
  domain-specific service, executor, or node implementation may be introduced.
- **FR-011**: LLM authoring MUST target validated workflow commands or the typed
  workflow specification and MUST NOT emit candidate-library state, raw Rivet
  projects, or executable MCP calls.
- **FR-012**: Each LLM-proposed change MUST be previewable as a semantic diff,
  explicitly accepted or rejected, atomic, and reversible.
- **FR-013**: The prototype MUST provide deterministic LLM responses and an
  in-process or local deterministic MCP fixture for routine testing.
- **FR-014**: At least two and no more than three MIT-licensed graph candidates
  MUST be tested with the same fixture, required behaviors, and scoring rubric.
- **FR-015**: The candidate bakeoff MUST assess phase rendering, custom blocks,
  ports, loops, selection, keyboard access, layout control, serialization
  separation, React integration, performance, package health, and testability.
- **FR-016**: The branch MUST deliver independently demonstrable checkpoints
  for baseline/postmortem, library bakeoff, static canvas, editing, generic MCP
  call, LLM authoring, integrated scenario, and final decision.
- **FR-017**: Each checkpoint MUST state its hypothesis, bounded scope,
  demonstration, automated verification, measurements, decision, and retained
  learning.
- **FR-018**: Prototype persistence MUST be local, explicitly disposable, and
  require no production schema migration.
- **FR-019**: The UI MUST expose purpose and engineering artifacts first while
  retaining exact MCP binding, schema, execution, and evidence details in an
  inspectable secondary view.
- **FR-020**: The prototype MUST preserve Wright's workspace scope, approvals,
  audit correlation, redaction, cancellation, and artifact evidence when it
  invokes MCP.
- **FR-021**: The default development loop MUST use pure model tests and
  component tests; browser automation MUST be limited to focused checkpoint
  journeys and the repository gate.
- **FR-022**: The branch MUST include a postmortem of the current Rivet
  integration and test process that identifies what to retain, change, retire,
  and measure, supported by observed timings and failure modes.
- **FR-023**: The final evidence MUST recommend retain, hybrid, replace, or stop
  and MUST separate the canvas-library decision from the generic MCP and
  workflow-specification decisions.
- **FR-024**: Prototype implementation MUST stop for human review after every
  major checkpoint, in accordance with the project constitution.

### Key Entities

- **Workflow Specification**: Versioned, library-neutral definition of phases,
  blocks, ports, connections, presentation, and bindings.
- **Phase Lane**: Configurable visual grouping with identity, order, label,
  description, and presentation attributes.
- **Workflow Block**: Stable semantic unit with role, purpose, configuration,
  ports, phase membership, and optional capability binding.
- **Connection**: Typed directed relationship with source/target ports and
  control or data semantics.
- **MCP Binding**: Exact reviewed server/tool declaration and schema identity
  used by the generic gateway path.
- **Authoring Command**: Validated atomic add, remove, update, move, connect, or
  disconnect operation proposed by a person or LLM.
- **Scenario Fixture**: Deterministic workflow, MCP catalog, results, and
  authoring responses used consistently across candidates and tests.
- **Checkpoint Evidence**: Hypothesis, demo, measurements, verification,
  findings, and decision for an incremental experiment.
- **Candidate Evaluation**: Common rubric and recorded evidence for one graph
  foundation.
- **Postmortem Finding**: Evidence-backed observation about the current code or
  process, with retain/change/retire disposition.

## Success Criteria

### Measurable Outcomes

- **SC-001**: At least 80% of representative evaluation sessions correctly
  identify the main path, verification gate, feedback loop, released artifact,
  and human approval without assistance.
- **SC-002**: The median time to answer the reference-workflow comprehension
  questions is at least 30% lower than the same exercise in the current Rivet
  baseline.
- **SC-003**: Three tools with materially different input schemas bind and run
  through one MCP block type and one gateway adapter with no domain-specific
  execution code.
- **SC-004**: At least 90% of a minimum 20 deterministic LLM authoring cases
  produce a valid proposed command set on the first response; 100% of invalid
  responses are rejected without modifying workflow state.
- **SC-005**: Pure workflow-model tests complete in 5 seconds or less,
  component feedback completes in 30 seconds or less, and the focused MCP/LLM
  contract suite completes in 2 minutes or less on the reference workstation.
- **SC-006**: No checkpoint requires more than three focused Chromium journeys,
  and ordinary implementation edits require no browser automation.
- **SC-007**: Every planned checkpoint is independently demonstrable and has a
  recorded go/change/stop decision before the next checkpoint begins.
- **SC-008**: The prototype adds zero Rivet patches, zero production database
  migrations, and zero domain-specific MCP service or executor classes.
- **SC-009**: The final decision record scores every candidate with the same
  rubric and provides an evidence-backed retain, hybrid, replace, or stop
  recommendation.

## Assumptions

- The existing Wright MCP catalog, gateway, workspace scoping, approvals, and
  evidence contracts remain the authoritative integration boundary.
- Candidate packages must be MIT-licensed at the pinned version; license and
  transitive dependency review is repeated before any production adoption.
- The prototype targets Wright's existing React web application and local
  desktop/browser environment but does not establish a permanent UI
  architecture.
- Remote LLM access is optional. Deterministic fixtures are the acceptance
  authority for authoring behavior.
- External engineering applications, suppliers, email, purchasing, and project
  systems are simulated unless an already-available generic MCP tool can be
  exercised safely.
- Prototype files may be deleted after review; specifications, evidence,
  measurements, and decision records are the durable deliverables.
