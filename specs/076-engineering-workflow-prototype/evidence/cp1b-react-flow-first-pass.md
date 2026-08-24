# CP1B Partial Evidence: React Flow First Pass

**Status**: First candidate implemented; no selection decision yet
**Branch**: `076-engineering-workflow-prototype`
**Date**: 2026-08-24

## Increment hypothesis

React Flow can replace only the static viewport/connector projection while preserving the accepted Wright visual shell, canonical workflow fixture, engineering capability discovery, and inspector behavior.

## Dependency review

- Package: `@xyflow/react@12.11.3`, pinned exactly in the prototype branch.
- License: MIT, confirmed by the [official xyflow repository](https://github.com/xyflow/xyflow) and package manifest.
- Maintenance: npm registry metadata reported publication on 2026-08-12; the [official React Flow documentation](https://reactflow.dev/learn) describes the current `@xyflow/react` package and v12 API.
- Compatibility: official package metadata supports React and React DOM 17 or newer; Wright uses React 19.2.
- Audit: no advisory was attributed to React Flow or its added dependencies. `npm audit` reported one moderate advisory in Wright's pre-existing direct `dompurify@3.4.12` dependency (GHSA-55q2-fjhq-7xh7); this increment does not alter that package.

## Implemented boundary

- A graph-library-neutral projection owns phase, block, connection, coordinate, size, and intent shapes.
- The accepted visual slice accepts a renderer slot and exports its existing block card, while importing no candidate package.
- The React Flow harness alone imports `@xyflow/react` and its base CSS.
- The same drill-bit-holder fixture supplies canonical IDs, roles, phase membership, connection semantics, labels, positions, and dimensions.
- The harness maps selection back to the existing Wright inspector and leaves editing, persistence, LLM, MCP, and execution disabled.
- Candidate-native serialization and parent/group semantics are not used.

## Visual evidence

- [React Flow first-pass capture](cp1b-react-flow-first-pass.png), 1680×940.

The capture confirms that the approved palette, searchable capability library entry point, configurable phase labels, role-based cards, review diamonds, inspector, legend, toolbar, and final manufacturing handoff survive the adapter. React Flow supplies pan/zoom, controls, handles, edges, fit behavior, and a reduced upper-right minimap.

## Measured evidence

| Check                     | Result    | Notes                                                                                   |
| ------------------------- | --------- | --------------------------------------------------------------------------------------- |
| Pure adapter/rubric tests | 5 passed  | 4.87 seconds before the candidate mount                                                 |
| Candidate component test  | Passed    | 4.04 seconds; mounts the real graph and verifies selection updates the Wright inspector |
| CP1A regression tests     | 3 passed  | Passed during the combined run                                                          |
| Production build          | Passed    | Vite portion 3.99 seconds                                                               |
| Candidate lazy JS chunk   | 181.45 kB | 58.60 kB gzip                                                                           |
| Candidate lazy CSS chunk  | 13.84 kB  | 2.83 kB gzip                                                                            |
| Browser capture           | Passed    | Headless Chromium, reference viewport, no new browser test suite                        |

The existing Vite `__dirname` future-loader warning and existing large main/Plotly chunk warnings remain.

## Findings and costs

1. The approved UI can be wired early without making React Flow canonical. The renderer-slot change is small and reusable by the other candidates.
2. Explicit Wright-known dimensions are better than candidate DOM measurement for this deterministic view. They made the component test reliable and avoid unnecessary layout startup work.
3. React Flow requires a local `ResizeObserver` shim under jsdom even when dimensions are explicit. This is candidate-specific test setup and must count against, but does not prevent, component testability.
4. React Flow's generic step edges preserve connectivity and non-color feedback cues, but do not yet reproduce the hand-routed feedback rails. A small custom edge projection would be needed for top visual-fidelity marks.
5. The first minimap position obscured the final manufacturing handoff. Browser inspection caught this immediately; moving and reducing it fixed the obstruction without a broad Playwright suite.
6. The original attempt to use candidate parent/child grouping was unnecessary coupling and unreliable in jsdom. Neutral absolute coordinates removed it with no canonical-model change.
7. React Flow adds a material but isolated lazy bundle cost. That cost must be compared with Rete and LiteGraph rather than judged alone.

## Still required before a candidate decision

- 25- and 100-block fixtures and interaction measurements;
- keyboard/semantic and axe evidence;
- custom feedback routing feasibility and focus behavior;
- completed rubric score and deletion exercise;
- equivalent shallow Rete.js and LiteGraph.js evidence.

No recommendation to retain or replace Rivet is made by this partial checkpoint.
