# Program Status Requirements Quality Checklist

**Purpose**: Verify that EPP-F01B requirements and design contracts are complete, precise, consistent, measurable, and safe before implementation approval.

**Created**: 2026-08-28

**Depth**: Formal approval-gate review

## Authority and identity

- [x] CHK001 The authoritative committed inputs, derived projection, and non-authoritative browser state are explicitly distinguished. [Spec FR-001–FR-003; Plan]
- [x] CHK002 Exact commit, tree, program-tree, snapshot digest, validation transition, unchanged EPP-F01 dashboard, supplemental projection, and bundle digest define one render identity. [Data Model; Bundle Contract]
- [x] CHK003 Requirements prohibit dirty-worktree evidence, UI-authored status, inferred approval, and refresh-triggered actions. [Spec FR-022–FR-024]
- [x] CHK004 Atomic publication and atomic all-panel replacement are specified for both publisher and browser boundaries. [Spec FR-020–FR-021; Research D2]
- [x] CHK005 Unsupported versions and identity mismatches have explicit fail-closed behavior that retains the last valid view. [API Contract; Data Model]

## Product-manager metric semantics

- [x] CHK006 The four readiness areas remain separately named, ordered, gated, and non-compensating. [Spec FR-004–FR-008]
- [x] CHK007 Governed benchmark `qualified/100` and proposed customer-story catalog counts are defined as separate populations. [Spec FR-009, FR-034, FR-036]
- [x] CHK008 A zero benchmark count requires phase, hold/blocker reason, dependencies, authority state, and the next qualifying action. [Spec US1.4; FR-034]
- [x] CHK009 Feature task completion is explicitly scoped to a named feature and cannot imply overall product completion. [Spec US2.3; FR-035]
- [x] CHK010 Every history ID has a fixed numerator/unit, inclusion rule, source classification, and decision use. [Data Model MetricSeries; Bundle Contract]
- [x] CHK011 Every graph requires causal transition/parent order, exact time/commit, deterministic latest change, limitation, and structured next action. [Spec FR-032–FR-033; Bundle Contract]
- [x] CHK012 Calendar-duration estimates are excluded as a proxy for effort; progress uses observable capabilities, gates, dependencies, and evidence. [Spec FR-039]

## Development-process visibility

- [x] CHK013 Integration/CI fields cover branch, target, frozen/pushed identity, PR, checks, CI age/failure, sync, merge gate, events, and next action. [Spec FR-037]
- [x] CHK014 Continued-development fields cover exclusive branch, milestone, demonstrated capability, blocker, and next action. [Spec FR-038]
- [x] CHK015 The contract requires exactly one integration lane followed by exactly one continued-development lane with exclusive branch ownership. [Data Model DeliveryLane; Bundle Contract]
- [x] CHK016 Every action has machine-readable ID, eligibility, authority, human-approval requirement, blocker, and evidence. [Spec FR-014; Bundle Contract]

## Failure, evidence, and security

- [x] CHK017 Empty, loading, current, stale, blocked, failed, unavailable, and unknown states have distinct required behavior. [Spec FR-019–FR-021]
- [x] CHK018 Passing, partial, skipped, unsupported, unavailable, inconclusive, contaminated, and corrected evidence cannot be collapsed into a false binary success. [Spec FR-017–FR-018]
- [x] CHK019 Every evidence reference has an internal browser detail bound to an exact allowlisted path/digest; optional exact-commit GitHub links and packaged content unavailability are explicit. [Spec FR-015–FR-016; API Contract]
- [x] CHK020 Forbidden sensitive fields and runtime side effects are explicit and testable. [Spec FR-023, FR-025–FR-026; API Contract]
- [x] CHK021 File, observation, finding, catalog, and event bounds are stated to prevent unbounded local reads or rendering. [API Contract; Bundle Contract]
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
- [x] CHK033 The bundle embeds the exact EPP-F01 dashboard contract unchanged, preserving status/classification/reason/freshness, benchmark, lease, correction, approval, delivery, and release semantics. [Data Model Authoritative Dashboard; Bundle Contract]
- [x] CHK034 The standard committed-identity publisher and package-install trigger are specified and tested end to end; mutable publisher heartbeat is separate from bundle identity. [Spec FR-022; Research D3; Tasks T039, T044]
- [x] CHK035 The API delegates through the constitution-required `tool_registry` boundary, and RBAC, data-testid, packaged lifecycle, rollback, and uninstall tests are explicit. [Plan Constitution Check; Tasks T013–T014, T040–T043]

## Review result

All 35 requirements-quality checks pass after bounded repair `EPP-F01B-REVIEW-CONTRACT-001`. No unresolved critical ambiguity or hidden P0 product decision remains. Implementation remains explicitly gated.
