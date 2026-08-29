# Program Status Requirements Quality Checklist

**Purpose**: Verify that EPP-F01B requirements and design contracts are complete, precise, consistent, measurable, and safe before implementation approval.

**Created**: 2026-08-28

**Depth**: Formal approval-gate review

## Authority and identity

- [x] CHK001 The authoritative committed inputs, derived projection, and non-authoritative browser state are explicitly distinguished. [Spec FR-001–FR-003; Plan]
- [x] CHK002 Exact commit, tree, program-tree, publisher-attested raw Git-blob digest/evidence, independently recomputable canonical-dashboard/bundle digests, digest-bound source catalog, validation transition, unchanged EPP-F01 dashboard, and supplemental projection define one render identity without claiming source-free raw recomputation. [Data Model; Bundle Contract]
- [x] CHK003 Requirements prohibit dirty-worktree evidence, UI-authored status, inferred approval, and refresh-triggered actions. [Spec FR-022–FR-024]
- [x] CHK004 Atomic publication and atomic all-panel replacement are specified for both publisher and browser boundaries. [Spec FR-020–FR-021; Research D2]
- [x] CHK005 Unsupported versions and identity mismatches have explicit fail-closed behavior that retains the last valid view. [API Contract; Data Model]

## Product-manager metric semantics

- [x] CHK006 The four readiness areas remain separately named, ordered, gated, and non-compensating. [Spec FR-004–FR-008]
- [x] CHK007 Governed benchmark `qualified/100` and proposed customer-story catalog counts are defined as separate populations. [Spec FR-009, FR-034, FR-036]
- [x] CHK008 A zero benchmark count requires a typed phase, hold state/reason, identified dependency states, authority state, and non-governing next qualifying action; missing or contradictory context rejects publication. [Spec US1.4; FR-034]
- [x] CHK009 Feature task completion is explicitly scoped to a named feature and cannot imply overall product completion. [Spec US2.3; FR-035]
- [x] CHK010 Every history ID has a fixed numerator/unit, inclusion rule, source classification, and decision use. [Data Model MetricSeries; Bundle Contract]
- [x] CHK011 Every graph requires causal transition/parent order, exact time/commit, deterministic latest change, limitation, and purpose-labeled non-governing metric guidance. [Spec FR-032–FR-033; Bundle Contract]
- [x] CHK012 Calendar-duration estimates are excluded as a proxy for effort; progress uses observable capabilities, gates, dependencies, and evidence. [Spec FR-039]

## Development-process visibility

- [x] CHK013 Integration/CI fields cover branch, target, frozen/pushed identity, PR, checks, CI age/failure, sync, merge gate, events, and next action. [Spec FR-037]
- [x] CHK014 Continued-development fields cover exclusive branch, milestone, demonstrated capability, blocker, and next action. [Spec FR-038]
- [x] CHK015 The contract requires exactly one closed integration lane followed by exactly one closed continued-development lane with distinct branch ownership; continued development rejects integration-only fields. [Data Model DeliveryLane; Bundle Contract]
- [x] CHK016 Every action has machine-readable ID, purpose, eligibility, authority, human-approval requirement, blocker, and evidence; the current program action has one explicit precedence rule and all other actions are labeled context. [Spec FR-013–FR-014; Bundle Contract]

## Failure, evidence, and security

- [x] CHK017 Empty, loading, current, stale, blocked, failed, unavailable, and unknown states have distinct required behavior. [Spec FR-019–FR-021]
- [x] CHK018 Passing, partial, skipped, unsupported, unavailable, inconclusive, contaminated, and corrected evidence cannot be collapsed into a false binary success. [Spec FR-017–FR-018]
- [x] CHK019 Every evidence reference resolves to exactly one internal browser detail bound to an exact catalog-allowlisted canonical path/digest; optional exact-commit GitHub links are length-bounded and parsed for exact HTTPS origin/path with credentials, port, query, fragment, slug, and path negatives, and packaged content unavailability is explicit. [Spec FR-015–FR-016; API Contract]
- [x] CHK020 Forbidden sensitive fields and runtime side effects are explicit and testable. [Spec FR-023, FR-025–FR-026; API Contract]
- [x] CHK021 File, observation, correction, finding, risk, decision, catalog, URL, and event bounds are stated; correction claims, findings, and independent verification form a closed reciprocal ID relation with derived counts and verdict/blocking outcomes. [API Contract; Bundle Contract]
- [x] CHK022 Rollback and invalid-newer-bundle behavior have an observable expected result. [Plan Delivery Gates; Quickstart]

## UX, accessibility, and compatibility

- [x] CHK023 Status meaning is required in text and structure in addition to color. [Spec FR-006]
- [x] CHK024 Keyboard use, focus visibility, 200% zoom, narrow viewport, reduced motion, contrast, and semantic announcements are specified. [Spec FR-027–FR-029]
- [x] CHK025 Every visualization has a usable prose/table fallback and is still actionable if Plotly fails. [Research D4; Plan Browser Boundary]
- [x] CHK026 The dedicated program page is explicitly separate from the existing workspace dashboard. [Spec FR-030]
- [x] CHK027 Packaged runtime behavior is specified without Git, source checkout, network, or an agent manager. [Plan Constitution Check; Delivery Gate 4]
- [x] CHK028 Additive/minor and breaking/major schema compatibility expectations are explicit. [API Contract Compatibility]

## Verification and scope

- [x] CHK029 Component, API/domain, UI-integration, and packaged system tests each have defined responsibilities. [Plan Delivery Gates]
- [x] CHK030 Deterministic regeneration and deliberate isolated corruption have human-repeatable acceptance steps. [Quickstart 1, 4]
- [x] CHK031 The five user stories are independently demonstrable in priority order and do not require benchmark execution. [Plan Implementation Slices]
- [x] CHK032 No requirement silently authorizes implementation, dependencies, benchmark execution, push/PR/merge, publication, or release. [Spec Scope Boundaries; Plan Planning Authority]
- [x] CHK033 The bundle embeds only the actual EPP-F01 dashboard contract unchanged and labels its action historical; current action, benchmark context, lifecycle, lease, delivery, correction, risk, decision, and finding details come from typed catalog-derived supplements without overriding readiness/benchmark/release truth. [Data Model Authoritative Dashboard and GovernanceSupplement; Bundle Contract]
- [x] CHK034 The standard two-second committed-identity publisher and package-install trigger are specified and tested end to end; the fully contracted mutable publisher heartbeat is separate from bundle identity and covered through service, API, client, UI, and end-to-end tasks. [Spec FR-022; Research D3; Tasks T006, T013, T016–T017, T038–T039, T044]
- [x] CHK035 The API delegates through the constitution-required `tool_registry` boundary, and RBAC, data-testid, packaged lifecycle, rollback, uninstall, and Windows/Linux/macOS atomic-lifecycle tests are explicit. [Plan Constitution Check; Tasks T013–T014, T040–T043, T046]
- [x] CHK036 Schema, publisher, runtime, and browser contracts jointly enforce source-catalog identity, raw attestation versus canonical recomputation, sole-current-action precedence, benchmark context, reciprocal correction/finding/verification relations, one-to-one evidence resolution, canonical paths/URLs, catalog totals, distinct lane branches, observation/series source classification, and task bounds. [Data Model Runtime relational validation; Tasks T005–T017]
- [x] CHK037 The first viewport is contractually required to answer the six operator questions before deep governance detail. [Spec FR-040; SC-013; Tasks T014–T019, T034, T042]
- [x] CHK038 Program-wide work uses a closed committed task-source population, separates active-feature counts, and exposes undecomposed roadmap work rather than implying full-program completion. [Spec FR-041; Data Model Work; Tasks T005–T007, T030–T034]
- [x] CHK039 Active-agent display requires stable identity, exact registered task and title/state, branch, safe worktree ID or lane, outcome-oriented purpose, time, and evidence; process activity is explicitly excluded. [Spec FR-042; Work Registry Contract]
- [x] CHK040 Governed all-use-case implementation requires user-visible acceptance evidence, independent verification remains separate, and code-only progress cannot count as implemented. [Spec FR-043; Use-Case Registry Contract]
- [x] CHK041 The 100-process subset keeps defined, in-progress, implemented, tested, independently verified, and benchmark-qualified counts orthogonal, with qualification reconciled only to the authoritative dashboard. [Spec FR-044; Bundle Contract]
- [x] CHK042 The proposed 100-story catalog remains a separate planning population unless an exact governed registry relation exists. [Spec FR-045; Research D14]
- [x] CHK043 Test history defines exact commit/time/suite/source provenance, terminal-rerun selection, parametrized identity counting, aggregate/component overlap rejection, count arithmetic, pass-rate semantics, category availability, and table fallback. [Spec FR-046–FR-047; Test Ledger Contract]
- [x] CHK044 The required visualization set covers task burn-up, two use-case funnels, test outcomes, roadmap/customer capability, four independent readiness areas, and benchmark qualification without a composite score. [Spec FR-048; Tasks T021–T025, T033–T034]
- [x] CHK045 Every new graph retains meaning, latest change, limitation/blocker, evidence-backed non-governing action, accessible axes/legend/tooltips, and semantic table fallback. [Spec FR-048; Bundle GraphContext]

## Review result

All 45 document-level requirements-quality checks pass for this material planning amendment. Exact local analysis and the same two independent exact-subject reviews remain required before a final PASS may be claimed. The prior implementation subject is superseded and implementation remains explicitly gated pending a replacement exact approval.
