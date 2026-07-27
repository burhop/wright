# Requirements Quality Checklist: Gateway Service and MCP

**Purpose**: Reviewer gate for protocol, identity, security, lifecycle, catalog, and migration requirement quality
**Created**: 2026-07-11
**Feature**: [spec.md](../spec.md)

## Identity and Authorization Completeness

- [X] CHK001 Are explicit binding requirements defined for both authenticated HTTP sessions and local STDIO processes? [Completeness, Spec §FR-002]
- [X] CHK002 Is immutability distinguished clearly from ordinary session persistence and reconnect behavior? [Clarity, Spec §FR-002, §US2]
- [X] CHK003 Are recent activity, global activation, and foreign-session state all explicitly excluded as routing or authorization inputs? [Coverage, Spec §FR-003]
- [X] CHK004 Are isolation requirements complete across tools, resources, approvals, audit, requests, tasks, notifications, and cancellation? [Completeness, Spec §FR-004]
- [X] CHK005 Is server policy consistently authoritative even when client annotations or approvals indicate safety? [Consistency, Spec §FR-013]

## Protocol and Transport Clarity

- [X] CHK006 Is the supported protocol target and negotiation behavior explicit without implying support for unverified newer versions? [Clarity, Spec §FR-005, §Assumptions]
- [X] CHK007 Are STDIO framing, diagnostic-channel, concurrency, EOF, and shutdown requirements documented? [Completeness, Spec §FR-006]
- [X] CHK008 Are HTTP authentication, Origin, headers, session/principal binding, reconnect, limits, and loopback requirements documented? [Completeness, Spec §FR-007]
- [X] CHK009 Are disconnect and cancellation semantics distinguished for HTTP transports? [Clarity, Spec §Edge Cases, §FR-010]
- [X] CHK010 Are advertised capabilities limited consistently to implemented protocol surfaces? [Consistency, Spec §FR-009, §Assumptions]
- [X] CHK011 Are stable protocol errors distinguished from tool-level structured error results? [Clarity, Spec §FR-012, Contract]

## Lifecycle and Concurrency Coverage

- [X] CHK012 Are start, restart, reconciliation, failure, cancellation, timeout, late completion, and shutdown scenarios all addressed? [Coverage, Spec §US3, §Edge Cases]
- [X] CHK013 Is generation authority specified so superseded work cannot publish current state? [Clarity, Spec §FR-018–FR-019]
- [X] CHK014 Can the one-current-runner and zero-leak outcomes be objectively measured? [Measurability, Spec §SC-004, §SC-009]
- [X] CHK015 Are concurrent message integrity and two-session isolation quantified with repeat counts? [Measurability, Spec §SC-001, §SC-003]

## Catalog and Result Contract Quality

- [X] CHK016 Is one authored catalog source required consistently across all consumers and distribution artifacts? [Consistency, Spec §FR-021]
- [X] CHK017 Are canonical identity, aliases, provenance, validation evidence, dates, schemas, and safety metadata defined? [Completeness, Spec §FR-022]
- [X] CHK018 Is incomplete clean-container evidence explicitly prevented from producing a passed status? [Clarity, Spec §FR-023]
- [X] CHK019 Are input validation, output validation, structured compatibility content, annotations, and redacted failures all specified? [Completeness, Spec §FR-011–FR-012]
- [X] CHK020 Are resource confinement and cross-workspace denial requirements defined for catalog, workspace, and artifact resources? [Coverage, Spec §FR-016]

## Migration, Recovery, and Scope

- [X] CHK021 Is the legacy gateway compatibility window, disabled-by-default posture, delegation rule, and removal condition documented? [Completeness, Spec §FR-008, Plan §Migration]
- [X] CHK022 Are upgrade, existing-state compatibility, failure, rollback, and partial-rollback hazards specified? [Coverage, Plan §Migration]
- [X] CHK023 Are atomic merge-only host configuration and unrelated-entry preservation requirements explicit? [Clarity, Spec §FR-024]
- [X] CHK024 Are experimental tasks, remote OAuth, plugin installation, release work, and Hermes thinning explicitly deferred? [Scope, Spec §Assumptions]
- [X] CHK025 Are compatibility claims constrained by exact version, platform, date, and executable evidence? [Traceability, Spec §FR-028, §SC-008]
