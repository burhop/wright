# CP2B phase focus and feedback routing

Date: 2026-08-24  
Branch: `076-engineering-workflow-prototype`

## Outcome

The selected React Flow adapter now supports progressive disclosure without
changing the Wright-owned workflow model:

- Workflows with 25 or more blocks show `All phases`, `Define`, `Verify`, and
  `Manufacture` focus controls.
- A focused phase shows only its blocks and internal connections, selects its
  first block for inspector context, and refits the viewport. Returning to
  `All phases` restores the complete projection.
- Fifty-plus-block all-phase views open at the existing 35% minimum zoom as an
  overview. Engineers can focus a phase for readable block-level work.
- Feedback connections use a dedicated dashed return rail and an explicit
  label. They are distinguishable by route and line pattern as well as color.
- The normal connection and phase semantics remain in Wright's projection;
  React Flow is still a rendering and interaction adapter only.

This checkpoint does not add editing, persistence, LLM execution, or MCP
execution. Generic MCP binding remains the runtime boundary; engineering
categories remain discovery metadata and templates.

## Visual evidence

- `cp2b-selected-ui.png`: the reference engineering workflow at
  `/prototype/engineering-workflow`.
- `cp2b-100-block-ui.png`: the deterministic scale fixture at
  `/prototype/engineering-workflow?scale=100`.

Both screenshots were captured at 1680 by 950 pixels with the accepted dark
navy visual contract. The navigation controls occupy a reserved header band so
they do not cover workflow blocks.

## Verification

Focused model/component suite:

```text
Test Files  4 passed (4)
Tests       14 passed (14)
Duration    6.22s
```

The suite covers neutral projection filtering, unknown-phase rejection,
custom feedback-edge semantics, loading/empty/error regressions, 25- and
100-block selection/focus, and a 100-block phase-focus round trip.

Production build:

```text
TypeScript build: passed
Vite build:       passed in 2.41s
Prototype chunk:  221.96 kB / 70.12 kB gzip
```

The existing Vite native-config and application-wide chunk-size warnings
remain informational and are not introduced by this checkpoint.

## Efficient test boundary

The large-workflow behavior is verified primarily with pure projection tests
and jsdom component tests. Browser use for this checkpoint was limited to two
repeatable screenshots because visual overlap and legibility cannot be proven
by model tests alone. No broad end-to-end Playwright suite was added.
