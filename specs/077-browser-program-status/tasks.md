# Tasks: Browser Program Status

**Input**: Design documents from `/specs/077-browser-program-status/`

**Prerequisites**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/`, and completed requirements checklists

**Authority**: This is a proposed implementation task graph. No task below may start until the exact EPP-F01B `material_change` and `feature_implementation` subject and bounded lease are approved.

**Tests**: Required by the feature specification and Wright constitution. Write each listed test first and observe the intended failure before implementing its behavior.

## Phase 1: Setup and contract fixtures

**Purpose**: Establish owned paths and test data without changing runtime behavior.

- [x] T001 Create the EPP-F01B publisher module skeleton in `scripts/program_status/__init__.py`, `scripts/program_status/publisher.py`, and `scripts/publish-engineering-program-status.py`
- [x] T002 [P] Add valid, empty, stale, corrupt, identity-mismatch, unsafe-link, closed work-registry, governed use-case-registry, canonical test-ledger, absent-assignment, and unavailable-history fixtures under `tests/fixtures/program-status/`
- [x] T003 [P] Add TypeScript contract types and runtime decoder skeleton in `apps/web/src/services/program-status.ts`
- [x] T004 [P] Add API Pydantic response/error schema skeleton in `apps/api/src/api/schemas/program_status.py`

**Checkpoint**: Owned files exist; no route, publisher action, or visible page is active.

---

## Phase 2: Foundational identity and read boundaries

**Purpose**: Complete the shared validation, atomic publication, and runtime read boundary that blocks every user story.

- [x] T005 [P] Add failing exact-dashboard preservation, digest-bound 20-source catalog mutation/current activation-correction acceptance, publisher identity, action/benchmark/correction relations, work-registry arithmetic, exact/absent assignments, unique use-case and `EPP-PROC-001..100` IDs, remaining arithmetic, wrong-stage-source/nonexistent-subject/resolved-verdict/equal-author-verifier negatives, test-ledger terminal-rerun/exact cross-language identity/run-key/runs digest/parametrization/cardinality/component-overlap/summary-exclusion/arithmetic/pass-rate handling, canonical path/URL, causal order, deterministic regeneration, concurrent-reader, and Windows replacement-failure tests in `tests/program_control_plane/test_program_status_publisher.py`
- [x] T006 [P] Add failing last-valid, fallback, corruption, bounds, identity/catalog, concurrent-read, heartbeat, and runtime relational-invariant tests for identity, actions, benchmark, evidence, corrections, catalog, lanes, observations, task registries, assignments, unique/ranged use cases and remaining arithmetic, selected test-source time/terminal/role/identities/digest/counts, disjointness, canonical totals/pass rate, and unavailable history in `packages/tool_registry/tests/test_program_status.py`
- [x] T007 Implement and validate the closed work/use-case/test source contracts and honest initial committed registry records under `docs/programs/engineering-process-platform/`; implement the exact digest-bound 20-source catalog including the current F01B activation-correction schema; reject every unlisted route; validate Git/EPP-F01 identity; enforce unique/ranged use-case identities plus exact stage source/parser subject/verdict/binding/author-verifier rules; verify test-ledger prior-revision append-only continuity, unique run IDs/run keys, deterministic latest-terminal selection, exact cross-language NFC/UTF-8-framed identity/run-key and canonical-JSON runs digests, `total = len(test_case_ids)`, and pairwise component disjointness; embed the dashboard unchanged; derive independently reconcilable supplements; and digest canonical source+dashboard+supplement in `scripts/program_status/publisher.py` (depends on T005)
- [x] T008 Implement same-directory temporary write, flush/fsync, validation, `os.replace`, supported parent-directory sync, failure-preserves-prior behavior, and unchanged-identity no-op in `scripts/program_status/publisher.py` (depends on T007)
- [x] T009 Implement the CLI arguments and non-secret exact-identity result in `scripts/publish-engineering-program-status.py` (depends on T008)
- [x] T010 Implement bounded bundle, source-catalog, publisher-state, work-registry, use-case-registry, and test-ledger validation; explicit `$id` registration of all five EPP-F01B schemas plus the authoritative dashboard schema; raw-attestation/evidence validation without source-byte recomputation; independent canonical-dashboard/bundle recomputation; all T006 relational invariants; installed-absent-only fallback; installed-invalid typed failure; and immutable result types in `packages/tool_registry/src/tool_registry/program_status.py` (depends on T006, T008)
- [x] T011 Export the program-status reader through `packages/tool_registry/src/tool_registry/__init__.py` and wire stable data-root configuration in `apps/api/src/api/composition.py` (depends on T010)
- [x] T012 Add structured trace-safe read/publication logging without evidence bodies or private paths in `scripts/program_status/publisher.py` and `packages/tool_registry/src/tool_registry/program_status.py` (depends on T008, T010)

**Checkpoint**: A committed fixture can be deterministically published and read as one identity; invalid newer data cannot replace a valid bundle.

---

## Phase 3: User Story 1 — See honest program readiness (Priority: P1) 🎯 MVP

**Goal**: Open one authenticated page and understand the four independent readiness areas, release posture, governed `0/100` benchmark, and separate proposed-story catalog.

**Independent Test**: Publish the mixed-state fixture, open `/program-status`, and verify the four areas, gate counts/blockers/freshness, release explanation, benchmark hold context, and catalog separation without reading raw files.

### Tests first

- [x] T013 [P] [US1] Add failing bundle 200/304 plus publisher-heartbeat 200/404/422/503, engineer/admin read, unauthenticated rejection, typed-error, exact-dashboard, complete at-a-glance supplement, and forbidden-field API tests in `apps/api/tests/test_program_status_api.py`
- [x] T014 [P] [US1] Add failing strict decoder, sole-current-action precedence, typed zero-benchmark context, work/use-case/test unavailable states, required `data-testid`, and loading/current/unavailable overview tests in `apps/web/src/__tests__/ProgramStatusPage.test.tsx`
- [x] T015 [P] [US1] Add a failing mocked primary journey that answers the six at-a-glance questions, preserves four readiness areas and release rule, explains `0/100`, separates the proposed catalog, labels historical/current actions correctly, and keeps unavailable committed evidence honest in `tests/ui-integration/program-status.spec.ts`

### Implementation

- [x] T016 [US1] Implement typed error mapping, ETag/304 and private cache headers for the bundle, no-store publisher heartbeat, and both read-only GETs in `apps/api/src/api/routers/program_status.py`; register them in `apps/api/src/api/main.py` (depends on T011, T013)
- [x] T017 [US1] Implement strict closed-version decoding of the exact EPP-F01 dashboard, EPP-F01B supplement/source identity, and separate publisher status; independently recompute typed per-use-case funnels and selected test-source identity digests/disjointness/counts/pass rates; validate publisher append-only/latest-selection attestations without claiming access to absent source history; and enforce every T006 relation client-side with negative fixtures before authenticated conditional fetching in `apps/web/src/services/program-status.ts` (depends on T014, T016)
- [x] T018 [P] [US1] Build the first-viewport `AtAGlanceSummary` plus token-based readiness, gate, release, benchmark-context, historical-action disclosure, sole-current-action, and proposed-catalog components in `apps/web/src/components/program-status/` (depends on T014)
- [x] T019 [US1] Compose the dedicated `apps/web/src/components/pages/ProgramStatusPage.tsx` with honest loading/current/unavailable states (depends on T017, T018)
- [x] T020 [US1] Register `/program-status` in `apps/web/src/App.tsx` and add the dedicated navigation item in `apps/web/src/components/layout/Sidebar.tsx` without changing `DashboardPage.tsx` semantics (depends on T019)

**Checkpoint**: US1 is a usable, independently demonstrable read-only MVP.

---

## Phase 4: User Story 2 — Understand progress across checkpoints (Priority: P2)

**Goal**: Make imbalance, stalls, and customer-value movement visible through exact-time, exact-commit, meaningfully annotated history.

**Independent Test**: Load the history fixture and verify units, dates/times, commits, change explanations, customer-vs-support imbalance, benchmark hold, and feature-local task scope in both graphs and table fallbacks.

### Tests first

- [x] T021 [P] [US2] Add failing metric-ID/unit/counting-rule/source-class pairing, transition/parent causal order, deterministic latest-change, omission/bounds, program and feature task burn-up, canonical test checkpoint selection/categories/pass rate, and customer/roadmap scope tests in `tests/program_control_plane/test_program_status_publisher.py`
- [x] T022 [P] [US2] Add failing task burn-up, test-outcome, customer-capability, readiness/benchmark chart, tooltip, semantic-table, reduced-motion, and graph-context tests in `apps/web/src/__tests__/ProgramStatusHistory.test.tsx`

### Implementation

- [x] T023 [US2] Derive each fixed-semantic customer, quality, automation, governance, readiness, benchmark, program-task, feature-task, delivery, and canonical test-outcome series from exact causally ordered committed observations in `scripts/program_status/publisher.py` (depends on T021)
- [x] T024 [US2] Implement reusable accessible Plotly task burn-up, test outcomes, roadmap/customer-capability, readiness, and benchmark histories plus semantic table fallbacks in `apps/web/src/components/program-status/ProgramHistory.tsx` using the existing renderer (depends on T022, T023)
- [x] T025 [US2] Add metric meaning, latest change, limitation, blocker, and next-action summaries to `apps/web/src/components/pages/ProgramStatusPage.tsx` (depends on T024)

**Checkpoint**: US2 explains what changed and what decision each trend supports; no ordinal-only or calendar-effort chart remains.

---

## Phase 5: User Story 3 — Trace a blocker to evidence (Priority: P3)

**Goal**: Move from a blocked/stale status to exact safe evidence, original findings, correction disposition, and bounded recovery guidance.

**Independent Test**: Use the blocked/corrected fixture and follow every detail disclosure while confirming non-passing classifications and unsafe links remain rejected.

### Tests first

- [x] T026 [P] [US3] Add failing byte-semantic dashboard preservation, publisher raw-attestation evidence, internal detail, exact canonical path/digest, traversal/lookalike/empty/dot/duplicate-segment rejection, parsed optional exact-GitHub credential/port/query/fragment/slug/path rejection, source-catalog boundary, and packaged identity-only evidence tests in `tests/program_control_plane/test_program_status_publisher.py`
- [x] T027 [P] [US3] Add failing keyboard disclosure, focus, status-text, correction/finding/verification relationship and verdict, canonical-path, and unsafe-URL tests in `apps/web/src/__tests__/ProgramStatusEvidence.test.tsx`

### Implementation

- [x] T028 [US3] Build the bounded internal evidence index and closed reciprocal correction/finding/verification graph, deriving all claim/finding counts from exact ID sets; include safe summary, freshness, recovery, availability, parsed optional exact-commit GitHub URL, and exactly one matching detail for every reference in `scripts/program_status/publisher.py` (depends on T026)
- [x] T029 [US3] Implement accessible internal evidence links, exact identity, correction claims, finding resolution links, verification verdict/blocking outcome, risk/decision disclosure, and honest raw-content availability in `apps/web/src/components/program-status/EvidenceDetails.tsx` (depends on T027, T028)

**Checkpoint**: US3 makes blockers inspectable without exposing raw or unsafe content.

---

## Phase 6: User Story 4 — Follow current work and the next safe action (Priority: P4)

**Goal**: Distinguish integration/CI from continued development and show feature-local tasks, checkpoints, authority, blockers, and the sole next eligible action.

**Independent Test**: Load two-lane evidence and verify exclusive branches, integration details, development milestone, approval boundary, and feature-local completion context.

### Tests first

- [x] T030 [P] [US4] Add failing two-lane order/uniqueness, continued-lane field rejection, catalog sum, lease projection, program/feature task totals and remaining arithmetic, undecomposed roadmap disclosure, exact active-assignment identity/task/title/state/branch/worktree-or-lane/purpose evidence, all-use-case and 100-process funnel stage separation, and action authority tests in `tests/program_control_plane/test_program_status_publisher.py`
- [x] T031 [P] [US4] Add failing work summary, active-assignment unavailable/exact states, use-case funnel, proposed-population separation, lane, authority, checkpoint timestamp, and product-context tests in `apps/web/src/__tests__/ProgramStatusWork.test.tsx`

### Implementation

- [x] T032 [US4] Derive closed lanes, safe lease, registered program/feature tasks, exact active assignments, all-use-case and 100-process funnels, separate catalog summary, sole current action, historical dashboard action, and non-granting metric/benchmark/lane actions from catalog-admitted committed evidence in `scripts/program_status/publisher.py` (depends on T030)
- [x] T033 [US4] Implement `DeliveryLanes.tsx`, `WorkProgress.tsx`, `ActiveAssignments.tsx`, and `UseCaseFunnels.tsx` with explicit evidence/population semantics and semantic tables in `apps/web/src/components/program-status/` (depends on T031, T032)
- [x] T034 [US4] Put the six-answer work/use-case/test/action summary above deep governance evidence and integrate the sole authority-aware action, historical dashboard action, non-governing guidance, blockers, lane history, and exact checkpoint times into `ProgramStatusPage.tsx` (depends on T033)

**Checkpoint**: US4 supports technical prioritization without granting authority or implying the program is nearly complete.

---

## Phase 7: User Story 5 — Stay oriented during stale or failed refresh (Priority: P5)

**Goal**: Refresh automatically on committed identity change while preserving one last-valid atomic view through failure.

**Independent Test**: Exercise unchanged, changed-valid, corrupt, mismatched, interrupted, and initially unavailable responses; verify one-identity rendering and bounded recovery.

### Tests first

- [x] T035 [P] [US5] Add failing conditional-poll, atomic-swap, race, cleanup, and last-valid reducer tests in `apps/web/src/__tests__/ProgramStatusRefresh.test.tsx`
- [x] T036 [P] [US5] Extend mocked UI integration coverage for unchanged 304, changed bundle, failed refresh, and no-prior-bundle states in `tests/ui-integration/program-status.spec.ts`

### Implementation

- [x] T037 [US5] Implement the five-second conditional poll lifecycle, cancellation, atomic reducer, and last-valid preservation in `apps/web/src/services/program-status.ts` and `ProgramStatusPage.tsx` (depends on T035)
- [x] T038 [US5] Implement visible stale/failed age, recovery, screen-reader announcement, unavailable-state, and separate publisher-heartbeat state in `apps/web/src/components/program-status/RefreshState.tsx` (depends on T036, T037)
- [x] T039 [US5] Implement standard bounded `--watch-committed` publisher mode with a declared two-second default, atomically written separate heartbeat state, its contributor command in `docs/getting-started/quickstart-local.md`, and commit-change-to-install plus heartbeat-failure tests without dirty-file observation or API Git coupling (depends on T008, T037)

**Checkpoint**: US5 refreshes one exact identity and fails closed without losing orientation.

---

## Phase 8: Cross-cutting verification and delivery readiness

- [x] T040 Add build/install wiring for the validated fallback, digest-bound source catalog, all five EPP-F01B schemas, and promoted `docs/programs/engineering-process-platform/schemas/dashboard.schema.json` (registered by its `dashboard-v2.schema.json` `$id`) under `src/wright_engineering/static/program-status/`; assert exact wheel contents and source-free schema resolution in `tests/packaging/test_wheel_contents.py`; prove data-root preservation across update/rollback/uninstall in `tests/native_runtime/test_program_status_lifecycle.py`; and document identity/source-precedence/work/use-case/test/rollback semantics in `docs/getting-started/program-status.md`; require the lifecycle job on Windows, Linux, and macOS
- [x] T041 [P] Add packaged API+SPA smoke without `.git`, Git executable, network, or source checkout in `tests/e2e/test_program_status.py` (depends on T040)
- [x] T042 [P] Add the six-question at-a-glance and graph-comprehension walkthroughs plus 200%-zoom, narrow-viewport, keyboard-only, non-color, tooltip, reduced-motion, `data-testid`, semantic-table, and Plotly-failure coverage in `tests/ui-integration/program-status.spec.ts`
- [x] T043 [P] Add compatibility regression proving existing workspace routes and `DashboardPage.tsx` behavior remain unchanged in `apps/web/src/__tests__/App.test.tsx`
- [x] T044 Add end-to-end committed fixture change → publisher install → ETag change → atomic browser refresh plus separate heartbeat refresh coverage in `tests/ui-integration/program-status.spec.ts` (depends on T039)
- [x] T045 Run and record deterministic quickstart acceptance, including work/assignment provenance, wrong-source/missing-subject/verdict/independence use-case negatives, cross-language digest golden fixtures and test-count cardinality, canonical test-history edge cases, isolated evidence corruption, publisher state, internal evidence navigation, and automatic committed refresh, in `specs/077-browser-program-status/quickstart.md`
- [x] T046 Run focused publisher, all five schemas plus the source catalog and three registry contracts, EPP-F01B API, named existing surface-auth Linux baselines, web, UI-integration, packaged/native lifecycle (including POSIX owned-listener detection), lint, format, type, security/secret, and program-control checks; record commands/results by stable cause, distinguish pre-existing baseline failures from feature regressions, and preserve an explicit Windows/Linux/macOS atomic-replacement/native-lifecycle matrix in feature evidence
- [x] T047 Run the scripted engineering-usability comprehension review and independent architecture/test review; resolve each stable cause within two bounded repairs and preserve reviewer identity/results
- [ ] T048 Freeze the exact implementation candidate and run Wright's dev push gate; stop for any missing authority before push, PR, merge, deployment, publication, or release

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
                -> T040–T048 (cross-cutting and delivery)
```

- US2, US3, and US4 may begin in parallel after US1 when different files are owned, but one writer must serialize edits to `publisher.py` and `ProgramStatusPage.tsx`.
- US5 depends on the US1 fetch/page boundary and the foundational atomic bundle identity; it does not depend on US2–US4 content components.
- T040 precedes packaged smoke T041; T042–T043 may run in parallel after relevant stories; T044–T048 are sequential integration evidence and gates.
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
