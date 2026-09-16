# Feature Specification: Engineering Output Content Validation

**Feature Branch**: `codex/082-output-content-validation`
**Created**: 2026-09-16
**Status**: Prepared for implementation review; G0 not ready
**Input**: Validate the content and requirements traceability of the 30 current engineering input packs after every process flow produces data. Preserve the earlier analysis and provide a future-agent implementation goal.

## User Scenarios & Testing

### User Story 1 - Trust a measured output verdict (Priority: P1)

An engineer independently checks retained heat-spreader and drill-jig outputs and can distinguish a correct analysis from a design that meets its requirements.

**Why this priority**: These numerical and geometric pilots establish the shared evidence contract before extending it to harder families.
**Independent Test**: Evaluate qualified positive, alternative and defective controls, then both retained pilots; follow each verdict back to an original requirement and measured artifact without starting a generation run.

**Acceptance Scenarios**:
1. **Given** a completed generation cohort and frozen requirements, **when** an output is checked, **then** its actual content supplies the measured values, with source identity, method, units and uncertainty.
2. **Given** a correct analysis that finds no feasible design, **when** results are assessed, **then** content can be verified while design compliance fails.
3. **Given** a missing observation, reader crash or interval crossing a limit, **when** evaluated, **then** the result cannot pass and retains its distinct reason.

### User Story 2 - Cover all engineering families (Priority: P1)

An engineer applies shared checks with case-specific requirements across the ten families and all 30 input packs.

**Why this priority**: A useful final validation campaign cannot omit difficult formats or entire families.
**Independent Test**: Each family accepts a valid alternative, detects targeted defects at the intended check, and gives every required part, candidate and requirement a disposition for all three retained cases.

**Acceptance Scenarios**:
1. **Given** the 30 source packs, **when** requirements are frozen, **then** prose, tables, images and authorized amendments are accounted for with source locators.
2. **Given** a changed datum, missing candidate or swapped net, **when** the affected output is checked, **then** the intended check detects it even if the report claims success.
3. **Given** an unavailable required reader, **when** coverage is reported, **then** implementation remains incomplete and the case is blocked rather than accepted as not applicable.

### User Story 3 - Inspect traceability in the workspace (Priority: P2)

An engineer opens a run's validation evidence from the existing workspace and sees the requirements matrix, measured evidence and current versus historical outcomes.

**Why this priority**: Reviewers need an accessible explanation of each verdict and its scope.
**Independent Test**: Enter the served application through Workflow/Workflows, open evidence, and reconcile its values with exported reports while exercising existing authoring.

**Acceptance Scenarios**:
1. **Given** a failed requirement, **when** the engineer opens its row, **then** the source, test, measured value, artifact and failure reason are accessible.
2. **Given** a newer failed or incomplete evaluation, **when** the view refreshes, **then** an older pass stays historical and cannot mask it.
3. **Given** original generation history, **when** content results appear, **then** execution, content, compliance and physical evidence remain distinct.

### User Story 4 - Replay and review a complete campaign (Priority: P2)

An authorized reviewer completes or disputes subject-bound judgments, and an engineer can reproduce all 30 evaluations without changing the original runs.

**Why this priority**: Results must survive interruption, changing inputs and later review.
**Independent Test**: Replay a frozen cohort, interrupt a reader, retry a terminal attempt and append a late review; verify preserved originals and immutable prior reports.

**Acceptance Scenarios**:
1. **Given** a later authorized review, **when** recorded, **then** a new assessment references the exact subject and leaves earlier evidence unchanged.
2. **Given** a known failure and a second blocked check, **when** aggregated, **then** noncompliance and incomplete evaluation are both visible.
3. **Given** source changes during a read, **when** finalizing, **then** mixed revisions cannot earn a pass.
4. **Given** a complete campaign with genuine design failures, **when** closed, **then** failures are retained with reproducible findings rather than removed to obtain 30 green results.

### Edge Cases

- Foreign-run artifacts, stale source hashes, missing variants, empty arrays, invalid units, nonfinite numbers and unsupported file versions.
- Tolerance boundaries, uncertainty intervals, symmetric geometry with a wrong key, and radial versus diametral clearance.
- Correct report of infeasibility versus an incorrect success claim; mixed failure/error/blocked outcomes.
- Unresolved source conflicts, narrowly scoped amendments and unperformed required reviews.
- Late review of a stale subject, terminal retry versus nonterminal resume, and an older pass behind newer incomplete work.
- Malicious archive paths, excessive parser resources, and native readers attempting to save original files.

## Requirements

### Functional Requirements

FR-001 through FR-016 retain the meaning of CVR-01 through CVR-16 in the [earlier plan](../081-engineering-workflow-templates/content-validation/plan.md).

- **FR-001**: Require and freeze a cohort of exactly 30 current, completed generation attempts with all required stable same-attempt outputs and verified identities before validation implementation is activated.
- **FR-002**: Record versioned atomic requirements from every authoritative input source and narrowly scoped amendment.
- **FR-003**: Separate requirements, verification methods and observations; freeze limits before evaluation and prevent generated reports or execution approvals from amending them.
- **FR-004**: Compose reusable checks by artifact capability, with case-specific data profiles rather than separate checking engines.
- **FR-005**: Independently inspect actual artifacts and bind every observation to its artifact and measurement method.
- **FR-006**: Verify semantic correspondence among native sources, exports, meshes, fields, reports and handoff bundles.
- **FR-007**: Apply explicit units, frames, applicability, finite tolerances and uncertainty; document bound inclusivity and near-zero rules.
- **FR-008**: Cover all ten families and 30 cases, including their required parts, alternatives, candidate grids and refinements.
- **FR-009**: Qualify each hard-check mechanism with independent known-good references, valid alternatives, targeted defects, boundaries and applicable transformation relationships.
- **FR-010**: Retain immutable attempts, findings, review decisions and assessment revisions separately from generation history.
- **FR-011**: Distinguish pass, fail, inconclusive, blocked, justified not-applicable and error; known failure remains visible even when evaluation is incomplete.
- **FR-012**: Produce machine-readable, tabular, human-readable and test-runner reports from the same results with requirement-to-test-to-measurement-to-artifact links.
- **FR-013**: Display current content verification, design compliance, coverage and pending review separately from historical generation achievements.
- **FR-014**: Support confined read-only replay, bounded resources, safe cancellation, identity-checked resume and terminal retries with new identities.
- **FR-015**: Preserve workspace authority, original files, existing authoring, offline operation and supported distribution boundaries; review attribution must reflect the actual authorized actor.
- **FR-016**: Deliver reproducible findings, limitations, qualification evidence and a final checkpoint for the whole corpus.
- **FR-017**: Prevent evaluator defects from being mislabeled engineering failures and prevent unauthenticated attribution or automated judgments from impersonating human review.

### Key Entities

- **Cohort and artifact subject**: selected current case attempts, exact inputs and retained outputs, with provenance and stable identities.
- **Source baseline, requirement and decision**: controlling source statements, classifications, limits and explicit resolution of conflicts or applicability.
- **Acceptance profile and reader identity**: required verification methods, evidence capabilities, versions and qualification.
- **Measurement and assertion result**: observed facts, method, uncertainty and check verdict linked to evidence.
- **Validation attempt and finding**: independent evaluation history, diagnostic classification and reproducer.
- **Review record and assessment revision**: authorized subject-bound judgment and immutable derived outcome.

## Success Criteria

### Measurable Outcomes

- **SC-001**: All 30 selected cases have reproducible eligibility evidence and a source inventory; every mandatory requirement has a verification method and final disposition.
- **SC-002**: Every in-scope hard-check mechanism accepts its qualified valid controls and detects its targeted defective controls at the intended check.
- **SC-003**: Every verdict in every report and the workspace reconciles with the same persisted evidence, including mixed failures and incomplete reviews.
- **SC-004**: Replay, interruption and review tests leave original run records and artifacts unchanged; no source change, skipped check or stale result earns a current pass.
- **SC-005**: The final campaign covers 30/30 cases with conclusive outcomes or explicitly identified outstanding evidence; corpus completion is claimed only when mandatory measurements and reviews are complete. Design failures do not prevent honest completion.
- **SC-006**: Normal offline checking and report inspection pass supported distribution tests, and workspace evidence access preserves existing authoring in all three required UI testing tiers.

## Assumptions

- The user-confirmed scope is 30 current packs, not 300.
- G0 remains mandatory. As of the preparation snapshot, 24 cases have current outputs; the three bracket and three sheet-metal cases do not.
- This package reviews and operationalizes the saved plan. Implementation starts after its human review and G0; past instructions not to change the active 081 selector apply to that historical checkout.
- Generation repair, physical qualification, public promotion, device dispatch, supplier submission and publication are separate work.
- Existing authoritative source evidence is reused. New source conflicts remain explicit; no tolerance is inferred from a candidate merely to make it pass.
- Tests of checker correctness, isolation, state semantics and UI behavior are explicitly required.
