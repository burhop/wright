# Phase 1 Data Model: Engineering Workflow Prototype

## Modeling rule

The Wright workflow specification is the only canonical product model. Canvas libraries project this model and emit Wright commands; they do not own persistence, execution semantics, validation, or revisions.

The prototype schema version is intentionally separate from Rivet project versions. No automatic migration to or from Rivet is in scope.

## Entity relationships

```text
Workflow 1 ── * Phase
Workflow 1 ── * Block  * ── 1 Phase
Workflow 1 ── * Connection
Block    1 ── * Port
Block    0 ── 1 McpBinding
Workflow 1 ── * Revision
Revision 1 ── * AuthoringProposal
Run      * ── 1 WorkflowRevision
Run      1 ── * StepResult
StepResult 1 ── * ArtifactReference
Run      1 ── * EvidenceEvent
Checkpoint 1 ── * EvidenceRecord
```

## Workflow

| Field           | Type             | Rules                                                        |
| --------------- | ---------------- | ------------------------------------------------------------ |
| `schemaVersion` | string           | Required; prototype version such as `0.1`.                   |
| `workflowId`    | stable ID        | Never derived from a display name.                           |
| `revision`      | positive integer | Incremented only when an accepted command changes the model. |
| `title`         | string           | Engineer-facing name.                                        |
| `purpose`       | string           | Concise outcome, not implementation detail.                  |
| `phases`        | ordered Phase[]  | At least one; order values unique.                           |
| `blocks`        | Block[]          | Each block references an existing phase.                     |
| `connections`   | Connection[]     | Endpoints and ports must exist and be compatible.            |
| `metadata`      | object           | Author, timestamps, tags, prototype fixture identifiers.     |

Invariant: parsing and validation produce either a fully valid canonical model or structured errors. Partially parsed models are never sent to a canvas or runtime.

## Phase

A phase is a semantic separator such as Define, Verify, or Manufacture. Templates can define different phases without changing code.

| Field         | Type         | Rules                                                                             |
| ------------- | ------------ | --------------------------------------------------------------------------------- |
| `phaseId`     | stable ID    | Unique within workflow.                                                           |
| `label`       | string       | Required; user editable.                                                          |
| `order`       | integer      | Unique and contiguous after normalization.                                        |
| `description` | string       | Optional outcome or entry/exit criteria.                                          |
| `colorToken`  | design token | Optional presentation hint from an approved palette; never raw execution meaning. |
| `collapsed`   | boolean      | View preference, excluded from semantic diff if stored separately.                |

## Block

Blocks use a small interaction-role vocabulary, not an engineering-domain taxonomy.

| Field          | Type                           | Rules                                                                                      |
| -------------- | ------------------------------ | ------------------------------------------------------------------------------------------ |
| `blockId`      | stable ID                      | Unique within workflow.                                                                    |
| `phaseId`      | Phase ID                       | Required.                                                                                  |
| `role`         | enum                           | `input`, `transform`, `mcp-action`, `decision`, `artifact`, `approval`, or `notification`. |
| `title`        | string                         | Engineer-facing action or noun.                                                            |
| `purpose`      | string                         | Plain-language expected outcome.                                                           |
| `instructions` | rich text/structured reference | Optional prompt or human instructions.                                                     |
| `ports`        | Port[]                         | Typed inputs and outputs.                                                                  |
| `position`     | `{x,y}`                        | Layout hint; validated finite numbers.                                                     |
| `size`         | optional dimensions            | Presentation hint only.                                                                    |
| `config`       | role-specific object           | Validated by role; cannot contain vendor-native canvas state.                              |
| `mcpBinding`   | optional McpBinding            | Allowed for `mcp-action`; validation rejects incompatible roles.                           |

The role controls visual grammar and generic behavior. “Create CAD model,” “Run FEA,” and “Request quote” may all be `mcp-action` blocks with different exact tool bindings and display labels.

## EngineeringCapabilityTemplate

A capability template makes a broad engineering catalog understandable without creating a runtime taxonomy.

| Field                | Type                      | Rules                                                               |
| -------------------- | ------------------------- | ------------------------------------------------------------------- |
| `capabilityId`       | stable ID                 | Organization-extensible presentation identity.                      |
| `categoryId`         | string                    | Search/filter metadata only; never an executor selector.            |
| `title`              | string                    | Engineer-facing name such as Parametric CAD or Structural FEA.      |
| `description`        | string                    | Outcome-oriented purpose.                                           |
| `keywords`           | string[]                  | Search synonyms such as CFD, fluids, or turbulence.                 |
| `expectedInputs`     | string/schema hints[]     | Helps authors understand and map required information.              |
| `expectedOutputs`    | string/schema hints[]     | Describes expected artifacts or result shapes.                      |
| `compatibilityQuery` | optional structured query | Narrows the generic workspace catalog without binding a tool.       |
| `catalogMatches`     | derived list/count        | Live or clearly labeled fixture data; never persisted as authority. |

Selecting a template creates an unbound `mcp-action` block. The block cannot run until the user reviews one exact catalog tool and its schema through `McpBinding`. Pinned and recent state is a user preference over template IDs, not a new service registry.

## Port

| Field          | Type                    | Rules                                                              |
| -------------- | ----------------------- | ------------------------------------------------------------------ |
| `portId`       | stable ID               | Unique within block.                                               |
| `direction`    | enum                    | `input` or `output`.                                               |
| `label`        | string                  | Plain-language name.                                               |
| `dataType`     | string/schema reference | Used for compatibility validation, not a fixed domain enumeration. |
| `required`     | boolean                 | Required input must be mapped before execution.                    |
| `multiplicity` | enum                    | `one` or `many`.                                                   |

## Connection

| Field          | Type                      | Rules                                                   |
| -------------- | ------------------------- | ------------------------------------------------------- |
| `connectionId` | stable ID                 | Unique within workflow.                                 |
| `source`       | block ID + output port ID | Must exist.                                             |
| `target`       | block ID + input port ID  | Must exist.                                             |
| `semantics`    | enum                      | `data`, `control`, or `feedback`.                       |
| `label`        | string                    | Optional condition or engineer-facing meaning.          |
| `condition`    | structured expression     | Optional; parsed by Wright, never by the canvas vendor. |

Invariants: no dangling endpoints, no output-to-output or input-to-input links, required multiplicity is enforced, and cycles are allowed only when explicitly marked as feedback or supported control behavior.

## McpBinding

An MCP binding captures reviewed catalog identity rather than a domain category.

| Field               | Type       | Rules                                                                            |
| ------------------- | ---------- | -------------------------------------------------------------------------------- |
| `serverId`          | catalog ID | Exact workspace-visible MCP server.                                              |
| `toolName`          | string     | Exact tool name.                                                                 |
| `qualifiedToolName` | string     | Stable server/tool identity where supplied by the catalog.                       |
| `serverRevision`    | string     | Exact reviewed server/catalog revision when available.                           |
| `inputSchemaDigest` | string     | Digest/version of the schema used for mapping.                                   |
| `argumentMappings`  | Mapping[]  | Each required tool argument is literal, port-derived, or an approved expression. |
| `outputMappings`    | Mapping[]  | Normalizes tool content/artifacts to output ports.                               |
| `approvalPolicy`    | reference  | Existing gateway policy identity; not locally reimplemented.                     |
| `presentationAlias` | string     | Optional friendly label with no dispatch semantics.                              |

Before every real call, the adapter compares the current catalog identity/schema with the binding. A mismatch produces a review-required state instead of best-effort invocation.

## AuthoringProposal and AuthoringCommand

| Field          | Type                | Rules                                                      |
| -------------- | ------------------- | ---------------------------------------------------------- |
| `proposalId`   | stable ID           | Unique.                                                    |
| `workflowId`   | stable ID           | Must match open workflow.                                  |
| `baseRevision` | integer             | Must equal the currently accepted revision.                |
| `summary`      | string              | Human-readable intent.                                     |
| `commands`     | AuthoringCommand[]  | Ordered, atomic, bounded set.                              |
| `assumptions`  | string[]            | Shown before acceptance.                                   |
| `warnings`     | structured errors[] | Validation and policy findings.                            |
| `status`       | enum                | `proposed`, `invalid`, `accepted`, `rejected`, or `stale`. |

Commands include phase/block/connection CRUD, exact MCP binding, argument mapping, and layout hints. Commands cannot invoke an MCP tool, mutate run history, bypass approval, or contain canvas-vendor objects.

Proposal application is transactional: apply every command to a copy, validate the complete result, compute a semantic diff, and accept all or none.

## Run, StepResult, ArtifactReference, EvidenceEvent

The prototype reuses the meanings already proven by Wright's governed runtime rather than inventing domain results.

| Entity            | Core fields                                                               | Notes                                                           |
| ----------------- | ------------------------------------------------------------------------- | --------------------------------------------------------------- |
| Run               | run ID, workflow ID/revision, status, timestamps                          | Immutable workflow revision reference.                          |
| StepResult        | block ID, status, normalized outputs, error, duration                     | UI tolerates absent historical optional fields.                 |
| ArtifactReference | artifact ID, media type, name, URI/vault reference, provenance            | STEP/DXF/reports are examples, not schema categories.           |
| EvidenceEvent     | event type, actor/provider, request/response digest, approval, timestamps | Produced by governed boundaries and displayed by the prototype. |

## CandidateCanvasAdapter

The adapter is deliberately not persisted.

```ts
interface CandidateCanvasAdapter {
  render(model: Readonly<Workflow>, selection: Selection): CanvasProjection;
  translate(
    event: CandidateEvent,
    model: Readonly<Workflow>,
  ): WorkflowCommand | ViewCommand;
  fitView(): void;
  focusBlock(blockId: string): void;
  dispose(): void;
}
```

`CanvasProjection` is disposable. The adapter must not mutate the workflow, execute blocks, call MCP, or expose vendor serialization as application state.

## CheckpointEvidence

| Field               | Type            | Rules                                                     |
| ------------------- | --------------- | --------------------------------------------------------- |
| `checkpointId`      | enum/string     | CP0 through CP7.                                          |
| `commit`            | Git commit      | Exact reviewed source.                                    |
| `hypothesis`        | string          | What uncertainty the checkpoint tests.                    |
| `acceptanceResults` | structured list | Criterion, result, evidence link, notes.                  |
| `testRuns`          | structured list | Command, duration, environment, pass/fail, failure class. |
| `screenshots`       | references      | Required for visual checkpoints.                          |
| `decision`          | enum            | `continue`, `change`, `stop`, or `defer`.                 |
| `reviewer`          | string          | Human approval required at major checkpoints.             |
| `followUps`         | list            | Bounded next work, not an unreviewed backlog expansion.   |
