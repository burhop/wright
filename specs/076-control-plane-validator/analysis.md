# Specification Analysis Report: EPP-F01 V9 Preflight Amendment

**Method:** non-destructive Spec Kit consistency, ambiguity, requirement/task coverage, constitution, exact-Git-object, and four independent read-only omission analyses.

**Result:** PASS for V9 planning after bounded dispositions. Implementation remains blocked at a fresh exact same-subject `material_change` and `feature_implementation` gate.

## Closed scope and coverage

| Requirement | Tasks | Evidence |
|---|---|---|
| FR-029 exact discovery-schema claim | T077–T078 | exact-value external schema, immutable blob/hash/container and strict-ancestry identity |
| FR-029 exact TR-0051 manifest-order claim | T077–T078 | 35 unique paths, complete container-set equality, two exact order digests and self indices |
| SC-015 negative matrix and unsupported-reader behavior | T077–T078 | every identity/schema/manifest/approval/finding near miss named and fail-closed |
| SC-015 policy/source/projection non-interference | T079 | frozen V9 policy bytes, roadmap policy, four areas, 34 gates, complete benchmark projections, source manifest and release envelope |
| reproducible independent checkpoint | T080 | schema-valid `EPP-F01-V9.json`, unchanged subject, exact commands/results/manifest/reviewer/rollback |

All 29 functional requirements, 15 success criteria, and 80 task identifiers are unique. T070–T071 remain complete; T072 and T073–T076 remain incomplete and blocked. Only T077→T078→T079→T080 may become eligible after exact V9 approval. The local T073 stash is incomplete, non-authoritative, outside the subject, and never required for V9.

## Independent audit dispositions

- Engineering usability: replaced V8-only catch-up/analysis truth; expanded the exact negative matrix; bound T079 to APR-009/TR-0053; gave T080 a durable evidence path and independent identity; recorded the local stash's exact identity/inventory and fresh-clone semantics.
- Architecture: independently recomputed both target blobs, raw hashes, ancestor subjects, external-schema identity, 35-path set equality and self indices; required the audit and TR-0053 artifacts before freeze.
- Commercial/release: retained null lease, stale V8 authority, four independent readiness areas, unchanged dashboard/release outputs, and all product/EPP-F01B/external/integration/release exclusions; clarified planning-time V9 action selection versus frozen-policy non-interference.
- Benchmark quality: extended the test mandate through SC-015 and enumerated counts, populations, coverage, qualification, attempts, holdout, tiers, oracle/artifact, freshness, trend inputs and synthetic non-authority in T079.

No P0 or P1 audit finding remains open within V9. Contract/schema tests pass. The known policy-test inversion below remains visible and excluded rather than hidden by the V9 pass.

## Explicit unresolved P0 question

`tests/program_control_plane/test_roadmap_approval_and_lease.py::test_next_action_human_flag_must_match_policy` hard-sets the current policy value rather than injecting its opposite. It is not either V9 claim and may not change under V9. T066 and the historical V8 sequence cannot resume until separately authorized and the required regression is green.

No clarification question was required for the literal two-claim boundary. No constitution exception, implementation, T073–T076 execution, roadmap-policy repair, dependency, product/EPP-F01B work, benchmark generation/execution, external mutation, push/PR/merge/integration, publication, or release is authorized.
