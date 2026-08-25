# CP2A visual lock and selected-canvas promotion

**Status**: Implemented; awaiting visual confirmation
**Branch**: `076-engineering-workflow-prototype`
**Date**: 2026-08-24

## Decision and hypothesis

The CP1B human gate selected **Continue** and explicitly accepted the prototype's
colors and style. This increment tests whether Wright can lock that visual
grammar, remove rejected graph implementations, and promote React Flow to the
main prototype route without changing the canonical workflow model.

The increment remains read-only. It does not add editing, persistence, LLM
authoring, MCP invocation, or workflow execution.

## Accepted visual contract

The visual contract is versioned as `cp2a-1` and is used by the rendered shell
and selected canvas adapter.

| Meaning | Color |
| --- | --- |
| Input and data flow | `#159cff` blue |
| AI task | `#9b4dff` purple |
| Generic MCP action | `#16c8c1` teal |
| Artifact and successful control flow | `#12c881` green |
| Review or approval gate | `#ffb20b` amber |
| Feedback or revision path | `#ff4058` red |
| Notification or handoff | `#76dc48` lime |

The contract also records these invariants:

- colors encode stable role or status semantics;
- phase names remain configurable even though the reference uses Define,
  Verify, and Manufacture;
- feedback paths retain a dashed non-color cue and direction;
- CAD, FEA, CAM, CFD, PLM/PDM, kinematics, and similar names remain discovery
  metadata and never select runtime services;
- every executable engineering capability remains the same generic MCP-action
  role bound to an exact catalog tool.

The contract lives in
`engineering-workflow-visual-contract.ts`. Its values and invariants have pure
tests, while the promoted component test verifies that the version and color
variables reach the rendered shell.

## Promotion and cleanup

- `/prototype/engineering-workflow` now lazy-loads
  `EngineeringWorkflowPrototype`, which composes the Wright-owned shell and
  fixture with `ReactFlowWorkflowCanvas` through the neutral render contract.
- The former React Flow bakeoff URL remains temporarily as an alias so an open
  review tab does not break; it renders the same promoted component.
- React Flow owns view mechanics only. Wright still owns workflow identity,
  phases, roles, coordinates, connection semantics, selection, and future
  persistence commands.
- Rete and LiteGraph routes and seven implementation/test/style files were
  removed.
- Their seven direct packages were removed; npm eliminated 16 packages in
  total after transitive cleanup.
- Candidate screenshots, measurements, rubric scores, and the CP1B decision
  report remain as architectural evidence.
- The production build no longer contains the LiteGraph chunk or its direct
  `eval` warning.

All deleted implementation files remain recoverable from Git history.

## Verification

| Check | Result |
| --- | --- |
| Focused visual-contract, route, accessibility, scale, and fixture suite | 10 tests in 5 files passed in 3.93 s |
| Complete engineering-workflow prototype suite | 20 tests in 9 files passed in 7.38 s |
| Rendered visual-contract smoke tests | 3 tests in 2 files passed in 3.21 s |
| Accessibility | Semantic phase/connection summaries, keyboard selection/focus, and zero detectable axe violations remain green |
| Lint | 0 errors; 3 pre-existing hook warnings outside the prototype |
| Production type-check/build | Passed; Vite build portion 3.18 s |
| Selected lazy UI chunk | 215.82 kB minified, 68.35 kB gzip, including shell and React Flow |
| Live main route | HTTP 200 |
| Temporary compatibility route | HTTP 200 |

The existing Vite future native-config-loader warning and existing large
application/Plotly chunk warnings remain. The existing moderate DOMPurify audit
finding is unchanged and is not caused by this increment.

## Visual evidence

- [CP2A selected UI](cp2a-selected-ui.png), 1680×940.

This is one focused checkpoint capture, not a new broad Playwright suite.

## Review gate and next increment

Confirm that the promoted main route still preserves the accepted dark navy
surface, role/status colors, phase separation, card anatomy, labeled edges,
feedback paths, inspector, and capability-library entry point.

If accepted, the next bounded CP2 increment should address usability rather
than backend wiring:

1. polish feedback-edge routing and viewport focus behavior;
2. add deterministic empty, loading, error, and details/evidence states;
3. define progressive disclosure for large workflows;
4. run the small engineer-comprehension comparison against the current Rivet
   baseline;
5. stop for review before any editing, LLM, or MCP execution work.
