# Workspace Surfaces Integration and Release Requirements Checklist

**Purpose**: Validate cross-package contracts, protocol coverage, compatibility, documentation and release evidence  
**Created**: 2026-07-30  
**Feature**: [spec.md](../spec.md)  
**Depth**: architecture/integration/release review

## Package and API Boundaries

- [x] CHK401 Are neutral values/errors/redaction in `core`, persistence in `data_vault`, MCP behavior in `tool_registry`, orchestration in `workspace_service`, transport/composition in `apps/api`, presentation in `apps/web`, and producer-only behavior in `src/wright` unambiguously assigned? [Package Ownership: Ownership Matrix](../package-ownership.md#ownership-matrix)
- [x] CHK402 Does every proposed dependency follow `architecture/python-packages.toml`, with manifest, package metadata/README and import-boundary evidence required for any graph change? [Package Ownership: Dependency Direction](../package-ownership.md#dependency-direction)
- [x] CHK403 Are API routes constrained to authentication, typed validation, dependency resolution, delegation and projection, with lifecycle, target and grant decisions in application services? [Plan: Constitution Check](../plan.md#constitution-check), [Package Ownership: apps/api](../package-ownership.md#appsapi)
- [x] CHK404 Does the control/data-plane contract avoid raw target URLs and durable credentials, define version negotiation/idempotency/stable errors, and cover presentation close/revocation/diagnostics/events? [OpenAPI Contract](../contracts/workspace-surfaces.openapi.yaml), [FR-053]

## Viewer and Host Compatibility

- [x] CHK405 Does migration preserve existing provider selection/document behavior/test IDs and the current file-content API while adding a dedicated preview contract? [Migration: Compatibility Goals](../migration.md#compatibility-goals), [FR-009]
- [x] CHK406 Is legacy path-keyed layout migration versioned and loss-aware, and are stale live state/window/PID/token values explicitly not migrated? [Migration: Data Migration](../migration.md#data-migration)
- [x] CHK407 Are browser and Electron host-adapter contracts complete for absolute preview origin resolution and guarded external opening, with no `file:` trust boundary or generic shell/IPC? [Package Ownership: Ownership Matrix](../package-ownership.md#ownership-matrix), [Threat Model: Cross-origin escape](../threat-model.md#cross-origin-escape-and-credential-theft)
- [x] CHK408 Does rollback state exactly how flags revoke authority/stop owned runtimes and how the pre-upgrade database backup is restored before an old binary starts? [Migration: Rollback and Recovery](../migration.md#rollback-and-recovery), [Migration: Data Migration](../migration.md#data-migration)

## MCP Apps and WebMCP

- [x] CHK409 Does the MCP contract cover capability negotiation, canonical/deprecated metadata, all content/result metadata, exact resource read, templates/subscriptions/notifications, server-scoped URI collisions and same-server visibility? [Research: MCP Apps](../research.md#mcp-apps), [FR-028 through FR-031]
- [x] CHK410 Is conventional BREP/server UI explicitly routed to the managed-app contract rather than external-URL MCP Apps, with documented behavior if BREP later publishes a packaged `ui://` resource? [Research: Executive Findings](../research.md#executive-findings), [Quickstart: MCP App Integration](../quickstart.md#mcp-app-integration)
- [x] CHK411 Does the WebMCP integration state the current `document.modelContext` API/draft status, tested native capability matrix, stable scoped SDK fallback, teardown and deprecation/removal of the global relay? [Research: WebMCP](../research.md#webmcp), [Migration: API and Contract Versioning](../migration.md#api-and-contract-versioning)

## Python and Framework Developer Experience

- [x] CHK412 Is the display envelope versioned, bounded and sufficiently typed for text/table/image/SVG/Plotly/safe HTML/active HTML, accessibility, durability, identity, revision and fallback? [Display Envelope](../contracts/display-envelope.schema.json), [FR-012 through FR-017]
- [x] CHK413 Does the installed `wright` package have no import-time side effects, lazy optional adapters, execution-scoped authority, package/export ownership and installed-wheel smoke requirements? [Package Ownership: src/wright](../package-ownership.md#srcwright), [Plan: Documentation and Evidence](../plan.md#documentation-and-evidence)
- [x] CHK414 Is the generic manifest expressive enough for BREP, FastAPI, Panel, Streamlit, Gradio and Dash without adding framework dependencies or one-off server branches to core? [Live App Manifest](../contracts/live-app-manifest.schema.json), [Framework Conformance](../framework-conformance.md)
- [x] CHK415 Is the canvas decision documented with covered use cases, accessibility/versioning rationale and a bounded future reevaluation condition? [Research: Canvas Decision](../research.md#canvas-decision), [Out of Scope](../spec.md#out-of-scope)

## Test and Release Evidence

- [x] CHK416 Does each user story and every release-blocking FR/SC map to contract/unit/component/mocked UI/live system/platform/manual evidence, with environment-dependent gaps explicitly named? [Traceability](../traceability.md), [Plan: Verification Strategy](../plan.md#verification-strategy), [SC-013]
- [x] CHK417 Are real fixtures required for safe/hostile display, HTTP/nested asset/redirect, WebSocket, SSE, MCP App read-without-list, WebMCP same-name simultaneous surfaces, framing denial and process-tree cleanup? [Threat Model: Security Verification Matrix](../threat-model.md#security-verification-matrix), [Traceability](../traceability.md)
- [x] CHK418 Does the supported matrix include Windows/macOS/Linux native, Docker single-port/wildcard routing, packaged wheel/no checkout, Chromium plus targeted Firefox/WebKit, Electron desktop build and WebMCP fallback? [Plan: Verification Strategy](../plan.md#verification-strategy), [SC-010]
- [x] CHK419 Are new merge-gate obligations (including desktop build if absent), release packaging/assets, dependency/security scans and the repository's authoritative `check-dev-merge`/release runbook called out? [Plan: Verification Strategy](../plan.md#verification-strategy), [Migration: Rollout Stages](../migration.md#rollout-stages)
- [x] CHK420 Are user, developer, security, operations, migration, troubleshooting, BREP, Python/framework and protocol docs/examples required to run offline from an installed release and kept executable in CI? [Plan: Documentation and Evidence](../plan.md#documentation-and-evidence), [FR-056]

## Notes

- Check only when an independent maintainer can derive ownership, compatibility and release evidence without inferring missing cross-package behavior.
- Any checklist item exposing a contract or ownership gap must be remediated in planning artifacts before `/speckit-tasks`.
- Resolved 2026-07-30 after package/API, viewer/rollback, MCP/WebMCP, Python/framework/canvas, 69-ID traceability, platform/fixture, merge/release and offline documentation review. Passing implementation/release evidence is still intentionally not claimed.
