# EPP-F01 committed-identity repair omission audits

**Scope:** read-only review of the planning-only correction for stable cause `EPP-F01-US1-COMMITTED-IDENTITY-001`.

**Authority boundary:** the four auditors made no file changes. The coordinator is the sole writer. These reviews do not approve DEC-P0-016 or authorize implementation.

## Engineering usability audit — pass after required amendments

Findings:

- A correction needed an explicit user-visible lifecycle rather than an unexplained pass after prior failures.
- Text and JSON diagnostics needed the affected artifact, exact JSON pointer, recorded/authoritative bounded values, correction ID, and resolution status.
- The lease defect needed diagnosis at its exact pointer, not a prose summary.
- README/quickstart needed an immutable-history recovery journey and honest unresolved, unauthorized, resolved, stale and unsupported states.
- A new test/task was required; completed T021 could not be silently reinterpreted.

Disposition: FR-025/SC-011, `CommittedIdentityCorrection`, validation-finding fields, CLI/quickstart contracts, and append-only T069 now cover these requirements. Original findings remain visible. No usability P0 remains in the written plan.

## Architecture audit — pass after target-set reconciliation

Findings:

- The wrong baseline tree was not one claim. `/baseline/tree` contains the commit ID in every archived state revision 1–26, and `/active_mutating_lease/dev_baseline/tree` repeats it in revisions 20, 21, 24, 25 and 26: 31 exact pointer claims.
- Together with six transition output-digest mismatches, the stable cause contains 37 factual claims.
- The correction grammar had to be closed to exact ordered targets, strict ancestors, immutable Git-object identities and canonical state digests; a generic schema was too permissive.
- Transition evidence needed a closed planning/re-analysis authority variant because the current v2 shape assumed implementation scopes.
- Planning must propose evidence without an editable `accepted` flag; later exact approvals activate the frozen digest.

Disposition: the schema/profile require the literal six-claim and 26-row/31-pointer sets, exact identities, `37/37` recomputation, no new records, strict ancestry and no correction-of-correction. Transition schema v2 now admits only the exact planning approval form alongside the existing implementation bundle. DEC-P0-016 remains open for the human.

## Commercial and release-readiness audit — pass after required safeguards

Findings:

- A correction could otherwise be mistaken for a general waiver or release-green mechanism.
- PROG-01 and PROG-05 needed explicit correction evidence and decision/risk semantics.
- Older readers and rollback behavior needed fail-closed requirements.
- Dashboard program health needed correction counts/links without coupling product, benchmark or commercial readiness.

Disposition: DEC-P0-016 and RISK-018 expose the material choice/risk; the gate catalog adds `CONTROL_IDENTITY_CORRECTION` to PROG-01/PROG-05; compatibility and rollback return findings to unresolved; the dashboard contract limits correction data to derived program-health disclosure. No commercial/release P0 remains hidden, but exact V4 approval is still required.

## Benchmark-quality audit — pass with encoded constraints

Findings:

- The target set must use literal equality, not wildcard/range or future revision acceptance.
- The profile must contain exactly six transition pointers plus the exact 26 state rows and 31 pointers.
- Benchmark policy, qualification, coverage, oracle/artifact, holdout, attempt/tier, freshness, counters, deficits and release data must all be forbidden targets.
- Verification must prove the complete benchmark and readiness projection is unchanged and report `37/37 verified` with the exact profile/digest/checkpoint.

Disposition: the correction schema/profile forbid every benchmark/readiness/gate/release/candidate/freshness class; FR-025, SC-011, T069 and the dashboard contract require semantic equality and negative fixtures. No benchmark P0 remains in the written plan.

## Contradiction resolution

The initial discovery summarized seven blockers: six digest mismatches plus one factual lease/tree identity defect. Architecture and benchmark reviews correctly distinguished one stable cause from its occurrences. The durable repair therefore uses:

- one stable cause;
- two factual defect forms;
- 37 exact claims: six transition pointers and 31 state pointers;
- 26 state target rows because five rows carry two affected pointers.

No audit recommendation to model only seven claims was retained. Task T069 is append-only-numbered and placed before T024 so the 23 completed task identities remain unchanged while execution remains dependency ordered.

## Remaining material question and stop

`DEC-P0-016` is the only new material question. It is explicit, owned, and blocks EPP-F01, PROG-01 and PROG-05. The plan assumes no answer. The next action is the exact V4 human `material_change` and `feature_implementation` gate. EPP-F01B and all dependency, benchmark execution, push/PR/merge/integration, external, publication and release actions remain unauthorized.
