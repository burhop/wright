# Completion: Runtime Process Output Validator

**Completed:** 2026-09-16

**Branch:** `codex/082-output-content-validation`

**Approved scope:** [implementation-goal.md](implementation-goal.md)

**Tasks:** T001–T034 complete

**Milestones:** M0–M5 complete

## Outcome

Wright now has a runtime process-output validator that checks exact upstream
output revisions, persists immutable evidence, blocks downstream work unless the
current mandatory scope passes, and can send bounded actionable findings to an
eligible producing AI step for correction and fresh revalidation. The same
application service is available to the canonical process runner, packaged CLI,
and thin BaseTool/MCP gateway.

The implementation publishes one versioned report contract with JSON, readable
Markdown, and requirements-traceability CSV projections. Existing Workflows
authoring and run surfaces expose profile/subject/correction settings, stopped
states, and links to saved assessment evidence. The separate reporting
application remains outside this branch.

The 30 input packs are a capability map rather than an all-output acceptance
campaign. Two engineering scenarios are qualified for bounded scopes and the
other 28 are explicitly unsupported. A separate structured demonstration
qualifies the generic local validator and correction path.

## Delivered milestones

| Milestone | Completed tasks | Delivered capability                                                                                                                                                                                                        |
| --------- | --------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| M0        | T001–T006       | Runtime integration inventory, 30-pack capability inventory, versioned domain/schema contracts, immutable SQLite WAL persistence, exact subject snapshots, bounded reader registry, and packaged/workspace profile loading. |
| M1        | T007–T013       | Structured readers and evaluator, canonical validator source/compile/run behavior, CLI and MCP gateway parity, authoring controls, and current-revision release gating.                                                     |
| M2        | T014–T018       | Typed bounded correction packets, one safe producer/check revision segment, persisted 0–3 budget, invalidation/no-progress/resume rules, run diagnostics, and retained real structured AI correction evidence.              |
| M3        | T019–T022       | Versioned report envelope, JSON/Markdown/RTM projections, authenticated get/findings/export/review operations, schema examples, and report-consumer handoff.                                                                |
| M4        | T023–T029       | Frozen jig and heat profiles, bounded STEP and thermal readers, independent controls, retained real engineering processes, and a reconciled 30-pack support map with extension recipes.                                     |
| M5        | T030–T034       | Security/native ownership, installed wheel and Docker boundary proof, three-tier UI evidence, runnable operator documentation, regression gates, and this completion audit.                                                 |

## Retained process demonstrations

### Ordinary AI structured correction

Evidence root:
`artifacts/process-validation/structured-loop/20260916T202647Z/`

- Run `structured-loop-20260916T202659Z` used the configured Hermes endpoint.
- Attempt 1 wrote `length_mm: 98`; assessment
  `assessment-c15a88754bb042aeb37a84d3dfaad2bf` returned `revise` with a
  measured `requirement.out_of_bounds` finding.
- The persisted feedback packet named the exact producer, expected 100 mm
  within 0.2 mm, constraints to preserve, complete recheck set, remaining
  budget, and full-result reference.
- The AI consumed that packet and attempt 2 wrote a distinct output revision
  with `length_mm: 100`; assessment
  `assessment-a867edfeee654ea9a2e196ea3ff740a2` passed.
- The downstream AI consumer ran only after the current revision passed. The
  retained assertions confirm the controlled defect, typed feedback delivery,
  new output identity/digest, current pass, and consumer release.
- `tests/external/process_validation/test_structured_loop_evidence.py`
  independently checks the retained manifest, hashes, run events, attempts,
  feedback, assessments, and consumer disposition.

### AI/MCP drill-jig correction

Evidence root:
`artifacts/process-validation/engineering/20260916T213859Z/jig/`

- Run `engineering-jig-20260916T213904Z` owned an isolated selected AgentCAD
  MCP process and produced actual STEP snapshots.
- Attempt 1 measured H1/H2 X centers at 31/171 mm; assessment
  `assessment-784aa83e624c471daf66cf8d9c2247bb` returned `revise` with exact
  evidence selectors and 30/170 mm correction targets.
- The AI/MCP producer consumed one persisted feedback delivery and created a
  distinct attempt-2 STEP snapshot. Assessment
  `assessment-e629d4174e524959a9191a22ba596d31` remeasured 30/170 mm centers
  and passed the complete six-check seat scope; the consumer was released.
- Both STEP revisions remain in `snapshots/` and the manifest pins their
  SHA-256 digests.

### Heat-spreader numerical validation

Evidence root:
`artifacts/process-validation/engineering/20260916T213859Z/heat/`

- Run `engineering-heat-20260916T214041Z` inspected actual coarse/fine
  baseline and revision fields plus the sizing decision.
- The bounded reader independently derived analytical-rise error, heat balance,
  refinement sensitivity, maximum temperatures, and selected candidate. It
  observed approximately 50.0 °C for 40 mm and 41.667 °C for 60 mm and verified
  selection of the 60 mm revision.
- Assessment `assessment-dadcac109d70423992bd47228ca54d45` passed and
  released the consumer. Retained assertions confirm actual-field measurement
  and read-only copying of source inputs.
- `tests/external/process_validation/test_engineering_process_evidence.py`,
  `test_geometry.py`, and `test_thermal.py` independently verify the retained
  processes and positive, alternative, defect, unit, datum, and boundary
  controls.

The parent engineering manifest pins every retained file. The evidence
verifiers passed during the final regression run.

## Requirement audit

| Requirement | Authoritative implementation and proof                                                                                                                                                                                                              | Result    |
| ----------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------- |
| FR-001      | `process_validation/application.py`, CLI/gateway adapters, canonical runner tests, and service/MCP parity assertions invoke one application service without a corpus gate.                                                                          | Satisfied |
| FR-002      | Core subject/producer/reference contracts, repository registration, subject resolver, exact attempt/port/revision/hash pins, and stale/foreign identity tests bind every assessment to immutable inputs.                                            | Satisfied |
| FR-003      | Packaged baseline/profile references include version and digest; frozen requirements retain methods, tolerances, applicability, exclusions, source locators, and unresolved scope.                                                                  | Satisfied |
| FR-004      | Reader registry and profile composition use capability IDs; packaged resources load through `importlib.resources` in an extracted wheel and isolated Docker runtime.                                                                                | Satisfied |
| FR-005      | Structured readers inspect actual values/files, geometry reads actual STEP circle placements, and thermal checks derive values from actual field/balance/refinement inputs. Reader identity, method, selectors, and evidence strength are retained. | Satisfied |
| FR-006      | `feedback.py` and typed findings include check/requirement IDs, exact owner, selector/evidence, expected/observed values, unit/frame/tolerance, explanation, correction target, routing, preserved constraints, and recheck IDs.                    | Satisfied |
| FR-007      | Contract aggregation and evaluator tests preserve pass, fail/revise, blocked, inconclusive, error, pending-review, and justified-not-applicable distinctions plus explicit completeness and physical-evidence scope.                                | Satisfied |
| FR-008      | Canonical runner gates the consumer on a conclusive pass for the exact current revision and entire mandatory profile. Empty scope, missing roles/capabilities, mixed unknown/error, and stale passes fail closed.                                   | Satisfied |
| FR-009      | One explicit feedback relationship targets the eligible producer; 0–3 revisions, preserved constraints, complete-profile recheck, and unchanged pinned requirements are enforced. Structured and jig demonstrations prove correction.               | Satisfied |
| FR-010      | Run records/repository persist budgets, feedback, attempts, invalidation, idempotency, and terminal state. Rework/resume tests prove no-progress, exhaustion, cancellation, stale identity, and budget persistence.                                 | Satisfied |
| FR-011      | Readers/evaluator are read-only; only the runner executes the configured producer. Security and native-boundary tests reject traversal, mutation, unknown side effects, unsafe correction topology, and in-place application edits.                 | Satisfied |
| FR-012      | `wright.process-validation-report/1`, generated schema/examples, Markdown, and RTM CSV are produced from one immutable assessment; authenticated service/API/CLI/gateway read and export operations are implemented.                                | Satisfied |
| FR-013      | Immutable historical assessments and reviews remain accessible; live currentness is computed fail closed; authenticated late review derives actor/authority and appends a new assessment.                                                           | Satisfied |
| FR-014      | Retained structured, jig, and heat processes are verified. Coverage schema version 2 contains exactly 30 scenario records: two bounded engineering scenarios are `qualified`, 28 are `unsupported`, and no sibling qualification is inferred.       | Satisfied |
| FR-015      | Structured, geometry, and thermal suites include valid, alternative, targeted-defect, missing, unit/frame, numerical-boundary, stale, confinement, and error-routing controls; existing workflow tests pass.                                        | Satisfied |
| FR-016      | Installed-wheel and no-network Docker tests prove offline resources/CLI/gateway/readers; API tests cover authentication/ownership; security tests cover trace propagation and owned native lifecycle; served authoring behavior remains functional. | Satisfied |
| FR-017      | Normal Workflows authoring exposes profiles, exact subjects, correction target/budget, held/repairing/exhausted states, and assessment links for live/recovered runs. Component, mocked Playwright, and FastAPI E2E evidence pass.                  | Satisfied |

## Success-criteria audit

| Criterion | Evidence                                                                                                                                                                                                          | Result    |
| --------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------- |
| SC-001    | Canonical structured and engineering runs release consumers only after the exact current output passes; fail/missing/stale/error cases hold.                                                                      | Satisfied |
| SC-002    | The retained structured and jig runs show real configured AI feedback consumption, new output identity, fresh assessment, pass, and release. Rework tests cover bounded stop/resume behavior.                     | Satisfied |
| SC-003    | Every nonpassing mandatory check in control and retained evidence has a typed, source/evidence-linked finding or precise blocked/error disposition; the Markdown projection and UI display readable explanations. | Satisfied |
| SC-004    | Reporting consistency tests validate JSON schema/examples and reconcile assessment ID/digest, effective currentness verdict, Markdown, and every RTM row without importing validator internals.                   | Satisfied |
| SC-005    | Structured, jig, and heat initial slices are verified. The support map accounts for all 30 packs and rejects mandatory unsupported capabilities.                                                                  | Satisfied |
| SC-006    | Design-check, approval/resume, canonical-source, authoring round-trip, component, mocked UI integration, served FastAPI E2E, and production web build checks pass.                                                | Satisfied |
| SC-007    | Subject/native security tests and retained manifests prove source protection and historical retention; repository/rework tests prove budgets cannot reset and stale passes cannot release newer output.           | Satisfied |

## Final verification

Final checks ran from `D:/repos/wright` on 2026-09-16 with isolated temp/cache
roots. Cross-package pytest suites were intentionally run by their native test
roots because this repository contains independent `tests` packages and
`conftest.py` modules.

| Gate                                                                                                             | Result                                                            |
| ---------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------- |
| Core process-validation contracts                                                                                | 22 passed                                                         |
| Data-vault immutable repository                                                                                  | 10 passed                                                         |
| Workspace validator, canonical workflow, rework/resume, design-check, reporting, security, coverage, and history | 199 passed                                                        |
| Authenticated API routes                                                                                         | 3 passed                                                          |
| Retained structured/engineering evidence, reader controls, native/canonical security, and FastAPI E2E            | 34 passed                                                         |
| Extracted-wheel/offline CLI/gateway/distribution                                                                 | 2 passed; fresh wheel built and inspected                         |
| Affected web component suites                                                                                    | 10 files, 130 tests passed                                        |
| Served Workflows Playwright journeys                                                                             | 2 passed: validator journey and existing workspace composer entry |
| Web TypeScript/Vite production build                                                                             | Passed, 901 modules transformed                                   |
| Targeted ESLint                                                                                                  | Passed                                                            |
| Ruff lint across feature Python files                                                                            | Passed                                                            |
| Strict MkDocs build                                                                                              | Passed                                                            |
| Prettier for final changed web/docs files and `git diff --check`                                                 | Passed                                                            |

The only emitted test warning was the existing Starlette/httpx deprecation
notice. Vite also emitted its existing native-config and large-chunk notices.
Neither changes validator behavior or the acceptance result.

Distribution details, including the extracted wheel contents and no-network
Docker smoke, remain in [evidence/distribution.md](evidence/distribution.md).

## Reporting-branch handoff

The reporting branch should consume
[`wright.process-validation-report/1`](contracts/report-consumer.md) and its
[`ValidationReport` schema](contracts/schemas/ValidationReport.schema.json).
It must validate the published examples without importing validator internals,
compute the effective verdict as
`currentness.is_current AND assessment.summary.release_eligible`, retain every
traceability row and scope limitation, and resolve opaque evidence references
through authorized workspace operations. Authenticated get, paged findings,
JSON/Markdown/CSV export, and human-review routes are documented in the
handoff. This feature does not include a report dashboard.

## Capability limits

- `structured@1` checks declared selectors and constraints in bounded inline,
  JSON, CSV, text, Markdown, and HTML content. It does not infer undeclared
  document meaning.
- `step-seat-geometry@1` qualifies only H1/H2 seat centers and diameters for
  `parametric-drill-jig-01` in its frozen workpiece datum. It does not establish
  general CAD correctness, manufacturability, collisions, fit, or physical
  acceptance.
- `thermal-field@1` qualifies only the frozen 40/60 mm heat-spreader field,
  balance, refinement, analytical-rise, and selection scope. It is not a solver,
  CFD qualification, CAD/manufacturing assessment, or physical thermal test.
- The remaining 28 engineering packs are explicitly unsupported until their
  source-backed profiles, readers, controls, and real process evidence satisfy
  the published extension recipes.
- No engineering approval, supplier submission, manufacturing action, device
  dispatch, physical qualification, push, merge, release, or publication was
  performed or implied.
