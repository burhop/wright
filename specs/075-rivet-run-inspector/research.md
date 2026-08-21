# Research: Rivet Run Inspector

## Decision 1: Use a collapsible bottom inspector

**Decision**: Place the Run Inspector below the Rivet canvas with a compact summary row that remains visible when collapsed. Open it automatically while a run is active and on terminal failure; select Outputs on success and Diagnosis on failure.

**Rationale**: Wright already reserves the right side of the workspace for the Agent control pane. A permanent result sidebar would materially reduce the graph canvas, especially on ordinary laptop screens. A bottom region preserves horizontal graph space and gives structured results enough width.

**Alternatives considered**:

- A permanent right sidebar was rejected because it competes with the Agent pane.
- A modal was rejected because it hides the graph and makes step-to-node correlation awkward.
- A toolbar tooltip was rejected because it cannot present complete, accessible results or history.

## Decision 2: Project one authoritative inspection snapshot

**Decision**: Add a workspace-service inspection projection and thin FastAPI endpoint that combine the persisted run record, incremental run events, MCP child-call evidence, final outputs, diagnostics, and completeness metadata. The frontend polls this projection only while a run is active and stops at terminal state.

**Rationale**: The current surface makes parallel requests for the run and history and only fetches evidence elsewhere. A single typed snapshot prevents the UI from combining mismatched generations or terminal states, provides one place for redaction and recovery wording, and lets a refreshed browser rebuild the complete inspector state.

**Alternatives considered**:

- Keeping all aggregation in React was rejected because recovery wording, redaction, and evidence completeness are domain behavior.
- Server-Sent Events were deferred because bounded local polling already exists and a new streaming lifecycle would add reconnection and cancellation complexity without being necessary to meet the one-second update target.
- Reading raw runner logs was rejected because logs are not the authoritative or stable user contract.

## Decision 3: Keep SQLite and existing evidence records authoritative

**Decision**: Extend `WorkflowRunRepository` with scoped recent-run queries and complete its projection of existing timestamp and trace columns. Continue using `workspace_workflow_run_events` and MCP `call_json` as the durable timeline and step evidence. Do not add a second run-history store.

**Rationale**: The existing schema already has workspace/session/workflow identity, revision, state, timestamps, outputs, events, manifests, child calls, artifacts, and trace fields. The run index already supports scoped history. The missing behavior is repository/query and projection logic rather than a new database.

**Alternatives considered**:

- Browser-local history was rejected because it would disappear on refresh and disagree with backend truth.
- A new run-inspector table was rejected because it would duplicate state and require reconciliation.

## Decision 4: Persist safe result projections at the execution boundary

**Decision**: Redact and bound final workflow outputs before persistence. Store complete redacted values when they fit the existing run-output limit; otherwise store an explicit typed preview, digest, original byte count, retained byte count, and truncation reason without changing a successful execution into a failure. Add an optional bounded result projection to the already-sanitized MCP child-call JSON so successful upstream step results remain inspectable.

**Rationale**: MCP results are already sanitized before returning to Rivet, but current child evidence stores only metadata and artifacts. Terminal outputs are bounded by SQLite persistence, but oversized values can currently make persistence fail. Applying one result-projection policy at the write boundary prevents secrets from reaching UI/copy/export paths and makes completeness truthful.

**Alternatives considered**:

- Persisting raw MCP responses was rejected because it duplicates sensitive transport content.
- Truncating only in React was rejected because copy, export, and other clients could still expose unsafe values.
- Automatically storing arbitrarily large output files was deferred because existing retention limits are explicitly in scope and artifact lifecycle expansion is not required for this feature.

## Decision 5: Derive steps from events and child calls

**Decision**: Build ordered `ExecutionStep` projections from run progress events and MCP child-call records, correlating by node ID and request ID. Prefer child-call terminal evidence over transient progress when both exist. Preserve unknown and not-run states when evidence is incomplete.

**Rationale**: The runner already emits redacted progress fields such as phase, node ID, and request ID, while child calls add tool identity, timing, trace identity, state, reason, and artifacts. A deterministic reducer can produce a useful step list without instrumenting Rivet internals twice.

**Alternatives considered**:

- Treating every timeline event as a separate step was rejected because progress events would overwhelm users.
- Inferring execution solely from graph topology was rejected because conditional or failed execution may not follow every graph edge.

## Decision 6: Centralize plain-language diagnostics in the domain layer

**Decision**: Add a stable reason-code-to-diagnostic projection in `workspace_service`. It returns a short summary, failing node/tool when known, a safe recovery action, and whether full rerun is allowed. Technical identifiers remain in an expandable section.

**Rationale**: Backend reason codes are currently shown directly in the canvas. Mapping them once keeps wording consistent across the direct surface, workflow panel, tests, and exported evidence while retaining exact codes for support.

**Alternatives considered**:

- A frontend-only error dictionary was rejected because non-web clients would receive poorer diagnostics.
- Model-generated explanations were rejected because run diagnosis must remain deterministic, offline, and safe.

## Decision 7: Full rerun is the recovery baseline

**Decision**: Provide full rerun from the saved revision. Do not implement partial retry in the first release. The contract reserves a retry mode, but it remains unavailable unless a future implementation proves graph position, idempotency, and child cleanup safety.

**Rationale**: MCP calls may modify external engineering applications. Replaying only part of a graph can duplicate side effects or continue from unverified state. The approved specification explicitly makes partial retry conditional.

**Alternatives considered**:

- Retrying the failed node unconditionally was rejected as unsafe.
- Hiding all retry actions was rejected because a full rerun is a useful and understandable baseline.

## Decision 8: Extend the trusted editor bridge for node state and focus

**Decision**: Version the same-origin parent/iframe bridge with messages that set or clear bounded node execution states and optionally focus one node. Implement the Rivet-side host seam in a maintained source patch and rebuild the pinned editor artifact and manifest.

**Rationale**: The parent already owns run state and the wrapper already validates parent origin and request IDs. Extending that boundary avoids DOM scraping and gives the canvas a controlled way to communicate running, success, failure, cancelled, and not-run states without exposing outputs or credentials to the editor iframe.

**Alternatives considered**:

- DOM selectors and synthetic clicks inside the iframe were rejected as brittle and inaccessible.
- Highlighting only the inspector list was rejected because the accepted specification requires graph correlation.

## Decision 9: Use the existing three-tier UI test pyramid

**Decision**: Add component tests for result rendering and inspector states, mocked Playwright journeys for run, failure, refresh, history, keyboard use, and large/redacted output, plus one focused local FastAPI/Rivet smoke covering start-to-inspection truth. Keep real MCP qualification outside normal regression tests.

**Rationale**: This matches Wright's constitution and allows rapid deterministic feedback without requiring OAuth, CAD applications, or external MCP servers.

**Alternatives considered**:

- Relying only on the ongoing live UI marathon was rejected because it is slower and less deterministic.
- A component-only suite was rejected because refresh reattachment and API/UI state correlation are page-level behavior.

