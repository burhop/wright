# DEC-P0-019 — Closed EPP-F01 T072 checkpoint-evidence correction

**Status:** Proposed; exact V8 human approval required.

## Decision

Permit one append-only correction profile, COR-EPP-F01-T072-CHECKPOINT-EVIDENCE-001, to disposition exactly three immutable claims: TR-0047 /outputs/0/sha256, TR-0047 /outputs/1/sha256, and TR-0050's exact feature/repair_checkpoint/BLOCKED/BLOCKED tuple as the existing repair/repair_checkpoint/BLOCKED/BLOCKED event. The original bytes and findings remain visible. The validator must independently read the bound Git objects, prove the exact target set and required repair evidence, and reject every other transition, pointer, tuple, wildcard, future record, policy widening, or correction-of-correction.

The gate-catalog digest rebind and the two evidence-walkthrough contract causes are direct repairs to current mutable sources; they are not historical correction claims. Rebinding may change only gate-evidence.json#/catalog_digest. The walkthrough causes are (1) stale fixed README/current-state expectations and (2) finding artifact labels that are not repository-relative resolvable paths.

## Authority and stop

Planning and re-analysis do not implement this decision. V8 implementation requires separate exact same-subject material_change and feature_implementation approvals. The V8 lease, if approved, is limited to T073–T076. T066 remains excluded.

A separately observed failing roadmap-policy test is outside the six-target V8 boundary and remains an explicit unresolved P0 question. It cannot be repaired under V8 or hidden by a green claim. No lifecycle rule is broadened. No readiness area, benchmark count, gate assertion, candidate, approval, dashboard bytes, delivery result, release eligibility, roadmap status, lease, or authority may change except the planned BLOCKED approval pointer.

Product or EPP-F01B implementation, dependencies, benchmark generation or execution, external changes, push, PR, merge, dev integration, publication, and release remain unauthorized.
