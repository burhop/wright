# EPP-F01 V7 repair-evidence amendment — independent omission audit

**Date:** 2026-08-27

**Mode:** bounded, independent, read-only; primary coordinator retained sole write authority

**Scope:** exact two-claim repair-evidence correction planning only

## Initial findings

| Priority | Finding | Required disposition |
|---|---|---|
| P0 | The operational pointer still exposed revision 46 as `IMPLEMENTING`, retained lease revision 10 and the invalid underscore cause ID, and allowed `EXECUTE_EPP_F01_TASKS`. | Append revision 47/TR-0046, set the lease to null, mark EPP-F01 `BLOCKED`, add DEC-P0-018, and expose only `APPROVE_EPP_F01_REPAIR_CORRECTION_V7`. |
| P1 | `approval.md` required “local validation is green,” creating a deadlock because the pre-V7 validator must fail closed until unauthorized T070–T071 implementation. | Require green planning JSON/schema/consistency checks and independent audit while explicitly retaining the expected semantic-validator blocker. |
| P1 | The expanded PROG-01 assertion exceeded the gate-catalog schema's 500-character requirement bound. | Shorten the assertion without losing exact V4/V5/V7 proof or non-interference semantics. |
| P1 | The planning contract test for a null mutating lease omitted the legal `BLOCKED` feature state. | Admit `BLOCKED` only when every exposed next action requires human approval; do not change validator implementation. |
| P2 | The README used item number 19 twice. | Renumber the later item 20. |

## Checks passed

- All source commits, trees, blobs, raw SHA-256 values, canonical state digests, and the full TR-0043 digest independently recomputed exactly.
- Both schema copies are byte-identical and close the source checkpoint, two ordered claims, target metadata, forbidden classes, projection list, authority, and discovery evidence to literal values.
- T070 → T071 → T072 → T066 retry ordering is explicit; all 72 task IDs are unique and the six uncompleted tasks remain unchecked.
- V7 requires same-subject `material_change` and `feature_implementation` approvals and preserves every explicit exclusion.
- Product, benchmark, commercial, and program-health readiness; benchmark 0/100 progress; lifecycle/lease; authority; candidate; dashboard delivery; and release eligibility remain independent and non-interfering.
- No product, validator implementation, dependency, benchmark, EPP-F01B implementation, or external-action file changed.
- The constitution review found no conflict.

## Final disposition

The primary coordinator applied all five planning-only fixes. Revision 47/TR-0046 and the current pointer record the stop truth; `approval.md` distinguishes planning checks from the expected pre-V7 fail-closed verdict; PROG-01 is schema-bounded; the no-lease test requires human-gated `BLOCKED`; and README numbering is unique. The amendment is **PASS after disposition**, subject to exact JSON/schema/digest revalidation and the enclosing Git subject freeze. No implementation authority is implied.

The Spec Kit prerequisite helper could not start through WSL on this Windows host; the auditor located and reviewed the declared feature artifacts directly. This is a tooling limitation, not a waived content check.
