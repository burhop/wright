# Program-Control Requirements Checklist: Control-Plane Validator and Live Readiness Dashboard

**Purpose**: Formal reviewer gate for the completeness, clarity, consistency, measurability, and scenario coverage of EPP-F01 requirements and approved design contracts
**Created**: 2026-08-27
**Feature**: [spec.md](../spec.md)

**Focus**: Control-plane truth, user experience, failure/recovery, inspectable I/O, tests, compatibility, benchmark boundaries, privacy/security, rollback, and material change control

## Requirement Completeness

- [x] CHK001 Are the authoritative subject, source artifacts, committed-byte identity, checkout observation, and generator identity all defined without relying on conversation history? [Completeness, Spec §FR-002, §FR-005; Data Model §Identity Rules]
- [x] CHK002 Are requirements present for schema validation, semantic validation, cross-references, digests, revisions, transitions, approvals, roadmap eligibility, WIP, leases, and stop conditions? [Completeness, Spec §FR-003–FR-009]
- [x] CHK003 Are requirements defined for all four readiness areas, their gate rows, evidence, counts, blockers, freshness, last success, and exact release formula? [Completeness, Spec §FR-010–FR-013]
- [x] CHK004 Are the human-readable journey, machine output, prerequisites, inputs, outputs, pass/fail meaning, evidence inspection, and next-action behavior all documented? [Completeness, Spec §FR-001, §FR-017, §FR-019, §FR-024; Quickstart §1–§4]
- [x] CHK005 Are explicit requirements present for primary, alternate, exception, recovery, non-functional, empty, dirty, stale, and unsupported-version scenarios? [Coverage, Spec §User Scenarios, §Edge Cases]

## Requirement Clarity

- [x] CHK006 Is “committed evidence” unambiguously defined as exact Git-object bytes while line-ending conversion and dirtiness remain separate observations? [Clarity, Spec §FR-005; Research §R-003]
- [x] CHK007 Is the non-circular distinction among source commit `S`, container commit `C`, and release candidate `R` explicit enough to prevent self-referential or cross-candidate claims? [Clarity, Plan §Design Decisions; Contracts §Dashboard Generation]
- [x] CHK008 Are supported and unsupported schema versions defined by an explicit compatibility table rather than the ambiguous phrase “known major”? [Clarity, Research §R-009; CLI Contract §Compatibility]
- [x] CHK009 Are lifecycle transitions, failed attempts, and repair checkpoints assigned distinct state domains/event kinds with explicit allowed-edge authority? [Clarity, Research §R-004; Data Model §TransitionEvidence]
- [x] CHK010 Is the difference between a dev baseline and actual worktree-start subject defined, including non-private worktree identity, lease mode, allowed actions, and recovery state? [Clarity, Research §R-005; Data Model §FeatureLeaseV2]

## Requirement Consistency

- [x] CHK011 Do the spec, plan, data model, CLI contract, and quickstart consistently prohibit product/benchmark execution, network calls, external writes, dependencies, and Git mutations? [Consistency, Spec §FR-014, §Out of Scope; Plan §Constraints; CLI Contract §Entrypoint]
- [x] CHK012 Do dashboard denominators, area aggregation, benchmark counts, and release eligibility consistently derive from gate catalog/evidence rather than editable projection fields? [Consistency, Spec §FR-010–FR-013; Research §R-007]
- [x] CHK013 Are approval rules consistent about historical subject integrity, append-only revocation/supersession, policy changes, exact scope, and machine-verifiable conditions? [Consistency, Spec §FR-008; Research §R-008]
- [x] CHK014 Are rollback requirements consistent with source immutability, manual-validation restoration, and invalidation of unsupported generated snapshots? [Consistency, Spec §FR-023; Data Model §Migration and Rollback; Quickstart §6]

## Acceptance Criteria Quality

- [x] CHK015 Can every fail-closed class in FR-003 through FR-009 be mapped to one isolated negative fixture and a stable expected reason code? [Measurability, Spec §FR-020, §SC-002; Plan §Verification Strategy]
- [x] CHK016 Can deterministic equivalence be assessed by excluding only explicitly named observation fields while comparing every semantic field and output order? [Measurability, Spec §SC-003; Validation Report Contract]
- [x] CHK017 Are the four-area pass/block/fail/stale matrix and the 100-success trap defined with objective expected release outcomes? [Measurability, Spec §SC-004–SC-005]
- [x] CHK018 Is transactional preservation quantified as byte-for-byte equality with non-success status and no partial replacement or temporary residue? [Measurability, Spec §SC-006; Dashboard Contract §Failure Atomicity]
- [x] CHK019 Are cross-platform compatibility outcomes objective: identical committed digests and semantic verdicts, with checkout representation differences confined to declared fields? [Measurability, Spec §SC-007]
- [x] CHK020 Is sensitive-output success defined as zero occurrences of every prohibited canary class across JSON, text, stdout, and stderr? [Measurability, Spec §SC-008; Plan §Verification Strategy]

## User Experience and Inspectability

- [x] CHK021 Are requirements defined for a fresh maintainer to find prerequisites, run the command, understand the highest-severity finding, inspect evidence, and identify recovery in under five minutes? [Coverage, Spec §SC-001; Quickstart §1–§5]
- [x] CHK022 Are empty, not-started, in-progress, stale, blocked, and failed meanings specified without synthetic progress or false authority? [Clarity, Spec §FR-011, §Edge Cases; Quickstart §4]
- [x] CHK023 Are terminal text and machine JSON required to share one semantic report model and expose the same verdict, subjects, areas, blockers, and next action? [Consistency, Spec §FR-017; CLI Contract §Result Model]
- [x] CHK024 Are gate and finding evidence references constrained to exact, local, repository-relative, bounded identifiers that a reviewer can follow? [Coverage, Spec §FR-016, §SC-010; Data Model §ValidationFinding]

## Failure, Recovery, and Atomicity

- [x] CHK025 Are malformed input, duplicate key, missing Git metadata, unsafe path, dirty checkout, stale approval, impossible transition, ambiguous eligibility, and lease conflict recovery requirements explicit? [Coverage, Spec §Edge Cases; Quickstart §5]
- [x] CHK026 Are candidate validation, write, flush, `fsync`, reread, replacement, and interruption failures all covered before the atomic commit point? [Coverage, Plan §Verification Strategy; Dashboard Contract §Failure Atomicity]
- [x] CHK027 Is the prohibition on modifying the prior dashboard merely to mark failure/staleness unambiguous? [Clarity, Research §R-011; Dashboard Contract §Failure Atomicity]
- [x] CHK028 Are bounded repair, stop, and reapproval requirements preserved rather than allowing the validator's success or recovery advice to create authority? [Consistency, Spec §FR-024; Quickstart §5; Plan §Delivery and Gate Impact]

## Security, Privacy, and Path Safety

- [x] CHK029 Are prohibited output classes complete enough to include credentials, tokens, cookies, endpoints, prompts, logs, proprietary payloads, artifact bodies, reusable authority, commands/arguments, and absolute paths? [Completeness, Spec §FR-018; CLI Contract §Privacy and Path Rules]
- [x] CHK030 Are requirements explicit that raw schema instance values and raw exception text cannot bypass the output allowlist? [Clarity, Research §R-010; CLI Contract §Privacy and Path Rules]
- [x] CHK031 Are normalization, repository-root containment, declared out-of-program references, symlink traversal, drive, UNC, `..`, and NUL cases addressed? [Coverage, Research §R-010; Data Model §Identity Rules]

## Benchmark and Readiness Independence

- [x] CHK032 Are benchmark policy, coverage, oracle, artifact, partition, attempt, holdout, independence, and freshness requirements validated without creating or executing cases? [Completeness, Spec §FR-012, §FR-022]
- [x] CHK033 Are non-passing evidence classifications explicitly prevented from counting as passed in every area? [Clarity, Spec §Edge Cases; Research §R-007]
- [x] CHK034 Is every product, benchmark, commercial, and program-health gate required exactly once for one exact candidate, with no score or cross-area compensation? [Consistency, Spec §FR-010–FR-013; Gate Catalog Contract]

## Dependencies, Change Control, and Compatibility

- [x] CHK035 Are the five material semantic changes, the immutable bootstrap profile, and the need for combined feature/material-change approval visible and approval-blocking? [Dependency, Plan §Design Decisions and Approval Boundary; Research §Remaining Material Questions]
- [x] CHK036 Are dependency, package, product-code, benchmark, external, push/PR/merge, integration, publication, and release exclusions all preserved as separately authorized boundaries? [Coverage, Spec §Out of Scope; Plan §Delivery and Gate Impact]
- [x] CHK037 Is the existing `jsonschema` dependency requirement documented without implying authority to add or upgrade packages? [Assumption, Plan §Technical Context; Research §R-002]
- [x] CHK038 Are the frozen revision-9 bootstrap checkpoint, seed dashboard, prior compatible snapshot, unsupported versions, unknown generator, and removed-validator states included in compatibility requirements? [Coverage, Data Model §Migration and Rollback; Plan §Verification Strategy]
- [x] CHK039 Are Wright fast-push, dev-merge, Linux/POSIX, and Windows gate requirements documented together with a test that prevents route drift? [Completeness, Research §R-013; Plan §Verification Strategy]
- [x] CHK040 Is independent verification required on an unchanged exact candidate after author verification, without expanding the current planning authority? [Consistency, Plan §Delivery and Gate Impact; Spec §Assumptions]

## DEC-P0-013/014 Amendment Quality

- [x] CHK041 Are r1–r9 and r10–r19 specified as two independently closed profiles, with every bridge revision/transition digest enumerated, no future v1 acceptance, and one migration successor? [Completeness, Spec §FR-004, §FR-021; Data Model §Bootstrap compatibility profile; Contract §Legacy Compatibility Profile]
- [x] CHK042 Is the bridge checkpoint-commit fixed-point avoided explicitly by resolving only the forthcoming exact material-change approval subject, without leaving a coordinator-selected default? [Clarity, Research §R-014; ADR 0013]
- [x] CHK043 Are explicit `--container`, constrained `HEAD` inference, absent/unresolved behavior, first-parent proof, and dashboard-only diff requirements consistent across CLI, plan, data model, and tests? [Consistency, Spec §FR-002; CLI Contract §validate; Research §R-015]
- [x] CHK044 Is validator identity defined as the canonical digest of a sorted, inspectable manifest of every generator source blob so a non-entrypoint module change invalidates identity? [Clarity, Spec §FR-002; Data Model §ValidationSubject; Dashboard Generation §Authoritative Input Manifest]
- [x] CHK045 Do validation-report and dashboard gate rows share all fields, including a required per-gate `fresh` boolean distinct from area freshness? [Consistency, Spec §FR-011; Validation Report and Dashboard schemas]
- [x] CHK046 Are dashboard bytes permanently candidate-only while committed-current delivery is proved solely by an external report envelope and independent descendant-`D` evidence? [Clarity, Spec §FR-015; Dashboard Generation §Committed-Current Delivery Envelope; ADR 0014]
- [x] CHK047 Does delivery evidence bind exact `S`, `C`, dashboard bytes, dashboard-only `S..C`, delivery-only `C..D`, and unchanged source inputs without embedding `C` or `D` in dashboard bytes? [Completeness, Verification Evidence schema; Data Model §DeliveryEnvelope]
- [x] CHK048 Do the 72 append-only-identified tasks cover both legacy profiles, all three exact correction profiles, container resolution, generator-bundle mutation, per-gate freshness parity, candidate-only bytes, and descendant delivery proof with tests preceding implementation? [Coverage, Tasks T002, T006, T016, T021, T069–T072, T024, T034, T039–T040, T048, T051, T067–T068]
- [x] CHK049 Are the earlier approvals explicitly stale and the replacement exact `material_change` plus `feature_implementation` approvals required before any task or implementation mutation resumes? [Dependency, Tasks §Authority gate; Research §Remaining Material Questions; Program State §next_eligible_actions]

## Final Independent-Audit Repair Cycle

- [x] CHK050 Is `D` resolvable only through explicit `--delivery`, with resolved `C`, fixed first-parent/diff rules, no descendant search, and complete report/test coverage? [Clarity, CLI Contract §validate; Data Model §DeliveryEnvelope; Tasks T024, T029, T034, T039, T048, T068]
- [x] CHK051 Is validator success explicitly independent of derived readiness/release status, so valid blocked/not-started areas can exit zero and retain a proven next action? [Consistency, Spec §FR-001; CLI Contract §Exit Status; Tasks T024, T029]
- [x] CHK052 Does all current approval prose mark the prior EPP-F01 implementation approvals stale and require a replacement same-subject two-record bundle? [Authority, Program Approval §Historical EPP-F01 decision; README §Next action]
- [x] CHK053 Must delivery evidence be passing and authored by an independent verifier in both schema and negative tests? [Evidence, Verification Evidence schema; Dashboard Generation §Committed-Current Delivery Envelope; Tasks T016, T034, T068]
- [x] CHK054 Is validator source-bundle membership closed by exact roots, tracked regular file type, normalized uniqueness/order, count/byte bounds, import boundary, runtime-HEAD/loaded-module binding to `S`, clean-path enforcement, and add/delete/change/dirty tests? [Completeness, Spec §FR-002; Plan §Implementation Flow; Tasks T023, T034, T039, T051]
- [x] CHK055 Are both legacy profiles structurally closed, contiguous, uniquely pathed, raw-byte-bound through exact hashes plus the sole non-circular terminal approval-subject blob rule, archived through revision 19, and checkpoint-resolved without self-mutation? [Consistency, Lifecycle and Legacy Profile schemas; ADR 0013; Tasks T002, T006, T009, T015]
- [x] CHK056 Does each catalog assertion have exactly one machine result, with a closed class→schema/role registry and SourceArtifact binding, and aggregate gate pass derived only from complete, fresh, supporting, class-complete, evidence-backed, policy-independent results? [Benchmark quality, Gate Catalog/Evidence schemas; Plan §Derive readiness; Tasks T008, T033, T036]
- [x] CHK057 Are benchmark coverage, qualification lifecycle, oracle/output references, artifact completeness, holdout/contamination, attempts, tiers, freshness, and summary equations explicit semantic validators with negative fixtures? [Coverage, Data Model §Benchmark summary algebra; Dashboard Generation §Four Independent Areas; Tasks T033, T038]
- [x] CHK058 Does the empty-context README link the active feature artifacts and exact TR-0018 approval manifest, with missing freeze evidence treated fail-closed? [Usability, README §Empty-context orientation; Tasks T052]

## DEC-P0-016 Closed-Correction Quality

- [x] CHK059 Is the correction profile a literal set of exactly six transition claims and 26 state rows/31 pointers, with no open range, wildcard, future record, or generic override? [Completeness, Spec §FR-025; Correction schema/profile]
- [x] CHK060 Does every target bind repository path, raw SHA-256, introducing commit/tree, Git blob, exact pointer, and canonical state digest where applicable, with `37/37` independent recomputation required? [Evidence, Data Model §CommittedIdentityCorrection; Tasks T069]
- [x] CHK061 Are historical bytes and original findings retained, while terminal text and JSON disclose exact pointer, recorded/authoritative digest, resolution state, and correction reference? [Usability, CLI Contract §Result Model; Quickstart §Known committed-history correction]
- [x] CHK062 Are state/lifecycle identity, manifests, authority, readiness, gates, benchmark/release evidence, candidate/freshness, and correction records forbidden targets? [Safety, Correction schema/profile §forbidden_target_classes]
- [x] CHK063 Must all four readiness areas, benchmark counters/deficits, freshness, candidate identity, approvals, and release eligibility remain unchanged before/after disposition? [Independence, Spec §FR-025, §SC-011; Dashboard Generation §Four Independent Areas]
- [x] CHK064 Do unsupported readers, partial/extra/substituted targets, non-ancestor/self/future/circular targets, missing approval, and profile-digest drift all fail closed? [Compatibility, Research §R-016; Quickstart §6]
- [x] CHK065 Are DEC-P0-016 plus exact V4 material-change and feature-implementation approvals visibly blocking, with EPP-F01B and every external/integration/release action still excluded? [Authority, Plan §Design Decisions; Research §Remaining Material Questions]

## DEC-P0-017 TR-0027 Input-Origin Quality

- [x] CHK066 Is the second profile closed to exactly TR-0027 `/inputs/3`, with exact transition/approval raw digests, Git blobs, source commit, unique container/tree, and no wildcard/range? [Completeness, Spec §FR-026; Transition Input Correction schema/profile]
- [x] CHK067 Must validation prove approval absence at the declared source and exact first introduction at the container while retaining the unchanged two-path manifest and original finding? [Evidence, Data Model §TransitionInputOriginCorrection; Research §R-017]
- [x] CHK068 Are any other transition/pointer, manifest/output, authority, lifecycle, readiness, benchmark/release, candidate/freshness, and correction targets forbidden? [Safety, Transition Input Correction schema/profile]
- [x] CHK069 Do T024/T026/T030/T031 cover positive proof, every identity/pointer/origin/authority mutation, human diagnostics, recovery, non-mutation, and non-interference without adding a 70th task? [Coverage, Tasks §US1]
- [x] CHK070 Are DEC-P0-017, RISK-019 and distinct same-subject V5 approvals blocking T024 onward while T069 remains complete and all excluded actions remain unauthorized? [Authority, Tasks §Authority gate; ADR 0017; Program state]

## DEC-P0-018 Repair-Evidence Correction Quality

- [x] CHK071 Is the third profile closed to exactly two ordered claims: two exact historical cause-ID occurrences and one exact TR-0044 digest pointer, with no open range, wildcard, or new record? [Completeness, Spec §FR-027; Repair Evidence Correction schema/profile]
- [x] CHK072 Does each target bind exact path, raw SHA-256, Git blob, introducing commit/tree, pointer, recorded value, authoritative value, and canonical state digest where applicable? [Evidence, Data Model §RepairEvidenceCorrection]
- [x] CHK073 Are omissions, additions, substitutions, reordered/relocated targets, wrong identities/origins/digests, current/future records, correction-of-correction, and missing V7 authority all required to fail closed? [Coverage, Tasks T070]
- [x] CHK074 Must the original bytes and findings remain visible while all lifecycle, state, lease, authority, readiness, benchmark, candidate, delivery, and release outputs remain unchanged? [Safety, Spec §FR-027, §SC-013; Tasks T071–T072]
- [x] CHK075 Did historical V7 preserve T070→T071→T072 ordering and stop when T072 failed before any T066 retry? [Historical authority, Tasks]
- [x] CHK076 Does current V8 preserve every exclusion: T066–T068, product and EPP-F01B implementation, dependencies, benchmarks, external changes, push/PR/merge/dev integration, publication, and release? [Scope, Tasks §Current V8 repair gate]

## Notes

- Formal depth; intended for the feature author and independent reviewer before task decomposition and again before implementation approval.
- All 76 requirements-quality checks passed against the amended spec, plan, research, data model, quickstart, contracts, ADRs, state, and tasks after the bounded two-claim repair-evidence amendment. No override was used.
- This checklist evaluates written requirements. It does not claim that implementation or verification has occurred.
- Material items in CHK071–CHK076 remain intentionally approval-blocking for implementation, while their explicit treatment makes the planning artifacts complete enough for read-only analysis and exact-subject freeze.

## DEC-P0-019 V8 Checkpoint-Correction Quality

- [x] CHK077 Is the V8 historical target set exactly three ordered claims, with both TR-0047 pointers and only TR-0050's event-domain tuple?
- [x] CHK078 Are raw Git blob bytes authoritative and checkout/CRLF hashes explicitly rejected?
- [x] CHK079 Is TR-0050 bound to the existing repair event rule with required evidence and no generic policy widening?
- [x] CHK080 Is catalog rebinding defined against the final catalog blob with every other gate-evidence field unchanged?
- [x] CHK081 Do two walkthrough causes cover all three affected walkthrough tests and retain isolated rooted-path negatives?
- [x] CHK082 Does non-interference cover all four areas, 34 rows, honest 0/100, isolated synthetic benchmark data, dashboard bytes, candidate, approval, delivery and release?
- [x] CHK083 Is the separate roadmap-policy inversion failure visible, excluded from V8, and blocking T066?
- [x] CHK084 Are T073–T076 approval-gated while product/EPP-F01B work, dependencies, benchmarks, external actions, integration, publication and release remain excluded?
