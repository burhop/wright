# Implementation Plan: Browser Program Status

**Branch**: `codex/epp-continued-development-reconciled` | **Date**: 2026-08-28 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/077-browser-program-status/spec.md`

**Planning authority**: Planning and local verification only. EPP-F01B implementation remains blocked until the exact frozen `material_change` and `feature_implementation` subject is approved and a current bounded lease exists.

## Summary

Add a dedicated, authenticated `/program-status` page to Wright that makes the engineering-process program understandable to a product-minded solo developer. Its first viewport answers six practical questions about work size, active work, purpose, implemented customer capability, test trend, and the next change. The page is a read-only projection of one atomically installed, schema-valid evidence bundle: EPP-F01's validated dashboard snapshot, publisher-attested and runtime-recomputed identities, a digest-bound source catalog, a closed work registry, a governed use-case registry, an append-only test-run ledger, derived checkpoint history, the separate proposed-story catalog, typed benchmark/governance disclosures, and two delivery-lane summaries. A deterministic repository-side publisher validates committed inputs and installs the bundle in Wright's stable data root. A thin FastAPI route serves the last valid bundle with an ETag and a separate operational route serves publisher heartbeat; React conditionally refreshes and atomically replaces the view only when the evidence identity changes. Existing Plotly support renders accessible trend views with tabular/text fallbacks. No status, assignment, acceptance, test result, approval, readiness result, benchmark qualification, or current action can be edited or inferred by the page.

## Technical Context

**Language/Version**: Python 3.11+; TypeScript 5.6; React 19

**Primary Dependencies**: Existing FastAPI/Pydantic, `tool_registry`, React Router, Plotly (`plotly.js-dist-min` already installed), Vitest/Testing Library, Playwright; no new dependency

**Storage**: Atomic JSON bundle in `<WRIGHT_DATA_ROOT>/program-status/`; packaged fallback bundle in the Wright runtime; authoritative program evidence remains committed repository content

**Testing**: Pytest contract/unit/API tests; Vitest component tests; mocked Playwright UI integration; packaged-runtime system smoke; existing program-control validator and Git gates

**Target Platform**: Wright local web application on Windows, Linux, and macOS; fully air-gapped; responsive desktop and narrow browser viewports

**Project Type**: Modular monorepo web application (React frontend + FastAPI API + Python domain service + deterministic repository publisher)

**Performance Goals**: First valid local bundle response under 250 ms p95; a committed identity becomes visible within 10 seconds while the standard publisher runs; five-second conditional polling returns 304 without retransmitting or client-reparsing the body; page remains responsive with the bounded 100-story catalog and history

**Constraints**: Read-only; one exact identity per view; no repository checkout required at packaged runtime; no Git execution in the API; no remote telemetry; no benchmark/product execution; no credentials/raw logs/absolute private paths; last-valid preservation on refresh failure; keyboard/200%-zoom/reduced-motion support

**Scale/Scope**: One local operator; four readiness areas; up to 500 governed use cases; a distinct 100 proposed-story catalog; a 100-process subset and 100 governed benchmark slots; up to 100 registered task sources, 10 active assignments, 1,000 retained test attempts, and 250 rendered checkpoints per series; one integration lane plus one continued-development lane

## Constitution Check

*GATE: Passed before Phase 0 research and re-checked after Phase 1 design.*

| Principle | Design evidence | Result |
| --- | --- | --- |
| Strict FastAPI and modular boundaries | Route delegates immediately to a typed `tool_registry` reader as constitution §1 requires; repository derivation stays in a CLI publisher | PASS |
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

`scripts/publish-engineering-program-status.py` is the only component that reads repository evidence. It accepts an exact committed subject, validates the digest-bound `program-status-source-catalog.json`, rejects every unlisted path/schema/parser/selection route, invokes the EPP-F01 validator, embeds the validated EPP-F01 dashboard unchanged, verifies and attests the raw committed Git-blob digest, recomputes the Wright-canonical parsed-object digest, derives only catalog-contracted supplemental fields, and validates canonical evidence identities. Program task counts come only from task sources named in the committed work registry; active-agent rows come only from exact committed assignments. Use-case stages are derived from evidence classes in the governed use-case registry. Test checkpoints select one latest terminal attempt per `(commit, suite_id, population_id)` and reject overlapping component populations. The publisher writes a same-directory temporary bundle, flushes/fsyncs it, validates it, and calls `os.replace`; supported platforms also sync the parent directory, and replacement failure preserves the prior file. Its standard `--watch-committed` contributor mode checks only `git rev-parse HEAD` every two seconds by default and publishes after that identity changes; dirty content is ignored and publisher state is written separately from the bundle. Package build/install atomically supplies a generated last-valid bundle and the source catalog, so runtime never needs Git or a source tree.

### Runtime read boundary

`tool_registry.program_status` reads bounded bundle, catalog, and publisher-state files from the stable data root. It validates the publisher's raw Git-blob attestation and exact evidence link without falsely claiming to possess repository bytes, independently recomputes canonical dashboard and bundle identities, verifies the source-catalog digest, and enforces evidence-reference, action-purpose/authority, benchmark-context, correction/finding/verification, catalog-sum, lane-distinctness, observation-classification, and task-count relationships. The FastAPI routes contain no derivation logic. A packaged fallback is used only when no installed bundle exists; an invalid installed bundle returns a typed failure and never silently falls back. Missing, invalid, or unreadable newer data cannot be served as current.

### Browser boundary

The React service makes authenticated conditional bundle GETs and bounded publisher-heartbeat GETs. One reducer owns the active bundle and swaps all panels only after complete schema and relational client-contract validation. A five-second browser poll is the default local cadence; unchanged evidence returns 304. The page retains the last valid bundle and announces stale/failed states while separately displaying publisher activity. Every graph has a text summary and data table; color is supplementary. Checkpoint labels use exact timestamps, append-only transition/parent order, and short commit IDs, never lexicographic SHA order, ordinal-only axes, or calendar-day estimates.

### Authority and metric semantics

- The four readiness areas remain independent and non-compensating.
- Governed benchmark progress remains `qualified / 100`; a proposed 100-story catalog is a separate population with definition-maturity counts.
- The embedded dashboard action is historical to that snapshot; `work.current_next_action`, derived from validated current program state and lifecycle policy, is the sole current program action. Metric, benchmark, and lane actions are labeled guidance and cannot supersede it.
- At `0/100`, typed benchmark context must state phase, hold reason, dependencies, authority, and the next qualifying action or publication fails.
- Task completion is always labeled with its feature identifier and is never a whole-program completion percentage.
- Program-wide task completion covers only the closed registered task-source population and discloses roadmap items not yet decomposed into tasks; repository-wide discovery is forbidden.
- Active-agent identity and purpose are shown only from a committed assignment bound to an exact registered task and compatible lease; unavailable evidence stays unavailable.
- Use-case IDs and non-null `EPP-PROC-001..100` IDs are unique. Definition, in-progress work, user-visible acceptance, tests, independent verification, and benchmark qualification are orthogonal; `remaining = total - implemented`; and the proposed story catalog remains separate.
- Test history retains attempts for traceability but selects only the latest terminal attempt per canonical key. The bundle carries exact selected test identities, source time, terminal/aggregate role, digest, and counts so runtime/browser can verify disjoint component populations, arithmetic, and pass rate; missing categories remain unavailable.
- Customer capability, quality, automation, governance, readiness, benchmark, and delivery histories use contract-defined units and exact committed observations.
- Each chart uses one contract-defined numerator/unit/inclusion rule/source class and includes deterministic latest-change, decision-use, limitation, and structured next-action evidence.
- Integration/CI and continued-development lanes have exclusive branch identities and independent next actions.
- Evidence links always open an internal detail bound to exact path/digest/summary. Optional exact-commit GitHub links are secondary; unavailable raw content is stated honestly.
- Correction claim sets, findings, and verification verdicts are joined by stable IDs and validated as a closed relation; display counts are derived from those sets.

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
│   ├── program-status-bundle.schema.json
│   ├── program-status-source-catalog.json
│   ├── program-status-source-catalog.schema.json
│   ├── work-registry.schema.json
│   ├── use-case-registry.schema.json
│   └── test-run-ledger.schema.json
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

docs/programs/engineering-process-platform/
├── work-registry.json
├── use-case-registry.json
└── test-run-ledger.json

packages/tool_registry/
├── src/tool_registry/program_status.py
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

**Structure Decision**: Reuse Wright's existing frontend/API/registry boundaries. Keep repository interpretation in a deterministic script, runtime file validation in the constitution-required `tool_registry` boundary, transport in a thin API router, and presentation in an isolated React page. Do not extend the workspace landing page or create a second persistence system.

## Delivery and Compatibility Gates

1. Publisher contract fixtures cover valid, empty, stale, corrupt, source-catalog mutation, publisher raw-attestation mismatch, canonical-identity mismatch, current-versus-historical action precedence, benchmark hold context, correction/finding/verification linkage, canonical paths, parsed GitHub URLs, registered-versus-unregistered task sources, absent/exact assignments, use-case evidence-stage separation, test reruns/parametrization/overlap/count arithmetic, same-time causal ordering, concurrent read/replace, Windows replacement failure, and deterministic regeneration.
2. Domain/API tests prove last-valid preservation, bounded reads, ETag/304 behavior, auth enforcement, and secret exclusion. Linux verification separately runs the EPP-F01B route tests and the named pre-existing surface auth baselines so an unrelated hang cannot conceal the new route's result.
3. Component and UI-integration tests cover all five independently shippable stories, the six-question first-viewport comprehension gate, keyboard operation, text/non-color status, 200% zoom, narrow viewport, reduced motion, accessible tooltips, and semantic chart tables.
4. Packaged runtime and native lifecycle tests prove `/program-status` works without `.git`, checkout, Git, or network; the wheel contains all five EPP-F01B schemas plus promoted `dashboard.schema.json`, registered by the authoritative `dashboard-v2.schema.json` `$id` required by the bundle's external `$ref`; installed data survives upgrade/rollback/uninstall rules; and invalid installed data never silently falls back. Atomic replacement and native lifecycle coverage run explicitly on Windows, Linux, and macOS CI. The repeatable GB10 POSIX owned-listener baseline failure is tracked and classified independently; it may not be silently skipped or misattributed to EPP-F01B.
5. Existing workspace routes and `DashboardPage` remain behaviorally compatible.
6. Program-control validator, targeted tests, normal repository checks, `check-dev-push`, PR CI, `check-dev-merge`, and dev deployment verification must pass in sequence after implementation authority exists.
7. Rollback is one code revert plus restoration of the prior immutable `current.json`; an invalid new bundle must already fail closed to the previous valid view.

## Implementation Slices

Each slice is independently testable and shippable behind the same read-only route:

1. **US1 — Honest readiness**: bundle envelope, API, four readiness areas, benchmark `0/100`, proposed-catalog separation, and release explanation.
2. **US2 — Meaningful history**: exact-time task burn-up, test outcomes, customer/roadmap capability, readiness, and benchmark charts with defined units and explanatory annotations.
3. **US3 — Evidence traceability**: safe evidence detail, corrections, freshness, blockers, and recovery guidance.
4. **US4 — Work, use cases, and next action**: program and active-feature task totals, committed assignments with purpose, governed use-case funnels, two delivery lanes, and the authority-aware next action.
5. **US5 — Refresh resilience**: conditional refresh, atomic swap, honest empty/stale/failed states, and last-valid recovery.

## Complexity Tracking

No constitution violations or additional infrastructure are planned. The separate publisher is necessary to keep Git/repository interpretation out of the packaged API runtime; it reuses the EPP-F01 validator and emits one bounded contract rather than introducing a service or database.
