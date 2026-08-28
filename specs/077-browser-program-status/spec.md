# Feature Specification: Browser Program Status

**Feature Branch**: `codex/epp-continued-development-reconciled`

**Created**: 2026-08-28

**Status**: Specified — planning only; implementation is not yet authorized

**Input**: User description: "Deliver a browser-visible, evidence-derived program dashboard that lets one developer manage customer value and the AI development process, with meaningful metrics and graphs over committed checkpoints."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - See Honest Program Readiness (Priority: P1)

As a Wright maintainer, I can open one read-only browser page and immediately understand product, benchmark, commercial, and program-health readiness without mistaking progress in one area for readiness in another.

**Why this priority**: The program cannot be governed safely if maintainers must reconstruct readiness from machine files or if a strong area can visually compensate for a blocked one.

**Independent Test**: Open the page with a validated committed snapshot representing mixed area states and confirm that all four areas, their gate counts, freshness, blockers, and the non-compensating release decision are understandable without inspecting raw files.

**Acceptance Scenarios**:

1. **Given** a validated committed snapshot with four different readiness states, **When** a maintainer opens the overview, **Then** the four areas appear separately in the required order with status text, non-color cues, gate numerators and denominators, freshness, and blockers.
2. **Given** three passing areas and one non-passing area, **When** the overview is displayed, **Then** release eligibility remains false and the page explains that all required gates and current release approval must pass for one exact candidate.
3. **Given** benchmark progress of zero qualified processes, **When** the overview is displayed, **Then** the page reports `0/100` honestly and does not imply product, commercial, or program-health readiness.
4. **Given** the governed benchmark remains at `0/100`, **When** a maintainer opens its primary progress view, **Then** the page states whether qualification is inactive, on hold, blocked, or failing; identifies the blocking dependency or authorization; and shows the next action that can change the count.
5. **Given** a 100-item proposed customer-story catalog and zero qualified benchmark processes, **When** both are displayed, **Then** the page labels them as separate populations and never presents proposed stories as executed or qualified.

---

### User Story 2 - Understand Progress Across Checkpoints (Priority: P2)

As a product-minded solo developer, I can see how customer capability, quality, process automation, governance, readiness, benchmark qualification, and delivery have changed across exact committed checkpoints so that I can identify imbalance and choose the next useful investment.

**Why this priority**: A current-state score alone cannot show whether work is converging on customer value, cycling on governance, or stalled behind one dependency.

**Independent Test**: Open a history fixture spanning specification, implementation, integration, and customer-capability checkpoints; confirm every point has an exact time and commit identity, each series has a defined unit, and the page explains the latest change and next action without using elapsed days as an effort estimate.

**Acceptance Scenarios**:

1. **Given** multiple committed checkpoints, **When** a trend is shown, **Then** its title, unit, time axis, legend, exact checkpoint time and commit, latest change, and decision use are understandable without reading control-plane internals.
2. **Given** quality and governance checkpoints rise while customer capability remains flat, **When** the history view is opened, **Then** the imbalance is explicit and the page identifies the next customer-value milestone rather than implying the program is nearly complete.
3. **Given** task completion is high for one bounded feature, **When** task history is shown, **Then** it is labeled as feature-local throughput and is paired with program-level customer, roadmap, readiness, and release context.
4. **Given** a checkpoint lacks a trustworthy timestamp or source identity, **When** history is rendered, **Then** the point is omitted or labeled unavailable rather than assigned an inferred time or order.

---

### User Story 3 - Trace a Blocker to Evidence (Priority: P3)

As a maintainer investigating a blocked or stale result, I can move from an area to its gate, assertion, exact evidence identity, age, and bounded recovery guidance while the original finding remains visible.

**Why this priority**: Status is actionable only when a maintainer can verify why it is true and find the smallest safe recovery action without exposing sensitive source content.

**Independent Test**: Use a snapshot containing passing, blocked, stale, and resolved-finding examples; follow each displayed detail path and confirm the page preserves the exact status, evidence identity, freshness, and recovery metadata.

**Acceptance Scenarios**:

1. **Given** a blocked gate with evidence and recovery metadata, **When** the maintainer opens its detail, **Then** the exact candidate or evidence subject, age, blocker, recovery guidance, and safe repository-relative evidence link are shown.
2. **Given** a historical correction that disposes a finding, **When** the maintainer reviews program health, **Then** both the original finding and its resolution metadata remain visible with the exact correction profile and verified claim counts.
3. **Given** unsupported, partial, skipped, unavailable, not-tested, inconclusive, or contaminated evidence, **When** it is displayed, **Then** its classification remains non-passing and is not relabeled as success.

---

### User Story 4 - Follow Current Work and the Next Safe Action (Priority: P4)

As a program coordinator, I can see the current customer milestone, active branch and lease, completed and total feature tasks, lifecycle checkpoints, blockers, and the sole next eligible action so that work stays within the approved WIP limit.

**Why this priority**: The dashboard must help prevent parallel scope creep and accidental execution of an action that lacks dependency or human authority.

**Independent Test**: Display committed examples with an integration lane, a feature-development lane, and blocked follow-on work; confirm the page identifies the active milestone and exposes only the action encoded by the validated source.

**Acceptance Scenarios**:

1. **Given** one integration lane and one feature-development lane, **When** the roadmap and work view opens, **Then** each lane's branch, milestone, latest demonstrated capability, blocker, and next action are distinguishable.
2. **Given** a proposed feature without implementation approval, **When** its status is viewed, **Then** planning progress may be shown but no implementation action is presented as authorized.
3. **Given** a roadmap dependency or P0 blocker, **When** the maintainer reviews the next action, **Then** the blocker and required authority are shown without inventing an alternative action.
4. **Given** feature tasks are nearly complete while the wider product program is still early, **When** progress is displayed, **Then** the page distinguishes feature-scope completion from customer-capability, roadmap, and release-gate maturity.
5. **Given** an integration lane and continued-development lane, **When** their status is displayed, **Then** the integration lane shows its frozen/pushed/PR/CI/dev state and the continued lane shows its customer milestone, demonstrated capability, blocker, and next action without implying shared branch ownership.

---

### User Story 5 - Stay Oriented During Stale or Failed Refresh (Priority: P5)

As a maintainer, I retain a clearly labeled last known valid view when new committed evidence cannot be validated, and I can tell whether the page is empty, loading, stale, blocked, failed, unavailable, or current.

**Why this priority**: A partial replacement or silently stale page could produce a false governance decision.

**Independent Test**: Start from a valid view, then present unchanged identity, changed valid identity, schema-invalid data, source-identity mismatch, unavailable data, and an interrupted refresh; confirm the page never displays a partial or falsely current replacement.

**Acceptance Scenarios**:

1. **Given** a last known valid snapshot and a failed validation of newer evidence, **When** refresh completes, **Then** the prior snapshot remains visible, is unmistakably labeled stale or failed, and includes bounded recovery guidance.
2. **Given** no valid snapshot has ever loaded, **When** evidence is unavailable, **Then** the page shows an honest empty or unavailable state and no readiness value is invented.
3. **Given** the committed snapshot and evidence identity have not changed, **When** refresh occurs, **Then** the visible authoritative content is not replaced or reinterpreted.
4. **Given** a new validated committed identity, **When** refresh succeeds, **Then** all views switch together to that identity rather than mixing old and new status.

### Edge Cases

- A snapshot is structurally valid but its declared source identity does not match the independently validated delivery envelope.
- One area or gate is stale while the other areas remain current.
- Required gates exist with a zero passed numerator, including honest `0/100` benchmark progress.
- A benchmark target is reached while product, commercial, or program-health gates remain non-passing.
- An evidence link is missing, unsafe, absolute, or outside the approved repository-relative set.
- A correction profile is proposed, stale, only partially verified, or has mismatched expected and verified claim counts.
- The active feature has no tasks yet, no lease, an expired lease, or a branch that differs from the committed record.
- The source exposes no next eligible action or requires human approval before the next action.
- A refresh is interrupted after validation begins but before all views can be updated.
- Long identifiers, blocker lists, and evidence descriptions are viewed on a narrow screen or at 200% zoom.
- Status colors are unavailable, indistinguishable, or motion is disabled.
- A checkpoint has a commit identity but no trustworthy event or commit time.
- A nearly complete task list belongs to a narrow control-plane feature while no customer journey is yet demoable.
- A push or CI event is unavailable, still running, superseded, or associated with a different branch/PR head.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The browser page MUST be a read-only projection of a schema-valid committed program snapshot and its independently validated delivery identity.
- **FR-002**: The page MUST validate the snapshot contract and its source identity before presenting it as current.
- **FR-003**: The page MUST NOT become an approval source, transition source, next-action grant, or independently editable authority.
- **FR-004**: The overview MUST present `product_readiness`, `benchmark_readiness`, `commercial_readiness`, and `program_health` as four separate areas in that order.
- **FR-005**: Each readiness area MUST show its status, required and passed gate counts, gate identities and states, blockers, evidence references, freshness, and last successful qualification when present.
- **FR-006**: Every status MUST be communicated by text and structure in addition to color.
- **FR-007**: The page MUST explain that release eligibility requires every required gate in all four areas to pass for the same exact candidate together with current human release approval.
- **FR-008**: The page MUST NOT average, weight, or visually compensate one readiness area with another.
- **FR-009**: The benchmark view MUST show counted and target progress from `0/100` through `100/100`, first-attempt and eventual outcomes, qualification tiers, non-passing populations, partition and coverage deficits, oracle and artifact completeness, contamination, attempts, and freshness when present in the validated source.
- **FR-010**: The product view MUST show customer outcomes, failure and recovery states, inspectability, accessibility, compatibility, exact candidate, and current blocking defects when present.
- **FR-011**: The commercial view MUST show offering posture, supported profiles, packaging, supply-chain, privacy, support, repository-control, and release-train status when present.
- **FR-012**: The program-health view MUST show roadmap blockers, WIP and leases, open or overdue P0 risks and decisions, repair and push bounds, verifier independence, evidence freshness, and flow progress when present.
- **FR-013**: The roadmap and work view MUST show the current customer milestone, active feature, branch and lease identity, completed and total tasks, lifecycle checkpoint progress, blocker, latest demonstrated capability, and sole next eligible action when supplied by committed evidence.
- **FR-014**: A next action that requires human approval MUST be labeled as requiring approval and MUST NOT be presented as executable authority.
- **FR-015**: Gate details MUST expose the evidence subject, age, blocker or recovery guidance, and history needed to understand the displayed state.
- **FR-016**: Evidence navigation MUST use only approved safe repository-relative references and MUST preserve exact evidence identity.
- **FR-017**: The page MUST render all correction disclosures, original findings, and resolution metadata without allowing edits or using a correction to change unrelated readiness, benchmark, authority, or release values.
- **FR-018**: The page MUST preserve non-passing classifications including skipped, partial, unsupported, unavailable, not tested, inconclusive, and contaminated.
- **FR-019**: The page MUST provide distinct and honest empty, loading, current, stale, blocked, failed, unavailable, and unknown presentations.
- **FR-020**: When newer evidence cannot be validated, the page MUST retain the last known valid snapshot, label it stale or failed, and show bounded recovery guidance rather than rendering a partial replacement.
- **FR-021**: All displayed views MUST advance atomically to one validated committed identity and MUST NOT combine content from different snapshot or delivery identities.
- **FR-022**: Automatic refresh MUST occur only in response to a changed committed snapshot or evidence identity; unchanged identity MUST NOT cause reinterpretation.
- **FR-023**: Refresh MUST NOT launch product runs, benchmark cases, tools, models, applications, publication, integration, or release actions.
- **FR-024**: The page MUST NOT read uncommitted author state as authority or infer missing status, approval, freshness, blockers, or actions.
- **FR-025**: The page MUST expose only allowlisted governance metadata and MUST exclude raw prompts, engineering inputs or outputs, artifact bodies, credentials, tokens, cookies, private endpoints, raw logs, commands, arguments, reusable authority, and unapproved absolute paths.
- **FR-026**: No data or telemetry MUST be uploaded automatically.
- **FR-027**: The complete primary journey and all detail disclosures MUST be operable with a keyboard and expose visible focus.
- **FR-028**: Content MUST remain understandable at 200% zoom, on narrow viewports, with reduced motion, and with status colors unavailable.
- **FR-029**: The page MUST provide usable contrast and programmatically meaningful names, relationships, and status announcements.
- **FR-030**: The existing general workspace dashboard MUST remain distinct from the program-status page and MUST NOT be treated as satisfying this feature merely because it displays adjacent operational data.
- **FR-031**: The page MUST provide checkpoint history for customer capability, quality, process automation, governance, the four readiness areas, benchmark qualification, bounded feature tasks, and integration/CI delivery when the validated source contains those observations.
- **FR-032**: Every historical point MUST bind a defined metric and unit to an exact committed checkpoint identity and trustworthy timestamp; missing identities or timestamps MUST remain visibly unavailable and MUST NOT be inferred.
- **FR-033**: Every graph MUST state what changed, why the metric matters, its current limitation or blocker, and the next action that can move it; unlabeled sequence numbers and unexplained flat lines are insufficient.
- **FR-034**: The benchmark progress view MUST be a primary metric and MUST pair `qualified/100` history with the current qualification phase, hold or blocker reason, dependencies, authorization state, and next qualifying action.
- **FR-035**: Task metrics MUST be scoped to their feature and MUST be displayed alongside customer-capability, roadmap, readiness, and release context so a nearly complete task list cannot imply that the overall product is nearly complete.
- **FR-036**: The page MUST separately report the proposed customer-story catalog total and definition-maturity counts from the governed qualified benchmark count; proposed stories MUST never be counted as benchmark executions or qualifications.
- **FR-037**: The integration view MUST show branch, target, frozen candidate, last pushed identity and time, PR identity/link, phase, passing/failing/pending checks, CI age, first actionable failure, dev synchronization, merge-gate state, next action, and a bounded push/CI event history when present.
- **FR-038**: The continued-development view MUST show its exclusive branch, current customer milestone, latest demonstrated capability, blocker, and next action independently from the integration lane.
- **FR-039**: The page MUST avoid calendar-duration estimates as a proxy for work and MUST express remaining progress through observable capabilities, gates, dependencies, checkpoints, and evidence.

### Scope Boundaries

- This feature presents existing validated committed evidence; it does not create, edit, approve, or repair that evidence.
- This feature does not generate or qualify benchmark cases and does not execute the 100-process benchmark.
- This feature does not implement the canonical process definition, process execution, authoring, commercial release, predictive schedules, or hand-authored trend values.
- This feature does not add remote telemetry, hosted status services, automatic uploads, or manual score controls.
- Planning artifacts may be created in this lane, but implementation remains blocked until an exact approved planning subject and current implementation lease exist.

### Key Entities

- **Program Snapshot**: The validated committed, read-only source containing readiness areas, gates, benchmark counts, roadmap progress, findings, authority, freshness, candidate, and release eligibility.
- **Delivery Identity**: Independent evidence that binds the rendered snapshot bytes to their exact committed source and delivery subjects.
- **Readiness Area**: One of four non-substitutable program dimensions with its own gate population, status, blockers, evidence, and freshness.
- **Gate Detail**: The displayed gate and assertion outcomes, evidence identities, age, blocker, recovery, and history that explain an area's state.
- **Work Lane**: A committed record of a branch, current customer milestone, latest demonstrated capability, blocker, lease or authority state, and next action.
- **Benchmark Progress**: Counted and target qualification populations plus tiers, attempts, deficits, completeness, contamination, and evidence cutoff.
- **Correction Disclosure**: A correction profile and its exact claim counts, original findings, resolutions, authority, and verification subject.
- **Checkpoint Observation**: An immutable metric value with a declared unit, exact commit/evidence identity, trustworthy timestamp, source classification, and optional change explanation.
- **Customer Story Catalog Summary**: Derived counts of proposed stories by definition maturity, kept categorically separate from benchmark qualification.
- **Delivery Lane Status**: A read-only integration/CI or continued-development projection with exclusive branch ownership, current phase, evidence, blocker, and next action.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In usability verification, at least 90% of representative maintainers identify all four readiness states, release eligibility, the primary blocker, and the next action correctly within two minutes of opening the overview.
- **SC-002**: Across the complete acceptance fixture set, 100% of displayed readiness states, gate counts, benchmark populations, candidate identities, blockers, evidence ages, corrections, and next actions match the validated committed source exactly.
- **SC-003**: Across mixed-state fixtures, 100% of cases with any non-passing required area show release eligibility as false, including cases with `100/100` benchmark progress.
- **SC-004**: The full primary and blocker-investigation journeys complete with keyboard input alone at 200% zoom on both standard and narrow viewports, with no loss of content, focus, status meaning, or evidence access.
- **SC-005**: In 100% of invalid, mismatched, unavailable, and interrupted-refresh tests, the page shows no partial or falsely current replacement; it either preserves a clearly labeled last valid view or presents an honest empty state.
- **SC-006**: A newly available validated committed identity is reflected consistently across all views within 10 seconds, while an unchanged identity produces no authoritative-content change.
- **SC-007**: Security and privacy inspection finds zero raw prompts, engineering payloads, artifact bodies, credentials, private endpoints, raw logs, command arguments, reusable authority, or unapproved absolute paths in the page or its support-safe diagnostics.
- **SC-008**: Verification confirms that no page interaction or refresh can mutate program evidence, authorize a transition, launch product or benchmark work, publish, integrate, or release.
- **SC-009**: In usability verification, at least 90% of representative maintainers correctly explain what each displayed graph measures, the latest material change, the current blocker, and one actionable next step within three minutes.
- **SC-010**: Across the history fixture set, 100% of plotted points retain their exact committed identity, trustworthy timestamp, metric unit, and source classification; no point is ordered or dated by an invented value.
- **SC-011**: In 100% of fixtures where a bounded feature is at least 90% task-complete but the product program is not customer-ready, the page clearly reports the feature-local scope and does not present the program as nearly complete.
- **SC-012**: Across catalog and benchmark fixtures, the page always preserves `100 proposed` and `0/100 qualified` as distinct labeled populations until governed qualification evidence changes the latter.

## Assumptions

- EPP-F01 integrates before EPP-F01B implementation begins and supplies the validated committed snapshot and independent delivery identity this page projects.
- EPP-F01 is integrated on `dev` at commit `b776b1182d5b6ee41364eb40b1bc95bf4eff797c` with tree `f22f61791a2385723934558d8557881862221eb1`; EPP-F01B planning is based on that immutable integrated result plus the separately verified continuation artifacts.
- The initial audience is a local Wright maintainer who already has authorized access to the repository and existing Wright browser workspace.
- The validated source remains the sole authority for vocabulary, ordering, counts, evidence identities, freshness, blockers, corrections, next action, and release eligibility.
- Safe evidence references resolve within the local, authorized repository context; external browsing and automatic upload are not required.
- Existing Wright navigation and design conventions may provide entry and visual consistency, but the program-status purpose and data authority remain distinct from the general workspace dashboard.
- Planning, clarification, design, tasks, and analysis remain separate governed phases; no implementation code is permitted from this draft alone.
- Historical graphs are derived only from committed checkpoint observations with trustworthy times; they are descriptive evidence, never schedules or token-to-time forecasts.
