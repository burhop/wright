# Atomic Workflow Command and Proposal Protocol

## Command batch

```json
{
  "command_batch_id": "batch.add-manufacturability",
  "workflow_id": "workflow.mounting-bracket",
  "base_revision": 3,
  "source": "ai_proposal",
  "commands": []
}
```

Supported semantic command families are:

- add, update, and remove block;
- add, update, and remove port;
- connect and disconnect relationship;
- add, update, and remove phase, gate/decision outcome, feedback path, artifact contract, binding, and component instance;
- update instructions and configuration.

These families define the promotion contract for the complete IR; they are not
all claimed as interactive controls in this disposable concept. The recovery
implementation exercises one bounded, fail-closed subset through the shared
command boundary:

- add, update, and remove blocks;
- connect, disconnect, relabel, redirect, and condition relationships;
- update block instructions and configuration;
- update port requiredness and cardinality; and
- update an existing binding's exact tool identity.

The JSON, YAML, and DSL projections still round-trip every phase, block, port,
relationship, artifact contract, binding, and component instance losslessly.
Code edits outside the implemented command subset are rejected as unsupported
and preserve the last-valid definition. Adding/removing ports, phases, artifact
contracts, bindings, or component instances remains a post-approval promotion
task; no UI path is allowed to mutate those structures by bypassing commands.

Layout move/resize/collapse commands use a separate layout batch and never appear in a semantic batch.

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

- Base mismatch returns `WFR-REVISION-STALE` with current/base identities and a regenerate/rebase correction.
- Two candidates from the same base may be previewed, but only the first explicit accepted save can advance that base.
- Undo/redo is a local stack of previously accepted in-memory states until save; it does not rewrite immutable stored revisions.

## Audit facts

Accepted change records retain command batch ID, source, base/new revision, semantic diff digest, user acceptance fact, and proposal ID when applicable. They do not log secrets or full proprietary payloads.
