# Human Program-Plan Approval Gate

## Current decision

**Approved.** [`APR-EPP-2026-001`](evidence/approvals/APR-EPP-2026-001.json) records the human decision made on 2026-08-26 for the exact subject below. The approval has no added conditions and is limited by its `program_plan` scope and the authorization boundaries in this document.

## Current EPP-F01 decision

**Approved for bounded local implementation.** [`APR-EPP-F01-MC-001`](evidence/approvals/APR-EPP-F01-MC-001.json) and [`APR-EPP-F01-IMPL-001`](evidence/approvals/APR-EPP-F01-IMPL-001.json) record separate `material_change` and `feature_implementation` decisions for the same frozen subject: commit `5279c51740a0352961c92a70bce9003923d8ca20`, repository tree `7e2eb93a9faed14b609075b72373a473a22fdbff`, program tree `8b6d5d6b3b0341f952e30c065b8dd289b9735213`, and the 21 artifact digests in `TR-0014`.

That approval authorizes only the 68 local tasks and implementation lease recorded in the approved plan. It does not authorize dependencies, product runtime changes, benchmark collection or execution, network or external mutation, push, PR, merge, dev integration, publication, or release.

## Approval subject

After the planning commit is created and local validation is green, resolve and present:

```powershell
git rev-parse HEAD
git rev-parse HEAD^{tree}
git rev-parse HEAD:docs/programs/engineering-process-platform
```

Also produce `evidence/artifact-manifest.json`, a sorted SHA-256 manifest of every other file under `docs/programs/engineering-process-platform/`, excluding only the manifest itself and any future approval record whose subject is this planning commit. Bind the manifest file's own SHA-256 separately; together those values cover the complete non-self-referential planning subject. The approval must bind:

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
