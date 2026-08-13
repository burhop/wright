# Program Hardening Requirements Quality Checklist

**Purpose**: Review the usability, diagnostic-safety, lifecycle-compatibility,
accessibility, and merge-gate requirements before implementation

**Created**: 2026-08-13

**Feature**: [spec.md](../spec.md)

**Audience/Depth**: PR reviewers; formal program-closing review

## Requirement Completeness

- [x] CHK001 Are the two representative first-use journeys and their start/end boundaries explicitly defined? [Completeness, Spec §FR-001, Contract engineering-journey]
- [x] CHK002 Are requirements present for every capability/model/scenario state that changes the next safe action? [Completeness, Spec §FR-003]
- [x] CHK003 Are diagnostic requirements defined for preview, consent, export, expiry, replay, restart, omission, redaction, truncation, and failure? [Completeness, Spec §FR-008–FR-013]
- [x] CHK004 Are all retained program-state classes named for upgrade, rollback, uninstall, purge, restart, and offline behavior? [Completeness, Spec §FR-016–FR-024]
- [x] CHK005 Are native, Docker, platform, architecture, artifact, and evidence-level dimensions documented? [Completeness, Spec §FR-025–FR-027]
- [x] CHK006 Are requirements specified for default, alternate, error, recovery, cancellation, residue, and non-functional journeys? [Coverage, Spec User Stories 1–5]

## Requirement Clarity

- [x] CHK007 Is “supported” constrained to exact, passed, artifact-bound evidence rather than fixture, skipped, or inferred results? [Clarity, Spec §FR-004, FR-025–FR-026]
- [x] CHK008 Is “safe diagnostic” expressed as explicit forbidden content, permitted correlation, and measurable size/record/string limits? [Clarity, Spec §FR-011–FR-013, NFR-002]
- [x] CHK009 Is explicit export confirmation bound to an exact preview identity with unambiguous expiry and replay behavior? [Clarity, Spec §FR-009–FR-010, Data Model DiagnosticExportGrant]
- [x] CHK010 Is “preserve” distinguished from retain, migrate, invalidate, rebuild, remove, quarantine, and purge? [Clarity, Spec §FR-016–FR-023]
- [x] CHK011 Are accessibility targets quantified for width, zoom, keyboard, motion, focus, status, and finding severity? [Clarity, Spec §FR-031–FR-035, NFR-008]
- [x] CHK012 Are time, interaction, cancellation, cleanup, diagnostic, and offline response targets objectively bounded? [Clarity, Spec §SC-001, NFR-001–NFR-006]

## Requirement Consistency

- [x] CHK013 Do offline requirements consistently prohibit network use while permitting explicitly unavailable remote refresh? [Consistency, Spec §FR-021, NFR-006]
- [x] CHK014 Do diagnostic correlation requirements remain consistent with the prohibited private-content list across UI, API, logs, traces, and export? [Consistency, Spec §FR-011–FR-013, NFR-007, NFR-010]
- [x] CHK015 Do rollback and uninstall requirements consistently preserve user data unless an explicit irreversible purge plan is reviewed? [Consistency, Spec §FR-020, FR-022–FR-023]
- [x] CHK016 Do release-rehearsal and final-integration requirements consistently forbid `main`, publication, tags, registries, licenses, and production mutation? [Consistency, Spec §FR-028, FR-040]
- [x] CHK017 Do Gate E and scenario recovery requirements consistently forbid machine authority and every form of physical actuation? [Consistency, Spec §FR-007, FR-038]
- [x] CHK018 Are support-taxonomy terms consistent with the catalog/model distinctions created in Loops 068–072? [Consistency, Spec §FR-004, FR-037]

## Acceptance Criteria Quality

- [x] CHK019 Can each user story be accepted independently using a deterministic offline fixture and explicit observable result? [Measurability, Spec User Stories 1–5]
- [x] CHK020 Do success criteria quantify task time/interactions, attribution accuracy, adversarial classes, retained-state accounting, accessibility findings, and synchronization? [Measurability, Spec §SC-001–SC-011]
- [x] CHK021 Is evidence stability separated into deterministic material identity versus host/time/trace observations? [Acceptance Criteria, Spec §NFR-004, SC-005]
- [x] CHK022 Is the exact tree eligible for merge defined by one authoritative gate and matching tested/merged tree hashes? [Acceptance Criteria, Spec §FR-040, SC-010–SC-011]

## Scenario and Edge-Case Coverage

- [x] CHK023 Are wrong-principal, wrong-workspace, changed-digest, expired, replayed, restart-invalidated, oversized, and serialization-failure exports addressed? [Coverage, Spec Edge Cases, Contract support-diagnostics-api]
- [x] CHK024 Are interrupted migration, mixed-version state, newer-than-runtime state, missing cache, referenced content, and destructive purge edge cases addressed? [Coverage, Spec Edge Cases, §FR-017–FR-023]
- [x] CHK025 Are unavailable credentials/licenses/hosts/platforms represented as honest blocks rather than false failures or false support? [Coverage, Spec §FR-006, FR-026, FR-039]
- [x] CHK026 Are cancellation races, late success, cleanup timeout, and residue inspection requirements explicit? [Coverage, Spec §FR-015, NFR-003, SC-008]
- [x] CHK027 Are refresh/restart replay risks covered for every mutating confirmation in scope? [Coverage, Spec §FR-034]

## Dependencies, Boundaries, and Traceability

- [x] CHK028 Are dependencies on completed Loops 068–072, existing SQLite/native stores, Docker volumes, and exact platform evidence explicit? [Dependency, Plan Technical Context]
- [x] CHK029 Are external moderated usability, proprietary/live application validation, unavailable hosts, and production release intentionally excluded or deferred? [Boundary, Spec Clarifications and Out of Scope]
- [x] CHK030 Is the no-host-software base-image boundary traceable to the clean-container MCP process? [Dependency, Spec §FR-027]
- [x] CHK031 Are every functional/non-functional requirement and success criterion uniquely identified for analysis and task traceability? [Traceability, Spec §FR-001–FR-040, NFR-001–NFR-010, SC-001–SC-011]
- [x] CHK032 Are constitution-sensitive choices—offline operation, thin routes, embedded state, three UI tiers, structured safe telemetry, and manual authorization—covered in both constitution checks? [Traceability, Plan Constitution Check]

## Review Result

32/32 requirements-quality checks pass. The checklist focuses on the two
highest-risk clusters—diagnostic privacy/authority and lifecycle persistence—
while covering the complete usability/accessibility and integration boundary.

