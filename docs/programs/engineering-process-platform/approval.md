# Human Program-Plan Approval Gate

## Current V9 EPP-F01 decision

**Completed and consumed.** [`APR-EPP-F01-MC-009`](evidence/approvals/APR-EPP-F01-MC-009.json) and [`APR-EPP-F01-IMPL-009`](evidence/approvals/APR-EPP-F01-IMPL-009.json) bind commit `d96e8b68c9fda08eea84065186452581727ec4fa`, tree `d16d81afaabac73e4374ecb186089cb0a95dd1bc`, program tree `ee2fbf3b1a15920701289a083431f0afd41ed4ec`, and all 31 TR-0053 artifact digests. T077–T080 completed under lease revision 13 and passed the independent evidence recorded in `EPP-F01-V9.json`. The approval cannot be replayed for later work.

The consumed V9 lease was limited to local T077–T080 and exactly two claims in `COR-EPP-F01-V9-PREFLIGHT-EVIDENCE-001`: the exact external-schema binding for immutable `EPP-F01-V8-discovery.json`, and the exact TR-0051 complete-set/self-path-order disposition. It never authorized T073–T076, stashed T073 work, roadmap-policy repair, T066–T068, EPP-F01B, dependencies, benchmarks, external changes, push/open/merge/integration, publication, or release.

## Historical V8 EPP-F01 decision — interrupted

**Approved with conditions.** [`APR-EPP-F01-MC-008`](evidence/approvals/APR-EPP-F01-MC-008.json) and [`APR-EPP-F01-IMPL-008`](evidence/approvals/APR-EPP-F01-IMPL-008.json) bind commit `c12eb00308cb72d96977846c4ae876dc0baa7e7e`, tree `7323b292d279fde752004bc744a2db850ab670d0`, program tree `18e3d4ad3f33e244b1f9145b55b27f4e02d4b54b`, and all 34 TR-0051 digests. They accept DEC-P0-019 and authorize the exact V8 six-target boundary.

Lease revision 12 was limited to local T073–T076, but it is closed and non-replayable after the two new clean-subject preflight failures. No T073 implementation is part of the V9 subject. The separately recorded roadmap-policy inversion test, T066–T068, product/EPP-F01B implementation, dependencies, benchmark generation/execution, external changes, push/PR/merge/dev integration, publication, and release remain excluded.

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

After the V9 planning commit is created and planning JSON/schema/consistency checks plus bounded independent audit are green, resolve and present the exact subject below. The current validator is expected to fail closed on the unsupported two-claim profile; implementation/regression success must not be claimed before separately approved T077–T080 execute.

```powershell
git rev-parse HEAD
git rev-parse HEAD^{tree}
git rev-parse HEAD:docs/programs/engineering-process-platform
```

For V9, use TR-0053's sorted output digest manifest as the exact non-self-referential artifact bundle; the transition blob itself is bound by the enclosing Git commit/tree. The bootstrap and V8 manifests remain historical. The approval must bind:

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

The original program-plan approval remains recorded. Current EPP-F01 authority is exclusively the bounded V9 T077–T080 lease above; no other implementation or external action is implied.
