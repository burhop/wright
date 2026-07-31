# Implementation Plan: Workspace Surfaces

**Branch**: `053-workspace-surfaces` | **Date**: 2026-07-30 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/053-workspace-surfaces/spec.md`

## Summary

Build one versioned Workspace Surface model for durable Python display results, existing file viewers, managed live web applications such as BREP, packaged MCP Apps, experimental WebMCP integrations, and explicitly approved view-only URLs. A backend-owned surface service will bind every surface, runtime, target, presentation, capability, and message to a workspace and session; persist durable intent and artifacts in SQLite plus the file vault; supervise process trees on native and Docker deployments; and expose isolated preview origins that correctly proxy HTTP, WebSocket, and SSE traffic without becoming a general-purpose proxy.

The React client will migrate the file-oriented viewer behind a compatibility adapter, retain live surface DOM across tab switches, add accessible surface tabs and focus mode that leaves chat operable, use the official MCP Apps bridge and mandated double-iframe sandbox, render versioned MIME bundles (including bundled-offline Plotly), and route all external-browser actions through a host adapter. A small installed `wright` Python package will provide `wright.display(...)` and novice graph helpers. Conventional webserver UIs remain managed live apps; only packaged `ui://` resources use MCP Apps. WebMCP remains feature-detected and experimental behind Wright's stable, surface-scoped compatibility contract.

## Technical Context

**Language/Version**: Python >=3.11; TypeScript ~6.0; React 19; Electron/CommonJS for the Hermes desktop shell

**Primary Dependencies**: FastAPI/Pydantic 2, Uvicorn/Starlette, httpx, psutil, SQLite, structlog/OpenTelemetry; React/Vite, `@modelcontextprotocol/ext-apps`, DOMPurify, bundled `plotly.js-dist-min`; optional adapters for Matplotlib, Plotly Python, pandas/PIL; platform process adapters using POSIX process groups and Windows Job Objects

**Storage**: Existing local SQLite repositories for surface metadata, preferences, grants, and audit indexes; existing file vault for display payloads, logs, and immutable resource bodies; no external database or cache service

**Testing**: pytest/pytest-asyncio/contract fixtures; Ruff and mypy; Vitest and React Testing Library; mocked and live Playwright; desktop/Electron harness; native lifecycle matrices on Windows, macOS, Linux plus Docker

**Target Platform**: Wright browser application served by packaged FastAPI; Hermes desktop wrapper; native runtime on Windows/macOS/Linux; Docker appliance; offline/air-gapped operation

**Project Type**: Modular monorepo containing Python service packages, FastAPI composition/routes, React web client, Electron host adapter, public Python helper, and reference applications

**Performance Goals**: Durable display visible within 2 seconds of producer completion; healthy reference app interactive within 5 seconds of readiness in >=95/100 trials; no whole-body buffering for SSE/streamed HTTP; responsive focus-mode layout; 100 concurrent reference interactions with zero cross-instance routing errors

**Constraints**: Zero route business logic; no general URL proxy; exact workspace/session/surface/origin binding; active content never executes on Wright's control-plane origin; offline core assets; no durable bearer tokens; preserve upstream framing/CSP policy; full process-tree cleanup; existing viewers remain compatible; no source checkout required in production artifacts

**Normative Defaults**: `policy-defaults.md` defines version-1 resource/time limits, race-safe endpoint ownership, stop/recovery ordering, degradation policy, and the reproducible reference evidence profile; `ux-contract.md` defines presentation eligibility, action consequences, state/action projection, layout, retention, keyboard/focus, beginner input, consent, and diagnostics behavior

**Scale/Scope**: Five surface source kinds; panel/browser/both presentation; HTTP/WebSocket/SSE; Python MIME updates; MCP Apps and scoped WebMCP; at least five framework/reference fixtures; cross-platform native and Docker validation; seven user journeys and 56 functional requirements

## Constitution Check

*GATE: Passed before Phase 0 research and re-checked after Phase 1 design.*

| Principle | Design evidence | Gate |
|---|---|---|
| Strictly typed FastAPI and modular boundaries | Pydantic request/response contracts; `workspace_service` owns orchestration, `tool_registry` owns MCP projection, `data_vault` owns persistence, routes only authenticate/validate/delegate/project | PASS |
| Offline-first | Plotly and MCP host assets are version-pinned and bundled; core display and managed local apps require no CDN; remote dependencies must be declared and policy-approved | PASS |
| Native runtime and Docker production parity | Surface service is manager-neutral; browser/Electron host adapters consume public API contracts; process and preview-origin adapters cover Windows/macOS/Linux/Docker; packaged helper and UI assets ship with runtime | PASS |
| Embedded storage and file vault | SQLite/WAL stores relational records and vault stores payloads/logs; no background database is introduced | PASS |
| Local authentication and RBAC | Existing user/session/workspace identity is mandatory on control-plane routes; grants add narrower authority and never replace RBAC | PASS |
| UI atomic design and test pyramid | New tokens, primitives, components, and patterns are separated; component, mocked Playwright, and live system suites are planned; every interactive control receives a stable `data-testid` | PASS |
| Structured observability | Surface operations propagate `trace_id`, emit structured redacted logs and OpenTelemetry spans, and expose correlation IDs without content or credential leakage | PASS |
| UI artifact transparency | Generated display records retain access-controlled prompt/direct-execution marker, effective constraints, and exact Python script revision; the verification UI exposes them without copying protected content into logs | PASS |
| Phase isolation and branch discipline | Work is on `053-workspace-surfaces`; this plan stops for human approval before tasks and implementation; no direct main/dev changes | PASS |

Post-design re-check: the contracts, data model, threat model, lifecycle design, and migration plan introduce no constitutional exception. The complexity table is therefore intentionally omitted.

## Architecture Decisions

1. **One surface model, separate execution profiles.** `SurfaceDescriptor` gives the UI one stable discriminated contract, while `DisplaySurface`, `FileSurface`, `LiveAppSurface`, `McpAppSurface`, and `ExternalUrlSurface` retain type-specific invariants. File viewers adapt into the model rather than being rewritten at once.
2. **MIME bundles instead of a custom canvas RPC.** `wright.display` uses versioned MIME bundles, typed Plotly data, SVG/images/tables/text, and `display_id` revision updates. A retained-mode canvas protocol is deferred because it would duplicate scene graphs, events, accessibility, update semantics, and renderer versioning already covered by established formats and full web apps.
3. **Managed apps for BREP and conventional webservers.** A declarative manifest launches or attaches to a verified target and may retain full JavaScript, HTTP, WebSocket, and SSE behavior. It can open in a panel or browser against the same instance. It is not modeled as an MCP App unless it actually publishes the stable `ui://` resource contract.
4. **Stable MCP Apps, scoped experimental WebMCP.** MCP-provided packaged HTML follows `io.modelcontextprotocol/ui` (2026-01-26) with official bridge types and a distinct-origin double iframe. WebMCP is feature-detected at `document.modelContext` and never becomes the sole route; Wright's compatibility messages are keyed by workspace, session, surface, document origin, server, and tool.
5. **Capability-bound preview routing.** Public preview URLs contain only opaque presentation identities. The backend resolves them to immutable, numeric, policy-validated target pins. No URL/request field may choose the upstream authority. Every HTTP request, redirect, WebSocket upgrade, and reconnect is checked against that record.
6. **Per-surface origin isolation.** Managed applications and active HTML receive distinct effective hostnames; MCP Apps use the mandated sandbox proxy origin. Port separation alone is insufficient because cookies ignore ports. Native mode uses validated opaque loopback hostnames such as `s-<id>.localhost`; hosted/Docker deployments require a configured wildcard preview domain or equivalent isolated-origin router on the existing public port. If safe isolation is unavailable, panel presentation is ineligible and browser presentation remains available.
7. **Durable intent and provenance, ephemeral authority.** Surface metadata, output revisions, exact generated-artifact prompt/direct-execution marker, effective constraints, script revision, preferences, and policy decisions may persist under workspace access control; running state, process identity, sockets, presentation cookies, and execution tokens are reconciled or recreated. No persisted tab assumes an old PID or bearer remains valid, and protected provenance is never emitted as general telemetry.
8. **Retained surface deck.** Live hosts remain mounted while inactive according to bounded retention policy so tab switching does not destroy BREP/Plotly client state. Static/file hosts may suspend. Exact-once disposal separates closing a presentation from stopping its runtime.
9. **Explicit defaults and conformance profiles.** Optional manifest fields inherit safe versioned limits rather than unlimited behavior. Frameworks translate the same injected host/port/origin/base-path contract through pinned conformance templates; a failing framework/version loses support or panel eligibility rather than gaining a security exception.

## Project Structure

### Documentation (this feature)

```text
specs/053-workspace-surfaces/
|-- spec.md
|-- plan.md
|-- research.md
|-- data-model.md
|-- threat-model.md
|-- lifecycle.md
|-- migration.md
|-- package-ownership.md
|-- policy-defaults.md
|-- ux-contract.md
|-- framework-conformance.md
|-- quickstart.md
|-- traceability.md
|-- contracts/
|   |-- live-app-manifest.schema.json
|   |-- display-envelope.schema.json
|   |-- surface-message.schema.json
|   |-- workspace-surfaces.openapi.yaml
|   `-- protocol-contracts.md
|-- checklists/
|   |-- requirements.md
|   |-- security.md
|   |-- runtime.md
|   |-- ux.md
|   `-- integration.md
`-- tasks.md                 # generated only after plan approval
```

### Source Code (repository root)

```text
packages/core/src/core/
`-- surfaces/                # side-effect-neutral IDs, values, errors, redaction/telemetry

packages/workspace_service/src/workspace_service/
|-- ports/                   # repositories, clock, tokens, process, network, preview
|-- use_cases/               # lifecycle, presentation, display, grants, reconciliation
`-- adapters/                # SQLite/vault, HTTP proxy, POSIX/Windows process adapters

packages/tool_registry/src/tool_registry/
|-- gateway/                 # preserve MCP UI metadata and child resources
|-- policy/                  # same-server visibility and app-originated authorization
`-- resources/               # composite server-scoped URI projection/cache/invalidation

packages/data_vault/src/data_vault/
`-- repositories/            # SQLite migrations/indexes and content-addressed payloads

apps/api/src/api/
|-- routers/surfaces.py      # thin control-plane routes
|-- routers/preview.py       # isolated presentation bootstrap + HTTP/WS/SSE relay
`-- composition.py           # service/repository/platform adapter wiring

apps/web/src/
|-- components/surfaces/     # atomic tabs, toolbar, approvals, diagnostics, presenters
|-- components/workspace/    # focus layout, retained deck, chat/surface switcher
|-- services/surfaces/       # contracts, registry, MCP bridge, scoped WebMCP adapter
|-- services/host-adapter/   # browser/desktop openExternal and endpoint resolution
`-- store/surfaces.tsx       # stable instance identity, layout and preference projection

src/wright/
|-- __init__.py              # public display and beginner graph API
|-- display.py               # adapters, MIME selection, bounded serialization
`-- client.py                # execution-scoped endpoint/token transport

hermes-wright-panel/
|-- preload.cjs              # narrow validated external-open IPC
|-- panel.cjs                # navigation/window-open policy
`-- types.d.ts

examples/workspace-surfaces/
|-- beginner_graph.py
|-- display_gallery.py
|-- fastapi_dashboard/
|-- panel_app/
|-- streamlit_app/
|-- gradio_app/
|-- dash_app/
|-- mcp_app_server/
|-- webmcp_app/
`-- hostile_surface/

tests/
|-- contract/workspace_surfaces/
|-- ui-integration/workspace-surfaces/
`-- e2e/workspace-surfaces/
```

**Structure Decision**: Extend the existing package owners instead of creating a parallel backend. Side-effect-neutral surface identifiers, values, errors, redaction and telemetry contracts live in `core`; `workspace_service` is the surface application boundary; `tool_registry` remains the only MCP gateway/policy boundary; `data_vault` supplies embedded persistence; `apps/api` only composes and translates HTTP/WebSocket transport; and `apps/web` owns presentation. The installed `src/wright` helper is deliberately small and communicates only through the public display contract. Dependency changes must update `architecture/python-packages.toml`, package metadata/README files, and the import-boundary fitness tests together.

## Delivery Phases

1. **Foundation and compatibility**: contracts, persistence migration, `SurfaceDescriptor`, file-viewer adapter, stable identity, API skeleton, feature flag, package/export changes.
2. **Durable Python display**: execution-scoped token, MIME ingestion, vault persistence, safe renderers, Plotly bundle, update semantics, novice helpers/examples.
3. **Managed live applications**: manifest, launch/attach, readiness/health, process-tree ownership, target pinning, presentation bootstrap, HTTP/WS/SSE proxy, browser action.
4. **MCP Apps and WebMCP**: upstream resource/metadata preservation, capability negotiation, official bridge/sandbox, same-server app tools, scoped compatibility adapter, draft-native feature detection.
5. **Workspace experience**: retained deck, accessible tabs/toolbars/dialogs, focus mode, responsive chat/surface switcher, versioned layout/preferences, diagnostics.
6. **Hardening and release evidence**: hostile fixtures, concurrency and lifecycle soak, native/Docker/browser/desktop matrices, docs/examples, accessibility, performance budgets, migration rollback, audit traceability.

Each phase is independently feature-flagged and must leave existing file/editor flows operational. Implementation tasks will be generated only after the human plan gate.

## Verification Strategy

- **Contract/unit**: schema compatibility, state transitions, explicit engineer/admin authority, target normalization/pinning, header filtering, redirect rules, MIME/encoding limits and sanitization, revision/provenance idempotency, MCP metadata/resource projection, bridge origin/source/correlation checks, preference and layout migrations, and traced SQLite/vault access.
- **Component**: every surface state and action; semantic tablist and keyboard behavior; focus/resize; capability dialog; diagnostics; renderer loading/error; responsive switcher; exact-once cleanup.
- **Mocked UI integration**: seven user journeys plus hostile messages, frame refusal, two surfaces sharing tool names, stale updates, presentation switching, chat updates in focus mode, narrow viewport, keyboard-only navigation.
- **Live system**: real FastAPI reference app exercising nested assets, redirects, chunked responses, SSE and WebSocket; MCP App fixtures; WebMCP fallback; browser + Electron host adapter; PID tree cleanup; persisted/reconciled restart.
- **Framework conformance**: FastAPI/Uvicorn baseline and pinned optional templates for Panel, Streamlit, Gradio, and Dash behind the real preview origin/base-path contract. Optional frameworks are test extras and examples, not core runtime dependencies.
- **Adversarial**: SSRF/rebinding/address confusion, cross-target redirects, hostile headers/cookies, token replay, cross-workspace/surface/origin messages, sandbox/CSP/permission escape, oversized/slow streams and frames, leaked process/port/grant/cookie checks.
- **Matrix**: Windows/macOS/Linux native and Docker; Chromium plus targeted Firefox/WebKit presentation tests; WebMCP tests always feature-detect and verify fallback; desktop build from `file://` proves absolute preview URLs and guarded `openExternal`.
- **Evidence protocol**: `policy-defaults.md` fixes the reference host class, warm-up/trial counts, timing boundaries, simultaneous concurrency, per-adapter cleanup cycles and zero-leak inspection set. Each result records environment and artifact digests; an unsupported environment is named rather than silently removed.
- **Traceability**: `traceability.md` maps all FR-001 through FR-056, SC-001 through SC-013 and seven independent user-story journeys to planned tests, fixtures, docs and evidence. Planned rows become pass/fail/blocked only from recorded evidence.
- **Gates**: Ruff format/check, mypy, full pytest, web lint/typecheck/Vitest/build, mocked Playwright, live Playwright, lifecycle soak, accessibility scan, dependency/security scan, package/native smoke, desktop build/test, and `scripts/check-dev-merge.sh` before any requested merge to `dev`. Release completion also follows `docs/release/release-runbook.md`, including wheel/native/UI/Docker contents, registry digest verification, published native lifecycle tests, versioned docs, and GitHub Release ordering; the authoritative scripts/docs are updated in the same feature if a required new suite is absent.

## Documentation and Evidence

Deliver user docs for opening panel/browser surfaces, permissions, focus mode, recovery, and the five-minute graph; developer docs for the public Python API, manifest, MCP Apps, WebMCP adapter, host adapter, framework templates, threat boundaries, diagnostics, testing, packaging, and migration. Examples must run from an installed release without a source checkout, avoid CDN dependencies, include accessibility descriptions, and have automated smoke coverage. The final audit will map every functional requirement and success criterion to tests, documentation, and recorded evidence, with environment-dependent manual checks called out explicitly.

## Planning Gate

Phase 0 research and Phase 1 design are complete when every artifact in the documentation tree above validates, targeted requirement-quality checklists have been generated, the constitution is re-checked, and no unresolved clarification remains. Per the constitution, stop for human approval at that point before generating `tasks.md` or modifying implementation code.
