# Workspace Surfaces UX and Accessibility Requirements Checklist

**Purpose**: Validate the panel/browser, chat coexistence, novice display, diagnostics and accessibility contract  
**Created**: 2026-07-30  
**Feature**: [spec.md](../spec.md)  
**Depth**: product design and accessibility release review

## Presentation and Continuity

- [x] CHK301 Are panel, browser and both-presentation choices defined for every surface kind, including eligibility, safe fallback and truthful explanation when framing/isolation/host capability blocks a choice? [UX Contract: Presentation Eligibility](../ux-contract.md#presentation-eligibility-and-disclosure), [FR-004 through FR-008]
- [x] CHK302 Is switching presentation required to preserve the same shareable app instance and state, while isolated-instance sources clearly communicate the difference before launch? [UX Contract: Presentation Eligibility](../ux-contract.md#presentation-eligibility-and-disclosure), [User Story 2](../spec.md#user-story-2---open-an-application-in-the-panel-or-browser-priority-p1)
- [x] CHK303 Are close tab/presentation, detach, stop application and delete durable output represented as distinct user actions with unambiguous consequences and recovery? [UX Contract: Commands](../ux-contract.md#commands-and-consequences), [FR-007]
- [x] CHK304 Is persisted presentation preference scoped to user+workspace+source and revalidated with a visible reason/fallback when no longer eligible? [UX Contract: Presentation Eligibility](../ux-contract.md#presentation-eligibility-and-disclosure), [Data Model: PresentationPreference](../data-model.md#presentationpreference)
- [x] CHK305 Are starting, ready, unhealthy, stopped, failed and reconnecting/reconciling projections paired with only valid actions and no blank/misleading frame? [UX Contract: Truthful Status](../ux-contract.md#truthful-status-and-valid-actions), [FR-003]

## Chat, Focus and Responsive Layout

- [x] CHK306 Does focus mode allocate all non-chat space to the surface while preserving visible, operable and resizable chat, including update continuity without mode exit? [UX Contract: Layout](../ux-contract.md#layout-and-retention), [User Story 4](../spec.md#user-story-4---focus-on-the-ui-while-continuing-the-conversation-priority-p1)
- [x] CHK307 Are minimum chat/surface sizes, container-relative resizing, persistence/versioning and behavior when constraints conflict defined rather than left to viewport guesses? [UX Contract: Layout](../ux-contract.md#layout-and-retention), [FR-046 through FR-047]
- [x] CHK308 At narrow widths, is an explicit reversible chat/surface switcher or stack required so neither pane disappears or clips essential controls? [UX Contract: Layout](../ux-contract.md#layout-and-retention), [User Story 4 Acceptance 3](../spec.md#user-story-4---focus-on-the-ui-while-continuing-the-conversation-priority-p1)
- [x] CHK309 Are live hosts retained across tab switches with bounded pressure/eviction behavior and a warning before destructive reload of stateful content? [UX Contract: Layout](../ux-contract.md#layout-and-retention), [Lifecycle: Retained Client Host Policy](../lifecycle.md#retained-client-host-policy)

## Keyboard and Assistive Technology

- [x] CHK310 Are semantic `tablist`/`tab` behavior, roving focus, selection, close, reorder if supported, and focus restoration specified for surface tabs? [UX Contract: Keyboard](../ux-contract.md#keyboard-and-focus-model), [SC-005]
- [x] CHK311 Are chat/surface separators keyboard-operable with separator role, orientation, current/min/max values, arrow increments and visible focus? [UX Contract: Keyboard](../ux-contract.md#keyboard-and-focus-model), [SC-005]
- [x] CHK312 Does focus move into/out of cross-origin frames predictably, avoid traps, provide a host escape/return action and preserve focus when tabs/modes change? [UX Contract: Keyboard](../ux-contract.md#keyboard-and-focus-model), [User Story 4 Acceptance 4](../spec.md#user-story-4---focus-on-the-ui-while-continuing-the-conversation-priority-p1)
- [x] CHK313 Are critical/serious automated accessibility violation thresholds, manual keyboard checks and accessible names/descriptions for every interactive `data-testid` control explicit? [UX Contract: Keyboard](../ux-contract.md#keyboard-and-focus-model), [SC-005]

## Beginner Display and Errors

- [x] CHK314 Does the beginner contract meet one import and <=10 executable lines, require no server/port/web concepts, name axes/title/description and remain durable after process exit? [Quickstart: Five-Minute Graph](../quickstart.md#five-minute-graph), [SC-001 through SC-002]
- [x] CHK315 Are line/bar/scatter/histogram inputs, empty/nonfinite/invalid/huge data, optional dependency absence and actionable example-linked errors described sufficiently for a novice? [UX Contract: Beginner Graph](../ux-contract.md#beginner-graph-input-and-revision-behavior), [FR-010 through FR-017]
- [x] CHK316 Are safe typed renderer selection, accessibility fallback/data table, ordinary HTML sanitization and active-HTML isolation communicated so the user understands capability differences? [Research: Python Display](../research.md#python-display-research), [Quickstart: HTML Safety](../quickstart.md#html-safety)
- [x] CHK317 Are display update/new-revision semantics predictable, visible and resistant to stale updates, including a user choice where the spec permits one? [UX Contract: Beginner Graph](../ux-contract.md#beginner-graph-input-and-revision-behavior), [Data Model: DisplayArtifact](../data-model.md#displayartifact)

## Consent and Diagnostics

- [x] CHK318 Does capability consent show source and version, requested operation/data, risk, duration/persistence, policy limits and deny/cancel paths in plain language? [UX Contract: Consent](../ux-contract.md#capability-consent-and-diagnostics), [FR-038]
- [x] CHK319 Are diagnostics complete enough for a newcomer to distinguish readiness, framing, permission, protocol and runtime failures while showing correlation IDs and excluding secrets/internal authority? [UX Contract: Diagnostics](../ux-contract.md#capability-consent-and-diagnostics), [Quickstart: Diagnostics](../quickstart.md#diagnostics-and-recovery)
- [x] CHK320 Does every failure state retain a useful non-UI or browser fallback where possible, avoid claiming iframe failure detection it cannot prove, and state the next valid recovery action? [UX Contract: Truthful Status](../ux-contract.md#truthful-status-and-valid-actions), [FR-034], [FR-048]

## Notes

- Check only when a product/accessibility reviewer can determine intended behavior without inspecting implementation code.
- The novice journey is release-blocking: terminology and examples must be validated with representative low-programming-experience engineers, not only expert reviewers.
- Resolved 2026-07-30 after adding the per-source presentation matrix, action consequences, state/action model, exact layout/retention values, keyboard/focus contract, graph validation/revision behavior and consent/diagnostic wording. User-study and implementation results remain planned evidence.
