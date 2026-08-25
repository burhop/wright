# CP2 selected-canvas usability review gate

Date: 2026-08-24  
Branch: `076-engineering-workflow-prototype`

## Decision status

**Ready for formative human review; CP2 usability gate is pending.**

The selected UI and its deterministic interaction states are implemented and
verified. The five-person comprehension comparison has not been run, and the
repository does not contain a current-Rivet drill-bit-holder project with
equivalent information. Therefore no 80% comprehension or 30% timing claim is
made here.

This is the deliberate review boundary before CP3 editing work.

## What is ready

- Accepted dark navy role/status visual contract and phase lanes.
- React Flow as a replaceable adapter over the Wright-owned typed fixture.
- Pan, zoom, minimap, selection, keyboard focus, and details/evidence inspector.
- Deterministic loading, empty, and error examples.
- Phase focus and a 100-block all-phases overview.
- Non-color-only feedback return rails and engineer-readable labels.
- Explicit generic MCP evidence boundary; no domain runtime services.
- A repeatable, counterbalanced moderator script at
  `apps/web/src/prototypes/engineering-workflow/evaluation/usability-script.md`.
- Pure metrics that reject duplicate/incomplete data and calculate the exact
  paired 80% comprehension and 30% median-time gates.

Visual evidence is retained in `cp2b-selected-ui.png` and
`cp2b-100-block-ui.png`.

## Verification economics

Complete isolated prototype suite:

```text
Test Files  13 passed (13)
Tests       36 passed (36)
Duration    11.38s
```

Production build:

```text
TypeScript build: passed
Vite build:       passed in 3.14s
Prototype chunk:  221.96 kB / 70.12 kB gzip
```

The behavior is owned by pure model/projection tests and component tests. CP2B
used two bounded Chromium screenshots for visual overlap and legibility only;
no broad or stateful Playwright workflow was added. This keeps the normal
feedback loop below the 30-second component-test gate and avoids repeating the
slow, failure-prone browser-heavy pattern observed in the Rivet work.

The existing Vite native-config warning and application-wide chunk warning are
informational baseline warnings.

## Baseline prerequisite

A valid comparison requires Rivet and the prototype to expose equivalent
content: the same 25 blocks, labels, phase meaning, connections, review gates,
feedback paths, and inspector facts. The existing repository Rivet examples
are different engineering stories and sizes. Substituting one would confound
content complexity with visual-language comprehension.

Acceptable ways to establish the baseline are:

1. use an existing user-owned Rivet drill-bit-holder project if one already
   contains the equivalent content; or
2. create a disposable Rivet fixture solely for baseline measurement, without
   modifying Rivet code, its project schema, or production persistence.

Capture the baseline project identity, commit/build, viewport, reset state, and
screenshot before recording participant times.

## Human review procedure

1. Confirm the equivalent Rivet baseline against the scoring key.
2. Run the product owner once as directional feedback and fix only clear visual
   defects before freezing the study surfaces.
3. Run at least five paired, counterbalanced, uncoached participants using the
   exact moderator script.
4. Preserve raw answers and trial records; calculate results through
   `evaluateComprehensionGate`.
5. Record common confusion separately from feature requests.
6. Choose `continue`, `change`, `stop`, or `defer` for CP3.

Until those steps are complete, the correct objective conclusion is that the
prototype is test-ready and visually promising, but comparative superiority
over current Rivet is unproven.
