# Human Program-Plan Approval Gate

## Current V8 EPP-F01 decision

**Approved with conditions.** [`APR-EPP-F01-MC-008`](evidence/approvals/APR-EPP-F01-MC-008.json) and [`APR-EPP-F01-IMPL-008`](evidence/approvals/APR-EPP-F01-IMPL-008.json) bind commit `c12eb00308cb72d96977846c4ae876dc0baa7e7e`, tree `7323b292d279fde752004bc744a2db850ab670d0`, program tree `18e3d4ad3f33e244b1f9145b55b27f4e02d4b54b`, and all 34 TR-0051 digests. They accept DEC-P0-019 and authorize the exact V8 six-target boundary.

Lease revision 12 is limited to local T073–T076. It does not authorize T066; the separately recorded roadmap-policy inversion test requires separate disposition. It also excludes T067–T068, product/EPP-F01B implementation, dependencies, benchmark generation/execution, external changes, push/PR/merge/dev integration, publication, and release. Older V7 approval remains historical for T070–T071 and cannot be replayed.

The approval records are append-only and reference the previously frozen subject, avoiding self-reference.

## Current decision

**Approved.** [`APR-EPP-2026-001`](evidence/approvals/APR-EPP-2026-001.json) records the human decision made on 2026-08-26 for the exact subject below. The approval has no added conditions and is limited by its `program_plan` scope and the authorization boundaries in this document.

## Historical V7 EPP-F01 decision — exhausted

**Historical only.** `APR-EPP-F01-MC-007` and `APR-EPP-F01-IMPL-007` bound the exact V7 subject and accepted DEC-P0-018. T070–T071 completed under that authority; T072 failed closed.

Lease revision 11 is closed. Its remaining T072/T066 authority is exhausted and non-replayable. T066–T068 and every product, EPP-F01B, dependency, benchmark, external, integration, publication and release action remain blocked.

## Historical EPP-F01 decision — stale

**No longer current; it grants no present implementation authority.** [`APR-EPP-F01-MC-001`](evidence/approvals/APR-EPP-F01-MC-001.json) and [`APR-EPP-F01-IMPL-001`](evidence/approvals/APR-EPP-F01-IMPL-001.json) historically recorded separate `material_change` and `feature_implementation` decisions for commit `5279c51740a0352961c92a70bce9003923d8ca20`, repository tree `7e2eb93a9faed14b609075b72373a473a22fdbff`, program tree `8b6d5d6b3b0341f952e30c065b8dd289b9735213`, and the 21 artifact digests in `TR-0014`. DEC-P0-013/014 and the amended planning subject made both approvals stale.

The v1 and v3 bundles are stale. V4 remains historical evidence for T069; V5 for T024–T041; V6 for T042–T065 and the failed first T066 attempt; V7 for completed T070–T071 only. None authorizes V8 implementation or T066. EPP-F01B implementation, dependencies, product runtime changes, benchmark collection or execution, network or external mutation, push, PR, merge, dev integration, publication, and release remain unauthorized.

## Approval subject

After the V8 planning commit is created and planning JSON/schema/consistency checks plus bounded independent audit are green, resolve and present the exact subject below. The pre-V8 validator is expected to fail closed on the unsupported three-claim profile; implementation/regression success must not be claimed before T073–T076 receive approval and execute.

```powershell
git rev-parse HEAD
git rev-parse HEAD^{tree}
git rev-parse HEAD:docs/programs/engineering-process-platform
```

For V8, use TR-0051's sorted 34-output digest manifest as the exact non-self-referential artifact bundle; the transition blob itself is bound by the enclosing Git commit/tree. The bootstrap manifest remains historical. The approval must bind:

- Git commit;
- repository tree;
- program-directory Git tree;
- per-file SHA-256 manifest;
- program ID/schema versions;
- decision (`approved`, `approved_with_conditions`, `rejected`, or revision requested);
- approver identity, timestamp, scope and conditions.

Approval of one subject does not approve later edits. Any material change or digest mismatch makes the approval stale. The approval record itself is committed in a later transition and references the already-fixed planning subject; this avoids a self-referential digest.

## Meaning of approval

Approval authorizes only transition from `AWAITING_PROGRAM_APPROVAL` to `PROGRAM_APPROVED` and selection/specification of the first dependency-eligible child feature under this control plane. It does not itself authorize product code, dependencies, external writes, benchmark generation, paid/proprietary/credentialed activity, dev integration or release unless the approval conditions explicitly say so.

The twelve visible P0 decisions in `decision-register.json` may remain deliberately open after program-plan approval because each names an owner and blocks its earliest affected feature/gate. Approval must not be interpreted as silently choosing any option. If the human wants a P0 choice settled as part of plan approval, the resulting ADR and register update require a new exact subject.

## Review checklist

- Objective, scope, precedence and prototype read-only boundary are acceptable.
- Four readiness areas are independent and release uses logical AND.
- Child feature sequence, WIP, worktrees, autonomy and repair/stop rules are acceptable.
- Spec Kit state machine and evidence requirements are acceptable.
- Product and commercial gates are sufficient.
- Benchmark sampling, holdout, lifecycle, coverage, oracles, artifacts, attempts and dashboard rules are sufficient as proposed.
- All four independent audit findings are dispositioned.
- All material P0 questions are visible, owned and blocking the right future transition.
- First five proposed Spec Kit features are small enough and independently shippable.
- No current artifact implies implementation/external/release authorization.

## Valid responses

- Approve the exact subject.
- Approve with explicit conditions tied to the exact subject.
- Request named revisions (`revision_requested`); state returns to `PLAN_DRAFT` and all downstream candidate digests are invalidated.
- Reject/stop.

The original program-plan approval remains recorded. Current EPP-F01 action is exclusively the exact V8 approval gate above; no implementation or external action is implied.
