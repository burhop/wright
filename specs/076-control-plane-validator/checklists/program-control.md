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

## Notes

- Formal depth; intended for the feature author and independent reviewer before task decomposition and again before implementation approval.
- All 40 requirements-quality checks passed against the exact spec, plan, research, data model, quickstart, and contracts at this checkpoint. No override was used.
- This checklist evaluates written requirements. It does not claim that implementation or verification has occurred.
- Material items in CHK035 remain intentionally approval-blocking for implementation, while their explicit treatment makes the planning artifacts complete enough for tasks and read-only analysis.
