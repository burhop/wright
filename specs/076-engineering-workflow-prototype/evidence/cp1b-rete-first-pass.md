# CP1B Partial Evidence: Rete.js First Pass

**Status**: Second candidate implemented; no selection decision yet
**Branch**: `076-engineering-workflow-prototype`
**Date**: 2026-08-24

## Increment hypothesis

Rete.js can replace only the static viewport/connector projection while preserving the accepted Wright visual shell, canonical workflow fixture, engineering capability discovery, and inspector behavior.

## Dependency review

- Packages are pinned exactly: `rete@2.0.6`, `rete-area-plugin@2.3.2`, `rete-connection-plugin@2.0.5`, `rete-render-utils@2.0.3`, `rete-react-plugin@2.1.2`, and `styled-components@6.5.3`.
- License: the Rete core and plugin repositories and their installed manifests report MIT. The styled-components official repository and installed manifest also report MIT.
- Maintenance: the [official Rete repository](https://github.com/retejs/rete), [Rete documentation](https://retejs.org/docs/guides/basic/), and [React renderer guide](https://retejs.org/docs/guides/renderers/react/) describe the current v2 plugin architecture and React 19 `createRoot` integration.
- The connection-editing plugin is installed as part of the representative Rete stack but deliberately not activated in this read-only checkpoint. Rete's area and React plugins render the candidate; Wright controls selection and prevents translation.
- Audit: installation reported the same one moderate advisory in Wright's pre-existing direct `dompurify@3.4.12` dependency (GHSA-55q2-fjhq-7xh7). No advisory was attributed to the Rete stack.

## Implemented boundary

- The graph-library-neutral projection remains the source of phase, block, connection, coordinate, size, and intent shapes.
- The accepted Wright shell and block component import no Rete package.
- The Rete harness alone creates the editor/area/renderer and maps the frozen fixture into temporary Rete nodes and connections.
- Phase lanes remain Wright semantic overlays synchronized to the Rete viewport; they are not fake editor nodes or persisted candidate groups.
- Selection updates the existing Wright inspector. Editing, persistence, LLM, MCP invocation, and execution remain disabled.
- The palette continues to expose pinned examples plus a searchable capability library for CAD, FEA, CAM, CFD, PLM/PDM, kinematics, and future organization-defined capabilities. Every executable example still renders as the same generic MCP-action role and exact `Bound MCP Tool`; categories do not dispatch runtime services.

## Visual evidence

- [Rete.js first-pass capture](cp1b-rete-first-pass.png), 1680×940.

The capture confirms the accepted toolbar, compact palette, capability-library entry point, configurable phase lanes, custom role cards, gates, inspector, legend, fit controls, minimap, and manufacturing handoff. Data, control, and feedback connections have distinct line treatment and arrow direction. Canonical edge labels such as `yes`, `pass`, `revise`, `reject`, and `approve` are retained.

## Measured evidence

| Check                            | Result               | Notes                                                                                              |
| -------------------------------- | -------------------- | -------------------------------------------------------------------------------------------------- |
| Complete focused prototype suite | 10 passed in 5 files | 6.26 seconds; includes both candidates, projection, rubric, shell, and flags                       |
| Candidate component test         | Passed               | 3.63-second command; mounts the real Rete area and verifies selection updates the Wright inspector |
| Production build                 | Passed               | Vite portion 1.91 seconds                                                                          |
| Candidate lazy JS chunk          | 110.23 kB            | 33.00 kB gzip                                                                                      |
| Candidate lazy CSS chunk         | 3.03 kB              | 1.08 kB gzip                                                                                       |
| Browser capture                  | Passed               | Headless Chromium, reference viewport, used as inspection evidence rather than a new browser test  |

The existing Vite `__dirname` future-loader warning and existing large main/Plotly chunk warnings remain.

## Findings and costs

1. Rete can reproduce the visual contract while leaving the Wright model canonical. It does not require candidate-native serialization or phase/group state.
2. Rete is a lower-level editor toolkit than React Flow for this use. The candidate needs an editor, area plugin, renderer plugin, render utilities, React renderer, and styled-components peer rather than one primary package.
3. Rete's default 24-pixel sockets were too large for the compact engineering cards. A custom supported socket renderer was required.
4. Rete's default direct Bezier paths placed reverse feedback links over forward flow. A custom SVG connection renderer was required to route feedback rails and retain engineer-facing labels.
5. The initial classic connection styling path forwarded a `styles` prop to an SVG path under React 19 and produced a browser warning. Replacing it with the custom SVG connection removed that warning. This compatibility friction counts against implementation cost even though the final candidate is clean.
6. Rete fit-to-view waits for an animation frame. The jsdom component test needs a deterministic `requestAnimationFrame` shim; it does not need Playwright or DOM-size polling.
7. Preventing node translation in the read-only harness is concise through an area pipe, but production editing would require translating Rete events into Wright commands and proving keyboard behavior rather than adopting Rete state.
8. The lazy bundle is materially smaller than the current React Flow candidate, but Rete required more custom canvas code to achieve comparable visual grammar. Bundle size must not outweigh accessibility, maintenance, and implementation/test economics.

## Still required before a candidate decision

- 25- and 100-block fixtures and interaction measurements;
- keyboard/semantic and axe evidence;
- completed rubric scores and deletion exercises;
- equivalent shallow LiteGraph.js evidence;
- a direct comparison of custom-routing and authoring-event costs.

No recommendation to retain or replace Rivet is made by this partial checkpoint.
