# EPP-F01 V5 TR-0027 Input-Origin Omission Audits

**Scope:** read-only review of the planning-only V5 amendment. The primary coordinator remained the sole writer. Auditors did not authorize implementation or external action.

## Engineering usability

Initial result: three material findings. TR-0034 was missing; the empty-context chain still pointed to V4/T069; and authority to bind the 69-task plan was conflated with authority to execute T042–T068.

Disposition: TR-0034 now binds revision 35 and the exact artifact manifest. README and analysis name V5/T024 as the sole next boundary. V5 binds the unchanged plan but may activate only T024–T041; `REVIEW_EPP_F01_T041_VALUE_CHECKPOINT` is the required human action before T042. Final rerun: **PASS**.

## Architecture and authority

Initial result: five material findings. TR-0034 was absent; stale V3 and current V5 actions competed; the new correction lacked a distinct gate class; analysis was stale; and the automated schema-promotion matrix had no pending task coverage.

Disposition: add the append-only transition; remove the stale V3 action; register `TRANSITION_INPUT_CORRECTION` for PROG-01/PROG-05; replace the analysis; and amend pending T024 to cover Draft 2020-12 plus byte-identical promotion. Exact source/container/blob/raw identities and the 69 unique task IDs independently recomputed. Final rerun: **PASS**.

## Commercial and release readiness

Initial result: three material checkpoint findings: missing TR-0034, stale analysis and a prior-subject audit status that could be mistaken for current V5 acceptance.

Disposition: TR-0034, this subject-bound synthesis and `audit-status.json` now bind V5. V4 is historical only beyond completed T069; state is blocked/no-lease; APR-*005 is the sole gate; rollback and unsupported-reader behavior fail closed; four-area AND release eligibility remains unchanged. Final rerun: **PASS**.

## Benchmark quality

Initial result: one high finding. Requirements forbade benchmark effects but did not require executable deep equality over the complete projection.

Disposition: the profile now carries a closed `unchanged_projection_fields` list. FR-020, plan, T024 and T031 require correction-off/on deep equality for both honest `0/100` and non-empty synthetic fixtures across the full benchmark area/summary, populations, deficits, coverage, qualification, oracle/artifact, holdout, attempts/tiers, cutoff/freshness, readiness colors, candidate, approval and release eligibility. Benchmark collection/execution remains unauthorized. Final rerun: **PASS**.

## Synthesis

The auditors' counts are compatible: twelve observations collapse to ten material findings because missing TR-0034 and stale analysis were independently found by three roles. All are explicitly dispositioned; none is hidden. DEC-P0-017 remains human-owned and blocks T024. No auditor recommended a generic transition exception, history rewrite, task-count expansion, benchmark execution, product work, EPP-F01B work, dependency change, or external/integration/release action.
