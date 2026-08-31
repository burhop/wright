# UX and Authority Requirements Quality Checklist

**Purpose**: Review whether the visual-composition requirements are complete, measurable, and safe before implementation
**Created**: 2026-08-31
**Audience**: Human planning approver and PR reviewers
**Depth**: Formal feature gate

## Requirement Completeness

- [x] CHK001 Are requirements defined for every concept in the representative journey: phases, blocks, typed ports, connections, gates, feedback paths, and intended artifacts? [Completeness, Spec §FR-003]
- [x] CHK002 Are create, select, move, connect, edit, delete, validate, save, close, reopen, and inspect requirements all explicitly covered? [Completeness, Spec §FR-002/FR-017]
- [x] CHK003 Are last-valid in-memory and last-valid persisted behaviors both specified for invalid or interrupted changes? [Completeness, Spec §FR-006/FR-008]
- [x] CHK004 Are renderer-unavailable, malformed draft, newer schema, stale revision, and interrupted-save requirements documented? [Coverage, Spec §Edge Cases]

## Requirement Clarity

- [x] CHK005 Is “stable semantic identity” defined independently of label and layout and consistently applied to every authorable concept? [Clarity, Spec §FR-004; Data Model]
- [x] CHK006 Are intended artifacts clearly distinguished from produced files or execution evidence? [Clarity, Spec §Key Entities; North Star]
- [x] CHK007 Are gate and feedback declarations clearly distinguished from executed approval or runtime state? [Clarity, North Star]
- [x] CHK008 Is desktop-oriented authoring clearly separated from narrow-layout inspection rather than implied to be identical? [Clarity, Spec §FR-012]

## Requirement Consistency

- [x] CHK009 Are diagram, text, inspector, validation, and persistence identity requirements consistent with one canonical model? [Consistency, Spec §FR-009/FR-013]
- [x] CHK010 Are the proposed draft API, data model, renderer adapter, and rollback decision consistent about version, identity, and validation authority? [Consistency, Plan §Architecture]
- [x] CHK011 Are authoring actions and authority consistently separate from the released Process Definition route and data? [Consistency, Spec §FR-010/FR-014]
- [x] CHK012 Are Rivet, execution, MCP, LLM, benchmark, migration, and release exclusions consistent across all artifacts? [Consistency, Spec §FR-015/FR-020]

## Acceptance Criteria Quality

- [x] CHK013 Can diagram/text semantic parity and save/reopen equality be measured without subjective interpretation? [Measurability, Spec §SC-002/SC-003]
- [x] CHK014 Are invalid-edit fixtures and expected diagnostics/recoveries specific enough for deterministic tests? [Measurability, Spec §SC-004]
- [x] CHK015 Are keyboard, 390 CSS-pixel, 200% zoom, overflow, and accessibility thresholds objective? [Measurability, Spec §SC-005/SC-006]
- [x] CHK016 Is renderer replacement acceptance defined in terms of unchanged semantics, validation, persistence, and text output? [Measurability, Spec §SC-008]

## Drift, Evidence, and Dependencies

- [x] CHK017 Is every retained, revised, rejected, or deferred prototype lesson traceable to a fresh production requirement or explicit non-goal? [Traceability, Prototype Parity]
- [x] CHK018 Are walkthrough cadence, raw/annotated screenshots, browser diagnostics, and dashboard refresh requirements explicit? [Completeness, Spec §FR-018/SC-009]
- [x] CHK019 Does the plan state that `DEC-P0-002` remains open and that the provisional contract does not silently resolve permanent syntax/Apply policy? [Dependency, Proposed Decision 0001]
- [x] CHK020 Are Windows-writer and GB10-verifier responsibilities separated with exact-commit evidence and no shared writes? [Dependency, Plan §Execution Resource Strategy]
- [x] CHK021 Are feature-disable/removal and prior-binary rollback requirements defined without deleting drafts or touching released-definition data? [Recovery, Proposed Decision 0001]
- [x] CHK022 Is the lack of a 100-block usability claim explicit despite prototype stress observations? [Scope, Prototype Parity]



