# Data Model: Visual Workflow Composition Foundation

## Workflow Draft Envelope

| Field | Rule |
|---|---|
| `document_kind` | Literal `workflow-draft`; prevents confusion with released definitions. |
| `schema_version` | Literal `1.0.0-draft.1` for this slice. |
| `draft_id` | Stable bounded identifier assigned once by the server. |
| `revision` | Positive server-assigned integer, increasing by one per successful save. |
| `semantic_sha256` | Canonical digest of semantic content only. |
| `layout_sha256` | Canonical digest of layout only. |
| `semantic` | Canonical authoring concepts below. |
| `layout` | Replaceable integer-grid presentation state keyed by semantic IDs. |

## Semantic entities

- **Phase**: `id`, `name`, `purpose`, `order`, `block_ids`. Each block belongs to exactly one phase.
- **Workflow Block**: `id`, `title`, `purpose`, `role`, `phase_id`, `input_port_ids`, `output_port_ids`, `gate_ids`, `intended_artifact_ids`.
- **Typed Port**: `id`, `owner_block_id`, `direction`, `name`, `value_type_id`, `required`, `cardinality`. Each port has exactly one owner.
- **Connection**: `id`, `source_port_id`, `target_port_id`. Source is output, target is input, value types match exactly, and duplicate endpoint pairs are invalid.
- **Gate**: `id`, `owner_block_id`, `condition`, `proceed_target_block_id`, `revise_target_block_id`, `feedback_path_id`.
- **Feedback Path**: `id`, `from_gate_id`, `to_block_id`, `reason`. It reciprocally matches the gate's revise target.
- **Intended Artifact**: `id`, `title`, `artifact_type_id`, `description`, `produced_by_block_id`. It declares an expectation only.

All semantic IDs are globally unique within a draft and are never derived from labels or positions.

## Layout entities

- **Layout**: `schema_version`, ordered `positions`.
- **Block Position**: `semantic_id`, integer `x`, integer `y`; exactly one row for each block and no row for non-block concepts.

Selection, viewport, panel state, drag previews, and invalid form values are not persisted.

## Persistence entities

- **Draft Head**: one row per `draft_id`, identifying current revision and digests.
- **Draft Revision**: immutable row keyed by (`draft_id`, `revision`) with canonical envelope bytes and digests.

One SQLite transaction inserts the new revision and advances the head with `WHERE current_revision = expected_revision`. A stale expectation returns a conflict. Any validation, transaction, or I/O failure preserves the prior head.

## State transitions

```text
empty candidate -> valid unsaved working draft -> saved revision N
saved revision N -> valid unsaved working draft -> saved revision N+1
saved revision N -> invalid candidate intent -> saved revision N unchanged
saved revision N -> failed/stale save -> saved revision N unchanged
saved revision N -> close -> reopen revision N
```

There is no released, approved, executable, running, or published transition in this feature.

## Validation diagnostics

`code`, `path`, `affected_semantic_ids`, `explanation`, and `correction`. Codes are stable and content-safe; source data, filesystem paths, credentials, and draft bodies are never logged or returned in diagnostics.
