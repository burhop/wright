# ADR 0013: Closed post-bootstrap v1 bridge

- Decision ID: `DEC-P0-013`
- Status: accepted for planning; implementation reapproval required
- Date: 2026-08-27
- Owner / human approver: human program and architecture approver
- Exact authority subject: `fedc2b439511780264a1897d326dc7a64560514b`, tree `659b36ba298285e81260dfe0e87a1ffbc09cb261`, program tree `eecae625813b52a131c1f033368a6e39ce898766`
- Authority record: [`APR-EPP-F01-AMEND-PLANNING-001`](../evidence/approvals/APR-EPP-F01-AMEND-PLANNING-001.json)
- Evidence: material-contract audit SHA-256 `5ca57c62ebbffb16158502bdafb3dee7684bdf964daf4c40f845c435447242c4`; stopped state canonical digest `ef9bd2dc3fd7400f3b5587d565ef35bf1c866139b01ac5d25a2710990eaad52d`
- Decision due gate: before EPP-F01 v1-to-v2 migration

## Context and claims affected

The approved `epp-bootstrap-v1-r1-r9` profile ended at revision 9, while governed planning, approval, implementation start, and the material stop produced authoritative v1 history through revision 18 / `TR-0017`. Accepting those records implicitly would weaken compatibility and append-only-history claims.

## Decision drivers

- Preserve every existing v1 byte and canonical state digest.
- Keep the exceptional r1–r9 profile closed and independently reviewable.
- Prevent an open-ended “same major” compatibility rule.
- Make the forthcoming exact approval checkpoint the final v1 record.
- Permit one auditable migration to v2 and no second successor.

## Options considered

1. Add a second closed bridge profile.
2. Replace r1–r9 with one wider profile.
3. Accept arbitrary later v1 records.
4. Rewrite or relabel later history.
5. Stop and redesign the lifecycle model.

## Evidence and contradictions

The material-contract audit demonstrated that a validator could not both reject post-r9 v1 records and accept authoritative current history. The stop added revision 18, so the final amended freeze must close the bridge at revision 19 / `TR-0018`, not at the audit's earlier revision-17 observation.

## Decision

Retain `epp-bootstrap-v1-r1-r9` unchanged. Add `epp-bridge-v1-r10-r19`, enumerating revisions 10–19 and transitions `TR-0009`–`TR-0018` with unique archive/transition paths, exact raw state and historical-transition blob SHA-256 values, and canonical prior/new state digests. Terminal `TR-0018` alone uses `raw_sha256_rule=checkpoint_commit_blob` with null embedded hash: embedding it would create a mutual raw-hash cycle because `TR-0018` manifests the changed profile. The later exact approval subject binds the commit containing both, and validation resolves and hashes the terminal transition there. The bridge terminates at program state `PROGRAM_ACTIVE`, child feature state `IMPLEMENTATION_APPROVAL_PENDING`, accepts no new v1 record, and permits exactly one v1-to-v2 lifecycle migration.

Because a commit cannot embed its own identity, the immutable fixture declares `checkpoint_commit_rule=exact_material_change_approval_subject` and leaves `checkpoint_commit` null permanently. The validator resolves the effective checkpoint commit from the new material-change approval record at validation time and verifies every enumerated state and transition blob at that exact subject. The profile is never patched to insert its own commit; any missing/different approval, path/blob mismatch, or non-ancestor subject fails closed.

## Consequences and residual risks

The validator requires two named legacy fixtures and exact chain tests. Revision 20 or another v1 transition is unsupported. Any planning mutation after the freeze invalidates the approval subject and requires a newly closed endpoint; it is not silently appended to the bridge.

## Compatibility, migration, rollback, and expiry

The decision expires if the frozen subject is changed before approval. Rollback preserves both legacy profiles and all source evidence, marks incompatible v2 projections stale, and restores manual validation. Reversal requires a superseding ADR and new material-change approval.

## Gate, roadmap, risk, and approval invalidation

This clears `DEC-P0-013` as a design question but does not authorize implementation. EPP-F01 remains `awaiting_approval`; the earlier EPP-F01 material-change and implementation approvals remain stale. `PROG-01` and `PROG-05` remain blocked until the replacement exact approval bundle exists.
