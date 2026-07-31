# User Story 4 Green Evidence

Recorded: 2026-07-30

## Implemented scope

- Version-2 user/workspace layout persistence in basis points with separate normal and focus values, legacy migration, malformed-state fallback, exact 320/480/8 CSS-pixel constraints, and reversible narrow state.
- Grid-based focus mode that removes non-chat chrome, retains live chat and surface trees, exposes pointer/keyboard resizing, and restores focus and prior layout state.
- Semantic surface tabs, selected-surface lifecycle status, explicit no-reorder behavior, next/previous/heading close focus restoration, and retained-host pressure consent before stateful reload.
- Explicit Chat/Surface narrow switcher, hidden-chat live announcements, F6 host-region cycling, controls on both sides of live frames, truthful unverified-frame disclosure, browser fallback, and Electron Ctrl/Command+Shift+F6 return-to-host routing.
- Focus/accessibility documentation and component scenarios for normal, focus, narrow, loading, error, and permission states.

## Automated evidence

### Web unit and component suite

```text
npm run test --workspace apps/web
Test Files  47 passed (47)
Tests       193 passed (193)
```

Focused layout, persistence, tab, separator, deck, and focus-manager runs also passed throughout implementation. The red baseline is recorded separately in `us4-red.md`.

### Electron host bridge

```text
node --test hermes-wright-panel/tests/surface-host-adapter.spec.cjs
tests 5; pass 5; fail 0
```

This covers the external-open boundary, navigation policy, exact return accelerator, child-frame preload exclusion, and removable preload callback.

### Complete Workspace Surfaces browser regression matrix

```text
npx playwright test tests/ui-integration/workspace-surfaces --workers=1
52 passed
```

The matrix ran Chromium, Firefox, WebKit, and desktop-host Chromium. It includes focus/narrow, keyboard/frame-return, axe, framing fallback, hostile surfaces, panel/browser sharing, presentation restoration, and Python display journeys. A compatibility rerun of the affected framing/Python/axe slice passed 20/20 after semantic tab/status corrections.

The dedicated final focus/accessibility matrix also passed:

```text
npx playwright test tests/ui-integration/workspace-surfaces/focus-layout.spec.ts tests/ui-integration/workspace-surfaces/focus-accessibility.spec.ts --workers=1
16 passed
```

Every configured engine reported zero serious or critical axe violations in the Wright host region.

### Static and production checks

```text
npm run lint --workspace apps/web
PASS

npm run build --workspace apps/web
PASS

git diff --check
PASS
```

The production build retained the repository's existing large-chunk advisory for the main/Plotly bundles; it produced no build error. Firefox and WebKit were initially absent on this Windows host, then the pinned Playwright runtimes were installed and the full matrix was rerun successfully.
