# Data Model: Canonical Workflow Recovery

## Authority map

| Record                        | Owns                                                                                                     | Must never own                                                                                  |
| ----------------------------- | -------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| Engineer workflow source      | One visible workspace-owned `.workflow.wflow` file using contextual engineering-script vocabulary        | Host revisions/digests, absolute paths, opaque canonical IDs, layout, proposal state, run state |
| Canonical workflow definition | Semantic engineering intent, stable identities, contracts, conditions, configuration, bindings           | Position, viewport, selection, proposal state, execution state, produced files                  |
| Workflow source metadata      | Workspace identity, safe relative path, storage revision/digest, accepted definition revision, byte size | Engineer-authored source semantics, layout, run state, second visible definition                |
| Layout document               | Stable-ID-keyed positions, sizes, collapsed state, optional grouping and viewport hints                  | Semantic order, conditions, bindings, run state                                                 |
| Candidate/proposal            | Unaccepted commands, diagnostics, assumptions, warnings, semantic diff, preview                          | Accepted revision or execution authority                                                        |
| Immutable run record          | Exact accepted definition revision, execution mode, timestamps, terminal state                           | Definition mutation or current editor layout                                                    |
| Step/activity record          | Per-block inputs, outputs, activity, diagnosis, timing, causal evidence                                  | Workflow definition or inferred causal claims without run evidence                              |
| Artifact record               | Actual file/value identity, producer, lineage, lifetime, allowed actions                                 | Intended artifact contract or connection handle                                                 |

## Engineer workflow source

The workspace exposes one visible UTF-8 file at
`workflows/<safe-slug>.workflow.wflow`. It is the engineer-owned authoring
artifact and uses contextual `workflow`, `input`, `task`, and optional `group`
constructs. It names prompts, files, design documents, engineering tasks,
tools, and outputs. It does not contain storage or definition revisions,
parents, semantic hashes, absolute paths, opaque `block.*`/`port.*`/`artifact.*`
identities, renderer nodes, or run records.

Entering **Workflows** in an active workspace is explicit intent to ensure this
default artifact exists. The default is a complete, prevalidated canonical
workflow source, not an empty placeholder. Create-if-absent is idempotent: the
first successful entry creates it, concurrent or later entries return the
existing source unchanged, and ordinary workspace entry creates nothing.

The source parser resolves contextual names against the exact accepted
canonical base and emits source spans plus a closed atomic command batch. A
supported edit is accepted only after the complete canonical candidate passes
validation. An unresolved structural addition, host-managed field, ambiguous
name, syntax error, or invalid candidate leaves the accepted canonical model
and stored file unchanged.

Groups are optional authoring organization. A task does not require a group
and a group does not constrain where its task may be reused or executed. The
nine-step acceptance fixture intentionally has no author-authored group.

## Workflow source metadata

The host keeps one hidden metadata record beside the workspace source history:

| Field                 | Rule                                                                                                                                                                 |
| --------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `workspace_id`        | Resolved from the active workspace session; never supplied as a filesystem path by the author.                                                                       |
| `path`                | Exact safe workspace-relative `workflows/<safe-slug>.workflow.wflow` path.                                                                                           |
| `storage_revision`    | Positive host-owned compare-and-set revision; advances once for changed stored bytes.                                                                                |
| `storage_digest`      | SHA-256 of the exact visible UTF-8 source bytes.                                                                                                                     |
| `definition_revision` | Positive host-owned accepted semantic revision; starts at 1 and advances once only when the trusted canonical application layer attests a validated semantic change. |
| `metadata_authority`  | Constant `wright_host`; never author-editable.                                                                                                                       |
| `size_bytes`          | Exact UTF-8 byte count, bounded to 1 MiB.                                                                                                                            |

State transitions are `missing -> Workflows bootstrap -> saved revision 1` and
`saved revision N -> changed local candidate -> saved revision N+1`. A plain
read never creates. A bootstrap against an existing path and a no-op save both
return the current bytes and identity without advancing them. A stale revision
or digest returns conflict with the current stored identity while preserving
both the stored bytes and the caller's local candidate. Path,
symlink/reparse, extension, encoding, size, or atomic-replace failures occur
before the visible file is committed.

## Canonical workflow definition

The recovery contract is `document_kind: workflow-ir` and `schema_version: 2.0.0-recovery.1`. It is a concept contract, not an approved production migration target.

### Workflow envelope

| Field                | Rule                                                                                            |
| -------------------- | ----------------------------------------------------------------------------------------------- |
| `workflow_id`        | Stable global workflow identity.                                                                |
| `revision`           | Positive accepted revision; candidates carry the base revision separately and cannot assign it. |
| `parent_revision`    | Previous accepted revision or null for the first revision.                                      |
| `semantic_sha256`    | Digest of canonical definition bytes only.                                                      |
| `metadata`           | Title, purpose, engineering domain, authorship/provenance labels, created/updated facts.        |
| `phases`             | Optional ordered grouping; blocks remain primary.                                               |
| `blocks`             | Engineering work, decisions, approvals, or reusable component instances.                        |
| `ports`              | Stable typed input/output contracts.                                                            |
| `relationships`      | Data, control, decision, and feedback relationships.                                            |
| `artifact_contracts` | Intended inputs/outputs, not produced files.                                                    |
| `bindings`           | Exact implementation/tool identities and argument/result mappings.                              |
| `components`         | Reusable subgraph definitions and version constraints.                                          |

### Optional internal group (`phase` on the canonical wire)

`id`, `name`, `purpose`, `order`, and `block_ids`. This is optional
organization in the canonical model. It cannot be the only way to navigate or
understand flow, does not have to appear in the authoring source, and does not
restrict a block to one engineering context.

### Block

| Field                               | Meaning                                                                 |
| ----------------------------------- | ----------------------------------------------------------------------- |
| `id`                                | Stable semantic identity.                                               |
| `kind`                              | `work`, `decision`, `approval`, or `component`.                         |
| `title`, `purpose`                  | Friendly engineering language.                                          |
| `phase_id`                          | Optional internal group identity; absent for ungrouped tasks.           |
| `execution_kind`                    | `deterministic`, `ai_capable`, or `human`.                              |
| `instructions`                      | Bounded intent/instructions independent of a vendor renderer.           |
| `configuration`                     | Closed JSON-compatible values governed by the block contract.           |
| `input_port_ids`, `output_port_ids` | Reciprocal typed ports.                                                 |
| `binding_id`                        | Optional exact executable binding. Human/structural blocks may omit it. |
| `component_ref`                     | Optional reusable component identity and compatible version range.      |

### Typed port

`id`, `owner_block_id`, `direction`, `name`, `type_id`, `required`, `cardinality`, `artifact_contract_id`, and optional `description`. `cardinality` is `one`, `optional`, or `many`. Connection handles use the port identity; artifact inspection uses a separate control bound to the artifact contract or runtime artifact.

### Relationship

| Kind       | Endpoints                                         | Extra rule                                                                    |
| ---------- | ------------------------------------------------- | ----------------------------------------------------------------------------- |
| `data`     | output port → input port                          | Type/cardinality compatible; carries a value/artifact reference during a run. |
| `control`  | block → block                                     | Orders eligibility without carrying an artifact.                              |
| `decision` | decision/approval block → block                   | Has a named outcome and condition.                                            |
| `feedback` | decision/approval block → earlier block/component | Has a named reason and visible non-color line treatment.                      |

All relationships have `id`, `kind`, endpoints, label, and optional condition. Cycles are invalid unless every back edge is explicitly `feedback`.

### Artifact contract

`id`, `name`, `type_id`, `media_type`, `description`, `producer_block_id`, `required_for_block_ids`, preview policy, and allowed conceptual actions. It states intent only; an `ArtifactRecord` states an actual value/file.

### Binding

| Field                                 | Rule                                                                      |
| ------------------------------------- | ------------------------------------------------------------------------- |
| `id`                                  | Stable binding identity.                                                  |
| `kind`                                | `internal`, `mcp_tool`, or `human`.                                       |
| `provider_id`, `server_id`, `tool_id` | Exact identities; required as applicable.                                 |
| `schema_digest`                       | Exact reviewed input/output contract identity.                            |
| `argument_map`                        | Port/config semantic source → exact argument target.                      |
| `result_map`                          | Exact result source → port/artifact semantic target.                      |
| `approval_policy`                     | Required authority before invocation or external mutation.                |
| `capability_name`                     | Friendly catalog/search label that cannot replace exact binding identity. |

### Reusable component

`id`, `version`, `title`, `input_port_ids`, `output_port_ids`,
`internal_definition_digest`, and a non-empty `internal_addresses` array. Each
address has `semantic_id`, `concept_kind`, and `relative_path`. Semantic IDs and
paths are unique within the component, the semantic ID is prefixed by the
component ID, and the path begins with the matching definition collection
(`blocks/`, `ports/`, `relationships/`, `artifact-contracts/`, `bindings/`, or
`components/`) without `.` or `..` traversal. Run paths never appear in the
definition address map.

A collapsed instance resolves an internal identity using this scope tuple:

```text
(component_instance_id, component_id, component_version, internal_semantic_id)
```

Diagnostics and immutable run-step lineage may therefore refer to the same
internal semantic concept without expanding the component or embedding runtime
state in the canonical definition.

## Layout document

The bounded recovery layout is `document_kind: workflow-layout` and
`schema_version: 1.0.0-recovery.1`, with `workflow_id`,
`semantic_revision`, `layout_revision`, a stable-ID-keyed `positions` map, and
`viewport {x,y,zoom}`. The JSON schema uses snake_case wire names; the
TypeScript adapter exposes equivalent camelCase properties. Unknown semantic
IDs fail with `WFR-LAYOUT-IDENTITY-UNKNOWN`; workflow/revision mismatch fails
with `WFR-LAYOUT-SUBJECT-MISMATCH`; an unsupported kind/version fails with
`WFR-LAYOUT-VERSION-UNSUPPORTED` before projection. All three failures preserve
the input document unchanged. Missing new block IDs receive deterministic
default placement without changing definition bytes.

## Command batch

The bounded portable recovery wire is `document_kind: workflow-command-batch`,
`schema_version: 1.0.0-recovery.1`, `base_revision`, `origin` (`graph`, `form`,
`text`, or `ai_proposal`), and ordered closed commands. The accepted
workflow object supplied to `apply` is the batch subject. A future durable audit
envelope may add `command_batch_id` and `workflow_id`; those are not fields in
this closed recovery version.

The portable subset covers block title/configuration scalar updates, selected
port/binding updates, relationship-condition updates, connect, and disconnect.
The TypeScript camelCase host adds local add/delete block,
relabel/redirect-relationship, move, and history commands. A move-only batch
advances `layout_revision` without changing semantic bytes; a semantic+move
batch is rejected. A host history batch contains exactly one `restore_snapshot`
command and validates the full restored definition and layout before acceptance.

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

The bounded projection is `document_kind: workflow-run`,
`schema_version: 1.0.0-recovery.1`, `run_id`, `workflow_id`,
`workflow_revision`, `semantic_sha256`, timestamps, mode, active identities,
state, steps, activity, artifact records, and material/output flags. The strict
schema closes root and nested records. Unknown versions fail with
`WFR-RUN-VERSION-UNSUPPORTED`; a workflow/revision/digest mismatch fails with
`WFR-RUN-SUBJECT-MISMATCH`. The bounded wire states are `idle`, `queued`,
`running`, `needs-input`, `succeeded`, `failed`, `blocked`, or `stale`.
Cancellation is future durable-runtime work, not a recovery-wire claim. State changes are append-only events; a
projection may summarize them without rewriting definition data.

### Step record

`step_id`, `run_id`, `block_id`, attempt, state events, start/end facts, input record IDs, output record IDs, diagnosis codes, and causal evidence. Every executable block can project Inputs, Outputs, Activity, and Diagnosis.

### Activity record

Append-only timestamped `registered`, `connected`, `first_event`, `first_output`, `progress`, `needs_input`, `resumed`, `cancel_requested`, `terminal`, and `cleanup` events with bounded human-readable summary and technical evidence reference.

### Artifact record

`artifact_id`, `run_id`, `step_id`, `contract_id`, `type_id`, media type, digest, size, producer, upstream artifact IDs, storage reference, preview state, allowed actions, lifetime/expiry, and cleanup state.

## Versioning and migration

| Document/projection      | Recovery kind/version                                                            | Unknown-version behavior                                                                                  |
| ------------------------ | -------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| Canonical definition     | `workflow-ir` / `2.0.0-recovery.1`                                               | Schema rejection or DSL `WFR-TEXT-FIELD-ENUM:version`; preserve original bytes and last-valid definition. |
| Layout                   | `workflow-layout` / `1.0.0-recovery.1`                                           | `WFR-LAYOUT-VERSION-UNSUPPORTED`; do not project or rewrite.                                              |
| Command batch            | `workflow-command-batch` / `1.0.0-recovery.1`                                    | `WFR-COMMAND-VERSION-UNSUPPORTED`; do not execute or rewrite.                                             |
| Run projection           | `workflow-run` / `1.0.0-recovery.1`                                              | `WFR-RUN-VERSION-UNSUPPORTED`; do not render overlays or rewrite.                                         |
| Engineer workflow source | Contextual authoring grammar treatment `0.2`; version is host-managed            | Structured source diagnostic; retain the last-valid definition, stored bytes, and local draft.            |
| Internal IR projection   | Header `legacy recovery treatment 0.1`; root workflow version `2.0.0-recovery.1` | Developer/evidence diagnostic; never silently rewrite the engineer source.                                |

- Every document kind owns its version independently.
- Readers support an explicit version set; unknown versions are preserved byte-for-byte and never silently rewritten.
- Compatible migrations are pure, deterministic, idempotent functions with before/after digests and a reversible or explicit one-way policy.
- Historical run records continue to reference the original definition revision/digest even after a definition migration.
- ADR 0002 now supplies the required superseding production decision. It promotes
  recovery definition `2.0.0-recovery.1` to stable definition `2.0.0` and
  recovery command semantics to stable command batch `1.0.0`; source and target
  digests plus exact source bytes make the initial promotion rollbackable.
- ADR 0003 promotes recovery layout `1.0.0-recovery.1` to stable layout `1.0.0`
  with independent append-only revisions, semantic-revision binding, exact-byte
  rollback, and recoverable unknown-version reopen.
- ADR 0004 adopts stable `workflow-run` / `1.0.0` for new canonical execution
  records. Normalized run, step, activity, and artifact lineage persists in an
  independent sidecar with cancellation, cursor reconnect, and terminal cleanup.
- Historical recovery `workflow-run` / `1.0.0-recovery.1` envelopes remain
  exact immutable bytes bound to their original recovery definition
  revision/digest; they are not silently rewritten as stable-definition runs.

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
11. Every reusable component exposes a valid non-empty internal semantic address map; diagnostics and run lineage retain the same scoped internal identity.
12. Unsupported definition, layout, command, and run versions fail before mutation or projection and preserve their inputs unchanged.
13. Engineer source contains no host-managed revision/digest or opaque canonical identity. Stable lower-snake connection names and closed engineering kinds such as `design_intent`, `cad_model`, and `step_file` map losslessly to internal port/type contracts, and accepted source and diagram edits lower to the same canonical command semantics.
14. A workspace exposes one visible workflow definition file; hidden metadata, layout, proposals, runs, and outputs cannot become competing definition files.
15. Plain read and ordinary workspace entry never create; Workflows bootstrap creates the validated default only while absent and otherwise returns the existing bytes and identity unchanged; stale or failed saves preserve stored source and local unsaved source; a changed successful save advances storage and definition identity exactly once.
