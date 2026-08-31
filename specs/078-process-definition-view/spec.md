# Feature Specification: Canonical Process Definition and Read-Only Engineer View

**Feature Branch**: `codex/078-process-definition-view`

**Created**: 2026-08-30

**Status**: Planning; implementation approval pending

**Input**: User description: "Deliver EPP-F02 as the smallest customer-visible product increment: an engineer opens one versioned sample engineering process and understands its phases, actions, ports, gates, feedback, and expected artifacts in matching text and diagram views."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Understand a Versioned Engineering Process (Priority: P1)

As an engineer, I can open one versioned sample product-definition process and understand what work occurs, what information enters and leaves each action, what gates control progress, what feedback can send work backward, and what artifacts should exist.

**Why this priority**: This is Wright's first customer-visible proof that a governed engineering process can be explained clearly without executing tools or requiring knowledge of control-plane internals.

**Independent Test**: Open the sample process from Wright's browser UI and, using only the page, identify every phase, action, input/output port, gate, feedback path, and expected artifact.

**Acceptance Scenarios**:

1. **Given** the bundled sample process, **When** an engineer opens its stable browser route, **Then** the page names the process and exact version and presents its purpose, phases, actions, ports, gates, feedback, and expected artifacts in plain language.
2. **Given** an action in the text view, **When** the engineer locates the same item in the diagram, **Then** both surfaces show the same stable semantic identifier and meaning.
3. **Given** the engineer uses keyboard-only navigation, 200% zoom, high contrast, or reduced motion, **When** the view is explored, **Then** all information remains reachable and understandable without relying on color alone.

---

### User Story 2 - Inspect Exact Inputs, Outputs, and Constraints (Priority: P2)

As an engineer reviewing whether a process fits my work, I can inspect the declared inputs, outputs, acceptance gates, artifact expectations, and version identity without any hidden execution or mutation.

**Why this priority**: Customer trust requires inspectable boundaries and an honest distinction between a process definition and a process run.

**Independent Test**: Trace one input through a named action to its output artifact and gate, then confirm the page exposes the exact source identity and performs no write or execution request.

**Acceptance Scenarios**:

1. **Given** a valid process definition, **When** an engineer follows a phase or action, **Then** every referenced input, output, gate, feedback edge, and artifact resolves to a visible definition with no dangling identity.
2. **Given** the read-only view, **When** an engineer explores all controls, **Then** no control can edit, apply, execute, invoke MCP, call an LLM, or persist process data.
3. **Given** the same bundled definition is reopened, **When** its source identity is inspected, **Then** the exact version and content identity are unchanged and visible.

---

### User Story 3 - Receive Honest Failure and Compatibility Guidance (Priority: P3)

As an engineer, I receive a bounded explanation when a process definition is missing, invalid, incompatible, or unavailable, and I can return to a safe Wright surface without losing existing workflows.

**Why this priority**: A customer-facing read path must fail clearly and must not destabilize Wright's existing workflow experiences.

**Independent Test**: Exercise missing, malformed, unsupported-version, and disabled-feature fixtures and confirm each state identifies the problem, preserves the source, and provides a recovery direction.

**Acceptance Scenarios**:

1. **Given** a missing or invalid definition, **When** the route is opened, **Then** the page shows an accessible diagnostic and recovery direction without rendering partial data or modifying the source.
2. **Given** an unsupported definition version, **When** it is requested, **Then** the page identifies the unsupported version and the versions this Wright build can read.
3. **Given** the feature is disabled or removed, **When** existing Wright workspace and Rivet journeys are exercised, **Then** they behave as before and no migrated data or cleanup is required.

### Edge Cases

- A process contains duplicate semantic identifiers or a reference to a missing port, gate, action, feedback edge, or artifact.
- A diagram would be visually dense at a narrow viewport or 200% zoom; the text hierarchy remains the complete accessible representation.
- A phase or action has no inputs, outputs, feedback, or artifacts; the view says "none declared" rather than omitting the category.
- The source is syntactically valid but uses an unsupported schema version.
- The bundled definition or its declared content identity is missing, stale, or mismatched.
- The browser route is requested while the feature flag is disabled.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Wright MUST provide one stable browser route for a bundled, versioned sample product-definition process.
- **FR-002**: The view MUST present process purpose, version, phases, actions, typed input/output ports, gates, feedback paths, and expected artifacts in plain language.
- **FR-003**: Text and diagram representations MUST derive from one validated definition and use identical stable semantic identifiers.
- **FR-004**: The text representation MUST remain complete without the diagram and MUST expose "none declared" for empty categories.
- **FR-005**: The page MUST expose the exact definition version and content identity used for the displayed view.
- **FR-006**: The read path MUST reject duplicate identities, dangling references, invalid structure, identity mismatches, and unsupported versions before presentation.
- **FR-007**: Missing, invalid, incompatible, disabled, and unavailable states MUST provide non-sensitive diagnostics and a bounded recovery direction without partial rendering or source mutation.
- **FR-008**: EPP-F02 MUST NOT edit, apply, execute, persist, migrate, invoke MCP, invoke an LLM, or claim that a process has run or qualified.
- **FR-009**: The route MUST meet Wright's keyboard, focus, contrast, non-color, narrow-viewport, 200%-zoom, and reduced-motion requirements; every interactive control MUST have a stable test identity.
- **FR-010**: The feature MUST be additive and removable behind a feature boundary; existing workspace, Rivet, API, native-runtime, and packaging behavior MUST remain compatible.
- **FR-011**: Tests MUST cover the validated model, cross-reference failures, browser text/diagram identity equivalence, accessibility states, failure states, packaging, and existing-workflow non-interference.
- **FR-012**: EPP-F02 MUST provide no governed benchmark evidence: its use-case row MUST have `process_100_id: null`, empty benchmark evidence, and no effect on the defined, in-progress, implemented, tested, independently verified, or qualified `process_100` funnel counts, all of which remain `0/100`.
- **FR-013**: The product study for `PROD-02` MUST be preregistered before implementation approval with its comparator, claim, independent-participant rule, tasks, and numeric completion, correctness, recovery, comprehension, and accessibility thresholds.
- **FR-014**: The browser page MUST link to or visibly identify the bundled definition's inspectable source while preventing unsafe absolute paths, traversal, or external URLs.
- **FR-015**: The live status dashboard MUST bind EPP-F02 by feature-qualified task path at activation and refresh at the US1, US2/US3, and candidate checkpoints without changing readiness or benchmark results.

### Key Entities

- **Process Definition**: One immutable, versioned semantic document with a stable process identity, title, purpose, schema version, content identity, ordered phases, and explicit references.
- **Phase**: An ordered grouping of actions with a stable identity and customer-readable purpose.
- **Action**: A bounded unit of engineering work with declared ports, gates, feedback, and expected artifacts; it grants no execution authority.
- **Port**: A typed input or output identity referenced by an action.
- **Gate**: A named acceptance condition that explains what must be true before progress.
- **Feedback Path**: A directed, explained return from a gate or action to an earlier semantic identity.
- **Expected Artifact**: A declared result type and purpose, not evidence that the artifact exists.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: At least 4 of 5 independent engineer participants correctly identify every phase, action, port direction, gate, feedback path, and expected artifact using the read-only page.
- **SC-002**: The median participant completes the core comprehension task within 3 minutes, at least 25% faster than the same task using the canonical source alone, with no reduction in correctness.
- **SC-003**: Each participant maps text items to diagram items with no more than one semantic-identity error, and at least 4 of 5 score 80% or higher on the preregistered comprehension questions.
- **SC-004**: All participants recover from each presented missing, invalid, or unsupported-version state using the displayed guidance without source mutation or facilitator instruction.
- **SC-005**: Automated accessibility checks report zero serious or critical issues, and the complete journey passes keyboard-only use, 200% zoom at 1280 CSS pixels, a 320 CSS-pixel viewport, non-color status cues, and reduced motion.
- **SC-006**: Automated tests prove 100% of text and diagram semantic identities match the validated source and that every source reference resolves exactly once.
- **SC-007**: Existing selected workspace, Rivet, API, native-runtime, and packaging regression journeys pass unchanged with the feature enabled, disabled, and removed from navigation.
- **SC-008**: Governed benchmark qualification remains exactly `0/100` unless a separately authorized benchmark run produces accepted evidence.

## Assumptions

- EPP-F02 uses a versioned semantic JSON document only as its immutable bundled read-only interchange contract; text and diagram are projections. Editable syntax, round-trip behavior, persistence, and Apply semantics remain undecided under `DEC-P0-002` and blocked until EPP-F06 evidence exists.
- The bundled sample describes the product-definition learning chain represented by `EPP-US-001` through `EPP-US-005`; it explains the process but does not perform those customer outcomes.
- The sample ships with Wright and requires no database, network, MCP server, LLM, or new dependency.
- The diagram is a replaceable projection, not a permanent renderer or authoring-syntax commitment.
- `PROD-02` uses five participants who did not author the implementation artifacts, a counterbalanced within-participant comparison against the canonical source, and one frozen task script; study execution is a later authorized verification action.
- EPP-F01B is merged in `dev` at commit `9f961d52683e0e999fe29a7fed4c1e016de29620`, whose tree exactly matches its approved candidate; EPP-F02 activation still requires the bounded post-merge correction and green development verification.

## Explicitly Out of Scope

- Process execution, run evidence, cancellation, retry, or recovery orchestration.
- Process editing, textual or diagram authoring, Apply behavior, persistence, migrations, semantic diff, or collaboration.
- MCP discovery or invocation, LLM generation, domain-specific dispatch, and benchmark execution.
- Reusing or promoting prototype feature code wholesale.
- A permanent commitment to one diagram library, editor, or textual authoring syntax.
- Any claim that the EPP-F02 definition is a governed benchmark case manifest or supplies `BENCH-02`/`BENCH-03` qualification evidence.
