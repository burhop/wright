# Feature Specification: Control-Plane Validator and Governed Readiness Snapshot

**Feature Branch**: `077-control-plane-validator`

**Created**: 2026-08-26

**Status**: Blocked — replacement exact approval required

**Input**: User description: "Create EPP-F01, a local control-plane validator and live readiness dashboard that validates program schemas, references, digests, approvals, transitions, roadmap eligibility, WIP and leases, then truthfully derives four independent evidence-linked readiness areas."

**Resolved boundary**: In EPP-F01, “dashboard” means the governed `dashboard.json` snapshot and equivalent CLI report only. The browser-accessible program-status page required by the parent program is the separate dependency-ordered EPP-F01B feature and is not one of these 68 tasks.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Validate the Program Before Acting (Priority: P1)

A maintainer or fresh agent runs one documented local validation action before changing the program and receives a terminal pass or fail for the exact committed program subject, together with the next eligible action when one can be proven.

**Why this priority**: Autonomous work is safe only when state, authority, dependencies, evidence, and WIP are proven rather than inferred from prose or memory.

**Independent Test**: Run validation against a known-valid committed fixture and independently mutate each critical invariant in isolated negative fixtures; the valid fixture passes and every invalid fixture fails with a stable reason and no source changes.

**Acceptance Scenarios**:

1. **Given** a clean committed control plane whose schemas, references, digests, approval, transition chain, roadmap, state revision, feature pointer, WIP, and lease are consistent, **When** validation runs, **Then** it identifies the exact subject, reports every required check as passed, and emits the sole dependency-eligible next action.
2. **Given** an unknown schema major, duplicate key, missing reference, digest mismatch, stale approval, illegal transition, revision gap, roadmap cycle, unmet dependency, conflicting eligible action, or lease/WIP conflict, **When** validation runs, **Then** it fails closed with a stable reason code, names the affected artifact and invariant, and emits no authorized next action.
3. **Given** a clean Windows checkout that represents the same committed content with platform line-ending conversion, **When** committed evidence is validated, **Then** the committed Git object bytes remain the identity authority and checkout representation is reported separately rather than misclassified as committed-content corruption.

---

### User Story 2 - Derive Four Truthful Readiness Areas (Priority: P2)

A program approver or maintainer generates and reads one evidence-linked machine snapshot and equivalent CLI report that keep product readiness, benchmark readiness, commercial readiness, and program health separate.

**Why this priority**: A high process pass count, a healthy program, or a commercially complete package must never conceal failure in another release obligation.

**Independent Test**: Generate the dashboard from fixtures where each readiness area independently passes, blocks, fails, or becomes stale; only source-supported area states appear, and overall release eligibility remains false unless all four areas and exact release approval pass together.

**Acceptance Scenarios**:

1. **Given** valid committed evidence with different states across the four areas, **When** the dashboard is generated, **Then** each area shows its own numerator, denominator, gates, blockers, freshness, evidence subjects, and last success without a weighted or composite score.
2. **Given** 100 terminally successful benchmark rows but a failed product, commercial, or program-health gate, **When** the dashboard is generated, **Then** benchmark success cannot make the other area green or make the program release-eligible.
3. **Given** no qualified benchmark collection and no product implementation, **When** the dashboard is generated, **Then** empty and not-started states are explicit and no synthetic progress is inferred.

---

### User Story 3 - Diagnose and Recover Safely (Priority: P3)

A maintainer can understand why validation or dashboard generation did not succeed, inspect bounded inputs and outputs, and follow a safe recovery that preserves the last valid dashboard.

**Why this priority**: A fail-closed tool that obscures the failing layer or overwrites the last trustworthy view would slow recovery and encourage unsafe manual overrides.

**Independent Test**: Inject malformed, inconsistent, stale, dirty, missing, and unreadable inputs; verify deterministic failure classification, bounded diagnostics, nonzero failure status, preservation of the last valid snapshot, and no partial replacement.

**Acceptance Scenarios**:

1. **Given** one or more invalid sources, **When** validation runs, **Then** all safely discoverable independent findings are reported in deterministic order with stable codes, locations, consequences, and the smallest valid recovery action.
2. **Given** dashboard generation fails after a prior valid snapshot exists, **When** the failure occurs, **Then** the valid snapshot remains byte-for-byte unchanged and the result explicitly marks current delivery stale or failed.
3. **Given** a candidate worktree contains uncommitted changes, private paths, credentials, raw logs, or disallowed payloads, **When** inspection runs, **Then** it does not copy sensitive content into output and does not present the candidate as committed evidence.

---

### User Story 4 - Reproduce the Result in an Empty Context (Priority: P4)

A fresh agent can use only committed documentation and machine output to identify what was checked, which inputs were authoritative, how the result was derived, what remains blocked, and what action is allowed next.

**Why this priority**: The program is intended for mostly autonomous development, so results must survive conversation loss and handoff without hidden operator knowledge.

**Independent Test**: Give a reviewer an empty checkout context plus the documented entrypoint and generated evidence; the reviewer can independently reproduce the same verdict and next action without conversational history.

**Acceptance Scenarios**:

1. **Given** the same committed subject and supported local environment, **When** two independent users run validation and generation, **Then** semantic results, ordering, counts, reason codes, and evidence identities match; only declared observation-time fields may differ.
2. **Given** generated output, **When** a user follows an evidence reference, **Then** it resolves to an exact local artifact or committed subject and does not rely on an unrecorded external service.

### Edge Cases

- State and transition files are individually valid but disagree on revision, transition ID, canonical digest, or raw committed-object digest.
- The roadmap is acyclic but has multiple equally eligible items when the state requires one sole next action.
- A referenced approval is structurally valid but expired, revoked, stale, scope-mismatched, or bound to a different subject.
- A lease is expired, duplicated, held for another feature, grants an unapproved path/action, or names a worktree/branch/base that no longer matches.
- A dashboard source changes during generation, or the destination cannot be atomically replaced.
- A future optional artifact or schema minor version is present, while an unknown major version appears elsewhere.
- Inputs contain duplicate object keys that a permissive parser would otherwise collapse.
- A gate lists skipped, unavailable, unsupported, partial, contaminated, or not-tested evidence.
- A benchmark count reaches 100 but coverage, oracle, artifact, holdout, independence, or freshness requirements remain incomplete.
- The checkout is dirty, detached unexpectedly, missing Git metadata, or represents committed text with platform line-ending conversion.
- The prior dashboard is absent, malformed, generated from a different subject, or already stale.
- Paths, diagnostics, or source values contain credentials, proprietary payloads, raw engineering artifacts, prompts, logs, or reusable authority.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The feature MUST provide one documented, non-interactive local entrypoint that validates the engineering-process-platform control plane and returns an unambiguous validator success or failure status. A successfully derived blocked, stale, in-progress, or not-started readiness area, or `release_eligible=false`, MUST NOT by itself make validation fail.
- **FR-002**: Every result MUST identify the inspected source commit `S`, repository tree, program-directory subject, container resolution and commit `C` when one is claimed, explicit delivery resolution and descendant commit `D` when delivery proof is requested, working-tree cleanliness, observation time, authoritative input set, and validator identity as a canonical digest of the closed source bundle consisting of the tracked `scripts/validate-engineering-process-program.py` blob plus every tracked regular `*.py` blob recursively below `scripts/program_control/` at `S`, sorted by normalized path. Before a passing verdict, generation, or recomputation, every loaded validator module MUST resolve to that local bundle; the same paths in runtime `HEAD` MUST have identical Git blob IDs to `S`, no dirty/untracked/ignored bundle path may exist, and only declared Git text/EOL checkout representation may differ from committed bytes. A runtime/source mismatch MUST fail closed, and uncommitted candidates MUST be visibly distinct from committed evidence.
- **FR-003**: Validation MUST reject duplicate object keys, malformed content, unknown schema major versions, schema violations, missing or unexpected required artifacts, broken cross-references, and unsupported identifier formats.
- **FR-004**: Validation MUST verify canonical state digests, exact committed-object digests, monotonic revisions, append-only state history, legal program and child transitions, raw evidence references, and required transition outputs. Legacy v1 acceptance MUST be limited to exactly two ordered profiles: the closed revision-1-through-9 bootstrap and separately approved revision-10-through-19 bridge, each with contiguous unique revisions/transitions, immutable archive paths, and exact raw state/transition blob identity. Historical transitions MUST embed exact SHA-256; terminal `TR-0018` MUST use the sole non-circular `checkpoint_commit_blob` rule and resolve its exact blob from the later material-change approval subject that contains both transition and profile. The bridge's null checkpoint MUST resolve only from that same exact subject without mutating the profile; no later v1 record may be accepted, and exactly one approved v1-to-v2 migration may follow.
- **FR-005**: For committed artifacts, exact byte identity MUST be derived from committed Git object content. Platform checkout transformations and dirty working content MUST be detected and reported separately; neither may silently redefine the committed subject.
- **FR-006**: Validation MUST prove the roadmap is acyclic and dependency ordered, statuses agree with evidence, blocking decisions are honored, no ineligible item is selected, and each state exposes only the permitted next action or actions.
- **FR-007**: Validation MUST enforce program WIP limits, singleton feature-pointer ownership, active-lease identity and freshness, branch/worktree/base consistency, allowed planning or implementation scope, and stop conditions.
- **FR-008**: Validation MUST verify approval existence, decision, scope, subject identity, conditions, expiry, revocation, and freshness; approval for one lifecycle boundary MUST NOT authorize another.
- **FR-009**: Validation MUST evaluate semantic invariants that individual schemas cannot express, including referenced-ID existence, equality of bound subjects and digests, readiness-count consistency, release-formula inputs, and state/roadmap/dashboard agreement.
- **FR-010**: The feature MUST derive, never hand-set, four independent machine-snapshot areas in this exact order: product readiness, benchmark readiness, commercial readiness, and program health.
- **FR-011**: Each readiness area MUST expose its status, passed and required gate counts, gate-level status, classification, reason, evidence, and explicit per-gate `fresh` value, plus area blockers, exact evidence references, aggregate freshness, and last successful qualification. Each catalog assertion MUST have one same-ID evaluator result; a closed catalog registry MUST bind every required evidence class to expected source schema ID and role; every evidence reference MUST match that registry and its resolved exact SourceArtifact; and gate pass MUST be derived only from complete, fresh, supporting, evidence-backed, required-class-complete, exact-candidate results with required verifier independence. The validation report and dashboard MUST use the same derived gate-row contract.
- **FR-012**: The machine dashboard snapshot MUST include benchmark target and counted totals, first-attempt and eventual outcomes, T0-T3 counts, failed, blocked, stale, contaminated, and not-tested counts, plus coverage, oracle, artifact, partition, and freshness deficits.
- **FR-013**: Overall release eligibility MUST remain false unless every required gate in all four readiness areas passes for the same exact candidate and a current exact-subject human release approval exists; no score, benchmark count, or manual flag may substitute.
- **FR-014**: Validation and generation MUST be read-only with respect to source evidence and MUST NOT launch product runs, benchmark cases, MCPs, models, applications, network calls, release actions, or external writes.
- **FR-015**: Dashboard replacement MUST be transactional. Generated dashboard bytes MUST remain `candidate_not_evidence`; a failed run MUST preserve the prior snapshot, expose a failed or stale delivery result, and never leave a partial or newly green snapshot. A committed-current claim MUST exist only in a validation delivery envelope backed by independently verified, passing delivery evidence in an explicitly supplied descendant `D` that binds source `S`, dashboard-only container `C`, exact dashboard bytes, and the allowed `C..D` delivery-only change without becoming an input to the snapshot. `D` MUST never be searched for, guessed, or inferred.
- **FR-016**: Findings MUST use stable reason codes, severity, affected artifact and invariant, evidence, consequence, and bounded recovery; output ordering MUST be deterministic and all safely discoverable independent findings MUST be reported in one run.
- **FR-017**: Human-readable CLI and machine-readable snapshot outputs MUST represent the same verdict, exact subjects, area states, counts, blockers, and next action. Machine output MUST be versioned and reject unknown major consumers/producers rather than guessing.
- **FR-018**: Output MUST include only allowlisted metadata and bounded summaries. It MUST exclude credentials, tokens, cookies, private endpoints, raw prompts, raw logs, proprietary payloads, engineering artifact bodies, reusable authority, and unapproved absolute paths.
- **FR-019**: The documented user journey MUST explain prerequisites, inputs, outputs, pass/fail meaning, empty/stale/blocked states, recovery, compatibility, and how to inspect the exact evidence behind every reported status.
- **FR-020**: Automated verification MUST include a valid end-to-end fixture and isolated negative fixtures for every fail-closed class in FR-003 through FR-009, both byte-closed legacy profiles and rejection of any later v1 record, explicit and constrained-inferred container resolution, explicit-only delivery resolution and every rejection path, closed source-bundle generator identity, validator-success/readiness-status separation, shared per-gate freshness, independent passing descendant delivery evidence, every dashboard truth rule in FR-010 through FR-013, transactional failure, deterministic output, redaction, and no-source-mutation behavior.
- **FR-021**: Compatibility verification MUST cover supported Windows and POSIX checkouts, including line-ending behavior, paths with spaces, missing optional data, current schema major behavior, the exact revision-1-through-9 bootstrap profile, the exact revision-10-through-19 bridge profile, rejection of revision 20 or any other future v1 record, and the single approved migration successor.
- **FR-022**: The feature MUST semantically validate benchmark policy; coverage quotas, intersections, distinctness, and equivalence families; legal qualification transitions; process/oracle/output references; artifact completeness; holdout-ledger continuity and contamination; attempt ordinals/history; T0–T3 claims; freshness; and deterministic summary populations/equations already present in the control plane. Missing or contradictory assertion evidence MUST prevent a benchmark gate from passing. The feature MUST NOT create process cases, execute qualification attempts, or claim benchmark readiness from terminal success alone.
- **FR-023**: Removal or rollback MUST leave program source evidence unchanged, restore the previous documented manual validation path, and prevent dashboards produced by the removed or incompatible validator from being treated as current.
- **FR-024**: A fresh agent using the committed README and direct links to the active feature artifacts and exact transition/approval manifest MUST be able to reproduce the verdict, identify the sole next eligible action or blocker, and recognize every action that still requires human approval.

### Key Entities

- **Validation Subject**: The exact commit, trees, cleanliness state, validator identity, and observation boundary being inspected.
- **Source Artifact**: A versioned program, roadmap, state, gate, risk, decision, approval, transition, benchmark, compatibility, or release record with path, schema identity, and committed-object digest.
- **Validation Finding**: A stable code, severity, artifact, invariant, evidence, consequence, and bounded recovery associated with one subject.
- **Feature Lease**: The singleton right to mutate one feature planning or implementation scope, bound to feature, branch, worktree, base, holder, revision, times, allowed paths/actions, and recovery.
- **Eligibility Result**: Dependency, decision, gate, approval, lease, and stop-condition derivation that yields a bounded next action or blocker.
- **Readiness Area**: One of four independent release obligations with required gates, current status, evidence, blockers, freshness, and last success.
- **Dashboard Snapshot**: A transactional projection of validated source artifacts for one exact subject; it never supersedes its sources.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A fresh maintainer can run the documented validation and identify pass/fail, the exact subject, the highest-severity finding, and the next allowed action in under 5 minutes without conversation history.
- **SC-002**: The complete known-valid control-plane fixture passes 100% of required checks, while every single-fault negative fixture for the enumerated fail-closed classes fails with the expected stable reason code and zero false-green area or release verdicts.
- **SC-003**: Two independent runs against the same committed subject produce identical semantic machine output, ordering, area states, counts, reason codes, evidence identities, and next action after excluding explicitly documented observation-time fields.
- **SC-004**: In a test matrix where each of the four readiness areas independently passes, blocks, fails, and becomes stale, 100% of dashboard area verdicts match source evidence and no area changes another area's verdict.
- **SC-005**: Across all fixtures where fewer than four readiness areas pass or exact release approval is absent/stale, release eligibility remains false in 100% of runs, including the fixture with 100 terminally successful processes.
- **SC-006**: Every injected generation failure preserves the previous valid dashboard byte-for-byte, produces a non-success result, and leaves no partial replacement.
- **SC-007**: Windows and POSIX validation of the same committed subject agrees on all semantic verdicts and committed digests in 100% of compatibility cases; platform checkout differences are reported only in their declared representation fields.
- **SC-008**: Secret/private-output fixtures yield zero credential, token, raw prompt, raw log, proprietary payload, artifact-body, reusable-authority, or unapproved absolute-path disclosures in human or machine output.
- **SC-009**: Validation never mutates a source artifact in the full verification suite; before/after source-content identities match in 100% of success and failure cases.
- **SC-010**: An independent empty-context reviewer can follow evidence links from each displayed area and reproduce the same blocker or pass rationale for 100% of sampled gates.

## Assumptions

- EPP-F01 is local repository tooling and documentation only; it does not implement the engineering-process product runtime, a browser-accessible status page, or a remote hosted dashboard. The governed browser projection is EPP-F01B and must traverse its own Spec Kit and approval lifecycle.
- The approved program control plane and existing Wright Git history are the source of truth. Conversation history, checked task boxes, and manually edited aggregate status are not authority.
- Git is available for exact committed-subject inspection. When Git metadata is unavailable, committed-evidence validation fails closed rather than falling back to checkout bytes.
- Existing repository dependencies and supported runtimes are sufficient for implementation; adding or upgrading a dependency requires separate approval.
- The checked-in seed dashboard and every generated dashboard byte sequence remain explicitly non-evidence. A later validation report may classify delivery as committed-current only from an exact `S`/`C` relation plus independent delivery evidence in descendant `D`; the dashboard never embeds `C` or `D` evidence.
- Benchmark support in this feature is validation and projection of already-existing metadata only; generation of the 100-process collection and live qualification remain later roadmap work.
- No network, credentials, proprietary systems, paid services, product execution, benchmark execution, push, PR, merge, publication, or release is required to deliver or verify this feature locally.
- The branch (`077-control-plane-validator`) and feature directory (`specs/076-control-plane-validator`) intentionally have independent Spec Kit sequence identities and are both recorded explicitly.

## Out of Scope

- Product process definition, authoring, visualization, execution, persistence, or MCP invocation.
- Browser route, frontend adapter, page, components, automatic refresh, or browser accessibility tests for program status; those belong to EPP-F01B.
- Generating, editing, or executing benchmark process cases or qualification attempts.
- Remote telemetry, hosted dashboards, notifications, SaaS integrations, or automatic uploads.
- Push, PR creation, dev integration, production release, dependency changes, or approval automation.
- Turning validation success into implementation, integration, or release authority.
