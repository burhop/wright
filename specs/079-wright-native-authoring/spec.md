# Feature Specification: Native Engineering Process Milestone

**Branch:** `codex/079-native-process-milestone` | **Created:** 2026-09-04

**Status:** bounded implementation planning under the user's standing goal. Original manual-only proposal preserved at `6daeb214`. [Scope authority and decisions](milestone-decision.md).

## User Scenarios and Testing

### US1 — Understand actual project progress (P1)

A user opens Program status and sees delivered capabilities, current milestone, remaining acceptance, task stages, quality gaps, next work and evidence identity. Independent test: distinguish implemented/verified/integrated tasks, find a failed or missing test/human review and follow its exact evidence. Refresh failure preserves prior valid content with a stale/error warning.

### US2 — Author and preserve a native process (P1)

An engineer creates source and registered task steps in a dominant graph, configures input once in a contextual Inspector, connects exact ports, undoes a mistake, saves and reopens. Independent test: three inputs/two consumers including fan-out; rename/move preserve identities. Invalid edits retain field text and last valid data; stale writer cannot overwrite another save. Complete the journey with keyboard and click without dragging.

### US3 — Execute and inspect actual results (P1)

The engineer validates and runs the saved process, sees durable step inputs/outputs and accesses an actual generated artifact with provenance. Independent test: three contrasting development examples generate independently checked real outputs; HTTP and headless paths produce equivalent semantics and artifact digests. UI refresh observes persisted execution state.

### US4 — Diagnose and recover (P1)

A failed check identifies its actual input/output evidence and correction target; blocked dependents explain why they did not execute. Correction and rerun create a new linked run preserving prior evidence. Independent test: failure, timeout, cancellation/late completion race and process interruption; no unsuccessful run publishes late outputs as successful.

### US5 — Bind a real local tool and verify delivery (P1)

The engineer selects an exact permitted local MCP tool, inspects schemas/preflight, runs it and sees actual protocol/tool evidence. Changed binding or denied permission blocks invocation. Independent test: disposable real local server through Wright's gateway, separate from mock results. Native/package/Docker and integrated-dev checks demonstrate the delivered boundary, with independent technical and actual human review.

## Functional Requirements

- FR-001: Native semantics, persistence and runtime replace Rivet's role for new engineering processes and remain independent of Rivet. The immutable F02 reader and legacy behavior remain compatible during transition; migration/retirement are tracked separately.
- FR-002: The versioned Wright process language is the official source of truth for AI clients, canvas/Inspector, readable text, API/headless and runtime. All consumers share its schema, operation contracts and authoritative validation; no separate AI or renderer semantics. Stable IDs and semantic digest exclude presentation/server revision. See [language authority](contracts/language-authority.md).
- FR-003: Typed exact ports, direction/cardinality, one input producer/fan-out and acyclic data dependencies are validated atomically. Draft readiness differs from structural validity.
- FR-004: Quantities have canonical decimal strings and explicit units; no floating-point identity ambiguity, implicit conversion or arbitrary expression execution.
- FR-005: Graph-first editor, compact creation, contextual Inspector and read-only source support exact endpoints, input configuration, rename/move and deletion impact review.
- FR-006: Commands/undo/redo are atomic; invalid field buffers preserve the last valid document. Saving retains session history without rewinding revision.
- FR-007: Authenticated workspace-scoped save/reopen uses transaction/CAS/idempotency, preserves failures/conflicts and rejects unsupported schemas without rewrite.
- FR-008: Workspace files and artifacts use authorized logical references, bounded content and verified containment/ownership/digest; no client absolute paths or credentials.
- FR-009: Execution uses an explicit versioned operation registry and sequential DAG, never example/domain/vendor/UI-label dispatch or Rivet serialization.
- FR-010: HTTP/headless invoke the same service and snapshot exact definition/input/binding identity; fixtures, actual local computation and live MCP modes remain distinct.
- FR-011: Durable run/step snapshots/events retain actual bounded inputs/outputs, timings, trace and failures; terminal state is immutable and refresh/restart is truthful.
- FR-012: Outputs are real indexed artifacts with provenance, integrity and allowed access/lifetime, not declarations interpreted as files.
- FR-013: Failures identify layer/correction and blocked dependencies. New correction runs link original immutable evidence; no automatic cyclic scheduling.
- FR-014: Bounded deadlines/cancellation and state CAS prevent late publication. Restart reconciles abandoned runs as interrupted and explains recovery.
- FR-015: Exact MCP server/tool/schema and workspace permissions are preflighted and revalidated before real invocation through the existing gateway.
- FR-016: Three representative examples each have a useful outcome, independent actual-output assertions and negative/recovery proof; they do not qualify the process-100 benchmark.
- FR-017: Dashboard derives task-stage counts/denominators and acceptance progress from records/evidence, with blockers/owners/next action and explicit scope changes.
- FR-018: Dashboard exposes tested commit/tree, PR/merge/deployment and result counts/findings/missing human evidence; distinguishes report recency from current-code coverage and preserves historical gate truth.
- FR-019: All essential UI operations are keyboard/click-without-drag accessible at narrow/zoomed sizes with non-color cues, focus and reduced-motion handling; stable test IDs and real human evaluation are required.
- FR-020: Required focused/candidate/native/Docker/compatibility/independent gates and PR integration precede completion; actual integrated build/browser verification and final truthful dashboard are required. No main release or broader external effects are authorized.

## Measurable Outcomes

- SC-001: All AC01–AC10 in the dashboard contract map to stable tasks and real evidence; no verified/integrated credit without matching current evidence.
- SC-002: Save conflict, exact retry, changed-key reuse and interrupted transaction tests preserve complete correct stored state.
- SC-003: Three examples produce independently checked artifacts and passing negative controls; UI/headless parity and one actual local MCP integration pass.
- SC-004: Cancellation/timeout/interruption and correction-linked rerun tests preserve terminal authority and historical outputs; no late successful publication.
- SC-005: Essential keyboard/non-drag/narrow/zoom journey passes, automated accessibility has no serious/critical issues, and actual human protocol meets its predefined thresholds.
- SC-006: Current exact candidate passes required technical review and delivery gates, merges through a dev PR, and passes verified integrated-build health/browser journeys; dashboard reflects remaining separate release/benchmark obligations.

## Explicit Deferrals

Editable DSL and autonomous AI authoring experience, general expression evaluation, implicit unit conversion, automatic cyclic/parallel execution, human-approval runtime steps, full 100-case generation/qualification, legacy migration/retirement and production release. The shared language/API contract for AI clients is included now. These deferred capabilities remain roadmap items, not hidden claims of this milestone or abandonment of Rivet replacement.
