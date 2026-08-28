# Implementation Plan: Browser Program Status

**Branch**: `codex/epp-continued-development-reconciled` | **Date**: 2026-08-28 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/077-browser-program-status/spec.md`

**Planning authority**: Planning and local verification only. EPP-F01B implementation remains blocked until the exact frozen `material_change` and `feature_implementation` subject is approved and a current bounded lease exists.

## Summary

Add a dedicated, authenticated `/program-status` page to Wright that makes the engineering-process program understandable to a product-minded solo developer. The page is a read-only projection of one atomically installed, schema-valid evidence bundle: EPP-F01's validated dashboard snapshot, independently bound source identity, derived checkpoint history, proposed customer-story catalog summary, and two delivery-lane summaries. A deterministic repository-side publisher validates committed inputs and installs the bundle in Wright's stable data root. A thin FastAPI route serves the last valid bundle with an ETag; React conditionally refreshes and atomically replaces the view only when the identity changes. Existing Plotly support renders accessible trend views with tabular/text fallbacks. No status, approval, readiness result, or benchmark qualification can be edited or inferred by the page.

## Technical Context

**Language/Version**: Python 3.11+; TypeScript 5.6; React 19

**Primary Dependencies**: Existing FastAPI/Pydantic, `workspace_service`, React Router, Plotly (`plotly.js-dist-min` already installed), Vitest/Testing Library, Playwright; no new dependency

**Storage**: Atomic JSON bundle in `<WRIGHT_DATA_ROOT>/program-status/`; packaged fallback bundle in the Wright runtime; authoritative program evidence remains committed repository content

**Testing**: Pytest contract/unit/API tests; Vitest component tests; mocked Playwright UI integration; packaged-runtime system smoke; existing program-control validator and Git gates

**Target Platform**: Wright local web application on Windows, Linux, and macOS; fully air-gapped; responsive desktop and narrow browser viewports

**Project Type**: Modular monorepo web application (React frontend + FastAPI API + Python domain service + deterministic repository publisher)

**Performance Goals**: First valid local bundle response under 250 ms p95; changed bundle visible within 15 seconds of installation; unchanged polling returns 304 without reparsing the body; page remains responsive with the bounded 100-story catalog and program history

**Constraints**: Read-only; one exact identity per view; no repository checkout required at packaged runtime; no Git execution in the API; no remote telemetry; no benchmark/product execution; no credentials/raw logs/absolute private paths; last-valid preservation on refresh failure; keyboard/200%-zoom/reduced-motion support

**Scale/Scope**: One local operator; four readiness areas; 100 proposed stories; 100 governed benchmark slots; bounded checkpoint, task, finding, correction, and CI-event histories; one integration lane plus one continued-development lane

## Constitution Check

*GATE: Passed before Phase 0 research and re-checked after Phase 1 design.*

| Principle | Design evidence | Result |
| --- | --- | --- |
| Strict FastAPI and modular boundaries | Route delegates immediately to a typed `workspace_service` reader; repository derivation stays in a CLI publisher | PASS |
| Offline-first | Bundle generation, API serving, graphs, and refresh are local; GitHub links are optional metadata, not a runtime dependency | PASS |
| Manager-neutral packaged runtime | API reads the Wright stable data root and a packaged fallback; it does not require a source checkout or agent manager | PASS |
| Embedded/file storage | Immutable JSON bundle uses the existing local data root; no database server is introduced | PASS |
| Security and identity | Existing local auth middleware protects the API; contract allowlists metadata and forbids secrets/raw bodies | PASS |
| UI atomic design | Page composes existing tokens/primitives and small status, chart, lane, evidence, and failure-state components | PASS |
| Three-tier UI testing | Component state tests, mocked Playwright journeys, and a packaged API+SPA smoke are explicit tasks | PASS |
| Observability | Structured read/refresh outcomes and trace IDs are planned without logging evidence bodies | PASS |
| Phase isolation | This plan freezes implementation behind an exact human approval subject and bounded lease | PASS |

Post-design re-check: the API and bundle contracts preserve all gates above. There are no constitution exceptions.

## Technical Design

### Evidence publication boundary

`scripts/publish-engineering-program-status.py` is the only component that reads repository evidence. It accepts an exact committed subject, invokes the EPP-F01 validator, derives only fields specified by the bundle contract, validates safe relative links, writes a temporary complete bundle, fsyncs it, and atomically replaces `current.json`. A development watcher may invoke the publisher only after `git rev-parse HEAD` changes; dirty working-tree content is ignored. Packaged builds install a generated last-valid bundle so runtime never needs Git or the source tree.

### Runtime read boundary

`workspace_service.program_status` reads a bounded file from the stable data root, validates it, verifies its envelope/body digest binding, and returns an immutable domain object plus ETag. The FastAPI route contains no derivation logic. Missing, invalid, or unreadable newer data becomes a typed unavailable/failed result; it never causes partial content to be served as current.

### Browser boundary

The React service makes an authenticated conditional GET. One reducer owns the active bundle and swaps all panels only after complete client-contract validation. A ten-second identity poll is the default local refresh cadence; unchanged evidence returns 304. The page retains the last valid bundle and announces stale/failed states. Every graph has a text summary and data table; color is supplementary. Checkpoint labels use exact timestamps and short commit IDs, not ordinal-only axes or calendar-day estimates.

### Authority and metric semantics

- The four readiness areas remain independent and non-compensating.
- Governed benchmark progress remains `qualified / 100`; a proposed 100-story catalog is a separate population with definition-maturity counts.
- Task completion is always labeled with its feature identifier and is never a whole-program completion percentage.
- Customer capability, quality, automation, governance, readiness, benchmark, and delivery histories use contract-defined units and exact committed observations.
- Each chart includes `what changed`, `why it matters`, `current limitation`, and `next action` text derived from allowlisted evidence fields.
- Integration/CI and continued-development lanes have exclusive branch identities and independent next actions.

## Project Structure

### Documentation (this feature)

```text
specs/077-browser-program-status/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── program-status-api.md
│   └── program-status-bundle.schema.json
├── checklists/
│   ├── requirements.md
│   └── program-status.md
├── tasks.md
└── analysis.md
```

### Source Code (repository root)

```text
scripts/
└── publish-engineering-program-status.py

packages/workspace_service/
├── src/workspace_service/program_status.py
└── tests/test_program_status.py

apps/api/
├── src/api/
│   ├── routers/program_status.py
│   ├── schemas/program_status.py
│   └── main.py
└── tests/test_program_status_api.py

apps/web/src/
├── components/
│   ├── layout/Sidebar.tsx
│   ├── pages/ProgramStatusPage.tsx
│   └── program-status/
├── services/program-status.ts
├── App.tsx
└── __tests__/

tests/
├── program_control_plane/test_program_status_publisher.py
├── ui-integration/program-status.spec.ts
└── e2e/test_program_status.py
```

**Structure Decision**: Reuse Wright's existing frontend/API/domain-service boundaries. Keep repository interpretation in a deterministic script, runtime file validation in `workspace_service`, transport in a thin API router, and presentation in an isolated React page. Do not extend the existing workspace landing page or create a second persistence system.

## Delivery and Compatibility Gates

1. Publisher contract fixtures cover valid, empty, stale, corrupt, unsafe-link, identity-mismatch, and deterministic-regeneration cases.
2. Domain/API tests prove last-valid preservation, bounded reads, ETag/304 behavior, auth enforcement, and secret exclusion.
3. Component and UI-integration tests cover all five independently shippable stories, keyboard operation, text/non-color status, 200% zoom, narrow viewport, reduced motion, and chart fallbacks.
4. Packaged runtime smoke proves `/program-status` works without `.git`, a Wright checkout, Git executable, or network.
5. Existing workspace routes and `DashboardPage` remain behaviorally compatible.
6. Program-control validator, targeted tests, normal repository checks, `check-dev-push`, PR CI, `check-dev-merge`, and dev deployment verification must pass in sequence after implementation authority exists.
7. Rollback is one code revert plus restoration of the prior immutable `current.json`; an invalid new bundle must already fail closed to the previous valid view.

## Implementation Slices

Each slice is independently testable and shippable behind the same read-only route:

1. **US1 — Honest readiness**: bundle envelope, API, four readiness areas, benchmark `0/100`, proposed-catalog separation, and release explanation.
2. **US2 — Meaningful history**: exact-time checkpoint charts with defined units, explanatory annotations, and feature-local task semantics.
3. **US3 — Evidence traceability**: safe evidence detail, corrections, freshness, blockers, and recovery guidance.
4. **US4 — Work lanes and next action**: integration/CI and continued-development lanes, bounded task/checkpoint progress, authority-aware next action.
5. **US5 — Refresh resilience**: conditional refresh, atomic swap, honest empty/stale/failed states, and last-valid recovery.

## Complexity Tracking

No constitution violations or additional infrastructure are planned. The separate publisher is necessary to keep Git/repository interpretation out of the packaged API runtime; it reuses the EPP-F01 validator and emits one bounded contract rather than introducing a service or database.
