# Feature Specification: Solid Edge Creation Visibility

**Feature Branch**: `048-solid-edge-creation-visibility`

**Created**: 2026-07-16

**Status**: Draft

**Input**: User description: "Make Solid Edge MCP use creation-only workflows, keep generated geometry visible in Solid Edge, provide timely phase and elapsed progress updates, instrument end-to-end latency, and prevent expensive or unintended inspection calls during creation tasks."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Create a New Visible Solid Edge Artifact (Priority: P1)

An engineer asks the agent to create a simple Solid Edge model from scratch. The agent creates a new document, builds the requested geometry, saves it to the requested workspace location, and leaves the result open and visible in Solid Edge without inspecting or modifying a document that was already open.

**Why this priority**: Creating the requested artifact safely and visibly is the only reason Solid Edge is connected and is the feature's primary value.

**Independent Test**: Start Solid Edge with any pre-existing document or a blank session, request a new 20 mm by 20 mm by 10 mm block, and verify that a separate saved Part containing the requested geometry remains open and visible while the pre-existing document is unchanged.

**Acceptance Scenarios**:

1. **Given** Solid Edge is running with no active document, **When** the engineer requests a new part, **Then** the agent creates a new document, displays the geometry in Solid Edge, saves it to the requested path, and leaves it open.
2. **Given** Solid Edge already has a document open, **When** the engineer requests a fresh smoke test, **Then** the agent creates an isolated new document and does not inspect or modify the pre-existing document.
3. **Given** a creation recipe is invalid or the output path is not permitted, **When** creation is attempted, **Then** the agent reports the exact blocking error and stops without switching to inspection or modifying existing geometry.

---

### User Story 2 - Understand Long-Running Work (Priority: P2)

An engineer watching a CAD request can tell whether the agent is planning, creating geometry, saving, verifying, or finishing, and can see that the process is still alive during any long phase.

**Why this priority**: Long periods without visible activity make a healthy process indistinguishable from a hang or crash.

**Independent Test**: Run a creation request with an intentionally delayed phase and verify that the user immediately sees a useful phase message followed by elapsed-time updates until completion or failure.

**Acceptance Scenarios**:

1. **Given** a creation request has just been submitted, **When** work begins, **Then** the user sees an initial planning status without waiting for the first CAD operation.
2. **Given** any phase lasts longer than 10 seconds, **When** the phase is still running, **Then** the user receives an elapsed-time update identifying the current phase at least every 10 seconds.
3. **Given** geometry creation begins, **When** the creation operation is active, **Then** the user sees a human-readable Solid Edge creation message rather than an internal tool identifier.

---

### User Story 3 - Diagnose Slow or Failed Creation (Priority: P3)

An operator can determine whether delay came from agent planning, tool discovery, Solid Edge execution, serialization, or an error, without exposing secrets or corrupting the tool protocol.

**Why this priority**: Accurate phase timing is necessary to improve speed and to route defects to Wright, Hermes, or the SolidEdgeMCP owner.

**Independent Test**: Execute a bounded creation request and verify that diagnostics show the number of calls, each operation's duration and outcome, payload sizes, active calls, and the slowest completed calls while protocol messages remain valid.

**Acceptance Scenarios**:

1. **Given** a creation call completes, **When** an operator views diagnostics, **Then** planning time and Solid Edge operation time can be distinguished from the total user wait.
2. **Given** a tool call exceeds the configured threshold, **When** it completes, **Then** it is identified as slow with its operation, duration, outcome, and redacted payload-size metadata.
3. **Given** diagnostic logging is enabled for a local subprocess tool, **When** the tool exchanges protocol messages, **Then** diagnostic output never appears on the protocol output channel.
4. **Given** Hermes owns the local Solid Edge connection, **When** Wright's UI polls status, **Then** no competing Solid Edge tool subprocess is started.

---

### User Story 4 - Avoid Unnecessary Work (Priority: P4)

An engineer's creation request exposes only creation-oriented Solid Edge capabilities to the agent and avoids broad inventories or oversized inspection results that do not contribute to the artifact.

**Why this priority**: Unneeded tool choices and large schemas increase planning time, create opportunities for miscommunication, and can trigger expensive reads.

**Independent Test**: Start a fresh creation session and verify that read-only document, face, feature, dimension, variable, and semantic-inventory operations are unavailable and never called.

**Acceptance Scenarios**:

1. **Given** the Solid Edge creation profile is active, **When** the agent discovers available capabilities, **Then** read-only inspection and inventory operations are absent.
2. **Given** a simple smoke test, **When** the agent completes the task, **Then** it uses one creation operation and no inspection operations.

### Edge Cases

- Solid Edge is not running or becomes unavailable during creation.
- A creation output path is outside the approved workspace roots.
- The requested output already exists and overwrite permission was not explicit.
- A recipe passes agent planning but fails provider validation before geometry is created.
- A stream consumer disconnects and later reconnects while the creation job continues.
- The agent finishes without returning user-facing text after a tool completes.
- Multiple local components attempt to own the same Solid Edge connection.
- A tool returns an unusually large schema or result payload.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST treat Solid Edge sessions as creation-oriented and MUST NOT begin with read-only inspection unless the user explicitly requests inspection in a future supported workflow.
- **FR-002**: A fresh or smoke-test request MUST create a new isolated document and MUST NOT inspect, modify, save, close, or discard any document that was already open.
- **FR-003**: Created geometry MUST be visible in Solid Edge during execution and the completed new document MUST remain open unless the user explicitly requests otherwise.
- **FR-004**: Every creation request MUST use an explicit output path within an approved workspace location.
- **FR-005**: The creation profile MUST exclude read-only document, face, feature, dimension, variable, measurement, capability, and semantic-inventory operations.
- **FR-006**: A simple part smoke test MUST use no more than one creation operation and MUST perform no inspection operations.
- **FR-007**: The system MUST provide canonical, unambiguous guidance for common creation recipes, including valid direction values and new-document behavior.
- **FR-008**: If validation or creation fails, the system MUST report the exact actionable error and stop without inspecting an existing model or attempting unrelated recovery operations.
- **FR-009**: The user MUST receive an immediate planning status when a request begins.
- **FR-010**: While work continues, the user MUST receive a human-readable current phase and elapsed-time update at least every 10 seconds.
- **FR-011**: Solid Edge operation progress MUST describe the artifact action in user language and MUST NOT expose only an internal operation identifier.
- **FR-012**: A user who reconnects to an active or recently completed stream MUST be able to receive the buffered phase, progress, result, and completion events.
- **FR-013**: Diagnostics MUST record started and terminal events for each operation with correlation identifiers, operation name, outcome, duration, argument count, timeout, and redacted response size.
- **FR-014**: Diagnostics MUST summarize active calls, completed calls, outcome counts, total and average operation time, and the slowest completed operations.
- **FR-015**: Diagnostic logging MUST use a channel separate from the subprocess protocol channel.
- **FR-016**: Exactly one local component MUST own and start the Solid Edge tool subprocess for a Hermes-driven session.
- **FR-017**: Passive API status polling MUST NOT start, stop, or duplicate externally owned tool subprocesses.
- **FR-018**: The system MUST preserve authentication when querying protected local service endpoints used by the Hermes integration.
- **FR-019**: Diagnostic records and progress updates MUST redact credentials and other secrets.
- **FR-020**: The system MUST make agent planning delay distinguishable from Solid Edge execution delay for every completed creation turn.

### Key Entities

- **Creation Request**: The engineer's requested artifact, dimensions or constraints, new-document intent, explicit output path, visibility preference, overwrite permission, and success criterion.
- **Creation Profile**: The bounded set of creation, validation, export, rebuild, and service-status capabilities available for a Solid Edge creation session.
- **Progress Update**: A user-facing phase, status, message, elapsed time, and optional operation correlation identifier.
- **Diagnostic Record**: A redacted started or terminal operation record containing correlation identifiers, timing, outcome, and payload-size metadata.
- **Runtime Owner**: The single local component responsible for the lifecycle of the Solid Edge tool subprocess.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: At least 95% of bounded simple-part smoke tests create the correct new visible artifact on the first creation attempt without inspecting a pre-existing document.
- **SC-002**: Users see the first meaningful status within 1 second of submitting a creation request and receive an update at intervals no greater than 10 seconds while work continues.
- **SC-003**: At least 90% of bounded simple-part smoke tests finish within 30 seconds, with geometry creation beginning within 10 seconds of submission.
- **SC-004**: 100% of successful smoke-test artifacts are saved to the requested approved path and remain open and visible in Solid Edge at completion.
- **SC-005**: 100% of failed validation attempts report an actionable error and make no change to a pre-existing Solid Edge document.
- **SC-006**: Every completed creation turn provides enough timing evidence to attribute at least 95% of the total elapsed time to planning, capability discovery, Solid Edge execution, result transfer, or final response generation.
- **SC-007**: Repeated UI polling and agent use maintain exactly one Solid Edge tool subprocess, with zero protocol parse errors caused by diagnostic output.
- **SC-008**: The creation profile results in zero calls to read-only inspection or inventory operations during bounded creation tests.

## Assumptions

- Solid Edge and the SolidEdgeMCP backend run locally on the same Windows workstation as Wright and Hermes.
- The user connects Solid Edge to create or modify artifacts; a general read-only inspection mode is outside this feature's scope.
- A bounded simple-part smoke test is a new rectangular sketch followed by one extrusion and one save to a unique Part file.
- Approved output locations are workspace-owned directories explicitly configured for Solid Edge creation.
- Explicit user instructions may authorize overwrite or closing the newly created document, but never imply permission to alter an unrelated pre-existing document.
- Existing local authentication and workspace authorization remain in force.
- Performance targets are measured on the target workstation with Solid Edge already running and the local agent services healthy.
