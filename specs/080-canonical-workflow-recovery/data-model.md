# Data Model: Canonical Workflow Recovery

## Authority map

| Record | Owns | Must never own |
|---|---|---|
| Canonical workflow definition | Semantic engineering intent, stable identities, contracts, conditions, configuration, bindings | Position, viewport, selection, proposal state, execution state, produced files |
| Layout document | Stable-ID-keyed positions, sizes, collapsed state, optional grouping and viewport hints | Semantic order, conditions, bindings, run state |
| Candidate/proposal | Unaccepted commands, diagnostics, assumptions, warnings, semantic diff, preview | Accepted revision or execution authority |
| Immutable run record | Exact accepted definition revision, execution mode, timestamps, terminal state | Definition mutation or current editor layout |
| Step/activity record | Per-block inputs, outputs, activity, diagnosis, timing, causal evidence | Workflow definition or inferred causal claims without run evidence |
| Artifact record | Actual file/value identity, producer, lineage, lifetime, allowed actions | Intended artifact contract or connection handle |

## Canonical workflow definition

The recovery contract is `document_kind: workflow-ir` and `schema_version: 2.0.0-recovery.1`. It is a concept contract, not an approved production migration target.

### Workflow envelope

| Field | Rule |
|---|---|
| `workflow_id` | Stable global workflow identity. |
| `revision` | Positive accepted revision; candidates carry the base revision separately and cannot assign it. |
| `parent_revision` | Previous accepted revision or null for the first revision. |
| `semantic_sha256` | Digest of canonical definition bytes only. |
| `metadata` | Title, purpose, engineering domain, authorship/provenance labels, created/updated facts. |
| `phases` | Optional ordered grouping; blocks remain primary. |
| `blocks` | Engineering work, decisions, approvals, or reusable component instances. |
| `ports` | Stable typed input/output contracts. |
| `relationships` | Data, control, decision, and feedback relationships. |
| `artifact_contracts` | Intended inputs/outputs, not produced files. |
| `bindings` | Exact implementation/tool identities and argument/result mappings. |
| `components` | Reusable subgraph definitions and version constraints. |

### Phase

`id`, `name`, `purpose`, `order`, and `block_ids`. A phase is optional presentation-supporting semantics; it cannot be the only way to navigate or understand flow.

### Block

| Field | Meaning |
|---|---|
| `id` | Stable semantic identity. |
| `kind` | `work`, `decision`, `approval`, or `component`. |
| `title`, `purpose` | Friendly engineering language. |
| `phase_id` | Optional group identity. |
| `execution_kind` | `deterministic`, `ai_capable`, or `human`. |
| `instructions` | Bounded intent/instructions independent of a vendor renderer. |
| `configuration` | Closed JSON-compatible values governed by the block contract. |
| `input_port_ids`, `output_port_ids` | Reciprocal typed ports. |
| `binding_id` | Optional exact executable binding. Human/structural blocks may omit it. |
| `component_ref` | Optional reusable component identity and compatible version range. |

### Typed port

`id`, `owner_block_id`, `direction`, `name`, `type_id`, `required`, `cardinality`, `artifact_contract_id`, and optional `description`. `cardinality` is `one`, `optional`, or `many`. Connection handles use the port identity; artifact inspection uses a separate control bound to the artifact contract or runtime artifact.

### Relationship

| Kind | Endpoints | Extra rule |
|---|---|---|
| `data` | output port → input port | Type/cardinality compatible; carries a value/artifact reference during a run. |
| `control` | block → block | Orders eligibility without carrying an artifact. |
| `decision` | decision/approval block → block | Has a named outcome and condition. |
| `feedback` | decision/approval block → earlier block/component | Has a named reason and visible non-color line treatment. |

All relationships have `id`, `kind`, endpoints, label, and optional condition. Cycles are invalid unless every back edge is explicitly `feedback`.

### Artifact contract

`id`, `name`, `type_id`, `media_type`, `description`, `producer_block_id`, `required_for_block_ids`, preview policy, and allowed conceptual actions. It states intent only; an `ArtifactRecord` states an actual value/file.

### Binding

| Field | Rule |
|---|---|
| `id` | Stable binding identity. |
| `kind` | `internal`, `mcp_tool`, or `human`. |
| `provider_id`, `server_id`, `tool_id` | Exact identities; required as applicable. |
| `schema_digest` | Exact reviewed input/output contract identity. |
| `argument_map` | Port/config semantic source → exact argument target. |
| `result_map` | Exact result source → port/artifact semantic target. |
| `approval_policy` | Required authority before invocation or external mutation. |
| `capability_metadata` | Friendly catalog/search metadata that cannot replace exact binding identity. |

### Reusable component

`id`, `version`, `title`, `input_interface`, `output_interface`, `internal_definition_digest`, and compatibility constraints. A component instance retains internal stable addresses for diagnostics and historical run lineage even when collapsed.

## Layout document

`document_kind: workflow-layout`, independently versioned, with `workflow_id`, `semantic_revision`, `layout_revision`, `layout_sha256`, `items`, and optional viewport hints. Each item has `semantic_id`, integer `x/y`, bounded `width/height`, and `collapsed`. Unknown semantic IDs fail validation; missing new IDs receive deterministic default placement without changing definition bytes.

## Command batch

`command_batch_id`, `workflow_id`, `base_revision`, `source` (`graph`, `form`, `text`, `ai_proposal`), and ordered closed commands. Commands cover add/remove/update/move-independent semantic concepts, connect/disconnect, component operations, configuration, and binding. Layout commands are a separate batch and cannot be mixed with semantic commands.

Application is all-or-none:

```text
accepted revision N + commands(base=N)
  -> clone
  -> apply every command
  -> validate complete candidate
  -> invalid: return diagnostics, preserve N
  -> valid: return candidate + semantic diff (still unaccepted)
  -> explicit accept/save: assign N+1 with parent N
```

## AI proposal

`proposal_id`, `workflow_id`, `base_revision`, `request_summary`, assumptions, warnings, rationale, command batch, validation result, semantic diff, and preview projection identity. The proposal cannot assign a revision, invoke a binding, satisfy approval, or accept itself.

## Diagnostics and source maps

A diagnostic contains `code`, `severity`, `semantic_ids`, optional `{start_line,start_column,end_line,end_column}`, explanation, and correction. Stable codes identify rules; source spans identify the current text occurrence; semantic IDs preserve identity after formatting.

## Immutable execution records

### Run record

`run_id`, `workflow_id`, `workflow_revision`, `semantic_sha256`, `mode`, `requested_by`, `created_at`, and terminal state facts. States are `queued`, `running`, `needs_input`, `succeeded`, `failed`, `blocked`, `cancelled`, or `stale`. State changes are append-only events; a projection may summarize them without rewriting definition data.

### Step record

`step_id`, `run_id`, `block_id`, attempt, state events, start/end facts, input record IDs, output record IDs, diagnosis codes, and causal evidence. Every executable block can project Inputs, Outputs, Activity, and Diagnosis.

### Activity record

Append-only timestamped `registered`, `connected`, `first_event`, `first_output`, `progress`, `needs_input`, `resumed`, `cancel_requested`, `terminal`, and `cleanup` events with bounded human-readable summary and technical evidence reference.

### Artifact record

`artifact_id`, `run_id`, `step_id`, `contract_id`, `type_id`, media type, digest, size, producer, upstream artifact IDs, storage reference, preview state, allowed actions, lifetime/expiry, and cleanup state.

## Versioning and migration

- Every document kind owns its version independently.
- Readers support an explicit version set; unknown versions are preserved byte-for-byte and never silently rewritten.
- Compatible migrations are pure, deterministic, idempotent functions with before/after digests and a reversible or explicit one-way policy.
- Historical run records continue to reference the original definition revision/digest even after a definition migration.
- The recovery version has no production migration. Promotion requires a superseding accepted ADR and fixtures proving prior-draft and historical-run behavior.

## Required invariants

1. Canonical IDs are unique and references reciprocal.
2. Port direction, type, requiredness, and cardinality are valid.
3. Only explicit feedback relationships create semantic back edges.
4. Exact bindings resolve every required argument/result map before execution.
5. `parse(format(IR))` is semantic equality.
6. Graph and text edits preserve every untouched semantic fact.
7. Invalid candidates preserve the exact accepted revision object/bytes.
8. Layout changes preserve semantic bytes and digest.
9. Proposal reject preserves revision; proposal accept uses current base revision once.
10. Run/activity/artifact changes preserve definition and layout bytes.

