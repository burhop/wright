# ADR 0016: Use one closed append-only committed-identity correction

**Status:** proposed; exact V4 approval required

**Date:** 2026-08-27
**Decision ID:** `DEC-P0-016`

## Context

EPP-F01 US1 validation found six output-digest mismatches in immutable transitions TR-0023 through TR-0025. The same review also proved that the recorded baseline value `255f2424ff11a9300f31b7a5506279d63d149e8f` is a commit ID, not its tree ID, in 31 exact JSON-pointer occurrences across immutable state revisions 1–26. Git resolves commit `ad162cca048ad23d848673ec4f49f588dcc77aff` to tree `e6a7553036a505003a959eebd0efd3e1683c431a`.

Rewriting historical evidence would destroy the exact record of what was approved and observed. Weakening committed Git-blob identity would make the validator unable to distinguish factual drift from valid evidence. A generic exception or editable acceptance flag could be reused to waive unrelated readiness, benchmark, approval, or release failures.

## Proposed decision

Preserve every historical byte. Add exactly one recognized profile, `COR-EPP-F01-US1-COMMITTED-IDENTITY-001`, containing a literal set of 37 claims: six transition output-digest pointers and 31 state tree pointers. Bind each target to its path, introducing commit/tree, Git blob and raw SHA-256; bind state targets to canonical state digests and transition resolutions to exact artifact blobs.

The validator must:

- recompute all `37/37` claims from Git objects;
- require target containers to be strict ancestors of the correction-containing commit;
- reject any addition, omission, substitution, wildcard, range, same/future/circular target, or correction-of-correction;
- retain original findings and show their exact pointer, recorded/authoritative value, `resolved` status and correction reference;
- treat unsupported/unauthorized/partial profiles as fail-closed;
- prove that the four readiness areas, every benchmark counter/deficit, freshness, candidate identity, approvals and release eligibility do not change.

The correction is factual metadata disposition only. It is not a virtual rewrite, gate result, approval, waiver or authority source. It becomes effective only after exact V4 `material_change` and `feature_implementation` approvals bind the frozen profile digest and accept this decision.

## Alternatives rejected

1. **Rewrite TR-0023–TR-0025 or state revisions 1–26.** Rejected because immutable evidence must remain inspectable.
2. **Ignore the mismatches or weaken exact blob identity.** Rejected because this destroys the validator's core trust boundary.
3. **Adopt a reusable correction/override mechanism.** Rejected because it could become a hidden waiver channel.
4. **Let the correction change program or release readiness.** Rejected because readiness is independently derived from governed evidence.

## Consequences

EPP-F01 grows from 68 to 69 tasks while preserving prior task IDs and completed work. DEC-P0-016, PROG-01 and PROG-05 remain blocked until exact V4 approval and `37/37` verification. Old validators fail closed. Rollback returns the original findings to unresolved; it never creates a corrected historical view. EPP-F01B and all external, integration, benchmark-execution, publication and release actions remain unauthorized.
