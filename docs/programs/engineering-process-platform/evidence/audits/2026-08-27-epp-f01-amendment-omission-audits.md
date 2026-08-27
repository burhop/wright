# EPP-F01 Amendment Independent Omission Audits

- Program: `EPP-2026`
- Feature: `EPP-F01`
- Audit date: 2026-08-27
- Scope: DEC-P0-013/014 planning amendments and final Spec Kit re-analysis only
- Writer: Codex primary coordinator, sole writer
- Independent auditors: engineering usability (`/root/amend_usability`), architecture (`/root/amend_architecture`), commercial/release readiness (`/root/amend_commercial`), benchmark quality (`/root/amend_benchmark`)
- Mutation boundary: auditors were read-only; no auditor edited, staged, committed, executed product/benchmark code, added dependencies, used the network, or made external changes
- Final verdict: **PASS**, conditional only on the exact local freeze checks recorded in `TR-0018`

## Method and repair boundary

Each auditor inspected the same planning-only working subject independently. The coordinator collected all initial findings before applying one consolidated final repair cycle under stable cause `EPP-F01-ANALYSIS-001`, attempt 2 of 2. Auditors then re-read the repaired subject. The coordinator resolved cross-audit contradictions and retained every original material finding below; a passing rerun does not erase it.

No implementation task was executed or checked. The preserved script drafts were not changed. The repair allowance is exhausted after this freeze; any new material defect requires a human-directed new repair authorization rather than another silent cycle.

## Engineering usability audit

Initial verdict: FAIL pending repair. Final independent verdict: **PASS**.

| Original finding | Severity | Resolution verified on rerun |
|---|---:|---|
| CLI could resolve `S`/`C` but could not deterministically locate delivery commit `D`. | HIGH | Added explicit-only `--delivery D`, resolved-`C` precondition, fixed first-parent/diff rules, no descendant search/inference, report fields, quickstart command, stable failures, and tests/tasks. |
| Validator failure/exit was conflated with legitimately blocked readiness. | HIGH | Validator success now means validation/derivation succeeded; non-passing independent areas and `release_eligible=false` may truthfully exit zero and retain a proven action/blocker. |
| Empty-context catch-up did not directly link the active feature subject or exact freeze manifest. | MEDIUM | README now links spec, plan, tasks, both checklists, analysis, `TR-0018`, and the revision-19 freeze prerequisite. |
| Generator source-bundle membership was not reproducible. | MEDIUM | Closed tracked entrypoint/package roots, normalized uniqueness/order, file/count/byte/import bounds, typed manifest, and mutation tests were added. |

Rerun conclusion: explicit delivery, exit meaning, catch-up navigation, and bundle membership are consistent across spec, plan, data model, CLI, provenance contract, schemas, quickstart, and 68-task plan. No new material usability omission remains.

## Architecture audit

Initial verdict: FAIL pending repair. Final independent verdict: **PASS conditional on freeze evidence**.

| Original finding | Severity | Resolution verified on rerun |
|---|---:|---|
| Profile schema forced null checkpoint while prose/tasks said implementation would fill it. | HIGH | The immutable profile keeps null permanently; validation resolves the effective checkpoint only from the later exact material-change approval subject. |
| Transition authority/check/output bytes were not frozen. | HIGH | Profiles now carry unique transition paths and committed Git-blob SHA-256 through `TR-0017`; terminal `TR-0018` uses the sole non-circular `checkpoint_commit_blob` rule. |
| Literal `SHA(TR-0018)` in the profile would form a mutual hash cycle because `TR-0018` manifests the changed profile. | HIGH | Terminal raw hash is null by rule; the later approval subject binds the commit containing both artifacts, from which validation resolves and hashes `TR-0018`. No iterative hash or self-mutation is permitted. |
| Early transition hashes were initially computed from Windows checkout/CRLF bytes. | HIGH | `TR-0001`–`TR-0004` were corrected from committed Git-object bytes; all committed transition hashes through `TR-0017` and all raw/canonical state identities through revision 19 were independently recomputed. |
| `D` discovery was ambiguous. | HIGH | Same explicit-only resolution repair verified by the usability auditor. |
| Source-bundle closure did not bind the code actually executing. | HIGH | Loaded modules and runtime `HEAD` bundle blobs must match `S`; dirty/untracked/ignored helpers, out-of-bundle modules, and source/runtime mismatch fail before pass/generation/recomputation, with Git text/EOL representation handled separately. |
| Revision 19 used mutable current-state path. | MEDIUM | Added immutable `evidence/states/program-state-revision-0019.json` with exact raw/canonical identity and pointed the bridge profile to it. |
| Exactly-two-profile structure and contiguity were only future semantics. | MEDIUM | Schemas require the two named ordered profiles/counts/successors; tasks require unique/contiguous/path/rule negative cases. |

Rerun conclusion: architecture is sound if `TR-0018`, the r19 archive, all amended artifacts, and exact commit/tree/program-tree/artifact digests are committed together and revalidated from committed blobs. These are freeze checks, not open design questions.

## Commercial and release-readiness audit

Initial verdict: FAIL pending repair. Final independent verdict: **PASS**.

| Original finding | Severity | Resolution verified on rerun |
|---|---:|---|
| `approval.md` still called the stale `5279c5…` subject current and implementation-approved. | HIGH | It now labels the decision historical/stale, grants no present authority, and requires replacement same-subject `material_change` and `feature_implementation` approvals. |
| Delivery schema allowed non-independent or non-passing `kind=delivery` records. | HIGH | Schema requires `actor.role=independent_verifier`, `actor.independent=true`, and `verdict=passed`; contracts/tasks add negative proof. |

Rerun conclusion: implementation, dependencies, product/benchmark execution, external writes, push/PR/merge/dev integration, publication, and release remain unauthorized. The four readiness areas and release approval remain independent; S/C/D delivery proof grants neither integration nor release authority.

## Benchmark-quality audit

Initial verdict: FAIL pending repair. Final independent verdict: **PASS**.

| Original finding | Severity | Resolution verified on rerun |
|---|---:|---|
| Aggregate gate rows could be hand-set passed without assertion-level proof. | HIGH | Catalog assertions have stable IDs; evidence must cover each exactly once; aggregate pass is derived only from complete passing/supporting/fresh/evidence-backed/independent results. |
| Required evidence classes were free labels and could be satisfied by relabeling an arbitrary artifact. | HIGH | Catalog has a closed class→schema-ID/source-role registry; evidence references carry class/schema/role and must match both registry and resolved SourceArtifact. |
| FR-022 benchmark domain invariants were not explicit semantic work/tests. | HIGH | Spec/plan/tasks now name coverage/intersections/equivalence families, qualification transitions, process/oracle/output references, artifact completeness, holdout chain/contamination, attempts, tiers, freshness, and hand-set-pass negative fixtures. |
| Benchmark counter populations/equations were underspecified. | MEDIUM | Fixed 100-slot status partition, counted definition, first-attempt/eventual relation, deficit independence, and T0–T3 prerequisites are explicit; T2 and T3 both require T0 and T1. |
| `BENCH-05` used “validation” instead of governed `frozen_qualification`. | LOW | Gate prose now uses the exact partition identifiers. |

Rerun conclusion: benchmark readiness remains independent, `100/100` cannot green another area, and EPP-F01 only validates/projects existing governed metadata. It neither creates nor executes benchmark cases.

## Contradictions resolved by the coordinator

1. **Exact transition bytes versus a non-circular terminal freeze**: exact embedded SHA-256 is used through `TR-0017`; terminal `TR-0018` is identified by path and `checkpoint_commit_blob`, with its exact blob resolved from the later approval subject. This preserves byte identity without an impossible profile/transition fixed point.
2. **Committed Git identity versus Windows execution bytes**: committed blobs remain authority; runtime `HEAD` blob IDs, loaded-module paths, and clean bundle status must match `S`, while declared Git text/EOL checkout representation is observed separately.
3. **Dashboard delivery versus readiness/release authority**: explicit `S`/`C`/`D` proof establishes only delivery currentness. Dashboard bytes remain candidate-only, readiness areas stay independent, and separate integration/release approvals remain mandatory.
4. **Evidence-class labels versus proof**: classes are not trusted labels; the catalog registry and SourceArtifact schema/role binding make class coverage reproducible.

## Remaining material questions and stop condition

No hidden P0 design question remains from DEC-P0-013/014 or these audits. The existing DEC-P0-001 through DEC-P0-012 remain visible and block their documented later gates; none was silently decided.

The only next action is the human approval gate for the newly frozen exact subject. Separate `material_change` and `feature_implementation` approvals must bind the same commit, repository tree, program tree, and `TR-0018` artifact digests. Until then: stop; do not resume implementation, add dependencies, execute product/benchmark code, push, open/merge a PR, integrate to `dev`, make external changes, publish, or release.
