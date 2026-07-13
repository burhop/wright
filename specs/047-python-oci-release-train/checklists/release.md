# Release Requirements Quality Checklist: Python and OCI Release Train

**Purpose**: Reviewer-grade requirements quality gate for exact-artifact identity, protected promotion, supply-chain evidence, and recovery
**Created**: 2026-07-12
**Feature**: [spec.md](../spec.md)
**Depth**: Formal release gate
**Audience**: Maintainer and security reviewer before implementation

## Requirement Completeness

- [x] CHK001 Are all release identity consumers—tag, Python metadata, OCI labels/tags, changelog, compatibility declarations, and evidence—explicitly enumerated? [Completeness, Spec §FR-001]
- [x] CHK002 Are the only public Python distribution and all forbidden internal distribution names/dependencies explicitly defined? [Completeness, Spec §FR-003–FR-004]
- [x] CHK003 Are wheel and source archive content, safety, metadata, hash, and independent-install requirements all specified? [Completeness, Spec §FR-005–FR-010]
- [x] CHK004 Are Python index ordering, exact-file reuse, retry identity, OIDC, and protected environment requirements all defined? [Completeness, Spec §FR-011–FR-015]
- [x] CHK005 Are OCI input pinning, build-once identity, smoke, scan, inventory, SBOM, provenance, promotion, and mirror requirements all defined? [Completeness, Spec §FR-016–FR-024]
- [x] CHK006 Are final orchestration order, failure terminal state, evidence fields, and no-publication rehearsal boundaries all specified? [Completeness, Spec §FR-025–FR-028]
- [x] CHK007 Are CI/supply-chain, clean-container separation, recovery, bypass prevention, legacy-path removal, and documentation requirements present? [Completeness, Spec §FR-029–FR-035]

## Requirement Clarity

- [x] CHK008 Is “one version source” clarified by naming the source and every value that must match it? [Clarity, Spec §FR-001]
- [x] CHK009 Is “build once” clarified as one primary wheel/sdist pair and one OCI candidate, with downstream rebuilds forbidden? [Clarity, Spec §FR-007, §FR-017]
- [x] CHK010 Is “exact artifact” defined through filenames plus byte hashes for Python and an immutable digest/manifest for OCI? [Clarity, Spec §FR-007, §FR-017–FR-018]
- [x] CHK011 Is “least privilege” made reviewable through named protected environments and side-effect-scoped job permissions? [Clarity, Spec §FR-014–FR-015]
- [x] CHK012 Is the vulnerability threshold quantified and is every required exception attribute named? [Clarity, Spec §FR-019]
- [x] CHK013 Is optional mirroring distinguished from canonical GHCR validation without making a configured mirror failure optional? [Clarity, Spec §FR-022–FR-023]
- [x] CHK014 Is “GitHub Release last” tied to exact required predecessor stages and failure behavior? [Clarity, Spec §FR-025–FR-026]
- [x] CHK015 Is rehearsal explicitly distinguished from publication and are all prohibited mutations enumerated? [Clarity, Spec §FR-028, Assumptions]

## Requirement Consistency

- [x] CHK016 Are the sole-public-Python-package requirements consistent with the OCI-appliance product boundary? [Consistency, Spec §FR-003–FR-010, Assumptions]
- [x] CHK017 Are the Python supported-version requirements consistent with the measurable clean-install matrix and metadata-capping rule? [Consistency, Spec §FR-008, §SC-002]
- [x] CHK018 Are OCI architecture requirements consistent across candidate build, manifest evidence, mirror, and public claims? [Consistency, Spec §FR-024, Assumptions]
- [x] CHK019 Are immutable artifact requirements consistent with retry, recovery, yank, quarantine, and alias-restore semantics? [Consistency, Spec §FR-012, §FR-031–FR-032]
- [x] CHK020 Are protected promotion requirements consistent with the operator's explicit prohibition on actual publication in this feature? [Consistency, Spec §FR-028, Assumptions]
- [x] CHK021 Are clean-container MCP boundaries consistent with the production image scope and release CI scope? [Consistency, Spec §FR-030]

## Acceptance Criteria Quality

- [x] CHK022 Can version consistency be objectively verified by injected mismatches across every named consumer? [Measurability, Spec §SC-001]
- [x] CHK023 Can Python package safety and compatibility be objectively verified for both artifacts on every admitted runtime? [Measurability, Spec §SC-002–SC-003]
- [x] CHK024 Can no-rebuild OCI identity be verified across every scan, smoke, evidence, promotion, and mirror record? [Measurability, Spec §SC-004]
- [x] CHK025 Can vulnerability and Action/permission policy compliance be counted without subjective interpretation? [Measurability, Spec §SC-005–SC-006]
- [x] CHK026 Can dry-run side-effect freedom and terminal workflow ordering be proven through explicit outcomes? [Measurability, Spec §SC-007–SC-008]
- [x] CHK027 Can all named recovery drills and the repository merge gate produce binary pass/fail evidence? [Measurability, Spec §SC-009–SC-010]

## Scenario and Edge-Case Coverage

- [x] CHK028 Are primary flows covered independently for Python artifacts, release identity, OCI candidates, protected promotion, and recovery? [Coverage, Spec §User Scenarios]
- [x] CHK029 Are malformed/mismatched versions, dirty source, existing conflicting subjects, and expired workflow artifacts addressed? [Coverage, Spec §Edge Cases]
- [x] CHK030 Are archive traversal/symlink/secret/unrelated-content and source-build divergence cases specified? [Coverage, Spec §Edge Cases]
- [x] CHK031 Are scanner outages, malformed SBOM/provenance, expiring exceptions, digest mismatch, and smoke timeout covered? [Coverage, Spec §Edge Cases]
- [x] CHK032 Are partial multi-registry promotion, absent optional credentials, configured mirror divergence, and mutable alias recovery covered? [Coverage, Spec §Edge Cases]
- [x] CHK033 Are premature documentation/GitHub Release and protected-approval failures assigned fail-closed terminal behavior? [Coverage, Spec §Edge Cases, §FR-026]

## Dependencies, Assumptions, and Boundaries

- [x] CHK034 Are external repository settings—protected environments, reviewers, and Trusted Publishers—identified as prerequisites rather than falsely claimed code deliverables? [Assumption, Spec §Assumptions]
- [x] CHK035 Are current host/runtime/version/platform selections dated or bounded so unsupported claims cannot silently expand? [Assumption, Spec §FR-008, §FR-024]
- [x] CHK036 Are Features 046, 048, and 049 boundaries explicit for the MCP bridge, Codex plugin, and Hermes integration? [Scope, Spec §Assumptions]
- [x] CHK037 Is actual public publication explicitly excluded without weakening the requirement to prepare its protected workflow? [Scope, Spec §FR-028, Assumptions]
- [x] CHK038 Are immutable evidence retention and correction-by-new-patch assumptions consistent with external registry behavior? [Assumption, Spec §FR-031–FR-032]

## Ambiguities and Conflicts

- [x] CHK039 Does the specification avoid treating Action tags, mutable image tags, or workflow artifact names as artifact identity? [Ambiguity, Spec §FR-007, §FR-013, §FR-017]
- [x] CHK040 Does the specification avoid calling a dry-run, static workflow inspection, or generated attestation a successful production release? [Ambiguity, Spec §FR-028, §SC-007, Assumptions]
- [x] CHK041 Are canonical registry and optional mirror responsibilities non-conflicting? [Conflict, Spec §FR-022–FR-023]
- [x] CHK042 Are stable and prerelease alias policies non-conflicting, including `latest` eligibility? [Conflict, Spec §FR-021]

## Notes

- All 42 requirement-quality checks pass. The checklist tests whether the approved requirements are complete, clear, consistent, measurable, and bounded; it does not substitute for implementation evidence.
