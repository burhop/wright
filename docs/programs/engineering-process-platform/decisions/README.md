# Decision-record process

The machine-readable inventory is [`../decision-register.json`](../decision-register.json). P0 questions may remain open only when they are visible, owned, and block an explicit future gate. They are never answered by prototype behavior, benchmark outcomes, task completion, or coordinator preference.

For each material decision:

1. Create `decisions/NNNN-short-name.md` before the `due_before` state.
2. Record ID, status, date, owner/approver, context, decision drivers, considered options, evidence, decision, consequences, compatibility/rollback, affected gates/roadmap/risks, review/expiry, and superseded records.
3. Bind the decision to exact artifact/commit/tree/evidence digests and a human approval.
4. Update the decision register, risks, gates, roadmap, state, dashboard, and invalidated approvals/evidence in the same change.
5. Return affected child work to the earliest impacted Spec Kit state and rerun downstream analysis.

An ADR can be `proposed`, `accepted`, `rejected`, `superseded`, or `deferred`. Deferred P0 decisions still block their listed transitions. Reversal requires a superseding record; history is never rewritten.

## Minimum ADR template

```markdown
# ADR NNNN: Title

- Decision ID:
- Status:
- Date:
- Owner / human approver:
- Exact subject and evidence digests:
- Decision due gate:

## Context and claims affected
## Decision drivers
## Options considered
## Evidence and contradictions
## Decision
## Consequences and residual risks
## Compatibility, migration, rollback, and expiry
## Gate, roadmap, risk, and approval invalidation
```
