# Proposed ADR: Wright-native Manual Authoring Boundary

**Historical proposal:** preserved as submitted at `6daeb214`. The September 4 [milestone decision](milestone-decision.md), [current plan](plan.md) and [language-authority contract](contracts/language-authority.md) supersede its prospective manual-only scope and repeated approval steps. Its original statements below remain historical context, not current implementation gates.

**Status**: Proposed; not accepted and not implementation authority.

**Date**: 2026-09-02

**Owner / approver**: Human architecture and product approver.

**Related decision**: `DEC-P0-002`; proposed bounded successor to [ADR 0021](../../docs/programs/engineering-process-platform/decisions/0021-epp-f02-read-only-boundary.md). The existing ADR and decision register remain unchanged until explicit acceptance.

## Outcome and non-negotiable boundary

Build Wright's own editor for Wright's own engineering-process definitions. Rivet is the legacy system being replaced, not the canvas, data model, or runtime of the new path. No new code under `integrations/rivet`, no extension of `DirectRivetSurface` or `WrightEditorBridge`, and no reuse of the quarantined 081 implementation is part of this proposal.

The first independent outcome is useful manual authoring with safe local save/reopen. It does not perform the work described by a process. Later EPP binding, execution, and migration features complete the replacement; leaving the old application available during transition does not make it a dependency of the new editor.

## Current evidence

- [EPP-F02 approval](../../docs/programs/engineering-process-platform/evidence/approvals/APR-EPP-F02-MC-001.json) explicitly excludes Rivet feature investment and wholesale prototype copying.
- EPP-F02 already has a validated read-only model, [projection boundary](../../apps/web/src/components/process-definition/projection.ts), readable text, and matching diagram. Its schema fixes the sample identity and uses sample-specific type vocabularies; it is not a general authoring schema or an existing exact-port canvas.
- [ADR 0021](../../docs/programs/engineering-process-platform/decisions/0021-epp-f02-read-only-boundary.md) leaves editable representation, round trips, persistence, and Apply undecided. Its deletion-only rollback is insufficient once users save documents.
- The frozen `076-engineering-workflow-prototype` at `e7bb75c1d97e70e55b943e0c94a31ff85cf9f82d` contains useful contracts, port research, and a provisional React Flow bakeoff. [The disposition](../../docs/programs/engineering-process-platform/prototype-evidence.md) permits learning from that evidence, not copying its implementation or claiming its human studies were completed.
- The approved image establishes the graph-first direction. It does not approve invented service status, actual Run/Ask AI actions, or a permanent choice of renderer or editable syntax.

## Recommended decisions for this bounded increment

### 1. Native product, replaceable canvas

Wright owns document validation, commands, undo/redo, selection identity, save state, and the meaning of each port. A canvas adapter receives a read-only projection and emits Wright intents. It cannot persist its node/edge JSON, execute work, create semantic IDs, or bypass command validation.

Recommend **React Flow as the initial replaceable renderer**, not as the workflow engine. This uses the prior bakeoff's learning without importing prototype components. A new adapter and Wright-styled node/port components are written against the approved contracts. Exact package version, license, advisory review, bundle impact, and dependency approval must be frozen before installation; no dependency is added by this ADR draft. Required attribution is retained unless an approved license permits otherwise.

The native service/model and text projection can reuse audited generic EPP concepts and helpers. Do not make the current immutable reader writable or silently widen its closed schema. Extract genuinely shared validation only with v1 regression tests.

### 2. Structured manual editing first; source remains read-only

Use fields in the Inspector and atomic canvas commands for this first increment. Source is a generated, inspectable representation, not a second editor. This avoids selecting JSON, YAML, or a DSL as the engineer's permanent editing language prematurely.

LLM proposals and editable text remain deferred under `DEC-P0-002`, including their required edit studies and acceptance semantics. This bounded decision must not close that entire decision or waive its remaining evidence.

### 3. New authored document contract, not Rivet or the frozen F02 schema

Propose a separately named `wright-authored-process` document, schema version `1.0.0`, containing:

- a semantic definition with document/process identity, title, purpose, ordered phases/actions, typed ports, exact connections, gates/feedback, expected artifacts, and authored input configuration;
- presentation metadata keyed only by stable semantic IDs, containing finite bounded integer layout coordinates and display preferences;
- server-owned revision/concurrency metadata returned outside the client-submitted semantic payload.

Revisions are positive safe integers. IDs are immutable and globally unique within a document. Identifiers do not derive from labels or array positions. The complete document is limited to 1 MiB; a schema-conformance step must freeze per-field/collection bounds before implementation approval.

The type contract is domain-neutral: a port declares a `data`, `artifact`, or `control` family, a versioned logical type identifier, `one` or `many` cardinality, and requiredness. Type identifiers are local declarations, not fetched schema URLs. Connections require equal family, logical type identity, and cardinality in this increment; coercion, unit conversion, schema subtyping, and collection assembly are explicit future operations rather than inferred behavior. File references are workspace-vault logical identities, never absolute paths or credentials.

One output may fan out to several inputs. One input has at most one source. Forward data dependencies remain acyclic and must respect explicit semantic action order; feedback is a separate declared gate-to-earlier-action relation. Gate creation/removal and reciprocal feedback references are one transaction. Dragging changes layout, never order or gate meaning.

An incomplete draft can be structurally valid and saved: missing required configuration and unbound tool/model intentions are readiness findings. Dangling IDs, incompatible edges, malformed values, or invalid gate relationships are structural errors and cannot enter the valid working document.

### 4. Separate field buffers, valid working copy, and persisted copy

Field text may temporarily be invalid. Submitting a user action constructs a candidate, validates the entire candidate, and either accepts it atomically or leaves the valid working copy unchanged. Failed field text remains available for correction; it never silently becomes executable state.

Each accepted user action is one undo unit. Continuous dragging is one layout action; deletion with confirmed dependent removals is one semantic action. Undo/redo operates on session content and never decrements stored revision identifiers. Save preserves session history; reopen starts a new history. A new edit after Undo clears the redo branch. Initial history is bounded to 100 accepted actions with visible oldest-history eviction, never document loss.

Compute a semantic digest excluding presentation, revision, and the digest itself; reuse `wright-process-json-v1` canonicalization only after cross-language vectors establish applicability to the new contract. The opaque document concurrency token covers all persisted semantic and presentation content. Layout-only saves change that token but not semantic identity. Pan, zoom, hover, and selection remain transient, unsaved view state.

### 5. Local save, conflict handling, and recovery

Create a separate authenticated workspace-owned authoring service/repository. The new API is not a write extension to `GET /api/process-definitions/{process_id}`. The existing read-only packaged assets and endpoint remain immutable.

Propose a dedicated SQLite document table within Wright's existing local database. Store the complete bounded semantic-plus-presentation envelope as one transactional row, with workspace identity, document identity, revision, digest/token, and the previous successful envelope for one-step recovery. No separate mutable file/DB pair may represent one commit. File bodies remain in the existing vault and are referenced, not copied into the document.

Save uses compare-and-swap against the loaded token in the same write transaction as replacement. A stale writer receives a conflict and retains its working copy. Recovery is explicit Reload after discard confirmation, or Save as new document; no automatic merge. Save requests carry an idempotency identity so a lost response can be retried without a duplicate revision or duplicate document. Transaction failure leaves the old row intact. Save success requires a committed transaction, not only a changed canvas.

Schema-reader ranges and the additive database migration must be reviewed on the exact previous-stable versions before implementation approval. There is no silent autosave in the initial increment. Closing with unsaved work prompts Save, Discard, or Cancel; unexpected process termination may lose unsaved session edits and must not be advertised as crash-recoverable autosave.

### 6. Honest Create rail and statuses

Input creates an authored source. LLM document creates a draft document task such as a specification or work order. MCP tools and 3D/Drawing/FDM groups create generic unbound step templates. BREP, Solid Edge, and Onshape may appear as intended-application hints in chooser descriptions; they confer no binding, installation, compatibility, or authority.

The first slice has no live discovery or exact MCP binding. If that makes a chooser misleading, show the generic template and its explicit “Needs binding in a later step” state rather than inventing a list of available tools. The execution layer must never dispatch by these labels.

The toolbar provides identity, view selection, undo/redo, save state, structural Check, and input-configuration summary. Run and Ask AI are absent in this increment rather than fake working controls. “Inputs configured” is not “ready to execute.” Expected artifacts are declarations; no artifact-open action appears unless a real, authorized value exists.

### 7. Migration and full replacement sequence

| Stage                                     | New Wright path                                                                                                                 | Legacy/Rivet posture                                                                  |
| ----------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| This proposed slice                       | Native manual definition editing, exact ports, local save/reopen                                                                | No feature investment; existing behavior unchanged                                    |
| Existing EPP binding/execution increments | Exact generic capability binding, durable runs, governed execution                                                              | New native documents never serialized or executed through Rivet                       |
| Separately approved migration             | Read-only import analysis, explicit conversion report, unsupported-feature diagnostics, copy-to-new identity, original retained | No in-place overwrite, execution of imported code, or automatic lossy conversion      |
| Retirement gate                           | Native equivalence and user-approved migration/rollback demonstrated                                                            | Remove legacy routes, editor bundle, bridge, and runtime only after separate approval |

No legacy or F02 import is included in the initial implementation. A fresh deterministic native example supplies the visual acceptance fixture. Disabling authoring removes its navigation/write actions, not user data. Older readers reject unsupported authored documents without modifying them. Database rollback must retain additive document storage; uninstall follows existing explicit data-retention choices.

## Alternatives considered

- **Continue patching Rivet**: rejected; contradicts the product direction and existing EPP approval.
- **Copy the prototype**: rejected; violates its evidence-only disposition and imports unapproved schema/runtime assumptions.
- **Native manual editor with a renderer adapter**: recommended; preserves Wright ownership while avoiding a custom low-level graph-interaction engine.
- **Editable JSON/YAML/DSL and LLM proposals immediately**: deferred; adds a second edit surface and unresolved studies/Apply scope.
- **Complete runtime and migration rewrite in this UI feature**: rejected; makes a small UI outcome depend on unrelated high-risk work and falsely implies execution authority.

## Approval and evidence gates

This draft does not unblock EPP-F06 or amend the roadmap. Its [current entry](../../docs/programs/engineering-process-platform/roadmap.json) depends on EPP-F04/F05 and decisions `DEC-P0-002`/`DEC-P0-004`. A native manual precursor needs an explicit human-approved split and exact scope/dependency amendment. The residual EPP-F06 dependencies and LLM studies remain in force.

Before product implementation, the exact approval subject must include this decision, the spec, bounded schema/examples, command/state/API contracts, storage migration and previous-reader analysis, dependency pin/review, and preregistered study protocol. A later implementation plan/tasks/analysis cannot self-approve these choices. No committed approval/evidence/readiness record is rewritten by this planning work.

The study protocol must freeze five independent non-author participants, tasks, scoring, recovery injections, and the spec's thresholds before implementation. Compare trace/comprehension with equivalent static canonical definitions; do not compare authoring speed against a read-only baseline. The approved image is an appearance reference only. Human study results, exact-port/rename/round-trip/invalid-edit tests, two-writer/lost-response/interrupted-save tests, accessibility, native/Docker persistence, and independent review are future evidence, not completed claims.

The plan should prioritize pure model/command/component tests and one small real-browser acceptance journey. Broad packaging/release suites run only at their appropriate candidate gate; no repeated full-suite or multi-renderer bakeoff is justified by this proposal.
