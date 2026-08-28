# Tasks: Browser Program Status

**Input**: Design documents from `/specs/077-browser-program-status/`

**Prerequisites**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/`, and completed requirements checklists

**Authority**: This is a proposed implementation task graph. No task below may start until the exact EPP-F01B `material_change` and `feature_implementation` subject and bounded lease are approved.

**Tests**: Required by the feature specification and Wright constitution. Write each listed test first and observe the intended failure before implementing its behavior.

## Phase 1: Setup and contract fixtures

**Purpose**: Establish owned paths and test data without changing runtime behavior.

- [ ] T001 Create the EPP-F01B publisher module skeleton in `scripts/program_status/__init__.py`, `scripts/program_status/publisher.py`, and `scripts/publish-engineering-program-status.py`
- [ ] T002 [P] Add valid, empty, stale, corrupt, identity-mismatch, and unsafe-link bundle fixtures under `tests/fixtures/program-status/`
- [ ] T003 [P] Add TypeScript contract types and runtime decoder skeleton in `apps/web/src/services/program-status.ts`
- [ ] T004 [P] Add API Pydantic response/error schema skeleton in `apps/api/src/api/schemas/program_status.py`

**Checkpoint**: Owned files exist; no route, publisher action, or visible page is active.

---

## Phase 2: Foundational identity and read boundaries

**Purpose**: Complete the shared validation, atomic publication, and runtime read boundary that blocks every user story.

- [ ] T005 [P] Add failing schema, bound, canonical-digest, safe-path, and deterministic-regeneration tests in `tests/program_control_plane/test_program_status_publisher.py`
- [ ] T006 [P] Add failing last-valid, missing, corrupt, oversized, and identity-mismatch service tests in `packages/workspace_service/tests/test_program_status.py`
- [ ] T007 Implement contracted repository input allowlists, exact Git identity checks, EPP-F01 validation invocation, and canonical projection digesting in `scripts/program_status/publisher.py` (depends on T005)
- [ ] T008 Implement temporary-write, fsync, validate, and atomic `current.json` installation plus unchanged-identity no-op in `scripts/program_status/publisher.py` (depends on T007)
- [ ] T009 Implement the CLI arguments and non-secret exact-identity result in `scripts/publish-engineering-program-status.py` (depends on T008)
- [ ] T010 Implement bounded bundle read, schema validation, digest binding, installed/fallback selection, and immutable result types in `packages/workspace_service/src/workspace_service/program_status.py` (depends on T006, T008)
- [ ] T011 Export the program-status service through `packages/workspace_service/src/workspace_service/__init__.py` and wire stable data-root configuration in `apps/api/src/api/composition.py` (depends on T010)
- [ ] T012 Add structured trace-safe read/publication outcome logging without evidence bodies or private paths in `scripts/program_status/publisher.py` and `packages/workspace_service/src/workspace_service/program_status.py`

**Checkpoint**: A committed fixture can be deterministically published and read as one identity; invalid newer data cannot replace a valid bundle.

---

## Phase 3: User Story 1 — See honest program readiness (Priority: P1) 🎯 MVP

**Goal**: Open one authenticated page and understand the four independent readiness areas, release posture, governed `0/100` benchmark, and separate proposed-story catalog.

**Independent Test**: Publish the mixed-state fixture, open `/program-status`, and verify the four areas, gate counts/blockers/freshness, release explanation, benchmark hold context, and catalog separation without reading raw files.

### Tests first

- [ ] T013 [P] [US1] Add failing 200/304/auth/typed-error and forbidden-field API tests in `apps/api/tests/test_program_status_api.py`
- [ ] T014 [P] [US1] Add failing decoder and loading/current/unavailable readiness component tests in `apps/web/src/__tests__/ProgramStatusPage.test.tsx`
- [ ] T015 [P] [US1] Add a failing mocked primary-journey test for four readiness areas, release rule, `0/100`, and `100 proposed` in `tests/ui-integration/program-status.spec.ts`

### Implementation

- [ ] T016 [US1] Implement typed error mapping, ETag/304, cache headers, and read-only GET in `apps/api/src/api/routers/program_status.py` and register it in `apps/api/src/api/main.py` (depends on T013)
- [ ] T017 [US1] Implement strict client decoding and authenticated conditional fetch in `apps/web/src/services/program-status.ts` (depends on T014, T016)
- [ ] T018 [P] [US1] Build token-based readiness, gate, release, benchmark, and catalog components in `apps/web/src/components/program-status/` (depends on T014)
- [ ] T019 [US1] Compose the dedicated `apps/web/src/components/pages/ProgramStatusPage.tsx` with honest loading/current/unavailable states (depends on T017, T018)
- [ ] T020 [US1] Register `/program-status` in `apps/web/src/App.tsx` and add the dedicated navigation item in `apps/web/src/components/layout/Sidebar.tsx` without changing `DashboardPage.tsx` semantics (depends on T019)

**Checkpoint**: US1 is a usable, independently demonstrable read-only MVP.

---

## Phase 4: User Story 2 — Understand progress across checkpoints (Priority: P2)

**Goal**: Make imbalance, stalls, and customer-value movement visible through exact-time, exact-commit, meaningfully annotated history.

**Independent Test**: Load the history fixture and verify units, dates/times, commits, change explanations, customer-vs-support imbalance, benchmark hold, and feature-local task scope in both graphs and table fallbacks.

### Tests first

- [ ] T021 [P] [US2] Add failing history derivation tests for trustworthy timestamps, omissions, bounds, units, and feature-local task scope in `tests/program_control_plane/test_program_status_publisher.py`
- [ ] T022 [P] [US2] Add failing chart, fallback-table, reduced-motion, and explanatory-copy tests in `apps/web/src/__tests__/ProgramStatusHistory.test.tsx`

### Implementation

- [ ] T023 [US2] Derive contracted customer, quality, automation, governance, readiness, benchmark, task, and delivery series from exact committed observations in `scripts/program_status/publisher.py` (depends on T021)
- [ ] T024 [US2] Implement reusable accessible Plotly history plus semantic table fallback in `apps/web/src/components/program-status/ProgramHistory.tsx` using the existing renderer (depends on T022, T023)
- [ ] T025 [US2] Add metric meaning, latest change, limitation, blocker, and next-action summaries to `apps/web/src/components/pages/ProgramStatusPage.tsx` (depends on T024)

**Checkpoint**: US2 explains what changed and what decision each trend supports; no ordinal-only or calendar-effort chart remains.

---

## Phase 5: User Story 3 — Trace a blocker to evidence (Priority: P3)

**Goal**: Move from a blocked/stale status to exact safe evidence, original findings, correction disposition, and bounded recovery guidance.

**Independent Test**: Use the blocked/corrected fixture and follow every detail disclosure while confirming non-passing classifications and unsafe links remain rejected.

### Tests first

- [ ] T026 [P] [US3] Add failing finding/correction preservation and safe-evidence projection tests in `tests/program_control_plane/test_program_status_publisher.py`
- [ ] T027 [P] [US3] Add failing keyboard disclosure, focus, status-text, and unsafe-link tests in `apps/web/src/__tests__/ProgramStatusEvidence.test.tsx`

### Implementation

- [ ] T028 [US3] Derive bounded gate, finding, correction, freshness, and recovery summaries in `scripts/program_status/publisher.py` (depends on T026)
- [ ] T029 [US3] Implement accessible evidence and correction disclosures in `apps/web/src/components/program-status/EvidenceDetails.tsx` (depends on T027, T028)

**Checkpoint**: US3 makes blockers inspectable without exposing raw or unsafe content.

---

## Phase 6: User Story 4 — Follow current work and the next safe action (Priority: P4)

**Goal**: Distinguish integration/CI from continued development and show feature-local tasks, checkpoints, authority, blockers, and the sole next eligible action.

**Independent Test**: Load two-lane evidence and verify exclusive branches, integration details, development milestone, approval boundary, and feature-local completion context.

### Tests first

- [ ] T030 [P] [US4] Add failing two-lane, catalog-maturity, task-scope, and next-action derivation tests in `tests/program_control_plane/test_program_status_publisher.py`
- [ ] T031 [P] [US4] Add failing lane, authority, checkpoint timestamp, and product-context component tests in `apps/web/src/__tests__/ProgramStatusWork.test.tsx`

### Implementation

- [ ] T032 [US4] Derive integration/CI events and continued-development lane summaries from allowlisted committed evidence in `scripts/program_status/publisher.py` (depends on T030)
- [ ] T033 [US4] Implement `DeliveryLanes.tsx` and `FeatureProgress.tsx` in `apps/web/src/components/program-status/` with explicit feature/program scope (depends on T031, T032)
- [ ] T034 [US4] Integrate authority-aware next action, blockers, lane history, and exact checkpoint times into `ProgramStatusPage.tsx` (depends on T033)

**Checkpoint**: US4 supports technical prioritization without granting authority or implying the program is nearly complete.

---

## Phase 7: User Story 5 — Stay oriented during stale or failed refresh (Priority: P5)

**Goal**: Refresh automatically on committed identity change while preserving one last-valid atomic view through failure.

**Independent Test**: Exercise unchanged, changed-valid, corrupt, mismatched, interrupted, and initially unavailable responses; verify one-identity rendering and bounded recovery.

### Tests first

- [ ] T035 [P] [US5] Add failing conditional-poll, atomic-swap, race, cleanup, and last-valid reducer tests in `apps/web/src/__tests__/ProgramStatusRefresh.test.tsx`
- [ ] T036 [P] [US5] Extend mocked UI integration coverage for unchanged 304, changed bundle, failed refresh, and no-prior-bundle states in `tests/ui-integration/program-status.spec.ts`

### Implementation

- [ ] T037 [US5] Implement the ten-second conditional poll lifecycle, cancellation, atomic reducer, and last-valid preservation in `apps/web/src/services/program-status.ts` and `ProgramStatusPage.tsx` (depends on T035)
- [ ] T038 [US5] Implement visible stale/failed age, recovery, screen-reader announcement, and unavailable-state components in `apps/web/src/components/program-status/RefreshState.tsx` (depends on T036, T037)
- [ ] T039 [US5] Add a committed-HEAD-only local republish helper mode to `scripts/publish-engineering-program-status.py` without dirty-file observation or runtime Git coupling (depends on T008, T037)

**Checkpoint**: US5 refreshes one exact identity and fails closed without losing orientation.

---

## Phase 8: Cross-cutting verification and delivery readiness

- [ ] T040 [P] Add 200%-zoom, narrow-viewport, keyboard-only, non-color, reduced-motion, and Plotly-failure acceptance coverage in `tests/ui-integration/program-status.spec.ts`
- [ ] T041 [P] Add packaged API+SPA smoke without `.git`, Git executable, network, or source checkout in `tests/e2e/test_program_status.py`
- [ ] T042 [P] Add compatibility regression proving existing workspace routes and `DashboardPage.tsx` behavior remain unchanged in `apps/web/src/__tests__/App.test.tsx`
- [ ] T043 Add build/install wiring for a validated fallback at `src/wright_engineering/static/program-status/current.json`, assert it in `tests/packaging/test_wheel_contents.py`, and document its generated source and rollback in `docs/getting-started/program-status.md`
- [ ] T044 Run and record deterministic quickstart acceptance, including isolated evidence corruption and atomic refresh, in `specs/077-browser-program-status/quickstart.md`
- [ ] T045 Run focused Python, API, web, UI-integration, system, lint, format, type, security/secret, and program-control tests; record exact commands and results in feature evidence
- [ ] T046 Run one independent engineering-usability review and one independent architecture/test review; resolve each stable cause within two bounded repairs and preserve reviewer identity/results
- [ ] T047 Freeze the exact implementation candidate and run Wright's dev push gate; stop for any missing authority before push, PR, merge, deployment, publication, or release

**Checkpoint**: The implementation candidate is independently verified and ready for the separately authorized integration lifecycle.

---

## Dependencies and execution order

```text
T001–T004
    -> T005–T012 (foundation)
        -> US1 T013–T020 (MVP)
            -> US2 T021–T025
            -> US3 T026–T029
            -> US4 T030–T034
            -> US5 T035–T039
                -> T040–T047 (cross-cutting and delivery)
```

- US2, US3, and US4 may begin in parallel after US1 when different files are owned, but one writer must serialize edits to `publisher.py` and `ProgramStatusPage.tsx`.
- US5 depends on the US1 fetch/page boundary and the foundational atomic bundle identity; it does not depend on US2–US4 content components.
- T040–T043 may run in parallel after all relevant stories; T044–T047 are sequential evidence and gate steps.
- No implementation task is eligible before the frozen subject and bounded lease are approved.

## Independent delivery slices

1. **US1 MVP**: honest current readiness and population separation.
2. **US2**: meaningful exact-time history.
3. **US3**: evidence/blocker traceability.
4. **US4**: two-lane work and authority visibility.
5. **US5**: resilient automatic refresh.

Each slice has its own test-first checkpoint and can be demonstrated without executing a benchmark or product engineering process.

## Parallel examples

- After setup, T005 and T006 can run together because publisher and service tests have separate files.
- Within US1, T013–T015 can run together; T018 can proceed independently while T016–T017 establish transport.
- Within each later story, publisher tests and component tests can run together; their implementation joins only at the page composition task.

## Stop conditions

Stop immediately for a public-contract/schema change outside this frozen plan, a new dependency, product or benchmark execution, readiness/authority mutation, unsafe evidence exposure, missing implementation approval or lease, two failed repairs for one stable cause, or any push/PR/merge/release action lacking its explicit gate.
