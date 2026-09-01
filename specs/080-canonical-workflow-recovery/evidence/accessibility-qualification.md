# T056 accessibility and usability qualification status

**Date**: 2026-09-01

**Exact automated subject**: commit `3f83b153b49fbdcb582681218dd59a7c2f0e272e` / tree `590491520b9406d76b7e7ae9702d5e3d9a8710a6`

**Task status**: **OPEN**. The locally automatable keyboard, focus, page-scale, accessibility-tree, and automated-rule portions pass. A real assistive-technology session and moderated representative-engineer sessions have not occurred and are not inferred.

## Passing local evidence

- A real Tab sequence preserves the intended top-level view/validate/port-lab/AI/palette order.
- Every representative action in the test uses keyboard activation: reusable-component disclosure, stable-ID focus, relationship selection/disconnect/reconnect through typed handles, modal open, focus trap, Escape close, and focus return.
- The test exposed that React Flow's roving-focus implementation skips nested node controls even when they declare `tabindex=0`. The accepted repair adds a keyboard-reachable component disclosure beside the stable-ID navigator; it drives the same renderer-only collapse state and leaves the accepted definition unchanged.
- Chromium's page scale factor is set to exactly `2`; `visualViewport.scale` reports `2`, document horizontal overflow remains zero, and palette/canvas/inspector semantics remain available.
- The Chromium accessibility tree includes the level-one workflow heading, named view and inspector tablists, named diagram, typed connection handles, separate artifact inspection, component expansion, and fit control.
- Axe reports zero serious or critical findings against the complete recovery concept at the two-times page scale. The retained reduced-motion and 390-pixel containment test also passes.

```text
Focused accessibility Playwright: 2 passed (1 worker)
Combined recovery + accessibility Playwright: 8 passed (14.4s)
Focused React renderer/host Vitest: 10 passed
TypeScript/Vite production build: passed
ESLint: 0 errors; 3 pre-existing hook warnings outside this change
```

## Failed-first evidence

The first keyboard run failed because the visual component button could be clicked but did not retain focus inside the React Flow node. Explicit nested key handling did not repair actual Tab reachability. A captured Tab-order diagnostic showed that focus moved from canvas controls directly to the inspector and skipped React Flow node wrappers. The keyboard-reachable navigator disclosure repaired the interaction without pretending the inaccessible nested path passed. The initial build then caught one strict `string | undefined` narrowing error in the supplementary node-arrow handler; it was repaired before the passing production build.

## Gates that remain external

The automated accessibility-tree snapshot is not an NVDA, JAWS, Narrator, or VoiceOver session. No claim is made about announcement cadence, virtual-cursor behavior, speech ambiguity, or real assistive-technology usability.

No representative mechanical engineers were recruited or observed. Therefore task T056 and CAP-025's moderated usability gate remain open. The ready-to-run protocol is [moderated-engineer-usability-protocol.md](moderated-engineer-usability-protocol.md). Closing this gate requires real participants, contemporaneous notes, exact subject identity, consent/privacy handling, and honest results—including failures—not an agent-authored simulation.

This external dependency does not authorize skipping the gate and does not prevent locally independent T057 security qualification from proceeding.

The refreshed dashboard verifier passed at `2026-09-01T04:54:40.544Z` while
keeping the ledger at 55/60, T056 visibly open on its human gates, eight
evidence images loaded, zero browser diagnostics, zero desktop/mobile overflow,
evidence HTTP checks at 200, traversal checks at 403, benchmark readiness at
0/100, and customer readiness false.
