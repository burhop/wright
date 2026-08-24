# CP1B Partial Evidence: LiteGraph.js First Pass

**Status**: Third shallow candidate implemented; provisional rejection pending final rubric
**Branch**: `076-engineering-workflow-prototype`
**Date**: 2026-08-24

## Increment hypothesis

LiteGraph.js can provide the canvas interaction layer for the accepted engineering workflow UI without forcing Wright to reimplement its block presentation, accessibility, connection grammar, or test strategy.

## Dependency review

- Package: `litegraph.js@0.7.18`, pinned exactly in the prototype branch.
- License: MIT, confirmed by the installed manifest and the [official jagenjo/litegraph.js repository](https://github.com/jagenjo/litegraph.js).
- Maintenance: npm metadata identifies 0.7.18 as the current original package, but the original repository's recent main-branch activity is materially older than the React Flow and Rete candidates. The installed type declaration still identifies itself as 0.7.0. The separately maintained Comfy fork was archived after moving into the ComfyUI frontend, which also indicates ecosystem fragmentation rather than a single current standalone package.
- Audit: installation reported the same one moderate advisory in Wright's pre-existing direct `dompurify@3.4.12` dependency (GHSA-55q2-fjhq-7xh7). No npm advisory was attributed to LiteGraph itself.
- Build security signal: Vite/Rolldown reports direct `eval` in `build/litegraph.js`. The package's supplied `litegraph.core.js` and `litegraph_mini.js` bundles contain the same direct call, so switching undocumented entry points would not remove it.

## Implemented boundary

- A pure disposable projection converts Wright blocks and connections into LiteGraph's required per-target input-slot indexes. It is covered without importing the canvas runtime.
- Wright continues to own the accepted shell, palette, searchable engineering capability entry point, inspector, legend, fixture, IDs, roles, phases, and connection semantics.
- LiteGraph owns its HTML canvas, native graph nodes/links, mouse selection, pan, zoom, fit, and render loop.
- Small canvas hooks draw phase lanes, feedback rails, and edge labels because LiteGraph's native link/node grammar cannot express the accepted UI directly.
- An off-screen Wright DOM index exposes labeled phases and block-selection buttons because the canvas nodes have no DOM semantics.
- Editing, persistence, LLM, MCP invocation, and execution remain disabled. `Bound MCP Tool` stays generic; CAD/FEA/CAM/CFD/PLM/PDM/kinematics remain discovery metadata rather than runtime services.

## Visual evidence

- [LiteGraph.js first-pass capture](cp1b-litegraph-first-pass.png), 1680×940.

The capture proves that LiteGraph can fit and render the frozen graph, preserve colored roles, connect ports, select a node into the Wright inspector, and coexist with the accepted palette/phase/inspector shell. It also makes the mismatch visible: native cards compress content and ports, titles require truncation, review gates remain ordinary rectangles, artifact/status anatomy is lost, and text clarity is materially below the DOM-based React Flow and Rete candidates.

## Measured evidence

| Check                            | Result                            | Notes                                                                                                                                                         |
| -------------------------------- | --------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Pure candidate projection        | 2 passed                          | 1.10-second command; actual tests execute in 5 ms                                                                                                             |
| Complete focused prototype suite | 12 passed in 6 files              | 6.71 seconds                                                                                                                                                  |
| Candidate component mount        | Not available in current T1 tier  | LiteGraph requires a real `CanvasRenderingContext2D`; jsdom exposes neither its pixels nor native node semantics without adding a canvas emulation dependency |
| Production build                 | Passed with direct-`eval` warning | Vite portion 2.27 seconds                                                                                                                                     |
| Candidate lazy JS chunk          | 507.75 kB                         | 125.10 kB gzip; largest candidate by a wide margin                                                                                                            |
| Candidate lazy CSS chunk         | 1.07 kB                           | 0.52 kB gzip                                                                                                                                                  |
| Browser capture                  | Passed                            | Headless Chromium, reference viewport; required for runtime behavior rather than used as a broad test suite                                                   |

The existing Vite `__dirname` future-loader warning and existing large main/Plotly chunk warnings remain. LiteGraph adds a new direct-`eval` warning and its candidate chunk independently exceeds the 500 kB warning threshold.

## Findings and costs

1. The canonical-model boundary works: the candidate can be deleted without changing the fixture, accepted shell, inspector, or common projection.
2. LiteGraph's canvas-native rendering cannot reuse `WorkflowBlock` or normal HTML semantics. Matching the approved UI would require reimplementing card layout, gates, badges, focus, tooltips, and text behavior in Canvas2D.
3. Phase lanes and labeled dashed feedback paths already require custom canvas drawing. Native per-link colors are available, but the accepted non-color feedback grammar is not.
4. Accessibility requires a parallel off-screen DOM representation. That duplicates block/phase presentation and creates a long-term divergence risk that the DOM-based candidates avoid.
5. Fast pure projection tests remain possible, but the real candidate runtime falls out of the existing jsdom component tier. Adding a native canvas emulator or moving ordinary selection/layout checks to Playwright would work against the prototype's test-economics goal.
6. The public package is monolithic for Wright's use: one candidate route adds 507.75 kB minified, and the package's alternate built bundles retain direct `eval`.
7. The installed package and type/version signals are older and less aligned with the current React/Vite toolchain than the other candidates.
8. The two bounded visual fixes—hiding LiteGraph's FPS/debug overlay and reducing/truncating native title text—improved hygiene but did not change the architectural mismatch. Additional polish was intentionally stopped.

## Provisional decision

LiteGraph should not advance to CP2 unless the final common rubric uncovers a decisive capability that outweighs its visual, accessibility, bundle, security-signal, and component-test costs. No such capability appeared in this first pass. This is a candidate-level rejection, not yet the final React Flow versus Rete selection and not a decision about Rivet migration.

## Still required before the CP1B decision

- common 25- and 100-block fixtures and interaction measurements for the viable candidates;
- keyboard/semantic and axe evidence;
- completed rubric scores and deletion exercises;
- a direct React Flow versus Rete comparison of feedback routing, selection/focus, and future command-event translation.
