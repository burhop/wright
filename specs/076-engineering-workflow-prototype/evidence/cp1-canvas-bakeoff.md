# CP1B canvas bakeoff decision

**Status**: Accepted; Continue selected at the CP1B human gate
**Branch**: `076-engineering-workflow-prototype`
**Date**: 2026-08-24

## Recommendation

Use **React Flow as the provisional canvas adapter for CP2**. Do not treat this
as a decision to replace Rivet in production, and do not adopt React Flow's
graph state as Wright's workflow model. The result is narrower: React Flow is
the best of the three tested view/interaction layers for cheaply validating the
engineer-readable UI.

Only React Flow clears all mandatory minimums. It reproduces the accepted UI,
reuses Wright's DOM components, supports fast component-level testing, and
remains isolated behind the common canvas projection. Its main costs are a
larger bundle than Rete and the need for a small custom edge implementation if
the feedback rails must match the reference image more precisely.

This recommendation does not create CAD, FEA, CAM, CFD, PLM, kinematics, or
other runtime services. Those names remain discovery metadata in a searchable
capability library. Execution remains one generic MCP action bound to an exact
catalog tool through the existing governed MCP gateway.

## Scored result

Scores are 0–5 and weighted to 100. Accessibility, canonical-model separation,
and component testability each have a mandatory minimum of 3; a high total
cannot hide a failure in one of those areas.

| Candidate | Weighted score | Accessibility | Canonical separation | Component testability | Gate result |
| --- | ---: | ---: | ---: | ---: | --- |
| React Flow | **91/100** | 4 | 5 | 5 | **Pass** |
| Rete.js | 70/100 | 3 | 5 | 2 | Fail: component-testability minimum |
| LiteGraph.js | 41/100 | 1 | 4 | 1 | Fail: accessibility and component-testability minimums |

The executable score data and minimum-gate test live in
`evaluation/candidate-evaluations.ts` and
`evaluation/candidate-evaluations.spec.ts`. The score is a decision aid backed
by the measurements below; it is not a claim of mathematical precision.

## Evidence by decision factor

### Visual grammar

- React Flow preserves the approved shell, role-colored Wright cards, review
  diamonds, configurable phase lanes, ports, labels, inspector, and selection.
  Generic step edges are legible but do not yet match every hand-routed feedback
  rail in the reference.
- Rete's custom SVG connection renderer produces the strongest feedback-path
  treatment, but reaching that result required custom sockets, custom
  connections, an editor, an area plugin, a React renderer, render utilities,
  and styled-components.
- LiteGraph renders a recognizable graph but cannot reuse the approved DOM card
  anatomy. It compresses text, renders gates as ordinary rectangles, and
  requires parallel Canvas2D phase/feedback drawing plus a duplicate accessible
  DOM index.

Reference-size captures:

- [React Flow](cp1b-react-flow-first-pass.png)
- [Rete.js](cp1b-rete-first-pass.png)
- [LiteGraph.js](cp1b-litegraph-first-pass.png)

### Accessibility

React Flow has a durable Vitest/jsdom regression covering semantic phase and
connection summaries, named block controls, keyboard selection, focus, and
axe. It passes in 2.22 seconds with zero detectable axe violations. The first
axe run found two real issues—prohibited names on decorative port handles and a
named minimap without an image role—and the components were corrected.

The same two Rete checks passed in an exploratory 6.73-second run with zero
detectable axe violations. That run emitted roughly 2,000 lines of React
`act(...)` warnings because Rete creates many independent React roots. The
warning-heavy rejected-candidate test was not retained as permanent test debt;
the outcome is recorded here and in the scored evidence.

LiteGraph could not receive the same real-runtime component audit in the T1
environment because jsdom has no Canvas2D implementation and native canvas
nodes expose no DOM semantics. A canvas emulator or browser test plus a
parallel DOM UI would be required. That is itself the relevant accessibility
and testability result.

The jsdom axe runs disable color-contrast analysis because layout and computed
visual contrast require a real browser. Contrast remains a manual/browser
checkpoint check.

### Scale and interaction

Deterministic 25- and 100-block fixtures use the same canonical
`WorkflowPreview` model and three phase lanes. Each fixture contains three long
feedback edges. Candidate routes can load them with `?scale=25` or
`?scale=100`.

| Candidate | 25 blocks | 100 blocks | Result |
| --- | ---: | ---: | --- |
| React Flow | 399.1 ms | 548.6 ms | Render, select last block, and focus: pass |
| Rete.js | 4,528.2 ms | Selection did not settle within 20 s | Fail; full attempt took about 57.35 s and flooded warnings |
| LiteGraph.js | Not promoted | Not promoted | Earlier mandatory requirements had already failed |

These are single-run development-machine observations used to distinguish
clear orders of magnitude, not formal performance statistics. Full details are
in [the scale evidence](cp1b-scale-evidence.md).

### Test economics and lessons from the existing Rivet code

The current Rivet work proved valuable durable seams: generic MCP discovery and
governed invocation, approvals, evidence/artifacts, workspace boundaries, and
the need for compatibility contracts. Those should be retained regardless of
the canvas choice.

It also demonstrated why Wright should not make another editor library
canonical:

- engineer-facing concepts became coupled to an upstream graph and
  serialization model;
- the most recent full gate spent roughly seven minutes in the API suite and
  another seven minutes in the root suite, with repeated costs before frontend
  and browser checks;
- one Windows PTY invalid-handle problem caused 42 cascading API failures even
  though the same tests passed outside the PTY;
- browser tests found valuable historical-data crashes, but late and at high
  diagnostic cost.

The prototype's response is architectural and procedural: Wright owns a typed
workflow model and pure projection; the canvas owns only rendering and
interaction; most feedback comes from T0/T1 tests; browser automation is kept
for a few cross-boundary demonstrations.

For this final CP1B increment:

- rubric, scale, keyboard, and axe suite: 8 tests in 4 files, 3.55 seconds;
- React Flow accessibility-only suite: 2 tests, 2.22 seconds;
- production type-check/build: pass;
- screenshots were captured as checkpoint evidence rather than converted into
  a broad Playwright suite.

Rete is an especially useful negative result. It can look excellent and has a
smaller bundle, yet its many independent React roots make routine tests noisy
and its 100-block case unreliable. Visual quality and runtime capability alone
are not enough; test architecture is a first-class selection requirement.

### Package, security, and bundle review

| Candidate | Pinned package surface | Lazy JS | Lazy JS gzip | Relevant signal |
| --- | --- | ---: | ---: | --- |
| React Flow | `@xyflow/react@12.11.3` | 181.29 kB | 58.53 kB | MIT, React 19-compatible, no candidate advisory |
| Rete.js | Six pinned Rete/renderer/style packages | 110.31 kB | 33.03 kB | MIT, no candidate advisory, larger integration surface |
| LiteGraph.js | `litegraph.js@0.7.18` | 507.87 kB | 125.16 kB | MIT, direct `eval`, older maintenance/type signals |

The production dependency audit reports one moderate advisory in Wright's
pre-existing direct `dompurify@3.4.12` dependency
(`GHSA-55q2-fjhq-7xh7`). No advisory is attributed to a canvas candidate. That
existing issue is outside this prototype decision but should remain visible in
normal dependency maintenance.

## Deletion-cost exercise

The exercise maps everything required to remove a candidate while preserving
the accepted shell, canonical fixture, scale generator, workflow contracts,
and evidence.

| Candidate | Candidate directory | Dependency removal | Outside-directory edits | Domain/model change |
| --- | ---: | ---: | --- | --- |
| React Flow | 3 files | 1 package | Lazy import/element/route; React Flow-only evaluation imports | None |
| Rete.js | 3 files | 6 packages | Lazy import/element/route | None |
| LiteGraph.js | 4 files | 1 package | Lazy import/element/route | None |

For CP2 after human approval:

1. Delete the Rete and LiteGraph candidate directories.
2. Remove their lazy imports, elements, and routes from `App.tsx`.
3. Remove only their pinned dependencies and refresh the lockfile.
4. Retain the neutral canvas contract/projection, Wright block components,
   canonical fixture, score report, and screenshot evidence.
5. Run the focused model/component suite and production build to prove no
   domain change was required.

The rejected implementations remained in the CP1B checkpoint for live comparison
and were deleted in CP2A after the Continue decision. Their evidence is retained.

## Limits of this decision

CP1B deliberately did not test editing, persistence, LLM authoring, live MCP
invocation, execution, or migration of Rivet workflows. It therefore cannot
justify a production rearchitecture or answer the final retain-Rivet versus
hybrid versus replace decision.

The human gate selected **Continue**. CP2A therefore deletes the rejected
candidates and validates only the selected UI through the same Wright-owned
contracts. Generic MCP binding and LLM-proposed edits stay in their later
checkpoints.

## Human gate decision

- **Decision**: Continue.
- **Accepted visual direction**: retain the dark navy engineering surface,
  role/status colors, phase bands, card anatomy, labeled edges, and feedback
  treatment shown in the selected React Flow prototype.
- **Authorized next increment**: visual-contract lock, rejected-candidate
  deletion, and selected-adapter promotion only.
