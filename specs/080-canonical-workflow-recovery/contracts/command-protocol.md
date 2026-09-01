# Atomic Workflow Command and Proposal Protocol

## Command batch

```json
{
  "document_kind": "workflow-command-batch",
  "schema_version": "1.0.0-recovery.1",
  "base_revision": 3,
  "origin": "ai_proposal",
  "commands": [
    {
      "kind": "set_block_title",
      "block_id": "block.generate-geometry",
      "title": "Generate manufacturable bracket geometry"
    }
  ]
}
```

This is the closed, portable snake_case recovery envelope implemented by the
Python conformance slice and validated by
`workflow-command-batch.schema.json`. The workflow subject is the accepted
definition passed to `apply`; `base_revision` binds the batch to that subject.
Unknown root, command, or nested fields fail closed.

| Document kind | Supported version | Unknown-version behavior |
|---|---|---|
| `workflow-command-batch` | `1.0.0-recovery.1` | Return `WFR-COMMAND-VERSION-UNSUPPORTED`, preserve the definition, layout, and original batch unchanged, and require an explicitly compatible reader. |

The portable subset is exactly: set block title/configuration scalar, set port
requiredness/cardinality, set binding tool identity, set relationship
condition, connect, and disconnect. TypeScript uses an ergonomic camelCase host
representation and a tested local extension for add/delete block,
relabel/redirect relationship, layout-only move, and validated undo/redo
snapshot restoration. Those host-only commands are not represented as if they
were proven portable wire commands.

The JSON, YAML, and DSL projections still round-trip every phase, block, port,
relationship, artifact contract, binding, and component instance losslessly.
Code edits outside the implemented command subset are rejected as unsupported
and preserve the last-valid definition. Adding/removing ports, phases, artifact
contracts, bindings, or component instances remains a post-approval promotion
task; no UI path is allowed to mutate those structures by bypassing commands.

The host-only block move updates the separately versioned layout document.
A batch containing both a move and a semantic command fails with
`WFR-COMMAND-MIXED-CONTAINMENT`; accepting a move-only batch advances
`layout_revision` without changing canonical definition bytes or semantic
digest. Resize and collapse are not implemented by this recovery contract.

Every command names stable target identities and all values needed for deterministic application. The kernel never invents IDs for AI; manual UI may request an ID from the host before constructing the command.

## Candidate result

A valid batch returns an unaccepted candidate and semantic diff. Acceptance belongs to the host/repository and must compare the same base revision again before assigning the next revision.

An invalid batch returns diagnostics and no candidate. Partial success is forbidden.

## AI proposal envelope

```text
proposal_id
workflow_id
base_revision
request_summary
assumptions[]
warnings[]
rationale
command_batch
validation
semantic_diff
preview_projection_digest
```

AI can create the envelope only. It cannot call accept, invoke a binding, mark an approval, or execute a run. The UI must provide explicit Preview, Accept, and Reject actions; Reject is always non-mutating.

## Concurrency

- Base mismatch returns `WFR-COMMAND-STALE-BASE` with current/base identities and a regenerate/rebase correction.
- Two candidates from the same base may be previewed, but only the first explicit accepted save can advance that base.
- Undo/redo is a TypeScript-host local stack of previously accepted in-memory states until save;
  each action is applied as one isolated `restore_snapshot` command with
  host-only `origin: history`, then the complete restored definition and layout are
  validated through the same fail-closed boundary. A history command cannot be
  mixed with any other command and does not rewrite immutable stored revisions.

## Audit facts

Future promoted accepted change records would retain durable batch ID, origin, workflow
identity, base/new revision, semantic diff digest, user acceptance fact, and
proposal ID when applicable. Those audit facts wrap the bounded recovery batch;
they do not alter its versioned shape and do not log secrets or full proprietary
payloads.
