# Human Program-Plan Approval Gate

## Current decision

**Approved.** [`APR-EPP-2026-001`](evidence/approvals/APR-EPP-2026-001.json) records the human decision made on 2026-08-26 for the exact subject below. The approval has no added conditions and is limited by its `program_plan` scope and the authorization boundaries in this document.

## Current EPP-F01 decision

**Approved for the bounded V7 repair and one T066 retry.** `APR-EPP-F01-MC-007` and `APR-EPP-F01-IMPL-007` bind commit `a2b9727a15c445875b2ef857f482bee31ccc594c`, tree `ee16d103c98c3d891d32c45b243a131dd0745527`, program tree `677f1ec8e895b6330941f8ab5afe92c5dadf980b`, and the 31 artifact digests in TR-0046. They accept DEC-P0-018 and the exact closed two-claim correction.

Lease revision 11 authorizes only local T070 through T072 and, after a passing replacement freeze, one distinct independent T066 retry. T067–T068, product changes, EPP-F01B implementation, dependencies, benchmark execution, external changes, push/PR/merge/dev integration, publication, and release remain blocked.

## Historical EPP-F01 decision — stale

**No longer current; it grants no present implementation authority.** [`APR-EPP-F01-MC-001`](evidence/approvals/APR-EPP-F01-MC-001.json) and [`APR-EPP-F01-IMPL-001`](evidence/approvals/APR-EPP-F01-IMPL-001.json) historically recorded separate `material_change` and `feature_implementation` decisions for commit `5279c51740a0352961c92a70bce9003923d8ca20`, repository tree `7e2eb93a9faed14b609075b72373a473a22fdbff`, program tree `8b6d5d6b3b0341f952e30c065b8dd289b9735213`, and the 21 artifact digests in `TR-0014`. DEC-P0-013/014 and the amended planning subject made both approvals stale.

The v1 and v3 bundles are stale. V4 remains valid historical evidence for T069. V5 is complete historical authority for T024–T041. V6 is historical authority for completed T042–T065 and the failed first T066 attempt; it cannot authorize this material correction or another implementation attempt. Exact same-subject V7 `material_change` and `feature_implementation` approvals must accept DEC-P0-018 and the frozen two-claim profile before T070–T072 or T066 retry. EPP-F01B implementation, dependencies, product runtime changes, benchmark collection or execution, network or external mutation, push, PR, merge, dev integration, publication, and release remain unauthorized.

## Approval subject

After the planning commit is created and the planning JSON/schema/consistency checks plus bounded independent audit are green, resolve and present the exact subject below. The pre-V7 validator is expected to fail closed on the unsupported two-claim profile; that exact bounded failure must remain visible and must not be described as green before T070–T072 are separately approved and executed.

```powershell
git rev-parse HEAD
git rev-parse HEAD^{tree}
git rev-parse HEAD:docs/programs/engineering-process-platform
```

For the V7 feature amendment, use TR-0046's sorted output-digest manifest as the exact non-self-referential artifact bundle; the transition blob itself is bound by the enclosing Git commit/tree. The program-plan bootstrap `evidence/artifact-manifest.json` remains historical and is not regenerated merely to create a circular feature-transition manifest. The approval must bind:

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

The approval is now recorded. The coordinator may select and specify the dependency-eligible `EPP-F01` child feature. No implementation or external action is implied; the feature must traverse the complete machine-evidenced lifecycle and receive its own exact implementation approval.
