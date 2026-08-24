# CP1A Evidence: Engineer-Readable Visual Contract

**Status**: Accepted — continue to CP1B
**Branch**: `076-engineering-workflow-prototype`
**Commit**: `63bfcba`

## Hypothesis

A faithful read-only UI based on the generated reference image can make the intended product concrete before Wright selects a graph library, provided reusable presentation components are separated from replaceable static positioning and connector code.

## Demonstrated scope

- Feature-flagged direct route: `/prototype/engineering-workflow`
- Offline deterministic fixture; no backend bootstrap required for the route
- Workflow toolbar, compact engineering palette, phase lanes, blocks, review gates, connections, inspector, legend, zoom controls, and minimap
- Selectable blocks with fixture-backed property details
- Searchable/filterable engineering capability library with 19 initial templates
- CAD, FEA, CAM, CFD, PLM/PDM, kinematics, thermal, manufacturing, quality, and supplier-oriented examples
- Generic MCP action presentation with no graph dependency, MCP call, LLM call, editing, or persistence

## Visual evidence

- [Workflow visual slice](visual-slice-workflow.png)
- [Engineering capability library](visual-slice-capability-library.png)

Both captures use the reference image dimensions of 1680×940.

## Verification

| Check                                    | Result   | Duration / notes                                             |
| ---------------------------------------- | -------- | ------------------------------------------------------------ |
| Focused component and feature-flag tests | 7 passed | 4.56 seconds on the final serialized run                          |
| Production web build                     | Passed   | 13.76 seconds wall time; Vite portion 2.23 seconds           |
| Graph dependencies added                 | None     | Static projection only                                       |
| Browser automation added                 | None     | Playwright was used only to capture the two checkpoint views |
| Domain-specific services/executors added | None     | Capability categories are discovery metadata                 |

Existing Vite warnings remain: future native config loading does not support the current `__dirname` use, and existing large production chunks exceed the reporting threshold. The prototype is lazy-loaded into its own 30.90 kB JavaScript / 18.16 kB CSS chunks.

## Findings

1. The target image translates well into Wright's existing dark design language without a graph library.
2. A narrow flat list does not scale across engineering disciplines. Pinned/recent templates plus a searchable library is substantially clearer.
3. Friendly categories must remain distinct from execution. Each card is explicitly a generic MCP action template and exact catalog binding is deferred.
4. The initial route was inside `AuthGate` and stalled at “Connecting to Wright…” without the backend. Moving the isolated route outside authenticated bootstrap made the deterministic visual review genuinely offline and allowed removal of prototype-specific `AppShell` behavior.
5. Focused component feedback is comfortably below the 30-second target. The first rerun exposed one ambiguous test query, not a product defect; the corrected suite completed in under five seconds.

## Intentionally unwired

- drag/drop, node creation, connection editing, undo/redo, and draft persistence;
- graph-library pan/layout behavior beyond the small static preview zoom control;
- real capability catalog match counts and exact MCP binding;
- LLM authoring, execution, approvals, artifacts, evidence, notifications, and history;
- production navigation, migration, and Rivet compatibility.

## Review questions

1. Is the overall visual direction close enough to the generated reference image to become the CP1B target?
2. Are the phase lanes, review gates, feedback paths, and role colors understandable at a glance?
3. Does the pinned-plus-library capability pattern feel appropriate for the breadth of engineering tools?
4. Should any visual element be changed before graph candidates are evaluated?

## Decision

Continue to CP1B, approved by the user on 2026-08-24.
