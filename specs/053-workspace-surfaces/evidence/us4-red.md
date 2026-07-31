# User Story 4 Red Baseline

Recorded: 2026-07-30

Command:

```text
npm run test --workspace apps/web -- --run src/components/workspace/workspace-layout.spec.ts src/components/surfaces/SurfaceTabs.spec.tsx src/components/workspace/PaneSeparator.spec.tsx src/components/surfaces/SurfaceDeck.spec.tsx
```

Expected result: **failed** before implementation.

- `workspace-layout.spec.ts` could not resolve the not-yet-created versioned layout reducer.
- `SurfaceTabs.spec.tsx` could not resolve the not-yet-created accessible tab primitive.
- `PaneSeparator.spec.tsx` could not resolve the not-yet-created separator primitive.
- The existing deck failed the new pressure-warning and explicit reload requirements because it silently evicted a stateful host.

The four pre-existing retained-deck assertions continued to pass. This baseline proves the new tests exercise behavior absent from the prior implementation instead of passing vacuously.
