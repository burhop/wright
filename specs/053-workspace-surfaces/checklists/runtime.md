# Workspace Surfaces Runtime Requirements Checklist

**Purpose**: Verify lifecycle, proxy, persistence, recovery and platform requirements are complete before task generation
**Created**: 2026-07-30
**Feature**: [spec.md](../spec.md)
**Depth**: formal runtime/reliability review

## Lifecycle Semantics

- [x] CHK201 Are every applicable state and legal/illegal transition defined, including new-generation behavior after stopped/failed and truthful projection during reconciliation? [Data Model: SurfaceInstance](../data-model.md#surfaceinstance), [FR-003]
- [x] CHK202 Are declaring, starting, readiness, health degradation/recovery, failure, restart, stop, presentation close and workspace/application shutdown distinguished with idempotency and concurrency semantics? [Lifecycle: Managed Live Application](../lifecycle.md#managed-live-application), [FR-018 through FR-024]
- [x] CHK203 Is presentation lifetime clearly separate from runtime lifetime, with app-declared policy preferred and workspace lifetime as the exact fallback when omitted? [Clarifications](../spec.md#clarifications), [Data Model: RuntimeRecord](../data-model.md#runtimerecord)
- [x] CHK204 Does shared versus isolated presentation behavior state when panel/browser reuse an instance, when a new instance is mandatory and what happens during simultaneous opens? [FR-005 through FR-007], [Lifecycle: Managed Live Application](../lifecycle.md#managed-live-application)
- [x] CHK205 Are cancellation and ordering outcomes defined for tab close, workspace/session change, disconnect, app exit, sleep, shutdown and late/stale events? [Lifecycle: Failure, Cancellation and Ordering](../lifecycle.md#failure-cancellation-and-ordering), [Spec Edge Cases](../spec.md#edge-cases)

## Process and Endpoint Ownership

- [x] CHK206 Are port allocation/race behavior, loopback binding, readiness proof, process+listener ownership and two concurrent instances fully specified without trusting an app-reported port alone? [Policy Defaults: Race-Safe Endpoint Ownership](../policy-defaults.md#race-safe-endpoint-ownership), [FR-020], [FR-026]
- [x] CHK207 Are graceful-stop signal, deadline, escalation, descendant cleanup, Windows/POSIX differences and unresolved-leak reporting measurable rather than merely aspirational? [Policy Defaults: Process Stop](../policy-defaults.md#process-stop-and-recovery-semantics), [SC-007]
- [x] CHK208 Does startup recovery require PID+creation time+generation+job/group/container+target evidence and define separate actions for owned stale processes versus unknown/unprovable processes? [Lifecycle: Startup Reconciliation](../lifecycle.md#startup-reconciliation)
- [x] CHK209 Are app/process/CPU/memory/restart/log/connection/body/frame/time limits and degraded-platform behavior declared or policy-defaulted with observable diagnostics? [Policy Defaults](../policy-defaults.md), [Live App Manifest](../contracts/live-app-manifest.schema.json)

## Transport Correctness

- [x] CHK210 Are HTTP methods, nested paths, queries, duplicate/end-to-end headers, cookies, compression, chunking, cancellation, redirects and 1xx/204/304 behavior within the conformance contract? [Protocol: HTTP](../contracts/protocol-contracts.md#http), [FR-021], [FR-025]
- [x] CHK211 Are WebSocket Origin, subprotocol, text/binary, close code/reason, backpressure, limits, reconnect and bidirectional cancellation requirements explicit? [Protocol: WebSocket](../contracts/protocol-contracts.md#websocket), [FR-021], [FR-025]
- [x] CHK212 Are SSE streaming/no-buffering, comments/heartbeat, retry/id, `Last-Event-ID`, 204 termination, disconnect and first-byte/idle deadlines explicit? [Protocol: SSE](../contracts/protocol-contracts.md#sse), [FR-021], [FR-025]
- [x] CHK213 Does the design define base-path/public-origin injection for FastAPI, Panel, Streamlit, Gradio and Dash without coupling core runtime behavior to those frameworks? [Framework Conformance](../framework-conformance.md), [Quickstart: Minimal Managed App](../quickstart.md#minimal-managed-app)

## Persistence, Packaging and Operations

- [x] CHK214 Are durable versus ephemeral fields enumerated so PID, socket, target pin, cookie, bearer, registration and live state are never restored as authority? [Data Model: Persistence and Recovery](../data-model.md#persistence-and-recovery-invariants), [Spec: Assumptions](../spec.md#assumptions)
- [x] CHK215 Does migration planning use a new contiguous/checksummed migration, preserve prior migrations, acknowledge old-binary future-schema rejection and require pre-upgrade backup restore for rollback? [Migration: Data Migration](../migration.md#data-migration)
- [x] CHK216 Are native/browser/Electron/Docker preview origins and endpoint resolution defined without a source checkout, random exposed child ports or control-plane cookie leakage? [Plan: Technical Context](../plan.md#technical-context), [Migration: Backend Migration](../migration.md#backend-migration)
- [x] CHK217 Are startup/shutdown hook ordering, stale-runtime recovery and cleanup-before-gateway/executor shutdown requirements identified for API composition? [Lifecycle: Startup Reconciliation](../lifecycle.md#startup-reconciliation), [Package Ownership](../package-ownership.md#public-boundaries)
- [x] CHK218 Do performance/reliability outcomes define the reference environment, trial counts, timing boundaries, concurrency and zero-leak evidence needed to evaluate SC-003, SC-006 and SC-007? [Policy Defaults: Reference Evidence Protocol](../policy-defaults.md#reference-evidence-protocol), [Success Criteria](../spec.md#success-criteria-mandatory)

## Notes

- Check only when independent runtime reviewers can derive deterministic state, timeout, cleanup and transport acceptance cases from the written design.
- A framework-specific exception must be expressed through the generic manifest/adapter contract or explicitly scoped as unsupported.
- Resolved 2026-07-30 after adding versioned numeric defaults, race-safe endpoint ownership, stop/reconciliation ordering, HTTP 1xx semantics, exact framework settings and reproducible evidence boundaries. Runtime implementation is not yet claimed.
