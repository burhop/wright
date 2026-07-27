# Requirements Quality Checklist: State Migration and Recovery

**Purpose**: Review migration, integrity, backup, restore, startup, and operator-contract requirements before implementation
**Created**: 2026-07-10
**Feature**: [spec.md](../spec.md)
**Audience/Timing**: Maintainer review before implementation and feature merge

## Requirement Completeness

- [x] CHK001 Are requirements defined for fresh, complete legacy, and partial legacy source states? [Completeness, Spec §FR-004]
- [x] CHK002 Are preservation requirements explicit for every category of existing user state? [Completeness, Spec §FR-005]
- [x] CHK003 Are status, backup, upgrade, restore, and downgrade-by-restore requirements all defined? [Completeness, Spec §FR-010–FR-015]
- [x] CHK004 Are both preflight and postflight database validation requirements specified? [Completeness, Spec §FR-008–FR-009]

## Requirement Clarity

- [x] CHK005 Are migration identity, ordering, continuity, and checksum rules unambiguous? [Clarity, Spec §FR-001–FR-003]
- [x] CHK006 Is the supported legacy baseline distinguished clearly from unknown future state? [Clarity, Spec §FR-004, Assumptions]
- [x] CHK007 Is readiness defined as a fail-closed state reached only after all lifecycle validation? [Clarity, Spec §FR-008]
- [x] CHK008 Is downgrade explicitly limited to verified snapshot restore rather than reverse mutation? [Clarity, Spec §FR-015]

## Requirement Consistency

- [x] CHK009 Are schema-only migration requirements consistent with separate catalog reconciliation? [Consistency, Spec §FR-006–FR-007]
- [x] CHK010 Are automatic startup upgrade requirements consistent with explicit operator upgrade commands? [Consistency, User Stories 1–3]
- [x] CHK011 Are backup and restore compatibility rules consistent between the spec, data model, and command contract? [Consistency, Spec §FR-012–FR-014]
- [x] CHK012 Is snapshot-based rollback consistent with the no-reverse-migrations assumption? [Consistency, Spec §FR-015, Assumptions]

## Scenario and Edge-Case Coverage

- [x] CHK013 Are interruption requirements defined at the same atomic boundary as migration ledger recording? [Coverage, Spec §FR-002]
- [x] CHK014 Are corruption, foreign-key failure, checksum drift, missing history, and future-version scenarios addressed? [Coverage, Edge Cases]
- [x] CHK015 Are busy database, read-only path, permission failure, and concurrent lifecycle operation requirements addressed? [Coverage, Spec §FR-016, Edge Cases]
- [x] CHK016 Are malformed, tampered, incompatible, and interrupted restore scenarios defined to preserve active state? [Coverage, Spec §FR-013–FR-014]

## Acceptance and Non-Functional Quality

- [x] CHK017 Can record preservation and interruption safety be objectively measured across every supported fixture? [Measurability, Spec §SC-001–SC-002]
- [x] CHK018 Are corruption/refusal and idempotency outcomes quantified rather than described qualitatively? [Measurability, Spec §SC-003, SC-005]
- [x] CHK019 Is the backup/restore performance target bounded by size, duration, and supported hardware context? [Clarity, Spec §SC-004]
- [x] CHK020 Are credential and row-content disclosure exclusions defined for output, errors, logs, and manifests? [Security, Spec §FR-017, SC-006]

## Dependencies and Scope

- [x] CHK021 Is ownership split between data-vault lifecycle, API compatibility, and catalog reconciliation explicitly documented? [Dependency, Spec §FR-006–FR-007]
- [x] CHK022 Are public CLI expansion, remote backup scheduling, reverse migrations, and non-SQLite artifact migration explicitly excluded or deferred? [Scope, Assumptions]
- [x] CHK023 Are Feature 043 credential recovery artifacts distinguished from normal state backups? [Dependency, Edge Cases]
